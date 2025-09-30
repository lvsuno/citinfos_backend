"""
Utilities for user account management and analytics.
"""

import random
import string
from datetime import timedelta
from typing import Any, Dict, List
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db.models import Avg
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import UserProfile, UserBadge, BadgeDefinition
from content.models import Post, Comment


def get_active_profile_or_404(**filters):
    """Return a UserProfile or raise 404 ensuring is_deleted=False.

    Usage: get_active_profile_or_404(id=uuid) or get_active_profile_or_404(user=request.user)
    """
    filters.update({'is_deleted': False})
    return get_object_or_404(UserProfile, **filters)


def get_active_profile(**filters):
    """Return a UserProfile or None ensuring is_deleted=False."""
    filters.update({'is_deleted': False})
    try:
        return UserProfile.objects.get(**filters)
    except UserProfile.DoesNotExist:
        return None


def calculate_content_quality_score(user, days=30):
    """Calculate content quality score based on engagement received."""
    from content.models import Like

    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    # Get user's posts and comments
    posts = Post.objects.filter(
        author=user,
        created_at__gte=start_date,
        created_at__lte=end_date
    )

    comments = Comment.objects.filter(
        author=user,
        created_at__gte=start_date,
        created_at__lte=end_date
    )

    if not posts.exists() and not comments.exists():
        return 0.0

    # Calculate engagement for posts
    post_engagement = 0
    for post in posts:
        likes_count = Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Post),
            object_id=post.id
        ).count()
        comments_count = post.comments.count()
        post_engagement += likes_count + comments_count

    # Calculate engagement for comments
    comment_engagement = 0
    for comment in comments:
        likes_count = Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Comment),
            object_id=comment.id
        ).count()
        comment_engagement += likes_count

    total_engagement = post_engagement + comment_engagement
    total_content = posts.count() + comments.count()

    avg_engagement = (
        total_engagement / total_content if total_content > 0 else 0
    )

    # Normalize to 0-1 scale (assuming max engagement of 100 per content)
    return min(avg_engagement / 100.0, 1.0)


