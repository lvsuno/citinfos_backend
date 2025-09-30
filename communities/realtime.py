"""
Real-time helpers for communities app.

Provides convenience functions to broadcast presence and task updates
to community WebSocket groups.
"""

import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


def broadcast_presence(community_id: str, user_id: str, username: str, status: str = 'online') -> bool:
    """Broadcast a presence update to a community group."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning('Channel layer not available; presence broadcast skipped')
        return False

    group_name = f'community_{community_id}'
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'presence_update',
                'data': {
                    'user_id': user_id,
                    'username': username,
                    'status': status,
                },
            },
        )
        return True
    except Exception:
        logger.exception('Failed to broadcast presence')
        return False


def broadcast_task_update(community_id: str, task_data: dict, actor: dict = None) -> bool:
    """Broadcast a community task update to a community group."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning('Channel layer not available; task broadcast skipped')
        return False

    group_name = f'community_{community_id}'
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'community_task',
                'data': task_data,
                'actor': actor or {},
            },
        )
        return True
    except Exception:
        logger.exception('Failed to broadcast task update')
        return False
