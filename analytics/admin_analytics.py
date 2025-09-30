"""
Comprehensive admin analytics endpoints for the analytics dashboard.
Utilizes all analytics models: ContentAnalytics,  SearchAnalytics,
DailyAnalytics, UserAnalytics, SystemMetric, ErrorLog, AuthenticationMetric,
AuthenticationReport, SessionAnalytic, CommunityAnalytics, UserEvent, and PostSee.
"""

import logging
from datetime import timedelta, datetime
from django.db.models import Count, Q, Avg, Max, Min, Sum, F
from django.utils import timezone
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from analytics.models import (
    ContentAnalytics,  SearchAnalytics,
    DailyAnalytics, UserAnalytics, SystemMetric, ErrorLog,
    AuthenticationMetric, AuthenticationReport, SessionAnalytic,
    CommunityAnalytics
)
from accounts.models import UserEvent
from content.models import PostSee

logger = logging.getLogger(__name__)


def get_period_filter(period='7d'):
    """Get date filter for the specified period."""
    now = timezone.now()

    if period == '1h':
        start_date = now - timedelta(hours=1)
    elif period == '24h':
        start_date = now - timedelta(hours=24)
    elif period == '7d':
        start_date = now - timedelta(days=7)
    elif period == '30d':
        start_date = now - timedelta(days=30)
    elif period == '90d':
        start_date = now - timedelta(days=90)
    elif period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=7)

    return start_date


