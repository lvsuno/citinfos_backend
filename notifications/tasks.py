from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.db.models import Count, Q
from datetime import timedelta
from notifications.models import Notification
from analytics.models import ErrorLog
import logging


@shared_task
def send_notification_emails():
    """Send email notifications for high-priority unread notifications"""
    try:
        from notifications.utils import NotificationService

        # Get high-priority notifications from the last 4 hours that need email alerts
        recent_notifications = Notification.objects.filter(created_at__gte=timezone.now() - timedelta(hours=4), is_deleted=False,
            is_read=False,
            notification_type__in=['system', 'message']  # Only important types get emails
        ).select_related('recipient__user')

        # Group by user to send batch emails
        user_notifications = {}
        for notification in recent_notifications:
            user_profile = notification.recipient
            if user_profile.user.email:
                if user_profile not in user_notifications:
                    user_notifications[user_profile] = []
                user_notifications[user_profile].append(notification)

        # Send emails
        sent_count = 0
        for user_profile, notifications in user_notifications.items():
            if len(notifications) > 0:
                try:
                    subject = f"You have {len(notifications)} important notifications"

                    # Use NotificationService to send email with global template
                    email_sent = NotificationService.send_email_notification(
                        recipient=user_profile,
                        subject=subject,
                        template='global/email/system/general_notification.html',
                        context={
                            'notification_title': 'Important Notifications',
                            'notification_icon': '🔔',
                            'notification_message': f"You have {len(notifications)} important notifications waiting for your attention.",
                            'details': {
                                'Notification Count': len(notifications),
                                'Time Period': 'Last 4 hours',
                                'Priority': 'High'
                            },
                            'notifications': notifications,
                            'user': user_profile.user,
                            'notification_count': len(notifications)
                        }
                    )

                    if email_sent:
                        sent_count += 1

                except Exception as e:
                    ErrorLog.objects.create(
                        level='warning',
                        message=f'Error sending email to {user_profile.user.email}: {str(e)}',
                        extra_data={
                            'email': user_profile.user.email,
                            'task': 'send_notification_emails'
                        }
                    )

        return f"Sent notification emails to {sent_count} users"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error sending notification emails: {str(e)}',
            extra_data={'task': 'send_notification_emails'}
        )
        return f"Error sending notification emails: {str(e)}"


@shared_task
def cleanup_old_notifications():
    """Clean up old read notifications to maintain performance"""
    try:
        # Delete read notifications older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        old_read_notifications = Notification.objects.filter(is_read=True,
            read_at__lt=cutoff_date, is_deleted=False)
        deleted_count = old_read_notifications.count()
        old_read_notifications.delete()

        # Delete unread notifications older than 90 days (user didn't see them)
        very_old_cutoff = timezone.now() - timedelta(days=90)
        very_old_notifications = Notification.objects.filter(is_read=False,
            created_at__lt=very_old_cutoff, is_deleted=False)
        very_old_count = very_old_notifications.count()
        very_old_notifications.delete()

        return f"Deleted {deleted_count} old read notifications and {very_old_count} very old unread notifications"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error cleaning up notifications: {str(e)}',
            extra_data={'task': 'cleanup_old_notifications'}
        )
        return f"Error cleaning up notifications: {str(e)}"


@shared_task
def generate_notification_digest():
    """Generate daily notification digest for users with multiple unread notifications"""
    try:
        from notifications.utils import NotificationService
        from accounts.models import UserProfile

        # Get users with 5+ unread notifications
        users_with_many_unread = UserProfile.objects.filter(notifications__is_read=False, is_deleted=False).annotate(
            unread_count=Count('notifications', filter=Q(notifications__is_read=False))
        ).filter(unread_count__gte=5)

        digest_created = 0
        for user in users_with_many_unread:
            # Check if we haven't sent a digest recently (last 24 hours)
            recent_digest = Notification.objects.filter(recipient=user,
                notification_type='digest',
                title__contains='Daily Digest',
                created_at__gte=timezone.now() - timedelta(hours=24), is_deleted=False
            ).exists()

            if not recent_digest:
                unread_count = user.notifications.filter(is_read=False).count()
                NotificationService.create_notification(
                    recipient=user,
                    title='Daily Digest',
                    message=f'You have {unread_count} unread notifications. Check them out!',
                    notification_type='digest',
                    app_context='system'
                )
                digest_created += 1

        return f"Created {digest_created} notification digests"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error generating notification digest: {str(e)}',
            extra_data={'task': 'generate_notification_digest'}
        )
        return f"Error generating notification digest: {str(e)}"


@shared_task
def update_notification_metrics():
    """Update notification system metrics for monitoring"""
    try:
        # Calculate metrics for the last 24 hours
        last_24h = timezone.now() - timedelta(hours=24)

        metrics = {
            'total_sent': Notification.objects.filter(created_at__gte=last_24h, is_deleted=False).count(),
            'total_read': Notification.objects.filter(read_at__gte=last_24h, is_deleted=False).count(),
            'by_type': {},
            'read_rate': 0
        }

        # Count by notification type
        type_counts = Notification.objects.filter(created_at__gte=last_24h, is_deleted=False).values('notification_type').annotate(
            count=Count('id')
        )

        for item in type_counts:
            metrics['by_type'][item['notification_type']] = item['count']

        # Calculate read rate
        if metrics['total_sent'] > 0:
            metrics['read_rate'] = (metrics['total_read'] / metrics['total_sent']) * 100

        # Log metrics
        ErrorLog.objects.create(
            level='info',
            message='Daily notification metrics generated',
            extra_data={
                'task': 'update_notification_metrics',
                'metrics': metrics
            }
        )

        return f"Updated notification metrics: {metrics['total_sent']} sent, {metrics['read_rate']:.1f}% read rate"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating notification metrics: {str(e)}',
            extra_data={'task': 'update_notification_metrics'}
        )
        return f"Error updating notification metrics: {str(e)}"


