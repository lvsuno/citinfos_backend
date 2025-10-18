from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Avg, Max, Min, Sum, F, Q
from django.db import transaction, connection
from datetime import timedelta
from analytics.models import (
    DailyAnalytics, UserAnalytics, SystemMetric, ErrorLog, CommunityAnalytics,
    AuthenticationMetric, AuthenticationReport, SessionAnalytic,
    ContentAnalytics, SearchAnalytics, AnonymousSession, AnonymousPageView,
    PageAnalytics
)
from analytics.utils import (
    update_user_analytics, generate_daily_analytics,
    clean_expired_analytics_data, calculate_content_quality_score
)
from content.utils import calculate_engagement_score
from content.models import PostSee, Post, Comment, PostReaction
from accounts.models import UserProfile
from communities.models import Community, CommunityMembership
from analytics.services import online_tracker
import logging
import hashlib

logger = logging.getLogger(__name__)


def calculate_percentile(values, percentile):
    """
    Calculate percentile without numpy dependency.

    Args:
        values: List of numeric values
        percentile: Percentile to calculate (0-100)

    Returns:
        float: The calculated percentile value
    """
    if not values:
        return 0.0

    sorted_values = sorted(values)
    n = len(sorted_values)

    if n == 1:
        return float(sorted_values[0])

    # Calculate index for percentile
    index = (percentile / 100.0) * (n - 1)

    if index.is_integer():
        return float(sorted_values[int(index)])
    else:
        # Interpolate between adjacent values
        lower_index = int(index)
        upper_index = lower_index + 1

        if upper_index >= n:
            return float(sorted_values[-1])

        lower_value = sorted_values[lower_index]
        upper_value = sorted_values[upper_index]

        # Linear interpolation
        fraction = index - lower_index
        return float(lower_value + fraction * (upper_value - lower_value))


@shared_task
def process_daily_analytics():
    """Process daily analytics for users and system"""
    try:
        today = timezone.now().date()

        # Create daily analytics record
        daily_analytics, created = DailyAnalytics.objects.get_or_create(
            date=today,
            defaults={
                'active_users': 0,
                'new_users': 0,
                'total_posts': 0,
                'total_comments': 0,
                'total_likes': 0,
                'average_session_time': 0
            }
        )

        if created:
            # Calculate metrics

            from django.contrib.auth.models import User

            # Count active users (users who successfully authenticated today)
            from analytics.models import AuthenticationMetric

            # Use timezone-aware datetime objects to avoid warnings
            today_start = timezone.make_aware(
                timezone.datetime.combine(today, timezone.datetime.min.time())
            )
            today_end = today_start + timedelta(days=1)

            active_users = AuthenticationMetric.objects.filter(
                timestamp__gte=today_start,
                timestamp__lt=today_end,
                success=True,
                user__isnull=False
            ).values('user').distinct().count()

            # Count new users
            new_users = User.objects.filter(date_joined__date=today).count()

            # Count content
            total_posts = Post.objects.filter(created_at__date=today).count()
            total_comments = Comment.objects.filter(created_at__date=today).count()
            # Count reactions (replaces likes)
            total_reactions = PostReaction.objects.filter(
                created_at__date=today
            ).count()

            # Update analytics
            daily_analytics.active_users = active_users
            daily_analytics.new_users = new_users
            daily_analytics.total_posts = total_posts
            daily_analytics.total_comments = total_comments
            daily_analytics.total_likes = total_reactions  # Now counts reactions
            daily_analytics.save()

        return f"Processed daily analytics for {today}"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error processing daily analytics: {str(e)}',
            extra_data={'task': 'process_daily_analytics'}
        )
        return f"Error: {str(e)}"


@shared_task
def update_system_metrics():
    """Update system performance metrics"""
    try:
        # Get database metrics using PostgreSQL-compatible queries
        with connection.cursor() as cursor:
            # PostgreSQL equivalent to get connection count
            cursor.execute("""
                SELECT count(*)
                FROM pg_stat_activity
                WHERE state = 'active'
            """)
            active_connections = cursor.fetchone()[0] if cursor.fetchone else 0

            # Get database size
            cursor.execute("""
                SELECT pg_database_size(current_database())
            """)
            db_size = cursor.fetchone()[0] if cursor.fetchone else 0

        # Create system metric records
        SystemMetric.objects.create(
            metric_type='database_connections',
            value=active_connections
        )

        SystemMetric.objects.create(
            metric_type='database_size_bytes',
            value=db_size,
        )

        return f"Updated system metrics at {timezone.now()}"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating system metrics: {str(e)}',
            extra_data={'task': 'update_system_metrics'}
        )
        return f"Error: {str(e)}"


@shared_task
def cleanup_old_data():
    """Clean up old analytics and log data"""
    try:
        cutoff_date = timezone.now() - timedelta(days=90)

        # Clean old error logs
        old_errors = ErrorLog.objects.filter(recorded_at__lt=cutoff_date)
        error_count = old_errors.count()
        old_errors.delete()

        # Clean old system metrics
        old_metrics = SystemMetric.objects.filter(recorded_at__lt=cutoff_date)
        metric_count = old_metrics.count()
        old_metrics.delete()

        return f"Cleaned {error_count} old error logs and {metric_count} old metrics"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error cleaning old data: {str(e)}',
            extra_data={'task': 'cleanup_old_data'}
        )
        return f"Error: {str(e)}"


@shared_task
def update_user_engagement_scores():
    """Update engagement scores for all users."""
    try:
        users = UserProfile.objects.all()
        updated_count = 0

        for user in users:
            try:
                engagement_score = calculate_engagement_score(user.user)
                quality_score = calculate_content_quality_score(user.user)

                # Update user profile with both scores
                user.engagement_score = engagement_score
                user.content_quality_score = quality_score
                user.save(update_fields=[
                    'engagement_score',
                    'content_quality_score'
                ])
                updated_count += 1

            except Exception as e:
                ErrorLog.objects.create(
                    user=user,
                    level='error',
                    message=f'Error updating engagement score: {str(e)}',
                    extra_data={
                        'user_id': str(user.id),
                        'task': 'update_user_engagement_scores'
                    }
                )

        return f"Updated engagement scores for {updated_count} users"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error in update_user_engagement_scores: {str(e)}',
            extra_data={'task': 'update_user_engagement_scores'}
        )
        return f"Error: {str(e)}"


@shared_task
def process_analytics_daily():
    """Process all daily analytics tasks."""
    try:
        # Use utility functions
        generate_daily_analytics()
        update_user_analytics()

        return "Daily analytics processed successfully"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error processing daily analytics: {str(e)}',
            extra_data={'task': 'process_analytics_daily'}
        )
        return f"Error: {str(e)}"


@shared_task
def update_advanced_system_metrics():
    """Update advanced system-wide metrics."""
    try:
        from django.db import connection

        # Database metrics
        with connection.cursor() as cursor:
            # Active sessions
            cursor.execute(
                "SELECT count(*) FROM django_session WHERE expire_date > NOW()"
            )
            active_sessions = cursor.fetchone()[0]

        SystemMetric.objects.create(
            metric_type='concurrent_connections',
            value=active_sessions,
            additional_data={'timestamp': timezone.now().isoformat()}
        )

        # Active users in the last hour
        active_users = UserProfile.objects.filter(
            last_active__gte=timezone.now() - timedelta(hours=1)
        ).count()

        SystemMetric.objects.create(
            metric_type='active_users_hourly',
            value=active_users,
            additional_data={'period': 'last_hour'}
        )

        # Memory usage (if available)
        try:
            import psutil
            memory_usage = psutil.virtual_memory().percent

            SystemMetric.objects.create(
                metric_type='memory_usage',
                value=memory_usage,
                additional_data={'unit': 'percent'}
            )
        except ImportError:
            pass  # psutil not available

        # Cache hit rate (if using cache)
        try:
            from django.core.cache import cache
            cache_info = cache.get('_cache_stats', {})
            hit_rate = cache_info.get('hit_rate', 0.0)

            SystemMetric.objects.create(
                metric_type='cache_hit_rate',
                value=hit_rate,
                additional_data=cache_info
            )
        except Exception:
            pass  # Cache stats not available

        return f"Updated advanced system metrics at {timezone.now()}"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating advanced system metrics: {str(e)}',
            extra_data={'task': 'update_advanced_system_metrics'}
        )
        return f"Error: {str(e)}"


