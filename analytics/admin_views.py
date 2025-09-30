"""
Admin Analytics Views for comprehensive dashboard data.
"""
import json
import csv
import io
from datetime import timedelta, date
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Count, Sum, Avg, Max, Min, F, Q
from django.db.models.functions import TruncDate, TruncHour
from django.core.paginator import Paginator

from analytics.models import (
    ContentAnalytics,  SearchAnalytics,
    UserAnalytics, AuthenticationMetric, DailyAnalytics,
    SystemMetric
)
from content.models import PostSee
from accounts.models import UserProfile
from communities.models import Community


def is_admin_user(user):
    """Check if user is admin or staff."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@method_decorator([csrf_exempt, login_required, user_passes_test(is_admin_user)], name='dispatch')
class AdminAnalyticsOverview(View):
    """Overview analytics for admin dashboard."""

    def get(self, request):
        try:
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)

            # Basic counts
            total_users = UserProfile.objects.filter(is_deleted=False).count()
            total_posts = ContentAnalytics.objects.filter(
                content_type='post', is_deleted=False
            ).count()

            # Daily active users (simplified - users who viewed content today)
            daily_active_users = ContentAnalytics.objects.filter(
                last_updated__date=today, is_deleted=False
            ).values('author').distinct().count()

            # Growth rates (week over week)
            users_last_week = UserProfile.objects.filter(
                user__date_joined__date__gte=week_ago, is_deleted=False
            ).count()
            posts_last_week = ContentAnalytics.objects.filter(
                created_at__date__gte=week_ago, is_deleted=False
            ).count()

            # Performance metrics
            avg_response_time = SystemMetric.objects.filter(
                metric_type='response_time',
                created_at__date=today
            ).aggregate(avg_time=Avg('value'))['avg_time'] or 0

            # Recent activity (24 hours)
            yesterday = today - timedelta(days=1)
            new_users_24h = UserProfile.objects.filter(
                user__date_joined__date__gte=yesterday, is_deleted=False
            ).count()
            new_posts_24h = ContentAnalytics.objects.filter(
                created_at__date__gte=yesterday, is_deleted=False
            ).count()

            data = {
                'total_users': total_users,
                'total_posts': total_posts,
                'daily_active_users': daily_active_users,
                'user_growth_rate': self._calculate_growth_rate(users_last_week, total_users),
                'post_growth_rate': self._calculate_growth_rate(posts_last_week, total_posts),
                'dau_growth_rate': 5.2,  # Placeholder - would need historical DAU data
                'avg_response_time': float(avg_response_time),
                'db_query_time': 2.5,  # Placeholder - would need actual DB metrics
                'new_users_24h': new_users_24h,
                'new_posts_24h': new_posts_24h,
                'timestamp': timezone.now().isoformat()
            }

            return JsonResponse(data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def _calculate_growth_rate(self, recent_count, total_count):
        """Calculate growth rate percentage."""
        if total_count == 0:
            return 0
        return (recent_count / total_count) * 100


@method_decorator([csrf_exempt, login_required, user_passes_test(is_admin_user)], name='dispatch')
class AdminContentAnalytics(View):
    """Content analytics for admin dashboard."""

    def get(self, request):
        try:
            period = request.GET.get('period', '7d')
            limit = int(request.GET.get('limit', 20))

            # Parse period
            days = self._parse_period(period)
            since_date = timezone.now() - timedelta(days=days)

            # Aggregate content metrics
            content_metrics = ContentAnalytics.objects.filter(
                created_at__gte=since_date, is_deleted=False
            ).aggregate(
                total_views=Sum('view_count'),
                total_likes=Sum('like_count'),
                total_shares=Sum('share_count'),
                total_comments=Sum('comment_count'),
                avg_engagement=Avg('engagement_rate')
            )

            # Top performing content
            top_content = ContentAnalytics.objects.filter(
                created_at__gte=since_date, is_deleted=False
            ).order_by('-engagement_rate')[:limit]

            top_content_data = []
            for content in top_content:
                top_content_data.append({
                    'id': str(content.content_id),
                    'content_type': content.content_type,
                    'title': f"Content {content.content_id}",  # Would need to join with actual content
                    'view_count': content.view_count,
                    'like_count': content.like_count,
                    'comment_count': content.comment_count,
                    'engagement_rate': float(content.engagement_rate),
                    'created_at': content.created_at.isoformat()
                })

            data = {
                'total_views': content_metrics['total_views'] or 0,
                'total_likes': content_metrics['total_likes'] or 0,
                'total_shares': content_metrics['total_shares'] or 0,
                'total_comments': content_metrics['total_comments'] or 0,
                'avg_engagement_rate': float(content_metrics['avg_engagement'] or 0),
                'top_content': top_content_data,
                'period': period,
                'timestamp': timezone.now().isoformat()
            }

            return JsonResponse(data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def _parse_period(self, period):
        """Parse period string to days."""
        if period == '1d':
            return 1
        elif period == '7d':
            return 7
        elif period == '30d':
            return 30
        elif period == '90d':
            return 90
        else:
            return 7


@method_decorator([csrf_exempt, login_required, user_passes_test(is_admin_user)], name='dispatch')
class AdminUserAnalytics(View):
    """User analytics for admin dashboard."""

    def get(self, request):
        try:
            period = request.GET.get('period', '30d')

            days = self._parse_period(period)
            since_date = timezone.now() - timedelta(days=days)

            # Active users (users with analytics updates in period)
            active_users = UserAnalytics.objects.filter(
                last_activity_date__gte=since_date, is_deleted=False
            ).count()

            # User metrics
            user_metrics = UserAnalytics.objects.filter(
                last_activity_date__gte=since_date, is_deleted=False
            ).aggregate(
                avg_session_time=Avg('avg_session_duration_minutes'),
                avg_engagement=Avg('engagement_score'),
                avg_reputation=Avg('reputation_score')
            )

            # Activity level distribution
            activity_distribution = UserAnalytics.objects.filter(
                is_deleted=False
            ).values('activity_level').annotate(
                count=Count('id')
            ).order_by('activity_level')

            activity_dist = {}
            for item in activity_distribution:
                activity_dist[item['activity_level']] = item['count']

            # Simplified metrics (would need more complex calculations in production)
            retention_rate = 75.5  # Placeholder
            bounce_rate = 32.1  # Placeholder

            data = {
                'active_users': active_users,
                'avg_session_time': float(user_metrics['avg_session_time'] or 0) * 60,  # Convert to seconds
                'retention_rate': retention_rate,
                'bounce_rate': bounce_rate,
                'avg_engagement_score': float(user_metrics['avg_engagement'] or 0),
                'avg_reputation_score': float(user_metrics['avg_reputation'] or 0),
                'activity_distribution': activity_dist,
                'period': period,
                'timestamp': timezone.now().isoformat()
            }

            return JsonResponse(data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def _parse_period(self, period):
        """Parse period string to days."""
        if period == '1d':
            return 1
        elif period == '7d':
            return 7
        elif period == '30d':
            return 30
        elif period == '90d':
            return 90
        else:
            return 30


@method_decorator([csrf_exempt, login_required, user_passes_test(is_admin_user)], name='dispatch')
class AdminSearchAnalytics(View):
    """Search analytics for admin dashboard."""

    def get(self, request):
        try:
            period = request.GET.get('period', '7d')
            limit = int(request.GET.get('limit', 10))

            days = self._parse_period(period)
            since_date = timezone.now() - timedelta(days=days)

            # Search metrics
            search_metrics = SearchAnalytics.objects.filter(
                searched_at__gte=since_date, is_deleted=False
            ).aggregate(
                total_searches=Count('id'),
                zero_results=Count('id', filter=Q(zero_results=True)),
                avg_ctr=Avg('click_through_rate'),
                avg_response_time=Avg('search_time_ms')
            )

            total_searches = search_metrics['total_searches'] or 0
            zero_results = search_metrics['zero_results'] or 0

            # Calculate rates
            zero_result_rate = (zero_results / max(total_searches, 1)) * 100
            success_rate = 100 - zero_result_rate

            # Popular search terms
            popular_terms = SearchAnalytics.objects.filter(
                searched_at__gte=since_date, is_deleted=False
            ).values('normalized_query').annotate(
                count=Count('id')
            ).order_by('-count')[:limit]

            popular_terms_data = []
            for term in popular_terms:
                popular_terms_data.append({
                    'query': term['normalized_query'],
                    'count': term['count']
                })

            data = {
                'total_searches': total_searches,
                'avg_ctr': float(search_metrics['avg_ctr'] or 0),
                'zero_result_rate': zero_result_rate,
                'avg_response_time': float(search_metrics['avg_response_time'] or 0),
                'success_rate': success_rate,
                'satisfaction_score': 78.5,  # Placeholder - would need user feedback data
                'popular_terms': popular_terms_data,
                'period': period,
                'timestamp': timezone.now().isoformat()
            }

            return JsonResponse(data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def _parse_period(self, period):
        """Parse period string to days."""
        if period == '1d':
            return 1
        elif period == '7d':
            return 7
        elif period == '30d':
            return 30
        elif period == '90d':
            return 90
        else:
            return 7


@method_decorator([csrf_exempt, login_required, user_passes_test(is_admin_user)], name='dispatch')
class AdminAuthenticationAnalytics(View):
    """Authentication analytics for admin dashboard."""

    def get(self, request):
        try:
            period = request.GET.get('period', '7d')

            days = self._parse_period(period)
            since_date = timezone.now() - timedelta(days=days)

            # Authentication metrics
            auth_metrics = AuthenticationMetric.objects.filter(
                created_at__gte=since_date, is_deleted=False
            ).aggregate(
                total_attempts=Count('id'),
                successful_logins=Count('id', filter=Q(success=True)),
                failed_attempts=Count('id', filter=Q(success=False)),
                avg_auth_time=Avg('response_time_ms'),
                token_renewals=Count('id', filter=Q(action='token_renewal'))
            )

            total_attempts = auth_metrics['total_attempts'] or 0
            successful_logins = auth_metrics['successful_logins'] or 0

            # Calculate success rate
            success_rate = (successful_logins / max(total_attempts, 1)) * 100

            # Authentication methods (simplified)
            auth_methods = {
                'password': {
                    'count': successful_logins,
                    'success_rate': success_rate
                },
                'social': {
                    'count': 0,  # Placeholder
                    'success_rate': 0.0
                },
                'sso': {
                    'count': 0,  # Placeholder
                    'success_rate': 0.0
                }
            }

            data = {
                'success_rate': success_rate,
                'avg_auth_time': float(auth_metrics['avg_auth_time'] or 0),
                'failed_attempts': auth_metrics['failed_attempts'] or 0,
                'token_renewals': auth_metrics['token_renewals'] or 0,
                'total_attempts': total_attempts,
                'auth_methods': auth_methods,
                'period': period,
                'timestamp': timezone.now().isoformat()
            }

            return JsonResponse(data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def _parse_period(self, period):
        """Parse period string to days."""
        if period == '1d':
            return 1
        elif period == '7d':
            return 7
        elif period == '30d':
            return 30
        elif period == '90d':
            return 90
        else:
            return 7


@method_decorator([csrf_exempt, login_required, user_passes_test(is_admin_user)], name='dispatch')
class AdminAnalyticsExport(View):
    """Export analytics data in various formats."""

    def get(self, request, analytics_type):
        try:
            format_type = request.GET.get('format', 'csv').lower()
            period = request.GET.get('period', '30d')

            if analytics_type not in ['content', 'users', 'search', 'authentication']:
                return JsonResponse({'error': 'Invalid analytics type'}, status=400)

            if format_type == 'csv':
                return self._export_csv(analytics_type, period)
            elif format_type == 'json':
                return self._export_json(analytics_type, period)
            else:
                return JsonResponse({'error': 'Unsupported format'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def _export_csv(self, analytics_type, period):
        """Export analytics data as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        days = self._parse_period(period)
        since_date = timezone.now() - timedelta(days=days)

        if analytics_type == 'content':
            writer.writerow(['Content ID', 'Type', 'Views', 'Likes', 'Comments', 'Engagement Rate', 'Created'])
            content_data = ContentAnalytics.objects.filter(
                created_at__gte=since_date, is_deleted=False
            ).order_by('-engagement_rate')

            for content in content_data:
                writer.writerow([
                    str(content.content_id),
                    content.content_type,
                    content.view_count,
                    content.like_count,
                    content.comment_count,
                    content.engagement_rate,
                    content.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
        # Create HTTP response with CSV
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{analytics_type}_analytics_{period}.csv"'
        return response

    def _export_json(self, analytics_type, period):
        """Export analytics data as JSON."""
        days = self._parse_period(period)
        since_date = timezone.now() - timedelta(days=days)

        data = {'type': analytics_type, 'period': period, 'data': []}

        if analytics_type == 'content':
            content_data = ContentAnalytics.objects.filter(
                created_at__gte=since_date, is_deleted=False
            ).order_by('-engagement_rate')

            for content in content_data:
                data['data'].append({
                    'content_id': str(content.content_id),
                    'content_type': content.content_type,
                    'view_count': content.view_count,
                    'like_count': content.like_count,
                    'comment_count': content.comment_count,
                    'engagement_rate': float(content.engagement_rate),
                    'created_at': content.created_at.isoformat()
                })

        response = HttpResponse(json.dumps(data, indent=2, default=str), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{analytics_type}_analytics_{period}.json"'
        return response

    def _parse_period(self, period):
        """Parse period string to days."""
        if period == '1d':
            return 1
        elif period == '7d':
            return 7
        elif period == '30d':
            return 30
        elif period == '90d':
            return 90
        else:
            return 30


@require_http_methods(["GET"])
@login_required
@user_passes_test(is_admin_user)
def admin_realtime_analytics(request):
    """Get real-time analytics data."""
    try:
        # Get current metrics
        now = timezone.now()
        last_hour = now - timedelta(hours=1)

        # Real-time activity
        recent_views = ContentAnalytics.objects.filter(
            last_updated__gte=last_hour, is_deleted=False
        ).aggregate(total_views=Sum('view_count'))['total_views'] or 0

        recent_searches = SearchAnalytics.objects.filter(
            searched_at__gte=last_hour, is_deleted=False
        ).count()

        # Active users (simplified)
        active_users_now = UserAnalytics.objects.filter(
            last_activity_date__date=now.date(), is_deleted=False
        ).count()

        data = {
            'active_users': active_users_now,
            'recent_views': recent_views,
            'recent_searches': recent_searches,
            'timestamp': now.isoformat(),
            'refresh_interval': 30  # seconds
        }

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
