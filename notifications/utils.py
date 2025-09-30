"""
Notification utilities for creating and managing notifications across all apps.
This module provides a centralized way to create notifications instead of using Django's email system.
"""

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from notifications.models import Notification
from accounts.models import UserProfile
from analytics.models import ErrorLog
from typing import Optional, List, Dict, Any, Union
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Centralized service for creating and managing notifications across all apps.
    """

    # Notification type mappings for different apps
    NOTIFICATION_TYPES = {
        'content': {
            'like': 'like',
            'comment': 'comment',
            'mention': 'mention',
            'share': 'share',
            'follow': 'follow',
        },
        'messaging': {
            'new_message': 'new_message',
            'message_reply': 'message',
            'group_message': 'message',
            'mention': 'mention',
            'call_missed': 'system',
        },
        'polls': {
            'poll_vote': 'system',
            'poll_comment': 'comment',
            'poll_closed': 'system',
            'poll_mention': 'mention',
        },
        'communities': {
            'community_invite': 'community_invite',
            'community_join': 'community_join',
            'community_post': 'community_post',
            'community_role_change': 'community_role_change',
            'geo_restriction': 'geo_restriction',
        },
        'system': {
            'account_update': 'system',
            'security_alert': 'security_alert',
            'maintenance': 'maintenance',
            'welcome': 'welcome',
            'digest': 'digest',
            'verification': 'verification',
            'badge': 'badge',            # added for badge awards
            'achievement': 'achievement'  # optional alias
        }
    }

    @staticmethod
    def create_notification(
        recipient: Union[UserProfile, str],
        title: str,
        message: str,
        notification_type: str,
        sender: Optional[UserProfile] = None,
        related_object: Optional[Any] = None,
        app_context: str = 'system',
        extra_data: Optional[Dict] = None,
        priority: int = 3
    ) -> Optional[Notification]:
        """
        Create a new notification.

        Args:
            recipient: UserProfile object or username string
            title: Notification title
            message: Notification message
            notification_type: Type of notification (like, comment, message)
            sender: UserProfile who triggered the notification
            related_object: Object that triggered the notification
            app_context: App context (content, messaging, etc.)
            extra_data: Additional data to store
            priority: Priority level (1=High, 2=Elevated, 3=Normal, etc.)

        Returns:
            Notification object or None if failed
        """
        try:
            # Handle recipient as string (username)
            if isinstance(recipient, str):
                try:
                    recipient = UserProfile.objects.get(user__username=recipient, is_deleted=False)
                except UserProfile.DoesNotExist:
                    logger.error(f"User not found: {recipient}")
                    return None

            # Don't send notifications to self
            if sender and recipient == sender:
                return None

            # Map notification type based on app context
            mapped_type = NotificationService._map_notification_type(
                notification_type, app_context
            )

            # Prepare content object data
            content_type = None
            object_id = None
            if related_object:
                content_type = ContentType.objects.get_for_model(related_object)
                object_id = getattr(related_object, 'id', None)

            # Create notification
            notification = Notification.objects.create(
                recipient=recipient,
                sender=sender,
                notification_type=mapped_type,
                title=title,
                message=message,
                priority=priority,
                content_type=content_type,
                object_id=object_id,
                extra_data=extra_data or {}
            )

            # Send real-time WebSocket notification
            NotificationService._send_realtime_notification(
                notification, app_context
            )

            logger.info(f"Notification created: {notification.id} for {recipient.user.username}")
            return notification

        except Exception as e:
            ErrorLog.objects.create(
                level='error',
                message=f'Error creating notification: {str(e)}',
                extra_data={
                    'recipient': getattr(recipient, 'user.username', str(recipient)),
                    'title': title,
                    'notification_type': notification_type,
                    'app_context': app_context
                }
            )
            logger.error(f"Failed to create notification: {str(e)}")
            return None

    @staticmethod
    def _map_notification_type(notification_type: str, app_context: str) -> str:
        """Map notification type based on app context."""
        app_types = NotificationService.NOTIFICATION_TYPES.get(app_context, {})
        return app_types.get(notification_type, 'system')

    @staticmethod
    def _send_realtime_notification(notification: Notification,
                                   app_context: str = 'system'):
        """
        Send real-time WebSocket notification.

        Args:
            notification: The notification object to send
            app_context: App context for routing to correct handler
        """
        try:
            # Import here to avoid circular imports
            from notifications.realtime import realtime_service

            # Prepare notification data for WebSocket
            notification_data = {
                'id': str(notification.id),
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'app': app_context,
                'priority': notification.priority,
                'sender': {
                    'id': str(notification.sender.id) if notification.sender else None,
                    'username': notification.sender.user.username if notification.sender else None,
                    'display_name': notification.sender.display_name if notification.sender else None
                } if notification.sender else None,
                'created_at': notification.created_at.isoformat(),
                'extra_data': notification.extra_data
            }

            # Map to appropriate WebSocket handler based on app context
            handler_map = {
                'content': 'social_notification',
                'accounts': 'social_notification',
                'communities': 'community_notification',
                'messaging': 'messaging_notification',
                'polls': 'poll_notification',
                'ai_conversations': 'ai_conversation_notification',
                'analytics': 'analytics_notification',
                'system': 'system_notification',
                'moderation': 'moderation_notification'
            }

            handler_type = handler_map.get(app_context, 'notification_message')

            # Send via WebSocket
            realtime_service.send_notification(
                str(notification.recipient.id),
                notification_data,
                handler_type
            )

        except ImportError:
            # WebSocket service not available, skip silently
            pass
        except Exception as e:
            logger.error(f"Failed to send real-time notification: {str(e)}")

    @staticmethod
    def create_bulk_notifications(
        recipients: List[Union[UserProfile, str]],
        title: str,
        message: str,
        notification_type: str,
        sender: Optional[UserProfile] = None,
        related_object: Optional[Any] = None,
        app_context: str = 'system'
    ) -> List[Notification]:
        """
        Create notifications for multiple recipients.

        Returns:
            List of created Notification objects
        """
        notifications = []
        for recipient in recipients:
            notification = NotificationService.create_notification(
                recipient=recipient,
                title=title,
                message=message,
                notification_type=notification_type,
                sender=sender,
                related_object=related_object,
                app_context=app_context
            )
            if notification:
                notifications.append(notification)
        return notifications

    @staticmethod
    def mark_as_read(notification_ids: List[str], user: UserProfile) -> int:
        """
        Mark notifications as read for a specific user.

        Returns:
            Number of notifications marked as read
        """
        try:
            updated = Notification.objects.filter(id__in=notification_ids,
                recipient=user,
                is_read=False, is_deleted=False).update(
                is_read=True,
                read_at=timezone.now()
            )
            return updated
        except Exception as e:
            logger.error(f"Error marking notifications as read: {str(e)}")
            return 0

    @staticmethod
    def get_unread_count(user: UserProfile) -> int:
        """Get count of unread notifications for a user."""
        try:
            return Notification.objects.filter(recipient=user,
                is_read=False, is_deleted=False).count()
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0

    @staticmethod
    def get_recent_notifications(
        user: UserProfile,
        limit: int = 20,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get recent notifications for a user."""
        try:
            queryset = Notification.objects.filter(recipient=user, is_deleted=False)
            if unread_only:
                queryset = queryset.filter(is_read=False)

            return list(queryset.order_by('-created_at')[:limit])
        except Exception as e:
            logger.error(f"Error getting recent notifications: {str(e)}")
            return []

    @staticmethod
    def delete_old_notifications(days: int = 30) -> int:
        """Delete notifications older than specified days."""
        try:
            cutoff_date = timezone.now() - timezone.timedelta(days=days)
            deleted_count = Notification.objects.filter(created_at__lt=cutoff_date, is_deleted=False).count()

            Notification.objects.filter(created_at__lt=cutoff_date, is_deleted=False).delete()

            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting old notifications: {str(e)}")
            return 0

    @staticmethod
    def send_sms_notification(
        recipient: UserProfile,
        message: str,
        phone_number: Optional[str] = None
    ) -> bool:
        """
        Send SMS notification to a user.

        Args:
            recipient: UserProfile to send SMS to
            message: SMS message content (max 160 characters recommended)
            phone_number: Override phone number (uses recipient.phone_number if not provided)

        Returns:
            True if SMS sent successfully, False otherwise
        """
        try:
            # Determine phone number to use
            target_phone = phone_number or getattr(recipient, 'phone_number', None)

            if not target_phone:
                logger.error(f"No phone number available for user: {recipient.user.username}")
                return False

            # Clean and validate phone number format
            import re
            cleaned_phone = re.sub(r'[^\d+]', '', str(target_phone))

            if not cleaned_phone or len(cleaned_phone) < 10:
                logger.error(f"Invalid phone number format: {target_phone}")
                return False

            # Import SMS service based on configuration
            from django.conf import settings

            # Check which SMS service to use (Twilio, AWS SNS, etc.)
            sms_service = getattr(settings, 'SMS_SERVICE', 'twilio')

            if sms_service.lower() == 'twilio':
                return NotificationService._send_twilio_sms(cleaned_phone, message)
            elif sms_service.lower() == 'aws_sns':
                return NotificationService._send_aws_sns_sms(cleaned_phone, message)
            else:
                # Mock/development mode
                return NotificationService._send_mock_sms(cleaned_phone, message)

        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return False

    @staticmethod
    def _send_twilio_sms(phone_number: str, message: str) -> bool:
        """Send SMS using Twilio service."""
        try:
            from django.conf import settings

            # Check if Twilio credentials are configured
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            from_phone = getattr(settings, 'TWILIO_PHONE_NUMBER', None)

            if not all([account_sid, auth_token, from_phone]):
                logger.error("Twilio credentials not properly configured")
                return False

            # Import Twilio client
            try:
                from twilio.rest import Client
            except ImportError:
                logger.error("Twilio package not installed. Run: pip install twilio")
                return False

            # Create Twilio client and send SMS
            client = Client(account_sid, auth_token)

            message_instance = client.messages.create(
                body=message,
                from_=from_phone,
                to=phone_number
            )

            logger.info(f"SMS sent via Twilio. SID: {message_instance.sid}")
            return True

        except Exception as e:
            logger.error(f"Twilio SMS error: {str(e)}")
            return False

    @staticmethod
    def _send_aws_sns_sms(phone_number: str, message: str) -> bool:
        """Send SMS using AWS SNS service."""
        try:
            from django.conf import settings
            import boto3

            # Get AWS credentials
            aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            aws_region = getattr(settings, 'AWS_REGION', 'us-east-1')

            if aws_access_key and aws_secret_key:
                sns = boto3.client(
                    'sns',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=aws_region
                )
            else:
                # Use default AWS credentials (IAM role, environment, etc.)
                sns = boto3.client('sns', region_name=aws_region)

            # Send SMS
            response = sns.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )

            message_id = response.get('MessageId')
            logger.info(f"SMS sent via AWS SNS. MessageId: {message_id}")
            return True

        except Exception as e:
            logger.error(f"AWS SNS SMS error: {str(e)}")
            return False

    @staticmethod
    def _send_mock_sms(phone_number: str, message: str) -> bool:
        """Mock SMS sending for development/testing."""
        logger.info(f"MOCK SMS to {phone_number}: {message}")

        # In development, optionally write to a file or database
        from django.conf import settings
        if settings.DEBUG:
            try:
                import os
                mock_sms_file = os.path.join(settings.BASE_DIR, 'mock_sms.log')
                with open(mock_sms_file, 'a', encoding='utf-8') as f:
                    from django.utils import timezone
                    timestamp = timezone.now().isoformat()
                    f.write(f"[{timestamp}] TO: {phone_number} | MESSAGE: {message}\n")
            except Exception:
                pass  # Fail silently for mock SMS logging

        return True

    @staticmethod
    def send_email_notification(
        recipient: UserProfile,
        subject: str,
        template: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send email notification to a user.

        Args:
            recipient: UserProfile to send email to
            subject: Email subject
            template: Path to HTML email template
                     (e.g., 'accounts/email/verification_email.html')
            context: Template context data (dictionary containing
                    variables for the template)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.template.loader import render_to_string, get_template
            from django.template import TemplateDoesNotExist
            from django.conf import settings
            from django.utils.html import strip_tags
            import re

            # Initialize content variables
            html_content = None
            text_content = None

            # Prepare the email content
            if template and context:
                try:
                    # Debug logging for template rendering
                    logger.info(f"Attempting to render template: {template}")
                    logger.info(f"Template context keys: {list(context.keys()) if context else 'None'}")

                    # Verify template exists and render HTML content
                    get_template(template)  # Raises TemplateDoesNotExist
                    logger.info(f"Template {template} found successfully")

                    # Add context processor variables to the context
                    from django.http import HttpRequest
                    from core.context_processors import domain_settings

                    # Create a dummy request for context processors
                    dummy_request = HttpRequest()

                    # Get context processor variables
                    processor_context = domain_settings(dummy_request)

                    # Merge contexts (user context takes priority)
                    full_context = {**processor_context, **context}
                    logger.info(f"Full context keys: {list(full_context.keys())}")

                    html_content = render_to_string(template, full_context)
                    logger.info(f"HTML content rendered successfully, length: {len(html_content)}")

                    # Create a clean plain text version
                    text_content = strip_tags(html_content)
                    # Clean up extra whitespace and line breaks
                    text_content = re.sub(r'\s+', ' ', text_content).strip()
                    text_content = re.sub(r'(\n\s*){3,}', '\n\n', text_content)

                except TemplateDoesNotExist as e:
                    logger.warning("Template not found: %s. Error: %s. Using fallback.",
                                   template, str(e))
                    html_content = None
                    fallback_msg = 'Notification from Equipment Platform'
                    text_content = context.get('message', fallback_msg)
                except Exception as template_error:
                    logger.error("Error rendering template %s: %s",
                                 template, str(template_error))
                    html_content = None
                    fallback_msg = 'Notification from Equipment Platform'
                    text_content = context.get('message', fallback_msg)

            elif context and 'message' in context:
                # Fallback to simple message
                text_content = context['message']
                html_content = None
            else:
                # Default message
                text_content = "You have new notifications. " \
                              "Please check the app."
                html_content = None

            # Validate recipient email
            if not recipient.user.email:
                logger.error("No email address for user: %s",
                             recipient.user.username)
                return False

            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient.user.email]
            )

            # Attach HTML version if we have valid HTML content
            if html_content and html_content.strip():
                msg.attach_alternative(html_content, "text/html")
                template_info = f"HTML template: {template}"
            else:
                template_info = "text-only"

            # Send the email
            msg.send(fail_silently=False)

            logger.info("Email sent to %s using %s",
                        recipient.user.email, template_info)
            return True

        except Exception as e:
            logger.error("Error sending email: %s", str(e))
            return False