@shared_task
def comprehensive_cleanup():
    """Comprehensive cleanup of old analytics data."""
    try:
        # Use utility function
        clean_expired_analytics_data()

        # Additional cleanup for user analytics
        old_user_analytics = UserAnalytics.objects.filter(
            updated_at__lt=timezone.now() - timedelta(days=180)
        )
        analytics_count = old_user_analytics.count()
        old_user_analytics.delete()

        return f"Comprehensive cleanup completed. Removed {analytics_count} old user analytics records"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error in comprehensive cleanup: {str(e)}',
            extra_data={'task': 'comprehensive_cleanup'}
        )
        return f"Error: {str(e)}"


@shared_task
def generate_weekly_analytics_report():
    """Generate weekly analytics summary."""
    try:
        from analytics.utils import get_analytics_summary

        # Get weekly summary
        weekly_summary = get_analytics_summary(days=7)

        # Log the summary as a system metric
        SystemMetric.objects.create(
            metric_type='weekly_summary',
            value=weekly_summary.get('total_users', 0),
            additional_data=weekly_summary
        )

        return f"Generated weekly analytics report: {weekly_summary['total_users']} total users"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error generating weekly report: {str(e)}',
            extra_data={'task': 'generate_weekly_analytics_report'}
        )
        return f"Error: {str(e)}"


# Community Analytics Tasks
@shared_task(bind=True, max_retries=3)
def cleanup_inactive_users(self):
    """Cleanup task to remove inactive users from Redis tracking."""
    try:
        cleaned_count = online_tracker.cleanup_inactive_users()
        logger.info("Cleaned up %d inactive users from online tracking", cleaned_count)
        return cleaned_count
    except Exception as exc:
        logger.error("Error during inactive users cleanup: %s", exc)
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def update_community_analytics(self, community_id=None):
    """Update database analytics from Redis data."""
    try:
        if community_id:
            communities = Community.objects.filter(id=community_id, is_deleted=False)
        else:
            communities = Community.objects.filter(is_deleted=False)

        updated_count = 0

        for community in communities:
            try:
                with transaction.atomic():
                    # Get or create today's analytics record
                    analytics, created = CommunityAnalytics.objects.get_or_create(
                        community=community,
                        date=timezone.now().date(),
                        defaults={
                            'current_online_members': 0,
                            'peak_online_today': 0,
                            'peak_online_this_week': 0,
                            'peak_online_this_month': 0,
                        }
                    )

                    # Get real-time data from Redis
                    current_online = online_tracker.get_online_count(str(community.id))
                    peaks = online_tracker.get_peak_counts(str(community.id))

                    # Update analytics
                    analytics.current_online_members = current_online
                    analytics.peak_online_today = max(
                        analytics.peak_online_today,
                        peaks['daily']
                    )
                    analytics.peak_online_this_week = max(
                        analytics.peak_online_this_week,
                        peaks['weekly']
                    )
                    analytics.peak_online_this_month = max(
                        analytics.peak_online_this_month,
                        peaks['monthly']
                    )

                    # Calculate activity metrics
                    today = timezone.now().date()

                    # Daily active members (members who were online today)
                    daily_active = CommunityMembership.objects.filter(
                        community=community,
                        status='active',
                        is_deleted=False,
                        last_active__date=today
                    ).count()

                    # Weekly active members
                    week_start = today - timezone.timedelta(days=today.weekday())
                    weekly_active = CommunityMembership.objects.filter(
                        community=community,
                        status='active',
                        is_deleted=False,
                        last_active__date__gte=week_start
                    ).count()

                    # Monthly active members
                    month_start = today.replace(day=1)
                    monthly_active = CommunityMembership.objects.filter(
                        community=community,
                        status='active',
                        is_deleted=False,
                        last_active__date__gte=month_start
                    ).count()

                    analytics.daily_active_members = daily_active
                    analytics.weekly_active_members = weekly_active
                    analytics.monthly_active_members = monthly_active

                    # Calculate new members
                    new_today = CommunityMembership.objects.filter(
                        community=community,
                        status='active',
                        is_deleted=False,
                        joined_at__date=today
                    ).count()

                    new_this_week = CommunityMembership.objects.filter(
                        community=community,
                        status='active',
                        is_deleted=False,
                        joined_at__date__gte=week_start
                    ).count()

                    new_this_month = CommunityMembership.objects.filter(
                        community=community,
                        status='active',
                        is_deleted=False,
                        joined_at__date__gte=month_start
                    ).count()

                    analytics.new_members_today = new_today
                    analytics.new_members_this_week = new_this_week
                    analytics.new_members_this_month = new_this_month

                    analytics.save()
                    updated_count += 1

            except Exception as e:
                logger.error("Error updating analytics for community %s: %s",
                           community.id, e)
                continue

        logger.info("Updated analytics for %d communities", updated_count)
        return updated_count

    except Exception as exc:
        logger.error("Error during analytics update: %s", exc)
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def sync_member_activity(self, user_id, community_id):
    """Sync member activity between database and Redis."""
    try:
        # Update last_active in database
        membership = CommunityMembership.objects.filter(
            user_id=user_id,
            community_id=community_id,
            status='active',
            is_deleted=False
        ).first()

        if membership:
            membership.last_active = timezone.now()
            membership.save(update_fields=['last_active'])

            # Update Redis tracking
            online_tracker.update_user_activity(str(user_id), str(community_id))

            logger.info("Synced activity for user %s in community %s",
                       user_id, community_id)
            return True
        else:
            logger.warning("Membership not found for user %s in community %s",
                         user_id, community_id)
            return False

    except Exception as exc:
        logger.error("Error syncing member activity: %s", exc)
        raise self.retry(exc=exc, countdown=30)



# Authentication Analytics Tasks
@shared_task
def generate_authentication_reports():
    """
    Generate aggregated authentication analytics reports.
    Creates hourly, daily, weekly, and monthly reports for performance analysis.
    """
    try:
        from django.db.models import Q
        from datetime import datetime

        now = timezone.now()

        # Generate hourly report for the past hour
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)

        _generate_auth_report('hourly', hour_start, hour_end)

        # Generate daily report for yesterday (if it's after midnight)
        if now.hour >= 1:  # Wait an hour after midnight to ensure all data is captured
            day_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            _generate_auth_report('daily', day_start, day_end)

        # Generate weekly report on Monday morning
        if now.weekday() == 0 and now.hour >= 1:  # Monday after 1 AM
            week_start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
            week_end = week_start + timedelta(days=7)
            _generate_auth_report('weekly', week_start, week_end)

        # Generate monthly report on the 1st of each month
        if now.day == 1 and now.hour >= 1:  # 1st of month after 1 AM
            month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            _generate_auth_report('monthly', month_start, month_end)

        return f"Authentication reports generated for {now}"

    except Exception as e:
        logger.error("Error generating authentication reports: %s", e)
        ErrorLog.objects.create(
            level='error',
            message=f'Error generating authentication reports: {str(e)}',
            extra_data={'task': 'generate_authentication_reports'}
        )
        return f"Error: {str(e)}"


