"""User account models for the Database Social Media Platform.

This module contains user profile and account-related models.
"""

from pyexpat import model
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import AdministrativeDivision

# Utilities
import uuid
import os

from django.core.exceptions import ValidationError
from django.conf import settings
import mimetypes
import subprocess
import tempfile
import shutil

# Optional libmagic support
try:
    import magic
except Exception:
    magic = None

# Signals for keeping UserProfile.role in sync with extension profiles
from django.db.models.signals import post_delete
from django.dispatch import receiver


class VerificationCode(models.Model):
    """Verification code for user accounts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Link to the user profile
    # Using OneToOneField to ensure one code per user
    # This assumes that each user has a profile created automatically
    # when the User object is created.
    user = models.OneToOneField(
        'UserProfile',
        on_delete=models.CASCADE,
        related_name='verification_code'
    )

    code = models.CharField(max_length=8, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()


    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        import os
        from datetime import timedelta

        # OPTIMIZATION: Minimal save method for speed
        update_expiry = False
        if self.pk:
            # Existing code: only update expires_at if code value changed (resend)
            try:
                old = VerificationCode.objects.get(pk=self.pk)
                if old.code != self.code:
                    update_expiry = True
            except VerificationCode.DoesNotExist:
                update_expiry = True
        else:
            # New code: always set expires_at
            update_expiry = True
        if update_expiry:
            timeout_minutes = int(os.environ.get('VERIFICATION_CODE_TIMEOUT_MINUTES', 5))
            self.expires_at = timezone.now() + timedelta(minutes=timeout_minutes)
        super().save(*args, **kwargs)

        # Always check verification period after save
        if hasattr(self, 'user') and self.user:
            self.user.sync_verification_status()

    def mark_as_used(self):
        """Mark verification code as used and verify the user profile."""
        if self.is_used:
            return False  # Already used

        if not self.is_active:
            return False  # Expired or inactive

        # Mark code as used
        self.is_used = True
        self.save()

        # Automatically verify the user and set verification timestamp
        if self.user:
            self.user.is_verified = True
            self.user.last_verified_at = timezone.now()

            # Increment registration_index only on first successful verification
            if self.user.registration_index == 0:
                self.user.assign_registration_index()

            self.user.save(update_fields=['is_verified', 'last_verified_at', 'registration_index'])

        return True

    @property
    def is_active(self):
        from django.utils import timezone
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"Verification code for {self.user.email}"


class UserProfile(models.Model):
    """Extended user model with comprehensive profile data."""

    ROLES = (
        # ('owner', 'Owner'),
        ('normal', 'Normal User'),
        ('commercial', 'Commercial'),
        ('professional', 'Professional'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLES,
        blank=True,
        null=True,
        default='normal'
    )
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    # Required contact and identity fields
    phone_number = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )
    # Legacy/optional image field
    # cover_photo = models.ImageField(
    #     upload_to='covers/',
    #     blank=True,
    #     null=True
    # )

    # New: support an image OR a short video for the user's cover media
    cover_media = models.FileField(
        upload_to='covers/',
        blank=True,
        null=True,
        help_text='Image or short video file used as user cover.'
    )
    cover_media_type = models.CharField(
        max_length=10,
        choices=[('image', 'Image'), ('video', 'Video')],
        default='image'
    )
    administrative_division = models.ForeignKey(
        AdministrativeDivision,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='User administrative division (city/municipality)'
    )

    # Privacy settings
    is_private = models.BooleanField(default=False)
    show_email = models.BooleanField(default=False)
    show_phone = models.BooleanField(default=False)
    show_location = models.BooleanField(default=True)
    # Advertising preference: allow targeted/promotional content
    allow_advertising = models.BooleanField(
        default=False,
        help_text='If True the user allows advertising/marketing content to be shown.'
    )

    # Terms and conditions acceptance
    accept_terms = models.BooleanField(
        default=False,
        help_text='User has accepted terms and conditions during registration'
    )

    # Account status
    is_verified = models.BooleanField(default=False)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    is_suspended = models.BooleanField(default=False)
    suspended_at = models.DateTimeField(null=True, blank=True)
    suspension_reason = models.TextField(blank=True)

    # Analytics
    follower_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    posts_count = models.PositiveIntegerField(default=0)
    # Cached counters for badge criteria (Option A)
    polls_created_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of polls created'
    )
    poll_votes_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of poll votes cast'
    )
    # Future extensible counters
    likes_given_count = models.PositiveIntegerField(
        default=0,
        help_text='Likes the user has given'
    )
    comments_made_count = models.PositiveIntegerField(
        default=0,
        help_text='Comments the user has made'
    )
    reposts_count = models.PositiveIntegerField(
        default=0,
        help_text='Feed reposts performed'
    )
    shares_sent_count = models.PositiveIntegerField(
        default=0,
        help_text='Private direct shares sent'
    )
    shares_received_count = models.PositiveIntegerField(
        default=0,
        help_text='Private direct shares received'
    )

    best_comments_count = models.PositiveIntegerField(
        default=0,
        help_text='Comments marked as best'
    )
    communities_joined_count = models.PositiveIntegerField(
        default=0,
        help_text='Active communities this user has joined'
    )
    registration_index = models.PositiveIntegerField(
        default=0,
        help_text='Sequential index assigned at registration'
    )

    def assign_registration_index(self):
        """Assign the next sequential registration index."""
        from django.db import transaction

        # Don't reassign if already has an index
        if self.registration_index is not None and self.registration_index > 0:
            return

        with transaction.atomic():
            # Get the highest existing registration_index
            max_index = UserProfile.objects.aggregate(
                max_index=models.Max('registration_index')
            )['max_index'] or 0

            # Assign next index
            self.registration_index = max_index + 1
            # Save the updated registration_index
            self.save(update_fields=['registration_index'])

            # NOTE: Badge evaluation is now handled separately in async task

    def sync_all_counters(self):
        """Synchronize all counters with actual model counts."""
        self.sync_posts_count()
        self.sync_followers_following_count()
        self.sync_likes_given_count()
        self.sync_comments_made_count()
        self.sync_reposts_count()
        self.sync_shares_count()
        self.sync_polls_and_votes_count()
        self.sync_communities_joined_count()

        # Save all updated counters
        self.save(update_fields=[
            'posts_count', 'follower_count', 'following_count',
            'likes_given_count', 'comments_made_count', 'reposts_count',
            'shares_sent_count', 'shares_received_count',
            'poll_votes_count', 'communities_joined_count'
        ])

    def sync_posts_count(self):
        """Sync posts_count with actual Post model count."""
        from content.models import Post
        self.posts_count = Post.objects.filter(
            author=self, is_deleted=False
        ).count()

    def sync_followers_following_count(self):
        """Sync follower and following counts."""
        from accounts.models import Follow
        self.follower_count = Follow.objects.filter(
            followed=self, status='approved', is_deleted=False
        ).count()
        self.following_count = Follow.objects.filter(
            follower=self, status='approved', is_deleted=False
        ).count()

    def sync_likes_given_count(self):
        """Sync likes_given_count with Like model."""
        from content.models import Like
        self.likes_given_count = Like.objects.filter(
            user=self, is_deleted=False
        ).count()

    def sync_comments_made_count(self):
        """Sync comments_made_count with Comment model."""
        from content.models import Comment
        self.comments_made_count = Comment.objects.filter(
            author=self, is_deleted=False
        ).count()

    def sync_reposts_count(self):
        """Sync reposts_count with repost-type posts."""
        from content.models import Post
        repost_types = ['repost', 'repost_with_media', 'repost_quote', 'repost_remix']
        self.reposts_count = Post.objects.filter(
            author=self, post_type__in=repost_types, is_deleted=False
        ).count()

    def sync_shares_count(self):
        """Sync shares sent and received counts."""
        from content.models import DirectShare, DirectShareRecipient
        self.shares_sent_count = DirectShare.objects.filter(
            sender=self, is_deleted=False
        ).count()
        self.shares_received_count = DirectShareRecipient.objects.filter(
            recipient=self, is_deleted=False
        ).count()


    def sync_polls_and_votes_count(self):
        """Sync poll creation and voting counts."""
        from polls.models import Poll, PollVote
        from content.models import Post

        # Count polls created (via posts authored by user)
        self.polls_created_count = Poll.objects.filter(
            post__author=self, is_deleted=False
        ).count()

        # Count poll votes cast
        self.poll_votes_count = PollVote.objects.filter(
            voter__profile=self, is_deleted=False
        ).count()

    def sync_communities_joined_count(self):
        """Sync communities_joined_count with CommunityMembership."""
        try:
            from communities.models import CommunityMembership
            self.communities_joined_count = CommunityMembership.objects.filter(
                user=self, is_deleted=False
            ).count()
        except ImportError:
            # communities app might not be available
            pass

    def increment_counter(self, counter_name, amount=1):
        """Safely increment a specific counter."""
        if hasattr(self, counter_name):
            current_value = getattr(self, counter_name, 0)
            setattr(self, counter_name, current_value + amount)
            self.save(update_fields=[counter_name])

    def decrement_counter(self, counter_name, amount=1):
        """Safely decrement a specific counter (minimum 0)."""
        if hasattr(self, counter_name):
            current_value = getattr(self, counter_name, 0)
            new_value = max(0, current_value - amount)
            setattr(self, counter_name, new_value)
            self.save(update_fields=[counter_name])

    def sync_verification_status(self):
        """Synchronize is_verified and last_verified_at with VerificationCode usage and recency."""
        import os
        from datetime import timedelta
        # Get allowed days from env, default 7
        allowed_days = int(os.environ.get('VERIFICATION_VALID_DAYS', 7))
        now = timezone.now()
        vcode = getattr(self, 'verification_code', None)
        if vcode and vcode.is_used:
            self.last_verified_at = vcode.updated_at
        # Check if last_verified_at is recent
        if self.last_verified_at and (now - self.last_verified_at).days <= allowed_days:
            self.is_verified = True
        else:
            self.is_verified = False
        self.save(update_fields=['is_verified', 'last_verified_at'])

    @property
    def is_recently_verified(self):
        import os
        from datetime import timedelta
        allowed_days = int(os.environ.get('VERIFICATION_VALID_DAYS', 365))
        if not self.last_verified_at:
            return False
        now = timezone.now()
        return (now - self.last_verified_at).days <= allowed_days

    # Recommendation factors
    engagement_score = models.FloatField(default=0.0)
    content_quality_score = models.FloatField(default=0.0)
    interaction_frequency = models.FloatField(default=0.0)

    # content_preferences = models.JSONField(default=dict, blank=True, null=True)

    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['role']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_suspended']),
            models.Index(fields=['administrative_division']),
            models.Index(fields=['-last_active']),
            models.Index(fields=['polls_created_count']),
            models.Index(fields=['poll_votes_count']),
            models.Index(fields=['reposts_count']),
            models.Index(fields=['shares_sent_count']),
            models.Index(fields=['shares_received_count']),
            models.Index(fields=['best_comments_count']),
            models.Index(fields=['communities_joined_count']),
            models.Index(fields=['registration_index']),
        ]

    def __str__(self):
        return self.user.username

    @property
    def location(self):
        """Return the complete location as 'Division, Country'."""
        if self.administrative_division and self.administrative_division.country:
            return f"{self.administrative_division.name}, {self.administrative_division.country.name}"
        return None

    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.user.first_name} {self.user.last_name}".strip()

    @property
    def display_name(self):
        """Return display name (full name if available, otherwise username)."""
        full_name = self.full_name
        return full_name if full_name else self.user.username

    @property
    def is_cover_video(self):
        """Return True if the current cover_media is a video file."""
        return bool(self.cover_media and self.cover_media_type == 'video')

    def _validate_cover_media(self):
        """Basic validation for cover media by extension and size."""
        if not self.cover_media:
            return
        # Determine MIME type using libmagic if available, otherwise fallback
        filename = getattr(self.cover_media, 'name', '') or ''

        mime = None
        try:
            # If FileField exposes a file-like object
            file_obj = getattr(self.cover_media, 'file', None)
            if magic and file_obj is not None:
                # Read a small chunk
                try:
                    file_obj.seek(0)
                    blob = file_obj.read(4096)
                    file_obj.seek(0)
                    mime = magic.from_buffer(blob, mime=True)
                except Exception:
                    mime = None
        except Exception:
            mime = None

        if not mime:
            # Fallback to mimetypes based on filename
            mime, _ = mimetypes.guess_type(filename)

        if not mime:
            raise ValidationError('Could not determine file MIME type for cover media.')

        # Size limits (bytes)
        max_image_bytes = int(getattr(settings, 'PROFILE_COVER_IMAGE_MAX_BYTES', os.environ.get('PROFILE_COVER_IMAGE_MAX_BYTES', 5 * 1024 * 1024)))
        max_video_bytes = int(getattr(settings, 'PROFILE_COVER_VIDEO_MAX_BYTES', os.environ.get('PROFILE_COVER_VIDEO_MAX_BYTES', 15 * 1024 * 1024)))

        # Validate by MIME
        if mime.startswith('image/'):
            expected_type = 'image'
            max_bytes = max_image_bytes
        elif mime.startswith('video/'):
            expected_type = 'video'
            max_bytes = max_video_bytes
        else:
            raise ValidationError('Unsupported cover_media MIME type.')

        # Size check
        try:
            size = getattr(self.cover_media, 'size', None)
        except Exception:
            size = None

        if size and size > max_bytes:
            raise ValidationError(f'Cover media exceeds max allowed size ({max_bytes} bytes).')

        # If video, check duration using ffprobe when available
        if expected_type == 'video':
            # Get configured max duration (seconds)
            max_duration = int(getattr(settings, 'COVER_VIDEO_MAX_DURATION_SECONDS', os.environ.get('COVER_VIDEO_MAX_DURATION_SECONDS', 60)))

            # Try to obtain a filesystem path for ffprobe; otherwise write a temp file
            file_path = None
            try:
                # FieldFile may have temporary_file_path (uploaded to disk by storage)
                file_path = self.cover_media.temporary_file_path()
            except Exception:
                file_path = None

            temp_file = None
            try:
                if not file_path:
                    # Write to temp file
                    temp = tempfile.NamedTemporaryFile(delete=False)
                    temp_file = temp.name
                    # ensure file pointer at start
                    f = getattr(self.cover_media, 'file', None)
                    if f is not None:
                        try:
                            f.seek(0)
                        except Exception:
                            pass
                        shutil.copyfileobj(f, temp)
                    else:
                        # Fallback: read from FieldFile
                        temp.write(self.cover_media.read())
                    temp.close()
                    file_path = temp_file

                # Run ffprobe to get duration
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

        # Sync declared type
        self.cover_media_type = expected_type

    def save(self, *args, **kwargs):
        # Validate cover media before saving
        try:
            self._validate_cover_media()
        except ValidationError:
            # Re-raise so callers can see validation errors
            raise
        except Exception:
            # Silently ignore unexpected validation problems
            pass

        super().save(*args, **kwargs)

    def restore_user(self):
        """Restore a soft-deleted user and track restoration."""
        if not self.is_deleted:
            return False, "User is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the user
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        return True, "User restored successfully"

    def restore_instance(self, cascade=True):
        """Enhanced restoration method with cascading support."""
        return self.restore_user()  # Use existing method for now

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Restore related objects
        related_objects = [
            ('verification_code', None),  # One-to-one
            ('professional_profile', None),  # One-to-one
            ('settings', None),  # One-to-one
            ('following', None),  # Following relationships
            ('followers', None),  # Follower relationships
            ('blocking', None),  # Blocking relationships
            ('sessions', None),  # User sessions
            ('account_events', None),  # Account events
            ('badges', None),  # User badges
        ]

        for relation_name, _ in related_objects:
            try:
                if hasattr(self, relation_name):
                    related_manager = getattr(self, relation_name)

                    if hasattr(related_manager, 'filter'):
                        # Handle reverse foreign keys (one-to-many)
                        deleted_related = related_manager.filter(is_deleted=True)
                        for related_obj in deleted_related:
                            if hasattr(related_obj, 'restore_instance'):
                                success, message = related_obj.restore_instance(cascade=False)
                                if success:
                                    restored_count += 1
                    elif hasattr(related_manager, 'is_deleted') and related_manager.is_deleted:
                        # Handle one-to-one relationships
                        if hasattr(related_manager, 'restore_instance'):
                            success, message = related_manager.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple user profiles."""
        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted user profiles found to restore"

        restored_count = 0

        for profile in queryset:
            try:
                success, message = profile.restore_instance(cascade=cascade)
                if success:
                    restored_count += 1
            except Exception as e:
                print(f"Error restoring {profile}: {e}")
                continue

        return restored_count, f"Successfully restored {restored_count} UserProfile objects"

    def get_restoration_history(self):
        """Get the restoration history of this user profile."""
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


