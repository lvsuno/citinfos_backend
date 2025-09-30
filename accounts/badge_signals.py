"""
Django signals for automatic badge evaluation when user stats change.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import UserProfile
from accounts.badge_triggers import trigger_badge_evaluation
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=UserProfile)
def handle_user_profile_badge_evaluation(sender, instance, created, **kwargs):
    """
    Trigger badge evaluation when UserProfile is updated with stat changes.

    This signal fires when UserProfile fields that affect badges are updated.
    We check if any badge-relevant fields have changed and trigger evaluation.
    """
    if created:
        # New user profile created - evaluate for early adopter and initial badges
        try:
            trigger_badge_evaluation(
                instance,
                'profile_created',
                async_evaluation=True,
                delay_seconds=10  # Give time for other setup operations
            )
            logger.info(f"Badge evaluation triggered for new profile: {instance.user.username}")
        except Exception as e:
            logger.error(f"Error triggering badge evaluation for new profile {instance.id}: {str(e)}")
        return

    # For existing profiles, check if badge-relevant fields changed
    if not hasattr(instance, '_state') or not instance._state.adding:
        # Get the previous state from database to compare
        try:
            # Fields that should trigger badge evaluation when changed
            badge_relevant_fields = [
                'posts_count',
                'polls_created_count',
                'poll_votes_count',
                'likes_given_count',
                'comments_made_count',
                'reposts_count',
                'shares_sent_count',
                'shares_received_count',
                'best_comments_count',
                'communities_joined_count',
                'follower_count',
                'following_count',
                'engagement_score',
                'content_quality_score',
                'interaction_frequency'
            ]

            # Get the current instance from database (pre-save state)
            try:
                old_instance = UserProfile.objects.get(pk=instance.pk)
            except UserProfile.DoesNotExist:
                # Profile might be new, treat as created
                return

            # Check if any badge-relevant field changed
            fields_changed = []
            for field in badge_relevant_fields:
                old_value = getattr(old_instance, field, 0)
                new_value = getattr(instance, field, 0)

                if old_value != new_value:
                    fields_changed.append(f"{field}: {old_value} -> {new_value}")

            # If badge-relevant fields changed, trigger evaluation
            if fields_changed:
                trigger_badge_evaluation(
                    instance,
                    'stats_updated',
                    async_evaluation=True,
                    delay_seconds=3
                )

                logger.info(
                    f"Badge evaluation triggered for {instance.user.username} "
                    f"due to changes in: {', '.join(fields_changed[:3])}"  # Log first 3 changes
                )

        except Exception as e:
            logger.error(f"Error checking badge evaluation triggers for profile {instance.id}: {str(e)}")


# Additional signals for specific model events that affect badges

def setup_badge_signals():
    """
    Setup additional signals for badge evaluation triggers.
    Call this function in apps.py ready() method.
    """

    # Import models at runtime to avoid circular imports
    try:
        from content.models import Post

        @receiver(post_save, sender=Post)
        def handle_post_created_badge_evaluation(sender, instance, created, **kwargs):
            """Trigger badge evaluation when user creates a post."""
            if created and hasattr(instance, 'author'):
                try:
                    trigger_badge_evaluation(
                        instance.author,
                        'post_created',
                        async_evaluation=True,
                        delay_seconds=2
                    )
                except Exception as e:
                    logger.error(f"Error triggering badge evaluation for post creation: {str(e)}")

    except ImportError:
        logger.warning("Content models not available for badge signal setup")

    try:
        from content.models import Comment

        @receiver(post_save, sender=Comment)
        def handle_comment_created_badge_evaluation(sender, instance, created, **kwargs):
            """Trigger badge evaluation when user creates a comment."""
            if created and hasattr(instance, 'author'):
                try:
                    trigger_badge_evaluation(
                        instance.author,
                        'comment_created',
                        async_evaluation=True,
                        delay_seconds=1
                    )
                except Exception as e:
                    logger.error(f"Error triggering badge evaluation for comment creation: {str(e)}")

    except ImportError:
        logger.warning("Comment model not available for badge signal setup")

    try:
        from accounts.models import Follow

        @receiver(post_save, sender=Follow)
        def handle_follow_created_badge_evaluation(sender, instance, created, **kwargs):
            """Trigger badge evaluation when user follows someone."""
            if created:
                try:
                    # Trigger evaluation for both follower and followed user
                    trigger_badge_evaluation(
                        instance.follower,
                        'follow_made',
                        async_evaluation=True,
                        delay_seconds=2
                    )
                    trigger_badge_evaluation(
                        instance.followed,
                        'follower_gained',
                        async_evaluation=True,
                        delay_seconds=2
                    )
                except Exception as e:
                    logger.error(f"Error triggering badge evaluation for follow: {str(e)}")

    except ImportError:
        logger.warning("Follow model not available for badge signal setup")


# Utility function to manually trigger badge evaluation for testing

def manual_badge_evaluation_trigger(user_profile, trigger_type="manual", sync=False):
    """
    Manually trigger badge evaluation for testing purposes.

    Args:
        user_profile: UserProfile instance
        trigger_type: Type of manual trigger
        sync: Whether to run synchronously (default: False)

    Returns:
        Task ID if async, result if sync
    """
    return trigger_badge_evaluation(
        user_profile,
        trigger_type,
        async_evaluation=not sync,
        delay_seconds=0 if sync else 1
    )