def _generate_auth_report(report_type, period_start, period_end):
    """Helper function to generate a specific authentication report."""
    from django.db.models import Q

    # Get or create the report
    report, created = AuthenticationReport.objects.get_or_create(
        report_type=report_type,
        period_start=period_start,
        defaults={
            'period_end': period_end,
        }
    )

    if not created and not report.period_end:
        report.period_end = period_end

    # Get authentication metrics for the period
    metrics = AuthenticationMetric.objects.filter(
        timestamp__gte=period_start,
        timestamp__lt=period_end,
        is_deleted=False
    )

    if not metrics.exists():
        logger.info(f"No authentication metrics found for {report_type} report {period_start}")
        return

    # Calculate authentication method counts
    report.jwt_valid_count = metrics.filter(auth_method='jwt_valid').count()
    report.jwt_expired_session_renewal_count = metrics.filter(
        auth_method='jwt_expired_session_renewal'
    ).count()
    report.session_only_count = metrics.filter(auth_method='session_only').count()
    report.unauthenticated_count = metrics.filter(auth_method='unauthenticated').count()
    report.authentication_failed_count = metrics.filter(
        auth_method='authentication_failed'
    ).count()

    # Calculate performance metrics
    successful_auths = metrics.filter(success=True)
    if successful_auths.exists():
        report.avg_total_auth_time = successful_auths.aggregate(
            avg_time=Avg('total_auth_time')
        )['avg_time'] or 0.0

        jwt_metrics = successful_auths.filter(jwt_validation_time__isnull=False)
        if jwt_metrics.exists():
            report.avg_jwt_validation_time = jwt_metrics.aggregate(
                avg_time=Avg('jwt_validation_time')
            )['avg_time'] or 0.0

        session_metrics = successful_auths.filter(session_lookup_time__isnull=False)
        if session_metrics.exists():
            report.avg_session_lookup_time = session_metrics.aggregate(
                avg_time=Avg('session_lookup_time')
            )['avg_time'] or 0.0

        # Calculate percentiles
        auth_times = list(successful_auths.values_list('total_auth_time', flat=True))
        if auth_times:
            report.p50_auth_time = calculate_percentile(auth_times, 50)
            report.p95_auth_time = calculate_percentile(auth_times, 95)
            report.p99_auth_time = calculate_percentile(auth_times, 99)

    # Calculate success rates
    total_requests = metrics.count()
    successful_requests = metrics.filter(success=True).count()

    if total_requests > 0:
        report.overall_success_rate = (successful_requests / total_requests) * 100

        jwt_requests = metrics.filter(auth_method__in=['jwt_valid', 'jwt_expired_session_renewal'])
        jwt_successful = jwt_requests.filter(success=True).count()
        jwt_total = jwt_requests.count()
        if jwt_total > 0:
            report.jwt_success_rate = (jwt_successful / jwt_total) * 100

        session_requests = metrics.filter(auth_method='session_only')
        session_successful = session_requests.filter(success=True).count()
        session_total = session_requests.count()
        if session_total > 0:
            report.session_success_rate = (session_successful / session_total) * 100

    # JWT renewal tracking
    report.jwt_renewals_count = metrics.filter(jwt_renewed=True).count()
    renewed_metrics = metrics.filter(jwt_renewed=True, token_age_seconds__isnull=False)
    if renewed_metrics.exists():
        report.avg_token_age_at_renewal = renewed_metrics.aggregate(
            avg_age=Avg('token_age_seconds')
        )['avg_age'] or 0.0

    # Unique metrics
    report.unique_users_count = metrics.filter(user__isnull=False).values('user').distinct().count()
    report.unique_sessions_count = metrics.exclude(session_id='').values('session_id').distinct().count()

    # Top endpoints
    endpoint_counts = metrics.values('endpoint').annotate(
        count=Count('endpoint')
    ).order_by('-count')[:10]
    report.top_endpoints = list(endpoint_counts)

    # Error patterns
    error_patterns = metrics.filter(success=False).values('error_message').annotate(
        count=Count('error_message')
    ).order_by('-count')[:10]
    report.error_patterns = list(error_patterns)

    report.save()

    logger.info(f"Generated {report_type} authentication report for {period_start} - {period_end}")


@shared_task
def cleanup_authentication_analytics():
    """
    Clean up old authentication analytics data to prevent database bloat.
    Keeps detailed metrics for 30 days, reports for 1 year.
    """
    try:
        from datetime import timedelta

        now = timezone.now()

        # Clean up detailed authentication metrics older than 30 days
        metrics_cutoff = now - timedelta(days=30)
        old_metrics = AuthenticationMetric.objects.filter(
            timestamp__lt=metrics_cutoff,
            is_deleted=False
        )
        metrics_count = old_metrics.count()
        old_metrics.update(is_deleted=True, deleted_at=now)

        # Clean up session analytics older than 90 days
        session_cutoff = now - timedelta(days=90)
        old_sessions = SessionAnalytic.objects.filter(
            created_at__lt=session_cutoff,
            is_deleted=False
        )
        sessions_count = old_sessions.count()
        old_sessions.update(is_deleted=True, deleted_at=now)

        # Clean up authentication reports older than 1 year
        reports_cutoff = now - timedelta(days=365)
        old_reports = AuthenticationReport.objects.filter(
            period_start__lt=reports_cutoff,
            is_deleted=False
        )
        reports_count = old_reports.count()
        old_reports.update(is_deleted=True, deleted_at=now)

        logger.info(f"Cleaned up {metrics_count} authentication metrics, "
                   f"{sessions_count} session analytics, "
                   f"{reports_count} authentication reports")

        return f"Cleaned up {metrics_count} metrics, {sessions_count} sessions, {reports_count} reports"

    except Exception as e:
        logger.error("Error cleaning up authentication analytics: %s", e)
        ErrorLog.objects.create(
            level='error',
            message=f'Error cleaning up authentication analytics: {str(e)}',
            extra_data={'task': 'cleanup_authentication_analytics'}
        )
        return f"Error: {str(e)}"


@shared_task
def track_authentication_performance(auth_data):
    """
    Track individual authentication performance metrics.
    Called by the authentication middleware for each request.

    Args:
        auth_data (dict): Authentication metrics data including:
            - auth_method: Authentication method used
            - user_id: User ID (if authenticated)
            - session_id: Session ID
            - jwt_validation_time: Time to validate JWT (ms)
            - session_lookup_time: Time to lookup session (ms)
            - total_auth_time: Total authentication time (ms)
            - endpoint: Request endpoint
            - http_method: HTTP method
            - ip_address: Client IP
            - user_agent: Client user agent
            - success: Whether authentication succeeded
            - error_message: Error message if failed
            - jwt_renewed: Whether JWT was renewed
            - token_age_seconds: Age of JWT token
            - token_remaining_seconds: Remaining JWT validity
            - additional_data: Any additional metadata
    """
    try:
        # Create authentication metric record
        AuthenticationMetric.objects.create(
            auth_method=auth_data.get('auth_method', 'unknown'),
            user_id=auth_data.get('user_id'),
            session_id=auth_data.get('session_id', ''),
            jwt_validation_time=auth_data.get('jwt_validation_time'),
            session_lookup_time=auth_data.get('session_lookup_time'),
            total_auth_time=auth_data.get('total_auth_time', 0.0),
            endpoint=auth_data.get('endpoint', ''),
            http_method=auth_data.get('http_method', ''),
            ip_address=auth_data.get('ip_address'),
            user_agent=auth_data.get('user_agent', ''),
            success=auth_data.get('success', False),
            error_message=auth_data.get('error_message', ''),
            jwt_renewed=auth_data.get('jwt_renewed', False),
            token_age_seconds=auth_data.get('token_age_seconds'),
            token_remaining_seconds=auth_data.get('token_remaining_seconds'),
            additional_data=auth_data.get('additional_data', {}),
        )

        return True

    except Exception as e:
        logger.error("Error tracking authentication performance: %s", e)
        return False


