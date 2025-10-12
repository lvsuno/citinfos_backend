"""Celery tasks for communities app."""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import (
    Community, CommunityMembership,
    CommunityModeration, CommunityRole
)
from analytics.models import SystemMetric, ErrorLog

# NOTE: CommunityInvitation and CommunityJoinRequest models are currently disabled
# Tasks using these models have been commented out


@shared_task
def reactivate_expired_bans():
    """
    Reactivate banned users whose ban duration has expired.
    Sets status to 'active' and clears ban fields.
    """
    now = timezone.now()
    expired_bans = CommunityMembership.objects.filter(
        status='banned',
        ban_expires_at__isnull=False,
        ban_expires_at__lte=now
    )
    for membership in expired_bans:
        membership.status = 'active'
        membership.banned_by = None
        membership.ban_reason = ''
        membership.banned_at = None
        membership.ban_expires_at = None
        membership.save(update_fields=['status', 'banned_by', 'ban_reason', 'banned_at', 'ban_expires_at'])


# @shared_task
# def cleanup_expired_community_join_requests():
#     """Mark pending community join requests as expired if not reviewed after 14 days."""
#     # NOTE: CommunityJoinRequest model is currently disabled
#     pass


@shared_task
def update_community_basic_metrics():
    """Update basic community metrics (member counts, post counts)"""
    try:
        communities = Community.objects.filter(is_active=True, is_deleted=False)

        for community in communities:
            # Calculate engagement metrics from related content
            recent_posts_count = 0
            total_engagement = 0

            # Get posts related to this community (if content app is available)
            try:
                recent_posts = community.posts.filter(
                    created_at__gte=timezone.now() - timedelta(days=7),
                    is_deleted=False
                )
                recent_posts_count = recent_posts.count()

                for post in recent_posts:
                    post_engagement = (
                        post.likes_count +
                        post.comments_count * 2 +
                        post.shares_count * 3
                    )
                    total_engagement += post_engagement
            except AttributeError:
                # Handle case where content app is not available
                recent_posts_count = 0
                total_engagement = 0

            avg_engagement = total_engagement / max(recent_posts_count, 1)

            # Update community counters
            community.members_count = community.memberships.filter(
                status='active',
                is_deleted=False
            ).count()
            community.posts_count = recent_posts_count
            community.save()

            # Store basic metrics for analytics system to use
            SystemMetric.objects.create(
                metric_type='community_engagement',
                value=avg_engagement,
                additional_data={
                    'community_id': str(community.id),
                    'community_name': community.name,
                    'recent_posts_7d': recent_posts_count,
                    'total_members': community.members_count,
                    'last_updated': timezone.now().isoformat()
                }
            )

        return f"Updated basic metrics for {communities.count()} communities"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating community basic metrics: {str(e)}',
            extra_data={'task': 'update_community_basic_metrics'}
        )
        return f"Error updating community basic metrics: {str(e)}"


# @shared_task
# def cleanup_expired_community_invitations():
#     """Clean up expired community invitations"""
#     # NOTE: CommunityInvitation model is currently disabled
#     # Uncomment this task when the model is re-enabled
#     pass
#     # try:
#     #     expired_invitations = CommunityInvitation.objects.filter(
#     #         expires_at__lt=timezone.now(),
#     #         status='pending'
#     #     )
#     #
#     #     expired_count = expired_invitations.count()
#     #     expired_invitations.update(status='expired')
#     #
#     #     return f"Marked {expired_count} community invitations as expired"
#     #
#     # except Exception as e:
#     #     ErrorLog.objects.create(
#     #         level='error',
#     #         message=f'Error cleaning up community invitations: {str(e)}',
#     #         extra_data={'task': 'cleanup_expired_community_invitations'}
#     #     )
#     #     return f"Error cleaning up community invitations: {str(e)}"


@shared_task
def update_community_member_counts():
    """Update member counts for all communities"""
    try:
        communities = Community.objects.all()
        updated_count = 0

        for community in communities:
            # Count active members
            active_member_count = community.memberships.filter(
                status='active'
            ).count()

            # Update if count has changed
            if community.members_count != active_member_count:
                community.members_count = active_member_count
                community.save(update_fields=['members_count'])
                updated_count += 1

        return f"Updated member counts for {updated_count} communities"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating community member counts: {str(e)}',
            extra_data={'task': 'update_community_member_counts'}
        )
        return f"Error updating community member counts: {str(e)}"


@shared_task
def cleanup_inactive_communities():
    """Mark communities as inactive if they have no activity for 90 days"""
    try:
        cutoff_date = timezone.now() - timedelta(days=90)

        # Find communities with no recent activity
        cutoff_date = timezone.now() - timedelta(days=90)

        # Get all communities that haven't been updated recently
        old_communities = Community.objects.filter(
            is_active=True,
            updated_at__lt=cutoff_date
        )

        # Find which ones to mark as inactive
        communities_to_deactivate = []
        for community in old_communities:
            # Check if community has recent membership activity
            recent_activity = community.memberships.filter(
                last_active__gte=cutoff_date
            ).exists()

            # If no recent activity, mark for deactivation
            if not recent_activity:
                communities_to_deactivate.append(community.id)

        # Mark identified communities as inactive
        inactive_count = Community.objects.filter(
            id__in=communities_to_deactivate
        ).update(is_active=False)

        return f"Marked {inactive_count} communities as inactive"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error cleaning up inactive communities: {str(e)}',
            extra_data={'task': 'cleanup_inactive_communities'}
        )
        return f"Error cleaning up inactive communities: {str(e)}"


