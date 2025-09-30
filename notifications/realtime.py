"""
Real-time WebSocket notification utilities for all Django apps.

This module provides utilities to send real-time notifications via WebSocket
across all Django apps in the equipment project.
"""

import json
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class RealTimeNotificationService:
    """
    Service for sending real-time notifications via WebSocket.

    This service integrates with all Django apps to provide instant
    notification delivery to users.
    """

    def __init__(self):
        self.channel_layer = get_channel_layer()

    def send_notification(self,
                         user_profile_id: str,
                         notification_data: Dict[str, Any],
                         notification_type: str = 'notification'):
        """
        Send a real-time notification to a specific user.

        Args:
            user_profile_id: UUID of the user profile
            notification_data: Notification data dictionary
            notification_type: Type of notification handler to use
        """
        if not self.channel_layer:
            logger.warning("Channel layer not configured - WebSocket unavailable")
            return False

        try:
            group_name = f"notifications_{user_profile_id}"

            async_to_sync(self.channel_layer.group_send)(
                group_name,
                {
                    "type": notification_type,
                    "data": notification_data
                }
            )

            logger.info(f"Sent real-time notification to user {user_profile_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send real-time notification: {e}")
            return False

    def send_admin_notification(self,
                               notification_data: Dict[str, Any],
                               notification_type: str = 'admin_alert'):
        """
        Send a notification to all admin users.

        Args:
            notification_data: Admin notification data
            notification_type: Type of admin notification
        """
        if not self.channel_layer:
            return False

        try:
            async_to_sync(self.channel_layer.group_send)(
                "admin_notifications",
                {
                    "type": notification_type,
                    "data": notification_data
                }
            )

            logger.info("Sent admin notification")
            return True

        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
            return False


# Global instance
realtime_service = RealTimeNotificationService()


# =============================================================================
# APP-SPECIFIC NOTIFICATION FUNCTIONS
# =============================================================================

# ACCOUNTS APP NOTIFICATIONS
def send_account_notification(user_profile, notification_type: str,
                            data: Dict[str, Any]):
    """Send account-related real-time notifications."""
    notification_data = {
        'title': data.get('title', ''),
        'message': data.get('message', ''),
        'app': 'accounts',
        'type': notification_type,
        'user_id': str(user_profile.id),
        'timestamp': get_current_timestamp(),
        **data
    }

    return realtime_service.send_notification(
        str(user_profile.id),
        notification_data,
        'notification_message'
    )


def send_follow_notification(follower_profile, followed_profile,
                           follow_status: str):
    """Send real-time notification for follow events."""
    data = {
        'title': f'New follower: @{follower_profile.user.username}',
        'message': f'@{follower_profile.user.username} is now following you.',
        'follower_id': str(follower_profile.id),
        'follower_username': follower_profile.user.username,
        'status': follow_status
    }

    return send_account_notification(
        followed_profile,
        'follow_notification',
        data
    )


def send_profile_verification_notification(user_profile, is_verified: bool):
    """Send profile verification status notification."""
    status = "verified" if is_verified else "verification_failed"
    title = "Profile Verified!" if is_verified else "Verification Failed"
    message = ("Your profile has been successfully verified." if is_verified
               else "Profile verification failed. Please try again.")

    data = {
        'title': title,
        'message': message,
        'verification_status': status
    }

    return send_account_notification(user_profile, 'verification', data)


# CONTENT APP NOTIFICATIONS
def send_content_notification(user_profile, notification_type: str,
                            data: Dict[str, Any]):
    """Send content-related real-time notifications."""
    notification_data = {
        'title': data.get('title', ''),
        'message': data.get('message', ''),
        'app': 'content',
        'type': notification_type,
        'timestamp': get_current_timestamp(),
        **data
    }

    return realtime_service.send_notification(
        str(user_profile.id),
        notification_data,
        'social_notification'
    )


def send_post_interaction_notification(post_author, actor_profile,
                                     interaction_type: str, post_id: str):
    """Send notification for post interactions (likes, comments, shares)."""
    interaction_messages = {
        'like': f'@{actor_profile.user.username} liked your post.',
        'comment': f'@{actor_profile.user.username} commented on your post.',
        'share': f'@{actor_profile.user.username} shared your post.',
        'repost': f'@{actor_profile.user.username} reposted your content.'
    }

    data = {
        'title': f'New {interaction_type}',
        'message': interaction_messages.get(interaction_type,
                   f'@{actor_profile.user.username} interacted with your post.'),
        'post_id': post_id,
        'actor_id': str(actor_profile.id),
        'actor_username': actor_profile.user.username,
        'interaction_type': interaction_type
    }

    return send_content_notification(
        post_author,
        f'post_{interaction_type}',
        data
    )


def send_content_moderation_notification(user_profile, action: str,
                                       content_id: str, reason: str = None):
    """Send content moderation notifications."""
    actions = {
        'approved': {
            'title': 'Content Approved',
            'message': 'Your content has been approved and is now visible.'
        },
        'removed': {
            'title': 'Content Removed',
            'message': f'Your content was removed. {reason or ""}'
        },
        'flagged': {
            'title': 'Content Under Review',
            'message': 'Your content is being reviewed by moderators.'
        }
    }

    action_data = actions.get(action, {
        'title': 'Content Update',
        'message': 'There has been an update to your content.'
    })

    data = {
        'title': action_data['title'],
        'message': action_data['message'],
        'content_id': content_id,
        'action': action,
        'reason': reason
    }

    return realtime_service.send_notification(
        str(user_profile.id),
        data,
        'moderation_notification'
    )