@shared_task
def track_session_comprehensive(session_data):
    """
    Comprehensive session tracking for lifecycle events and page analytics.
    Now properly handles event-specific fields and counters.

    Args:
        session_data (dict): Session data including:
            - session_id: Session identifier (raw, will be hashed)
            - user_id: User ID
            - event_type: Event type from SESSION_EVENTS
                         (created, renewed, expired, ended, cleanup)
            - processing_time_ms: Time taken for this event processing
            - creation_time_ms: Session creation time (for 'created' event)
            - expires_at: Session expiration time (optional)
            - ip_address: Client IP (optional)
            - user_agent: Client user agent (optional)
            - location_data: Geographic location data (optional)
            - path: Request path (for page visits)
            - http_method: HTTP method (for page visits)
            - additional_metadata: Any additional data (optional)
    """
    try:
        from django.conf import settings
        from django.contrib.auth import get_user_model
        import hashlib

        User = get_user_model()

        session_id = session_data.get('session_id')
        user_id = session_data.get('user_id')
        event_type = session_data.get('event_type', 'lookup')

        if not session_id:
            logger.warning("Missing session_id in session tracking data")
            return False

        # Hash the session ID consistently with middleware
        hash_algo = getattr(settings, 'SESSION_TOKEN_HASH_ALGO', 'sha256')
        hashed_session_id = hashlib.new(
            hash_algo, session_id.encode()
        ).hexdigest()

        # Get user if user_id provided
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(
                    f"User {user_id} not found for session analytics"
                )
                # For existing sessions without user, try to find by session_id
                try:
                    session_analytic = SessionAnalytic.objects.get(
                        session_id=hashed_session_id
                    )
                    user = session_analytic.user
                except SessionAnalytic.DoesNotExist:
                    return False

        if not user:
            logger.debug(
                f"Skipping session analytics for {session_id[:8]}... - "
                "no user context"
            )
            return False

        # Get processing time for this event
        processing_time = session_data.get('processing_time_ms', 0.0)
        now = timezone.now()

        # Handle session creation event
        if event_type == 'created':
            default_expires = timezone.now() + timedelta(hours=4)
            session_analytic, created = SessionAnalytic.objects.get_or_create(
                session_id=hashed_session_id,
                defaults={
                    'user': user,
                    'created_at': now,
                    'last_activity': now,
                    'expires_at': (
                        session_data.get('expires_at') or default_expires
                    ),
                    'creation_time_ms': session_data.get(
                        'creation_time_ms', processing_time
                    ),
                    'created_event_at': now,
                    'ip_address': session_data.get('ip_address'),
                    'user_agent': session_data.get('user_agent', ''),
                    'location_data': session_data.get('location_data', {}),
                    'additional_metadata': session_data.get(
                        'additional_metadata', {}
                    ),
                    'lookup_count': 1,
                    'total_processing_time_ms': processing_time,
                }
            )

            if created:
                logger.debug(
                    f"Created session analytics for {session_id[:8]}..."
                )

            return True

        # For all other events, get existing session record
        try:
            session_analytic = SessionAnalytic.objects.get(
                session_id=hashed_session_id
            )
        except SessionAnalytic.DoesNotExist:
            logger.warning(
                f"Session analytics not found for {session_id[:8]}... "
                f"event: {event_type}"
            )
            return False

        # Update common fields
        session_analytic.last_activity = now
        session_analytic.lookup_count = F('lookup_count') + 1
        session_analytic.total_processing_time_ms = (
            F('total_processing_time_ms') + processing_time
        )

        # Handle specific event types
        if event_type == 'renewed':
            # Update renewal counters
            session_analytic.renewal_count = F('renewal_count') + 1
            session_analytic.last_renewal_time_ms = processing_time
            session_analytic.total_renewal_time_ms = (
                F('total_renewal_time_ms') + processing_time
            )
            session_analytic.last_renewed_at = now

            # Set first renewal time if not set
            if not session_analytic.first_renewed_at:
                session_analytic.first_renewed_at = now

        elif event_type == 'smart_renewal':
            # Update smart renewal counters
            session_analytic.smart_renewals = F('smart_renewals') + 1
            session_analytic.last_smart_renewal_at = now

        elif event_type == 'renewal_skipped':
            # Track prevented renewals
            session_analytic.unnecessary_renewals_prevented = (
                F('unnecessary_renewals_prevented') + 1
            )

        elif event_type == 'expired':
            # Update expiry tracking
            session_analytic.expiry_check_count = F('expiry_check_count') + 1
            session_analytic.last_expiry_check_time_ms = processing_time
            session_analytic.total_expiry_check_time_ms = (
                F('total_expiry_check_time_ms') + processing_time
            )
            session_analytic.last_expired_checked_at = now

            # Mark session as actually expired
            session_analytic.session_actually_expired = True
            session_analytic.session_expired_at = now
            session_analytic.ended_at = now
            session_analytic.end_reason = 'expired'

        elif event_type == 'ended':
            # Update ended tracking
            session_analytic.ended_count = F('ended_count') + 1
            session_analytic.last_ended_time_ms = processing_time
            session_analytic.last_ended_checked_at = now
            session_analytic.manually_ended_at = now
            session_analytic.ended_at = now
            session_analytic.end_reason = 'ended'

            # Store specific reason if provided
            ended_reason = session_data.get('additional_metadata', {}).get(
                'termination_reason'
            )
            if ended_reason:
                session_analytic.ended_reason = ended_reason

        elif event_type == 'cleanup':
            # Update cleanup tracking
            session_analytic.cleanup_count = F('cleanup_count') + 1
            session_analytic.last_cleanup_time_ms = processing_time
            session_analytic.total_cleanup_time_ms = (
                F('total_cleanup_time_ms') + processing_time
            )
            session_analytic.last_cleanup_checked_at = now
            session_analytic.automated_cleanup_at = now
            session_analytic.ended_at = now
            session_analytic.end_reason = 'cleanup'

        elif event_type == 'page_visit':
            # Handle page visit tracking
            path = session_data.get('path', '')
            http_method = session_data.get('http_method', 'GET')

            if path:
                # Initialize metadata if needed
                if not session_analytic.additional_metadata:
                    session_analytic.additional_metadata = {}

                # Track page visits
                page_visits = session_analytic.additional_metadata.get(
                    'page_visits', {}
                )
                page_key = f"{http_method}:{path}"
                page_visits[page_key] = page_visits.get(page_key, 0) + 1
                session_analytic.additional_metadata[
                    'page_visits'
                ] = page_visits

                # Track endpoint history
                endpoints = session_analytic.additional_metadata.get(
                    'endpoints', []
                )
                endpoints.append({
                    'path': path,
                    'method': http_method,
                    'timestamp': now.isoformat()
                })
                # Keep only last 50 endpoints to avoid bloating
                session_analytic.additional_metadata[
                    'endpoints'
                ] = endpoints[-50:]

        # Update session expiration if provided
        if session_data.get('expires_at'):
            session_analytic.expires_at = session_data['expires_at']

        # Save the updated record
        session_analytic.save()

        # Update average renewal time if we have renewals
        if event_type in ['renewed', 'smart_renewal']:
            # Fetch fresh data for calculations since we used F() objects
            session_analytic.refresh_from_db()
            if session_analytic.renewal_count > 0:
                session_analytic.avg_renewal_time_ms = (
                    session_analytic.total_renewal_time_ms /
                    session_analytic.renewal_count
                )
                session_analytic.save(update_fields=['avg_renewal_time_ms'])

        logger.debug(
            f"Updated session analytics for {session_id[:8]}... - "
            f"{event_type}"
        )
        return True

    except Exception as e:
        logger.error("Error in comprehensive session tracking: %s", e)
        return False


# Enhanced Analytics Tasks for New Models

@shared_task
def track_content_analytics(content_data):
    """
    Track content performance metrics for posts, comments, and interactions.
    """
    try:
        content_type = content_data.get('content_type')
        content_id = content_data.get('content_id')
        author_id = content_data.get('author_id')
        action = content_data.get('action', 'view')

        if not all([content_type, content_id, author_id]):
            logger.warning("Missing required fields in content analytics data")
            return False

        # Get or create content analytics record
        analytics, created = ContentAnalytics.objects.get_or_create(
            content_type=content_type,
            content_id=content_id,
            defaults={'author_id': author_id}
        )

        # Update metrics based on action
        if action == 'view':
            analytics.view_count += 1
            user_id = content_data.get('user_id')
            if user_id:
                analytics.unique_views = analytics.view_count  # Simplified

            # Update read time
            read_time = content_data.get('read_time', 0)
            if read_time > 0:
                total_time = (analytics.avg_read_time_seconds *
                             (analytics.view_count - 1) + read_time)
                analytics.avg_read_time_seconds = (
                    total_time / analytics.view_count
                )

        elif action == 'like':
            analytics.like_count += 1
        elif action == 'dislike':
            analytics.dislike_count += 1
        elif action == 'share':
            analytics.share_count += 1
        elif action == 'comment':
            analytics.comment_count += 1
        elif action == 'reply':
            analytics.reply_count += 1

        # Update engagement rate
        if analytics.view_count > 0:
            total_engagement = (
                analytics.like_count + analytics.comment_count +
                analytics.share_count + analytics.reply_count
            )
            analytics.engagement_rate = (
                (total_engagement / analytics.view_count) * 100
            )

        # Update first engagement time
        if not analytics.first_engagement_at and action != 'view':
            analytics.first_engagement_at = timezone.now()

        # Calculate engagement velocity
        if analytics.first_engagement_at:
            time_diff = timezone.now() - analytics.first_engagement_at
            hours_since_first = time_diff.total_seconds() / 3600
            if hours_since_first > 0:
                total_engagements = (
                    analytics.like_count + analytics.comment_count +
                    analytics.share_count + analytics.reply_count
                )
                analytics.engagement_velocity = (
                    total_engagements / hours_since_first
                )

        analytics.save()
        return True

    except Exception as e:
        logger.error("Error tracking content analytics: %s", e)
        return False