class ProfessionalProfile(models.Model):
    """Professional profile for users with professional roles."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="professional_profile"
    )

    description = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    business_address = models.CharField(max_length=255, blank=True)

    # Professional details
    company_name = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    years_experience = models.PositiveIntegerField(null=True, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    services_offered = models.JSONField(default=list, blank=True)

    # Verification
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    verification_documents = models.JSONField(default=list, blank=True)
    trust_score = models.FloatField(default=0.0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['profile']),
            models.Index(fields=['is_verified']),
        ]

    def __str__(self):
        return f"{self.profile.user.username} - Pro"

    def save(self, *args, **kwargs):
        """Ensure the parent UserProfile.role is set to 'professional' when this profile exists."""
        super().save(*args, **kwargs)
        try:
            if self.profile and self.profile.role != 'professional':
                self.profile.role = 'professional'
                self.profile.save(update_fields=['role'])
        except Exception:
            pass


class CommercialProfile(models.Model):
    """Commercial profile for users with commercial/business roles."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="commercial_profile"
    )

    # Business Information
    business_name = models.CharField(max_length=200)
    business_type = models.CharField(
        max_length=100,
        choices=[
            ('retailer', 'Retailer'),
            ('manufacturer', 'Manufacturer'),
            ('distributor', 'Distributor'),
            ('service_provider', 'Service Provider'),
            ('rental_company', 'Rental Company'),
            ('marketplace', 'Marketplace'),
            ('other', 'Other'),
        ],
        default='retailer'
    )
    business_description = models.TextField(blank=True)

    # Contact Information
    business_phone = models.CharField(max_length=20, blank=True)
    business_email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    business_address = models.CharField(max_length=255, blank=True)

    # Business Details
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Business tax identification number"
    )
    registration_number = models.CharField(max_length=100, blank=True)
    established_year = models.PositiveIntegerField(null=True, blank=True)
    employee_count = models.CharField(
        max_length=20,
        choices=[
            ('1', '1'),
            ('2-10', '2-10'),
            ('11-50', '11-50'),
            ('51-200', '51-200'),
            ('201-1000', '201-1000'),
            ('1000+', '1000+'),
        ],
        blank=True
    )

    # Products/Services
    product_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="List of product categories"
    )
    services_offered = models.JSONField(
        default=list,
        blank=True,
        help_text="List of services offered"
    )
    brands_carried = models.JSONField(
        default=list,
        blank=True,
        help_text="List of brands carried"
    )

    # Business Hours
    business_hours = models.JSONField(
        default=dict,
        blank=True,
        help_text="Business operating hours by day of week"
    )

    # Social Media & Marketing
    social_media_links = models.JSONField(default=dict, blank=True)
    marketing_preferences = models.JSONField(default=dict, blank=True)

    # Verification & Trust
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    verification_documents = models.JSONField(default=list, blank=True)
    trust_score = models.FloatField(default=0.0)

    # Business Metrics
    total_sales = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    customer_rating = models.FloatField(default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)

    # Subscription & Features
    subscription_plan = models.CharField(
        max_length=50,
        choices=[
            ('basic', 'Basic'),
            ('premium', 'Premium'),
            ('enterprise', 'Enterprise'),
        ],
        default='basic'
    )
    subscription_expires = models.DateTimeField(null=True, blank=True)
    featured_listings_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['profile']),
            models.Index(fields=['business_type']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['subscription_plan']),
            models.Index(fields=['trust_score']),
            models.Index(fields=['customer_rating']),
        ]

    def __str__(self):
        return f"{self.business_name} - Commercial"

    @property
    def is_subscription_active(self):
        """Check if subscription is currently active."""
        if not self.subscription_expires:
            return True  # No expiration means active
        return timezone.now() < self.subscription_expires

    def get_business_hours_display(self):
        """Return formatted business hours for display."""
        if not self.business_hours:
            return "Hours not specified"

        days = [
            'monday', 'tuesday', 'wednesday', 'thursday',
            'friday', 'saturday', 'sunday'
        ]
        formatted_hours = []

        for day in days:
            if day in self.business_hours:
                hours = self.business_hours[day]
                if hours.get('closed', False):
                    formatted_hours.append(f"{day.capitalize()}: Closed")
                else:
                    open_time = hours.get('open', '')
                    close_time = hours.get('close', '')
                    if open_time and close_time:
                        formatted_hours.append(
                            f"{day.capitalize()}: {open_time} - {close_time}"
                        )

        return '\n'.join(formatted_hours)

    def save(self, *args, **kwargs):
        """Ensure the parent UserProfile.role is set to 'commercial' when this profile exists."""
        is_new = self._state.adding
        super().save(*args, **kwargs)
        try:
            if self.profile and self.profile.role != 'commercial':
                self.profile.role = 'commercial'
                self.profile.save(update_fields=['role'])
        except Exception:
            # Prevent save-time failures from bubbling up; role sync is best-effort
            pass


