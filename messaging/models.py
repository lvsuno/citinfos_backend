"""Messaging models for chat rooms and messages."""

import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from accounts.models import UserProfile


class ChatRoom(models.Model):
    """Chat rooms for messaging."""

    ROOM_TYPES = [
        ('direct', 'Direct Message'),
        ('group', 'Group Chat'),
        # ('ai_chat', 'AI Chat'),  # Added for future AI integration
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, blank=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    participants = models.ManyToManyField(
        UserProfile,
        related_name='chat_rooms'
    )
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='created_rooms'
    )

    # Group chat settings
    description = models.TextField(max_length=500, blank=True)
    image = models.ImageField(upload_to='chat_rooms/', blank=True, null=True)

    # Enhanced messaging features
    is_private = models.BooleanField(default=False)  # Private/public groups
    max_participants = models.PositiveIntegerField(default=100)  # Limit group size
    is_archived = models.BooleanField(default=False)  # Archive old rooms
    last_activity = models.DateTimeField(auto_now=True)  # Track last activity

    # Message count for performance
    messages_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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
    # Restoration tracking fields
    # Restoration tracking fields

    def clean(self):
        """Validate that only verified users can create chat rooms."""
        super().clean()
        from accounts.permissions import validate_user_for_interaction
        validate_user_for_interaction(self.created_by, "create chat rooms")

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or f"{self.room_type.title()} Room"

    class Meta:
        indexes = [
            models.Index(fields=['room_type', '-updated_at']),
            models.Index(fields=['created_by', '-created_at']),
            models.Index(fields=['is_archived', '-last_activity']),
        ]


class Message(models.Model):
    """Messages in chat rooms"""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'File'),
        ('location', 'Location'),
        ('system', 'System'),  # Added for system messages
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    content = models.TextField(max_length=2000, blank=True)
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPES,
        default='text'
    )

    # Media attachments with chatroom-based folders and type subfolders
    def message_media_path(instance, filename, media_type):
        room_id = str(instance.room.id)
        return f"messages/{room_id}/{media_type}/{filename}"

    def image_upload_to(instance, filename):
        return Message.message_media_path(instance, filename, 'images')

    def video_upload_to(instance, filename):
        return Message.message_media_path(instance, filename, 'videos')

    def audio_upload_to(instance, filename):
        return Message.message_media_path(instance, filename, 'audio')

    def file_upload_to(instance, filename):
        return Message.message_media_path(instance, filename, 'files')

    image = models.ImageField(
        upload_to=image_upload_to,
        blank=True,
        null=True
    )
    video = models.FileField(
        upload_to=video_upload_to,
        blank=True,
        null=True
    )
    audio = models.FileField(
        upload_to=audio_upload_to,
        blank=True,
        null=True
    )
    file = models.FileField(
        upload_to=file_upload_to,
        blank=True,
        null=True
    )

    # Enhanced message features
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )  # Message threading/replies

    forward_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='forwards'
    )  # Message forwarding

    mentions = models.ManyToManyField(
        UserProfile,
        blank=True,
        related_name='mentioned_in_messages'
    )  # User mentions

    # Message status
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    # Restoration tracking fields
    is_pinned = models.BooleanField(default=False)  # Pin important messages

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate that only verified users can send messages."""
        super().clean()
        from accounts.permissions import validate_user_for_interaction
        validate_user_for_interaction(self.sender, "send messages")

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        content_preview = (
            self.content[:50] + "..." if len(self.content) > 50
            else self.content
        )
        return f"{self.sender.user.username}: {content_preview}"

    class Meta:
        indexes = [
            models.Index(fields=['room', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['reply_to', '-created_at']),
            models.Index(fields=['is_pinned', '-created_at']),
        ]
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



class MessageRead(models.Model):
    """Track message read status."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_by'
    )
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
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
    class Meta:
        unique_together = ('message', 'user')
        indexes = [
            models.Index(fields=['user', '-read_at']),
            models.Index(fields=['message', 'user']),
        ]

    def __str__(self):
        return f"{self.user.username} read {self.message.id}"


class MessageReaction(models.Model):
    """Message reactions (emojis) - flexible system."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Common default reactions for quick access
    DEFAULT_REACTIONS = [
        '👍', '👎', '❤️', '😂', '😮', '😢', '🎉',
        '💯', '🤔', '😍', '🤝', '👏', '💪', '🙏'
    ]

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    # Flexible emoji field - can be any unicode emoji
    emoji = models.CharField(max_length=20)  # Support for complex emojis

    # Soft delete field

    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validate that only verified users can react to messages."""
        super().clean()
        from accounts.permissions import validate_user_for_interaction
        validate_user_for_interaction(self.user, "react to messages")

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('message', 'user', 'emoji')
        indexes = [
            models.Index(fields=['message', 'emoji']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to message"

    @classmethod
    def get_default_reactions(cls):
        """Get list of default/popular reactions for UI quick-select"""
        return cls.DEFAULT_REACTIONS
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



# NOTE: TypingIndicator moved to Redis implementation
# See messaging/utils.py for Redis-based typing indicators
# Benefits: Real-time performance, auto-expiry, no DB overhead


class UserPresence(models.Model):
    """
    Track user online/offline status and activity

    Benefits of server-side presence:
    - Multi-device synchronization (online on any device = online)
    - Last seen tracking for offline users
    - Custom status messages that persist
    - Analytics on user engagement patterns
    - Smart notifications (don't notify offline users)
    - Business intelligence on peak usage times
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('away', 'Away'),        # Auto-set after inactivity
        ('busy', 'Busy'),        # Do not disturb
        ('offline', 'Offline'),  # Explicitly offline
        ('invisible', 'Invisible'),  # Appear offline but still online
    ]

    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='presence'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='offline'
    )
    last_seen = models.DateTimeField(auto_now=True)
    # Rich status features
    custom_status = models.CharField(max_length=100, blank=True)
    status_emoji = models.CharField(max_length=10, blank=True)  # Status emoji
    # Automatic away detection
    away_since = models.DateTimeField(null=True, blank=True)
    # Activity tracking
    total_online_time = models.DurationField(default=timedelta)  # Analytics
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
    # Restoration tracking fields
    # Restoration tracking fields
    class Meta:
        indexes = [
            models.Index(fields=['status', '-last_seen']),
            models.Index(fields=['-last_seen']),  # For "last seen" queries
        ]

    def __str__(self):
        status_display = f"{self.status_emoji} {self.status}" if self.status_emoji else self.status
        return f"{self.user.username} - {status_display}"

    def is_online(self):
        """Check if user is considered online (not offline)"""
        return self.status in ['online', 'away', 'busy', 'invisible']

    def get_display_status(self):
        """Get status to display to other users (respects invisible mode)"""
        if self.status == 'invisible':
            return 'offline'
        return self.status
