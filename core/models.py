"""Core models for the Equipment Database Social Media Platform.

This module contains base models and utilities used across the application.
"""

import uuid
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ValidationError
from .html_sanitizer import sanitize_announcement_html, strip_all_html


# =============================================================================
# CUSTOM MANAGERS FOR COMMUNITY CONTEXT
# =============================================================================

class PostManager(models.Manager):
    """Custom manager for Post model with community filtering."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def community_posts(self, community=None):
        """Get posts that belong to a specific community or all community posts."""
        if community:
            return self.filter(community=community)
        return self.filter(community__isnull=False)

    def general_posts(self):
        """Get posts that don't belong to any community."""
        return self.filter(community__isnull=True)

    def by_context(self, context_type='all', community=None):
        """Get posts by context type."""
        if context_type == 'community':
            return self.community_posts(community)
        elif context_type == 'general':
            return self.general_posts()
        return self.all()


class CommentManager(models.Manager):
    """Custom manager for Comment model with community filtering."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def community_comments(self, community=None):
        """Get comments from community posts."""
        if community:
            return self.filter(post__community=community)
        return self.filter(post__community__isnull=False)

    def general_comments(self):
        """Get comments from non-community posts."""
        return self.filter(post__community__isnull=True)

    def by_context(self, context_type='all', community=None):
        """Get comments by context type."""
        if context_type == 'community':
            return self.community_comments(community)
        elif context_type == 'general':
            return self.general_comments()
        return self.all()


class MentionManager(models.Manager):
    """Custom manager for Mention model with community filtering."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def community_mentions(self, community=None):
        """Get mentions from community contexts."""
        if community:
            return self.filter(
                models.Q(post__community=community) |
                models.Q(comment__post__community=community)
            )
        return self.filter(
            models.Q(post__community__isnull=False) |
            models.Q(comment__post__community__isnull=False)
        )

    def general_mentions(self):
        """Get mentions from non-community contexts."""
        return self.filter(
            models.Q(post__community__isnull=True) |
            models.Q(comment__post__community__isnull=True)
        )

    def by_context(self, context_type='all', community=None):
        """Get mentions by context type."""
        if context_type == 'community':
            return self.community_mentions(community)
        elif context_type == 'general':
            return self.general_mentions()
        return self.all()


# =============================================================================
# LOCATION MODELS
# =============================================================================