class AdminProfile(models.Model):
    """Admin profile for users with administrative roles."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="admin_profile"
    )

    # Administrative Information
    admin_level = models.CharField(
        max_length=20,
        choices=[
            ('super_admin', 'Super Administrator'),
            ('system_admin', 'System Administrator'),
            ('content_admin', 'Content Administrator'),
            ('user_admin', 'User Administrator'),
            ('support_admin', 'Support Administrator'),
        ],
        default='system_admin'
    )

    department = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, blank=True)

    # Permissions & Access
    permissions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of specific permissions assigned"
    )
    access_level = models.PositiveIntegerField(
        default=1,
        help_text="Numeric access level (1-10, higher = more access)"
    )
    can_access_sensitive_data = models.BooleanField(default=False)
    can_modify_system_settings = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_manage_content = models.BooleanField(default=False)
    can_view_analytics = models.BooleanField(default=False)
    can_export_data = models.BooleanField(default=False)

    # Work Schedule & Contact
    work_schedule = models.JSONField(
        default=dict,
        blank=True,
        help_text="Work schedule by day of week"
    )
    emergency_contact = models.CharField(max_length=20, blank=True)
    internal_notes = models.TextField(
        blank=True,
        help_text="Internal notes about this admin"
    )

    # Activity Tracking
    last_admin_action = models.DateTimeField(null=True, blank=True)
    total_admin_actions = models.PositiveIntegerField(default=0)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)

    # Security
    two_factor_enabled = models.BooleanField(default=False)
    ip_whitelist = models.JSONField(
        default=list,
        blank=True,
        help_text="List of allowed IP addresses"
    )
    session_timeout_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Session timeout in minutes"
    )

    # Status & Dates
    is_active = models.BooleanField(default=True)
    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    last_security_review = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['profile']),
            models.Index(fields=['admin_level']),
            models.Index(fields=['is_active']),
            models.Index(fields=['access_level']),
            models.Index(fields=['-last_admin_action']),
        ]

    def __str__(self):
        admin_level_display = self.get_admin_level_display()
        return f"{self.profile.user.username} - {admin_level_display}"

    def record_admin_action(self):
        """Record that an admin action was performed."""
        self.last_admin_action = timezone.now()
        self.total_admin_actions += 1
        self.save(update_fields=['last_admin_action', 'total_admin_actions'])

    def save(self, *args, **kwargs):
        """Ensure the parent UserProfile.role is set to 'admin' when this profile exists."""
        super().save(*args, **kwargs)
        try:
            if self.profile and self.profile.role != 'admin':
                self.profile.role = 'admin'
                self.profile.save(update_fields=['role'])
        except Exception:
            pass

    def reset_failed_login_attempts(self):
        """Reset failed login attempts counter."""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.save(update_fields=['failed_login_attempts', 'last_failed_login'])

    def increment_failed_login(self):
        """Increment failed login attempts."""
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        self.save(update_fields=['failed_login_attempts', 'last_failed_login'])

    @property
    def is_super_admin(self):
        """Check if this is a super administrator."""
        return self.admin_level == 'super_admin'

    @property
    def needs_security_review(self):
        """Check if admin needs security review (older than 6 months)."""
        if not self.last_security_review:
            return True

        from datetime import timedelta
        six_months_ago = timezone.now() - timedelta(days=180)
        return self.last_security_review < six_months_ago


class ModeratorProfile(models.Model):
    """Moderator profile for users with content moderation roles."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="moderator_profile"
    )

    # Moderator Information
    moderator_level = models.CharField(
        max_length=20,
        choices=[
            ('junior', 'Junior Moderator'),
            ('senior', 'Senior Moderator'),
            ('lead', 'Lead Moderator'),
            ('community_mod', 'Community Moderator'),
            ('content_mod', 'Content Moderator'),
            ('global_mod', 'Global Moderator'),
        ],
        default='junior'
    )

    specialization = models.CharField(
        max_length=100,
        choices=[
            ('content', 'Content Moderation'),
            ('community', 'Community Management'),
            ('spam', 'Spam Detection'),
            ('safety', 'Safety & Trust'),
            ('general', 'General Moderation'),
        ],
        default='general'
    )

    # Assigned Areas
    assigned_communities = models.JSONField(
        default=list,
        blank=True,
        help_text="List of community IDs assigned to moderate"
    )
    assigned_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="List of content categories assigned"
    )
    languages = models.JSONField(
        default=list,
        blank=True,
        help_text="Languages this moderator can handle"
    )

    # Moderation Permissions
    can_remove_posts = models.BooleanField(default=True)
    can_remove_comments = models.BooleanField(default=True)
    can_ban_users = models.BooleanField(default=False)
    can_suspend_users = models.BooleanField(default=False)
    can_feature_content = models.BooleanField(default=False)
    can_manage_reports = models.BooleanField(default=True)
    can_escalate_issues = models.BooleanField(default=True)
    can_send_warnings = models.BooleanField(default=True)

    # Activity & Performance Tracking
    total_actions = models.PositiveIntegerField(default=0)
    posts_reviewed = models.PositiveIntegerField(default=0)
    posts_approved = models.PositiveIntegerField(default=0)
    posts_removed = models.PositiveIntegerField(default=0)
    comments_reviewed = models.PositiveIntegerField(default=0)
    comments_approved = models.PositiveIntegerField(default=0)
    comments_removed = models.PositiveIntegerField(default=0)
    reports_handled = models.PositiveIntegerField(default=0)
    users_warned = models.PositiveIntegerField(default=0)
    users_suspended = models.PositiveIntegerField(default=0)
    users_banned = models.PositiveIntegerField(default=0)

    # Quality Metrics
    accuracy_score = models.FloatField(
        default=0.0,
        help_text="Moderation accuracy percentage"
    )
    response_time_avg = models.FloatField(
        default=0.0,
        help_text="Average response time in minutes"
    )
    community_feedback_score = models.FloatField(default=0.0)
    escalation_rate = models.FloatField(
        default=0.0,
        help_text="Percentage of cases escalated"
    )

    # Work Schedule & Availability
    work_schedule = models.JSONField(
        default=dict,
        blank=True,
        help_text="Work schedule by day of week and time zones"
    )
    timezone = models.CharField(max_length=50, default='UTC')
    is_available = models.BooleanField(default=True)
    current_shift_start = models.DateTimeField(null=True, blank=True)
    current_shift_end = models.DateTimeField(null=True, blank=True)

    # Training & Certification
    training_completed = models.JSONField(
        default=list,
        blank=True,
        help_text="List of completed training modules"
    )
    certifications = models.JSONField(
        default=list,
        blank=True,
        help_text="List of moderation certifications"
    )
    training_score = models.FloatField(default=0.0)
    last_training_date = models.DateTimeField(null=True, blank=True)
    next_training_due = models.DateTimeField(null=True, blank=True)

    # Status & Dates
    is_active = models.BooleanField(default=True)
    probation_until = models.DateTimeField(null=True, blank=True)
    last_action_date = models.DateTimeField(null=True, blank=True)
    last_performance_review = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['profile']),
            models.Index(fields=['moderator_level']),
            models.Index(fields=['specialization']),
            models.Index(fields=['is_active', 'is_available']),
            models.Index(fields=['-last_action_date']),
            models.Index(fields=['accuracy_score']),
        ]

    def __str__(self):
        moderator_level_display = self.get_moderator_level_display()
        return f"{self.profile.user.username} - {moderator_level_display}"

    def record_moderation_action(self, action_type):
        """Record a moderation action and update counters."""
        self.total_actions += 1
        self.last_action_date = timezone.now()

        # Update specific counters based on action type
        action_counters = {
            'post_approved': 'posts_approved',
            'post_removed': 'posts_removed',
            'comment_approved': 'comments_approved',
            'comment_removed': 'comments_removed',
            'report_handled': 'reports_handled',
            'user_warned': 'users_warned',
            'user_suspended': 'users_suspended',
            'user_banned': 'users_banned',
        }

        if action_type in action_counters:
            current_value = getattr(self, action_counters[action_type], 0)
            setattr(self, action_counters[action_type], current_value + 1)

        # Update reviewed counters
        if action_type.startswith('post_'):
            self.posts_reviewed += 1
        elif action_type.startswith('comment_'):
            self.comments_reviewed += 1

        self.save(update_fields=[
            'total_actions', 'last_action_date', 'posts_reviewed',
            'posts_approved', 'posts_removed', 'comments_reviewed',
            'comments_approved', 'comments_removed', 'reports_handled',
            'users_warned', 'users_suspended', 'users_banned'
        ])

    def save(self, *args, **kwargs):
        """Ensure the parent UserProfile.role is set to 'moderator' when this profile exists."""
        super().save(*args, **kwargs)
        try:
            if self.profile and self.profile.role != 'moderator':
                self.profile.role = 'moderator'
                self.profile.save(update_fields=['role'])
        except Exception:
            pass

    def calculate_accuracy_score(self):
        """Calculate and update accuracy score based on performance."""
        total_reviewed = self.posts_reviewed + self.comments_reviewed
        if total_reviewed == 0:
            return 0.0

        # This would need to be calculated based on appeals, overturns, etc.
        # For now, return a placeholder calculation
        total_correct_actions = (
            self.posts_approved + self.comments_approved +
            self.posts_removed + self.comments_removed
        )

        if total_reviewed > 0:
            accuracy = (total_correct_actions / total_reviewed) * 100
        else:
            accuracy = 0.0

        self.accuracy_score = min(100.0, accuracy)
        self.save(update_fields=['accuracy_score'])
        return self.accuracy_score

    @property
    def is_on_probation(self):
        """Check if moderator is currently on probation."""
        if not self.probation_until:
            return False
        return timezone.now() < self.probation_until

    @property
    def needs_performance_review(self):
        """Check if moderator needs performance review (3+ months)."""
        if not self.last_performance_review:
            return True

        from datetime import timedelta
        three_months_ago = timezone.now() - timedelta(days=90)
        return self.last_performance_review < three_months_ago

    @property
    def current_workload_score(self):
        """Calculate current workload based on assigned areas."""
        if self.assigned_communities:
            communities_count = len(self.assigned_communities)
        else:
            communities_count = 0

        if self.assigned_categories:
            categories_count = len(self.assigned_categories)
        else:
            categories_count = 0

        return communities_count + (categories_count * 0.5)