# @shared_task
# def process_community_join_requests():
#     """Process pending join requests for restricted communities only"""
#     # NOTE: CommunityJoinRequest model is currently disabled
#     pass


@shared_task
def validate_community_access_rules():
    """Validate and enforce community access rules"""
    try:
        # NOTE: CommunityJoinRequest model is currently disabled
        # # Clean up invalid join requests for public/private communities
        # invalid_requests = CommunityJoinRequest.objects.filter(
        #     status='pending',
        #     community__community_type__in=['public', 'private']
        # )
        #
        # invalid_count = invalid_requests.count()
        # invalid_requests.update(
        #     status='rejected',
        #     reviewed_at=timezone.now(),
        #     review_message='Join requests not allowed for this community type'
        # )

        invalid_count = 0

        # NOTE: CommunityInvitation model is currently disabled
        # # Find expired invitations and mark them as expired
        # expired_invitations = CommunityInvitation.objects.filter(
        #     status='pending',
        #     expires_at__lt=timezone.now()
        # )
        #
        # expired_count = expired_invitations.count()
        # expired_invitations.update(
        #     status='expired',
        #     responded_at=timezone.now()
        # )
        #
        # # Find invitations that are about to expire (within 24 hours)
        # # This could be used to send reminder notifications
        # expiring_soon = CommunityInvitation.objects.filter(
        #     status='pending',
        #     expires_at__lt=timezone.now() + timedelta(hours=24),
        #     expires_at__gt=timezone.now()
        # )
        #
        # expiring_count = expiring_soon.count()

        expired_count = 0
        expiring_count = 0

        return (f"Rejected {invalid_count} invalid join requests, "
                f"expired {expired_count} invitations, "
                f"{expiring_count} invitations expiring soon")

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error validating community access rules: {str(e)}',
            extra_data={'task': 'validate_community_access_rules'}
        )
        return f"Error validating community access rules: {str(e)}"


@shared_task
def update_community_moderation_stats():
    """Update moderation stats for all communities."""
    try:
        communities = Community.objects.filter(is_active=True)
        updated_count = 0
        for community in communities:
            moderation_actions = CommunityModeration.objects.filter(
                community=community,
                is_active=True
            )
            total_bans = moderation_actions.filter(action_type='ban').count()
            total_mutes = moderation_actions.filter(action_type='mute').count()
            total_warnings = moderation_actions.filter(action_type='warn').count()
            # Store stats in SystemMetric
            SystemMetric.objects.create(
                metric_type='community_moderation_stats',
                value=total_bans + total_mutes + total_warnings,
                additional_data={
                    'community_id': str(community.id),
                    'community_name': community.name,
                    'bans': total_bans,
                    'mutes': total_mutes,
                    'warnings': total_warnings
                }
            )
            updated_count += 1
        return f"Updated moderation stats for {updated_count} communities"
    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating moderation stats: {str(e)}',
            extra_data={'task': 'update_community_moderation_stats'}
        )
        return f"Error updating moderation stats: {str(e)}"


@shared_task
def update_community_role_stats():
    """Update role stats for all communities."""
    try:
        communities = Community.objects.filter(is_active=True)
        updated_count = 0
        for community in communities:
            roles = CommunityRole.objects.filter(community=community)
            role_counts = {}
            for role in roles:
                member_count = role.memberships.filter(status='active').count()
                role_counts[role.name] = member_count
            # Store stats in SystemMetric
            SystemMetric.objects.create(
                metric_type='community_role_stats',
                value=sum(role_counts.values()),
                additional_data={
                    'community_id': str(community.id),
                    'community_name': community.name,
                    'role_counts': role_counts
                }
            )
            updated_count += 1
        return f"Updated role stats for {updated_count} communities"
    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating role stats: {str(e)}',
            extra_data={'task': 'update_community_role_stats'}
        )
        return f"Error updating role stats: {str(e)}"


@shared_task
def sync_community_with_analytics():
    """Sync community data with the new analytics system."""
    try:
        # Import here to avoid circular imports
        from analytics.services import online_tracker
        from analytics.tasks import update_community_analytics

        # Update member last_active timestamps for users currently online
        communities = Community.objects.filter(is_active=True, is_deleted=False)
        synced_count = 0

        for community in communities:
            community_id = str(community.id)

            # Get online members from Redis
            online_members = online_tracker.get_online_members(community_id)

            # Update last_active for online members
            if online_members:
                memberships_updated = CommunityMembership.objects.filter(
                    community=community,
                    user__id__in=online_members,
                    status='active',
                    is_deleted=False
                ).update(last_active=timezone.now())

                synced_count += memberships_updated

        # Trigger comprehensive analytics update
        update_community_analytics.delay()

        return f"Synced {synced_count} member activity records with analytics system"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error syncing community with analytics: {str(e)}',
            extra_data={'task': 'sync_community_with_analytics'}
        )
        return f"Error syncing community with analytics: {str(e)}"


# @shared_task
# def cleanup_expired_community_join_requests_extended():
#     """Enhanced cleanup of expired join requests with analytics tracking."""
#     # NOTE: CommunityJoinRequest model is currently disabled
#     pass
