"""Poll models for creating and managing polls."""

import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from content.models import Post


class Poll(models.Model):
    """Poll configuration for posts with poll type."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Changed from OneToOneField to ForeignKey to support multiple polls per post
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='polls'
    )
    question = models.CharField(
        max_length=500, help_text="Main poll question"
    )

    # Poll ordering for multiple polls per post
    order = models.PositiveIntegerField(
        default=0, help_text="Display order for multiple polls"
    )

    # Poll settings
    multiple_choice = models.BooleanField(
        default=False, help_text="Allow multiple selections"
    )
    anonymous_voting = models.BooleanField(
        default=False, help_text="Hide voter identities"
    )

    # Poll duration
    expires_at = models.DateTimeField(
        null=True, blank=True, help_text="When the poll expires"
    )

    # Poll metrics
    total_votes = models.PositiveIntegerField(default=0)
    voters_count = models.PositiveIntegerField(
        default=0, help_text="Unique voters count"
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_closed = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate that only verified users can create polls."""
        super().clean()
        from accounts.permissions import validate_user_for_interaction
        if self.post and self.post.user:
            validate_user_for_interaction(self.post.user, "create polls")

    def __str__(self):
        question_str = str(self.question) if self.question else "Poll"
        return f"Poll: {question_str[:50]}"

    def save(self, *args, **kwargs):
        """Set default expiration if not provided."""
        if not self.expires_at:
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(days=1)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if the poll has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    class Meta:
        indexes = [
            models.Index(fields=['post', 'order']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_active', '-created_at']),
        ]
        ordering = ['order', 'created_at']
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



class PollOption(models.Model):
    """Individual options for a poll."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(
        Poll, on_delete=models.CASCADE, related_name='options'
    )
    text = models.CharField(max_length=200, help_text="Option text")
    order = models.PositiveIntegerField(default=0, help_text="Display order")

    # Option metrics
    votes_count = models.PositiveIntegerField(default=0)

    # Optional media attachment for the option
    image = models.ImageField(
        upload_to='polls/options/', blank=True, null=True
    )

    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        question_preview = (
            str(self.poll.question)[:30]
            if self.poll.question else "Poll"
        )
        return f"{question_preview} - {self.text}"

    @property
    def vote_percentage(self):
        """Calculate the percentage of votes for this option."""
        total_votes = self.poll.total_votes
        if total_votes == 0:
            return 0
        return round((self.votes_count / total_votes) * 100, 1)

    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['poll', 'order']),
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



class PollVote(models.Model):
    """Track individual poll votes."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(
        Poll, on_delete=models.CASCADE, related_name='votes'
    )
    option = models.ForeignKey(
        PollOption, on_delete=models.CASCADE, related_name='votes'
    )
    voter = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='poll_votes'
    )

    # Vote metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
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
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validate that only verified users can vote in polls."""
        super().clean()
        from accounts.permissions import validate_user_for_interaction
        from accounts.models import UserProfile
        try:
            user_profile = UserProfile.objects.get(user=self.voter)
            validate_user_for_interaction(user_profile, "vote in polls")
        except UserProfile.DoesNotExist:
            from django.core.exceptions import ValidationError
            raise ValidationError("User profile not found")

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        voter_name = (
            str(self.voter.username) if hasattr(self.voter, 'username')
            else "User"
        )
        option_text = (
            str(self.option.text) if hasattr(self.option, 'text')
            else "Option"
        )
        return f"{voter_name} voted for {option_text}"

    class Meta:
        # Prevent duplicate votes (unless multiple choice is enabled)
        unique_together = ('poll', 'voter', 'option')
        indexes = [
            models.Index(fields=['poll', '-created_at']),
            models.Index(fields=['voter', '-created_at']),
            models.Index(fields=['option', '-created_at']),
        ]


class PollVoter(models.Model):
    """Track unique voters per poll (for multiple choice polls)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(
        Poll, on_delete=models.CASCADE, related_name='unique_voters'
    )
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    votes_count = models.PositiveIntegerField(default=1)

    first_vote_at = models.DateTimeField(auto_now_add=True)
    last_vote_at = models.DateTimeField(auto_now=True)
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

    def clean(self):
        """Validate that only verified users can be poll voters."""
        super().clean()
        from accounts.permissions import validate_user_for_interaction
        from accounts.models import UserProfile
        try:
            user_profile = UserProfile.objects.get(user=self.voter)
            validate_user_for_interaction(user_profile, "vote in polls")
        except UserProfile.DoesNotExist:
            from django.core.exceptions import ValidationError
            raise ValidationError("User profile not found")

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('poll', 'voter')
        indexes = [
            models.Index(fields=['poll', '-first_vote_at']),
        ]

    def __str__(self):
        return f"{self.voter.username} - {self.poll.question[:30]}"
