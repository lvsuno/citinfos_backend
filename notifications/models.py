"""Notification models."""

import uuid
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from accounts.models import UserProfile


class Notification(models.Model):
    """User notifications with extended metadata (priority, expiry)."""
    NOTIFICATION_TYPES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('mention', 'Mention'),
        ('message', 'Message'),
        ('new_message', 'New Message'),
        ('share', 'Share'),
        ('report', 'Report'),
        ('repost', 'Repost'),
        ('system', 'System'),
        ('badge', 'Badge'),
        ('achievement', 'Achievement'),
        ('warranty', 'Warranty'),
        ('maintenance', 'Maintenance'),
        ('welcome', 'Welcome'),
        ('security_alert', 'Security Alert'),
        ('digest', 'Digest'),
        # Community notifications
        ('community_invite', 'Community Invite'),
        ('community_join', 'Community Join'),
        ('community_post', 'Community Post'),
        ('community_role_change', 'Community Role Change'),
        ('geo_restriction', 'Geo Restriction'),
    ]

    PRIORITY_LEVELS = [
        (1, 'High'),
        (2, 'Elevated'),
        (3, 'Normal'),
        (4, 'Low'),
        (5, 'Very Low'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sent_notifications'
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(max_length=200)
    message = models.TextField(max_length=500)

    # Priority (for ordering & queueing)
    priority = models.PositiveSmallIntegerField(
        choices=PRIORITY_LEVELS,
        default=3,
        help_text='Lower number = higher priority'
    )

    # Generic foreign key for related object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Additional data for notification context
    extra_data = models.JSONField(
        null=True,
        blank=True,
        help_text='Additional context data for the notification'
    )

    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Expiration (optional auto-clean / hide after date)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Optional expiry timestamp — ignored if null'
    )
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



    # Soft delete field


    is_deleted = models.BooleanField(default=False)


    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['content_type', 'object_id', 'notification_type']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['is_read']),
            models.Index(fields=['priority', '-created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.recipient.user.username}"
