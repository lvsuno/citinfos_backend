"""
Real-time WebSocket consumers for notifications system.

This module handles WebSocket connections for real-time notification delivery
across all Django apps in the equipment project.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.

    Handles user-specific notification channels for instant delivery
    of notifications from all Django apps (accounts, content, communities, etc.)
    """

    async def connect(self):
        """Accept WebSocket connection and add user to their notification group."""
        self.user = self.scope.get("user")

        if self.user and not isinstance(self.user, AnonymousUser):
            # Get user profile
            try:
                self.user_profile = await self.get_user_profile()
                self.notification_group = f"notifications_{self.user_profile.id}"

                # Join user-specific notification group
                await self.channel_layer.group_add(
                    self.notification_group,
                    self.channel_name
                )

                await self.accept()

                # Check if JWT token was renewed during authentication
                token_renewed = self.scope.get('token_renewed', False)
                new_jwt_token = self.scope.get('new_jwt_token')

                # Send initial connection confirmation
                connection_message = {
                    'type': 'connection_established',
                    'message': 'Real-time notifications connected',
                    'user_id': str(self.user_profile.id),
                    'timestamp': self.get_current_timestamp()
                }

                # If token was renewed during WebSocket authentication, send new token to client
                if token_renewed and new_jwt_token:
                    connection_message.update({
                        'token_renewed': True,
                        'new_jwt_token': new_jwt_token,
                        'message': 'Real-time notifications connected (JWT token renewed)'
                    })
                    logger.info(f"User {self.user.username} connected with JWT token renewal")

                await self.send(text_data=json.dumps(connection_message))

                logger.info(f"User {self.user.username} connected to notifications WebSocket")

            except Exception as e:
                logger.error(f"Error connecting user {self.user.username}: {e}")
                await self.close(code=4001)  # Custom close code for authentication error
        else:
            logger.warning("Unauthenticated user attempted WebSocket connection")

            # Check the authentication error for appropriate close code
            auth_error = self.scope.get('auth_error', 'authentication_required')

            if auth_error == 'missing_credentials':
                await self.close(code=4001)  # Authentication required
            elif auth_error == 'both_token_and_session_expired':
                await self.close(code=4004)  # Both token and session expired
            elif auth_error in ['invalid_token', 'token_expired']:
                await self.close(code=4002)  # Invalid token
            elif auth_error == 'session_expired':
                await self.close(code=4003)  # Session expired
            else:
                await self.close(code=4001)  # Generic authentication required

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'notification_group'):
            await self.channel_layer.group_discard(
                self.notification_group,
                self.channel_name
            )
            logger.info(f"User {self.user.username} disconnected from notifications WebSocket")

    @database_sync_to_async
    def get_user_profile(self):
        """Get user profile for the authenticated user."""
        from accounts.models import UserProfile
        return UserProfile.objects.get(user=self.user)

    def get_current_timestamp(self):
        """Get current timestamp in ISO format."""
        from django.utils import timezone
        return timezone.now().isoformat()

    async def receive(self, text_data):
        """Handle incoming WebSocket messages from client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                # Respond to ping with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': self.get_current_timestamp()
                }))

            elif message_type == 'mark_notification_read':
                # Handle marking notification as read
                notification_id = data.get('notification_id')
                if notification_id:
                    await self.mark_notification_read(notification_id)

            elif message_type == 'get_notification_summary':
                # Send current notification summary
                summary = await self.get_notification_summary()
                await self.send(text_data=json.dumps({
                    'type': 'notification_summary',
                    'data': summary,
                    'timestamp': self.get_current_timestamp()
                }))

            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error("Invalid JSON received from WebSocket client")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark a notification as read."""
        from notifications.models import Notification
        try:
            notification = Notification.objects.get(
                id=notification_id,
                profile=self.user_profile
            )
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            return True
        except Notification.DoesNotExist:
            return False

    @database_sync_to_async
    def get_notification_summary(self):
        """Get notification summary for the user."""
        from notifications.serializers import NotificationSummarySerializer
        serializer = NotificationSummarySerializer()
        return serializer.to_representation(self.user_profile)

    # WebSocket message handlers for different notification types
    async def notification_message(self, event):
        """Handle general notification messages."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['data'],
            'timestamp': self.get_current_timestamp()
        }))

    async def moderation_notification(self, event):
        """Handle moderation-specific notifications."""
        await self.send(text_data=json.dumps({
            'type': 'moderation_notification',
            'data': event['data'],
            'priority': 'high',
            'timestamp': self.get_current_timestamp()
        }))

    async def social_notification(self, event):
        """Handle social notifications (follows, likes, comments)."""
        await self.send(text_data=json.dumps({
            'type': 'social_notification',
            'data': event['data'],
            'timestamp': self.get_current_timestamp()
        }))

    async def system_notification(self, event):
        """Handle system notifications (maintenance, updates, etc.)."""
        await self.send(text_data=json.dumps({
            'type': 'system_notification',
            'data': event['data'],
            'priority': event.get('priority', 'medium'),
            'timestamp': self.get_current_timestamp()
        }))

    async def community_notification(self, event):
        """Handle community-specific notifications."""
        await self.send(text_data=json.dumps({
            'type': 'community_notification',
            'data': event['data'],
            'community_id': event.get('community_id'),
            'timestamp': self.get_current_timestamp()
        }))


    async def poll_notification(self, event):
        """Handle poll-related notifications."""
        await self.send(text_data=json.dumps({
            'type': 'poll_notification',
            'data': event['data'],
            'poll_id': event.get('poll_id'),
            'timestamp': self.get_current_timestamp()
        }))

    async def ai_conversation_notification(self, event):
        """Handle AI conversation notifications."""
        await self.send(text_data=json.dumps({
            'type': 'ai_conversation_notification',
            'data': event['data'],
            'conversation_id': event.get('conversation_id'),
            'timestamp': self.get_current_timestamp()
        }))

    async def messaging_notification(self, event):
        """Handle messaging notifications."""
        await self.send(text_data=json.dumps({
            'type': 'messaging_notification',
            'data': event['data'],
            'chat_id': event.get('chat_id'),
            'priority': 'high',  # Messages are usually high priority
            'timestamp': self.get_current_timestamp()
        }))

    async def analytics_notification(self, event):
        """Handle analytics and reporting notifications."""
        await self.send(text_data=json.dumps({
            'type': 'analytics_notification',
            'data': event['data'],
            'report_type': event.get('report_type'),
            'timestamp': self.get_current_timestamp()
        }))


class AdminNotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for admin notifications.

    Handles admin-specific notifications like moderation alerts,
    system status, and bulk operations.
    """

    async def connect(self):
        """Accept WebSocket connection for admin users."""
        self.user = self.scope.get("user")

        if self.user and not isinstance(self.user, AnonymousUser):
            try:
                self.user_profile = await self.get_user_profile()

                # Check if user has admin/moderator privileges
                if await self.is_admin_user():
                    self.admin_group = "admin_notifications"

                    await self.channel_layer.group_add(
                        self.admin_group,
                        self.channel_name
                    )

                    await self.accept()

                    await self.send(text_data=json.dumps({
                        'type': 'admin_connection_established',
                        'message': 'Admin real-time notifications connected',
                        'user_id': str(self.user_profile.id),
                        'timestamp': self.get_current_timestamp()
                    }))

                    logger.info(f"Admin user {self.user.username} connected to admin notifications")
                else:
                    await self.close(code=4003)  # Insufficient privileges
            except Exception as e:
                logger.error(f"Error connecting admin user {self.user.username}: {e}")
                await self.close(code=4001)
        else:
            await self.close(code=4001)

    async def disconnect(self, close_code):
        """Handle admin WebSocket disconnection."""
        if hasattr(self, 'admin_group'):
            await self.channel_layer.group_discard(
                self.admin_group,
                self.channel_name
            )
            logger.info(f"Admin user {self.user.username} disconnected from admin notifications")

    @database_sync_to_async
    def get_user_profile(self):
        """Get user profile for the authenticated user."""
        from accounts.models import UserProfile
        return UserProfile.objects.get(user=self.user)

    @database_sync_to_async
    def is_admin_user(self):
        """Check if user has admin or moderator privileges."""
        return (self.user.is_staff or
                self.user.is_superuser or
                self.user_profile.role in ['admin', 'moderator'])

    def get_current_timestamp(self):
        """Get current timestamp in ISO format."""
        from django.utils import timezone
        return timezone.now().isoformat()

    async def receive(self, text_data):
        """Handle incoming WebSocket messages from admin client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': self.get_current_timestamp()
                }))

            elif message_type == 'get_moderation_queue':
                # Send current moderation queue status
                queue_status = await self.get_moderation_queue_status()
                await self.send(text_data=json.dumps({
                    'type': 'moderation_queue_status',
                    'data': queue_status,
                    'timestamp': self.get_current_timestamp()
                }))

        except json.JSONDecodeError:
            logger.error("Invalid JSON received from admin WebSocket client")
        except Exception as e:
            logger.error(f"Error processing admin WebSocket message: {e}")

    @database_sync_to_async
    def get_moderation_queue_status(self):
        """Get current moderation queue status."""
        from content.models import ContentReport, ModerationQueue

        pending_reports = ContentReport.objects.filter(
            status='pending',
            is_deleted=False
        ).count()

        queue_items = ModerationQueue.objects.filter(
            status='pending',
            is_deleted=False
        ).count()

        return {
            'pending_reports': pending_reports,
            'queue_items': queue_items,
            'total_pending': pending_reports + queue_items
        }

    # Admin-specific message handlers
    async def admin_alert(self, event):
        """Handle admin alerts."""
        await self.send(text_data=json.dumps({
            'type': 'admin_alert',
            'data': event['data'],
            'severity': event.get('severity', 'high'),
            'timestamp': self.get_current_timestamp()
        }))

    async def moderation_alert(self, event):
        """Handle moderation alerts for admins."""
        await self.send(text_data=json.dumps({
            'type': 'moderation_alert',
            'data': event['data'],
            'action_required': event.get('action_required', True),
            'timestamp': self.get_current_timestamp()
        }))

    async def system_status(self, event):
        """Handle system status updates."""
        await self.send(text_data=json.dumps({
            'type': 'system_status',
            'data': event['data'],
            'status': event.get('status', 'info'),
            'timestamp': self.get_current_timestamp()
        }))

    async def bulk_operation_status(self, event):
        """Handle bulk operation status updates."""
        await self.send(text_data=json.dumps({
            'type': 'bulk_operation_status',
            'data': event['data'],
            'operation_id': event.get('operation_id'),
            'progress': event.get('progress', 0),
            'timestamp': self.get_current_timestamp()
        }))