@receiver(post_delete, sender=CommercialProfile)
def _reset_role_on_commercial_delete(sender, instance, **kwargs):
    """Reset UserProfile.role to 'normal' when a CommercialProfile is deleted."""
    try:
        profile = instance.profile
        if profile and profile.role == 'commercial':
            profile.role = 'normal'
            profile.save(update_fields=['role'])
    except Exception:
        pass


@receiver(post_delete, sender=AdminProfile)
def _reset_role_on_admin_delete(sender, instance, **kwargs):
    """Reset UserProfile.role to 'normal' when an AdminProfile is deleted."""
    try:
        profile = instance.profile
        if profile and profile.role == 'admin':
            profile.role = 'normal'
            profile.save(update_fields=['role'])
    except Exception:
        pass


@receiver(post_delete, sender=ModeratorProfile)
def _reset_role_on_moderator_delete(sender, instance, **kwargs):
    """Reset UserProfile.role to 'normal' when a ModeratorProfile is deleted."""
    try:
        profile = instance.profile
        if profile and profile.role == 'moderator':
            profile.role = 'normal'
            profile.save(update_fields=['role'])
    except Exception:
        pass


class UserSettings(models.Model):
    """User preferences and settings."""

    NOTIFICATION_FREQUENCY = [
        ('real_time', 'Real Time'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('never', 'Never'),
    ]

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('fr', 'French'),
        ('es', 'Spanish'),
        ('de', 'German'),
        ('it', 'Italian'),
    ]

    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='settings'
    )

    # Notification settings
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    warranty_expiry_notifications = models.BooleanField(default=True)
    maintenance_reminder_notifications = models.BooleanField(default=True)
    notification_frequency = models.CharField(
        max_length=20,
        choices=NOTIFICATION_FREQUENCY,
        default='real_time'
    )

    # Privacy settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('friends', 'Friends Only'),
            ('private', 'Private'),
        ],
        default='public'
    )

    # Interface settings
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en'
    )
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='light'
    )
    timezone = models.CharField(max_length=50, default='UTC')

    # Content settings
    auto_play_videos = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.user.username} - Settings"