# Convenience functions for specific notification types
class ContentNotifications:
    """Content-specific notification helpers."""

    @staticmethod
    def like_notification(post_or_comment, liker: UserProfile):
        """Create notification for likes."""
        if hasattr(post_or_comment, 'author'):
            recipient = post_or_comment.author
            content_type = 'post' if hasattr(post_or_comment, 'content') else 'comment'

            return NotificationService.create_notification(
                recipient=recipient,
                title=f"New like on your {content_type}",
                message=f"{liker.display_name} liked your {content_type}",
                notification_type='like',
                sender=liker,
                related_object=post_or_comment,
                app_context='content'
            )

    @staticmethod
    def comment_notification(post, commenter: UserProfile, comment):
        """Create notification for comments."""
        return NotificationService.create_notification(
            recipient=post.author,
            title="New comment on your post",
            message=f"{commenter.display_name} commented on your post",
            notification_type='comment',
            sender=commenter,
            related_object=comment,
            app_context='content'
        )

    @staticmethod
    def mention_notification(mentioned_user: UserProfile, mentioner: UserProfile, content):
        """Create notification for mentions."""
        return NotificationService.create_notification(
            recipient=mentioned_user,
            title="You were mentioned",
            message=f"{mentioner.display_name} mentioned you in a post",
            notification_type='mention',
            sender=mentioner,
            related_object=content,
            app_context='content'
        )


