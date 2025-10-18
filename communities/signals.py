"""
Signals for community notifications with real-time WebSocket support.
Handles automatic notification creation for community events.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from notifications.utils import CommunityNotifications
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='communities.CommunityMembership')
def handle_community_membership_created(sender, instance, created, **kwargs):
    """Handle new community membership creation with real-time notifications."""
    # pylint: disable=unused-argument
    if created and instance.status == 'active':
        try:
            # Skip ALL notifications during community creation time
            # Only handle notifications for post-creation member joining
            from django.utils import timezone
            from datetime import timedelta

            community_created_recently = (
                timezone.now() - instance.community.created_at
            ) < timedelta(minutes=10)  # 10 minute window for initial setup

            if community_created_recently:
                logger.info(
                    "Skipping membership notification during community creation: %s",
                    instance.user.user.username
                )
                return

            # This is a regular member joining an existing community
            # Send real-time notification to the new member
            from notifications.realtime import (
                send_community_membership_notification
            )
            send_community_membership_notification(
                user_profile=instance.user,
                community_name=instance.community.name,
                status='approved'
            )

            # Notify community admins about new member
            admin_memberships = sender.objects.filter(
                community=instance.community,
                role__name__in=['Admin', 'Creator'],
                status='active',
                is_deleted=False
            ).select_related('user')

            for admin_membership in admin_memberships:
                # Don't notify self
                if admin_membership.user != instance.user:
                    CommunityNotifications.community_join_notification(
                        community_admin=admin_membership.user,
                        new_member=instance.user,
                        community=instance.community
                    )

                    # Send real-time notification to admin
                    from notifications.realtime import (
                        send_community_notification
                    )
                    send_community_notification(
                        user_profile=admin_membership.user,
                        notification_type='new_member',
                        data={
                            'title': f'New member in {instance.community.name}',
                            'message': (
                                f'@{instance.user.user.username} joined '
                                f'{instance.community.name}'
                            ),
                            'community_name': instance.community.name,
                            'community_id': str(instance.community.id),
                            'member_username': instance.user.user.username
                        }
                    )

        except ObjectDoesNotExist as e:
            logger.error("Failed to create membership notification: %s", str(e))
        except (ValueError, AttributeError) as e:
            logger.error("Unexpected error in membership notification: %s", str(e))


# # Commented out - Public communities don't use invitations
# @receiver(post_save, sender='communities.CommunityInvitation')
# def handle_community_invitation_created(sender, instance, created, **kwargs):
#     """Handle community invitation creation."""
#     # pylint: disable=unused-argument
#     if created and instance.status == 'pending':
#         try:
#             CommunityNotifications.community_invitation_notification(
#                 recipient=instance.invitee,
#                 inviter=instance.inviter,
#                 community=instance.community
#             )
#         except ObjectDoesNotExist as e:
#             logger.error("Failed to create invitation notification: %s", str(e))
#         except Exception as e:
#             logger.error("Unexpected error in invitation notification: %s", str(e))


@receiver(post_save, sender='communities.CommunityMembership')
def handle_community_role_change(sender, instance, created, **kwargs):
    """Handle community role changes."""
    # pylint: disable=unused-argument
    if not created and hasattr(instance, '_role_changed'):
        try:
            # Skip notifications during community creation time
            from django.utils import timezone
            from datetime import timedelta

            community_created_recently = (
                timezone.now() - instance.community.created_at
            ) < timedelta(minutes=10)  # 10 minute window for initial setup

            if community_created_recently:
                logger.info(
                    "Skipping role change notification during creation: %s",
                    instance.user.user.username
                )
                return

            # This is a post-creation role change
            CommunityNotifications.community_role_change_notification(
                recipient=instance.user,
                role_changer=getattr(instance, '_role_changed_by', None),
                community=instance.community,
                new_role=instance.role
            )
        except ObjectDoesNotExist as e:
            logger.error("Failed to create role change notification: %s", str(e))
        except (ValueError, AttributeError) as e:
            logger.error("Unexpected error in role change notification: %s", str(e))


@receiver(post_save, sender='communities.Community')
def populate_enabled_rubriques(sender, instance, created, **kwargs):
    """Auto-populate enabled_rubriques with ALL active rubriques for new communities.

    All communities start with all rubriques enabled by default.
    Customization happens later when communities disable specific rubriques.
    """
    # pylint: disable=unused-argument
    if created:
        try:
            from .models import RubriqueTemplate

            # Get ALL active templates (including parent and children)
            all_templates = RubriqueTemplate.objects.filter(
                is_active=True
            ).order_by('path', 'default_order')

            # Populate enabled_rubriques with ALL rubrique UUIDs
            instance.enabled_rubriques = [
                str(template.id) for template in all_templates
            ]
            instance.save(update_fields=['enabled_rubriques'])

            logger.info(
                "Populated ALL %d active rubriques for community: %s",
                len(instance.enabled_rubriques),
                instance.name
            )

        except Exception as e:
            logger.error(
                "Failed to populate rubriques for community %s: %s",
                instance.name,
                str(e)
            )


