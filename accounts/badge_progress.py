"""
Badge progress calculation utilities for finding nearest achievable badges.
"""
from django.utils import timezone
from .models import BadgeDefinition, UserBadge
from content.models import Post, Comment, DirectShare, Like, Dislike
from accounts.models import Follow


def get_user_statistics(user_profile):
    """
    Collect all relevant user statistics for badge evaluation.
    Returns a dictionary with all counters needed for badge criteria.
    """
    user = user_profile.user

    # Get counts for various activities
    stats = {
        # Content creation stats
        'posts_count': Post.objects.filter(
            author=user_profile, is_deleted=False
        ).count(),
        'comments_count': Comment.objects.filter(
            author=user_profile, is_deleted=False
        ).count(),
        # Social interaction stats (using available models)
        'shares_sent_count': DirectShare.objects.filter(
            sender=user_profile, is_deleted=False
        ).count(),

        # Social network stats
        'followers_count': Follow.objects.filter(
            followed=user_profile, is_deleted=False
        ).count(),
        'following_count': Follow.objects.filter(
            follower=user_profile, is_deleted=False
        ).count(),

        # Placeholder stats for badges that might need them
        'polls_created_count': 0,  # No Poll model found
        'votes_cast_count': 0,     # No Vote model found
        'reposts_count': 0,        # No Repost model found
        'likes_given_count': 0,    # Would need Like model queries
        'likes_received_count': 0,  # Would need Like model queries

        # Time-based stats
        'days_since_joining': (
            timezone.now().date() - user.date_joined.date()
        ).days,
        'active_days_count': 1,  # Placeholder
    }

    return stats


def calculate_badge_progress(badge_definition, user_stats):
    """
    Calculate how close a user is to achieving a specific badge.
    Returns progress percentage (0-100) and remaining requirements.
    """
    criteria = badge_definition.criteria

    if not criteria or criteria.get('type') != 'stat_threshold':
        return {
            'progress_percentage': 0,
            'current_value': 0,
            'required_value': 0,
            'remaining': 0,
            'achievable': False
        }

    stat_field = criteria.get('stat')
    required_value = criteria.get('value', 0)
    current_value = user_stats.get(stat_field, 0)

    progress_percentage = min(
        100, (current_value / required_value) * 100
    ) if required_value > 0 else 0
    remaining = max(0, required_value - current_value)
    achievable = current_value > 0  # User has some activity in this area

    return {
        'progress_percentage': progress_percentage,
        'current_value': current_value,
        'required_value': required_value,
        'remaining': remaining,
        'achievable': achievable,
        'stat_field': stat_field
    }


def get_nearest_achievable_badge(user_profile):
    """
    Find the nearest achievable badge for a user based on their current
    statistics. Returns the badge definition with progress information that
    the user is closest to achieving.
    """
    # Get user's current statistics
    user_stats = get_user_statistics(user_profile)

    # Get badges the user hasn't earned yet
    earned_badge_codes = set(
        UserBadge.objects.filter(
            profile=user_profile,
            is_deleted=False
        ).values_list('badge__code', flat=True)
    )

    available_badges = BadgeDefinition.objects.filter(
        is_active=True,
        is_deleted=False
    ).exclude(
        code__in=earned_badge_codes
    )

    best_candidate = None
    best_score = 0

    for badge in available_badges:
        progress_info = calculate_badge_progress(badge, user_stats)

        # Skip badges where user has no activity in the relevant area
        if not progress_info['achievable']:
            continue

        # Calculate a "closeness score" that considers:
        # 1. Progress percentage (higher is better)
        # 2. Absolute remaining amount (lower is better, but weighted)
        # 3. Badge tier (Bronze badges are easier targets)

        progress_score = progress_info['progress_percentage']

        # Tier weighting (Bronze = easier target)
        tier_weights = {'Bronze': 1.2, 'Silver': 1.0, 'Gold': 0.8}
        tier_weight = tier_weights.get(badge.tier, 1.0)

        # Distance penalty (badges requiring too much more work are less
        # achievable)
        remaining = progress_info['remaining']
        if remaining > 0:
            # Logarithmic penalty for large remaining amounts
            distance_penalty = max(0.1, 1 / (1 + remaining / 10))
        else:
            distance_penalty = 1.0

        # Combined score
        combined_score = progress_score * tier_weight * distance_penalty

        if combined_score > best_score:
            best_score = combined_score
            best_candidate = {
                'badge': badge,
                'progress_info': progress_info,
                'combined_score': combined_score
            }

    return best_candidate


def get_badge_progress_summary(user_profile):
    """
    Get a comprehensive summary of user's badge progress including nearest
    achievable badge.
    """
    # Get earned badges count
    earned_count = UserBadge.objects.filter(
        profile=user_profile,
        is_deleted=False
    ).count()

    # Get total available badges
    total_badges = BadgeDefinition.objects.filter(
        is_active=True,
        is_deleted=False
    ).count()

    # Get nearest achievable badge
    nearest_badge = get_nearest_achievable_badge(user_profile)

    # Get user statistics for context
    user_stats = get_user_statistics(user_profile)

    return {
        'earned_badges_count': earned_count,
        'total_badges_count': total_badges,
        'completion_percentage': (
            (earned_count / total_badges * 100) if total_badges > 0 else 0
        ),
        'nearest_achievable_badge': nearest_badge,
        'user_statistics': user_stats
    }