class MessagingNotifications:
    """Messaging-specific notification helpers."""

    @staticmethod
    def new_message_notification(recipient: UserProfile, sender: UserProfile, message):
        """Create notification for new messages."""
        return NotificationService.create_notification(
            recipient=recipient,
            title="New message",
            message=f"New message from {sender.display_name}",
            notification_type='new_message',
            sender=sender,
            related_object=message,
            app_context='messaging'
        )

    @staticmethod
    def mention_notification(mentioned_user: UserProfile, mentioner: UserProfile, message):
        """Create notification for mentions in messages."""
        return NotificationService.create_notification(
            recipient=mentioned_user,
            title="You were mentioned in a message",
            message=f"{mentioner.display_name} mentioned you in a message",
            notification_type='mention',
            sender=mentioner,
            related_object=message,
            app_context='messaging'
        )

    @staticmethod
    def group_message_notification(recipients: List[UserProfile], sender: UserProfile, message, group_name: str):
        """Create notifications for group messages."""
        return NotificationService.create_bulk_notifications(
            recipients=[r for r in recipients if r != sender],
            title=f"New message in {group_name}",
            message=f"{sender.display_name} sent a message in {group_name}",
            notification_type='group_message',
            sender=sender,
            related_object=message,
            app_context='messaging'
        )