class Country(models.Model):
    """Country model with ISO codes and optional boundary geometry."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    iso3 = models.CharField(max_length=3, unique=True, db_index=True)  # BEN, CAN
    iso2 = models.CharField(max_length=2, unique=True, db_index=True)  # BJ, CA
    name = models.CharField(max_length=100, db_index=True)
    code = models.IntegerField(null=True, blank=True, db_index=True)

    # Default administrative level for this country's primary divisions
    # e.g., 3 for Benin communes, 4 for Canada municipalities
    default_admin_level = models.IntegerField(
        null=True, blank=True,
        help_text="Primary admin level (3=communes, 4=municipalities)"
    )

    # Note: Country geometry is now handled by AdministrativeDivision
    # at admin_level=0. This eliminates redundancy and provides unified
    # geometry management.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ['name']
        indexes = [
            models.Index(fields=['iso3', 'name']),
        ]

    def __str__(self) -> str:
        return str(self.name)

    def get_default_divisions(self):
        """Get divisions at the default level for this country."""
        if self.default_admin_level is None:
            return None

        # Import here to avoid circular import
        return self.administrativedivision_set.filter(
            admin_level=self.default_admin_level
        )

    def get_default_division_name(self):
        """Get the actual boundary type name used at the default level."""
        if self.default_admin_level is None:
            return None

        # Get the most common boundary_type at the default level
        divisions = self.administrativedivision_set.filter(
            admin_level=self.default_admin_level
        ).values_list('boundary_type', flat=True)

        if divisions:
            # Return the most common boundary type, or the first one if tied
            from collections import Counter
            counter = Counter(divisions)
            return counter.most_common(1)[0][0] if counter else None

        return f'Level {self.default_admin_level}'

    def get_boundary_types_by_level(self):
        """Get a dict of admin_level -> most common boundary_type."""
        from collections import Counter

        result = {}
        divisions = self.administrativedivision_set.values(
            'admin_level', 'boundary_type'
        )

        # Group by admin_level
        level_types = {}
        for div in divisions:
            level = div['admin_level']
            boundary_type = div['boundary_type']

            if level not in level_types:
                level_types[level] = []
            level_types[level].append(boundary_type)

        # Get most common type for each level
        for level, types in level_types.items():
            counter = Counter(types)
            most_common = counter.most_common(1)[0][0] if counter else None
            if most_common:
                result[level] = most_common

        return result


# City model removed - cities are now represented as AdministrativeDivision records
# at appropriate admin levels (level 3 for municipalities, etc.)


class AdministrativeDivision(models.Model):
    """
    Unified administrative division model supporting multiple countries and admin levels.
    Handles different geometry types (polygons, lines, points) in separate fields for optimal queries.
    """

    # Administrative levels - standardized across countries
    ADMIN_LEVELS = (
        (0, 'Country'),                        # Country level (ADM0)
        (1, 'State/Province/Department'),      # Benin: Department, Quebec: Province
        (2, 'Region/Prefecture/MRC'),          # Benin: Prefecture, Quebec: MRC
        (3, 'Municipality/Commune'),           # Benin: Commune, Quebec: Municipality
        (4, 'Arrondissement/District'),        # Both have arrondissements
        (5, 'Village/Locality'),               # Local subdivisions
    )

    # Point types for administrative points (city halls, offices, etc.)
    POINT_TYPES = (
        ('city_hall', 'City Hall/Hotel de Ville'),
        ('prefecture', 'Prefecture Headquarters'),
        ('office', 'Administrative Office'),
        ('bureau', 'Bureau/Sub-office'),
        ('center', 'Administrative Center'),
        ('other', 'Other'),
    )

    # Core identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, db_index=True)
    admin_level = models.IntegerField(choices=ADMIN_LEVELS, db_index=True)
    name = models.CharField(max_length=200, db_index=True)
    local_name = models.CharField(max_length=200, blank=True, null=True)

    # Administrative codes - flexible for different systems
    admin_code = models.CharField(max_length=50, blank=True, db_index=True)  # General admin code
    local_code = models.CharField(max_length=50, blank=True)  # Country-specific codes

    # Hierarchy - self-referencing for parent-child relationships
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                              related_name='children', db_index=True)

    # SEPARATE GEOMETRY FIELDS for different types - enables one record per division
    area_geometry = gis_models.MultiPolygonField(null=True, blank=True, spatial_index=True)  # Polygons
    boundary_geometry = gis_models.MultiLineStringField(null=True, blank=True, spatial_index=True)  # LineStrings
    point_geometry = gis_models.PointField(null=True, blank=True, spatial_index=True)  # Points

    # Pre-computed derived fields (auto-calculated from area_geometry)
    centroid = gis_models.PointField(null=True, blank=True, spatial_index=True)  # Auto-computed centroid
    area_sqkm = models.FloatField(null=True, blank=True)  # Auto-computed area

    # Point and boundary type classification (when applicable)
    point_type = models.CharField(max_length=20, choices=POINT_TYPES, blank=True)
    boundary_type = models.CharField(max_length=50, blank=True,
                                   help_text="Dynamic boundary type (country-specific)")

    # Metadata
    population = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)

    # Flexible attributes for country-specific data
    attributes = models.JSONField(default=dict, blank=True)  # Store country-specific fields

    # Data source tracking
    data_source = models.CharField(max_length=100, blank=True,
                                  help_text="Source of the data (e.g., 'Benin SALB 2019')")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Administrative Divisions"
        ordering = ['country__name', 'admin_level', 'name']
        indexes = [
            models.Index(fields=['country', 'admin_level']),
            models.Index(fields=['country', 'admin_level', 'name']),
            models.Index(fields=['parent', 'admin_level']),
            models.Index(fields=['admin_code', 'country']),
            models.Index(fields=['point_type']),
            models.Index(fields=['boundary_type']),
            # Spatial indexes handled by spatial_index=True on geometry fields
        ]
        unique_together = [
            ('country', 'admin_level', 'admin_code'),  # Unique codes within country/level
        ]

    def __str__(self):
        level_name = dict(self.ADMIN_LEVELS).get(self.admin_level, 'Unknown')
        if self.parent:
            return f'{self.name} ({level_name}) - {self.parent.name}'
        return f'{self.name} ({level_name}), {self.country.name}'

    @property
    def full_path(self):
        """Return full administrative path (e.g., 'Benin > Alibori > Banikoara')"""
        path = []
        current = self
        while current:
            path.append(current.name)
            current = current.parent
        path.append(self.country.name)  # Add country at the top
        return ' > '.join(reversed(path))

    @property
    def admin_level_name(self):
        """Return human-readable admin level name"""
        return dict(self.ADMIN_LEVELS).get(self.admin_level, 'Unknown')

    def save(self, *args, **kwargs):
        # Auto-compute centroid and area from area_geometry
        if self.area_geometry:
            self.centroid = self.area_geometry.centroid
            # Transform to Web Mercator for area calculation, then convert to km²
            area_m2 = self.area_geometry.transform(3857, clone=True).area
            self.area_sqkm = area_m2 / 1_000_000  # Convert to km²

        # Auto-generate boundary geometry from area geometry if not already set
        auto_generate_boundary = kwargs.pop('auto_generate_boundary', True)
        if auto_generate_boundary and self.area_geometry and not self.boundary_geometry:
            self.generate_boundary_from_area()

        super().save(*args, **kwargs)

    def has_area(self):
        """Check if this division has area geometry"""
        return bool(self.area_geometry)

    def has_boundaries(self):
        """Check if this division has boundary geometry"""
        return bool(self.boundary_geometry)

    def has_point(self):
        """Check if this division has point geometry"""
        return bool(self.point_geometry)

    def generate_boundary_from_area(self):
        """Generate boundary geometry from area geometry (polygon edges)"""
        if not self.area_geometry:
            return False

        try:
            from django.contrib.gis.geos import MultiLineString, LineString

            # Extract boundary from polygon(s)
            if hasattr(self.area_geometry, '__iter__'):
                # MultiPolygon - extract boundary from each polygon
                linestrings = []
                for polygon in self.area_geometry:
                    boundary = polygon.boundary
                    if isinstance(boundary, LineString):
                        linestrings.append(boundary)
                    elif hasattr(boundary, '__iter__'):
                        linestrings.extend(boundary)

                if linestrings:
                    self.boundary_geometry = MultiLineString(linestrings)
            else:
                # Single polygon
                boundary = self.area_geometry.boundary
                if isinstance(boundary, LineString):
                    self.boundary_geometry = MultiLineString([boundary])
                else:
                    self.boundary_geometry = MultiLineString(boundary)

            return True
        except Exception as e:
            print(f"Error generating boundary for {self.name}: {e}")
            return False

    def regenerate_boundary(self):
        """Force regeneration of boundary geometry from area geometry"""
        if self.area_geometry:
            self.boundary_geometry = None  # Clear existing
            self.generate_boundary_from_area()
            self.save(auto_generate_boundary=False)  # Avoid recursion
            return True
        return False

    def get_geometry_types(self):
        """Return list of available geometry types for this division"""
        types = []
        if self.area_geometry:
            types.append('area')
        if self.boundary_geometry:
            types.append('boundary')
        if self.point_geometry:
            types.append('point')
        return types


# =============================================================================
# BASE ABSTRACT MODELS
# =============================================================================

class BaseModel(models.Model):
    """Abstract base model with common fields."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
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



