"""WebSocket consumers for real-time visitor analytics."""

import json
import logging
from typing import Dict, Any
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


class VisitorAnalyticsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time visitor count updates.

    Broadcasts visitor count changes to all connected clients for a community.
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.community_id = self.scope['url_route']['kwargs']['community_id']
        self.room_group_name = f'visitors_{self.community_id}'
        self.user = self.scope.get('user')

        # Visitor analytics is public - anyone can view visitor counts
        # Just verify the community exists
        community_exists = await self.check_community_exists()

        if not community_exists:
            await self.close(code=4004)  # Custom code for not found
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial visitor count
        initial_count = await self.get_visitor_count()
        await self.send(text_data=json.dumps({
            'type': 'visitor_count',
            'community_id': self.community_id,
            'count': initial_count,
            'timestamp': self.get_timestamp()
        }))

        logger.info(
            f"User {self.user.id if self.user and self.user.is_authenticated else 'anonymous'} "
            f"connected to visitors_{self.community_id}"
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

        logger.info(
            f"User disconnected from {self.room_group_name} "
            f"with code {close_code}"
        )

    async def receive(self, text_data):
        """
        Handle messages from WebSocket.

        Supports:
        - ping/pong for keepalive
        - request_count for manual refresh
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': self.get_timestamp()
                }))

            elif message_type == 'request_count':
                count = await self.get_visitor_count()
                await self.send(text_data=json.dumps({
                    'type': 'visitor_count',
                    'community_id': self.community_id,
                    'count': count,
                    'timestamp': self.get_timestamp()
                }))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error in receive: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal error'
            }))

    async def visitor_count_update(self, event):
        """
        Handle visitor count update messages from channel layer.

        Called when a message is sent to the group.
        """
        await self.send(text_data=json.dumps({
            'type': 'visitor_count',
            'community_id': event['community_id'],
            'count': event['count'],
            'change': event.get('change', 0),
            'timestamp': event.get('timestamp', self.get_timestamp())
        }))

    async def visitor_joined(self, event):
        """Handle visitor joined event."""
        await self.send(text_data=json.dumps({
            'type': 'visitor_joined',
            'community_id': event['community_id'],
            'count': event['count'],
            'timestamp': event.get('timestamp', self.get_timestamp())
        }))

    async def visitor_left(self, event):
        """Handle visitor left event."""
        await self.send(text_data=json.dumps({
            'type': 'visitor_left',
            'community_id': event['community_id'],
            'count': event['count'],
            'timestamp': event.get('timestamp', self.get_timestamp())
        }))

    @database_sync_to_async
    def check_community_exists(self) -> bool:
        """Check if community exists and is not deleted."""
        from communities.models import Community

        try:
            Community.objects.get(
                id=self.community_id,
                is_deleted=False
            )
            return True
        except ObjectDoesNotExist:
            return False

    @database_sync_to_async
    def check_community_access(self) -> bool:
        """
        Check if user has access to community analytics.

        For VisitorAnalyticsConsumer, this is public (returns True).
        For VisitorDashboardConsumer, requires membership.
        """
        # This method kept for compatibility but not used by VisitorAnalyticsConsumer
        from communities.models import Community, CommunityMembership

        if not self.user or not self.user.is_authenticated:
            return False

        try:
            community = Community.objects.get(
                id=self.community_id,
                is_deleted=False
            )

            # Check if user is a member
            membership = CommunityMembership.objects.filter(
                community=community,
                user=self.user.profile,
                status='active',
                is_deleted=False
            ).exists()

            return membership

        except ObjectDoesNotExist:
            return False

    @database_sync_to_async
    def get_visitor_count(self) -> int:
        """Get current visitor count from Redis."""
        from analytics.services import online_tracker

        try:
            return online_tracker.get_online_count(self.community_id)
        except Exception as e:
            logger.error(f"Error getting visitor count: {e}")
            return 0

    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from django.utils import timezone
        return timezone.now().isoformat()


class VisitorDashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for visitor analytics dashboard.

    Provides real-time updates of visitor statistics for moderators/admins.
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.community_id = self.scope['url_route']['kwargs']['community_id']
        self.room_group_name = f'visitor_dashboard_{self.community_id}'
        self.user = self.scope.get('user')

        # Check if user has moderator/admin access
        has_access = await self.check_dashboard_access()

        if not has_access:
            await self.close(code=4003)
            return

        # Join dashboard group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial dashboard data
        dashboard_data = await self.get_dashboard_data()
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'data': dashboard_data,
            'timestamp': self.get_timestamp()
        }))

        logger.info(
            f"User {self.user.id} connected to visitor dashboard "
            f"for community {self.community_id}"
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': self.get_timestamp()
                }))

            elif message_type == 'request_update':
                dashboard_data = await self.get_dashboard_data()
                await self.send(text_data=json.dumps({
                    'type': 'dashboard_update',
                    'data': dashboard_data,
                    'timestamp': self.get_timestamp()
                }))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error in dashboard receive: {e}")

    async def dashboard_update(self, event):
        """Handle dashboard update messages from channel layer."""
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'data': event['data'],
            'timestamp': event.get('timestamp', self.get_timestamp())
        }))

    async def analytics_update(self, event):
        """Handle analytics update events."""
        await self.send(text_data=json.dumps({
            'type': 'analytics_update',
            'metric': event['metric'],
            'value': event['value'],
            'timestamp': event.get('timestamp', self.get_timestamp())
        }))

    @database_sync_to_async
    def check_dashboard_access(self) -> bool:
        """
        Check if user has access to dashboard (admin only).

        Only community admins (role='Admin' in CommunityMembership) can access
        advanced analytics. Moderators can moderate content but not access analytics.
        """
        from communities.models import Community, CommunityMembership

        if not self.user or not self.user.is_authenticated:
            return False

        try:
            community = Community.objects.get(
                id=self.community_id,
                is_deleted=False
            )

            membership = CommunityMembership.objects.filter(
                community=community,
                user=self.user.profile,
                status='active',
                is_deleted=False
            ).first()

            if not membership or not membership.role:
                return False

            # Only 'Admin' role can access advanced analytics
            # Moderators can moderate posts but NOT access analytics
            return membership.role.name == 'Admin'

        except ObjectDoesNotExist:
            return False

    @database_sync_to_async
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        from analytics.visitor_utils import (
            get_today_visitors,
            get_realtime_visitors
        )

        try:
            # Get today's stats
            today_stats = get_today_visitors(self.community_id)

            # Get real-time count
            realtime_data = get_realtime_visitors(self.community_id)

            return {
                'today_visitors': today_stats,
                'realtime_count': realtime_data['current_online'],
                'community_id': self.community_id
            }

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                'today_visitors': {
                    'authenticated_visitors': 0,
                    'anonymous_visitors': 0,
                    'total_unique_visitors': 0
                },
                'realtime_count': 0,
                'community_id': self.community_id
            }

    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from django.utils import timezone
        return timezone.now().isoformat()