class AdminRealtimeAnalytics(View):
    """Real-time analytics overview for admin dashboard."""

    def get(self, request):
        try:
            now = timezone.now()
            last_hour = now - timedelta(hours=1)

            # Real-time metrics from the last hour
            data = {
                'timestamp': now.isoformat(),
                'period': 'last_hour',

                # User activity (from UserEvent)
                'active_users_last_hour': UserEvent.objects.filter(
                    created_at__gte=last_hour,
                    is_deleted=False
                ).values('user').distinct().count(),

                # Post views (from PostSee)
                'post_views_last_hour': PostSee.objects.filter(
                    seen_at__gte=last_hour
                ).count(),

                # Authentication activity (from AuthenticationMetric)
                'auth_attempts_last_hour': AuthenticationMetric.objects.filter(
                    timestamp__gte=last_hour,
                    is_deleted=False
                ).count(),

                'auth_success_rate_last_hour': self._calculate_auth_success_rate(last_hour),

                # Errors (from ErrorLog)
                'errors_last_hour': ErrorLog.objects.filter(
                    created_at__gte=last_hour,
                    is_deleted=False
                ).count(),

                # System performance (from SystemMetric)
                'avg_response_time_last_hour': self._get_avg_response_time(last_hour),

                # Search activity (from SearchAnalytics)
                'searches_last_hour': SearchAnalytics.objects.filter(
                    searched_at__gte=last_hour,
                    is_deleted=False
                ).count(),

                # Community activity (from CommunityAnalytics)
                'communities_active_last_hour': CommunityAnalytics.objects.filter(
                    last_updated__gte=last_hour,
                    is_deleted=False
                ).count(),
            }

            return JsonResponse(data)

        except Exception as e:
            logger.error(f"Error in AdminRealtimeAnalytics: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)

    def _calculate_auth_success_rate(self, since):
        """Calculate authentication success rate."""
        total = AuthenticationMetric.objects.filter(
            timestamp__gte=since,
            is_deleted=False
        ).count()

        if total == 0:
            return 100.0

        successful = AuthenticationMetric.objects.filter(
            timestamp__gte=since,
            success=True,
            is_deleted=False
        ).count()

        return round((successful / total) * 100, 2)

    def _get_avg_response_time(self, since):
        """Get average response time from system metrics."""
        avg_time = SystemMetric.objects.filter(
            recorded_at__gte=since,
            metric_type='response_time',
            is_deleted=False
        ).aggregate(avg_time=Avg('value'))['avg_time']

        return round(avg_time or 0, 2)


class AdminSystemPerformance(View):
    """System performance analytics."""

    def get(self, request):
        try:
            period = request.GET.get('period', '24h')
            start_date = get_period_filter(period)

            # System metrics
            system_metrics = SystemMetric.objects.filter(
                recorded_at__gte=start_date,
                is_deleted=False
            )

            # Performance by metric type
            performance_data = {}
            for metric_type in ['response_time', 'cpu_usage', 'memory_usage', 'database_query_time']:
                metrics = system_metrics.filter(metric_type=metric_type)
                performance_data[metric_type] = {
                    'current': metrics.latest('recorded_at').value if metrics.exists() else 0,
                    'average': round(metrics.aggregate(avg=Avg('value'))['avg'] or 0, 2),
                    'max': metrics.aggregate(max=Max('value'))['max'] or 0,
                    'min': metrics.aggregate(min=Min('value'))['min'] or 0,
                    'count': metrics.count()
                }

            # Error rate calculation
            total_requests = system_metrics.filter(
                metric_type='response_time'
            ).count()

            total_errors = ErrorLog.objects.filter(
                created_at__gte=start_date,
                level__in=['error', 'critical'],
                is_deleted=False
            ).count()

            error_rate = round((total_errors / total_requests * 100) if total_requests > 0 else 0, 2)

            # Authentication performance
            auth_performance = AuthenticationMetric.objects.filter(
                timestamp__gte=start_date,
                is_deleted=False
            ).aggregate(
                avg_total_time=Avg('total_auth_time'),
                avg_jwt_time=Avg('jwt_validation_time'),
                avg_session_time=Avg('session_lookup_time')
            )

            data = {
                'period': period,
                'system_performance': performance_data,
                'error_rate': error_rate,
                'total_requests': total_requests,
                'total_errors': total_errors,
                'authentication_performance': {
                    'avg_total_auth_time': round(auth_performance['avg_total_time'] or 0, 2),
                    'avg_jwt_validation_time': round(auth_performance['avg_jwt_time'] or 0, 2),
                    'avg_session_lookup_time': round(auth_performance['avg_session_time'] or 0, 2)
                },
                'timestamp': timezone.now().isoformat()
            }

            return JsonResponse(data)

        except Exception as e:
            logger.error(f"Error in AdminSystemPerformance: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class AdminTopContent(View):
    """Top performing content analytics."""

    def get(self, request):
        try:
            period = request.GET.get('period', '7d')
            limit = int(request.GET.get('limit', 10))
            start_date = get_period_filter(period)

            # Top posts by views (from PostSee)
            top_posts_by_views = PostSee.objects.filter(
                seen_at__gte=start_date
            ).values('post_id').annotate(
                total_views=Count('id'),
                unique_viewers=Count('user', distinct=True),
                avg_duration=Avg('view_duration_seconds'),
                avg_scroll=Avg('scroll_percentage'),
                engagement_rate=Count('id', filter=Q(is_engaged=True)) * 100.0 / Count('id')
            ).order_by('-total_views')[:limit]

            # Top content by engagement (from ContentAnalytics)
            top_content_by_engagement = ContentAnalytics.objects.filter(
                last_updated__gte=start_date,
                is_deleted=False
            ).order_by('-engagement_rate')[:limit].values(
                'content_id', 'content_type', 'view_count', 'engagement_rate',
                'like_count', 'comment_count', 'share_count', 'quality_score'
            )

            # Search trends (from SearchAnalytics)
            trending_searches = SearchAnalytics.objects.filter(
                searched_at__gte=start_date,
                is_deleted=False
            ).values('normalized_query').annotate(
                search_count=Count('id'),
                avg_results=Avg('total_results'),
                avg_ctr=Avg('click_through_rate')
            ).order_by('-search_count')[:limit]

            data = {
                'period': period,
                'top_posts_by_views': list(top_posts_by_views),
                'top_content_by_engagement': list(top_content_by_engagement),
                'trending_searches': list(trending_searches),
                'timestamp': timezone.now().isoformat()
            }

            return JsonResponse(data)

        except Exception as e:
            logger.error(f"Error in AdminTopContent: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class AdminUserBehavior(View):
    """User behavior analytics."""

    def get(self, request):
        try:
            period = request.GET.get('period', '30d')
            start_date = get_period_filter(period)

            # User activity patterns (from UserEvent)
            user_events = UserEvent.objects.filter(
                created_at__gte=start_date,
                is_deleted=False
            )

            # Event type distribution
            event_distribution = user_events.values('event_type').annotate(
                count=Count('id')
            ).order_by('-count')[:10]

            # User engagement levels (from UserAnalytics)
            engagement_distribution = UserAnalytics.objects.filter(
                last_calculated__gte=start_date,
                is_deleted=False
            ).values('activity_level').annotate(
                count=Count('id')
            )

            # Session patterns (from SessionAnalytic)
            session_patterns = SessionAnalytic.objects.filter(
                created_at__gte=start_date,
                is_deleted=False
            ).aggregate(
                avg_session_duration=Avg(F('ended_at') - F('created_at')),
                total_sessions=Count('id'),
                avg_renewals=Avg('renewal_count'),
                avg_lookups=Avg('lookup_count')
            )

            # User retention analysis
            user_analytics = UserAnalytics.objects.filter(
                last_calculated__gte=start_date,
                is_deleted=False
            )

            retention_metrics = user_analytics.aggregate(
                avg_retention_score=Avg('retention_score'),
                avg_churn_risk=Avg('churn_risk_score'),
                high_risk_users=Count('id', filter=Q(churn_risk_score__gt=70))
            )

            # Platform preferences
            platform_usage = user_analytics.aggregate(
                total_mobile_sessions=Sum('mobile_sessions'),
                total_desktop_sessions=Sum('desktop_sessions'),
                total_tablet_sessions=Sum('tablet_sessions')
            )

            total_sessions = sum(platform_usage.values())
            platform_percentages = {}
            if total_sessions > 0:
                platform_percentages = {
                    'mobile': round((platform_usage['total_mobile_sessions'] or 0) / total_sessions * 100, 1),
                    'desktop': round((platform_usage['total_desktop_sessions'] or 0) / total_sessions * 100, 1),
                    'tablet': round((platform_usage['total_tablet_sessions'] or 0) / total_sessions * 100, 1)
                }

            data = {
                'period': period,
                'event_distribution': list(event_distribution),
                'engagement_distribution': list(engagement_distribution),
                'session_patterns': {
                    'avg_session_duration_seconds': session_patterns['avg_session_duration'].total_seconds() if session_patterns['avg_session_duration'] else 0,
                    'total_sessions': session_patterns['total_sessions'],
                    'avg_renewals_per_session': round(session_patterns['avg_renewals'] or 0, 2),
                    'avg_lookups_per_session': round(session_patterns['avg_lookups'] or 0, 2)
                },
                'retention_metrics': {
                    'avg_retention_score': round(retention_metrics['avg_retention_score'] or 0, 2),
                    'avg_churn_risk_score': round(retention_metrics['avg_churn_risk'] or 0, 2),
                    'high_risk_users_count': retention_metrics['high_risk_users']
                },
                'platform_usage': platform_percentages,
                'timestamp': timezone.now().isoformat()
            }

            return JsonResponse(data)

        except Exception as e:
            logger.error(f"Error in AdminUserBehavior: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class AdminSearchTrends(View):
    """Search analytics and trends."""

    def get(self, request):
        try:
            period = request.GET.get('period', '7d')
            start_date = get_period_filter(period)

            searches = SearchAnalytics.objects.filter(
                searched_at__gte=start_date,
                is_deleted=False
            )

            # Search volume trends
            search_trends = searches.values('normalized_query').annotate(
                search_count=Count('id'),
                avg_results=Avg('total_results'),
                avg_ctr=Avg('click_through_rate'),
                success_rate=Count('id', filter=Q(resulted_in_action=True)) * 100.0 / Count('id')
            ).order_by('-search_count')[:20]

            # Search type distribution
            search_types = searches.values('search_type').annotate(
                count=Count('id'),
                avg_results=Avg('total_results'),
                avg_ctr=Avg('click_through_rate')
            ).order_by('-count')

            # Performance metrics
            performance_metrics = searches.aggregate(
                avg_search_time=Avg('search_time_ms'),
                avg_db_time=Avg('database_query_time_ms'),
                zero_results_rate=Count('id', filter=Q(zero_results=True)) * 100.0 / Count('id'),
                total_searches=Count('id')
            )

            # Popular filters and sorting
            filter_usage = searches.exclude(
                filters_applied={}
            ).values('search_type').annotate(
                filter_usage_rate=Count('id') * 100.0 / Count('id', filter=Q(search_type=F('search_type')))
            )

            # Time patterns (hourly distribution)
            hourly_distribution = searches.extra(
                select={'hour': 'EXTRACT(hour FROM searched_at)'}
            ).values('hour').annotate(
                search_count=Count('id')
            ).order_by('hour')

            data = {
                'period': period,
                'trending_queries': list(search_trends),
                'search_type_distribution': list(search_types),
                'performance_metrics': {
                    'avg_search_time_ms': round(performance_metrics['avg_search_time'] or 0, 2),
                    'avg_database_time_ms': round(performance_metrics['avg_db_time'] or 0, 2),
                    'zero_results_rate': round(performance_metrics['zero_results_rate'] or 0, 2),
                    'total_searches': performance_metrics['total_searches']
                },
                'filter_usage': list(filter_usage),
                'hourly_distribution': list(hourly_distribution),
                'timestamp': timezone.now().isoformat()
            }

            return JsonResponse(data)

        except Exception as e:
            logger.error(f"Error in AdminSearchTrends: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class AdminAuthenticationAnalytics(View):
    """Authentication performance and security analytics."""

    def get(self, request):
        try:
            period = request.GET.get('period', '24h')
            start_date = get_period_filter(period)

            # Authentication metrics
            auth_metrics = AuthenticationMetric.objects.filter(
                timestamp__gte=start_date,
                is_deleted=False
            )

            # Method distribution
            method_distribution = auth_metrics.values('auth_method').annotate(
                count=Count('id'),
                success_rate=Count('id', filter=Q(success=True)) * 100.0 / Count('id'),
                avg_time=Avg('total_auth_time')
            ).order_by('-count')

            # Performance grades
            performance_grades = {}
            for metric in auth_metrics:
                grade = metric.performance_grade
                performance_grades[grade] = performance_grades.get(grade, 0) + 1

            # JWT optimization metrics
            jwt_metrics = auth_metrics.filter(auth_method__startswith='jwt')
            jwt_optimization = jwt_metrics.aggregate(
                total_jwt_auths=Count('id'),
                avg_jwt_validation_time=Avg('jwt_validation_time'),
                jwt_renewal_rate=Count('id', filter=Q(jwt_renewed=True)) * 100.0 / Count('id'),
                avg_token_age=Avg('token_age_seconds')
            )

            # Security events from UserEvent
            security_events = UserEvent.objects.filter(
                created_at__gte=start_date,
                event_type__startswith='security_',
                is_deleted=False
            ).values('event_type').annotate(
                count=Count('id')
            ).order_by('-count')

            # Session analytics
            session_analytics = SessionAnalytic.objects.filter(
                created_at__gte=start_date,
                is_deleted=False
            ).aggregate(
                avg_session_duration=Avg(F('ended_at') - F('created_at')),
                total_sessions=Count('id'),
                avg_efficiency_score=Avg('efficiency_score'),
                smart_renewals_total=Sum('smart_renewals')
            )

            # Error analysis
            auth_errors = ErrorLog.objects.filter(
                created_at__gte=start_date,
                level__in=['error', 'critical'],
                message__icontains='auth',
                is_deleted=False
            ).count()

            data = {
                'period': period,
                'method_distribution': list(method_distribution),
                'performance_grades': performance_grades,
                'jwt_optimization': {
                    'total_jwt_authentications': jwt_optimization['total_jwt_auths'],
                    'avg_jwt_validation_time_ms': round(jwt_optimization['avg_jwt_validation_time'] or 0, 2),
                    'jwt_renewal_rate': round(jwt_optimization['jwt_renewal_rate'] or 0, 2),
                    'avg_token_age_seconds': round(jwt_optimization['avg_token_age'] or 0, 2)
                },
                'security_events': list(security_events),
                'session_analytics': {
                    'avg_session_duration_seconds': session_analytics['avg_session_duration'].total_seconds() if session_analytics['avg_session_duration'] else 0,
                    'total_sessions': session_analytics['total_sessions'],
                    'avg_efficiency_score': round(session_analytics['avg_efficiency_score'] or 0, 2),
                    'smart_renewals_total': session_analytics['smart_renewals_total'] or 0
                },
                'authentication_errors': auth_errors,
                'timestamp': timezone.now().isoformat()
            }

            return JsonResponse(data)

        except Exception as e:
            logger.error(f"Error in AdminAuthenticationAnalytics: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


# API endpoint decorators for REST framework compatibility
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_realtime_analytics(request):
    """REST API wrapper for realtime analytics."""
    view = AdminRealtimeAnalytics()
    response = view.get(request)
    return Response(response.content)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_system_performance(request):
    """REST API wrapper for system performance."""
    view = AdminSystemPerformance()
    response = view.get(request)
    if hasattr(response, 'content'):
        import json
        return Response(json.loads(response.content))
    return Response(response)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_top_content(request):
    """REST API wrapper for top content."""
    view = AdminTopContent()
    response = view.get(request)
    if hasattr(response, 'content'):
        import json
        return Response(json.loads(response.content))
    return Response(response)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_user_behavior(request):
    """REST API wrapper for user behavior."""
    view = AdminUserBehavior()
    response = view.get(request)
    if hasattr(response, 'content'):
        import json
        return Response(json.loads(response.content))
    return Response(response)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_search_trends(request):
    """REST API wrapper for search trends."""
    view = AdminSearchTrends()
    response = view.get(request)
    if hasattr(response, 'content'):
        import json
        return Response(json.loads(response.content))
    return Response(response)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_authentication_analytics(request):
    """REST API wrapper for authentication analytics."""
    view = AdminAuthenticationAnalytics()
    response = view.get(request)
    if hasattr(response, 'content'):
        import json
        return Response(json.loads(response.content))
    return Response(response)


class AdminOverview(View):
    """Overview analytics combining all major metrics."""

    def get(self, request):
        try:
            period = request.GET.get('period', '7d')
            start_date = get_period_filter(period)

            # Key performance indicators
            kpis = {
                # User metrics
                'total_users': UserEvent.objects.filter(
                    created_at__gte=start_date,
                    is_deleted=False
                ).values('user').distinct().count(),

                # Content metrics
                'total_content_views': PostSee.objects.filter(
                    seen_at__gte=start_date
                ).count(),

                'avg_engagement_rate': ContentAnalytics.objects.filter(
                    last_updated__gte=start_date,
                    is_deleted=False
                ).aggregate(avg=Avg('engagement_rate'))['avg'] or 0,

                # Search metrics
                'total_searches': SearchAnalytics.objects.filter(
                    searched_at__gte=start_date,
                    is_deleted=False
                ).count(),

                # System metrics
                'avg_response_time': SystemMetric.objects.filter(
                    recorded_at__gte=start_date,
                    metric_type='response_time',
                    is_deleted=False
                ).aggregate(avg=Avg('value'))['avg'] or 0,

                'error_count': ErrorLog.objects.filter(
                    created_at__gte=start_date,
                    level__in=['error', 'critical'],
                    is_deleted=False
                ).count(),
            }

            # Community analytics
            community_stats = CommunityAnalytics.objects.filter(
                last_updated__gte=start_date,
                is_deleted=False
            ).aggregate(
                total_communities=Count('id'),
                avg_member_count=Avg('total_members'),
                avg_activity_score=Avg('activity_score')
            )

            # Daily trends
            daily_trends = DailyAnalytics.objects.filter(
                date__gte=start_date.date(),
                is_deleted=False
            ).order_by('date').values(
                'date', 'total_users', 'total_sessions', 'bounce_rate',
                'avg_session_duration', 'page_views'
            )

            data = {
                'period': period,
                'kpis': kpis,
                'community_stats': community_stats,
                'daily_trends': list(daily_trends),
                'timestamp': timezone.now().isoformat()
            }

            return JsonResponse(data)

        except Exception as e:
            logger.error(f"Error in AdminOverview: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class AdminContentAnalytics(View):
    """Detailed content performance analytics."""

    def get(self, request):
        try:
            period = request.GET.get('period', '7d')
            start_date = get_period_filter(period)

            # Content performance (from ContentAnalytics)
            content_performance = ContentAnalytics.objects.filter(
                last_updated__gte=start_date,
                is_deleted=False
            ).aggregate(
                total_content=Count('id'),
                avg_views=Avg('view_count'),
                avg_engagement=Avg('engagement_rate'),
                avg_likes=Avg('like_count'),
                avg_comments=Avg('comment_count'),
                avg_shares=Avg('share_count'),
                avg_quality=Avg('quality_score')
            )

            # Content type distribution
            content_types = ContentAnalytics.objects.filter(
                last_updated__gte=start_date,
                is_deleted=False
            ).values('content_type').annotate(
                count=Count('id'),
                avg_engagement=Avg('engagement_rate'),
                total_views=Sum('view_count')
            ).order_by('-count')

            # Post view analytics (from PostSee)
            post_analytics = PostSee.objects.filter(
                seen_at__gte=start_date
            ).aggregate(
                total_views=Count('id'),
                unique_viewers=Count('user', distinct=True),
                avg_duration=Avg('view_duration_seconds'),
                avg_scroll=Avg('scroll_percentage'),
                engagement_rate=Count('id', filter=Q(is_engaged=True)) * 100.0 / Count('id')
            )

            # Top performing content
            top_content = ContentAnalytics.objects.filter(
                last_updated__gte=start_date,
                is_deleted=False
            ).order_by('-engagement_rate')[:10].values(
                'content_id', 'content_type', 'view_count', 'engagement_rate',
                'like_count', 'comment_count', 'share_count', 'quality_score'
            )

            # Content quality distribution
            quality_ranges = [
                (0, 20, 'Poor'),
                (20, 40, 'Fair'),
                (40, 60, 'Good'),
                (60, 80, 'Very Good'),
                (80, 100, 'Excellent')
            ]

            quality_distribution = []
            for min_score, max_score, label in quality_ranges:
                count = ContentAnalytics.objects.filter(
                    last_updated__gte=start_date,
                    quality_score__gte=min_score,
                    quality_score__lt=max_score,
                    is_deleted=False
                ).count()
                quality_distribution.append({
                    'range': label,
                    'count': count,
                    'min_score': min_score,
                    'max_score': max_score
                })

            data = {
                'period': period,
                'content_performance': content_performance,
                'content_types': list(content_types),
                'post_analytics': post_analytics,
                'top_content': list(top_content),
                'quality_distribution': quality_distribution,
                'timestamp': timezone.now().isoformat()
            }

            return JsonResponse(data)

        except Exception as e:
            logger.error(f"Error in AdminContentAnalytics: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class AdminSearchAnalytics(View):
    """Detailed search analytics."""

    def get(self, request):
        try:
            period = request.GET.get('period', '7d')
            start_date = get_period_filter(period)

            searches = SearchAnalytics.objects.filter(
                searched_at__gte=start_date,
                is_deleted=False
            )

            # Search overview
            search_overview = searches.aggregate(
                total_searches=Count('id'),
                avg_results=Avg('total_results'),
                avg_search_time=Avg('search_time_ms'),
                zero_results_rate=Count('id', filter=Q(zero_results=True)) * 100.0 / Count('id'),
                avg_ctr=Avg('click_through_rate'),
                conversion_rate=Count('id', filter=Q(resulted_in_action=True)) * 100.0 / Count('id')
            )

            # Search type breakdown
            search_types = searches.values('search_type').annotate(
                count=Count('id'),
                avg_results=Avg('total_results'),
                avg_ctr=Avg('click_through_rate'),
                success_rate=Count('id', filter=Q(resulted_in_action=True)) * 100.0 / Count('id')
            ).order_by('-count')

            # Popular queries
            popular_queries = searches.values('normalized_query').annotate(
                search_count=Count('id'),
                avg_results=Avg('total_results'),
                avg_ctr=Avg('click_through_rate')
            ).order_by('-search_count')[:20]

            # Query performance analysis
            query_performance = searches.values('normalized_query').annotate(
                search_count=Count('id'),
                avg_time=Avg('search_time_ms'),
                zero_results_rate=Count('id', filter=Q(zero_results=True)) * 100.0 / Count('id')
            ).order_by('-search_count')[:10]

            # Search filters usage
            filter_stats = {}
            for search in searches.exclude(filters_applied={}):
                for filter_key in search.filters_applied.keys():
                    filter_stats[filter_key] = filter_stats.get(filter_key, 0) + 1

            filter_usage = [
                {'filter': k, 'usage_count': v}
                for k, v in sorted(filter_stats.items(), key=lambda x: x[1], reverse=True)[:10]
            ]

            data = {
                'period': period,
                'search_overview': search_overview,
                'search_types': list(search_types),
                'popular_queries': list(popular_queries),
                'query_performance': list(query_performance),
                'filter_usage': filter_usage,
                'timestamp': timezone.now().isoformat()
            }

            return JsonResponse(data)

        except Exception as e:
            logger.error(f"Error in AdminSearchAnalytics: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class AdminUsersAnalytics(View):
    """Detailed user analytics."""

    def get(self, request):
        try:
            period = request.GET.get('period', '30d')
            start_date = get_period_filter(period)

            # User analytics overview
            user_analytics = UserAnalytics.objects.filter(
                last_calculated__gte=start_date,
                is_deleted=False
            )

            user_overview = user_analytics.aggregate(
                total_users=Count('id'),
                avg_engagement_score=Avg('engagement_score'),
                avg_retention_score=Avg('retention_score'),
                avg_session_count=Avg('total_sessions'),
                avg_session_duration=Avg('avg_session_duration'),
                high_risk_users=Count('id', filter=Q(churn_risk_score__gt=70))
            )

            # Activity level distribution
            activity_distribution = user_analytics.values('activity_level').annotate(
                count=Count('id'),
                avg_engagement=Avg('engagement_score')
            ).order_by('activity_level')

            # Platform usage
            platform_stats = user_analytics.aggregate(
                total_mobile=Sum('mobile_sessions'),
                total_desktop=Sum('desktop_sessions'),
                total_tablet=Sum('tablet_sessions')
            )

            total_sessions = sum([v for v in platform_stats.values() if v])
            platform_distribution = []
            if total_sessions > 0:
                platform_distribution = [
                    {'platform': 'Mobile', 'count': platform_stats['total_mobile'] or 0, 'percentage': round((platform_stats['total_mobile'] or 0) / total_sessions * 100, 1)},
                    {'platform': 'Desktop', 'count': platform_stats['total_desktop'] or 0, 'percentage': round((platform_stats['total_desktop'] or 0) / total_sessions * 100, 1)},
                    {'platform': 'Tablet', 'count': platform_stats['total_tablet'] or 0, 'percentage': round((platform_stats['total_tablet'] or 0) / total_sessions * 100, 1)}
                ]

            # User events breakdown
            user_events = UserEvent.objects.filter(
                created_at__gte=start_date,
                is_deleted=False
            )

            event_distribution = user_events.values('event_type').annotate(
                count=Count('id'),
                unique_users=Count('user', distinct=True)
            ).order_by('-count')[:15]

            # Churn risk analysis
            churn_ranges = [
                (0, 20, 'Low Risk'),
                (20, 40, 'Moderate Risk'),
                (40, 60, 'Medium Risk'),
                (60, 80, 'High Risk'),
                (80, 100, 'Critical Risk')
            ]

            churn_distribution = []
            for min_score, max_score, label in churn_ranges:
                count = user_analytics.filter(
                    churn_risk_score__gte=min_score,
                    churn_risk_score__lt=max_score
                ).count()
                churn_distribution.append({
                    'range': label,
                    'count': count,
                    'min_score': min_score,
                    'max_score': max_score
                })

            # Daily user trends
            daily_trends = DailyAnalytics.objects.filter(
                date__gte=start_date.date(),
                is_deleted=False
            ).order_by('date').values(
                'date', 'total_users', 'new_users', 'returning_users',
                'avg_session_duration', 'bounce_rate'
            )

            data = {
                'period': period,
                'user_overview': user_overview,
                'activity_distribution': list(activity_distribution),
                'platform_distribution': platform_distribution,
                'event_distribution': list(event_distribution),
                'churn_distribution': churn_distribution,
                'daily_trends': list(daily_trends),
                'timestamp': timezone.now().isoformat()
            }

            return JsonResponse(data)

        except Exception as e:
            logger.error(f"Error in AdminUsersAnalytics: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


# API endpoint decorators for the new views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_overview(request):
    """REST API wrapper for overview analytics."""
    view = AdminOverview()
    response = view.get(request)
    if hasattr(response, 'content'):
        import json
        return Response(json.loads(response.content))
    return Response(response)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_content_analytics(request):
    """REST API wrapper for content analytics."""
    view = AdminContentAnalytics()
    response = view.get(request)
    if hasattr(response, 'content'):
        import json
        return Response(json.loads(response.content))
    return Response(response)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_search_analytics(request):
    """REST API wrapper for search analytics."""
    view = AdminSearchAnalytics()
    response = view.get(request)
    if hasattr(response, 'content'):
        import json
        return Response(json.loads(response.content))
    return Response(response)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_users_analytics(request):
    """REST API wrapper for users analytics."""
    view = AdminUsersAnalytics()
    response = view.get(request)
    if hasattr(response, 'content'):
        import json
        return Response(json.loads(response.content))
    return Response(response)