class SoftDeleteModel(BaseModel):
    """Abstract model with soft delete functionality."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Override save to automatically set deleted_at when is_deleted changes."""
        from django.utils import timezone

        # Store original state for comparison
        original_is_deleted = False
        if self.pk:
            try:
                # Get the original object from database
                original = type(self).objects.get(pk=self.pk)
                original_is_deleted = original.is_deleted
            except type(self).DoesNotExist:
                # Object doesn't exist yet, treat as new
                pass

        # Handle deletion state changes
        if not original_is_deleted and self.is_deleted:
            # Object being soft deleted
            self.deleted_at = timezone.now()
        elif original_is_deleted and not self.is_deleted:
            # Object being restored
            self.deleted_at = None
        elif not self.pk and self.is_deleted:
            # New object being created as deleted
            self.deleted_at = timezone.now()

        super().save(*args, **kwargs)

    def soft_delete(self):
        """Soft delete the object."""
        self.is_deleted = True
        self.save()

    def restore(self):
        """Restore a soft-deleted object."""
        self.is_deleted = False
        self.save()


class TimestampedModel(models.Model):
    """Abstract model with timestamp fields."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Announcement(models.Model):
    """Global announcements created by app-level moderators/admins.

    These are system-wide announcements that can be displayed across the app.
    For community-specific announcements, use communities.CommunityAnnouncement.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True)
    body_html = models.TextField(blank=True, help_text='Sanitized HTML for announcement body')
    # Announcement source and permissions
    is_system_generated = models.BooleanField(
        default=False,
        help_text='True if generated automatically by the system (e.g., welcome messages)'
    )
    created_by = models.ForeignKey(
        'accounts.UserProfile', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='global_announcements_created',
        help_text='User who created this announcement (null for system-generated)'
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
        help_text='Mark this as a welcome message for new users'
    )

    # Display settings
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

    # Targeting options for global announcements
    target_specific_user = models.ForeignKey(
        'accounts.UserProfile', on_delete=models.CASCADE,
        null=True, blank=True, related_name='targeted_announcements',
        help_text='Target a specific user (overrides other targeting options)'
    )
    target_community = models.ForeignKey(
        'communities.Community', on_delete=models.CASCADE,
        null=True, blank=True, related_name='targeted_global_announcements',
        help_text='Target all members of a specific community'
    )
    target_user_roles = models.JSONField(
        default=list, blank=True,
        help_text='Target specific user roles (empty = all users)'
    )
    target_countries = models.JSONField(
        default=list, blank=True,
        help_text='Target specific countries (empty = all countries)'
    )
    target_timezones = models.JSONField(
        default=list, blank=True,
        help_text='Target specific timezones (empty = all timezones)'
    )
    target_cities = models.JSONField(
        default=list, blank=True,
        help_text='Target specific cities (empty = all cities)'
    )
    target_regions = models.JSONField(
        default=list, blank=True,
        help_text='Target specific regions/states (empty = all regions)'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_sticky', '-created_at']

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

    def is_targeted_to_user(self, user_profile):
        """Check if this announcement is targeted to a specific user."""
        # If targeting a specific user, only show to that user
        if self.target_specific_user:
            return self.target_specific_user == user_profile

        # If targeting a specific community, check if user is a member
        if self.target_community:
            from communities.models import CommunityMembership
            return CommunityMembership.objects.filter(
                community=self.target_community,
                user=user_profile,
                status='active',
                is_deleted=False
            ).exists()

        # Check role targeting
        if self.target_user_roles:
            if user_profile.role not in self.target_user_roles:
                return False

        # Check geographic targeting
        if self.target_countries:
            if user_profile.country not in self.target_countries:
                return False

        if self.target_timezones:
            if user_profile.timezone not in self.target_timezones:
                return False

        if self.target_cities:
            if user_profile.city not in self.target_cities:
                return False

        if self.target_regions:
            if user_profile.region not in self.target_regions:
                return False

        # If no targeting criteria exclude the user, show the announcement
        return True

    @classmethod
    def create_system_announcement(cls, title, body_html, **targeting_kwargs):
        """Create a system-generated announcement with targeting options."""
        announcement = cls(
            title=title,
            body_html=body_html,
            is_system_generated=True,
            created_by=None,  # System-generated, no user
            **targeting_kwargs
        )
        announcement.full_clean()
        announcement.save()
        return announcement

    @classmethod
    def create_welcome_message(cls, title, body_html, target_user=None):
        """Create a system-generated welcome message for new users."""
        return cls.create_system_announcement(
            title=title,
            body_html=body_html,
            is_welcome_message=True,
            target_specific_user=target_user
        )

    def can_user_edit(self, user_profile):
        """Check if a user can edit this announcement."""
        # System-generated announcements can't be edited by users
        if self.is_system_generated:
            return False

        # Only admins and moderators can edit global announcements
        return user_profile.role in ['admin', 'moderator']

    @classmethod
    def get_announcements_for_user(cls, user_profile):
        """Get all announcements that should be shown to a specific user."""
        announcements = cls.objects.filter(is_published=True)
        targeted_announcements = []

        for announcement in announcements:
            if announcement.is_targeted_to_user(user_profile):
                targeted_announcements.append(announcement)

        return targeted_announcements

    def __str__(self):
        return f"{self.title or 'Global Announcement'}"