# class EquipmentNotifications:
#     """Equipment-specific notification helpers."""

#     @staticmethod
#     def equipment_shared_notification(recipient: UserProfile, sharer: UserProfile, equipment):
#         """Create notification for equipment sharing."""
#         return NotificationService.create_notification(
#             recipient=recipient,
#             title="Equipment shared with you",
#             message=f"{sharer.display_name} shared equipment: {equipment.name}",
#             notification_type='equipment_shared',
#             sender=sharer,
#             related_object=equipment,
#             app_context='equipment'
#         )

#     @staticmethod
#     def equipment_request_notification(equipment_owner: UserProfile, requester: UserProfile, equipment):
#         """Create notification for equipment requests."""
#         return NotificationService.create_notification(
#             recipient=equipment_owner,
#             title="Equipment request",
#             message=f"{requester.display_name} requested to use your equipment: {equipment.name}",
#             notification_type='equipment_request',
#             sender=requester,
#             related_object=equipment,
#             app_context='equipment'
#         )

#     @staticmethod
#     def equipment_approved_notification(requester: UserProfile, approver: UserProfile, equipment):
#         """Create notification for approved equipment requests."""
#         return NotificationService.create_notification(
#             recipient=requester,
#             title="Equipment request approved",
#             message=f"Your request for {equipment.name} has been approved",
#             notification_type='equipment_approved',
#             sender=approver,
#             related_object=equipment,
#             app_context='equipment'
#         )