class Follow(models.Model):
    """User following relationships with approval system."""

    FOLLOW_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='following'
    )
    followed = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='followers'
    )
    status = models.CharField(
        max_length=10,
        choices=FOLLOW_STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)

    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Unique constraint to prevent duplicate follows."""
        unique_together = ('follower', 'followed')
        indexes = [
            models.Index(fields=['follower', 'created_at']),
            models.Index(fields=['followed', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def save(self, *args, **kwargs):
        is_new = not self.pk
        was_approved = False

        # Check if this is a status change to approved
        if self.pk:
            try:
                old_instance = Follow.objects.get(pk=self.pk)
                was_approved = (old_instance.status != 'approved' and
                              self.status == 'approved')
            except Follow.DoesNotExist:
                pass

        # Auto-approve for public accounts
        if is_new and not self.followed.is_private:
            self.status = 'approved'
            self.approved_at = timezone.now()
        # Set approved_at when status changes to approved
        elif self.status == 'approved' and not self.approved_at:
            self.approved_at = timezone.now()

        super().save(*args, **kwargs)

        # Send notifications after saving
        if is_new:
            self._send_follow_request_notification()
        elif was_approved:
            self._send_follow_approved_notification()

    def _send_follow_request_notification(self):
        """Send notification when a follow request is created."""
        from notifications.utils import NotificationService
        from notifications.realtime import send_follow_notification

        # Determine message based on account privacy
        if self.followed.is_private and self.status == 'pending':
            message_text = (f'@{self.follower.user.username} wants to follow you. '
                          f'Accept or decline this request in your notifications.')
            should_send_email = True
        else:
            message_text = f'@{self.follower.user.username} is now following you.'
            should_send_email = False  # No email for public follows

        # Create in-app notification using NotificationService (includes WebSocket)
        notification_service = NotificationService()
        notification_service.create_notification(
            recipient=self.followed,
            sender=self.follower,
            notification_type='follow_request',
            title=f'New follow request from @{self.follower.user.username}',
            message=message_text,
            related_object=self,
            app_context='accounts',
            extra_data={
                'follow_id': str(self.id),
                'follower_id': str(self.follower.id),
                'follower_username': self.follower.user.username,
                'status': self.status,
                'is_private': self.followed.is_private,
                'action_required': self.followed.is_private and self.status == 'pending'
            }
        )

        # Send additional real-time notification
        send_follow_notification(
            follower_profile=self.follower,
            followed_profile=self.followed,
            follow_status=self.status
        )

        # Send email notification for private profile follow requests
        if should_send_email:
            # Send email asynchronously
            from notifications.async_email_tasks import (
                send_follow_request_email_async
            )

            send_follow_request_email_async.delay(str(self.id))

            # Immediate in-app notification for the follow request
            NotificationService.create_notification(
                recipient=self.followed,
                title="Follow Request Email Sent",
                message=f"Follow request from @{self.follower.user.username} sent via email",
                notification_type='email_sent',
                app_context='accounts'
            )

    def _send_follow_approved_notification(self):
        """Send notification when a follow request is approved."""
        from notifications.utils import NotificationService

        # Create in-app notification using NotificationService
        notification_service = NotificationService()
        title = f'@{self.followed.user.username} accepted your follow request'
        message = (f'@{self.followed.user.username} accepted your follow '
                   f'request. You can now see their posts and activity.')

        notification_service.create_notification(
            recipient=self.follower,
            sender=self.followed,
            notification_type='follow_approved',
            title=title,
            message=message,
            related_object=self,
            app_context='accounts',
            extra_data={
                'follow_id': str(self.id),
                'followed_id': str(self.followed.id),
                'followed_username': self.followed.user.username,
                'status': self.status
            }
        )

    def approve(self):
        """Approve the follow request."""
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.save()

    def reject(self):
        """Reject the follow request."""
        self.status = 'rejected'
        self.save()

    def __str__(self):
        return f"{self.follower.user.username} follows " \
               f"{self.followed.user.username} ({self.status})"


class Block(models.Model):
    """User blocking relationships."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blocker = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='blocking'
    )
    blocked = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='blocked_by'
    )
    reason = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Unique constraint to prevent duplicate blocks."""
        unique_together = ('blocker', 'blocked')

    def __str__(self):
        return f"{self.blocker.user.username} blocks " \
               f"{self.blocked.user.username}"


class UserSession(models.Model):
    """Track user sessions for analytics."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    # Authentication tokens (store hashes or references; avoid raw tokens if possible)
    session_id = models.CharField(max_length=255, unique=True)

    # Network / location / Device / client metadata
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_info = models.JSONField(default=dict, blank=True)
    location_data = models.JSONField(default=dict, blank=True)
    device_fingerprint = models.CharField(max_length=128, blank=True)
    fast_fingerprint = models.CharField(
        max_length=64,
        blank=True,
        help_text='Fast device fingerprint for quick session lookup'
    )
    persistent = models.BooleanField(default=False)  # "remember me"

    # Session metrics
    pages_visited = models.PositiveIntegerField(default=0)
    termination_reason = models.CharField(max_length=255, blank=True, null=True)
    # time_spent = models.DurationField(null=True, blank=True)

    # Session lifecycle timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True, null=True, blank=True)

    # Status flags
    is_active = models.BooleanField(default=True)   # true until ended/expired
    is_ended = models.BooleanField(default=False, db_index=True)

    # Administrative
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', '-started_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_active', '-started_at']),
            models.Index(fields=['device_fingerprint']),
            models.Index(fields=['user', 'fast_fingerprint', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.id[:8]}"

    def mark_ended(self, reason=None, when=None, from_cleanup: bool = False):
        """Mark session as ended. Updates both DB and Redis."""
        from django.utils import timezone
        from django.conf import settings
        import redis
        import json

        end_time = when or timezone.now()
        self.is_ended = True
        self.is_active = False
        self.ended_at = end_time
        self.expires_at = end_time  # Expire immediately
        if reason:
            self.termination_reason = reason

        # Save to database
        self.save(update_fields=[
            'is_ended', 'is_active', 'ended_at', 'expires_at',
            'termination_reason', 'updated_at'
        ])

        # Track session ended analytics only if NOT called from cleanup
        # (cleanup process already tracks analytics with 'cleanup' event type)
        if not from_cleanup:
            try:
                from analytics.tasks import track_session_comprehensive

                # Use 'ended' for manual session termination
                # cleanup events are handled separately in cleanup tasks
                analytics_data = {
                    'session_id': self.session_id,
                    'user_id': self.user.user.id,
                    'event_type': 'ended',
                    'additional_metadata': {
                        'termination_reason': reason or 'manual_termination',
                        'ended_at': end_time.isoformat(),
                        'source': 'UserSession.mark_ended'
                    }
                }

                # Track session ended synchronously (not in a critical path)
                track_session_comprehensive(analytics_data)

            except Exception as e:
                # Don't fail the session termination if analytics fail
                import logging
                logger = logging.getLogger('accounts.models')
                logger.warning(f"Failed to track session ended analytics: {e}")

        # Update Redis if enabled
        use_redis = getattr(settings, 'USE_REDIS_SESSIONS', False)
        if use_redis:
            try:
                redis_url = getattr(
                    settings, 'REDIS_URL', 'redis://localhost:6379/0'
                )
                redis_client = redis.from_url(redis_url, decode_responses=True)

                # Update session data in Redis
                redis_key = f"session:{self.session_id}"
                session_data = redis_client.get(redis_key)
                if session_data:
                    data = json.loads(session_data)
                    data.update({
                        'is_active': False,
                        'is_ended': True,
                        'ended_at': end_time.isoformat(),
                        'expires_at': end_time.isoformat(),
                        'termination_reason': reason or ''
                    })
                    # Set short expiry for ended sessions (1 hour for cleanup)
                    redis_client.setex(
                        redis_key, 3600, json.dumps(data, default=str)
                    )

                # Remove from user's active sessions
                user_sessions_key = f"user_sessions:{self.user.id}"
                redis_client.srem(user_sessions_key, self.session_id)

            except Exception as e:
                # Log but don't fail if Redis update fails
                import logging
                logger = logging.getLogger('accounts.models')
                logger.warning(
                    f"Failed to update Redis for ended session "
                    f"{self.session_id}: {e}"
                )

    def extend_session(self, additional_hours=None):
        """Extend the session expiration time in both database and Redis."""
        from django.utils import timezone
        from django.conf import settings
        import redis
        import json

        # Calculate new expiration time
        if additional_hours is None:
            # Use persistent duration for remember me sessions
            if self.persistent:
                additional_hours = getattr(
                    settings, 'PERSISTENT_SESSION_DURATION_DAYS', 30
                ) * 24
            else:
                # Use default session duration from settings
                additional_hours = getattr(
                    settings, 'SESSION_DURATION_HOURS', 4
                )

        new_expires_at = timezone.now() + timezone.timedelta(
            hours=additional_hours
        )

        # Update database
        self.expires_at = new_expires_at
        self.save(update_fields=['expires_at', 'updated_at'])

        # Update Redis if enabled
        use_redis = getattr(settings, 'USE_REDIS_SESSIONS', False)
        if use_redis:
            try:
                redis_url = getattr(
                    settings, 'REDIS_URL', 'redis://localhost:6379/0'
                )
                redis_client = redis.from_url(redis_url, decode_responses=True)

                # Update session data in Redis
                redis_key = f"session:{self.session_id}"
                session_data = redis_client.get(redis_key)

                if session_data:
                    data = json.loads(session_data)
                    data['expires_at'] = new_expires_at.isoformat()

                    # Calculate new TTL in seconds
                    ttl_seconds = int(additional_hours * 3600)

                    # Update Redis with new expiration
                    redis_client.setex(
                        redis_key, ttl_seconds,
                        json.dumps(data, default=str)
                    )

                    # Also update user sessions set expiration
                    user_sessions_key = f"user_sessions:{self.user.id}"
                    redis_client.expire(user_sessions_key, ttl_seconds)

                    import logging
                    logger = logging.getLogger('accounts.models')
                    logger.info(
                        f"Extended session {self.session_id} by "
                        f"{additional_hours} hours until {new_expires_at}"
                    )
                else:
                    # Session not found in Redis, recreate essential data
                    redis_data = {
                        'session_id': self.session_id,
                        'user_id': str(self.user.id),
                        'ip_address': self.ip_address,
                        'location_data': self.location_data,
                        'device_fingerprint': self.device_fingerprint,
                        'persistent': self.persistent,
                        'termination_reason': self.termination_reason or '',
                        'is_active': self.is_active,
                        'is_ended': self.is_ended,
                        'started_at': self.started_at.isoformat(),
                        'expires_at': new_expires_at.isoformat()
                    }

                    ttl_seconds = int(additional_hours * 3600)
                    redis_client.setex(
                        redis_key, ttl_seconds,
                        json.dumps(redis_data, default=str)
                    )

                    # Re-add to user sessions
                    user_sessions_key = f"user_sessions:{self.user.id}"
                    redis_client.sadd(user_sessions_key, self.session_id)
                    redis_client.expire(user_sessions_key, ttl_seconds)

            except Exception as e:
                import logging
                logger = logging.getLogger('accounts.models')
                logger.warning(
                    f"Failed to extend session in Redis for "
                    f"{self.session_id}: {e}"
                )

        return new_expires_at

    @classmethod
    def get_active_session(cls, session_id):
        """Get active session from database, checking Redis first."""
        from django.conf import settings
        import redis
        import json

        use_redis = getattr(settings, 'USE_REDIS_SESSIONS', False)

        # Try Redis first for faster lookup
        if use_redis:
            try:
                redis_url = getattr(
                    settings, 'REDIS_URL', 'redis://localhost:6379/0'
                )
                redis_client = redis.from_url(redis_url, decode_responses=True)

                redis_key = f"session:{session_id}"
                session_data = redis_client.get(redis_key)

                if session_data:
                    data = json.loads(session_data)
                    # Check if session is still active according to Redis
                    if data.get('is_active') and not data.get('is_ended'):
                        # Return database session for full functionality
                        try:
                            return cls.objects.get(
                                session_id=session_id,
                                is_active=True,
                                is_ended=False
                            )
                        except cls.DoesNotExist:
                            # Clean up stale Redis entry
                            redis_client.delete(redis_key)
                            return None

            except Exception as e:
                import logging
                logger = logging.getLogger('accounts.models')
                logger.warning(
                    f"Redis lookup failed for session {session_id}: {e}"
                )

        # Fallback to database lookup
        try:
            return cls.objects.get(
                session_id=session_id,
                is_active=True,
                is_ended=False
            )
        except cls.DoesNotExist:
            return None


    # @property
    # def time_spent(self):
    #     """Calculate total time spent in the session in seconds."""
    #     if self.ended_at:
    #         return (self.ended_at - self.started_at)
    #     return (timezone.now() - self.started_at)

class UserEvent(models.Model):
    """Event logging for user account and security actions."""
    EVENT_TYPES = [
        # Authentication & Security
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('login_failed', 'Login Failed'),
        ('register', 'Register'),
        ('password_change', 'Password Change'),
        ('password_reset_request', 'Password Reset Request'),
        ('password_reset_complete', 'Password Reset Complete'),
        ('email_change', 'Email Change'),
        ('email_verify', 'Email Verification'),
        ('two_factor_enable', 'Two-Factor Authentication Enabled'),
        ('two_factor_disable', 'Two-Factor Authentication Disabled'),
        ('security_login_failed', 'Login Failed'),
        ('security_suspicious_activity', 'Suspicious Activity'),
        ('security_account_locked', 'Account Locked'),
        ('security_password_breach', 'Password Breach Detected'),
        ('security_two_factor_enabled', 'Two-Factor Authentication Enabled'),
        ('security_session_hijack', 'Session Hijack Detected'),

        # Account Management
        ('profile_update', 'Profile Update'),
        ('profile_picture_change', 'Profile Picture Change'),
        ('privacy_update', 'Privacy Settings Update'),
        ('notification_settings_update', 'Notification Settings Update'),
        ('account_deactivation', 'Account Deactivation'),
        ('account_reactivation', 'Account Reactivation'),
        ('account_deletion_request', 'Account Deletion Request'),
        ('data_export_request', 'Data Export Request'),
        ('account_delete', 'Account Deleted'),
        ('account_reactivate', 'Account Reactivated'),
        ('session_expire', 'Session Expired'),

        # Social Account Actions
        ('user_follow', 'User Follow'),
        ('user_unfollow', 'User Unfollow'),
        ('user_block', 'User Block'),
        ('user_unblock', 'User Unblock'),
        ('profile_view', 'Profile View'),

        # Professional Account
        ('pro_upgrade', 'Professional Account Upgrade'),
        ('pro_verification_request', 'Professional Verification Request'),
        ('pro_verification_complete', 'Professional Verification Complete'),

        # Security Events
        ('suspicious_login', 'Suspicious Login Attempt'),
        ('device_change', 'New Device Login'),
        ('location_change', 'New Location Login'),
        ('session_timeout', 'Session Timeout'),
        ('forced_logout', 'Forced Logout'),

        # Session and tracking (added for middleware compatibility)
        ('session_create', 'Session Started'),
        ('session_update', 'Session Updated'),
        ('event_track', 'Event Tracked'),
        ('settings', 'Settings Changed'),
        ('api_access', 'API Access'),
        ('search_perform', 'Search Performed'),
        ('file_upload', 'File Uploaded'),
        ('error_encountered', 'Error Encountered'),

        # Analytics events
        ('analytics_view', 'Analytics Viewed'),
        ('daily_analytics_view', 'Daily Analytics Viewed'),
        ('user_analytics_view', 'User Analytics Viewed'),
        ('metric_record', 'Metric Recorded'),
        ('error_log', 'Error Logged'),
        ('system_metric_view', 'System Metrics Viewed'),

        # Content events
        ('post_create', 'Post Created'),
        ('post_update', 'Post Updated'),
        ('post_delete', 'Post Deleted'),
        ('post_like', 'Post Liked'),
        ('post_unlike', 'Post Unliked'),
        ('post_share', 'Post Shared'),
        ('comment_create', 'Comment Created'),
        ('comment_update', 'Comment Updated'),
        ('comment_delete', 'Comment Deleted'),
        ('post_view', 'Post Viewed'),
        ('post_bookmark', 'Post Bookmarked'),
        ('file_download', 'File Downloaded'),
        ('media_access', 'Media Accessed'),
        ('hashtag_create', 'Hashtag Created'),
        ('hashtag_follow', 'Hashtag Followed'),
        ('hashtag_unfollow', 'Hashtag Unfollowed'),

        # Community events
        ('community_create', 'Community Created'),
        ('community_update', 'Community Updated'),
        ('community_delete', 'Community Deleted'),
        ('community_join', 'Community Joined'),
        ('community_leave', 'Community Left'),
        ('community_post', 'Community Post'),
        ('community_membership_create', 'Community Membership Created'),
        ('community_role_create', 'Community Role Created'),
        ('community_role_update', 'Community Role Updated'),
        ('community_moderation', 'Community Moderation Action'),
        ('community_invitation_create', 'Community Invitation Created'),
        ('community_invitation_accept', 'Community Invitation Accepted'),
        ('community_invitation_decline', 'Community Invitation Declined'),

        # AI Conversation events
        ('ai_conversation_create', 'AI Conversation Started'),
        ('ai_conversation_update', 'AI Conversation Updated'),
        ('ai_conversation_delete', 'AI Conversation Deleted'),
        ('ai_message_create', 'AI Message Sent'),
        ('ai_message_rating', 'AI Message Rated'),
        ('ai_agent_create', 'AI Agent Created'),
        ('ai_agent_update', 'AI Agent Updated'),
        ('ai_agent_delete', 'AI Agent Deleted'),
        ('ai_model_create', 'AI Model Created'),
        ('ai_model_update', 'AI Model Updated'),
        ('ai_analytics_view', 'AI Analytics Viewed'),
        ('ai_model_performance_view', 'AI Model Performance Viewed'),
        ('ai_conversation_summary_create', 'AI Conversation Summary Created'),

        # Messaging events
        ('message_send', 'Message Sent'),
        ('chat_create', 'Chat Created'),
        ('chat_join', 'Chat Joined'),
        ('chat_leave', 'Chat Left'),
        ('message_read', 'Message Read'),
        ('message_delete', 'Message Deleted'),

        # Poll events
        ('poll_create', 'Poll Created'),
        ('poll_update', 'Poll Updated'),
        ('poll_delete', 'Poll Deleted'),
        ('poll_view', 'Poll Viewed'),
        ('poll_vote', 'Poll Vote Cast'),
        ('poll_option_create', 'Poll Option Created'),
        ('poll_option_update', 'Poll Option Updated'),
        ('poll_option_delete', 'Poll Option Deleted'),
        ('poll_voter_create', 'Poll Voter Added'),
        ('poll_close', 'Poll Closed'),

        # Content safety events
        ('content_flagged', 'Content Flagged'),
        ('content_moderated', 'Content Moderated'),
        ('content_approved', 'Content Approved'),
        ('content_rejected', 'Content Rejected'),
        ('bot_detection', 'Bot Detected'),
        ('spam_detection', 'Spam Detected'),
        ('abuse_report', 'Abuse Reported'),

        # Badge & Achievement events
        ('badge_earned', 'Badge Earned'),
        ('badge_progress_update', 'Badge Progress Updated'),
        ('achievement_milestone', 'Achievement Milestone Reached'),
        ('badge_criteria_met', 'Badge Criteria Met'),
        ('badge_level_up', 'Badge Level Up'),
        ('badge_streak_started', 'Badge Streak Started'),
        ('badge_streak_maintained', 'Badge Streak Maintained'),
        ('badge_streak_broken', 'Badge Streak Broken'),
        ('badge_combo_earned', 'Badge Combo Earned'),
        ('achievement_points_awarded', 'Achievement Points Awarded'),
        ('badge_showcase_updated', 'Badge Showcase Updated'),
        ('badge_shared', 'Badge Shared'),
        ('achievement_celebration', 'Achievement Celebration'),
        ('badge_rarity_achieved', 'Rare Badge Achieved'),
        ('badge_collection_milestone', 'Badge Collection Milestone'),
    ]

    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='account_events'
    )
    session = models.ForeignKey(
        UserSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_LEVELS,
        default='low'
    )
    description = models.TextField(blank=True)

    # Event metadata
    metadata = models.JSONField(default=dict, blank=True)
    # ip_address = models.GenericIPAddressField(null=True, blank=True)
    # user_agent = models.CharField(max_length=500, blank=True)

    # Geographic data
    # country = models.CharField(max_length=100, blank=True)
    # administrative_division = models.CharField(max_length=100, blank=True)

    # Success/failure tracking
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    # Reference to affected object (optional)
    target_user = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events_about_me'
    )

    # Flagging for review
    requires_review = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_events'
    )

    created_at = models.DateTimeField(auto_now_add=True)


    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['target_user', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['success', '-created_at']),
            models.Index(fields=['requires_review', '-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        status = "✓" if self.success else "✗"
        event_display = dict(self.EVENT_TYPES).get(
            self.event_type,
            self.event_type
        )
        return f"{status} {self.user.user.username} - {event_display}"

    @property
    def is_security_event(self):
        """Check if this is a security-related event."""
        security_events = [
            'login_failed', 'suspicious_login', 'device_change',
            'location_change', 'forced_logout', 'two_factor_enable',
            'two_factor_disable', 'password_change'
        ]
        return self.event_type in security_events

    @property
    def risk_score(self):
        """Calculate risk score based on event type and metadata."""
        base_scores = {
            'login_failed': 3,
            'suspicious_login': 8,
            'device_change': 5,
            'location_change': 4,
            'password_change': 2,
            'two_factor_disable': 7,
        }
        return base_scores.get(self.event_type, 1)

# =============================================================
# BADGE / ACHIEVEMENT SYSTEM
# =============================================================


class BadgeDefinition(models.Model):
    """Defines an achievement badge and its criteria.

    criteria JSON examples:
    {
      "type": "stat_threshold",
      "stat": "posts_count",
      "operator": ">=",
      "value": 10
    }
    or composite:
    {
      "type": "and",
      "conditions": [ { ... }, { ... } ]
    }
    Supported types:
      - stat_threshold (compares UserProfile numeric field)
      - account_age_days (days since profile.created_at)
      - follower_threshold (follower_count >= value)
      - composite logical: and / or
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(max_length=50, unique=True, help_text="Internal badge code")
    full_name = models.CharField(max_length=100)
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Badge name extracted from full_name"
    )
    tier = models.CharField(
        max_length=20,
        blank=True,
        help_text="Badge tier extracted from full_name (Bronze/Silver/Gold)"
    )
    description = models.TextField(max_length=500, blank=True)
    icon = models.CharField(
        max_length=150,
        blank=True,
        help_text="Icon reference or asset path"
    )
    criteria = models.JSONField(
        default=dict,
        help_text="Criteria definition JSON"
    )
    is_secret = models.BooleanField(
        default=False,
        help_text="If true, not listed until earned"
    )
    points = models.PositiveIntegerField(
        default=0,
        help_text="Points granted when earned"
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['code']),
        ]

    def save(self, *args, **kwargs):
        """Override save to extract name and tier from full_name."""
        if self.full_name:
            self.name, self.tier = self._extract_name_and_tier(self.full_name)
        super().save(*args, **kwargs)

    def _extract_name_and_tier(self, full_name_str: str) -> tuple:
        """Extract name and tier from full_name string.

        Examples:
        - 'Quality Creator (Silver)' -> ('Quality Creator', 'Silver')
        - 'Early Adopter' -> ('Early Adopter', 'Gold')
        - 'Community Helper (Bronze)' -> ('Community Helper', 'Bronze')

        If tier can't be extracted, defaults to 'Gold'.
        """
        import re

        # Pattern to match: "Name (Tier)" format
        pattern = r'^(.+?)\s*\(([^)]+)\)$'
        match = re.match(pattern, full_name_str.strip())

        if match:
            name = match.group(1).strip()
            tier_candidate = match.group(2).strip()

            # Validate tier is one of Bronze, Silver, Gold
            valid_tiers = ['Bronze', 'Silver', 'Gold']
            tier = tier_candidate if tier_candidate in valid_tiers else 'Gold'

            return name, tier
        else:
            # No tier found, use full_name as name, default to Gold
            return full_name_str.strip(), 'Gold'

    def __str__(self):
        return f"Badge {self.code}"

    def evaluate_for(self, profile: 'UserProfile') -> bool:
        from accounts.utils import evaluate_badge_criteria_for_profile
        return evaluate_badge_criteria_for_profile(self, profile)


class UserBadge(models.Model):
    """Awarded badge for a user profile."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='badges'
    )
    badge = models.ForeignKey(
        BadgeDefinition,
        on_delete=models.CASCADE,
        related_name='awards'
    )
    first_trigger_event = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional event type that triggered award"
    )
    metadata = models.JSONField(default=dict, blank=True)
    earned_at = models.DateTimeField(auto_now_add=True)

    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('profile', 'badge')
        indexes = [
            models.Index(fields=['profile', '-earned_at']),
            models.Index(fields=['badge']),
        ]

    def __str__(self):
        return f"{self.profile.user.username} earned {self.badge.code}"


