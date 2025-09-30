"""AI conversation models for the AI system."""

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import UserProfile


class LLMModel(models.Model):
    """LLM models configuration for AI conversations."""
    MODEL_TYPES = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('google', 'Google'),
        ('huggingface', 'Hugging Face'),
        ('custom', 'Custom'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('deprecated', 'Deprecated'),
        ('maintenance', 'Maintenance'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    model_id = models.CharField(max_length=200)
    api_endpoint = models.URLField(blank=True)

    # Configuration
    max_tokens = models.PositiveIntegerField(default=4096)
    temperature = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)]
    )
    top_p = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )

    # Cost management
    cost_per_input_token = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        default=Decimal('0')
    )
    cost_per_output_token = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        default=Decimal('0')
    )

    # Status and limits
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    daily_request_limit = models.PositiveIntegerField(default=1000)
    rate_limit_per_minute = models.PositiveIntegerField(default=60)

    # Capabilities
    supports_streaming = models.BooleanField(default=True)
    supports_function_calling = models.BooleanField(default=False)
    supports_vision = models.BooleanField(default=False)

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
    # Restoration tracking fields
    # Restoration tracking fields
    # Restoration tracking fields
    # Restoration tracking fields
    def __str__(self):
        return f"{self.name} ({self.model_type})"

    class Meta:
        indexes = [
            models.Index(fields=['model_type', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]


class ConversationAgent(models.Model):
    """AI agents with specific personalities and roles."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    AGENT_TYPES = [
        ('assistant', 'General Assistant'),
        ('expert', 'Domain Expert'),
        ('tutor', 'Educational Tutor'),
        ('custom', 'Custom Role'),
    ]

    name = models.CharField(max_length=100)
    agent_type = models.CharField(max_length=20, choices=AGENT_TYPES)
    description = models.TextField(max_length=1000)

    # Agent configuration
    system_prompt = models.TextField(
        help_text="System prompt that defines the agent's personality and role"
    )
    preferred_model = models.ForeignKey(
        LLMModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Behavior settings
    temperature_override = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)]
    )
    max_tokens_override = models.PositiveIntegerField(null=True, blank=True)

    # Features
    can_browse_web = models.BooleanField(default=False)
    can_analyze_images = models.BooleanField(default=False)
    can_generate_images = models.BooleanField(default=False)
    can_code = models.BooleanField(default=True)

    # Metadata
    avatar = models.ImageField(
        upload_to='agents/avatars/',
        blank=True,
        null=True
    )
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Usage stats
    total_conversations = models.PositiveIntegerField(default=0)
    total_messages = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0.0)

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
    # Restoration tracking fields
    # Restoration tracking fields
    # Restoration tracking fields
    # Restoration tracking fields
    def __str__(self):
        return f"{self.name} ({self.agent_type})"

    class Meta:
        indexes = [
            models.Index(fields=['agent_type', 'is_active']),
            models.Index(fields=['is_public', 'is_active']),
            models.Index(fields=['created_by', '-created_at']),
        ]


class AIConversation(models.Model):
    """Individual AI conversation sessions between users and AI agents."""
    CONVERSATION_STATUS = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='ai_conversations'
    )
    agent = models.ForeignKey(
        ConversationAgent,
        on_delete=models.CASCADE,
        related_name='conversations'
    )

    title = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=20,
        choices=CONVERSATION_STATUS,
        default='active'
    )

    # Conversation metadata
    total_messages = models.PositiveIntegerField(default=0)
    total_tokens_used = models.PositiveIntegerField(default=0)
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=Decimal('0')
    )
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields

    # Settings
    context_window = models.PositiveIntegerField(default=10)
    auto_summarize = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        title_display = self.title or f"Conversation with {self.agent.name}"
        return f"{title_display} - {self.user.user.username}"

    def clean(self):
        """Validate that only verified, non-suspended users can create AI conversations."""
        super().clean()
        from accounts.permissions import validate_user_for_interaction
        validate_user_for_interaction(self.user, "create AI conversations")

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['user', '-last_message_at']),
            models.Index(fields=['agent', '-created_at']),
            models.Index(fields=['status', '-updated_at']),
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



class AIMessage(models.Model):
    """Individual messages in AI conversations."""
    MESSAGE_ROLES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
        ('function', 'Function'),
    ]

    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('code', 'Code'),
        ('function_call', 'Function Call'),
        ('function_result', 'Function Result'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    role = models.CharField(max_length=20, choices=MESSAGE_ROLES)
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default='text'
    )
    content = models.TextField()

    # Token usage and cost tracking
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        default=Decimal('0')
    )

    # Processing metadata
    model_used = models.ForeignKey(
        LLMModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    response_time = models.FloatField(null=True, blank=True)

    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    attachments = models.JSONField(default=list, blank=True)

    # Status
    is_error = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        content_preview = (
            self.content[:50] + "..." if len(self.content) > 50
            else self.content
        )
        return f"{self.role}: {content_preview}"

    def clean(self):
        """Validate that only verified, non-suspended users can send messages."""
        super().clean()
        # Only validate for user messages, not assistant/system messages
        if self.role == 'user':
            from accounts.permissions import validate_user_for_interaction
            validate_user_for_interaction(
                self.conversation.user,
                "send AI messages"
            )

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['role', '-created_at']),
            models.Index(fields=['message_type', '-created_at']),
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



class AIMessageRating(models.Model):
    """User helpfulness rating (single 1-5 score) for AI responses."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    message = models.ForeignKey(
        AIMessage,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    # Single helpful score 1..5
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
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
    # Restoration tracking fields
    # Restoration tracking fields
    # Restoration tracking fields
    # Restoration tracking fields

    def clean(self):
        """Validate that only verified users can rate messages."""
        super().clean()
        from accounts.permissions import validate_user_for_interaction
        validate_user_for_interaction(self.user, "rate AI messages")

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('message', 'user')
        indexes = [
            models.Index(fields=['message', '-created_at']),
        ]

    def __str__(self):  # noqa: D401
        return f"helpful: {self.score}/5"


class AIMessageFlag(models.Model):
    """Problem / issue flags for AI responses (binary signals)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    FLAG_TYPES = [
        ('safety_issue', 'Safety Issue'),
        ('inappropriate', 'Inappropriate'),
        ('factual_error', 'Factual Error'),
        ('outdated', 'Outdated Info'),
        ('off_topic', 'Off Topic'),
    ]

    message = models.ForeignKey(
        AIMessage,
        on_delete=models.CASCADE,
        related_name='flags'
    )
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    flag_type = models.CharField(max_length=30, choices=FLAG_TYPES)
    comment = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
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
    # Restoration tracking fields
    # Restoration tracking fields
    # Restoration tracking fields
    # Restoration tracking fields
    class Meta:
        unique_together = ('message', 'user', 'flag_type')
        indexes = [
            models.Index(fields=['flag_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.flag_type} flag on {self.message.id}"


class AIUsageAnalytics(models.Model):
    """Track AI usage analytics per user."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='ai_usage'
    )
    date = models.DateField()

    # Usage metrics
    conversations_started = models.PositiveIntegerField(default=0)
    messages_sent = models.PositiveIntegerField(default=0)
    tokens_consumed = models.PositiveIntegerField(default=0)
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=Decimal('0')
    )

    # Time metrics
    total_time_spent = models.DurationField(default=timezone.timedelta(0))
    average_response_time = models.FloatField(default=0.0)

    # Feature usage
    image_analysis_requests = models.PositiveIntegerField(default=0)
    code_generation_requests = models.PositiveIntegerField(default=0)
    web_browsing_requests = models.PositiveIntegerField(default=0)

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
    # Restoration tracking fields
    # Restoration tracking fields
    # Restoration tracking fields
    # Restoration tracking fields
    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"AI Usage {self.user.user.username} - {self.date}"


