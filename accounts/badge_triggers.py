"""
Utility functions for triggering badge evaluations based on user actions.
"""

from typing import Optional
from django.db import transaction
from celery import current_app
from accounts.models import UserProfile


def trigger_badge_evaluation(
    user_profile: UserProfile,
    trigger_event: str,
    async_evaluation: bool = True,
    delay_seconds: int = 5
) -> Optional[str]:
    """
    Trigger badge evaluation for a user after a specific action.

    Args:
        user_profile: The UserProfile to evaluate
        trigger_event: The event that triggered this evaluation
                      (e.g., 'post_created', 'follow_made', 'comment_posted')
        async_evaluation: Whether to run evaluation asynchronously (default: True)
        delay_seconds: Delay before running async task (default: 5 seconds)

    Returns:
        Task ID if async, or result string if sync
    """
    if async_evaluation:
        # Import the task at runtime to avoid circular imports
        from accounts.tasks import evaluate_badges_for_profile_task

        # Schedule the task with a small delay to allow other operations to complete
        task = evaluate_badges_for_profile_task.apply_async(
            args=[str(user_profile.id)],
            countdown=delay_seconds
        )
        return task.id
    else:
        # Run synchronously (use with caution)
        from accounts.badge_evaluator import badge_evaluator
        awarded_count, new_badges = badge_evaluator.evaluate_user_badges(user_profile)
        return f"Sync evaluation: {awarded_count} badges awarded: {', '.join(new_badges)}"


def trigger_badge_evaluation_by_trigger_type(
    trigger_type: str,
    user_profile: Optional[UserProfile] = None,
    async_evaluation: bool = True,
    delay_seconds: int = 10
) -> Optional[str]:
    """
    Trigger badge evaluation based on trigger type with optimized processing.

    Args:
        trigger_type: Type of trigger event
        user_profile: Specific user to evaluate (None = all users)
        async_evaluation: Whether to run asynchronously
        delay_seconds: Delay before execution

    Returns:
        Task ID if async, or result if sync
    """
    if async_evaluation:
        from accounts.tasks import evaluate_badges_by_trigger

        user_id = str(user_profile.id) if user_profile else None
        task = evaluate_badges_by_trigger.apply_async(
            args=[trigger_type, user_id],
            countdown=delay_seconds
        )
        return task.id
    else:
        # Handle sync execution
        if user_profile:
            return trigger_badge_evaluation(
                user_profile,
                trigger_type,
                async_evaluation=False
            )
        else:
            # Sync evaluation for all users - use with extreme caution
            from accounts.badge_evaluator import badge_evaluator
            stats = badge_evaluator.evaluate_all_users(batch_size=50)
            return f"All users evaluation: {stats['total_badges_awarded']} badges awarded"


# Predefined trigger functions for common actions

def on_post_created(user_profile: UserProfile) -> Optional[str]:
    """Trigger badge evaluation after post creation."""
    return trigger_badge_evaluation(user_profile, 'post_created', delay_seconds=3)


def on_comment_posted(user_profile: UserProfile) -> Optional[str]:
    """Trigger badge evaluation after comment posting."""
    return trigger_badge_evaluation(user_profile, 'comment_posted', delay_seconds=2)


def on_like_given(user_profile: UserProfile) -> Optional[str]:
    """Trigger badge evaluation after giving a like."""
    return trigger_badge_evaluation(user_profile, 'like_given', delay_seconds=1)


def on_follow_made(user_profile: UserProfile) -> Optional[str]:
    """Trigger badge evaluation after following someone."""
    return trigger_badge_evaluation(user_profile, 'follow_made', delay_seconds=2)


def on_poll_created(user_profile: UserProfile) -> Optional[str]:
    """Trigger badge evaluation after creating a poll."""
    return trigger_badge_evaluation(user_profile, 'poll_created', delay_seconds=2)


def on_poll_vote_cast(user_profile: UserProfile) -> Optional[str]:
    """Trigger badge evaluation after voting in a poll."""
    return trigger_badge_evaluation(user_profile, 'poll_vote_cast', delay_seconds=1)


def on_best_comment_marked(user_profile: UserProfile) -> Optional[str]:
    """Trigger badge evaluation after comment is marked as best."""
    return trigger_badge_evaluation(user_profile, 'best_comment_marked', delay_seconds=2)


def on_community_joined(user_profile: UserProfile) -> Optional[str]:
    """Trigger badge evaluation after joining a community."""
    return trigger_badge_evaluation(user_profile, 'community_joined', delay_seconds=2)


def on_repost_made(user_profile: UserProfile) -> Optional[str]:
    """Trigger badge evaluation after making a repost."""
    return trigger_badge_evaluation(user_profile, 'repost_made', delay_seconds=1)


def on_share_sent(user_profile: UserProfile) -> Optional[str]:
    """Trigger badge evaluation after sending a share."""
    return trigger_badge_evaluation(user_profile, 'share_sent', delay_seconds=1)


def on_share_received(user_profile: UserProfile) -> Optional[str]:
    """Trigger badge evaluation after receiving a share."""
    return trigger_badge_evaluation(user_profile, 'share_received', delay_seconds=1)


# Batch evaluation triggers

def trigger_daily_badge_evaluation() -> Optional[str]:
    """Trigger comprehensive daily badge evaluation for all users."""
    from accounts.tasks import evaluate_all_badges_periodic

    task = evaluate_all_badges_periodic.apply_async(countdown=60)  # 1 minute delay
    return task.id


def trigger_badge_threshold_update() -> Optional[str]:
    """Trigger badge definition update after threshold changes."""
    from accounts.tasks import initialize_badge_definitions

    task = initialize_badge_definitions.apply_async(countdown=30)  # 30 second delay
    return task.id


# Helper function to get badge progress for display

def get_user_badge_progress(user_profile: UserProfile, badge_codes: list = None) -> dict:
    """
    Get badge progress for a user, optionally for specific badges.

    Args:
        user_profile: The UserProfile to check
        badge_codes: List of specific badge codes to check (None = all)

    Returns:
        Dictionary with badge progress information
    """
    from accounts.badge_evaluator import badge_evaluator
    from accounts.models import BadgeDefinition

    if badge_codes:
        # Get progress for specific badges
        progress = {}
        for badge_code in badge_codes:
            progress[badge_code] = badge_evaluator.get_badge_progress(
                user_profile, badge_code
            )
        return progress
    else:
        # Get progress for all active badges
        active_badges = BadgeDefinition.objects.filter(
            is_active=True,
            is_deleted=False
        ).values_list('code', flat=True)

        progress = {}
        for badge_code in active_badges:
            progress[badge_code] = badge_evaluator.get_badge_progress(
                user_profile, badge_code
            )
        return progress
