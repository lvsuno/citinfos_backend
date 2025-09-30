"""Views for the analytics app with complete CRUD operations."""

import logging
from datetime import timedelta, datetime
from django.db.models import Count, Q, Avg, Max, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from communities.models import Community, CommunityMembership
from analytics.models import (
    DailyAnalytics, UserAnalytics, SystemMetric, ErrorLog, CommunityAnalytics,
    SearchAnalytics, AuthenticationMetric
)
from analytics.serializers import (
    DailyAnalyticsSerializer, UserAnalyticsSerializer,
    UserAnalyticsCreateUpdateSerializer, SystemMetricSerializer,
    SystemMetricCreateUpdateSerializer, ErrorLogSerializer,
    ErrorLogCreateUpdateSerializer
)
from analytics.services import online_tracker
from analytics.signals import track_user_activity

logger = logging.getLogger(__name__)

class DailyAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing daily analytics."""
    serializer_class = DailyAnalyticsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        instance.is_deleted = True
        instance.save()

    def get_queryset(self):
        """Get daily analytics ordered by date."""
        return DailyAnalytics.objects.all().order_by('-date').filter(is_deleted=False)

    @action(detail=False, methods=['get'])
    def date_range(self, request):
        """Get analytics for a specific date range."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            analytics = self.get_queryset().filter(
                date__gte=start_date,
                date__lte=end_date
            )
            serializer = self.get_serializer(analytics, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get trending analytics data."""
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
            start_date = timezone.now().date() - timedelta(days=days)

            analytics = self.get_queryset().filter(date__gte=start_date)

            trends = analytics.aggregate(
                avg_users=Avg('total_users'),
                avg_sessions=Avg('total_sessions'),
                avg_page_views=Avg('total_page_views'),
                avg_session_duration=Avg('avg_session_duration'),
                avg_bounce_rate=Avg('bounce_rate'),
                avg_conversion_rate=Avg('conversion_rate')
            )

            return Response(trends)
        except ValueError:
            return Response(
                {'error': 'days must be a valid integer'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user analytics."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get analytics for the authenticated user."""
        return UserAnalytics.objects.filter(is_deleted=False,
            user=self.request.user.profile
        )

    def get_serializer_class(self):
        """Return the appropriate serializer class."""
        if self.action in ['create', 'update', 'partial_update']:
            return UserAnalyticsCreateUpdateSerializer
        return UserAnalyticsSerializer

    def perform_create(self, serializer):
        """Create analytics with the current user."""
        serializer.save(user=self.request.user.profile)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get user dashboard analytics."""
        try:
            analytics = self.get_queryset().first()
            if not analytics:
                return Response(
                    {'error': 'No analytics data found for user'},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = self.get_serializer(analytics)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def update_engagement(self, request):
        """Update user engagement score."""
        score = request.data.get('engagement_score')
        if score is None:
            return Response(
                {'error': 'engagement_score is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            score = float(score)
            analytics, created = UserAnalytics.objects.get_or_create(
                user=request.user.profile,
                defaults={'engagement_score': score}
            )

            if not created:
                analytics.engagement_score = score
                analytics.save()

            serializer = self.get_serializer(analytics)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'engagement_score must be a valid number'},
                status=status.HTTP_400_BAD_REQUEST
            )


class SystemMetricViewSet(viewsets.ModelViewSet):
    """ViewSet for managing system metrics."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Get all system metrics ordered by recorded at time."""
        return SystemMetric.objects.all().order_by('-recorded_at').filter(is_deleted=False)

    def get_serializer_class(self):
        """Return the appropriate serializer class."""
        if self.action in ['create', 'update', 'partial_update']:
            return SystemMetricCreateUpdateSerializer
        return SystemMetricSerializer

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get metrics filtered by category."""
        category = request.query_params.get('category')
        if not category:
            return Response(
                {'error': 'category parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        metrics = self.get_queryset().filter(metric_category=category)
        serializer = self.get_serializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get metrics filtered by type."""
        metric_type = request.query_params.get('type')
        if not metric_type:
            return Response(
                {'error': 'type parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        metrics = self.get_queryset().filter(metric_type=metric_type)
        serializer = self.get_serializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest metrics for each metric type."""
        latest_metrics = self.get_queryset().values('metric_type').annotate(
            latest_time=Max('recorded_at')
        )

        metric_ids = []
        for metric in latest_metrics:
            latest_metric = self.get_queryset().filter(
                metric_type=metric['metric_type'],
                measurement_time=metric['latest_time']
            ).first()
            if latest_metric:
                metric_ids.append(latest_metric.id)

        latest_metrics_qs = self.get_queryset().filter(id__in=metric_ids)
        serializer = self.get_serializer(latest_metrics_qs, many=True)
        return Response(serializer.data)


class ErrorLogViewSet(viewsets.ModelViewSet):
    """ViewSet for managing error logs."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get error logs for the authenticated user."""
        return ErrorLog.objects.filter(is_deleted=False,
            user=self.request.user.profile
        ).select_related('session').order_by('-timestamp')

    def get_serializer_class(self):
        """Return the appropriate serializer class."""
        if self.action in ['create', 'update', 'partial_update']:
            return ErrorLogCreateUpdateSerializer
        return ErrorLogSerializer

    def perform_create(self, serializer):
        """Create a new error log with the current user."""
        serializer.save(user=self.request.user.profile)

    @action(detail=False, methods=['get'])
    def unresolved(self, request):
        """Get unresolved error logs."""
        errors = self.get_queryset().filter(is_resolved=False)
        serializer = self.get_serializer(errors, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get error logs filtered by type."""
        error_type = request.query_params.get('error_type')
        if not error_type:
            return Response(
                {'error': 'error_type parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        errors = self.get_queryset().filter(error_type=error_type)
        serializer = self.get_serializer(errors, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark an error as resolved."""
        error_log = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')

        error_log.is_resolved = True
        error_log.resolution_notes = resolution_notes
        error_log.save()

        serializer = self.get_serializer(error_log)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get error statistics."""
        errors = self.get_queryset()

        # Date range filtering
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
            start_date = timezone.now() - timedelta(days=days)
            errors = errors.filter(timestamp__gte=start_date)
        except ValueError:
            pass

        stats = errors.aggregate(
            total_errors=Count('id'),
            resolved_errors=Count('id', filter=Q(is_resolved=True)),
            unresolved_errors=Count('id', filter=Q(is_resolved=False))
        )

        # Error type breakdown
        type_breakdown = errors.values('error_type').annotate(
            count=Count('id')
        ).order_by('-count')

        stats['type_breakdown'] = list(type_breakdown)
        stats['resolution_rate'] = (
            stats['resolved_errors'] / stats['total_errors'] * 100
            if stats['total_errors'] > 0 else 0
        )

        return Response(stats)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_community_online_count(request, community_id):
    """Get real-time online member count for a community."""
    try:
        # Verify user has access to this community
        community = get_object_or_404(Community, id=community_id, is_deleted=False)
        membership = CommunityMembership.objects.filter(
            community=community,
            user=request.user.profile,
            status='active',
            is_deleted=False
        ).first()

        if not membership:
            return Response(
                {'error': 'You are not a member of this community'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get real-time data from Redis
        online_count = online_tracker.get_online_count(str(community_id))
        peaks = online_tracker.get_peak_counts(str(community_id))

        # Track user activity
        track_user_activity(
            str(request.user.profile.id),
            str(community_id),
            'view_online_count'
        )

        return Response({
            'community_id': str(community_id),
            'current_online': online_count,
            'peaks': peaks,
            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error("Error getting online count for community %s: %s", community_id, e)
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_community_analytics(request, community_id):
    """Get comprehensive analytics for a community."""
    try:
        # Verify user has access
        community = get_object_or_404(Community, id=community_id, is_deleted=False)
        membership = CommunityMembership.objects.filter(
            community=community,
            user=request.user.profile,
            status='active',
            is_deleted=False
        ).first()

        if not membership:
            return Response(
                {'error': 'You are not a member of this community'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if user can view detailed analytics
        can_view_detailed = membership.can_moderate_posts()

        # Get cached analytics first
        cache_key = f"community_analytics_{community_id}"
        cached_analytics = cache.get(cache_key)

        if not cached_analytics:
            # Get from database
            today = timezone.now().date()
            analytics = CommunityAnalytics.objects.filter(
                community=community,
                date=today
            ).first()

            if not analytics:
                # Create basic analytics if none exist
                analytics = CommunityAnalytics.objects.create(
                    community=community,
                    date=today,
                    current_online_members=0
                )

            # Get real-time data
            current_online = online_tracker.get_online_count(str(community_id))
            peaks = online_tracker.get_peak_counts(str(community_id))

            basic_data = {
                'community_id': str(community_id),
                'community_name': community.name,
                'current_online': current_online,
                'peaks': peaks,
                'total_members': community.members_count,
                'date': today.isoformat(),
                'last_updated': timezone.now().isoformat(),
            }

            if can_view_detailed:
                detailed_data = {
                    **basic_data,
                    'daily_active_members': analytics.daily_active_members,
                    'weekly_active_members': analytics.weekly_active_members,
                    'monthly_active_members': analytics.monthly_active_members,
                    'new_members_today': analytics.new_members_today,
                    'new_members_this_week': analytics.new_members_this_week,
                    'new_members_this_month': analytics.new_members_this_month,
                    'total_posts_today': analytics.total_posts_today,
                    'total_comments_today': analytics.total_comments_today,
                    'total_likes_today': analytics.total_likes_today,
                }
                cached_analytics = detailed_data
            else:
                cached_analytics = basic_data

            # Cache for 30 seconds
            cache.set(cache_key, cached_analytics, 30)

        # Track activity
        track_user_activity(
            str(request.user.profile.id),
            str(community_id),
            'view_analytics'
        )

        return Response(cached_analytics)

    except Exception as e:
        logger.error("Error getting analytics for community %s: %s", community_id, e)
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_community_activity(request, community_id):
    """Track user activity in a community."""
    try:
        # Verify user is a member
        community = get_object_or_404(Community, id=community_id, is_deleted=False)
        membership = CommunityMembership.objects.filter(
            community=community,
            user=request.user.profile,
            status='active',
            is_deleted=False
        ).first()

        if not membership:
            return Response(
                {'error': 'You are not a member of this community'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get activity type from request
        activity_type = request.data.get('activity_type', 'general')

        # Track activity
        current_count = online_tracker.update_user_activity(
            str(request.user.profile.id),
            str(community_id)
        )

        # Send activity signal
        track_user_activity(
            str(request.user.profile.id),
            str(community_id),
            activity_type
        )

        return Response({
            'success': True,
            'current_online': current_count,
            'activity_type': activity_type,
            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error("Error tracking activity for user %s in community %s: %s",
                    request.user.id, community_id, e)
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_communities_status(request):
    """Get online status for all user's communities."""
    try:
        user_id = str(request.user.profile.id)

        # Get user's active memberships
        memberships = CommunityMembership.objects.filter(
            user=request.user.profile,
            status='active',
            is_deleted=False
        ).select_related('community')

        communities_status = []
        for membership in memberships:
            community = membership.community
            online_count = online_tracker.get_online_count(str(community.id))
            is_user_online = online_tracker.is_user_online_in_community(
                user_id,
                str(community.id)
            )

            communities_status.append({
                'community_id': str(community.id),
                'community_name': community.name,
                'online_count': online_count,
                'user_is_online': is_user_online,
                'user_role': membership.role.name if membership.role else membership.legacy_role,
                'total_members': community.members_count,
            })

        return Response({
            'user_id': user_id,
            'communities': communities_status,
            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error("Error getting user communities status: %s", e)
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =============================================================================
# ADMIN ANALYTICS ENDPOINTS
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_overview(request):
    """Get comprehensive overview analytics."""
    try:
        from accounts.models import User
        from content.models import PostSee, Post, Comment, Like
        from analytics.models import (
            DailyAnalytics, UserAnalytics, SystemMetric,
            AuthenticationMetric, CommunityAnalytics, ContentAnalytics
        )
        from django.utils import timezone
        from datetime import timedelta

        # Current counts
        total_users = User.objects.count()
        total_posts = Post.objects.count()
        total_comments = Comment.objects.count() if hasattr(Comment.objects, 'count') else 0
        total_likes = Like.objects.count() if hasattr(Like.objects, 'count') else 0

        # Today's data
        today = timezone.now().date()
        today_start = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )
        today_end = today_start + timedelta(days=1)

        # Active users today (from authentication metrics)
        active_users_today = AuthenticationMetric.objects.filter(
            timestamp__gte=today_start,
            timestamp__lt=today_end,
            success=True,
            user__isnull=False
        ).values('user').distinct().count()

        # New users today
        new_users_today = User.objects.filter(
            date_joined__gte=today_start,
            date_joined__lt=today_end
        ).count()

        # Recent daily analytics
        recent_daily = DailyAnalytics.objects.order_by('-date')[:7]
        daily_analytics = [
            {
                'date': day.date.isoformat(),
                'active_users': day.active_users,
                'new_users': day.new_users,
                'new_posts': day.new_posts,
                'total_users': day.total_users
            }
            for day in recent_daily
        ]

        # User analytics summary
        user_analytics_count = UserAnalytics.objects.count()
        avg_engagement = UserAnalytics.objects.aggregate(
            avg=Avg('engagement_score')
        )['avg'] or 0

        # System metrics
        system_metrics_count = SystemMetric.objects.count()
        recent_system_load = SystemMetric.objects.filter(
            metric_type__icontains='load'
        ).order_by('-recorded_at').first()

        system_load_value = recent_system_load.value if recent_system_load else 0.0

        # Authentication analytics
        auth_metrics_count = AuthenticationMetric.objects.count()
        successful_auths_today = AuthenticationMetric.objects.filter(
            timestamp__gte=today_start,
            timestamp__lt=today_end,
            success=True
        ).count()

        # Community analytics
        community_analytics_count = CommunityAnalytics.objects.count()
        communities_data = CommunityAnalytics.objects.order_by('-daily_active_members')[:5]
        top_communities = [
            {
                'name': ca.community.name if ca.community else 'Unknown',
                'daily_active_members': ca.daily_active_members,
                'total_threads_today': ca.total_threads_today,
                'total_posts_today': ca.total_posts_today,
                'total_comments_today': ca.total_comments_today
            }
            for ca in communities_data
        ]

        # Content analytics
        content_analytics_count = ContentAnalytics.objects.count()
        avg_engagement_rate = ContentAnalytics.objects.aggregate(
            avg=Avg('engagement_rate')
        )['avg'] or 0

        # PostSee analytics
        postsee_count = PostSee.objects.count()
        avg_duration = PostSee.objects.aggregate(
            avg=Avg('view_duration_seconds')
        )['avg'] or 0

        # PostSee 7-day trend for overview chart
        postsee_trend = []
        for i in range(7):
            day_start = today_start - timedelta(days=6-i)
            day_end = day_start + timedelta(days=1)
            day_views = PostSee.objects.filter(
                seen_at__gte=day_start,
                seen_at__lt=day_end
            ).count()
            postsee_trend.append({
                'date': day_start.strftime('%m/%d'),
                'views': day_views
            })

        # PostSee summary stats
        postsee_engaged_views = PostSee.objects.filter(is_engaged=True).count()
        postsee_engagement_rate = (postsee_engaged_views / postsee_count * 100) if postsee_count > 0 else 0

        # Content summary for dashboard
        content_summary = {
            'summary': {
                'total_posts': total_posts,
                'total_comments': total_comments,
                'total_likes': total_likes,
                'total_engagement': total_comments + total_likes,
                'avg_engagement_rate': round(avg_engagement_rate, 2),
                'top_performing_posts': min(total_posts, 5)  # Assume top 5 or total if less
            }
        }

        # Fix duplicate communities in top_communities
        seen_communities = set()
        unique_communities = []
        for community in top_communities:
            if community['name'] not in seen_communities:
                seen_communities.add(community['name'])
                unique_communities.append(community)

        return Response({
            # Current totals
            'total_users': total_users,
            'total_posts': total_posts,
            'total_comments': total_comments,
            'total_likes': total_likes,

            # Today's activity
            'active_users_today': active_users_today,
            'new_users_today': new_users_today,
            'successful_auths_today': successful_auths_today,

            # Analytics data counts
            'analytics_records': {
                'daily_analytics': len(daily_analytics),
                'user_analytics': user_analytics_count,
                'system_metrics': system_metrics_count,
                'auth_metrics': auth_metrics_count,
                'community_analytics': community_analytics_count,
                'content_analytics': content_analytics_count,
                'postsee_views': postsee_count
            },

            # Detailed analytics
            'recent_daily_analytics': daily_analytics,
            'top_communities': unique_communities,

            # Content summary for dashboard
            'contentSummary': content_summary,

            # PostSee trend data for overview chart
            'postsee_trend': postsee_trend,

            # Performance metrics
            'system_load': round(system_load_value, 2),
            'avg_engagement_score': round(avg_engagement, 2),
            'avg_content_engagement_rate': round(avg_engagement_rate, 2),
            'avg_view_duration': round(avg_duration, 2),

            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error("Error in admin_overview: %s", e)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_system_performance(request):
    """Get system performance metrics."""
    try:
        # Get recent system metrics
        system_metrics = SystemMetric.objects.filter(
            recorded_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-recorded_at')[:100]

        # Group by metric type
        metrics_by_type = {}
        for metric in system_metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append({
                'value': metric.value,
                'timestamp': metric.recorded_at.isoformat(),
            })

        # Calculate averages
        performance_summary = {}
        for metric_name, values in metrics_by_type.items():
            avg_value = sum(v['value'] for v in values) / len(values)
            performance_summary[metric_name] = {
                'average': round(avg_value, 2),
                'latest': values[0]['value'] if values else 0,
                'count': len(values),
            }

        return Response({
            'metrics_by_type': metrics_by_type,
            'performance_summary': performance_summary,
            'total_metrics': system_metrics.count(),
            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error("Error in admin_system_performance: %s", e)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_user_behavior(request):
    """Get user behavior analytics."""
    try:
        from accounts.models import User
        from analytics.models import SessionAnalytic

        period = request.GET.get('period', '30d')

        # Parse period
        if period == '7d':
            days = 7
        elif period == '30d':
            days = 30
        else:
            days = 30

        now = timezone.now()
        start_date = now - timedelta(days=days)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)

        # Basic user counts from real data
        total_users = User.objects.count()

        # Active users this week (users who have sessions)
        active_this_week = SessionAnalytic.objects.filter(
            last_activity__gte=week_start
        ).values('user').distinct().count()

        # New users this month
        new_this_month = User.objects.filter(
            date_joined__gte=month_start
        ).count()

        # Create daily aggregates using session data
        daily_data = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            # Sessions created on this day
            day_sessions = SessionAnalytic.objects.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            )

            # Count unique active users for this day
            day_active_users = day_sessions.values('user').distinct().count()

            # Count total sessions created
            day_session_count = day_sessions.count()

            # Calculate average session duration (last_activity - created_at)
            day_durations = []
            for session in day_sessions:
                if session.last_activity and session.created_at:
                    duration_seconds = (
                        session.last_activity - session.created_at
                    ).total_seconds()
                    day_durations.append(duration_seconds)

            avg_duration = (
                sum(day_durations) / len(day_durations)
                if day_durations else 0
            )

            daily_data.append({
                'date': day_start.date().isoformat(),
                'active_users': day_active_users,
                'total_sessions': day_session_count,
                'avg_session_duration': round(avg_duration, 2),
            })

        # Overall summary from session data
        total_sessions = SessionAnalytic.objects.filter(
            created_at__gte=start_date
        ).count()

        total_active_users = SessionAnalytic.objects.filter(
            created_at__gte=start_date
        ).values('user').distinct().count()

        # Calculate overall average session duration
        all_sessions = SessionAnalytic.objects.filter(
            created_at__gte=start_date
        )

        all_durations = []
        for session in all_sessions:
            if session.last_activity and session.created_at:
                duration_seconds = (
                    session.last_activity - session.created_at
                ).total_seconds()
                all_durations.append(duration_seconds)

        overall_avg_duration = (
            sum(all_durations) / len(all_durations)
            if all_durations else 0
        )

        return Response({
            'daily_data': daily_data,
            'summary': {
                'total_active_days': len([
                    d for d in daily_data if d['active_users'] > 0
                ]),
                'total_sessions': total_sessions,
                'avg_session_duration': round(overall_avg_duration, 2),
                'total_active_users': total_active_users,
            },
            # Additional user stats for dashboard
            'total_users': total_users,
            'active_this_week': active_this_week,
            'new_this_month': new_this_month,
            'period': period,
            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error("Error in admin_user_behavior: %s", e)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_authentication(request):
    """Get authentication analytics."""
    try:
        # AuthenticationMetric data
        auth_metrics = AuthenticationMetric.objects.all()

        # Recent login attempts (use `timestamp` field on AuthenticationMetric)
        recent_attempts = auth_metrics.filter(
            timestamp__gte=timezone.now() - timedelta(days=7)
        )

        # Group by success/failure
        success_count = recent_attempts.filter(success=True).count()
        failure_count = recent_attempts.filter(success=False).count()

        # Daily breakdown
        # Group daily using the `timestamp` field (DATE(timestamp))
        daily_auth = recent_attempts.extra(
            select={'day': 'DATE(timestamp)'}
        ).values('day').annotate(
            successful_logins=Count('id', filter=Q(success=True)),
            failed_logins=Count('id', filter=Q(success=False)),
            total_attempts=Count('id'),
        ).order_by('day')

        # Format data
        daily_data = [
            {
                'date': item['day'],
                'successful_logins': item['successful_logins'],
                'failed_logins': item['failed_logins'],
                'total_attempts': item['total_attempts'],
            }
            for item in daily_auth
        ]

        return Response({
            'summary': {
                'total_attempts': auth_metrics.count(),
                'successful_logins': success_count,
                'failed_logins': failure_count,
                'success_rate': round(
                    (success_count / (success_count + failure_count)) * 100, 2
                ) if (success_count + failure_count) > 0 else 0,
            },
            'daily_data': daily_data,
            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error("Error in admin_authentication: %s", e)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_postsee_analytics(request):
    """
    Admin endpoint for PostSee analytics in dashboard format.
    Returns data structure expected by the React dashboard.
    """
    try:
        from content.models import PostSee

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

        # Summary statistics
        summary_data = queryset.aggregate(
            total_views=Count('id'),
            unique_viewers=Count('user', distinct=True),
            unique_posts=Count('post', distinct=True),
            avg_view_duration=Avg('view_duration_seconds'),
            max_view_duration=Max('view_duration_seconds'),
            avg_scroll_percentage=Avg('scroll_percentage'),
            engaged_views=Count('id', filter=Q(is_engaged=True)),
        )

        # Calculate engagement rate
        total_views = summary_data['total_views'] or 0
        engaged_views = summary_data['engaged_views'] or 0
        engagement_rate = (engaged_views / total_views * 100) if total_views > 0 else 0

        # Source breakdown for visualizations
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

        # Hourly distribution for charts
        hourly_data = []
        for hour in range(24):
            hour_views = queryset.filter(seen_at__hour=hour).count()
            hourly_data.append({
                'hour': f"{hour:02d}:00",
                'views': hour_views
            })

        # Format data to match client expectations
        analytics_data = {
            'summary': {
                'total_views': total_views,
                'engaged_views': engaged_views,
                'avg_view_duration': round(summary_data['avg_view_duration'] or 0, 1),
                'unique_viewers': summary_data['unique_viewers'] or 0,
                'unique_posts': summary_data['unique_posts'] or 0,
                'engagement_rate': round(engagement_rate, 2),
                'avg_scroll_percentage': round(summary_data['avg_scroll_percentage'] or 0, 1),
                'bounce_rate': round(100 - engagement_rate, 2)
            },
            'breakdowns': [
                {
                    'name': breakdown['source'],
                    'value': breakdown['count'],
                    'avg_duration': round(breakdown['avg_duration'] or 0, 1),
                    'engagement_rate': round(breakdown['engagement_rate'], 2)
                } for breakdown in source_breakdown
            ],
            'device_breakdown': [
                {
                    'device': breakdown['device_type'],
                    'views': breakdown['count'],
                    'avg_duration': round(breakdown['avg_duration'] or 0, 1),
                    'engagement_rate': round(breakdown['engagement_rate'], 2)
                } for breakdown in device_breakdown
            ],
            'hourly_distribution': hourly_data,
            'period': period,
            'timestamp': timezone.now().isoformat(),
        }

        return Response(analytics_data)

    except Exception as e:
        logger.error("Error in admin_postsee_analytics: %s", e)
        return Response(
            {'error': f'Failed to get PostSee analytics: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_top_content(request):
    """Get top content analytics."""
    try:
        from content.models import PostSee

        limit = int(request.GET.get('limit', 10))
        period = request.GET.get('period', '7d')

        # Parse period
        if period == '7d':
            days = 7
        elif period == '30d':
            days = 30
        else:
            days = 7

        start_date = timezone.now() - timedelta(days=days)

        # Get PostSee data for the period
        postsee_data = PostSee.objects.filter(seen_at__gte=start_date)

        # Group by post and aggregate
        content_stats = postsee_data.values('post_id').annotate(
            view_count=Count('id'),
            total_duration=Sum('view_duration_seconds'),
            avg_duration=Avg('view_duration_seconds'),
            unique_viewers=Count('user', distinct=True),
        ).order_by('-view_count')[:limit]

        # Format data
        top_content = []
        for stat in content_stats:
            top_content.append({
                'post_id': stat['post_id'],
                'content_type': 'post',  # Since PostSee is always for posts
                'view_count': stat['view_count'],
                'total_duration': round(stat['total_duration'] or 0, 2),
                'avg_duration': round(stat['avg_duration'] or 0, 2),
                'unique_viewers': stat['unique_viewers'],
            })

        return Response({
            'top_content': top_content,
            'period': period,
            'limit': limit,
            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error("Error in admin_top_content: %s", e)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_search_trends(request):
    """Get search trends analytics."""
    try:
        period = request.GET.get('period', '7d')

        # Parse period
        if period == '7d':
            days = 7
        elif period == '30d':
            days = 30
        else:
            days = 7

        start_date = timezone.now() - timedelta(days=days)

        # SearchAnalytics data
        search_analytics = SearchAnalytics.objects.filter(
            searched_at__gte=start_date
        )

        # Top search terms
        top_terms = search_analytics.values('query').annotate(
            search_count=Count('id'),
            unique_users=Count('user', distinct=True),
        ).order_by('-search_count')[:20]

        # Daily search volume
        daily_searches = search_analytics.extra(
            select={'day': 'DATE(searched_at)'}
        ).values('day').annotate(
            total_searches=Count('id'),
            unique_users=Count('user', distinct=True),
        ).order_by('day')

        # Format data
        daily_data = [
            {
                'date': item['day'],
                'total_searches': item['total_searches'],
                'unique_users': item['unique_users'],
            }
            for item in daily_searches
        ]

        return Response({
            'top_terms': list(top_terms),
            'daily_data': daily_data,
            'summary': {
                'total_searches': search_analytics.count(),
                'unique_searchers': search_analytics.values(
                    'user'
                ).distinct().count(),
                'avg_searches_per_user': round(
                    search_analytics.count() / max(
                        search_analytics.values('user').distinct().count(), 1
                    ), 2
                ),
            },
            'period': period,
            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error("Error in admin_search_trends: %s", e)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_realtime(request):
    """Get real-time analytics data."""
    try:
        from accounts.models import User

        # Current active users (logged in within last hour)
        current_active = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(hours=1)
        ).count()

        # Recent activity (last 5 minutes)
        recent_activity = UserAnalytics.objects.filter(
            last_calculated__gte=timezone.now() - timedelta(minutes=5)
        ).count()

        # System metrics (latest)
        latest_system_metrics = SystemMetric.objects.order_by(
            '-recorded_at'
        )[:5]

        system_status = []
        for metric in latest_system_metrics:
            system_status.append({
                'metric': metric.metric_type,
                'value': metric.value,
                'timestamp': metric.recorded_at.isoformat(),
            })

        return Response({
            'current_active_users': current_active,
            'recent_activity_count': recent_activity,
            'system_status': system_status,
            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error("Error in admin_realtime: %s", e)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