@shared_task
def dispatch_new_badge_notifications():
    """Create notifications for newly earned badges lacking a notification.

    Prerequisite: add a boolean field or separate tracking to UserBadge.
    For now we detect un-notified by checking absence of a Notification with
    content_type/object_id referencing the UserBadge and type in ('badge','achievement').
    This is O(n) with small queries; optimize with explicit flag later.
    """
    try:
        from django.contrib.contenttypes.models import ContentType
        from accounts.models import UserBadge
        from notifications.utils import BadgeNotifications

        badge_ct = ContentType.objects.get_for_model(UserBadge)
        # UserBadges without a notification
        user_badges = UserBadge.objects.select_related('profile', 'badge').all()
        created = 0
        for ub in user_badges:
            exists = Notification.objects.filter(content_type=badge_ct,
                object_id=ub.id,
                notification_type__in=['badge', 'achievement'], is_deleted=False).exists()
            if exists:
                continue
            if not ub.badge or not ub.profile:
                continue
            BadgeNotifications.badge_awarded(ub)
            created += 1
        return f"Created {created} badge notifications"
    except Exception as e:  # noqa: BLE001
        ErrorLog.objects.create(
            level='error',
            message=f'Error dispatching badge notifications: {e}',
            extra_data={'task': 'dispatch_new_badge_notifications'}
        )
        return f"Error dispatching badge notifications: {e}"


@shared_task
def send_system_notification_email(user_profile_id, notification_data):
    """Send system notification email using global template.

    Args:
        user_profile_id: ID of UserProfile to send to
        notification_data: Dictionary containing notification details
    """
    try:
        from accounts.models import UserProfile
        from notifications.utils import NotificationService

        user_profile = UserProfile.objects.get(id=user_profile_id)

        # Use global template for system notifications
        email_sent = NotificationService.send_email_notification(
            recipient=user_profile,
            subject=notification_data.get('subject', 'System Notification'),
            template='global/email/system/general_notification.html',
            context={
                'notification_title': notification_data.get('title', 'System Notification'),
                'notification_icon': notification_data.get('icon', '🔔'),
                'notification_message': notification_data.get('message', ''),
                'alert_message': notification_data.get('alert_message'),
                'alert_type': notification_data.get('alert_type', 'info'),
                'details': notification_data.get('details', {}),
                'action_items': notification_data.get('action_items', []),
                'primary_action_url': notification_data.get('action_url'),
                'primary_action_text': notification_data.get('action_text'),
                'show_timestamp': notification_data.get('show_timestamp', True),
                'additional_notes': notification_data.get('notes'),
                'user': user_profile.user
            }
        )

        if email_sent:
            return f"System notification email sent to {user_profile.user.email}"
        else:
            return f"Failed to send system notification email to {user_profile.user.email}"

    except UserProfile.DoesNotExist:
        return f"UserProfile {user_profile_id} not found"
    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error sending system notification email: {str(e)}',
            extra_data={'user_profile_id': user_profile_id, 'notification_data': notification_data}
        )
        return f"Error sending system notification: {str(e)}"


def send_follow_request_email(follow_id):
    """Send email notification for follow request."""
    try:
        from accounts.models import Follow
        from django.urls import reverse
        from django.conf import settings

        # Get the follow request
        follow = Follow.objects.select_related(
            'follower__user', 'followed__user'
        ).get(id=follow_id)

        # Only send email for pending requests to private profiles
        if follow.status != 'pending' or not follow.followed.is_private:
            return f"Email not needed for follow {follow_id}"

        recipient_user = follow.followed.user
        if not recipient_user.email:
            return f"No email address for user {recipient_user.username}"

        # Build URLs (these will fail in development but work in production)
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:3000')
        accept_url = f"{base_url}/api/auth/follow-requests/{follow_id}/accept/"
        decline_url = f"{base_url}/api/auth/follow-requests/{follow_id}/decline/"
        profile_url = f"{base_url}/profile/{follow.follower.user.username}/"

        # Prepare email context
        context = {
            'recipient': follow.followed,
            'follower': follow.follower,
            'follow': follow,
            'accept_url': accept_url,
            'decline_url': decline_url,
            'profile_url': profile_url,
            'LOGO_URL': getattr(settings, 'LOGO_URL', ''),
        }

        # Send email using NotificationService
        from notifications.utils import NotificationService

        email_sent = NotificationService.send_email_notification(
            recipient=follow.followed,
            subject=f'New follow request from @{follow.follower.user.username}',
            template='accounts/email/follow_request_email.html',
            context=context
        )

        if email_sent:
            return f"Follow request email sent to {recipient_user.email}"
        else:
            return f"Failed to send follow request email to {recipient_user.email}"

    except Follow.DoesNotExist:
        return f"Follow request {follow_id} not found"
    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error sending follow request email: {e}',
            extra_data={'task': 'send_follow_request_email', 'follow_id': follow_id}
        )
        return f"Error sending follow request email: {e}"


# Ensure asynchronous email task module is imported so Celery registers
# tasks defined in `notifications/async_email_tasks.py` during autodiscovery.
try:
    from . import async_email_tasks  # noqa: F401
except Exception:
    logger = logging.getLogger(__name__)
    logger.exception('Failed to import notifications.async_email_tasks')
