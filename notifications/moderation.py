"""
Moderation notification utilities for content app.
"""

from notifications.utils import NotificationService
from notifications.models import Notification
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class ModerationNotifications:
    """Content moderation specific notification helpers."""

    @staticmethod
    def send_moderation_notification(user, decision_type, details):
        """
        Send moderation notification to user.

        Args:
            user: UserProfile receiving the notification
            decision_type: Type of moderation decision
            details: Dictionary containing notification details
        """
        notification_templates = {
            'content_approved': {
                'title': 'Content Approved',
                'message': 'Your content has been reviewed and approved.',
                'notification_type': 'system',
                'priority': 3
            },
            'content_removed': {
                'title': 'Content Removed',
                'message': 'Your content violated community guidelines.',
                'notification_type': 'system',
                'priority': 2,
                'extra_data': {'appeal_available': True}
            },
            'account_restricted': {
                'title': 'Account Restricted',
                'message': 'Temporary restrictions applied to your account.',
                'notification_type': 'security_alert',
                'priority': 1
            },
            'bot_detection': {
                'title': 'Automated Activity Detected',
                'message': 'Your account has been flagged for review.',
                'notification_type': 'security_alert',
                'priority': 1,
                'extra_data': {'verification_required': True}
            },
            'warning_issued': {
                'title': 'Warning Issued',
                'message': 'You have received a warning for policy violation.',
                'notification_type': 'system',
                'priority': 2
            },
            'suspension_lifted': {
                'title': 'Account Suspension Lifted',
                'message': 'Your account restrictions have been removed.',
                'notification_type': 'system',
                'priority': 2
            }
        }

        template = notification_templates.get(decision_type)
        if not template:
            logger.error(f"Unknown moderation decision type: {decision_type}")
            return None

        # Merge template with provided details
        title = details.get('title', template['title'])
        message = details.get('message', template['message'])
        extra_data = {
            **template.get('extra_data', {}),
            **details.get('extra_data', {}),
            'moderation_action': decision_type,
            'timestamp': timezone.now().isoformat()
        }

        # Add moderation-specific context
        if 'content_id' in details:
            extra_data['content_id'] = str(details['content_id'])
        if 'moderator' in details:
            extra_data['moderator'] = details['moderator']
        if 'appeal_deadline' in details:
            extra_data['appeal_deadline'] = details['appeal_deadline']

        return NotificationService.create_notification(
            recipient=user,
            title=title,
            message=message,
            notification_type=template['notification_type'],
            app_context='content',
            extra_data=extra_data
        )

    @staticmethod
    def update_moderation_metrics(action_type, decision, confidence):
        """
        Update moderation analytics and metrics.

        Args:
            action_type: Type of moderation action
            decision: Final decision made
            confidence: Confidence score of the action
        """
        try:
            from analytics.models import AnalyticsEvent

            # Log moderation analytics event
            AnalyticsEvent.objects.create(
                event_type='moderation_action',
                event_data={
                    'action_type': action_type,
                    'decision': decision,
                    'confidence': confidence,
                    'timestamp': timezone.now().isoformat()
                },
                user_agent='system',
                ip_address='127.0.0.1'
            )

        except ImportError:
            logger.warning("Analytics app not available for moderation metrics")
        except Exception as e:
            logger.error(f"Error updating moderation metrics: {str(e)}")

    @staticmethod
    def notify_content_approved(user, content, moderator=None):
        """Send content approved notification."""
        details = {
            'content_id': getattr(content, 'id', None),
            'moderator': getattr(moderator, 'user.username', None),
            'extra_data': {
                'content_type': content.__class__.__name__.lower(),
                'appeal_available': False
            }
        }

        return ModerationNotifications.send_moderation_notification(
            user, 'content_approved', details
        )

    @staticmethod
    def notify_content_removed(user, content, reason, moderator=None,
                             appeal_deadline=None):
        """Send content removed notification."""
        message = f"Your content was removed: {reason}"

        details = {
            'message': message,
            'content_id': getattr(content, 'id', None),
            'moderator': getattr(moderator, 'user.username', None),
            'appeal_deadline': appeal_deadline,
            'extra_data': {
                'content_type': content.__class__.__name__.lower(),
                'removal_reason': reason,
                'appeal_available': True
            }
        }

        return ModerationNotifications.send_moderation_notification(
            user, 'content_removed', details
        )

    @staticmethod
    def notify_account_restricted(user, restriction_type, duration=None,
                                reason=None):
        """Send account restriction notification."""
        if duration:
            message = f"Your account has been restricted for {duration}."
        else:
            message = "Your account has been restricted."

        if reason:
            message += f" Reason: {reason}"

        details = {
            'message': message,
            'extra_data': {
                'restriction_type': restriction_type,
                'duration': duration,
                'reason': reason,
                'appeal_available': True
            }
        }

        return ModerationNotifications.send_moderation_notification(
            user, 'account_restricted', details
        )

    @staticmethod
    def notify_bot_detection(user, detection_reason, confidence_score):
        """Send bot detection notification."""
        message = f"Automated activity detected: {detection_reason}"

        details = {
            'message': message,
            'extra_data': {
                'detection_reason': detection_reason,
                'confidence_score': confidence_score,
                'verification_required': True,
                'appeal_available': True
            }
        }

        return ModerationNotifications.send_moderation_notification(
            user, 'bot_detection', details
        )

    @staticmethod
    def notify_warning_issued(user, warning_reason, strike_count=None):
        """Send warning notification."""
        message = f"Warning: {warning_reason}"

        if strike_count:
            message += f" (Strike {strike_count})"

        details = {
            'message': message,
            'extra_data': {
                'warning_reason': warning_reason,
                'strike_count': strike_count,
                'appeal_available': True
            }
        }

        return ModerationNotifications.send_moderation_notification(
            user, 'warning_issued', details
        )

    @staticmethod
    def notify_suspension_lifted(user, moderator=None):
        """Send suspension lifted notification."""
        details = {
            'moderator': getattr(moderator, 'user.username', None),
            'extra_data': {
                'account_restored': True,
                'appeal_available': False
            }
        }

        return ModerationNotifications.send_moderation_notification(
            user, 'suspension_lifted', details
        )


# Helper functions for easy import in content app
def send_moderation_notification(user, decision_type, details):
    """Wrapper function for easy import."""
    return ModerationNotifications.send_moderation_notification(
        user, decision_type, details
    )


def update_moderation_metrics(action_type, decision, confidence):
    """Wrapper function for easy import."""
    return ModerationNotifications.update_moderation_metrics(
        action_type, decision, confidence
    )


# Export for use in content app
__all__ = [
    'ModerationNotifications',
    'send_moderation_notification',
    'update_moderation_metrics'
]
