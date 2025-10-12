"""
Visitor Analytics Utility Functions

Helper functions for retrieving and analyzing visitor data including:
- Unique visitor counts (authenticated & anonymous)
- Division-level breakdowns
- Time-based filtering and aggregation
- Conversion metrics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from django.utils import timezone
from django.db.models import Q, Count, Avg, F

from analytics.models import (
    AnonymousSession,
    AnonymousPageView,
    PageAnalytics
)
from accounts.models import UserEvent

logger = logging.getLogger(__name__)


class VisitorAnalytics:
    """Main class for visitor analytics utilities."""

    @staticmethod
    def get_unique_visitors(
        community_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_anonymous: bool = True,
        include_authenticated: bool = True
    ) -> Dict[str, Any]:
        """
        Get unique visitor count for a community within a date range.

        Args:
            community_id: UUID of the community
            start_date: Start of date range (default: today)
            end_date: End of date range (default: today)
            include_anonymous: Include anonymous visitors
            include_authenticated: Include authenticated visitors

        Returns:
            Dictionary with visitor counts and breakdown
        """
        try:
            # Default to today if no dates provided
            if not start_date:
                start_date = timezone.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            if not end_date:
                end_date = timezone.now()

            result = {
                'community_id': community_id,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'authenticated_visitors': 0,
                'anonymous_visitors': 0,
                'total_unique_visitors': 0,
            }

            # Get authenticated visitors from UserEvent
            if include_authenticated:
                auth_visitors = UserEvent.objects.filter(
                    event_type='community_visit',
                    metadata__community_id=community_id,
                    created_at__gte=start_date,
                    created_at__lte=end_date
                ).values('user').distinct().count()

                result['authenticated_visitors'] = auth_visitors

            # Get anonymous visitors from Redis or database
            if include_anonymous:
                anon_count = VisitorAnalytics._get_anonymous_visitor_count(
                    community_id,
                    start_date,
                    end_date
                )
                result['anonymous_visitors'] = anon_count

            # Total unique (note: may have overlap if user was anon then auth)
            result['total_unique_visitors'] = (
                result['authenticated_visitors'] +
                result['anonymous_visitors']
            )

            return result

        except Exception as e:
            logger.error(
                f"Error getting unique visitors for community "
                f"{community_id}: {e}"
            )
            return {
                'error': str(e),
                'community_id': community_id
            }

    @staticmethod
    def _get_anonymous_visitor_count(
        community_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Get anonymous visitor count from Redis with DB fallback."""
        try:
            # For historical date ranges, always use database
            # Redis only tracks current/recent visitors
            # Count unique device fingerprints visiting community pages
            from communities.models import Community

            try:
                community = Community.objects.get(
                    id=community_id,
                    is_deleted=False
                )
            except Community.DoesNotExist:
                return 0

            # Get anonymous sessions that visited community pages
            community_url_pattern = f"/communities/{community.slug}"

            anon_visitors = AnonymousPageView.objects.filter(
                url__contains=community_url_pattern,
                viewed_at__gte=start_date,
                viewed_at__lte=end_date
            ).values('session__device_fingerprint').distinct().count()

            return anon_visitors

        except Exception as e:
            logger.error(
                f"Error getting anonymous visitor count: {e}"
            )
            return 0

    @staticmethod
    def _get_redis_anonymous_count(community_id: str) -> Optional[int]:
        """Get current anonymous visitor count from Redis."""
        try:
            import redis
            from django.conf import settings

            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )

            # Pattern: anon_visitor:{community_id}:{fingerprint}
            pattern = f"anon_visitor:{community_id}:*"
            cursor = 0
            fingerprints = set()

            while True:
                cursor, keys = redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )

                for key in keys:
                    # Extract fingerprint from key
                    parts = key.split(':')
                    if len(parts) >= 3:
                        fingerprints.add(parts[2])

                if cursor == 0:
                    break

            return len(fingerprints)

        except Exception as e:
            logger.debug(
                f"Redis anonymous count unavailable: {e}"
            )
            return None

    @staticmethod
    def get_division_breakdown(
        community_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get visitor breakdown by division for a community.

        Args:
            community_id: UUID of the community
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dictionary with division-level visitor data
        """
        try:
            if not start_date:
                start_date = timezone.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            if not end_date:
                end_date = timezone.now()

            # Get community division
            from communities.models import Community

            try:
                community = Community.objects.select_related(
                    'division'
                ).get(id=community_id, is_deleted=False)
            except Community.DoesNotExist:
                return {'error': 'Community not found'}

            community_division_id = (
                str(community.division.id)
                if community.division
                else None
            )

            # Get visitor events with division data
            visitor_events = UserEvent.objects.filter(
                event_type='community_visit',
                metadata__community_id=community_id,
                created_at__gte=start_date,
                created_at__lte=end_date
            )

            # Count by division
            same_division_visitors = visitor_events.filter(
                metadata__visitor_division_id=community_division_id,
                metadata__has_key='visitor_division_id'
            ).exclude(
                metadata__visitor_division_id=None
            ).values('user').distinct().count()

            cross_division_visitors = visitor_events.filter(
                metadata__is_cross_division=True
            ).values('user').distinct().count()

            # No division: either visitor_division_id is None or not present
            no_division_visitors = visitor_events.filter(
                metadata__visitor_division_id=None
            ).values('user').distinct().count()

            # Get anonymous visitors (no division tracking)
            anon_count = VisitorAnalytics._get_anonymous_visitor_count(
                community_id,
                start_date,
                end_date
            )

            return {
                'community_id': community_id,
                'community_division_id': community_division_id,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'breakdown': {
                    'same_division': same_division_visitors,
                    'cross_division': cross_division_visitors,
                    'no_division': no_division_visitors,
                    'anonymous': anon_count,
                },
                'total_visitors': (
                    same_division_visitors +
                    cross_division_visitors +
                    no_division_visitors +
                    anon_count
                ),
            }

        except Exception as e:
            logger.error(
                f"Error getting division breakdown for "
                f"community {community_id}: {e}"
            )
            return {'error': str(e)}

    @staticmethod
    def get_visitor_trends(
        community_id: str,
        days: int = 7,
        granularity: str = 'daily'
    ) -> Dict[str, Any]:
        """
        Get visitor trends over time.

        Args:
            community_id: UUID of the community
            days: Number of days to look back
            granularity: 'hourly', 'daily', or 'weekly'

        Returns:
            Dictionary with time-series visitor data
        """
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)

            trends = []

            if granularity == 'daily':
                # Daily aggregation
                for i in range(days):
                    day_start = start_date + timedelta(days=i)
                    day_end = day_start + timedelta(days=1)

                    visitors = VisitorAnalytics.get_unique_visitors(
                        community_id,
                        day_start,
                        day_end
                    )

                    trends.append({
                        'date': day_start.date().isoformat(),
                        'authenticated': visitors.get(
                            'authenticated_visitors', 0
                        ),
                        'anonymous': visitors.get(
                            'anonymous_visitors', 0
                        ),
                        'total': visitors.get(
                            'total_unique_visitors', 0
                        ),
                    })

            elif granularity == 'hourly':
                # Hourly aggregation for last 24 hours
                hours = min(days * 24, 168)  # Max 7 days
                for i in range(hours):
                    hour_start = end_date - timedelta(hours=hours-i)
                    hour_end = hour_start + timedelta(hours=1)

                    visitors = VisitorAnalytics.get_unique_visitors(
                        community_id,
                        hour_start,
                        hour_end
                    )

                    trends.append({
                        'datetime': hour_start.isoformat(),
                        'authenticated': visitors.get(
                            'authenticated_visitors', 0
                        ),
                        'anonymous': visitors.get(
                            'anonymous_visitors', 0
                        ),
                        'total': visitors.get(
                            'total_unique_visitors', 0
                        ),
                    })

            elif granularity == 'weekly':
                # Weekly aggregation
                weeks = (days // 7) or 1
                for i in range(weeks):
                    week_start = start_date + timedelta(weeks=i)
                    week_end = week_start + timedelta(weeks=1)

                    visitors = VisitorAnalytics.get_unique_visitors(
                        community_id,
                        week_start,
                        week_end
                    )

                    trends.append({
                        'week_start': week_start.date().isoformat(),
                        'week_end': week_end.date().isoformat(),
                        'authenticated': visitors.get(
                            'authenticated_visitors', 0
                        ),
                        'anonymous': visitors.get(
                            'anonymous_visitors', 0
                        ),
                        'total': visitors.get(
                            'total_unique_visitors', 0
                        ),
                    })

            return {
                'community_id': community_id,
                'granularity': granularity,
                'days': days,
                'trends': trends,
            }

        except Exception as e:
            logger.error(
                f"Error getting visitor trends for "
                f"community {community_id}: {e}"
            )
            return {'error': str(e)}

    @staticmethod
    def get_conversion_metrics(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get anonymous-to-authenticated conversion metrics.

        Args:
            start_date: Start of date range
            end_date: End of date range
            page_url: Optional filter by specific page

        Returns:
            Dictionary with conversion metrics
        """
        try:
            if not start_date:
                start_date = timezone.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            if not end_date:
                end_date = timezone.now()

            # Get conversions from AnonymousSession
            conversions_query = AnonymousSession.objects.filter(
                converted_at__gte=start_date,
                converted_at__lte=end_date,
                converted_to_user__isnull=False
            )

            total_conversions = conversions_query.count()

            # Get anonymous sessions in same period
            total_sessions = AnonymousSession.objects.filter(
                session_start__gte=start_date,
                session_start__lte=end_date
            ).count()

            # Calculate conversion rate
            conversion_rate = (
                (total_conversions / total_sessions * 100)
                if total_sessions > 0
                else 0
            )

            # Average time to conversion
            avg_time_to_conversion = conversions_query.annotate(
                time_to_conversion=F('converted_at') - F('session_start')
            ).aggregate(
                avg_time=Avg('time_to_conversion')
            )['avg_time']

            # Average pages before conversion
            avg_pages_before_conversion = conversions_query.aggregate(
                avg_pages=Avg('pages_visited')
            )['avg_pages']

            # Top conversion pages (from landing pages of converted sessions)
            conversion_pages = []
            if total_conversions > 0:
                top_pages = conversions_query.filter(
                    landing_page__isnull=False
                ).values('landing_page').annotate(
                    conversions=Count('id')
                ).order_by('-conversions')[:10]

                conversion_pages = [
                    {
                        'page': page['landing_page'],
                        'conversions': page['conversions']
                    }
                    for page in top_pages
                ]

            return {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_conversions': total_conversions,
                'total_anonymous_sessions': total_sessions,
                'overall_conversion_rate': round(conversion_rate, 2),
                'avg_time_to_conversion_seconds': (
                    avg_time_to_conversion.total_seconds()
                    if avg_time_to_conversion
                    else None
                ),
                'avg_pages_before_conversion': (
                    round(avg_pages_before_conversion or 0, 1)
                ),
                'top_conversion_pages': conversion_pages,
            }

        except Exception as e:
            logger.error(f"Error getting conversion metrics: {e}")
            return {'error': str(e)}

    @staticmethod
    def get_visitor_demographics(
        community_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get visitor demographics (device, browser, OS).

        Args:
            community_id: UUID of the community
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dictionary with demographic breakdown
        """
        try:
            if not start_date:
                start_date = timezone.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            if not end_date:
                end_date = timezone.now()

            from communities.models import Community

            try:
                community = Community.objects.get(
                    id=community_id,
                    is_deleted=False
                )
            except Community.DoesNotExist:
                return {'error': 'Community not found'}

            # Get anonymous sessions visiting community pages
            community_url_pattern = f"/communities/{community.slug}"

            anonymous_sessions = AnonymousSession.objects.filter(
                page_views__url__contains=community_url_pattern,
                session_start__gte=start_date,
                session_start__lte=end_date
            ).distinct()

            # Device type breakdown
            device_breakdown = anonymous_sessions.values(
                'device_type'
            ).annotate(
                count=Count('id')
            ).order_by('-count')

            # Browser breakdown
            browser_breakdown = anonymous_sessions.values(
                'browser'
            ).annotate(
                count=Count('id')
            ).order_by('-count')

            # OS breakdown
            os_breakdown = anonymous_sessions.values(
                'os'
            ).annotate(
                count=Count('id')
            ).order_by('-count')

            return {
                'community_id': community_id,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_sessions': anonymous_sessions.count(),
                'device_types': list(device_breakdown),
                'browsers': list(browser_breakdown),
                'operating_systems': list(os_breakdown),
            }

        except Exception as e:
            logger.error(
                f"Error getting visitor demographics for "
                f"community {community_id}: {e}"
            )
            return {'error': str(e)}

    @staticmethod
    def get_realtime_visitors(community_id: str) -> Dict[str, Any]:
        """
        Get current real-time visitor count from Redis.

        Args:
            community_id: UUID of the community

        Returns:
            Dictionary with real-time visitor data
        """
        try:
            from communities.visitor_tracker import visitor_tracker

            # Get online count from Redis
            online_count = visitor_tracker.get_online_count(community_id)

            # Get authenticated vs anonymous breakdown
            authenticated_count = 0
            anonymous_count = 0

            try:
                import redis
                from django.conf import settings

                redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True
                )

                # Check authenticated visitors
                auth_pattern = f"visitor:{community_id}:*"
                cursor = 0

                while True:
                    cursor, keys = redis_client.scan(
                        cursor=cursor,
                        match=auth_pattern,
                        count=100
                    )
                    authenticated_count += len(keys)

                    if cursor == 0:
                        break

                # Check anonymous visitors
                anon_pattern = f"anon_visitor:{community_id}:*"
                cursor = 0

                while True:
                    cursor, keys = redis_client.scan(
                        cursor=cursor,
                        match=anon_pattern,
                        count=100
                    )
                    anonymous_count += len(keys)

                    if cursor == 0:
                        break

            except Exception as e:
                logger.debug(f"Could not get visitor breakdown: {e}")

            return {
                'community_id': community_id,
                'timestamp': timezone.now().isoformat(),
                'total_online': online_count,
                'authenticated_online': authenticated_count,
                'anonymous_online': anonymous_count,
            }

        except Exception as e:
            logger.error(
                f"Error getting realtime visitors for "
                f"community {community_id}: {e}"
            )
            return {'error': str(e)}


# Convenience functions for common use cases

def get_realtime_visitors(community_id: str) -> Dict[str, Any]:
    """Get current real-time visitor count for a community."""
    return VisitorAnalytics.get_realtime_visitors(community_id)


def get_today_visitors(community_id: str) -> Dict[str, Any]:
    """Get today's unique visitors for a community."""
    today_start = timezone.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return VisitorAnalytics.get_unique_visitors(
        community_id,
        today_start,
        timezone.now()
    )


def get_weekly_visitors(community_id: str) -> Dict[str, Any]:
    """Get this week's unique visitors for a community."""
    week_start = timezone.now() - timedelta(days=7)
    return VisitorAnalytics.get_unique_visitors(
        community_id,
        week_start,
        timezone.now()
    )


def get_monthly_visitors(community_id: str) -> Dict[str, Any]:
    """Get this month's unique visitors for a community."""
    month_start = timezone.now() - timedelta(days=30)
    return VisitorAnalytics.get_unique_visitors(
        community_id,
        month_start,
        timezone.now()
    )


def get_visitor_growth_rate(
    community_id: str,
    current_period_days: int = 7
) -> Dict[str, Any]:
    """
    Calculate visitor growth rate comparing two periods.

    Args:
        community_id: UUID of the community
        current_period_days: Number of days for current period

    Returns:
        Dictionary with growth metrics
    """
    try:
        end_date = timezone.now()
        current_start = end_date - timedelta(days=current_period_days)
        previous_start = current_start - timedelta(days=current_period_days)

        # Current period
        current_visitors = VisitorAnalytics.get_unique_visitors(
            community_id,
            current_start,
            end_date
        )

        # Previous period
        # (end just before current period starts to avoid overlap)
        previous_visitors = VisitorAnalytics.get_unique_visitors(
            community_id,
            previous_start,
            current_start - timedelta(microseconds=1)
        )

        current_total = current_visitors.get('total_unique_visitors', 0)
        previous_total = previous_visitors.get('total_unique_visitors', 0)

        # Calculate growth rate
        if previous_total > 0:
            growth_rate = (
                (current_total - previous_total) / previous_total * 100
            )
        else:
            growth_rate = 100 if current_total > 0 else 0

        return {
            'community_id': community_id,
            'period_days': current_period_days,
            'current_period': {
                'start': current_start.isoformat(),
                'end': end_date.isoformat(),
                'visitors': current_total,
            },
            'previous_period': {
                'start': previous_start.isoformat(),
                'end': current_start.isoformat(),
                'visitors': previous_total,
            },
            'growth_rate': round(growth_rate, 2),
            'absolute_change': current_total - previous_total,
        }

    except Exception as e:
        logger.error(f"Error calculating growth rate: {e}")
        return {'error': str(e)}
