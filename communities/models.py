"""Community models for managing communities and memberships."""

from django.db import models, IntegrityError
from accounts.models import UserProfile
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from core.html_sanitizer import sanitize_announcement_html, strip_all_html
import uuid

import os
import mimetypes
import subprocess
import tempfile
import shutil
from django.conf import settings

# Optional libmagic support
try:
    import magic
except Exception:
    magic = None


def is_valid_timezone(tz_name: str) -> bool:
    """
    Check if a timezone name is valid IANA timezone.

    Tries to use stdlib zoneinfo (Python 3.9+) if available, otherwise falls back to pytz.
    If neither is available, performs a basic string check (not ideal but better than nothing).
    """
    # Timezone validation helper: prefer stdlib zoneinfo, fall back to pytz
    try:
        from zoneinfo import ZoneInfo

        def is_valid_timezone(tz_name: str) -> bool:
            try:
                ZoneInfo(tz_name)
                return True
            except Exception:
                return False
    except Exception:
        try:
            import pytz

            def is_valid_timezone(tz_name: str) -> bool:
                return tz_name in getattr(pytz, 'all_timezones', [])
        except Exception:

                return isinstance(tz_name, str) and bool(tz_name)


def validate_timezones(value):
    """Validator for timezone_list JSONField: expects a list of valid IANA time zone names."""
    if value is None:
        return
    if not isinstance(value, list):
        raise ValidationError(_('Timezones must be a list.'))
    errors = []
    for tz in value:
        if not isinstance(tz, str) or not tz:
            errors.append(ValidationError(_('Invalid timezone entry: %(tz)s'), params={'tz': tz}))
            continue
        if not is_valid_timezone(tz):
            errors.append(ValidationError(_('Unknown timezone: %(tz)s'), params={'tz': tz}))
    if errors:
        raise ValidationError(errors)


