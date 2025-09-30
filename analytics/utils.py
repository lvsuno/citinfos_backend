"""Analytics utility functions for tracking, metrics, and data analysis."""

from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Sum, F
from user_agents import parse

# Import models from different apps
from accounts.models import UserProfile, UserEvent, UserSession
from .models import UserAnalytics, DailyAnalytics, SystemMetric, ErrorLog

User = get_user_model()


def calculate_content_quality_score(user, days=30):
    """Calculate content quality score based on engagement received."""
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    try:
        from content.models import Post, Comment

        # Get user's posts and comments - exclude soft-deleted items
        posts = Post.objects.filter(author=user,
            created_at__gte=start_date,
            created_at__lte=end_date,
            is_deleted=False).annotate(
            engagement=F('likes_count') + F('comments_count') + F('shares_count') + F('repost_count')
        )

        comments = Comment.objects.filter(author=user,
            created_at__gte=start_date,
            created_at__lte=end_date,
            is_deleted=False).annotate(
            engagement=Count('likes') + Count('replies')
        )

        if not posts.exists() and not comments.exists():
            return 0.0

        # Calculate average engagement
        total_engagement = sum(p.engagement for p in posts) + sum(c.engagement for c in comments)
        total_content = posts.count() + comments.count()

        avg_engagement = total_engagement / total_content if total_content > 0 else 0

        # Normalize to 0-1 scale
        return min(avg_engagement / 10.0, 1.0)

    except ImportError:
        # Fallback if content app models not available
        return 0.0


def update_user_analytics():
    """Update user analytics data."""
    users = User.objects.all()

    for user in users:
        try:
            user_profile = UserProfile.objects.get(user=user, is_deleted=False)
        except UserProfile.DoesNotExist:
            continue

        analytics, created = UserAnalytics.objects.get_or_create(user=user_profile)

        try:
            from content.models import Post, Comment
            from communities.models import Follow

            # Update basic counts - exclude soft-deleted items
            analytics.total_posts = Post.objects.filter(author=user, is_deleted=False).count()
            analytics.total_comments = Comment.objects.filter(author=user, is_deleted=False).count()

            # Update engagement metrics
            recent_events = UserEvent.objects.filter(user=user,
                created_at__gte=timezone.now() - timedelta(days=30), is_deleted=False
            )

            analytics.total_likes_given = recent_events.filter(
                event_type__in=['post_like', 'comment_like']
            ).count()

            # Update social metrics
            recent_follows = Follow.objects.filter(following=user_profile,
                created_at__gte=timezone.now() - timedelta(days=30), is_deleted=False
            )
            analytics.followers_gained = recent_follows.count()

        except ImportError:
            # Set defaults if models not available
            analytics.total_posts = 0
            analytics.total_comments = 0
            analytics.total_likes_given = 0
            analytics.followers_gained = 0

        # Update session metrics
        sessions = UserSession.objects.filter(user=user,
            started_at__gte=timezone.now() - timedelta(days=30), is_deleted=False
        )
        analytics.total_sessions = sessions.count()

        if sessions.exists():
            avg_duration = sessions.aggregate(
                avg_duration=Avg('time_spent')
            )['avg_duration']
            analytics.avg_session_duration = avg_duration or timedelta(0)

        analytics.save()


def generate_daily_analytics():
    """Generate daily analytics summary."""
    yesterday = timezone.now().date() - timedelta(days=1)

    # Check if already generated
    if DailyAnalytics.objects.filter(date=yesterday, is_deleted=False).exists():
        return

    # User metrics
    new_users = User.objects.filter(date_joined__date=yesterday).count()
    total_users = User.objects.count()

    # Active users (users with events yesterday)
    active_users = UserEvent.objects.filter(created_at__date=yesterday, is_deleted=False).values('user').distinct().count()

    # Get daily events
    daily_events = UserEvent.objects.filter(created_at__date=yesterday, is_deleted=False)

    # Content metrics
    new_posts = daily_events.filter(event_type='post_create').count()
    new_comments = daily_events.filter(event_type='comment_create').count()
    total_likes = daily_events.filter(event_type__in=['post_like', 'comment_like']).count()
    total_shares = daily_events.filter(event_type='post_share').count()  # legacy event; consider splitting direct/repost

    # Engagement metrics
    total_interactions = daily_events.count()

    # System metrics
    system_metrics = SystemMetric.objects.filter(
        recorded_at__date=yesterday
    )

    avg_response_time = system_metrics.filter(
        metric_type='response_time'
    ).aggregate(avg=Avg('value'))['avg'] or 0.0

    error_count = system_metrics.filter(
        metric_type='error_rate'
    ).aggregate(total=Sum('value'))['total'] or 0

    # Create daily analytics record
    DailyAnalytics.objects.create(
        date=yesterday,
        new_users=new_users,
        active_users=active_users,
        total_users=total_users,
        new_posts=new_posts,
        new_comments=new_comments,
        total_likes=total_likes,
        total_shares=total_shares,
        total_interactions=total_interactions,
        avg_response_time=avg_response_time,
        error_count=error_count,
    )


def clean_expired_analytics_data():
    """Clean up expired analytics data to maintain performance."""
    # Clean old metrics (keep only last 90 days)
    cutoff_date = timezone.now() - timedelta(days=90)

    SystemMetric.objects.filter(recorded_at__lt=cutoff_date).delete()
    ErrorLog.objects.filter(
        created_at__lt=cutoff_date,
        is_resolved=True
    ).delete()

    # Clean old daily analytics (keep only last 1 year)
    analytics_cutoff = timezone.now().date() - timedelta(days=365)
    DailyAnalytics.objects.filter(date__lt=analytics_cutoff, is_deleted=False).delete()


def record_system_metric(metric_type, value, metadata=None):
    """Record a system metric for monitoring."""
    if metadata is None:
        metadata = {}

    SystemMetric.objects.create(
        metric_type=metric_type,
        value=value,
        additional_data=metadata
    )


def record_error(user=None, level='error', message='', stack_trace='',
                 url='', method='', ip_address='', extra_data=None):
    """Record an error for tracking and analysis."""
    if extra_data is None:
        extra_data = {}

    user_profile = None
    if user:
        try:
            user_profile = UserProfile.objects.get(user=user, is_deleted=False)
        except UserProfile.DoesNotExist:
            pass

    ErrorLog.objects.create(
        user=user_profile,
        level=level,
        message=message,
        stack_trace=stack_trace,
        url=url,
        method=method,
        ip_address=ip_address,
        extra_data=extra_data
    )


def get_analytics_summary(days=30):
    """Get analytics summary for the specified number of days."""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    # Get daily analytics for the period
    daily_analytics = DailyAnalytics.objects.filter(date__gte=start_date,
        date__lte=end_date, is_deleted=False)

    if not daily_analytics.exists():
        return {
            'total_users': 0,
            'new_users': 0,
            'active_users': 0,
            'total_posts': 0,
            'total_comments': 0,
            'total_interactions': 0,
            'avg_response_time': 0.0,
            'error_count': 0,
        }

    # Aggregate the data
    summary = daily_analytics.aggregate(
        total_users=Sum('total_users'),
        new_users=Sum('new_users'),
        active_users=Sum('active_users'),
        total_posts=Sum('new_posts'),
        total_comments=Sum('new_comments'),
        total_interactions=Sum('total_interactions'),
        avg_response_time=Avg('avg_response_time'),
        error_count=Sum('error_count'),
    )

    # Get latest total users count
    latest_analytics = daily_analytics.order_by('-date').first()
    if latest_analytics:
        summary['total_users'] = latest_analytics.total_users

    return summary
