"""
Asynchronous email tasks to prevent blocking main application processes.

This module provides Celery tasks for sending emails asynchronously,
ensuring that database CRUD operations and other core functionality
remain fast and responsive.
"""

import email
from celery import shared_task
from notifications.utils import NotificationService
from analytics.models import ErrorLog
from accounts.models import UserProfile
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_email_notification_async(
    self, recipient_id, subject, template=None, context=None
):
    """
    Send email notification asynchronously.

    Args:
        recipient_id: UserProfile ID
        subject: Email subject
        template: Email template path (optional)
        context: Template context data (optional)

    Returns:
        Success message or error
    """
    try:
        # Get the recipient
        try:
            recipient = UserProfile.objects.get(
                id=recipient_id, is_deleted=False
            )
        except UserProfile.DoesNotExist:
            logger.error(f"UserProfile {recipient_id} not found")
            return f"UserProfile {recipient_id} not found"

        # Send the email
        success = NotificationService.send_email_notification(
            recipient=recipient,
            subject=subject,
            template=template,
            context=context or {}
        )

        if success:
            logger.info(f"Async email sent to {recipient.user.email}")
            return f"Email sent successfully to {recipient.user.email}"
        else:
            raise Exception("Email sending failed")

    except Exception as exc:
        logger.warning(
            f"Async email failed (attempt {self.request.retries + 1}): {exc}"
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(exc=exc, countdown=countdown)
        else:
            # Final failure - log it
            ErrorLog.objects.create(
                level='error',
                message=f'Async email finally failed: {str(exc)}',
                extra_data={
                    'recipient_id': recipient_id,
                    'subject': subject,
                    'template': template,
                    'task': 'send_email_notification_async'
                }
            )
            return f"Email failed after {self.max_retries} retries: {str(exc)}"


@shared_task(bind=True, max_retries=3)
def send_verification_email_async(
    self, user_profile_id, verification_code, email_type='verification',
    extra_context=None
):
    """
    Send verification email asynchronously.

    Args:
        user_profile_id: UserProfile ID
        verification_code: The verification code
        email_type: Type of verification
                   ('verification','reverification', 'phone_change', 'email_change')
        extra_context: Additional context (e.g., new_phone, expires_at)
    """
    try:
        profile = UserProfile.objects.get(id=user_profile_id, is_deleted=False)

        # Template mapping - USE EXISTING TEMPLATES ONLY
        templates = {
            'verification': 'accounts/email/verification_email.html',
            'reverification': 'accounts/email/reverification_email.html',
            'phone_change': 'accounts/email/phone_change_verification.html',
            'email_change': 'accounts/email/new_email_verification.html'
        }

        subjects = {
            'verification': 'Your Account Verification Code - Action Required',
            'reverification': 'Re-Verification Required - New Code Inside',
            'phone_change': 'Phone Change Verification Code',
            'email_change': 'Email Change Verification Code'
        }

        template = templates.get(email_type, templates['verification'])
        subject = subjects.get(email_type, subjects['verification'])

        # Base context
        context = {
            'code': verification_code,
            'user': profile.user,
            'email_type': email_type
        }

        # Add extra context if provided
        if extra_context:
            context.update(extra_context)

        success = NotificationService.send_email_notification(
            recipient=profile,
            subject=subject,
            template=template,
            context=context
        )

        if success and email_type in ['phone_change', 'email_change']:
            # Send in-app notification that email was sent
            NotificationService.create_notification(
                recipient=profile,
                title="Verification Email Sent",
                message=f"Check email for {email_type} verification code",
                notification_type='email_sent',
                app_context='accounts',
                extra_data={'email_type': email_type}
            )
            return f"Verification email sent to {profile.user.email}"
        else:
            raise Exception("Email sending failed")

    except Exception as exc:
        logger.warning(
            f"Verification email failed "
            f"(attempt {self.request.retries + 1}): {exc}"
        )
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_follow_request_email_async(self, follow_id):
    """Send follow request email asynchronously."""
    try:
        from accounts.models import Follow

        follow = Follow.objects.select_related(
            'follower__user', 'followed__user'
        ).get(id=follow_id)

        # Only send email for pending requests to private profiles
        if follow.status != 'pending' or not follow.followed.is_private:
            return f"Email not needed for follow {follow_id}"

        if not follow.followed.user.email:
            return f"No email address for user {follow.followed.user.username}"

        # Prepare context
        from django.conf import settings
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:3000')

        context = {
            'follower_username': follow.follower.user.username,
            'follower_display_name': follow.follower.display_name,
            'followed_username': follow.followed.user.username,
            'followed_display_name': follow.followed.display_name,
            'accept_url': f"{base_url}/api/auth/follow-requests/{follow_id}/accept/",
            'decline_url': f"{base_url}/api/auth/follow-requests/{follow_id}/decline/",
            'profile_url': f"{base_url}/profile/{follow.follower.user.username}/",
            'follow': follow,
            'follower': follow.follower,
            'LOGO_URL': getattr(settings, 'LOGO_URL', ''),
        }

        success = NotificationService.send_email_notification(
            recipient=follow.followed,
            subject=f'New follow request from @{follow.follower.user.username}',
            template='accounts/email/follow_request_email.html',
            context=context
        )

        if success:
            return f"Follow request email sent to {follow.followed.user.email}"
        else:
            raise Exception("Email sending failed")

    except Exception as exc:
        logger.warning(
            f"Follow request email failed (attempt {self.request.retries + 1}): {exc}"
        )
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True)
def send_email_change_confirmation_async(self, profile_id, old_email, new_email):
    """
    Send email change confirmation notification asynchronously.
    This is the ONLY unique email type not covered by send_verification_email_async.
    """
    try:
        profile = UserProfile.objects.get(id=profile_id)

        # Use existing template for email change confirmation
        template_name = 'accounts/email/email_change_confirmation.html'
        subject = f"Email Address Changed - {settings.SITE_NAME}"
        context = {
            'user': profile.user,
            'old_email': old_email,
            'new_email': new_email,
            'changed_at': timezone.now()
        }

        # Send email via NotificationService
        notification_service = NotificationService()
        success = notification_service.send_email_notification(
            recipient=profile,
            subject=subject,
            template=template_name,
            context=context
        )

        if success:
            logger.info(
                f"Email change confirmation sent to {profile.user.email}"
            )
            return True
        else:
            logger.error(
                f"Failed to send email change confirmation to {profile.user.email}"
            )
            return False

    except UserProfile.DoesNotExist:
        logger.error(f"UserProfile with id {profile_id} does not exist")
        return False
    except Exception as e:
        logger.error(f"Error sending email change confirmation: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(
            countdown=60 * (2 ** self.request.retries),
            max_retries=3,
            exc=e
        )
# Convenience function for immediate response
def queue_email_with_feedback(recipient, subject, template=None, context=None,
                            notification_title="Email Sent",
                            notification_message="Check your email"):
    """
    Queue an async email and immediately send in-app notification.

    This provides immediate user feedback while processing email asynchronously.
    """
    try:
        # Queue the async email
        task = send_email_notification_async.delay(
            str(recipient.id), subject, template, context
        )

        # Immediate in-app notification
        NotificationService.create_notification(
            recipient=recipient,
            title=notification_title,
            message=notification_message,
            notification_type='email_queued',
            app_context='system',
            extra_data={
                'task_id': task.id,
                'email_subject': subject
            }
        )

        return True
    except Exception as e:
        logger.error(f"Failed to queue email with feedback: {e}")
        return False