class Community(models.Model):
    """Communities that users can create and join"""
    COMMUNITY_TYPES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('restricted', 'Restricted'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=1000, blank=True)
    community_type = models.CharField(
        max_length=10,
        choices=COMMUNITY_TYPES,
        default='public'
    )

    # Media
    avatar = models.ImageField(
        upload_to='communities/avatars/',
        blank=True,
        null=True
    )
    # New: support image OR short video for community cover
    cover_media = models.FileField(
        upload_to='communities/covers/media/',
        blank=True,
        null=True,
        help_text='Image or short video file used as community cover.'
    )
    cover_media_type = models.CharField(
        max_length=10,
        choices=[('image', 'Image'), ('video', 'Video')],
        default='image'
    )

    # Geographic Association - Optional (divisions can change over time)
    division = models.ForeignKey(
        'core.AdministrativeDivision',
        on_delete=models.SET_NULL,
        related_name='communities',
        null=True,
        blank=True,
        help_text=(
            "The geographic division this community belongs to "
            "(e.g., municipality, commune). Optional as divisions may change."
        )
    )

    # Management
    creator = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='created_communities'
    )
    rules = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)

    # Rubrique configuration
    enabled_rubriques = models.JSONField(
        default=list,
        blank=True,
        help_text="List of enabled rubrique template IDs (UUIDs as strings)"
    )

    # Settings
    allow_posts = models.BooleanField(default=True)
    require_post_approval = models.BooleanField(default=False)
    allow_external_links = models.BooleanField(default=True)

    # Geo-restriction settings
    # is_geo_restricted = models.BooleanField(
    #     default=False,
    #     help_text="Whether this community is restricted to specific geographic regions"
    # )
    # geo_restriction_type = models.CharField(
    #     max_length=20,
    #     choices=[
    #         ('none', 'No Restriction'),
    #         ('countries', 'Specific Countries'),
    #         ('cities', 'Specific Cities'),
    #         ('exclude_countries', 'Exclude Countries'),
    #         ('exclude_cities', 'Exclude Cities'),
    #         ('timezone_based', 'Timezone Based'),
    #         ('exclude_timezones', 'Exclude Timezones')
    #     ],
    #     default='none',
    #     help_text="Type of geographic restriction applied"
    # )
    # geo_restriction_message = models.TextField(
    #     max_length=500,
    #     blank=True,
    #     help_text="Custom message shown to users from restricted regions"
    # )

    # Analytics (no members_count - communities are public)
    posts_count = models.PositiveIntegerField(default=0)
    threads_count = models.PositiveIntegerField(default=0)

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['division', '-created_at']),
            models.Index(fields=['community_type', '-created_at']),
            models.Index(fields=['is_active', '-posts_count']),
            models.Index(fields=['is_featured', '-created_at']),
        ]

    def _generate_unique_slug(self, base_text=None, max_length=100):
        """Generate a URL-safe unique slug for this Community.

        Uses `slugify` on the provided base_text (falls back to the community name).
        If a slug collision occurs, appends a short uuid4 hex suffix and retries.
        """
        if not base_text:
            base_text = (self.name or "community").strip()

        # Base slug
        base_slug = slugify(base_text)[:max_length].strip('-') or 'community'

        slug = base_slug
        attempt = 0
        # Ensure slug unique across communities (exclude self when updating)
        while True:
            qs = Community.objects.filter(slug=slug)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if not qs.exists():
                return slug

            # Collision: append short suffix and retry
            attempt += 1
            suffix = uuid.uuid4().hex[:6]
            # Trim base to allow suffix and hyphen within max_length
            trim_length = max_length - (len(suffix) + 1)
            slug = f"{base_slug[:trim_length].rstrip('-')}-{suffix}"
            if attempt >= 10:
                # As a last resort, add full uuid
                slug = f"{base_slug[:max_length-8]}-{uuid.uuid4().hex[:8]}"
                return slug

    def save(self, *args, **kwargs):
        """Override save to auto-generate a unique slug when missing.

        This ensures frontend no longer needs to supply slugs; the database
        constraint will still enforce uniqueness. The method retries on
        collisions and guards against race conditions by catching IntegrityError
        and regenerating the slug a few times.
        """
        # If slug is blank/None, generate one from the name
        if not self.slug:
            self.slug = self._generate_unique_slug()

        # Try saving; on IntegrityError (rare race), regenerate and retry
        attempts = 0
        while True:
            try:
                # Validate cover_media MIME, size and duration (for video)
                if self.cover_media:
                    filename = getattr(self.cover_media, 'name', '') or ''

                    mime = None
                    try:
                        fobj = getattr(self.cover_media, 'file', None)
                        if magic and fobj is not None:
                            try:
                                fobj.seek(0)
                                blob = fobj.read(4096)
                                fobj.seek(0)
                                mime = magic.from_buffer(blob, mime=True)
                            except Exception:
                                mime = None
                    except Exception:
                        mime = None

                    if not mime:
                        mime, _ = mimetypes.guess_type(filename)

                    if not mime:
                        raise ValidationError('Could not determine cover_media MIME type')

                    max_image_bytes = int(getattr(settings, 'PROFILE_COVER_IMAGE_MAX_BYTES', os.environ.get('PROFILE_COVER_IMAGE_MAX_BYTES', 5 * 1024 * 1024)))
                    max_video_bytes = int(getattr(settings, 'PROFILE_COVER_VIDEO_MAX_BYTES', os.environ.get('PROFILE_COVER_VIDEO_MAX_BYTES', 15 * 1024 * 1024)))

                    if mime.startswith('image/'):
                        expected_type = 'image'
                        max_bytes = max_image_bytes
                    elif mime.startswith('video/'):
                        expected_type = 'video'
                        max_bytes = max_video_bytes
                    else:
                        raise ValidationError('Unsupported cover_media MIME type')

                    size = None
                    try:
                        size = getattr(self.cover_media, 'size', None)
                    except Exception:
                        size = None

                    if size and size > max_bytes:
                        raise ValidationError(f'Cover media exceeds max allowed size ({max_bytes} bytes).')

                    # If video, check duration with ffprobe
                    if expected_type == 'video':
                        max_duration = int(getattr(settings, 'COVER_VIDEO_MAX_DURATION_SECONDS', os.environ.get('COVER_VIDEO_MAX_DURATION_SECONDS', 60)))

                        file_path = None
                        temp_file = None
                        try:
                            try:
                                file_path = self.cover_media.temporary_file_path()
                            except Exception:
                                file_path = None

                            if not file_path:
                                temp = tempfile.NamedTemporaryFile(delete=False)
                                temp_file = temp.name
                                f = getattr(self.cover_media, 'file', None)
                                if f is not None:
                                    try:
                                        f.seek(0)
                                    except Exception:
                                        pass
                                    shutil.copyfileobj(f, temp)
                                else:
                                    temp.write(self.cover_media.read())
                                temp.close()
                                file_path = temp_file

                            cmd = [
                                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                '-of', 'default=noprint_wrappers=1:nokey=1', file_path
                            ]
                            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
                            if proc.returncode == 0 and proc.stdout:
                                try:
                                    duration = float(proc.stdout.strip())
                                except Exception:
                                    duration = None
                            else:
                                duration = None

                            if duration is not None and duration > max_duration:
                                raise ValidationError(f'Cover video duration {duration:.1f}s exceeds maximum of {max_duration}s')
                        finally:
                            if temp_file:
                                try:
                                    os.unlink(temp_file)
                                except Exception:
                                    pass

                    self.cover_media_type = expected_type

                super().save(*args, **kwargs)
                break
            except IntegrityError:
                attempts += 1
                if attempts > 5:
                    raise
                # Regenerate slug with extra randomness
                self.slug = self._generate_unique_slug()

    def __str__(self):
        return self.name

    # Rubrique management helper methods
    def get_enabled_rubriques(self):
        """
        Get all enabled rubriques for this community as a queryset.

        Returns:
            QuerySet of RubriqueTemplate objects that are enabled for this community.
        """
        if not self.enabled_rubriques:
            return RubriqueTemplate.objects.none()

        return RubriqueTemplate.objects.filter(
            id__in=self.enabled_rubriques,
            is_active=True
        ).order_by('path', 'default_order')

    def is_rubrique_enabled(self, rubrique_id):
        """
        Check if a specific rubrique is enabled for this community.

        Args:
            rubrique_id: UUID or string UUID of the rubrique to check

        Returns:
            Boolean indicating if the rubrique is enabled
        """
        if not self.enabled_rubriques:
            return False

        # Convert to string for comparison
        rubrique_id_str = str(rubrique_id)
        return rubrique_id_str in self.enabled_rubriques

    def get_rubrique_tree(self):
        """
        Get enabled rubriques organized in a hierarchical tree structure.

        Returns:
            List of dicts representing the rubrique hierarchy:
            [
                {
                    'id': UUID,
                    'template_type': 'evenements',
                    'name': 'Événements',
                    'icon': '🎭',
                    'depth': 0,
                    'children': [
                        {'id': UUID, 'template_type': 'evenements_concerts', ...},
                        ...
                    ]
                },
                ...
            ]
        """
        enabled = self.get_enabled_rubriques()

        # Build tree structure
        tree = []
        rubrique_map = {}

        # First pass: create all nodes
        for rubrique in enabled:
            node = {
                'id': str(rubrique.id),
                'template_type': rubrique.template_type,
                'name': rubrique.default_name,
                'icon': rubrique.default_icon,
                'color': rubrique.default_color,
                'depth': rubrique.depth,
                'path': rubrique.path,
                'parent_id': str(rubrique.parent_id) if rubrique.parent_id else None,
                'children': [],
                'isExpandable': False  # Will be set to True if has children
            }
            rubrique_map[str(rubrique.id)] = node

        # Second pass: build hierarchy
        for node in rubrique_map.values():
            if node['parent_id'] and node['parent_id'] in rubrique_map:
                # Add to parent's children
                rubrique_map[node['parent_id']]['children'].append(node)
                # Mark parent as expandable
                rubrique_map[node['parent_id']]['isExpandable'] = True
            else:
                # Top-level rubrique
                tree.append(node)

        return tree

    def add_rubrique(self, rubrique_id):
        """
        Enable a rubrique for this community.

        Args:
            rubrique_id: UUID or string UUID of the rubrique to enable

        Returns:
            Boolean indicating if the rubrique was added (False if already enabled)
        """
        rubrique_id_str = str(rubrique_id)

        # Verify rubrique exists and is active
        try:
            rubrique = RubriqueTemplate.objects.get(id=rubrique_id_str, is_active=True)
        except RubriqueTemplate.DoesNotExist:
            return False

        # Initialize list if needed
        if self.enabled_rubriques is None:
            self.enabled_rubriques = []

        # Check if already enabled
        if rubrique_id_str in self.enabled_rubriques:
            return False

        # Add rubrique
        self.enabled_rubriques.append(rubrique_id_str)
        self.save(update_fields=['enabled_rubriques', 'updated_at'])
        return True

    def remove_rubrique(self, rubrique_id):
        """
        Disable a rubrique for this community.

        Note: Cannot remove required rubriques.

        Args:
            rubrique_id: UUID or string UUID of the rubrique to disable

        Returns:
            Boolean indicating if the rubrique was removed (False if not enabled or required)
        """
        rubrique_id_str = str(rubrique_id)

        # Check if rubrique is required
        try:
            rubrique = RubriqueTemplate.objects.get(id=rubrique_id_str)
            if rubrique.is_required:
                return False
        except RubriqueTemplate.DoesNotExist:
            return False

        # Check if enabled
        if not self.enabled_rubriques or rubrique_id_str not in self.enabled_rubriques:
            return False

        # Remove rubrique
        self.enabled_rubriques.remove(rubrique_id_str)
        self.save(update_fields=['enabled_rubriques', 'updated_at'])
        return True

    # def can_user_access_geographically(self, user_profile, current_country=None, current_city=None):
    #     """
    #     Check if user can access this community based on geographic restrictions.

    #     This method now supports traveler-friendly access by checking both:
    #     1. User's registration location (profile-based) - for original access rights
    #     2. User's current location (IP-based) - for current location restrictions

    #     Supports both country and city-level restrictions for comprehensive geo-control.

    #     If user registered in an allowed location but is traveling to a restricted
    #     location, they maintain access based on their registration location.

    #     Args:
    #         user_profile: UserProfile object or Country object (fallback)
    #         current_country: Country object from IP detection (optional)
    #         current_city: City object from IP detection (optional)

    #     Returns:
    #         tuple: (is_allowed, restriction_type, error_message)
    #             - is_allowed: Boolean indicating if access is granted
    #             - restriction_type: String indicating type of restriction applied
    #             - error_message: Error message if access denied
    #     """
    #     if not self.is_geo_restricted or self.geo_restriction_type == 'none':
    #         return True, None, None

    #     # Extract user's profile/registration location
    #     profile_country = None
    #     profile_city = None

    #     if hasattr(user_profile, 'country'):
    #         profile_country = user_profile.country
    #         profile_city = user_profile.city
    #     elif hasattr(user_profile, 'iso2'):  # It's a Country object
    #         profile_country = user_profile

    #     # If no profile location and no current location, restrict access
    #     if not profile_country and not current_country:
    #         if self.geo_restriction_type in ['countries', 'cities', 'exclude_countries']:
    #             return False, self.geo_restriction_type, (
    #                 self.geo_restriction_message or
    #                 "This community is restricted to specific regions. "
    #                 "Please update your location in your profile to continue."
    #             )
    #         return True, None, None

    #     # NEW PRIORITY-BASED ACCESS LOGIC:
    #     # Priority 2: Check registration/profile location first
    #     # (Note: Priority 1 - membership check is handled in views.py)
    #     if profile_country:
    #         profile_allowed, restriction_type, profile_message = self._check_location_access(
    #             profile_country, profile_city
    #         )
    #         if profile_allowed:
    #             # User's registration location is allowed - grant access regardless of current location
    #             return True, None, None

    #     # Priority 3: Check current location (only if registration location failed/blocked)
    #     # This handles cases where registration is blocked but current location is allowed
    #     if current_country:
    #         current_allowed, restriction_type, current_message = self._check_location_access(
    #             current_country, current_city
    #         )
    #         if current_allowed:
    #             # Current location is allowed, even though registration location was blocked
    #             return True, None, None

    #     # Priority 4: Block access - both registration and current locations are blocked/unavailable
    #     # Determine which error message to show based on available location data
    #     if current_country:
    #         # Show current location restriction message
    #         location_name = current_city.name if current_city else current_country.name
    #         return False, restriction_type, (
    #             current_message or
    #             self.geo_restriction_message or
    #             f"Access restricted. This community is not available in {location_name}."
    #         )
    #     elif profile_country:
    #         # Show profile location restriction message
    #         return self._check_location_access(profile_country, profile_city)
    #     else:
    #         # No location data available
    #         return False, self.geo_restriction_type, (
    #             self.geo_restriction_message or
    #             "This community is restricted to specific regions. "
    #             "Please update your location in your profile to continue."
    #         )

    #     return True, None, None

    # def _check_location_access(self, country, city=None):
    #     """
    #     Check if a location (country + optional city) can access community.

    #     Handles both country-level and city-level restrictions.

    #     Args:
    #         country: Country object to check
    #         city: City object to check (optional, for city restrictions)

    #     Returns:
    #         tuple: (is_allowed, restriction_type, error_message)
    #     """
    #     if not country:
    #         return False, 'location', "Location information required for access."

    #     # Check country-based restrictions (enhanced)
    #     if self.geo_restriction_type in ['countries', 'exclude_countries']:
    #         country_allowed, country_msg = self._check_enhanced_country_access(
    #             country
    #         )
    #         if not country_allowed:
    #             return False, 'country', country_msg

    #         # Country allowed - check city restrictions if applicable
    #         if city:
    #             city_allowed, city_msg = self._check_city_access(country, city)
    #             if not city_allowed:
    #                 return False, 'city', city_msg
    #         return True, None, None

    #     elif self.geo_restriction_type in ['cities', 'exclude_cities']:
    #         # For city-based restrictions
    #         country_allowed = self.geo_restrictions.filter(
    #             community=self,
    #             restriction_type__in=['allow_country', 'allow_city'],
    #             country=country,
    #             is_active=True
    #         ).exists()

    #         if not country_allowed:
    #             return False, 'country', (
    #                 self.geo_restriction_message or
    #                 f"This community is restricted to specific regions. "
    #                 f"{country.name} is not included."
    #             )

    #         # Country allowed - check city restrictions if applicable
    #         if city:
    #             city_allowed, city_msg = self._check_city_access(country, city)
    #             if not city_allowed:
    #                 return False, 'city', city_msg

    #     elif self.geo_restriction_type in ['timezone_based', 'exclude_timezones']:
    #         # Use comprehensive timezone-based access control
    #         try:
    #             from communities.timezone_access_control import (
    #                 validate_community_timezone_access
    #             )

    #             # Attach request to community for timezone validation
    #             request = getattr(self, '_request', None)
    #             if not request:
    #                 return False, 'timezone', (
    #                     "Timezone-based access control requires user session "
    #                     "information."
    #                 )

    #             # Use comprehensive timezone validation
    #             is_allowed, error_message = validate_community_timezone_access(
    #                 request, self, check_hours=True
    #             )

    #             if not is_allowed:
    #                 return False, 'timezone', error_message

    #         except ImportError:
    #             # Fallback to basic timezone check if utilities not available
    #             timezone_restrictions = self.geo_restrictions.filter(
    #                 restriction_type__in=['allow_timezone', 'block_timezone'],
    #                 is_active=True
    #             )
    #             if timezone_restrictions.exists():
    #                 return False, 'timezone', (
    #                     "Timezone-based restrictions are configured but "
    #                     "timezone utilities are not available."
    #                 )

    #     return True, None, None

    # def _check_city_access(self, country, city):
    #     """
    #     Check city-level restrictions for a given country and city.

    #     Args:
    #         country: Country object
    #         city: City object

    #     Returns:
    #         tuple: (is_allowed, error_message)
    #     """
    #     # Check if city is explicitly allowed
    #     if self.geo_restrictions.filter(
    #         restriction_type='allow_city',
    #         country=country,
    #         city=city,
    #         is_active=True
    #     ).exists():
    #         return True, None

    #     # Check if city is explicitly blocked
    #     if self.geo_restrictions.filter(
    #         restriction_type='block_city',
    #         country=country,
    #         city=city,
    #         is_active=True
    #     ).exists():
    #         return False, (
    #             self.geo_restriction_message or
    #             f"Access restricted in {city.name}, {country.name}."
    #         )

    #     # Check if there are city allow restrictions for this country
    #     has_allow_city_rules = self.geo_restrictions.filter(
    #         restriction_type='allow_city',
    #         country=country,
    #         is_active=True
    #     ).exists()

    #     if has_allow_city_rules:
    #         # City restrictions exist but this city not explicitly allowed
    #         return False, (
    #             self.geo_restriction_message or
    #             f"Access restricted in {city.name}, {country.name}."
    #         )

    #     # No city restrictions or city is allowed by default
    #     return True, None

    # def get_allowed_countries_list(self):
    #     """Get list of allowed countries for this community."""
    #     if not self.is_geo_restricted:
    #         return []

    #     if self.geo_restriction_type == 'countries':
    #         # Get allowed countries from CommunityGeoRestriction
    #         allowed_restrictions = self.geo_restrictions.filter(
    #             restriction_type='allow_country',
    #             is_active=True
    #         ).select_related('country')
    #         return list(allowed_restrictions.values(
    #             'country__name', 'country__iso2', 'country__iso3'
    #         ))
    #     elif self.geo_restriction_type == 'exclude_countries':
    #         # Get all countries except blocked ones
    #         from core.models import Country
    #         blocked_restrictions = self.geo_restrictions.filter(
    #             restriction_type='block_country',
    #             is_active=True
    #         ).values_list('country_id', flat=True)
    #         return list(Country.objects.exclude(
    #             id__in=blocked_restrictions
    #         ).values('name', 'iso2', 'iso3'))

    #     return []

    # def get_geo_restriction_summary(self):
    #     """Get human-readable summary of geo-restrictions."""
    #     if not self.is_geo_restricted:
    #         return "Available worldwide"

    #     if self.geo_restriction_type == 'countries':
    #         allowed_restrictions = self.geo_restrictions.filter(
    #             restriction_type='allow_country',
    #             is_active=True
    #         ).select_related('country')
    #         countries = [r.country for r in allowed_restrictions if r.country]
    #         if len(countries) <= 3:
    #             country_names = [c.name for c in countries]
    #             return f"Available in: {', '.join(country_names)}"
    #         else:
    #             return f"Available in {len(countries)} countries"

    #     elif self.geo_restriction_type == 'exclude_countries':
    #         blocked_restrictions = self.geo_restrictions.filter(
    #             restriction_type='block_country',
    #             is_active=True
    #         ).select_related('country')
    #         blocked = [r.country for r in blocked_restrictions if r.country]
    #         if len(blocked) <= 3:
    #             country_names = [c.name for c in blocked]
    #             return f"Not available in: {', '.join(country_names)}"
    #         else:
    #             return f"Not available in {len(blocked)} countries"

    #     elif self.geo_restriction_type == 'regions':
    #         return "Available in specific regions"

    #     elif self.geo_restriction_type == 'timezone_based':
    #         return "Available based on timezone"

    #     elif self.geo_restriction_type == 'exclude_timezones':
    #         return "Not available in specific timezones"

    #     return "Geo-restricted"

    # def _check_enhanced_country_access(self, user_country):
    #     """
    #     Check country access using CommunityGeoRestriction entries.
    #     This provides granular country-based restrictions.
    #     """
    #     # Check individual CommunityGeoRestriction entries for country rules
    #     country_restrictions = self.geo_restrictions.filter(
    #         is_active=True,
    #         country=user_country,
    #         restriction_type__in=['allow_country', 'block_country']
    #     )

    #     for restriction in country_restrictions:
    #         if restriction.restriction_type == 'block_country':
    #             return False, (
    #                 restriction.notes or
    #                 self.geo_restriction_message or
    #                 f"This community is not available in {user_country.name}."
    #             )
    #         elif restriction.restriction_type == 'allow_country':
    #             # If there's an explicit allow rule, country is allowed
    #             return True, None

    #     # Check if there are 'allow_country' rules that exclude this country
    #     allow_country_rules = self.geo_restrictions.filter(
    #         is_active=True,
    #         restriction_type='allow_country'
    #     )

    #     if allow_country_rules.exists():
    #         # There are allow rules, but none for this country
    #         allowed_names = list(
    #             allow_country_rules.values_list('country__name', flat=True)
    #         )
    #         return False, (
    #             self.geo_restriction_message or
    #             f"This community is only available in: "
    #             f"{', '.join(allowed_names)}."
    #         )

    #     return True, None