# =============================================================================
# SUPPORT SYSTEM MODELS
# =============================================================================

class SupportTicket(models.Model):
    """Support ticket model for user requests."""
    
    PRIORITY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Élevée'),
        ('urgent', 'Urgente'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Ouvert'),
        ('in_progress', 'En cours'),
        ('waiting_user', 'En attente utilisateur'),
        ('resolved', 'Résolu'),
        ('closed', 'Fermé'),
    ]
    
    CATEGORY_CHOICES = [
        ('technical', 'Problème technique'),
        ('account', 'Problème de compte'),
        ('billing', 'Facturation'),
        ('feature_request', 'Demande de fonctionnalité'),
        ('report', 'Signalement'),
        ('other', 'Autre'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Ticket identification
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    
    # User information
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='support_tickets',
        null=True, blank=True  # Allow anonymous tickets
    )
    user_email = models.EmailField()  # Store email even for anonymous users
    user_name = models.CharField(max_length=100)
    
    # Ticket details
    subject = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Assignment
    assigned_to = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        related_name='assigned_tickets',
        null=True, blank=True,
        limit_choices_to={'profile__role': 'admin'}
    )
    
    # Metadata
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    browser_info = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['assigned_to', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['ticket_number']),
        ]

    def save(self, *args, **kwargs):
        """Generate ticket number if not set."""
        if not self.ticket_number:
            import time
            # Format: YYYY-HHMMSS (Year-HourMinuteSecond)
            timestamp = time.strftime('%Y-%H%M%S')
            # Add a random 3-digit suffix to avoid collisions
            import random
            suffix = random.randint(100, 999)
            self.ticket_number = f"TK-{timestamp}-{suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.ticket_number} - {self.subject}"

    @property
    def is_overdue(self):
        """Check if ticket is overdue based on priority."""
        from django.utils import timezone
        from datetime import timedelta
        
        if self.status in ['resolved', 'closed']:
            return False
            
        overdue_hours = {
            'urgent': 2,
            'high': 24,
            'medium': 72,
            'low': 168,  # 1 week
        }
        
        hours = overdue_hours.get(self.priority, 72)
        deadline = self.created_at + timedelta(hours=hours)
        return timezone.now() > deadline


