"""
Example implementation showing how to integrate notifications into existing APIs.

This file demonstrates different approaches for adding notification data to API responses.
"""

# Approach 1: Using the decorator (simplest)
from notifications.views import with_notifications
from rest_framework.decorators import api_view
from rest_framework.response import Response


@with_notifications
@api_view(['GET'])
def example_api_with_auto_notifications(request):
    """
    Example API that automatically includes notification summary.
    The @with_notifications decorator adds notification data to response.
    """
    return Response({
        'posts': ['post1', 'post2', 'post3'],
        'message': 'Posts retrieved successfully'
    })
    # Response will automatically include:
    # {
    #   'posts': [...],
    #   'message': '...',
    #   'notifications': {
    #     'has_notifications': True,
    #     'unread_count': 5,
    #     'urgent_alerts': [...]
    #   }
    # }


# Approach 2: Manual integration (more control)
from notifications.views import add_notification_summary
from rest_framework import generics


class ExamplePostListView(generics.ListAPIView):
    """
    Example API view that manually adds notification data.
    This gives you full control over when/how to include notifications.
    """

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        # Add notification summary to response
        add_notification_summary(response.data, request.user.profile)

        # Add any custom notification logic here
        if response.data.get('notifications', {}).get('unread_count', 0) > 10:
            response.data['alert'] = 'You have many unread notifications!'

        return response


# Approach 3: Field in serializer (for object-specific notifications)
from rest_framework import serializers
from notifications.serializers import InlineNotificationSerializer


class PostWithNotificationsSerializer(serializers.ModelSerializer):
    """
    Example serializer that includes notification data for the current user.
    Useful when you want notifications in the context of specific objects.
    """

    notifications = serializers.SerializerMethodField()

    def get_notifications(self, obj):
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile'):
            serializer = InlineNotificationSerializer()
            return serializer.to_representation(request.user.profile)
        return None

    class Meta:
        fields = ['id', 'title', 'content', 'notifications']


# Approach 4: WebSocket/SSE for real-time notifications (advanced)
"""
For real-time notifications, you can implement WebSocket or Server-Sent Events.

Example WebSocket consumer (if using Django Channels):

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from notifications.utils import NotificationService

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            await self.channel_layer.group_add(
                f"notifications_{self.scope['user'].profile.id}",
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.scope["user"].is_authenticated:
            await self.channel_layer.group_discard(
                f"notifications_{self.scope['user'].profile.id}",
                self.channel_name
            )

    async def notification_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

# To send real-time notifications:
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_realtime_notification(user_profile, notification_data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notifications_{user_profile.id}",
        {
            "type": "notification_message",
            "message": notification_data
        }
    )
"""


# Integration with existing moderation system
def integrate_moderation_notifications():
    """
    Example of how to integrate moderation notifications into your content app.
    Add these imports and calls to your content/utils.py or content/signals.py
    """

    # In content/utils.py - add these imports:
    # from notifications.moderation import (
    #     send_moderation_notification,
    #     update_moderation_metrics
    # )

    # Example usage in your moderation functions:

    def example_content_approved(user, content, moderator):
        """Example of content approval with notification."""
        # Your existing approval logic here
        content.is_approved = True
        content.save()

        # Send notification
        # send_moderation_notification(user, 'content_approved', {
        #     'content_id': content.id,
        #     'moderator': moderator.user.username if moderator else None
        # })

        # Update metrics
        # update_moderation_metrics('approval', 'approved', 0.95)

    def example_content_removed(user, content, reason, moderator):
        """Example of content removal with notification."""
        # Your existing removal logic here
        content.is_deleted = True
        content.save()

        # Send notification
        # send_moderation_notification(user, 'content_removed', {
        #     'content_id': content.id,
        #     'message': f'Your content was removed: {reason}',
        #     'moderator': moderator.user.username if moderator else None,
        #     'extra_data': {
        #         'removal_reason': reason,
        #         'appeal_available': True
        #     }
        # })

        # Update metrics
        # update_moderation_metrics('removal', 'removed', 0.87)


# Real-world usage examples for your specific endpoints

class ContentAPIViewWithNotifications:
    """
    Example of how to modify your existing content views.
    """

    @with_notifications  # Option 1: Automatic
    def get_posts(self, request):
        # Your existing logic
        posts = []  # Your post query
        return Response({'posts': posts})

    def create_post(self, request):
        # Your existing post creation logic
        post = None  # Your created post

        # Manual notification integration (Option 2)
        response_data = {'post': post, 'message': 'Post created'}
        add_notification_summary(response_data, request.user.profile)

        return Response(response_data)


# Configuration example for your settings.py
NOTIFICATION_SETTINGS_EXAMPLE = """
# Add to your settings.py

# Notification configuration
NOTIFICATIONS = {
    'REAL_TIME_ENABLED': False,  # Enable WebSocket/SSE
    'EMAIL_NOTIFICATIONS': True,
    'SMS_NOTIFICATIONS': False,
    'BATCH_SIZE': 100,  # For bulk notifications
    'RETENTION_DAYS': 30,  # Auto-delete old notifications
}

# If using WebSocket for real-time notifications
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
"""