class RubriqueTemplate(models.Model):
    """Global hierarchical library of ALL possible rubriques and subsections.

    This model contains an exhaustive list of all possible rubriques organized
    hierarchically. Communities simply select which ones they want to enable
    via a JSONField list of IDs. No per-community records are created.

    Architecture Flow:
        1. RubriqueTemplate = Global hierarchical tree (100-200 records total)
           - Main rubriques (parent=None, depth=0)
           - Subsections (parent=rubrique, depth=1+)
        2. Community.enabled_rubriques = JSONField with list of rubrique IDs
        3. Thread.rubrique_template = FK to ANY rubrique (main or subsection)
        4. Validation: rubrique_template.id must be in community.enabled_rubriques

    Example hierarchy:
        Événements (parent=None, depth=0)
        ├── Concerts (parent=Événements, depth=1)
        ├── Sports (parent=Événements, depth=1)
        │   ├── Hockey (parent=Sports, depth=2)
        │   └── Soccer (parent=Sports, depth=2)
        └── Festivals (parent=Événements, depth=1)

    For 10,000 communities:
        - ~200 RubriqueTemplate records (global)
        - 0 additional records (just JSON arrays in Community)
        - Threads FK directly to global RubriqueTemplate
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Hierarchical structure (self-referential)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent rubrique (null for top-level rubriques)"
    )

    # Template identification (unique code for referencing)
    template_type = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique code (e.g., 'actualites', 'evenements_sports_hockey')"
    )

    # Default values (French - primary language)
    default_name = models.CharField(
        max_length=100,
        help_text="Default French name for this rubrique"
    )
    default_name_en = models.CharField(
        max_length=100,
        blank=True,
        help_text="Default English name"
    )
    default_description = models.TextField(
        max_length=500,
        blank=True,
        help_text="Default description template"
    )
    default_icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Default icon (MUI icon name)"
    )
    default_color = models.CharField(
        max_length=7,
        blank=True,
        default='#6366f1',
        help_text="Default color (hex code)"
    )

    # Hierarchy metadata (denormalized for performance)
    depth = models.PositiveIntegerField(
        default=0,
        help_text="0=top-level, 1=subsection, 2=sub-subsection, etc."
    )
    path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Materialized path (e.g., '001.002.003')"
    )

    # Behavior flags
    is_required = models.BooleanField(
        default=False,
        help_text="Auto-enable for all new communities"
    )
    allow_threads = models.BooleanField(
        default=True,
        help_text="Allow creating threads in this rubrique"
    )
    allow_direct_posts = models.BooleanField(
        default=False,
        help_text="Allow posts without threads"
    )

    # Ordering
    default_order = models.PositiveIntegerField(
        default=0,
        help_text="Default display order within parent or at root level"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Template is active and available for use"
    )

    class Meta:
        db_table = 'rubrique_templates'
        ordering = ['parent__default_order', 'default_order', 'default_name']
        verbose_name = 'Rubrique Template'
        verbose_name_plural = 'Rubrique Templates'
        indexes = [
            models.Index(fields=['parent', 'default_order']),
            models.Index(fields=['depth']),
            models.Index(fields=['path']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.default_name} → {self.default_name}"
        return self.default_name

    def get_hierarchy_path(self, separator=' → '):
        """Get full path from root to this rubrique."""
        path_parts = []
        current = self
        while current:
            path_parts.insert(0, current.default_name)
            current = current.parent
        return separator.join(path_parts)

    def get_ancestors(self):
        """Get all ancestor rubriques from root to parent."""
        if not self.parent:
            return RubriqueTemplate.objects.none()

        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent

        return RubriqueTemplate.objects.filter(id__in=[r.id for r in ancestors])

    def get_descendants(self, include_self=False):
        """Get all descendant rubriques recursively."""
        descendants = []

        if include_self:
            descendants.append(self.id)

        def collect_descendants(rubrique):
            for child in rubrique.children.filter(is_active=True):
                descendants.append(child.id)
                collect_descendants(child)

        collect_descendants(self)
        return RubriqueTemplate.objects.filter(id__in=descendants)

    def save(self, *args, **kwargs):
        """Auto-calculate depth and path on save."""
        # Calculate depth
        if self.parent:
            self.depth = self.parent.depth + 1
        else:
            self.depth = 0

        # Generate materialized path
        if self.parent:
            parent_path = self.parent.path or str(self.parent.default_order).zfill(3)
            self.path = f"{parent_path}.{str(self.default_order).zfill(3)}"
        else:
            self.path = str(self.default_order).zfill(3)

        super().save(*args, **kwargs)


def get_default_rubrique_template():
    """Get the default rubrique template (Actualités) for threads."""
    from communities.models import RubriqueTemplate
    try:
        return RubriqueTemplate.objects.get(template_type='actualites').id
    except RubriqueTemplate.DoesNotExist:
        # Fallback to first available template
        first_template = RubriqueTemplate.objects.first()
        return first_template.id if first_template else None


class Thread(models.Model):
    """Discussion thread inside a community.

    Threads organize posts into topics inside a community. Posting directly
    to a community is still allowed, but a post may optionally belong to a
    thread. The thread.owner (creator) can perform thread-level moderation
    like marking best comments or closing the thread.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Rubrique template relationship (REQUIRED for all threads)
    rubrique_template = models.ForeignKey(
        'RubriqueTemplate',
        on_delete=models.PROTECT,  # Can't delete template if threads exist
        related_name='threads',
        default=get_default_rubrique_template,
        help_text="Rubrique category for this thread (REQUIRED)"
    )

    # Community relationship
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='threads'
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, null=True)
    creator = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='created_threads'
    )
    body = models.TextField(blank=True)

    # Best post (for Q&A, solutions, helpful posts, etc.)
    best_post = models.ForeignKey(
        'content.Post',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='thread_best_post_for',
        help_text="Post marked as best by thread creator"
    )

    # Thread configuration
    is_closed = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)

    # Counters
    posts_count = models.PositiveIntegerField(default=0)

    # Soft delete / status
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields (soft restoration support)
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['community', '-created_at']),
            models.Index(fields=['creator', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.community.name}"

    def clean(self):
        """Validate thread data."""
        super().clean()
        from django.core.exceptions import ValidationError

        # Validate rubrique_template is required
        if not self.rubrique_template:
            raise ValidationError({
                'rubrique_template': 'All threads must have a rubrique.'
            })

        # Validate rubrique is enabled for this community
        if self.rubrique_template and self.community:
            # Check if rubrique is in community's enabled_rubriques list
            enabled_rubriques = self.community.enabled_rubriques or []
            rubrique_id = str(self.rubrique_template.id)

            if rubrique_id not in enabled_rubriques:
                raise ValidationError({
                    'rubrique_template':
                        f"Rubrique '{self.rubrique_template.default_name}' "
                        f"is not enabled for '{self.community.name}'."
                })

    def save(self, *args, **kwargs):
        """Save thread after validation and generate slug if needed."""
        # Generate slug from title if not present
        if not self.slug and self.title:
            from django.utils.text import slugify
            base_slug = slugify(self.title)[:250]
            slug = base_slug
            counter = 1

            # Ensure slug is unique
            while Thread.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug[:240]}-{counter}"
                counter += 1

            self.slug = slug

        self.full_clean()
        super().save(*args, **kwargs)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted thread and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store previous deletion timestamp
        self.last_deletion_at = self.deleted_at

        # Restore
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored', 'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Attempt to restore related objects if they implement restore_instance
            for rel in self._meta.get_fields():
                try:
                    if hasattr(rel, 'get_accessor_name'):
                        manager = getattr(self, rel.get_accessor_name(), None)
                        if manager is None:
                            continue
                        if hasattr(manager, 'filter'):
                            deleted_qs = manager.filter(is_deleted=True)
                            for obj in deleted_qs:
                                if hasattr(obj, 'restore_instance'):
                                    success, _ = obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1
                except Exception:
                    continue

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple Thread instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_count = 0
        for obj in queryset:
            try:
                success, _ = obj.restore_instance(cascade=cascade)
                if success:
                    restored_count += 1
            except Exception:
                continue

        return restored_count, f"Successfully restored {restored_count} {cls.__name__} objects"

    def get_restoration_history(self):
        """Return restoration metadata for this thread."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None,
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at,
                }

        return history


# class CommunityGeoRestriction(models.Model):
#     """
#     Detailed geo-restrictions for communities (cities, regions, timezones).
#     """
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