class AIModelPerformance(models.Model):
    """Track performance metrics for AI models."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        LLMModel,
        on_delete=models.CASCADE,
        related_name='performance_metrics'
    )
    date = models.DateField()

    # Usage metrics
    total_requests = models.PositiveIntegerField(default=0)
    successful_requests = models.PositiveIntegerField(default=0)
    failed_requests = models.PositiveIntegerField(default=0)

    # Performance metrics
    average_response_time = models.FloatField(default=0.0)
    average_tokens_per_request = models.FloatField(default=0.0)
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=Decimal('0')
    )

    # Quality metrics
    average_user_rating = models.FloatField(default=0.0)
    total_user_ratings = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
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
    # Restoration tracking fields
    # Restoration tracking fields
    # Restoration tracking fields
    # Restoration tracking fields
    class Meta:
        unique_together = ('model', 'date')
        indexes = [
            models.Index(fields=['model', '-date']),
            models.Index(fields=['date', '-average_user_rating']),
        ]

    def __str__(self):
        return f"{self.model.name} Performance - {self.date}"


class AIConversationSummary(models.Model):
    """Automated summaries of AI conversations."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.OneToOneField(
        AIConversation,
        on_delete=models.CASCADE,
        related_name='summary'
    )

    # Summary content
    title_suggestion = models.CharField(max_length=200, blank=True)
    summary_text = models.TextField()
    key_topics = models.JSONField(default=list, blank=True)

    # Metadata
    message_count_at_summary = models.PositiveIntegerField()
    summary_model = models.ForeignKey(
        LLMModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

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
    # Restoration tracking fields
    # Restoration tracking fields
    # Restoration tracking fields
    # Restoration tracking fields
    def __str__(self):
        return f"Summary for {self.conversation}"

    class Meta:
        indexes = [
            models.Index(fields=['conversation', '-updated_at']),
        ]