#     @staticmethod
#     def warranty_notification(equipment_owner: UserProfile, equipment, days_until_expiry: int):
#         """Create notification for warranty expiration."""
#         return NotificationService.create_notification(
#             recipient=equipment_owner,
#             title="Warranty Expiring Soon",
#             message=f"The warranty for your {equipment.name} expires in {days_until_expiry} days.",
#             notification_type='warranty',
#             related_object=equipment,
#             app_context='equipment'
#         )

#     @staticmethod
#     def maintenance_notification(equipment_owner: UserProfile, equipment, maintenance_type: str, priority: str = 'medium'):
#         """Create notification for equipment maintenance."""
#         priority_text = 'URGENT' if priority == 'high' else priority.title()
#         return NotificationService.create_notification(
#             recipient=equipment_owner,
#             title=f"{priority_text}: Maintenance Required",
#             message=f'Your {equipment.name} needs {maintenance_type} maintenance.',
#             notification_type='maintenance',
#             related_object=equipment,
#             app_context='equipment'
#         )


class SystemNotifications:
    """System-wide notification helpers."""

    @staticmethod
    def welcome_notification(user: UserProfile):
        """Create welcome notification for new users."""
        return NotificationService.create_notification(
            recipient=user,
            title="Welcome to Equipment Database!",
            message="Welcome! Start by exploring equipment and connecting with others.",
            notification_type='welcome',
            app_context='system'
        )

    @staticmethod
    def security_alert_notification(user: UserProfile, alert_message: str):
        """Create security alert notification."""
        return NotificationService.create_notification(
            recipient=user,
            title="Security Alert",
            message=alert_message,
            notification_type='security_alert',
            app_context='system'
        )

    @staticmethod
    def maintenance_notification(users: List[UserProfile], message: str):
        """Create maintenance notifications for multiple users."""
        return NotificationService.create_bulk_notifications(
            recipients=users,
            title="Scheduled Maintenance",
            message=message,
            notification_type='maintenance',
            app_context='system'
        )