#     RESTRICTION_TYPES = [
#         ('allow_country', 'Allow Specific Country'),
#         ('block_country', 'Block Specific Country'),
#         ('allow_city', 'Allow Specific City'),
#         ('block_city', 'Block Specific City'),
#         ('allow_region', 'Allow Region/State'),
#         ('block_region', 'Block Region/State'),
#         ('allow_timezone', 'Allow Timezone'),
#         ('block_timezone', 'Block Timezone'),
#         ('ip_range', 'IP Address Range'),
#     ]

#     community = models.ForeignKey(
#         Community,
#         on_delete=models.CASCADE,
#         related_name='geo_restrictions'
#     )
#     restriction_type = models.CharField(
#         max_length=20, choices=RESTRICTION_TYPES
#     )

#     # Location-based restrictions
#     country = models.ForeignKey(
#         'core.Country',
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True
#     )
#     city = models.ForeignKey(
#         'core.City',
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True
#     )
#     region_name = models.CharField(
#         max_length=255,
#         blank=True,
#         help_text="Region/State name for broader geographic restrictions"
#     )

#     # Advanced restrictions
#     timezone_list = models.JSONField(
#         default=list,
#     blank=True,
#     help_text="List of allowed/blocked timezones",
#     validators=[validate_timezones],
#     )
#     ip_range_start = models.GenericIPAddressField(null=True, blank=True)
#     ip_range_end = models.GenericIPAddressField(null=True, blank=True)