@shared_task
def track_search_analytics(search_data):
    """
    Track search queries, performance, and user interactions.
    """
    try:
        query = search_data.get('query', '').strip()
        if not query:
            return False

        # Create query hash for deduplication
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()

        # Create search analytics record
        search_analytics = SearchAnalytics.objects.create(
            query=query,
            query_hash=query_hash,
            normalized_query=query.lower().strip(),
            user_id=search_data.get('user_id'),
            session_id=search_data.get('session_id', ''),
            search_type=search_data.get('search_type', 'global'),
            filters_applied=search_data.get('filters_applied', {}),
            sort_criteria=search_data.get('sort_criteria', ''),
            total_results=search_data.get('total_results', 0),
            results_page=search_data.get('results_page', 1),
            results_per_page=search_data.get('results_per_page', 20),
            search_time_ms=search_data.get('search_time_ms', 0.0),
            database_query_time_ms=search_data.get('database_query_time_ms', 0.0),
            elasticsearch_time_ms=search_data.get('elasticsearch_time_ms'),
            clicked_results=search_data.get('clicked_results', []),
            zero_results=search_data.get('total_results', 0) == 0,
            ip_address=search_data.get('ip_address'),
            country_code=search_data.get('country_code', ''),
            device_type=search_data.get('device_type', ''),
            suggested_terms=search_data.get('suggested_terms', []),
            autocomplete_used=search_data.get('autocomplete_used', False),
            voice_search=search_data.get('voice_search', False),
        )

        # Calculate click-through rate
        clicked_results = search_data.get('clicked_results', [])
        if clicked_results and search_analytics.total_results > 0:
            results_shown = min(
                search_analytics.results_per_page,
                search_analytics.total_results
            )
            search_analytics.click_through_rate = (
                (len(clicked_results) / results_shown) * 100
            )

            # Track first click position and time
            if clicked_results:
                first_click = min(
                    clicked_results,
                    key=lambda x: x.get('position', float('inf'))
                )
                search_analytics.first_click_position = first_click.get('position')
                search_analytics.time_to_first_click_ms = first_click.get('time_ms')

        # Mark if search resulted in action
        search_analytics.resulted_in_action = search_data.get(
            'resulted_in_action', False
        )
        search_analytics.user_refined_search = search_data.get(
            'user_refined_search', False
        )

        search_analytics.save()
        return True

    except Exception as e:
        logger.error("Error tracking search analytics: %s", e)
        return False


@shared_task
def update_comprehensive_user_analytics(user_id=None):
    """
    Update comprehensive user analytics including behavioral metrics.
    """
    try:
        from django.db.models import Q

        if user_id:
            users = UserProfile.objects.filter(id=user_id, is_deleted=False)
        else:
            users = UserProfile.objects.filter(is_deleted=False)[:100]

        updated_count = 0

        for user_profile in users:
            try:
                with transaction.atomic():
                    analytics, created = UserAnalytics.objects.get_or_create(
                        user=user_profile,
                        defaults={}
                    )

                    # Update content metrics
                    user_content = ContentAnalytics.objects.filter(
                        author=user_profile, is_deleted=False
                    ).aggregate(
                        total_views=Sum('view_count'),
                        total_engagements=Sum(
                            F('like_count') + F('comment_count') + F('share_count')
                        ),
                        avg_engagement_rate=Avg('engagement_rate'),
                        total_content_pieces=Count('id')
                    )

                    # Update search metrics
                    user_searches = SearchAnalytics.objects.filter(
                        user=user_profile.user, is_deleted=False
                    ).aggregate(
                        total_searches=Count('id'),
                        successful_searches=Count(
                            'id', filter=~Q(zero_results=True)
                        ),
                        avg_ctr=Avg('click_through_rate')
                    )

                    # Update analytics fields
                    analytics.total_searches = (
                        user_searches['total_searches'] or 0
                    )
                    analytics.successful_searches = (
                        user_searches['successful_searches'] or 0
                    )

                    # Calculate engagement score
                    total_engagements = user_content['total_engagements'] or 0
                    total_views = user_content['total_views'] or 0
                    if total_views > 0:
                        analytics.engagement_score = (
                            (total_engagements / total_views) * 100
                        )
                    else:
                        analytics.engagement_score = 0.0

                    # Calculate reputation score
                    content_pieces = user_content['total_content_pieces'] or 0
                    content_score = min(content_pieces / 10, 1.0) * 25
                    engagement_score = min(
                        analytics.engagement_score / 100, 1.0
                    ) * 25
                    analytics.reputation_score = (
                        content_score + engagement_score
                    )

                    # Update activity level
                    activity_score = (
                        analytics.engagement_score + (analytics.total_searches / 10)
                    )
                    if activity_score >= 80:
                        analytics.activity_level = 'very_high'
                    elif activity_score >= 60:
                        analytics.activity_level = 'high'
                    elif activity_score >= 40:
                        analytics.activity_level = 'medium'
                    elif activity_score >= 20:
                        analytics.activity_level = 'low'
                    else:
                        analytics.activity_level = 'very_low'

                    # Calculate days since registration
                    registration_date = user_profile.user.date_joined.date()
                    today = timezone.now().date()
                    analytics.days_since_registration = (
                        (today - registration_date).days
                    )

                    analytics.last_activity_date = timezone.now()
                    analytics.save()
                    updated_count += 1

            except Exception as e:
                logger.error(
                    "Error updating analytics for user %s: %s",
                    user_profile.id, e
                )
                continue

        logger.info("Updated comprehensive analytics for %d users", updated_count)
        return updated_count

    except Exception as e:
        logger.error("Error in comprehensive user analytics update: %s", e)
        return 0


@shared_task
def generate_comprehensive_analytics_reports():
    """
    Generate comprehensive analytics reports across all models.
    """
    try:
        today = timezone.now().date()

        # Content analytics summary
        content_summary = ContentAnalytics.objects.filter(
            created_at__date=today, is_deleted=False
        ).aggregate(
            total_content=Count('id'),
            total_views=Sum('view_count'),
            total_engagements=Sum(
                F('like_count') + F('comment_count') + F('share_count')
            ),
            avg_engagement_rate=Avg('engagement_rate'),
        )

        # Search analytics summary
        search_summary = SearchAnalytics.objects.filter(
            searched_at__date=today, is_deleted=False
        ).aggregate(
            total_searches=Count('id'),
            zero_result_searches=Count('id', filter=Q(zero_results=True)),
            avg_search_time=Avg('search_time_ms'),
            avg_ctr=Avg('click_through_rate')
        )

        # Create daily analytics record
        daily_analytics, created = DailyAnalytics.objects.get_or_create(
            date=today,
            defaults={
                'total_interactions': (content_summary['total_engagements'] or 0),
                'avg_response_time': search_summary['avg_search_time'] or 0.0,
            }
        )

        daily_analytics.new_posts = content_summary['total_content'] or 0
        daily_analytics.total_likes = content_summary['total_engagements'] or 0
        daily_analytics.save()

        # Store insights
        insights = {
            'date': today.isoformat(),
            'content_performance': {
                'total_content_pieces': content_summary['total_content'],
                'total_views': content_summary['total_views'],
                'avg_engagement_rate': content_summary['avg_engagement_rate'],
            },
            'search_performance': {
                'total_searches': search_summary['total_searches'],
                'zero_result_rate': (
                    (search_summary['zero_result_searches'] or 0) /
                    max(search_summary['total_searches'] or 1, 1)
                ) * 100,
                'avg_response_time': search_summary['avg_search_time'],
            }
        }

        SystemMetric.objects.create(
            metric_type='daily_insights',
            value=0,
            additional_data=insights
        )

        logger.info("Generated comprehensive analytics report for %s", today)
        return f"Generated analytics report for {today}"

    except Exception as e:
        logger.error("Error generating analytics reports: %s", e)
        return f"Error: {str(e)}"


@shared_task
def cleanup_comprehensive_analytics():
    """
    Clean up old analytics data with retention policies.
    """
    try:
        now = timezone.now()

        # Content analytics: Keep 90 days
        content_cutoff = now - timedelta(days=90)
        old_content = ContentAnalytics.objects.filter(
            created_at__lt=content_cutoff, is_deleted=False
        )
        content_count = old_content.count()
        old_content.update(is_deleted=True, deleted_at=now)

        # Search analytics: Keep 30 days
        search_cutoff = now - timedelta(days=30)
        old_searches = SearchAnalytics.objects.filter(
            searched_at__lt=search_cutoff, is_deleted=False
        )
        search_count = old_searches.count()
        old_searches.update(is_deleted=True, deleted_at=now)

        logger.info(
            "Cleaned up %d content,  %d search analytics records",
            content_count, search_count
        )

        return (
            f"Cleaned up {content_count + search_count} "
            "analytics records"
        )

    except Exception as e:
        logger.error("Error cleaning up comprehensive analytics: %s", e)
        return f"Error: {str(e)}"


# === PostSee Analytics Integration ===