# COMMUNITIES APP NOTIFICATIONS
def send_community_notification(user_profile, notification_type: str,
                              data: Dict[str, Any]):
    """Send community-related real-time notifications."""
    notification_data = {
        'title': data.get('title', ''),
        'message': data.get('message', ''),
        'app': 'communities',
        'type': notification_type,
        'timestamp': get_current_timestamp(),
        **data
    }

    return realtime_service.send_notification(
        str(user_profile.id),
        notification_data,
        'community_notification'
    )


def send_community_membership_notification(user_profile, community_name: str,
                                         status: str):
    """Send community membership notifications."""
    status_messages = {
        'approved': f'You have been accepted to join {community_name}!',
        'rejected': f'Your request to join {community_name} was declined.',
        'invited': f'You have been invited to join {community_name}.',
        'removed': f'You have been removed from {community_name}.'
    }

    data = {
        'title': f'Community Update: {community_name}',
        'message': status_messages.get(status,
                   f'Community membership status changed: {status}'),
        'community_name': community_name,
        'status': status
    }

    return send_community_notification(user_profile, 'membership', data)


def send_message_notification(recipient_profile, sender_profile,
                            message_preview: str, chat_id: str = None):
    """Send real-time message notifications."""
    data = {
        'title': f'New message from @{sender_profile.user.username}',
        'message': message_preview,
        'app': 'messaging',
        'sender_id': str(sender_profile.id),
        'sender_username': sender_profile.user.username,
        'chat_id': chat_id,
        'timestamp': get_current_timestamp()
    }

    return realtime_service.send_notification(
        str(recipient_profile.id),
        data,
        'messaging_notification'
    )


# POLLS APP NOTIFICATIONS
def send_poll_notification(user_profile, notification_type: str,
                         data: Dict[str, Any]):
    """Send poll-related real-time notifications."""
    notification_data = {
        'title': data.get('title', ''),
        'message': data.get('message', ''),
        'app': 'polls',
        'type': notification_type,
        'timestamp': get_current_timestamp(),
        **data
    }

    return realtime_service.send_notification(
        str(user_profile.id),
        notification_data,
        'poll_notification'
    )


def send_poll_result_notification(poll_creator, poll_title: str,
                                total_votes: int):
    """Send poll results notification."""
    data = {
        'title': 'Poll Results Available',
        'message': f'Your poll "{poll_title}" has received {total_votes} votes.',
        'poll_title': poll_title,
        'total_votes': total_votes
    }

    return send_poll_notification(poll_creator, 'poll_results', data)


# AI CONVERSATIONS APP NOTIFICATIONS
def send_ai_conversation_notification(user_profile, notification_type: str,
                                    data: Dict[str, Any]):
    """Send AI conversation notifications."""
    notification_data = {
        'title': data.get('title', ''),
        'message': data.get('message', ''),
        'app': 'ai_conversations',
        'type': notification_type,
        'timestamp': get_current_timestamp(),
        **data
    }

    return realtime_service.send_notification(
        str(user_profile.id),
        notification_data,
        'ai_conversation_notification'
    )


def send_ai_response_notification(user_profile, conversation_title: str):
    """Send AI response ready notification."""
    data = {
        'title': 'AI Response Ready',
        'message': f'Your AI conversation "{conversation_title}" has a new response.',
        'conversation_title': conversation_title
    }

    return send_ai_conversation_notification(
        user_profile,
        'ai_response',
        data
    )


# ANALYTICS APP NOTIFICATIONS
def send_analytics_notification(user_profile, notification_type: str,
                              data: Dict[str, Any]):
    """Send analytics-related notifications."""
    notification_data = {
        'title': data.get('title', ''),
        'message': data.get('message', ''),
        'app': 'analytics',
        'type': notification_type,
        'timestamp': get_current_timestamp(),
        **data
    }

    return realtime_service.send_notification(
        str(user_profile.id),
        notification_data,
        'analytics_notification'
    )


def send_weekly_report_notification(user_profile, report_data: Dict[str, Any]):
    """Send weekly analytics report notification."""
    data = {
        'title': 'Weekly Report Available',
        'message': 'Your weekly activity report is ready to view.',
        'report_data': report_data
    }

    return send_analytics_notification(user_profile, 'weekly_report', data)


# UTILITY FUNCTIONS
def get_current_timestamp():
    """Get current timestamp in ISO format."""
    from django.utils import timezone
    return timezone.now().isoformat()


def send_system_notification(user_profile, title: str, message: str,
                           priority: str = 'medium'):
    """Send system-wide notifications."""
    data = {
        'title': title,
        'message': message,
        'app': 'system',
        'priority': priority,
        'timestamp': get_current_timestamp()
    }

    return realtime_service.send_notification(
        str(user_profile.id),
        data,
        'system_notification'
    )


def send_bulk_notification(user_profile_ids: List[str],
                         notification_data: Dict[str, Any],
                         notification_type: str = 'notification_message'):
    """Send bulk notifications to multiple users."""
    success_count = 0

    for user_profile_id in user_profile_ids:
        if realtime_service.send_notification(
            user_profile_id,
            notification_data,
            notification_type
        ):
            success_count += 1

    logger.info(f"Sent bulk notification to {success_count}/{len(user_profile_ids)} users")
    return success_count
