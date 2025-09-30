"""
Notification serializers for API endpoints.
"""

from rest_framework import serializers
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from notifications.models import Notification
from accounts.models import UserProfile


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for in-app notifications."""

    sender_name = serializers.CharField(
        source='sender.user.username', read_only=True
    )
    sender_display_name = serializers.CharField(
        source='sender.display_name', read_only=True
    )
    time_ago = serializers.SerializerMethodField()
    content_type_name = serializers.CharField(
        source='content_type.model', read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'priority',
            'sender_name', 'sender_display_name', 'time_ago',
            'is_read', 'read_at', 'created_at', 'expires_at',
            'content_type_name', 'object_id', 'extra_data'
        ]
        read_only_fields = ['id', 'created_at']

    def get_time_ago(self, obj):
        """Get human-readable time ago."""
        from django.utils.timesince import timesince
        return timesince(obj.created_at, timezone.now())


class NotificationWithContentSerializer(serializers.ModelSerializer):
    """Enhanced notification serializer that includes the actual content object."""

    sender_name = serializers.CharField(
        source='sender.user.username', read_only=True
    )
    sender_display_name = serializers.CharField(
        source='sender.display_name', read_only=True
    )
    time_ago = serializers.SerializerMethodField()
    content_type_name = serializers.CharField(
        source='content_type.model', read_only=True
    )
    content_object = serializers.SerializerMethodField()
    action_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'priority',
            'sender_name', 'sender_display_name', 'time_ago',
            'is_read', 'read_at', 'created_at', 'expires_at',
            'content_type_name', 'object_id', 'extra_data',
            'content_object', 'action_url'
        ]
        read_only_fields = ['id', 'created_at']

    def get_time_ago(self, obj):
        """Get human-readable time ago."""
        from django.utils.timesince import timesince
        return timesince(obj.created_at, timezone.now())

    def get_content_object(self, obj):
        """Get the actual content object with relevant details."""
        if not obj.content_object:
            return None

        content_obj = obj.content_object
        content_type = obj.content_type.model

        try:
            # Handle different content types
            if content_type == 'post':
                return self._serialize_post(content_obj)
            elif content_type == 'comment':
                return self._serialize_comment(content_obj)
            elif content_type == 'message':
                return self._serialize_message(content_obj)
            elif content_type == 'communityrolemembership':
                return self._serialize_community_role_membership(content_obj)
            elif content_type == 'community':
                return self._serialize_community(content_obj)
            elif content_type == 'userprofile':
                return self._serialize_user_profile(content_obj)
            elif content_type == 'badge':
                return self._serialize_badge(content_obj)
            else:
                # Generic fallback
                return {
                    'id': getattr(content_obj, 'id', None),
                    'title': getattr(content_obj, 'title', None),
                    'name': getattr(content_obj, 'name', None),
                    'type': content_type
                }
        except Exception:
            return {
                'id': obj.object_id,
                'type': content_type,
                'error': 'Content object not available'
            }

    def get_action_url(self, obj):
        """Get the URL for the action the user should take."""
        if not obj.content_object:
            return None

        content_type = obj.content_type.model
        content_obj = obj.content_object

        try:
            # Generate appropriate URLs based on content type
            if content_type == 'post':
                return f"/posts/{content_obj.id}"
            elif content_type == 'comment':
                # Link to the parent post with comment highlighted
                if hasattr(content_obj, 'post'):
                    return f"/posts/{content_obj.post.id}#comment-{content_obj.id}"
            elif content_type == 'message':
                if hasattr(content_obj, 'conversation'):
                    return f"/conversations/{content_obj.conversation.id}"
            elif content_type == 'communityrolemembership':
                # For moderator nominations
                if obj.notification_type == 'moderator_nomination':
                    return f"/moderator-nomination/{obj.id}"
                elif hasattr(content_obj, 'community'):
                    return f"/communities/{content_obj.community.slug}"
            elif content_type == 'community':
                return f"/communities/{content_obj.slug}"
            elif content_type == 'userprofile':
                return f"/users/{content_obj.user.username}"
            elif content_type == 'badge':
                return f"/badges/{content_obj.id}"

            # Fallback to notification detail page
            return f"/notifications/{obj.id}"
        except Exception:
            return f"/notifications/{obj.id}"

    def _serialize_post(self, post):
        """Serialize post content."""
        return {
            'id': str(post.id),
            'title': post.title,
            'content_preview': post.content[:100] + '...' if len(post.content) > 100 else post.content,
            'author': post.author.display_name or post.author.user.username,
            'created_at': post.created_at.isoformat(),
            'community': {
                'name': post.community.name,
                'slug': post.community.slug
            } if hasattr(post, 'community') and post.community else None,
            'type': 'post'
        }

    def _serialize_comment(self, comment):
        """Serialize comment content."""
        return {
            'id': str(comment.id),
            'content_preview': comment.content[:100] + '...' if len(comment.content) > 100 else comment.content,
            'author': comment.author.display_name or comment.author.user.username,
            'created_at': comment.created_at.isoformat(),
            'post': {
                'id': str(comment.post.id),
                'title': comment.post.title
            } if hasattr(comment, 'post') else None,
            'type': 'comment'
        }

    def _serialize_message(self, message):
        """Serialize message content."""
        return {
            'id': str(message.id),
            'content_preview': message.content[:100] + '...' if len(message.content) > 100 else message.content,
            'sender': message.sender.display_name or message.sender.user.username,
            'created_at': message.created_at.isoformat(),
            'conversation': {
                'id': str(message.conversation.id),
                'title': getattr(message.conversation, 'title', 'Conversation')
            } if hasattr(message, 'conversation') else None,
            'type': 'message'
        }

    def _serialize_community_role_membership(self, membership):
        """Serialize community role membership (for moderator nominations)."""
        return {
            'id': str(membership.id),
            'role': membership.role.name if hasattr(membership, 'role') else 'Unknown',
            'community': {
                'id': str(membership.community.id),
                'name': membership.community.name,
                'slug': membership.community.slug,
                'description': membership.community.description[:100] + '...' if len(membership.community.description) > 100 else membership.community.description
            } if hasattr(membership, 'community') else None,
            'assigned_by': {
                'name': membership.assigned_by.display_name or membership.assigned_by.user.username,
                'username': membership.assigned_by.user.username
            } if hasattr(membership, 'assigned_by') and membership.assigned_by else None,
            'status': getattr(membership, 'status', 'pending'),
            'created_at': membership.created_at.isoformat() if hasattr(membership, 'created_at') else None,
            'type': 'community_role_membership'
        }

    def _serialize_community(self, community):
        """Serialize community content."""
        return {
            'id': str(community.id),
            'name': community.name,
            'slug': community.slug,
            'description': community.description[:100] + '...' if len(community.description) > 100 else community.description,
            'member_count': getattr(community, 'member_count', 0),
            'created_at': community.created_at.isoformat(),
            'type': 'community'
        }

    def _serialize_user_profile(self, user_profile):
        """Serialize user profile content."""
        return {
            'id': str(user_profile.id),
            'username': user_profile.user.username,
            'display_name': user_profile.display_name,
            'bio': user_profile.bio[:100] + '...' if user_profile.bio and len(user_profile.bio) > 100 else user_profile.bio,
            'joined_at': user_profile.user.date_joined.isoformat(),
            'type': 'user_profile'
        }

    def _serialize_badge(self, badge):
        """Serialize badge content."""
        return {
            'id': str(badge.id),
            'name': badge.name,
            'description': badge.description,
            'category': getattr(badge, 'category', 'general'),
            'icon': getattr(badge, 'icon', None),
            'rarity': getattr(badge, 'rarity', 'common'),
            'type': 'badge'
        }

    # def _serialize_equipment(self, equipment):
    #     """Serialize equipment content."""
    #     return {
    #         'id': str(equipment.id),
    #         'name': equipment.name,
    #         'description': equipment.description[:100] + '...' if equipment.description and len(equipment.description) > 100 else equipment.description,
    #         'category': getattr(equipment, 'category', 'general'),
    #         'owner': equipment.owner.display_name or equipment.owner.user.username if hasattr(equipment, 'owner') else None,
    #         'status': getattr(equipment, 'status', 'available'),
    #         'type': 'sment'
    #     }


class NotificationSummarySerializer(serializers.Serializer):
    """Serializer for notification summary/counts."""

    unread_count = serializers.IntegerField()
    total_count = serializers.IntegerField()
    has_high_priority = serializers.BooleanField()
    latest_notification = NotificationSerializer(required=False, allow_null=True)


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read."""

    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="List of notification IDs to mark as read. If empty, marks all as read."
    )


