"""
PostSee Analytics API Views
Provides comprehensive analytics for post viewing behavior.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg, Sum, Max, Min, Q
from django.utils import timezone
from datetime import timedelta, datetime
from content.models import PostSee, Post
from analytics.models import ContentAnalytics
from analytics.tasks import track_post_view, sync_postsee_analytics
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_post_view_api(request):
    """
    Track a post view and update analytics.

    Expected data:
    {
        "post_id": "uuid",
        "view_duration_seconds": 30,
        "scroll_percentage": 75.5,
        "source": "feed",
        "device_type": "mobile",
        "session_id": "session_key",
        "clicked_links": [],
        "media_viewed": []
    }
    """
    try:
        data = request.data
        user_profile = request.user.profile

        post_id = data.get('post_id')
        if not post_id:
            return Response(
                {'error': 'post_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if post exists
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response(
                {'error': 'Post not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get or create PostSee record
        post_see, created = PostSee.objects.get_or_create(
            user=user_profile,
            post=post,
            defaults={
                'source': data.get('source', 'feed'),
                'device_type': data.get('device_type', 'desktop'),
                'session_id': data.get('session_id', ''),
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )

        # Update view data
        view_duration = data.get('view_duration_seconds', 0)
        scroll_percentage = data.get('scroll_percentage', 0.0)

        if view_duration > 0:
            post_see.update_view_duration(view_duration)

        if scroll_percentage > 0:
            post_see.update_scroll_percentage(scroll_percentage)

        # Handle clicked links
        clicked_links = data.get('clicked_links', [])
        for link in clicked_links:
            post_see.add_clicked_link(link)

        # Handle media viewed
        media_viewed = data.get('media_viewed', [])
        if media_viewed:
            current_media = post_see.media_viewed or []
            post_see.media_viewed = list(set(current_media + media_viewed))
            post_see.save(update_fields=['media_viewed'])

        # Mark as engaged if significant interaction
        if (view_duration > 10 or scroll_percentage > 50 or
            clicked_links or media_viewed):
            post_see.mark_engaged('view_interaction')

        # Trigger analytics update
        post_view_data = {
            'post_see_id': str(post_see.id),
            'post_id': str(post_id),
            'user_id': str(user_profile.id),
            'view_duration_seconds': view_duration,
            'scroll_percentage': scroll_percentage,
            'source': post_see.source,
            'device_type': post_see.device_type,
            'is_engaged': post_see.is_engaged,
            'session_id': post_see.session_id,
            'ip_address': post_see.ip_address,
        }

        # Queue analytics update
        track_post_view.delay(post_view_data)

        return Response({
            'success': True,
            'post_see_id': str(post_see.id),
            'is_new_view': created,
            'is_engaged': post_see.is_engaged,
            'total_views': PostSee.objects.filter(post=post).count()
        })

    except Exception as e:
        logger.error("Error tracking post view: %s", e)
        return Response(
            {'error': 'Failed to track view'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def post_view_analytics(request, post_id=None):
    """
    Get comprehensive analytics for post views.

    Query parameters:
    - period: 'day', 'week', 'month', 'all' (default: 'week')
    - post_id: specific post ID (optional)
    """
    try:
        period = request.GET.get('period', 'week')

        # Calculate date range
        now = timezone.now()
        if period == 'day':
            start_date = now - timedelta(days=1)
        elif period == 'week':
            start_date = now - timedelta(weeks=1)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        else:  # 'all'
            start_date = None

        # Base queryset
        queryset = PostSee.objects.all()
        if start_date:
            queryset = queryset.filter(seen_at__gte=start_date)

        if post_id:
            queryset = queryset.filter(post_id=post_id)

        # Summary statistics
        summary = queryset.aggregate(
            total_views=Count('id'),
            unique_viewers=Count('user', distinct=True),
            unique_posts=Count('post', distinct=True),
            avg_duration=Avg('view_duration_seconds'),
            max_duration=Max('view_duration_seconds'),
            avg_scroll=Avg('scroll_percentage'),
            engaged_views=Count('id', filter=Q(is_engaged=True)),
        )

        # Calculate derived metrics
        total_views = summary['total_views'] or 0
        engaged_views = summary['engaged_views'] or 0
        engagement_rate = (engaged_views / total_views * 100) if total_views > 0 else 0

        # Source breakdown
        source_breakdown = queryset.values('source').annotate(
            count=Count('id'),
            avg_duration=Avg('view_duration_seconds'),
            engagement_rate=Count('id', filter=Q(is_engaged=True)) * 100.0 / Count('id')
        ).order_by('-count')

        # Device breakdown
        device_breakdown = queryset.values('device_type').annotate(
            count=Count('id'),
            avg_duration=Avg('view_duration_seconds'),
            engagement_rate=Count('id', filter=Q(is_engaged=True)) * 100.0 / Count('id')
        ).order_by('-count')

        # Hourly distribution
        hourly_views = []
        for hour in range(24):
            hour_count = queryset.filter(seen_at__hour=hour).count()
            hourly_views.append({'hour': hour, 'views': hour_count})

        # Top posts by engagement (if not filtering by specific post)
        top_posts = []
        if not post_id:
            top_posts = queryset.values('post_id').annotate(
                total_views=Count('id'),
                unique_viewers=Count('user', distinct=True),
                avg_duration=Avg('view_duration_seconds'),
                engagement_rate=Count('id', filter=Q(is_engaged=True)) * 100.0 / Count('id')
            ).order_by('-engagement_rate')[:10]

        return Response({
            'period': period,
            'summary': {
                **summary,
                'engagement_rate': engagement_rate,
                'bounce_rate': 100 - engagement_rate,
            },
            'breakdowns': {
                'source': list(source_breakdown),
                'device': list(device_breakdown),
                'hourly': hourly_views,
            },
            'top_posts': list(top_posts) if not post_id else None,
        })

    except Exception as e:
        logger.error("Error getting post view analytics: %s", e)
        return Response(
            {'error': 'Failed to get analytics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_view_history(request):
    """
    Get the current user's post viewing history and statistics.

    Query parameters:
    - limit: number of recent views to return (default: 50)
    - period: 'day', 'week', 'month', 'all' (default: 'month')
    """
    try:
        user_profile = request.user.profile
        limit = int(request.GET.get('limit', 50))
        period = request.GET.get('period', 'month')

        # Calculate date range
        now = timezone.now()
        if period == 'day':
            start_date = now - timedelta(days=1)
        elif period == 'week':
            start_date = now - timedelta(weeks=1)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        else:  # 'all'
            start_date = None

        # Base queryset
        queryset = PostSee.objects.filter(user=user_profile)
        if start_date:
            queryset = queryset.filter(seen_at__gte=start_date)

        # User statistics
        user_stats = queryset.aggregate(
            total_views=Count('id'),
            unique_posts=Count('post', distinct=True),
            total_time=Sum('view_duration_seconds'),
            avg_duration=Avg('view_duration_seconds'),
            avg_scroll=Avg('scroll_percentage'),
            engaged_views=Count('id', filter=Q(is_engaged=True)),
        )

        # Calculate engagement rate
        total_views = user_stats['total_views'] or 0
        engaged_views = user_stats['engaged_views'] or 0
        engagement_rate = (engaged_views / total_views * 100) if total_views > 0 else 0

        # Recent views with post details
        recent_views = []
        recent_post_sees = queryset.select_related('post').order_by('-seen_at')[:limit]

        for post_see in recent_post_sees:
            recent_views.append({
                'id': str(post_see.id),
                'post_id': str(post_see.post.id),
                'post_title': getattr(post_see.post, 'title', 'Post'),
                'seen_at': post_see.seen_at,
                'view_duration_seconds': post_see.view_duration_seconds,
                'scroll_percentage': post_see.scroll_percentage,
                'source': post_see.source,
                'device_type': post_see.device_type,
                'is_engaged': post_see.is_engaged,
            })

        # Daily activity for the period
        daily_activity = []
        if start_date:
            current_date = start_date.date()
            end_date = now.date()

            while current_date <= end_date:
                day_views = queryset.filter(seen_at__date=current_date).count()
                daily_activity.append({
                    'date': current_date.isoformat(),
                    'views': day_views
                })
                current_date += timedelta(days=1)

        return Response({
            'period': period,
            'user_stats': {
                **user_stats,
                'engagement_rate': engagement_rate,
                'total_time_minutes': (user_stats['total_time'] or 0) / 60,
            },
            'recent_views': recent_views,
            'daily_activity': daily_activity,
        })

    except Exception as e:
        logger.error("Error getting user view history: %s", e)
        return Response(
            {'error': 'Failed to get view history'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_analytics(request):
    """
    Manually trigger analytics synchronization.
    Useful for admin dashboard to ensure latest data.
    """
    try:
        # Trigger sync task
        task = sync_postsee_analytics.delay()

        return Response({
            'success': True,
            'task_id': task.id,
            'message': 'Analytics sync started'
        })

    except Exception as e:
        logger.error("Error triggering analytics sync: %s", e)
        return Response(
            {'error': 'Failed to start sync'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def content_analytics_summary(request):
    """
    Get summary of ContentAnalytics integrated with PostSee data.
    Provides comprehensive view of content performance.
    """
    try:
        period = request.GET.get('period', 'week')

        # Calculate date range
        now = timezone.now()
        if period == 'day':
            start_date = now - timedelta(days=1)
        elif period == 'week':
            start_date = now - timedelta(weeks=1)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        else:  # 'all'
            start_date = None

        # Base queryset for ContentAnalytics
        analytics_queryset = ContentAnalytics.objects.filter(
            content_type='post',
            is_deleted=False
        )
        if start_date:
            analytics_queryset = analytics_queryset.filter(created_at__gte=start_date)

        # Summary from ContentAnalytics
        content_summary = analytics_queryset.aggregate(
            total_posts=Count('id'),
            total_views=Sum('view_count'),
            total_unique_views=Sum('unique_views'),
            avg_engagement_rate=Avg('engagement_rate'),
            avg_quality_score=Avg('quality_score'),
            avg_read_time=Avg('avg_read_time_seconds'),
        )

        # Top performing content
        top_content = analytics_queryset.order_by('-engagement_rate')[:10].values(
            'content_id', 'view_count', 'unique_views', 'engagement_rate',
            'quality_score', 'avg_read_time_seconds'
        )

        # PostSee data for the same period
        postsee_queryset = PostSee.objects.all()
        if start_date:
            postsee_queryset = postsee_queryset.filter(seen_at__gte=start_date)

        postsee_summary = postsee_queryset.aggregate(
            total_detailed_views=Count('id'),
            avg_view_duration=Avg('view_duration_seconds'),
            avg_scroll_depth=Avg('scroll_percentage'),
            total_engaged_views=Count('id', filter=Q(is_engaged=True)),
        )

        # Calculate combined metrics
        total_detailed_views = postsee_summary['total_detailed_views'] or 0
        total_engaged_views = postsee_summary['total_engaged_views'] or 0
        detailed_engagement_rate = (
            (total_engaged_views / total_detailed_views * 100)
            if total_detailed_views > 0 else 0
        )

        return Response({
            'period': period,
            'content_analytics': content_summary,
            'postsee_analytics': {
                **postsee_summary,
                'engagement_rate': detailed_engagement_rate,
            },
            'top_content': list(top_content),
            'integration_health': {
                'analytics_posts': content_summary['total_posts'] or 0,
                'detailed_views_available': total_detailed_views > 0,
                'data_freshness': 'current' if start_date else 'all_time',
            }
        })

    except Exception as e:
        logger.error("Error getting content analytics summary: %s", e)
        return Response(
            {'error': 'Failed to get summary'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