@shared_task
def track_post_view(post_see_data):
    """
    Track detailed post view from PostSee data and update analytics.

    Args:
        post_see_data (dict): PostSee tracking data including:
            - post_see_id: PostSee UUID
            - post_id: Post UUID
            - user_id: UserProfile UUID
            - view_duration_seconds: Time spent viewing
            - scroll_percentage: How much was scrolled
            - source: Where the view came from
            - device_type: Device used
            - is_engaged: Whether user engaged
    """
    try:

        post_see_id = post_see_data.get('post_see_id')
        post_id = post_see_data.get('post_id')
        user_id = post_see_data.get('user_id')

        if not all([post_see_id, post_id]):
            logger.warning("Missing required fields in post view data")
            return False

        # Get the PostSee object
        try:
            post_see = PostSee.objects.get(id=post_see_id)
        except PostSee.DoesNotExist:
            logger.warning("PostSee object not found: %s", post_see_id)
            return False

        # Get the Post object
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            logger.warning("Post object not found: %s", post_id)
            return False

        # Update ContentAnalytics
        analytics, created = ContentAnalytics.objects.get_or_create(
            content_type='post',
            content_id=post_id,
            defaults={'author_id': post.author.id}
        )

        # Update view metrics
        analytics.view_count += 1

        # Update unique views (simple implementation)
        if user_id:
            # Check if this user has viewed before
            previous_views = PostSee.objects.filter(
                post=post, user_id=user_id
            ).exclude(id=post_see_id).exists()

            if not previous_views:
                analytics.unique_views += 1

        # Update read time from PostSee data
        view_duration = post_see_data.get('view_duration_seconds', 0)
        if view_duration > 0:
            total_time = (analytics.avg_read_time_seconds *
                         (analytics.view_count - 1) + view_duration)
            analytics.avg_read_time_seconds = total_time / analytics.view_count

        # Update engagement metrics
        is_engaged = post_see_data.get('is_engaged', False)
        if not is_engaged:
            # Calculate bounce rate (views without engagement)
            total_views = analytics.view_count
            engaged_views = PostSee.objects.filter(
                post=post, is_engaged=True
            ).count()
            analytics.bounce_rate = ((total_views - engaged_views) / total_views) * 100

        # Update quality score based on scroll percentage and duration
        scroll_percentage = post_see_data.get('scroll_percentage', 0)
        if scroll_percentage > 0:
            # Factor in scroll depth and time for quality
            quality_factor = (scroll_percentage / 100) * min(view_duration / 30, 1)
            current_quality = analytics.quality_score or 0
            view_count = analytics.view_count
            analytics.quality_score = (
                (current_quality * (view_count - 1) + quality_factor * 100) / view_count
            )

        analytics.save()

        # Track content analytics with enhanced data
        content_analytics_data = {
            'content_type': 'post',
            'content_id': str(post_id),
            'author_id': str(post.author.id),
            'action': 'view',
            'user_id': str(user_id) if user_id else None,
            'read_time': view_duration,
            'scroll_percentage': scroll_percentage,
            'source': post_see_data.get('source', 'unknown'),
            'device_type': post_see_data.get('device_type', 'unknown'),
            'session_id': post_see_data.get('session_id', ''),
            'ip_address': post_see_data.get('ip_address'),
        }

        # Call existing content analytics tracking
        track_content_analytics.delay(content_analytics_data)

        return True

    except Exception as e:
        logger.error("Error tracking post view: %s", e)
        return False


@shared_task
def sync_postsee_analytics():
    """
    Sync PostSee data with ContentAnalytics for comprehensive reporting.
    Runs periodically to ensure analytics are up to date.
    """
    try:

        from django.db.models import Avg, Count,  Max

        # Get posts that have PostSee data but may need analytics update
        posts_with_views = Post.objects.filter(
            sees__isnull=False
        ).distinct()

        updated_count = 0

        for post in posts_with_views:
            try:
                # Get or create analytics for this post
                analytics, created = ContentAnalytics.objects.get_or_create(
                    content_type='post',
                    content_id=post.id,
                    defaults={'author_id': post.author.id}
                )

                # Aggregate PostSee data
                post_see_stats = PostSee.objects.filter(post=post).aggregate(
                    total_views=Count('id'),
                    unique_users=Count('user', distinct=True),
                    avg_duration=Avg('view_duration_seconds'),
                    avg_scroll=Avg('scroll_percentage'),
                    engaged_views=Count('id', filter=Q(is_engaged=True)),
                    max_duration=Max('view_duration_seconds'),
                )

                # Update analytics with PostSee data
                analytics.view_count = post_see_stats['total_views'] or 0
                analytics.unique_views = post_see_stats['unique_users'] or 0
                analytics.avg_read_time_seconds = post_see_stats['avg_duration'] or 0.0

                # Calculate bounce rate
                total_views = post_see_stats['total_views'] or 1
                engaged_views = post_see_stats['engaged_views'] or 0
                analytics.bounce_rate = ((total_views - engaged_views) / total_views) * 100

                # Calculate quality score based on engagement and scroll depth
                avg_scroll = post_see_stats['avg_scroll'] or 0
                max_duration = post_see_stats['max_duration'] or 0
                engagement_factor = engaged_views / total_views if total_views > 0 else 0
                scroll_factor = min(avg_scroll / 100, 1.0)
                duration_factor = min(max_duration / 60, 1.0)  # Cap at 1 minute

                analytics.quality_score = (
                    (engagement_factor * 40) +
                    (scroll_factor * 35) +
                    (duration_factor * 25)
                )

                # Update engagement rate if we have like/comment data
                if hasattr(post, 'likes') and hasattr(post, 'comments'):
                    total_engagement = (
                        post.likes.count() +
                        post.comments.count() +
                        analytics.share_count
                    )
                    if analytics.view_count > 0:
                        analytics.engagement_rate = (
                            (total_engagement / analytics.view_count) * 100
                        )

                analytics.save()
                updated_count += 1

            except Exception as e:
                logger.error("Error syncing analytics for post %s: %s", post.id, e)
                continue

        logger.info("Synced PostSee analytics for %d posts", updated_count)
        return updated_count

    except Exception as e:
        logger.error("Error in PostSee analytics sync: %s", e)
        return 0


@shared_task
def generate_post_view_insights():
    """
    Generate insights from PostSee data for analytics dashboard.
    Creates summary reports of viewing patterns and engagement.
    """
    try:

        from django.utils import timezone

        today = timezone.now().date()

        # Daily PostSee summary
        daily_views = PostSee.objects.filter(
            seen_at__date=today
        ).aggregate(
            total_views=Count('id'),
            unique_viewers=Count('user', distinct=True),
            unique_posts=Count('post', distinct=True),
            avg_duration=Avg('view_duration_seconds'),
            avg_scroll=Avg('scroll_percentage'),
            engaged_views=Count('id', filter=Q(is_engaged=True)),
        )

        # Source breakdown
        source_breakdown = PostSee.objects.filter(
            seen_at__date=today
        ).values('source').annotate(
            count=Count('id'),
            avg_duration=Avg('view_duration_seconds'),
            engagement_rate=Count('id', filter=Q(is_engaged=True)) * 100.0 / Count('id')
        ).order_by('-count')

        # Device breakdown
        device_breakdown = PostSee.objects.filter(
            seen_at__date=today
        ).values('device_type').annotate(
            count=Count('id'),
            avg_duration=Avg('view_duration_seconds'),
            engagement_rate=Count('id', filter=Q(is_engaged=True)) * 100.0 / Count('id')
        ).order_by('-count')

        # Top performing posts by engagement
        top_posts = PostSee.objects.filter(
            seen_at__date=today
        ).values('post_id').annotate(
            total_views=Count('id'),
            unique_viewers=Count('user', distinct=True),
            avg_duration=Avg('view_duration_seconds'),
            engagement_rate=Count('id', filter=Q(is_engaged=True)) * 100.0 / Count('id')
        ).order_by('-engagement_rate')[:10]

        # Create insights summary
        insights = {
            'date': today.isoformat(),
            'summary': daily_views,
            'source_breakdown': list(source_breakdown),
            'device_breakdown': list(device_breakdown),
            'top_posts': list(top_posts),
            'metrics': {
                'overall_engagement_rate': (
                    (daily_views['engaged_views'] or 0) /
                    max(daily_views['total_views'] or 1, 1)
                ) * 100,
                'average_view_duration': daily_views['avg_duration'] or 0,
                'average_scroll_depth': daily_views['avg_scroll'] or 0,
            }
        }

        # Store insights
        SystemMetric.objects.create(
            metric_type='post_view_insights',
            value=daily_views['total_views'] or 0,
            additional_data=insights
        )

        logger.info("Generated post view insights for %s", today)
        return f"Generated insights for {daily_views['total_views']} views"

    except Exception as e:
        logger.error("Error generating post view insights: %s", e)
        return f"Error: {str(e)}"


@shared_task
def cleanup_old_postsee_data():
    """
    Clean up old PostSee data based on retention policy.
    Keeps detailed view data for 30 days, aggregated data longer.
    """
    try:

        now = timezone.now()

        # Keep PostSee data for 30 days
        cutoff_date = now - timedelta(days=30)

        old_views = PostSee.objects.filter(seen_at__lt=cutoff_date)
        count = old_views.count()

        # Before deletion, ensure analytics are synced
        sync_postsee_analytics.delay()

        # Delete old PostSee records
        old_views.delete()

        logger.info("Cleaned up %d old PostSee records", count)
        return f"Cleaned up {count} old PostSee records"

    except Exception as e:
        logger.error("Error cleaning up PostSee data: %s", e)
        return f"Error: {str(e)}"