class SupportMessage(models.Model):
    """Messages within a support ticket."""
    
    MESSAGE_TYPES = [
        ('user_message', 'Message utilisateur'),
        ('admin_reply', 'Réponse admin'),
        ('system_note', 'Note système'),
        ('status_change', 'Changement de statut'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='support_messages',
        null=True, blank=True  # Can be null for system messages
    )
    
    # Message content
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='user_message')
    content = models.TextField()
    is_internal = models.BooleanField(default=False)  # Internal admin notes
    
    # Attachments (future feature)
    attachments = models.JSONField(default=list, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Read status
    is_read_by_user = models.BooleanField(default=False)
    is_read_by_admin = models.BooleanField(default=False)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['message_type']),
        ]

    def __str__(self):
        sender_name = self.sender.username if self.sender else "Système"
        return f"{sender_name} sur #{self.ticket.ticket_number}"

    def save(self, *args, **kwargs):
        """Auto-mark as read by sender."""
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new and self.sender:
            # Auto-mark as read by the sender
            if hasattr(self.sender, 'profile') and self.sender.profile.role == 'admin':
                self.is_read_by_admin = True
            else:
                self.is_read_by_user = True
            super().save(update_fields=['is_read_by_admin', 'is_read_by_user'])


# Import contact change models
from .contact_change_models import ContactChangeRequest, ContactChangeLog