#     # Configuration
#     is_active = models.BooleanField(default=True)
#     notes = models.TextField(
#         blank=True, help_text="Admin notes for this restriction"
#     )

#     # Metadata
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     # Soft delete fields
#     is_deleted = models.BooleanField(default=False)
#     deleted_at = models.DateTimeField(null=True, blank=True)
#     is_restored = models.BooleanField(default=False)
#     restored_at = models.DateTimeField(null=True, blank=True)
#     last_deletion_at = models.DateTimeField(null=True, blank=True)

#     def restore_instance(self, cascade=True):
#         """Restore this soft-deleted instance."""
#         from django.utils import timezone

#         if not self.is_deleted:
#             return False, f"{self.__class__.__name__} is not deleted"

#         self.last_deletion_at = self.deleted_at
#         self.is_deleted = False
#         self.deleted_at = None
#         self.is_restored = True
#         self.restored_at = timezone.now()

#         self.save(update_fields=[
#             'is_deleted', 'deleted_at', 'is_restored',
#             'restored_at', 'last_deletion_at'
#         ])

#         return True, f"{self.__class__.__name__} restored successfully"

#     @classmethod
#     def bulk_restore(cls, queryset=None, cascade=True):
#         """Bulk restore multiple instances."""
#         from django.utils import timezone

#         if queryset is None:
#             queryset = cls.objects.filter(is_deleted=True)
#         else:
#             queryset = queryset.filter(is_deleted=True)

#         if not queryset.exists():
#             return 0, "No deleted objects found to restore"

#         restored_count = 0
#         for obj in queryset:
#             try:
#                 success, message = obj.restore_instance(cascade=cascade)
#                 if success:
#                     restored_count += 1
#             except Exception as e:
#                 print(f"Error restoring {obj}: {e}")
#                 continue

#         return restored_count, f"Successfully restored {restored_count} {cls.__name__} objects"

#     def get_restoration_history(self):
#         """Get the restoration history of this object."""
#         history = {
#             'is_currently_deleted': self.is_deleted,
#             'is_restored': self.is_restored,
#             'last_restoration': self.restored_at,
#             'last_deletion': self.last_deletion_at,
#             'deletion_restoration_cycle': None
#         }

#         if self.last_deletion_at and self.restored_at:
#             if self.restored_at > self.last_deletion_at:
#                 history['deletion_restoration_cycle'] = {
#                     'deleted_at': self.last_deletion_at,
#                     'restored_at': self.restored_at,
#                     'cycle_duration': self.restored_at - self.last_deletion_at
#                 }

#         return history

#     class Meta:
#         indexes = [
#             models.Index(fields=['community', 'restriction_type', 'is_active']),
#             models.Index(fields=['country', 'city']),
#         ]
#         ordering = ['created_at']

#     def __str__(self):
#         return f"{self.community.name} - {self.get_restriction_type_display()}"

#     def get_restriction_summary(self):
#         """Get human-readable summary of this restriction."""
#         if self.restriction_type in ['allow_city', 'block_city'] and self.city:
#             action = "Allow" if "allow" in self.restriction_type else "Block"
#             return f"{action} {self.city.name}, {self.city.country.name}"

#         elif self.restriction_type in ['allow_region', 'block_region'] and self.region_name:
#             action = "Allow" if "allow" in self.restriction_type else "Block"
#             country_name = self.country.name if self.country else "Unknown"
#             return f"{action} {self.region_name}, {country_name}"

#         elif self.restriction_type == 'timezone' and self.timezone_list:
#             return f"Timezone restriction: {', '.join(self.timezone_list[:3])}..."

#         elif self.restriction_type == 'ip_range' and self.ip_range_start:
#             if self.ip_range_end:
#                 return f"IP Range: {self.ip_range_start} - {self.ip_range_end}"
#             else:
#                 return f"IP Address: {self.ip_range_start}"

#         return f"{self.get_restriction_type_display()}"

#     def restore_instance(self, cascade=True):
#         """Restore this soft-deleted instance and optionally cascade to related objects."""
#         from django.utils import timezone

#         if not self.is_deleted:
#             return False, f"{self.__class__.__name__} is not deleted"

#         # Store the deletion timestamp before restoring
#         self.last_deletion_at = self.deleted_at