def update_user_analytics():
    """Update user analytics data for all users."""
    from .models import UserSession
    from analytics.models import UserAnalytics

    users = User.objects.all()

    for user in users:
        # Get or create UserProfile for this user
        try:
            user_profile = user.profile
        except:
            continue  # Skip users without profiles

        analytics, created = UserAnalytics.objects.get_or_create(
            user=user_profile
        )

        # Update basic counts
        analytics.total_posts = Post.objects.filter(author=user_profile).count()
        analytics.total_comments = Comment.objects.filter(
            author=user_profile
        ).count()

        # Update engagement metrics
        from .models import UserEvent
        recent_events = UserEvent.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(days=30)
        )

        analytics.total_likes_given = recent_events.filter(
            event_type__in=['post_like', 'comment_like']
        ).count()

        # Update social metrics
        from .models import Follow
        recent_follows = Follow.objects.filter(
            followed=user_profile,
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        analytics.followers_gained = recent_follows.count()

        # Update session metrics
        sessions = UserSession.objects.filter(
            user=user,
            started_at__gte=timezone.now() - timedelta(days=30)
        )
        analytics.total_sessions = sessions.count()

        if sessions.exists():
            avg_duration = sessions.aggregate(
                avg_duration=Avg('time_spent')
            )['avg_duration']
            analytics.avg_session_duration = avg_duration

        analytics.save()


def get_user_recommendations(user_profile, limit=10):
    """
    Get user recommendations for the given user profile.
    Simple implementation based on mutual follows and interests.
    """
    from .models import Follow, UserProfile
    from django.db.models import Count, Q

    # Get users that the current user's followers also follow
    # (collaborative filtering approach)
    followers = Follow.objects.filter(
        followed=user_profile
    ).values_list('follower', flat=True)

    # Find users followed by these followers, excluding current user
    # and users already followed
    followed_by_current = Follow.objects.filter(
        follower=user_profile
    ).values_list('followed', flat=True)

    recommended_users = UserProfile.objects.filter(
        followers__follower__in=followers
    ).exclude(
        Q(id=user_profile.id) | Q(id__in=followed_by_current)
    ).annotate(
        mutual_followers=Count('followers__follower')
    ).order_by('-mutual_followers')[:limit]

    return recommended_users


def calculate_user_activity_score(user_profile, days=7):
    """Calculate recent activity score for a user."""
    from .models import UserEvent

    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    # Count recent events
    recent_events = UserEvent.objects.filter(
        user=user_profile.user,
        created_at__gte=start_date
    ).count()

    # Simple scoring: normalize by expected activity
    # Assuming 5 events per day is high activity
    expected_events = days * 5
    activity_score = min(recent_events / expected_events, 1.0)

    return activity_score


def _compare(a: Any, op: str, b: Any) -> bool:
    try:
        if op == '>=':
            return a >= b
        if op == '>':
            return a > b
        if op == '<=':
            return a <= b
        if op == '<':
            return a < b
        if op == '==':
            return a == b
        if op == '!=':
            return a != b
    except Exception:
        return False
    return False


def _evaluate_criteria_dict(criteria: Dict[str, Any], profile) -> bool:
    if not criteria:
        return False
    ctype = criteria.get('type')

    if ctype in ('and', 'or'):
        conds = criteria.get('conditions', [])
        results = [_evaluate_criteria_dict(cond, profile) for cond in conds]
        return all(results) if ctype == 'and' else any(results)

    if ctype == 'stat_threshold':
        stat = criteria.get('stat')
        op = criteria.get('operator', '>=')
        value = criteria.get('value')
        if not hasattr(profile, stat):
            return False
        return _compare(getattr(profile, stat), op, value)

    if ctype == 'account_age_days':
        days = criteria.get('value', 0)
        age = (timezone.now() - profile.created_at).days
        op = criteria.get('operator', '>=')
        return _compare(age, op, days)

    if ctype == 'follower_threshold':
        value = criteria.get('value', 0)
        op = criteria.get('operator', '>=')
        return _compare(profile.follower_count, op, value)

    return False


def evaluate_badge_criteria_for_profile(badge_definition, profile) -> bool:
    return _evaluate_criteria_dict(badge_definition.criteria or {}, profile)


def evaluate_badges_for_profile(profile) -> int:
    awarded = 0
    active = BadgeDefinition.objects.filter(is_active=True)
    existing = set(UserBadge.objects.filter(profile=profile).values_list('badge_id', flat=True))
    with transaction.atomic():
        for badge in active:
            if badge.id in existing:
                continue
            if evaluate_badge_criteria_for_profile(badge, profile):
                UserBadge.objects.create(profile=profile, badge=badge)
                awarded += 1
                # enqueue notification task here if desired
    return awarded


def evaluate_badges_for_all_profiles(batch_size: int = 500) -> int:
    from accounts.models import UserProfile
    total = 0
    qs = UserProfile.objects.all().order_by('id')
    start = 0
    while True:
        batch = list(qs[start:start+batch_size])
        if not batch:
            break
        for profile in batch:
            total += evaluate_badges_for_profile(profile)
        start += batch_size
    return total


def generate_strong_password(length: int = 12) -> str:
    """
    Generate a strong password that meets our validation requirements:
    - At least 8 characters (default 12)
    - Include uppercase and lowercase letters
    - Include numbers
    - Include special characters (!@#$%^&*)
    """
    if length < 8:
        length = 8

    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = '!@#$%^&*'

    # Ensure at least one character from each required set
    password = [
        random.choice(uppercase),      # At least one uppercase
        random.choice(lowercase),      # At least one lowercase
        random.choice(digits),         # At least one digit
        random.choice(special_chars),  # At least one special char
    ]

    # Fill the rest with random characters from all sets
    all_chars = lowercase + uppercase + digits + special_chars
    for _ in range(length - 4):
        password.append(random.choice(all_chars))

    # Shuffle the password to avoid predictable patterns
    random.shuffle(password)

    return ''.join(password)


def generate_memorable_password() -> str:
    """
    Generate a memorable but strong password using word patterns.
    Format: Word + Numbers + Special + Word
    Example: Blue42!Ocean, Code99#Star
    """
    words = [
        'Blue', 'Green', 'Ocean', 'Mountain', 'River', 'Forest',
        'Eagle', 'Tiger', 'Dragon', 'Phoenix', 'Storm', 'Thunder',
        'Code', 'Tech', 'Cyber', 'Digital', 'Smart', 'Quick',
        'Star', 'Moon', 'Solar', 'Nova', 'Cosmic', 'Galaxy',
        'Fire', 'Ice', 'Wind', 'Earth', 'Light', 'Shadow'
    ]

    special_chars = '!@#$%^&*'

    # Pick two random words
    word1 = random.choice(words)
    word2 = random.choice([w for w in words if w != word1])

    # Generate 2-3 random digits
    numbers = ''.join([
        str(random.randint(0, 9))
        for _ in range(random.randint(2, 3))
    ])

    # Pick a special character
    special = random.choice(special_chars)

    # Combine in a memorable pattern
    return f"{word1}{numbers}{special}{word2}"


def generate_password_suggestions(count: int = 3) -> List[str]:
    """
    Generate multiple password suggestions for the user to choose from.
    """
    suggestions = []

    # Generate one short strong password (8 chars)
    suggestions.append(generate_strong_password(8))

    # Generate one medium strong password (12 chars)
    suggestions.append(generate_strong_password(12))

    # Generate memorable passwords for remaining slots
    for _ in range(count - 2):
        suggestions.append(generate_memorable_password())

    return suggestions


def validate_password_strength(password: str) -> dict:
    """
    Validate password strength and return detailed feedback.
    Returns a dictionary with strength level and requirements met.
    """
    import re

    if not password:
        return {
            'strength': '',
            'score': 0,
            'requirements': {
                'length': False,
                'uppercase': False,
                'lowercase': False,
                'numbers': False,
                'special': False
            }
        }

    requirements = {
        'length': len(password) >= 8,
        'uppercase': bool(re.search(r'[A-Z]', password)),
        'lowercase': bool(re.search(r'[a-z]', password)),
        'numbers': bool(re.search(r'[0-9]', password)),
        'special': bool(re.search(r'[!@#$%^&*]', password))
    }

    # Calculate score (0-5)
    score = sum(requirements.values())

    # Determine strength level
    if len(password) < 6:
        strength = 'Weak'
    elif score >= 5:  # All requirements met
        strength = 'Strong'
    elif len(password) >= 8:
        strength = 'Medium'
    else:
        strength = 'Weak'

    return {
        'strength': strength,
        'score': score,
        'requirements': requirements
    }