class CommunityNotifications:
    """Community-specific notification helpers."""

    @staticmethod
    def geo_restriction_notification(
        user: UserProfile,
        community,
        restriction_type: str,
    restriction_message: Optional[str] = None,
    user_location: Optional[str] = None,
    send_email: bool = True,
    is_traveling: Optional[bool] = False,
    profile_location: Optional[str] = None,
    current_location: Optional[str] = None,
    ):
        """
        Create both display and email notifications for geo-restrictions.

        Args:
            user: UserProfile who was restricted
            community: Community object that was restricted
            restriction_type: Type of restriction (country, region, timezone)
            restriction_message: Custom restriction message
            user_location: User's current location for context
            send_email: Whether to send email notification (default: True)
            is_traveling: Whether user is marked as traveling
            profile_location: User's profile location
            current_location: User's current detected location
        """
        # Create display notification
        title = f"Access Restricted: {community.name}"
        message = (
            restriction_message or
            "This community has geographic restrictions. "
            "Access is limited based on your location."
        )

        logger.info(f"Creating geo-restriction notification for user: {user.user.username}")
        logger.info(f"Community: {community.name}, Restriction type: {restriction_type}")
        logger.info(f"Send email: {send_email}")

        # Prepare extra data with proper serialization
        community_id_str = ''
        try:
            community_id_str = str(community.id)
        except AttributeError:
            community_id_str = ''

        display_notification = NotificationService.create_notification(
            recipient=user,
            title=title,
            message=message,
            notification_type='geo_restriction',
            related_object=community,
            app_context='communities',
            extra_data={
                'restriction_type': restriction_type,
                'user_location': user_location,
                'is_traveling': bool(is_traveling),
                'profile_location': profile_location,
                'current_location': current_location,
                'community_id': community_id_str,
                'community_name': getattr(community, 'name', str(community))
            }
        )

        logger.info(f"Display notification created: {display_notification.id if display_notification else 'FAILED'}")

        # Send email notification if requested
        email_sent = False
        if send_email:
            logger.info("Attempting to send email notification...")
            # Update with actual domain from settings
            from django.conf import settings
            domain = getattr(settings, 'SITE_DOMAIN', 'your-domain.com')

            email_context = {
                'user': user.user,  # Pass the User object, not UserProfile
                'user_profile': user,  # Also pass UserProfile if needed
                'community': community,
                'restriction_message': restriction_message,
                'restriction_type': restriction_type.replace('_', ' ').title(),
                'user_location': (user_location or current_location or
                                profile_location or "Not specified"),
                'is_traveling': bool(is_traveling),
                'profile_location': profile_location,
                'current_location': current_location,
                'profile_settings_url': (
                    f"http://{domain}/profile/#settings"
                )
            }

            email_sent = NotificationService.send_email_notification(
                recipient=user,
                subject=f"Community Access Restricted - {community.name}",
                template='communities/email/geo_restriction_notice.html',
                context=email_context
            )
            logger.info(f"Email sent: {email_sent}")

        return {
            'display_notification': display_notification,
            'email_sent': email_sent
        }

    @staticmethod
    def community_invitation_notification(
        recipient: UserProfile,
        inviter: UserProfile,
        community
    ):
        """Create notification for community invitations."""
        return NotificationService.create_notification(
            recipient=recipient,
            title=f"Community Invitation: {community.name}",
            message=(
                f"{inviter.display_name} invited you to join {community.name}"
            ),
            notification_type='community_invite',
            sender=inviter,
            related_object=community,
            app_context='communities'
        )

    @staticmethod
    def community_join_notification(
        community_admin: UserProfile,
        new_member: UserProfile,
        community
    ):
        """Create notification for new community members."""
        return NotificationService.create_notification(
            recipient=community_admin,
            title=f"New Member: {community.name}",
            message=f"{new_member.display_name} joined your community",
            notification_type='community_join',
            sender=new_member,
            related_object=community,
            app_context='communities'
        )

    @staticmethod
    def community_role_change_notification(
        recipient: UserProfile,
        role_changer: UserProfile,
        community,
        new_role: str
    ):
        """Create notification for community role changes."""
        return NotificationService.create_notification(
            recipient=recipient,
            title=f"Role Changed: {community.name}",
            message=(
                f"Your role in {community.name} has been changed to {new_role}"
            ),
            notification_type='community_role_change',
            sender=role_changer,
            related_object=community,
            app_context='communities'
        )

    @staticmethod
    def moderator_assignment_notification(
        user: UserProfile,
        community,
        assigned_by: UserProfile = None,
        membership=None,
        send_email: bool = True
    ):
        """
        Notify a user that they've been assigned as a moderator for a community.

        Creates an in-app notification and (optionally) sends an email.
        """
        try:
            title = f"Moderator Assignment: {getattr(community, 'name', 'a community')}"
            # Use display_name property method correctly
            if assigned_by and hasattr(assigned_by, 'display_name'):
                assigner_name = assigned_by.display_name
            elif assigned_by and assigned_by.user:
                assigner_name = assigned_by.user.username
            else:
                assigner_name = 'Someone'

            community_name = getattr(community, 'name', 'this community')
            message = (f"You have been assigned as a moderator of "
                      f"{community_name} by {assigner_name}.")

            display_notification = NotificationService.create_notification(
                recipient=user,
                title=title,
                message=message,
                notification_type='community_role_change',
                sender=assigned_by,
                related_object=community,
                app_context='communities'
            )

            email_sent = False
            if send_email:
                try:
                    from django.conf import settings

                    domain = getattr(settings, 'SITE_DOMAIN', 'your-domain.com')
                    frontend_domain = getattr(settings, 'FRONTEND_DOMAIN', 'localhost:3000')

                    # Generate notification URL pointing to notification detail page
                    notification_url = None
                    if display_notification:
                        # Link directly to the notification detail page
                        notification_url = (
                            f"http://{frontend_domain}/notifications/"
                            f"{display_notification.id}"
                        )
                    elif membership:
                        # Fallback for membership ID
                        notification_url = (
                            f"http://{frontend_domain}/notifications"
                            f"?membership_id={membership.id}"
                        )

                    email_context = {
                        'user': user,
                        'community': community,
                        'assigned_by': assigned_by,
                        'profile_settings_url': (
                            f"http://{domain}/profile/#settings"
                        ),
                        'message': message,
                        'notification_url': notification_url,
                        'membership': membership
                    }

                    subject = (
                        f"You were made a moderator of "
                        f"{getattr(community, 'name', '')}"
                    )
                    email_sent = NotificationService.send_email_notification(
                        recipient=user,
                        subject=subject,
                        template='communities/email/moderator_assignment.html',
                        context=email_context
                    )
                except Exception:
                    # Don't let email failures block the main flow
                    email_sent = False

            return {
                'display_notification': display_notification,
                'email_sent': email_sent
            }

        except Exception as exc:
            logger.exception(
                'Failed to send moderator assignment notification: %s', exc
            )
            return {'display_notification': None, 'email_sent': False}


class BadgeNotifications:
    """Badge / achievement notification helpers."""
    @staticmethod
    def badge_awarded(user_badge):
        from notifications.utils import NotificationService
        profile = user_badge.profile
        badge = user_badge.badge
        title = f"Badge Earned: {badge.name}"
        message = badge.description or f"You earned the {badge.name} badge!"
        return NotificationService.create_notification(
            recipient=profile,
            title=title,
            message=message,
            notification_type='badge',
            related_object=user_badge,
            app_context='system',
            extra_data={'badge_code': badge.code, 'points': badge.points}
        )


# Export the main service and helper classes
__all__ = [
    'NotificationService',
    'ContentNotifications',
    'MessagingNotifications',

    'SystemNotifications',
    'CommunityNotifications',
    'BadgeNotifications'
]