#         # Restore the instance
#         self.is_deleted = False
#         self.deleted_at = None
#         self.is_restored = True
#         self.restored_at = timezone.now()

#         self.save(update_fields=[
#             'is_deleted', 'deleted_at', 'is_restored',
#             'restored_at', 'last_deletion_at'
#         ])

#         restored_count = 1

#         if cascade:
#             # Cascade restore to related objects
#             related_count = self._cascade_restore_related()
#             restored_count += related_count

#         return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

#     def _cascade_restore_related(self):
#         """Cascade restore to related objects."""
#         restored_count = 0

#         # Get all reverse foreign key relationships
#         for rel in self._meta.get_fields():
#             if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
#                 if rel.remote_field and hasattr(rel.remote_field, 'name'):
#                     try:
#                         related_manager = getattr(self, rel.get_accessor_name())

#                         # Find soft-deleted related objects
#                         if hasattr(related_manager, 'filter'):
#                             deleted_related = related_manager.filter(is_deleted=True)

#                             for related_obj in deleted_related:
#                                 if hasattr(related_obj, 'restore_instance'):
#                                     success, message = related_obj.restore_instance(cascade=False)
#                                     if success:
#                                         restored_count += 1

#                     except (AttributeError, Exception):
#                         # Skip relationships that can't be processed
#                         continue

#         # Handle ManyToMany relationships
#         for field in self._meta.many_to_many:
#             try:
#                 related_manager = getattr(self, field.name)
#                 if hasattr(related_manager, 'filter'):
#                     deleted_related = related_manager.filter(is_deleted=True)

#                     for related_obj in deleted_related:
#                         if hasattr(related_obj, 'restore_instance'):
#                             success, message = related_obj.restore_instance(cascade=False)
#                             if success:
#                                 restored_count += 1

#             except (AttributeError, Exception):
#                 continue

#         return restored_count

#     @classmethod
#     def bulk_restore(cls, queryset=None, cascade=True):
#         """Bulk restore multiple instances."""
#         from django.utils import timezone

#         if queryset is None:
#             queryset = cls.objects.filter(is_deleted=True)
#         else:
#             queryset = queryset.filter(is_deleted=True)

#         if not queryset.exists():
#             return 0, "No deleted objects found to restore"

#         restored_objects = []
#         total_restored = 0

#         for obj in queryset:
#             try:
#                 success, message = obj.restore_instance(cascade=cascade)
#                 if success:
#                     restored_objects.append(obj)
#                     total_restored += 1
#             except Exception as e:
#                 print(f"Error restoring {obj}: {e}")
#                 continue

#         return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

#     def get_restoration_history(self):
#         """Get the restoration history of this object."""
#         history = {
#             'is_currently_deleted': self.is_deleted,
#             'is_restored': self.is_restored,
#             'last_restoration': self.restored_at,
#             'last_deletion': self.last_deletion_at,
#             'deletion_restoration_cycle': None
#         }

#         if self.last_deletion_at and self.restored_at:
#             if self.restored_at > self.last_deletion_at:
#                 history['deletion_restoration_cycle'] = {
#                     'deleted_at': self.last_deletion_at,
#                     'restored_at': self.restored_at,
#                     'cycle_duration': self.restored_at - self.last_deletion_at
#                 }

#         return history


