"""Django signals for community analytics and online tracking."""

import logging
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver, Signal
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from communities.models import Community, CommunityMembership
from analytics.models import CommunityAnalytics
from analytics.services import online_tracker
from analytics.tasks import sync_member_activity, update_community_analytics

logger = logging.getLogger(__name__)

# Custom signal for activity tracking
user_activity_signal = Signal()

@receiver(post_save, sender=CommunityMembership)
def handle_membership_change(sender, instance, created, **kwargs):
    """Handle community membership changes."""
    _ = sender, kwargs  # Ignore unused parameters
    try:
        community_id = str(instance.community.id)
        user_id = str(instance.user.id)

        if created and instance.status == 'active':
            # New member joined
            logger.info("New member %s joined community %s", user_id, community_id)

            # Update community member count
            instance.community.members_count += 1
            instance.community.save(update_fields=['members_count'])

            # Trigger analytics update
            update_community_analytics.delay(community_id)

        elif not created:
            # Membership status changed
            if instance.status == 'active' and not instance.is_deleted:
                # Member became active - add to online tracking
                sync_member_activity.delay(user_id, community_id)
            elif instance.status in ['banned', 'left'] or instance.is_deleted:
                # Member left or was banned - remove from online tracking
                online_tracker.remove_user_from_community(user_id, community_id)

                # Update community member count
                if instance.status == 'left':
                    instance.community.members_count = max(0, instance.community.members_count - 1)
                    instance.community.save(update_fields=['members_count'])

                # Trigger analytics update
                update_community_analytics.delay(community_id)

    except Exception as e:
        logger.error("Error handling membership change: %s", e)

@receiver(pre_delete, sender=CommunityMembership)
def handle_membership_deletion(sender, instance, **kwargs):
    """Handle membership deletion."""
    _ = sender, kwargs  # Ignore unused parameters
    try:
        community_id = str(instance.community.id)
        user_id = str(instance.user.id)

        # Remove from online tracking
        online_tracker.remove_user_from_community(user_id, community_id)

        # Update community member count
        if instance.status == 'active':
            instance.community.members_count = max(0, instance.community.members_count - 1)
            instance.community.save(update_fields=['members_count'])

        # Trigger analytics update
        update_community_analytics.delay(community_id)

        logger.info("Membership deleted for user %s in community %s", user_id, community_id)

    except Exception as e:
        logger.error("Error handling membership deletion: %s", e)

@receiver(user_logged_in)
def handle_user_login(sender, request, user, **kwargs):
    """Handle user login - add to all their active communities."""
    _ = sender, request, kwargs  # Ignore unused parameters
    try:
        if hasattr(user, 'profile'):
            user_profile = user.profile
            user_id = str(user_profile.id)

            # Get all active community memberships
            active_memberships = CommunityMembership.objects.filter(
                user=user_profile,
                status='active',
                is_deleted=False
            )

            # Add user to all their communities' online tracking
            for membership in active_memberships:
                community_id = str(membership.community.id)
                online_tracker.add_user_to_community(user_id, community_id)

                # Update last_active timestamp
                membership.last_active = timezone.now()
                membership.save(update_fields=['last_active'])

            logger.info("User %s logged in and added to %d communities",
                       user_id, active_memberships.count())

    except Exception as e:
        logger.error("Error handling user login: %s", e)

@receiver(user_logged_out)
def handle_user_logout(sender, request, user, **kwargs):
    """Handle user logout - remove from all communities."""
    _ = sender, request, kwargs  # Ignore unused parameters
    try:
        if hasattr(user, 'profile'):
            user_profile = user.profile
            user_id = str(user_profile.id)

            # Get user's active communities from Redis
            active_communities = online_tracker.get_user_communities(user_id)

            # Remove user from all communities
            for community_id in active_communities:
                online_tracker.remove_user_from_community(user_id, community_id)

            logger.info("User %s logged out and removed from %d communities",
                       user_id, len(active_communities))

    except Exception as e:
        logger.error("Error handling user logout: %s", e)

@receiver(post_save, sender=Community)
def handle_community_creation(sender, instance, created, **kwargs):
    """Handle community creation."""
    _ = sender, kwargs  # Ignore unused parameters
    try:
        if created:
            # Create initial analytics record
            CommunityAnalytics.objects.get_or_create(
                community=instance,
                date=timezone.now().date(),
                defaults={
                    'current_online_members': 0,
                    'peak_online_today': 0,
                    'peak_online_this_week': 0,
                    'peak_online_this_month': 0,
                }
            )

            logger.info("Created analytics for new community %s", instance.id)

    except Exception as e:
        logger.error("Error handling community creation: %s", e)

@receiver(user_activity_signal)
def handle_user_activity(sender, user_id, community_id, activity_type='general', **kwargs):
    """Handle user activity signals."""
    _ = sender, kwargs  # Ignore unused parameters
    try:
        # Update Redis tracking
        current_count = online_tracker.update_user_activity(
            str(user_id),
            str(community_id)
        )

        # Trigger async task to sync with database
        sync_member_activity.delay(str(user_id), str(community_id))

        logger.debug("User %s activity in community %s (type: %s). Online count: %d",
                    user_id, community_id, activity_type, current_count)

    except Exception as e:
        logger.error("Error handling user activity: %s", e)

# Helper function to trigger activity
def track_user_activity(user_id, community_id, activity_type='general'):
    """Helper function to track user activity."""
    user_activity_signal.send(
        sender=None,
        user_id=user_id,
        community_id=community_id,
        activity_type=activity_type
    )