@shared_task
def track_page_view(user_id, page_url=None, referrer=None, session_id=None):
    """
    Track a page view for analytics.

    Args:
        user_id: UUID string of the user
        page_url: The page URL that was viewed (optional)
        referrer: The referrer URL (optional)
        session_id: Session identifier (optional)
    """
    try:
        from accounts.models import UserProfile
        from analytics.models import UserAnalytics

        # Get user profile
        user_profile = UserProfile.objects.get(id=user_id)

        # Increment page views
        analytics = UserAnalytics.increment_user_page_views(
            user_profile, count=1
        )

        # Optional: Log page view details for more detailed tracking
        logger.info(
            f"Page view tracked for user {user_profile.user.username}: "
            f"total_views={analytics.total_page_views}"
        )

        return {
            'success': True,
            'user_id': str(user_id),
            'total_page_views': analytics.total_page_views,
            'page_url': page_url,
        }

    except UserProfile.DoesNotExist:
        logger.warning(
            f"User profile not found for page view tracking: {user_id}"
        )
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error tracking page view for user {user_id}: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def persist_anonymous_session(device_fingerprint, session_data):
    """
    Persist anonymous session data from Redis to database.

    This task is triggered every 5th page view to save anonymous
    session tracking data to the database, reducing DB writes while
    maintaining data integrity.

    Args:
        device_fingerprint: Unique device identifier
        session_data: Dictionary containing session information from Redis
    """
    try:
        from datetime import datetime
        import json

        # Parse dates from ISO format
        session_start = datetime.fromisoformat(
            session_data.get('session_start')
        )
        last_activity = datetime.fromisoformat(
            session_data.get('last_activity')
        )

        # Get or create AnonymousSession
        session, created = AnonymousSession.objects.get_or_create(
            device_fingerprint=device_fingerprint,
            session_start=session_start,
            defaults={
                'last_activity': last_activity,
                'pages_visited': int(session_data.get('pages_visited', 0)),
                'landing_page': session_data.get('landing_page', ''),
                'exit_page': session_data.get('exit_page', ''),
                'referrer': session_data.get('referrer', ''),
                'utm_source': session_data.get('utm_source', ''),
                'utm_medium': session_data.get('utm_medium', ''),
                'utm_campaign': session_data.get('utm_campaign', ''),
                'utm_term': session_data.get('utm_term', ''),
                'utm_content': session_data.get('utm_content', ''),
                'ip_address': session_data.get('ip_address', ''),
                'user_agent': session_data.get('user_agent', ''),
                'device_type': session_data.get('device_type', 'unknown'),
                'browser': session_data.get('browser', 'Unknown'),
                'os': session_data.get('os', 'Unknown'),
                'session_ended': False,
            }
        )

        # Update existing session
        if not created:
            session.last_activity = last_activity
            session.pages_visited = int(session_data.get('pages_visited', 0))
            session.exit_page = session_data.get('exit_page', '')
            session.save(update_fields=[
                'last_activity', 'pages_visited', 'exit_page'
            ])

        # Parse and save page views
        page_views_json = session_data.get('page_views', '[]')
        page_views = json.loads(page_views_json)

        # Track which page views we've already persisted
        existing_urls = set(
            AnonymousPageView.objects.filter(
                session=session
            ).values_list('page_url', flat=True)
        )

        # Create new page view records (avoid duplicates)
        new_page_views = []
        for page_view in page_views:
            page_url = page_view.get('page_url', '')

            # Skip if already persisted
            if page_url in existing_urls:
                continue

            # Parse timestamp
            viewed_at = datetime.fromisoformat(
                page_view.get('viewed_at')
            )

            new_page_views.append(
                AnonymousPageView(
                    session=session,
                    page_url=page_url,
                    page_type=page_view.get('page_type', 'other'),
                    viewed_at=viewed_at,
                    time_spent_seconds=page_view.get(
                        'time_spent_seconds', 0
                    ),
                    referrer_url=page_view.get('referrer_url', '')
                )
            )

        # Bulk create new page views
        if new_page_views:
            AnonymousPageView.objects.bulk_create(
                new_page_views,
                ignore_conflicts=True
            )

        # Update PageAnalytics for each unique page
        unique_pages = set(pv.get('page_url') for pv in page_views)
        for page_url in unique_pages:
            analytics, _ = PageAnalytics.objects.get_or_create(
                page_url=page_url,
                date=last_activity.date()
            )
            analytics.anonymous_views += 1
            analytics.save(update_fields=['anonymous_views'])

        logger.info(
            f"Persisted anonymous session {device_fingerprint}: "
            f"{len(new_page_views)} new page views, "
            f"{session.pages_visited} total pages"
        )


        return {
            'success': True,
            'session_id': str(session.id),
            'device_fingerprint': device_fingerprint,
            'new_page_views': len(new_page_views),
            'total_pages': session.pages_visited,
        }

    except Exception as e:
        logger.error(
            f"Error persisting anonymous session "
            f"{device_fingerprint}: {e}",
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e),
            'device_fingerprint': device_fingerprint
        }


@shared_task
def track_anonymous_page_view_async(page_view_data):
    """
    Async task to track anonymous page views in Redis (NON-BLOCKING).

    This task is called from middleware to avoid blocking HTTP responses
    with Redis operations. All Redis I/O happens here in the background.

    Args:
        page_view_data: Dictionary containing:
            - device_fingerprint
            - current_url
            - page_type
            - ip_address
            - user_agent
            - device_type
            - referrer
            - utm_params (dict)
    """
    try:
        import redis
        import json
        from datetime import datetime
        from django.conf import settings

        device_fingerprint = page_view_data['device_fingerprint']

        # Connect to Redis with connection pooling
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=2,  # 2 second timeout
            socket_timeout=2,
        )

        # Redis key for anonymous session
        session_key = f"anon_session:{device_fingerprint}"

        # Get current session data or create new
        session_data = redis_client.hgetall(session_key)

        if not session_data:
            # New anonymous session
            session_data = {
                'device_fingerprint': device_fingerprint,
                'session_start': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'pages_visited': '0',
                'landing_page': page_view_data['current_url'],
                'referrer': page_view_data['referrer'],
                'ip_address': page_view_data['ip_address'],
                'user_agent': page_view_data['user_agent'],
                'device_type': page_view_data['device_type'],
                'browser': _extract_browser(page_view_data['user_agent']),
                'os': _extract_os(page_view_data['user_agent']),
                'page_views': json.dumps([]),
            }

            # Add UTM parameters if present
            utm_params = page_view_data.get('utm_params')
            if utm_params:
                session_data.update(utm_params)

            logger.info(
                f"Created new anonymous session for "
                f"fingerprint {device_fingerprint[:16]}..."
            )
        else:
            # Update existing session
            session_data['last_activity'] = datetime.now().isoformat()

        # Increment pages visited
        pages_visited = int(session_data.get('pages_visited', 0))
        pages_visited += 1
        session_data['pages_visited'] = str(pages_visited)

        # Update exit page
        session_data['exit_page'] = page_view_data['current_url']

        # Add page view to list
        page_views = json.loads(session_data.get('page_views', '[]'))
        page_view_entry = {
            'url': page_view_data['current_url'],
            'page_type': page_view_data['page_type'],
            'viewed_at': datetime.now().isoformat(),
            'referrer': page_view_data['referrer']
        }
        page_views.append(page_view_entry)
        session_data['page_views'] = json.dumps(page_views)

        # Save to Redis with 30-minute TTL
        redis_client.hset(session_key, mapping=session_data)
        redis_client.expire(session_key, 1800)  # 30 minutes

        logger.debug(
            f"Updated anonymous session "
            f"{device_fingerprint[:16]}...: "
            f"{pages_visited} pages visited"
        )

        # Persist to database every 5th page view
        if pages_visited % 5 == 0:
            logger.info(
                f"Triggering DB persistence for anonymous session "
                f"{device_fingerprint[:16]}... "
                f"(page {pages_visited})"
            )
            persist_anonymous_session.delay(
                device_fingerprint,
                session_data
            )

    except redis.ConnectionError as e:
        logger.error(
            f"Redis connection error tracking anonymous page view: {e}"
        )
    except Exception as e:
        logger.error(f"Error tracking anonymous page view async: {e}")