class CommunityMembership(models.Model):
    """User membership in communities."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('banned', 'Banned'),
       # ('left', 'Left'),
    ]

    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='community_memberships'
    )
    role = models.ForeignKey(
        'CommunityRole',
        on_delete=models.CASCADE,
        related_name='memberships',
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )

    # Invitation details
    invited_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='community_invited_memberships'
    )
    invited_at = models.DateTimeField(auto_now_add=True)

    # Moderation
    banned_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='community_bans_issued'
    )
    ban_reason = models.TextField(max_length=500, blank=True)
    banned_at = models.DateTimeField(null=True, blank=True)
    ban_expires_at = models.DateTimeField(null=True, blank=True, help_text="When the ban ends and user is reactivated.")

    # Activity tracking
    posts_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    last_active = models.DateTimeField(null=True, blank=True)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    joined_at = models.DateTimeField(auto_now_add=True)
    leaved_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    notifications_enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ('community', 'user')
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['community', 'status', 'role']),
            models.Index(fields=['user', 'status']),
        ]

    def save(self, *args, **kwargs):
        """
        Validate that only users with admin/moderator UserProfile.role
        can be assigned Admin/Moderator roles in communities.
        """
        from django.core.exceptions import ValidationError

        # If a role is assigned, validate user's global role
        if self.role and self.role.name in ['Admin', 'Moderator']:
            user_role = self.user.role if self.user else None

            # Only users with 'admin' or 'moderator' UserProfile.role
            # can be assigned Admin/Moderator roles in communities
            if user_role not in ['admin', 'moderator']:
                raise ValidationError(
                    f"Only users with 'admin' or 'moderator' role can be "
                    f"assigned as community {self.role.name}. "
                    f"User {self.user.user.username} has role '{user_role}'."
                )

        super().save(*args, **kwargs)

    def is_active_member(self):
        """Return True if this membership is active and not soft-deleted."""
        return self.status == 'active' and not self.is_deleted

    def can_remove_member(self, target_membership):
        """Check if this member can remove the target member. Only active members can interact."""
        if not self.is_active_member() or not target_membership.is_active_member():
            return False
        role_name = self.role.name if self.role else None
        target_role_name = target_membership.role.name if target_membership.role else None

        # Admin/Creator role has full permissions
        if role_name == 'Admin':
            return True
        elif role_name == 'Moderator' and target_role_name == 'Member':
            return True
        return False

    def can_moderate_posts(self):
        """Check if this member can moderate posts. Only active members can interact."""
        if not self.is_active_member():
            return False
        role_name = self.role.name if self.role else None
        return role_name in ['Admin', 'Moderator']

    def can_manage_community(self):
        """Check if this member can manage community settings. Only active members can interact."""
        if not self.is_active_member():
            return False
        role_name = self.role.name if self.role else None
        return role_name == 'Admin'

    def can_invite_members(self):
        """Check if this member can invite new members. Only active members can interact."""
        if not self.is_active_member():
            return False
        role_name = self.role.name if self.role else None
        return role_name in ['Admin', 'Moderator']

    def __str__(self):
        return (f"{self.user.user.username} - {self.community.name} "
                f"({self.role.name if self.role else 'No Role'})")


# class CommunityInvitation(models.Model):
#     """Invitations to join communities."""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('accepted', 'Accepted'),
#         ('declined', 'Declined'),
#         ('expired', 'Expired'),
#     ]

#     community = models.ForeignKey(
#         Community,
#         on_delete=models.CASCADE,
#         related_name='invitations'
#     )
#     inviter = models.ForeignKey(
#         UserProfile,
#         on_delete=models.CASCADE,
#         related_name='community_invitations_sent'
#     )
#     invitee = models.ForeignKey(
#         UserProfile,
#         on_delete=models.CASCADE,
#         related_name='community_invitations_received'
#     )
#     message = models.TextField(max_length=500, blank=True)
#     status = models.CharField(
#         max_length=10,
#         choices=STATUS_CHOICES,
#         default='pending'
#     )
#     invite_code = models.CharField(max_length=50, unique=True, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     expires_at = models.DateTimeField()
#     responded_at = models.DateTimeField(null=True, blank=True)
#     is_deleted = models.BooleanField(default=False)
#     deleted_at = models.DateTimeField(null=True, blank=True)
#     # Restoration tracking fields
#     is_restored = models.BooleanField(default=False)
#     restored_at = models.DateTimeField(null=True, blank=True)
#     last_deletion_at = models.DateTimeField(null=True, blank=True)

#     class Meta:
#         unique_together = ('community', 'invitee')
#         ordering = ['-created_at']
#         indexes = [
#             models.Index(fields=['invitee', 'status']),
#             models.Index(fields=['expires_at']),
#         ]

#     def __str__(self):
#         return (f"{self.inviter.user.username} invited "
#                 f"{self.invitee.user.username} to {self.community.name}")
#     def restore_instance(self, cascade=True):
#         """Restore this soft-deleted instance and optionally cascade to related objects."""
#         from django.utils import timezone

#         if not self.is_deleted:
#             return False, f"{self.__class__.__name__} is not deleted"

#         # Store the deletion timestamp before restoring
#         self.last_deletion_at = self.deleted_at

#         # Restore the instance
#         self.is_deleted = False
#         self.deleted_at = None
#         self.is_restored = True
#         self.restored_at = timezone.now()

#         self.save(update_fields=[
#             'is_deleted', 'deleted_at', 'is_restored',
#             'restored_at', 'last_deletion_at'
#         ])

#         restored_count = 1

#         if cascade:
#             # Cascade restore to related objects
#             related_count = self._cascade_restore_related()
#             restored_count += related_count

#         return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

#     def _cascade_restore_related(self):
#         """Cascade restore to related objects."""
#         restored_count = 0

#         # Get all reverse foreign key relationships
#         for rel in self._meta.get_fields():
#             if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
#                 if rel.remote_field and hasattr(rel.remote_field, 'name'):
#                     try:
#                         related_manager = getattr(self, rel.get_accessor_name())

#                         # Find soft-deleted related objects
#                         if hasattr(related_manager, 'filter'):
#                             deleted_related = related_manager.filter(is_deleted=True)

#                             for related_obj in deleted_related:
#                                 if hasattr(related_obj, 'restore_instance'):
#                                     success, message = related_obj.restore_instance(cascade=False)
#                                     if success:
#                                         restored_count += 1

#                     except (AttributeError, Exception):
#                         # Skip relationships that can't be processed
#                         continue

#         # Handle ManyToMany relationships
#         for field in self._meta.many_to_many:
#             try:
#                 related_manager = getattr(self, field.name)
#                 if hasattr(related_manager, 'filter'):
#                     deleted_related = related_manager.filter(is_deleted=True)

#                     for related_obj in deleted_related:
#                         if hasattr(related_obj, 'restore_instance'):
#                             success, message = related_obj.restore_instance(cascade=False)
#                             if success:
#                                 restored_count += 1

#             except (AttributeError, Exception):
#                 continue

#         return restored_count

#     @classmethod
#     def bulk_restore(cls, queryset=None, cascade=True):
#         """Bulk restore multiple instances."""
#         from django.utils import timezone

#         if queryset is None:
#             queryset = cls.objects.filter(is_deleted=True)
#         else:
#             queryset = queryset.filter(is_deleted=True)

#         if not queryset.exists():
#             return 0, "No deleted objects found to restore"

#         restored_objects = []
#         total_restored = 0

#         for obj in queryset:
#             try:
#                 success, message = obj.restore_instance(cascade=cascade)
#                 if success:
#                     restored_objects.append(obj)
#                     total_restored += 1
#             except Exception as e:
#                 print(f"Error restoring {obj}: {e}")
#                 continue

#         return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

#     def get_restoration_history(self):
#         """Get the restoration history of this object."""
#         history = {
#             'is_currently_deleted': self.is_deleted,
#             'is_restored': self.is_restored,
#             'last_restoration': self.restored_at,
#             'last_deletion': self.last_deletion_at,
#             'deletion_restoration_cycle': None
#         }

#         if self.last_deletion_at and self.restored_at:
#             if self.restored_at > self.last_deletion_at:
#                 history['deletion_restoration_cycle'] = {
#                     'deleted_at': self.last_deletion_at,
#                     'restored_at': self.restored_at,
#                     'cycle_duration': self.restored_at - self.last_deletion_at
#                 }

#         return history


# class CommunityJoinRequest(models.Model):
#     """Requests to join restricted communities."""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('approved', 'Approved'),
#         ('rejected', 'Rejected'),
#     ]

#     community = models.ForeignKey(
#         Community,
#         on_delete=models.CASCADE,
#         related_name='join_requests'
#     )
#     user = models.ForeignKey(
#         UserProfile,
#         on_delete=models.CASCADE,
#         related_name='community_join_requests'
#     )
#     message = models.TextField(max_length=500, blank=True)
#     status = models.CharField(
#         max_length=10,
#         choices=STATUS_CHOICES,
#         default='pending'
#     )

#     reviewed_by = models.ForeignKey(
#         UserProfile,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='community_requests_reviewed'
#     )
#     review_message = models.TextField(max_length=500, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)
#     reviewed_at = models.DateTimeField(null=True, blank=True)
#     is_deleted = models.BooleanField(default=False)
#     deleted_at = models.DateTimeField(null=True, blank=True)
#     # Restoration tracking fields
#     is_restored = models.BooleanField(default=False)
#     restored_at = models.DateTimeField(null=True, blank=True)
#     last_deletion_at = models.DateTimeField(null=True, blank=True)
#     # Restoration tracking fields

#     class Meta:
#         """Ensure a user can only have one active join request per community."""
#         unique_together = ('community', 'user')
#         indexes = [
#             models.Index(fields=['community', 'status']),
#             models.Index(fields=['user', 'status']),
#         ]

#     def __str__(self):
#         return (f"{self.user.user.username} requested to join "
#                 f"{self.community.name}")
#     def restore_instance(self, cascade=True):
#         """Restore this soft-deleted instance and optionally cascade to related objects."""
#         from django.utils import timezone

#         if not self.is_deleted:
#             return False, f"{self.__class__.__name__} is not deleted"

#         # Store the deletion timestamp before restoring
#         self.last_deletion_at = self.deleted_at

#         # Restore the instance
#         self.is_deleted = False
#         self.deleted_at = None
#         self.is_restored = True
#         self.restored_at = timezone.now()

#         self.save(update_fields=[
#             'is_deleted', 'deleted_at', 'is_restored',
#             'restored_at', 'last_deletion_at'
#         ])

#         restored_count = 1

#         if cascade:
#             # Cascade restore to related objects
#             related_count = self._cascade_restore_related()
#             restored_count += related_count

#         return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

#     def _cascade_restore_related(self):
#         """Cascade restore to related objects."""
#         restored_count = 0

#         # Get all reverse foreign key relationships
#         for rel in self._meta.get_fields():
#             if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
#                 if rel.remote_field and hasattr(rel.remote_field, 'name'):
#                     try:
#                         related_manager = getattr(self, rel.get_accessor_name())

#                         # Find soft-deleted related objects
#                         if hasattr(related_manager, 'filter'):
#                             deleted_related = related_manager.filter(is_deleted=True)

#                             for related_obj in deleted_related:
#                                 if hasattr(related_obj, 'restore_instance'):
#                                     success, message = related_obj.restore_instance(cascade=False)
#                                     if success:
#                                         restored_count += 1

#                     except (AttributeError, Exception):
#                         # Skip relationships that can't be processed
#                         continue

#         # Handle ManyToMany relationships
#         for field in self._meta.many_to_many:
#             try:
#                 related_manager = getattr(self, field.name)
#                 if hasattr(related_manager, 'filter'):
#                     deleted_related = related_manager.filter(is_deleted=True)

#                     for related_obj in deleted_related:
#                         if hasattr(related_obj, 'restore_instance'):
#                             success, message = related_obj.restore_instance(cascade=False)
#                             if success:
#                                 restored_count += 1

#             except (AttributeError, Exception):
#                 continue

#         return restored_count

#     @classmethod
#     def bulk_restore(cls, queryset=None, cascade=True):
#         """Bulk restore multiple instances."""
#         from django.utils import timezone

#         if queryset is None:
#             queryset = cls.objects.filter(is_deleted=True)
#         else:
#             queryset = queryset.filter(is_deleted=True)

#         if not queryset.exists():
#             return 0, "No deleted objects found to restore"

#         restored_objects = []
#         total_restored = 0

#         for obj in queryset:
#             try:
#                 success, message = obj.restore_instance(cascade=cascade)
#                 if success:
#                     restored_objects.append(obj)
#                     total_restored += 1
#             except Exception as e:
#                 print(f"Error restoring {obj}: {e}")
#                 continue

#         return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

#     def get_restoration_history(self):
#         """Get the restoration history of this object."""
#         history = {
#             'is_currently_deleted': self.is_deleted,
#             'is_restored': self.is_restored,
#             'last_restoration': self.restored_at,
#             'last_deletion': self.last_deletion_at,
#             'deletion_restoration_cycle': None
#         }

#         if self.last_deletion_at and self.restored_at:
#             if self.restored_at > self.last_deletion_at:
#                 history['deletion_restoration_cycle'] = {
#                     'deleted_at': self.last_deletion_at,
#                     'restored_at': self.restored_at,
#                     'cycle_duration': self.restored_at - self.last_deletion_at
#                 }

#         return history


class CommunityRole(models.Model):
    """Roles within communities with specific permissions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Community association
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='roles'
    )
    name = models.CharField(max_length=50)
    permissions = models.JSONField(default=dict)
    color = models.CharField(max_length=7, default='#000000')  # Hex color
    is_default = models.BooleanField(default=False)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta options for the CommunityRole model."""
        unique_together = ('community', 'name')
        ordering = ['name']
        indexes = [
            models.Index(fields=['community', 'is_default']),
        ]

    def __str__(self):
        return f"{self.name} - {self.community.name}"


class CommunityModeration(models.Model):
    """Moderation actions taken in communities."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.is_active:
            exists = CommunityModeration.objects.filter(
                community=self.community,
                moderator=self.moderator,
                action_type=self.action_type,
                target=self.target,
                is_active=True
            )
            if self.pk:
                exists = exists.exclude(pk=self.pk)
            if exists.exists():
                raise ValidationError(
                    "An active moderation action of this type already exists for this moderator and target in this community."
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    ACTION_TYPES = [
        ('warn', 'Warning'),
        ('mute', 'Mute'),
        ('ban', 'Ban'),
        ('kick', 'Kick'),
        ('unban', 'Unban'),
        ('unmute', 'Unmute'),
    ]

    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='moderation_actions'
    )
    moderator = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='moderation_actions_taken'
    )
    target = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='moderation_actions_received'
    )
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    reason = models.TextField(max_length=500)
    details = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['community', 'target', 'is_active']),
            models.Index(fields=['moderator', '-created_at']),
        ]
        # MySQL does not support conditional/partial unique constraints (models.W036).
        # The original intent was to ensure there is at most one *active* moderation
        # action of the same type for a given moderator/target/community. Since
        # conditional constraints aren't supported on MySQL, include `is_active`
        # in the constraint fields. This enforces uniqueness for the tuple
        # (community, moderator, action_type, target, is_active) which allows
        # both an active and an inactive record for the same tuple but prevents
        # multiple active records. The model's `clean()` method additionally
        # protects against duplicates at the application level.
        constraints = [
            models.UniqueConstraint(
                fields=['community', 'moderator', 'action_type', 'target', 'is_active'],
                name='unique_active_moderation_action',
            )
        ]

    def __str__(self):
        return (f"{self.moderator.user.username} {self.action_type} "
                f"{self.target.user.username} in {self.community.name} - Reason: {self.reason}")

    @property
    def duration(self):
        """Return the duration as the difference between created_at and expires_at."""
        if self.expires_at and self.created_at:
            return self.expires_at - self.created_at
        return None