class NotificationPreferencesSerializer(serializers.Serializer):
    """Serializer for user notification preferences."""

    email_notifications = serializers.BooleanField(default=True)
    push_notifications = serializers.BooleanField(default=True)
    sms_notifications = serializers.BooleanField(default=False)

    # Content-specific preferences
    content_likes = serializers.BooleanField(default=True)
    content_comments = serializers.BooleanField(default=True)
    content_mentions = serializers.BooleanField(default=True)
    content_shares = serializers.BooleanField(default=True)

    # Moderation preferences
    moderation_updates = serializers.BooleanField(default=True)
    security_alerts = serializers.BooleanField(default=True)
    account_restrictions = serializers.BooleanField(default=True)

    # System preferences
    system_maintenance = serializers.BooleanField(default=True)
    feature_updates = serializers.BooleanField(default=False)
    digest_emails = serializers.BooleanField(default=True)


class ModerationNotificationSerializer(serializers.Serializer):
    """Serializer for moderation-specific notifications."""

    action_type = serializers.ChoiceField(
        choices=[
            ('content_approved', 'Content Approved'),
            ('content_removed', 'Content Removed'),
            ('account_restricted', 'Account Restricted'),
            ('bot_detection', 'Bot Detection'),
            ('warning_issued', 'Warning Issued'),
            ('suspension_lifted', 'Suspension Lifted'),
        ]
    )

    title = serializers.CharField(max_length=200)
    message = serializers.CharField(max_length=500)

    # Moderation-specific fields
    content_id = serializers.UUIDField(required=False, allow_null=True)
    moderator = serializers.CharField(required=False, allow_null=True)
    appeal_available = serializers.BooleanField(default=False)
    restriction_duration = serializers.CharField(required=False, allow_null=True)

    # Additional context
    extra_data = serializers.JSONField(required=False, allow_null=True)


class InlineNotificationSerializer(serializers.Serializer):
    """Lightweight serializer for notification data in API responses."""

    has_notifications = serializers.BooleanField()
    unread_count = serializers.IntegerField()
    urgent_alerts = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )

    def to_representation(self, user_profile):
        """Generate notification summary for a user."""
        from notifications.utils import NotificationService

        if not user_profile:
            return {
                'has_notifications': False,
                'unread_count': 0,
                'urgent_alerts': []
            }

        # Get unread count
        unread_count = NotificationService.get_unread_count(user_profile)

        # Get urgent alerts (high priority unread notifications)
        urgent_notifications = Notification.objects.filter(
            recipient=user_profile,
            is_read=False,
            priority__lte=2,  # High and Elevated priority
            is_deleted=False
        ).order_by('priority', '-created_at')[:3]

        urgent_alerts = []
        for notification in urgent_notifications:
            urgent_alerts.append({
                'id': str(notification.id),
                'title': notification.title,
                'type': notification.notification_type,
                'priority': notification.priority,
                'created_at': notification.created_at.isoformat()
            })

        return {
            'has_notifications': unread_count > 0,
            'unread_count': unread_count,
            'urgent_alerts': urgent_alerts
        }
