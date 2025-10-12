"""Utility functions for broadcasting visitor analytics via WebSockets."""

import logging
from typing import Optional
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

logger = logging.getLogger(__name__)


class VisitorBroadcaster:
    """Utility class for broadcasting visitor count updates via WebSockets."""

    def __init__(self):
        self.channel_layer = get_channel_layer()

    def broadcast_visitor_count(
        self,
        community_id: str,
        count: int,
        change: int = 0
    ) -> None:
        """
        Broadcast visitor count update to all connected clients.

        Args:
            community_id: UUID of the community
            count: Current visitor count
            change: Change in count (+1 for join, -1 for leave)
        """
        if not self.channel_layer:
            logger.warning("Channel layer not configured")
            return

        room_group_name = f'visitors_{community_id}'

        try:
            async_to_sync(self.channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'visitor_count_update',
                    'community_id': str(community_id),
                    'count': count,
                    'change': change,
                    'timestamp': timezone.now().isoformat()
                }
            )
            logger.debug(
                f"Broadcasted visitor count {count} "
                f"(change: {change:+d}) to {room_group_name}"
            )
        except Exception as e:
            logger.error(
                f"Error broadcasting visitor count for {community_id}: {e}"
            )

    def broadcast_visitor_joined(
        self,
        community_id: str,
        count: int
    ) -> None:
        """
        Broadcast that a visitor has joined.

        Args:
            community_id: UUID of the community
            count: New visitor count after join
        """
        if not self.channel_layer:
            return

        room_group_name = f'visitors_{community_id}'

        try:
            async_to_sync(self.channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'visitor_joined',
                    'community_id': str(community_id),
                    'count': count,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting visitor joined: {e}")

    def broadcast_visitor_left(
        self,
        community_id: str,
        count: int
    ) -> None:
        """
        Broadcast that a visitor has left.

        Args:
            community_id: UUID of the community
            count: New visitor count after leave
        """
        if not self.channel_layer:
            return

        room_group_name = f'visitors_{community_id}'

        try:
            async_to_sync(self.channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'visitor_left',
                    'community_id': str(community_id),
                    'count': count,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting visitor left: {e}")

    def broadcast_dashboard_update(
        self,
        community_id: str,
        dashboard_data: dict
    ) -> None:
        """
        Broadcast dashboard update to moderators/admins.

        Args:
            community_id: UUID of the community
            dashboard_data: Dashboard analytics data
        """
        if not self.channel_layer:
            return

        room_group_name = f'visitor_dashboard_{community_id}'

        try:
            async_to_sync(self.channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'dashboard_update',
                    'data': dashboard_data,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting dashboard update: {e}")

    def broadcast_analytics_metric(
        self,
        community_id: str,
        metric: str,
        value: any
    ) -> None:
        """
        Broadcast a specific analytics metric update.

        Args:
            community_id: UUID of the community
            metric: Metric name (e.g., 'conversion_rate')
            value: Metric value
        """
        if not self.channel_layer:
            return

        room_group_name = f'visitor_dashboard_{community_id}'

        try:
            async_to_sync(self.channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'analytics_update',
                    'metric': metric,
                    'value': value,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting analytics metric: {e}")


# Global broadcaster instance
visitor_broadcaster = VisitorBroadcaster()