class CommunityAnnouncement(models.Model):
    """Community-specific announcements created by community creators or moderators.

    These are separate from global announcements and can be managed by community
    creators and community moderators (not just app-level admins).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='community_announcements'
    )
    title = models.CharField(max_length=255)
    body_html = models.TextField(
        help_text='Sanitized HTML content for the announcement'
    )
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='community_announcements_created'
    )

    # Display settings
    is_published = models.BooleanField(default=True)
    is_sticky = models.BooleanField(
        default=False,
        help_text='Sticky announcements appear at the top'
    )
    is_important = models.BooleanField(
        default=False,
        help_text='Important announcements are highlighted'
    )
    is_welcome_message = models.BooleanField(
        default=False,
        help_text='Mark this as a welcome message for new community members'
    )

    # Banner display settings
    BANNER_STYLE_CHOICES = [
        ('none', 'Regular Announcement (No Banner)'),
        ('static', 'Static Banner'),
        ('scrolling', 'Scrolling Banner'),
        ('fade', 'Fade In/Out Banner'),
        ('slide', 'Slide Animation Banner'),
    ]
    banner_style = models.CharField(
        max_length=20,
        choices=BANNER_STYLE_CHOICES,
        default='none',
        help_text='Choose how to display this announcement - as regular content or as a banner with different styles'
    )

    # Scheduling
    publish_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Schedule announcement to be published at a specific time'
    )
    expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Automatically unpublish after this date'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-is_sticky', '-is_important', '-created_at']
        indexes = [
            models.Index(fields=['community', '-created_at']),
            models.Index(fields=['community', 'is_published', '-created_at']),
            models.Index(fields=['created_by', '-created_at']),
            models.Index(fields=['is_sticky', 'is_important', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.community.name}"

    def can_user_edit(self, user_profile):
        """Check if a user can edit this announcement.

        Returns True if:
        - User is the creator of the announcement
        - User is the community creator
        - User is a community moderator or admin
        """
        # Creator can always edit
        if self.created_by == user_profile:
            return True

        # Community creator can edit
        if self.community.creator == user_profile:
            return True

        # Check if user is a community moderator/admin
        try:
            membership = CommunityMembership.objects.get(
                community=self.community,
                user=user_profile,
                status='active',
                is_deleted=False
            )

            if membership.role:
                role_name = membership.role.name.lower()
                if role_name in ['admin', 'moderator']:
                    return True
        except CommunityMembership.DoesNotExist:
            pass

        return False

    def is_currently_published(self):
        """Check if announcement is currently published considering scheduling."""
        from django.utils import timezone

        if not self.is_published:
            return False

        now = timezone.now()

        # Check if scheduled for future
        if self.publish_at and now < self.publish_at:
            return False

        # Check if expired
        if self.expires_at and now > self.expires_at:
            return False

        return True

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted announcement."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        self.last_deletion_at = self.deleted_at
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        return True, f"{self.__class__.__name__} restored successfully"

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_count = 0
        for obj in queryset:
            try:
                success, _ = obj.restore_instance(cascade=cascade)
                if success:
                    restored_count += 1
            except Exception:
                continue

        return restored_count, f"Successfully restored {restored_count} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history
    @staticmethod
    def strip_html_tags(html_content):
        """Strip HTML tags from content and return plain text."""
        return strip_all_html(html_content)

    def save(self, *args, **kwargs):
        """Override save to sanitize HTML content."""
        if self.body_html:
            self.body_html = sanitize_announcement_html(self.body_html)
        super().save(*args, **kwargs)

    def clean(self):
        """Validate announcement data."""
        from django.core.exceptions import ValidationError
        super().clean()

        # Banner style validation - only apply length restriction for animated banners
        # 'none' and 'static' have no length restrictions
        if (self.banner_style and
            self.banner_style in ['scrolling', 'fade', 'slide']):
            plain_text = self.strip_html_tags(self.body_html)
            if len(plain_text) > 180:
                raise ValidationError({
                    'banner_style': (
                        f'Animated banner styles work best with shorter messages. '
                        f'Please use "Regular Announcement" or "Static Banner" for '
                        f'longer content, or shorten your message to 180 characters '
                        f'or less. Current message is {len(plain_text)} characters.'
                    )
                })