def _extract_browser(user_agent):
    """Extract browser name from user agent string."""
    ua_lower = user_agent.lower()
    if 'chrome' in ua_lower:
        return 'Chrome'
    elif 'firefox' in ua_lower:
        return 'Firefox'
    elif 'safari' in ua_lower:
        return 'Safari'
    elif 'edge' in ua_lower:
        return 'Edge'
    elif 'opera' in ua_lower:
        return 'Opera'
    else:
        return 'Unknown'


def _extract_os(user_agent):
    """Extract operating system from user agent string."""
    ua_lower = user_agent.lower()
    if 'windows' in ua_lower:
        return 'Windows'
    elif 'mac' in ua_lower:
        return 'macOS'
    elif 'linux' in ua_lower:
        return 'Linux'
    elif 'android' in ua_lower:
        return 'Android'
    elif 'iphone' in ua_lower or 'ipad' in ua_lower:
        return 'iOS'
    else:
        return 'Unknown'


@shared_task
def finalize_anonymous_session(device_fingerprint):
    """
    Mark an anonymous session as ended when Redis session expires.

    This task is triggered when a Redis session reaches its TTL (30 min
    of inactivity) to properly close the session in the database.

    Args:
        device_fingerprint: Unique device identifier
    """
    try:
        from django.utils import timezone

        # Find the most recent active session for this fingerprint
        session = AnonymousSession.objects.filter(
            device_fingerprint=device_fingerprint,
            session_ended=False
        ).order_by('-last_activity').first()

        if not session:
            logger.warning(
                f"No active session found to finalize for "
                f"fingerprint: {device_fingerprint}"
            )
            return {'success': False, 'error': 'Session not found'}

        # Mark session as ended
        session.session_ended = True
        session.ended_at = timezone.now()
        session.save(update_fields=['session_ended', 'ended_at'])

        # Calculate session duration
        duration = (session.ended_at - session.session_start).total_seconds()

        logger.info(
            f"Finalized anonymous session {session.id}: "
            f"{session.pages_visited} pages, {duration:.1f}s duration"
        )

        return {
            'success': True,
            'session_id': str(session.id),
            'device_fingerprint': device_fingerprint,
            'pages_visited': session.pages_visited,
            'duration_seconds': duration,
        }

    except Exception as e:
        logger.error(
            f"Error finalizing anonymous session "
            f"{device_fingerprint}: {e}",
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e),
            'device_fingerprint': device_fingerprint
        }


@shared_task
def cleanup_old_anonymous_data():
    """
    Delete old anonymous session data based on retention policy.

    Removes:
    - AnonymousSessions older than 90 days
    - AnonymousPageViews associated with deleted sessions

    This task should run daily via Celery Beat.
    """
    try:
        from django.utils import timezone

        # Calculate cutoff date (90 days ago)
        cutoff_date = timezone.now() - timedelta(days=90)

        # Delete old sessions (CASCADE will delete related page views)
        old_sessions = AnonymousSession.objects.filter(
            session_start__lt=cutoff_date
        )

        session_count = old_sessions.count()

        # Get page view count before deletion
        page_view_count = AnonymousPageView.objects.filter(
            session__in=old_sessions
        ).count()

        # Delete sessions (cascades to page views)
        old_sessions.delete()

        logger.info(
            f"Cleaned up {session_count} anonymous sessions "
            f"and {page_view_count} page views older than 90 days"
        )

        return {
            'success': True,
            'deleted_sessions': session_count,
            'deleted_page_views': page_view_count,
            'cutoff_date': cutoff_date.isoformat(),
        }

    except Exception as e:
        logger.error(
            f"Error cleaning up anonymous data: {e}",
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def sync_community_analytics_from_redis():
    """
    Sync CommunityAnalytics from Redis anonymous visitor data.

    Reads current anonymous visitor counts from Redis and updates
    CommunityAnalytics to reflect real-time visitor statistics.

    This task should run every 30 seconds via Celery Beat.
    """
    try:
        from django.utils import timezone
        from django_redis import get_redis_connection
        import re

        # Get all Redis keys for anonymous community visitors
        # Pattern: anon_visitor:{community_id}:{device_fingerprint}
        visitor_pattern = 'anon_visitor:*'

        # Group visitor fingerprints by community
        community_visitors = {}

        # Get Redis connection properly
        try:
            redis_client = get_redis_connection('default')
        except Exception as e:
            print(f"Could not get Redis connection: {e}")
            return {'success': False, 'error': str(e)}

        cursor = 0
        while True:
            cursor, keys = redis_client.scan(
                cursor=cursor,
                match=visitor_pattern,
                count=100
            )

            for key in keys:
                # Extract community_id from key
                # Format: anon_visitor:{community_id}:{fingerprint}
                match = re.match(
                    r'anon_visitor:([^:]+):([^:]+)',
                    key.decode('utf-8')
                )
                if match:
                    community_id = match.group(1)
                    fingerprint = match.group(2)

                    if community_id not in community_visitors:
                        community_visitors[community_id] = set()

                    community_visitors[community_id].add(fingerprint)

            if cursor == 0:
                break

        # Update CommunityAnalytics for each community
        updated_count = 0
        today = timezone.now().date()

        for community_id, fingerprints in community_visitors.items():
            try:
                from communities.models import Community

                # Verify community exists
                community = Community.objects.get(
                    id=community_id,
                    is_deleted=False
                )

                # Get or create analytics for today
                analytics, _ = CommunityAnalytics.objects.get_or_create(
                    community=community,
                    date=today
                )

                # Update anonymous visitor count
                analytics.anonymous_visitors_today = len(fingerprints)
                analytics.save(update_fields=['anonymous_visitors_today'])

                updated_count += 1

            except Community.DoesNotExist:
                logger.warning(
                    f"Community {community_id} not found, "
                    "skipping analytics update"
                )
                continue
            except Exception as e:
                logger.error(
                    f"Error updating analytics for community "
                    f"{community_id}: {e}"
                )
                continue

        logger.info(
            f"Synced anonymous visitor data for {updated_count} "
            "communities from Redis"
        )

        return {
            'success': True,
            'communities_updated': updated_count,
            'total_communities_tracked': len(community_visitors),
        }

    except Exception as e:
        logger.error(
            f"Error syncing community analytics from Redis: {e}",
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def track_anonymous_conversion(device_fingerprint, user_id, conversion_page):
    """
    Track anonymous-to-authenticated user conversion.

    Links an anonymous session to a registered user and updates
    conversion metrics in PageAnalytics.

    Args:
        device_fingerprint: Device fingerprint of the anonymous user
        user_id: UUID of the newly registered/verified user
        conversion_page: URL where conversion happened (usually /verify)
    """
    try:
        from django.utils import timezone
        from accounts.models import UserProfile

        # Find the most recent active anonymous session
        session = AnonymousSession.objects.filter(
            device_fingerprint=device_fingerprint,
            session_ended=False
        ).order_by('-last_activity').first()

        if not session:
            logger.warning(
                f"No active anonymous session found for conversion "
                f"tracking: {device_fingerprint}"
            )
            return {'success': False, 'error': 'No session found'}

        # Get user profile
        try:
            user_profile = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            logger.error(f"User profile not found: {user_id}")
            return {'success': False, 'error': 'User not found'}

        # Link session to user (if not already linked)
        if not session.converted_user:
            session.converted_user = user_profile
            session.converted_at = timezone.now()
            session.save(update_fields=['converted_user', 'converted_at'])

        # Update PageAnalytics for all pages visited in this session
        page_views = AnonymousPageView.objects.filter(session=session)

        conversion_date = timezone.now().date()
        pages_updated = 0

        for page_view in page_views:
            analytics, _ = PageAnalytics.objects.get_or_create(
                page_url=page_view.page_url,
                date=conversion_date
            )

            # Increment conversion count
            analytics.anonymous_to_auth_conversions += 1
            analytics.save(update_fields=['anonymous_to_auth_conversions'])
            pages_updated += 1

        # Update conversion page specifically
        conversion_analytics, _ = PageAnalytics.objects.get_or_create(
            page_url=conversion_page,
            date=conversion_date
        )
        conversion_analytics.anonymous_to_auth_conversions += 1
        conversion_analytics.save(
            update_fields=['anonymous_to_auth_conversions']
        )

        logger.info(
            f"Tracked conversion for session {session.id}: "
            f"user={user_id}, pages_updated={pages_updated}"
        )

        return {
            'success': True,
            'session_id': str(session.id),
            'user_id': user_id,
            'device_fingerprint': device_fingerprint,
            'pages_updated': pages_updated,
            'session_duration': (
                session.last_activity - session.session_start
            ).total_seconds(),
        }

    except Exception as e:
        logger.error(
            f"Error tracking conversion for {device_fingerprint}: {e}",
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e),
            'device_fingerprint': device_fingerprint
        }


