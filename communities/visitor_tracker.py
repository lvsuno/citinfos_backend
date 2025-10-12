"""
Community Visitor Tracking with Division Analytics

Tracks real-time visitors to communities with support for:
- Visitor counts per community
- Division-based analytics (where visitors are from)
- Cross-division visit tracking
- Visitor session management
- WebSocket broadcasting for real-time updates
"""

import logging
import json
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime, timedelta

import redis
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class CommunityVisitorTracker:
    """
    Redis-based service for tracking community visitors with division analytics.

    Tracks visitors instead of members, including:
    - Real-time visitor count
    - Visitor home divisions
    - Cross-division visits (users from division A visiting division B)
    - Visit duration and page views
    """

    def __init__(self):
        """Initialize Redis connection for real-time visitor tracking."""
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
        self.visitor_timeout = 300  # 5 minutes
        self.analytics_update_interval = 30  # 30 seconds

    # ==================== Redis Key Patterns ====================

    def _get_community_visitors_key(self, community_id: str) -> str:
        """Get Redis key for community visitors hash (replaces online_members)."""
        return f"community:{community_id}:visitors"

    def _get_visitor_communities_key(self, user_id: str) -> str:
        """Get Redis key for user's currently visiting communities."""
        return f"user:{user_id}:visiting_communities"

    def _get_visitor_activity_key(self, user_id: str, community_id: str) -> str:
        """Get Redis key for visitor's last activity timestamp."""
        return f"visitor:{user_id}:community:{community_id}:activity"

    def _get_division_visitors_key(self, community_id: str) -> str:
        """Get Redis key for division breakdown (division -> count)."""
        return f"community:{community_id}:visitors:by_division"

    def _get_cross_division_key(self, community_id: str) -> str:
        """Get Redis key for cross-division visit tracking."""
        return f"community:{community_id}:cross_division_visits"

    def _get_visitor_peak_key(self, community_id: str, period: str) -> str:
        """Get Redis key for peak visitor counts (daily/weekly/monthly)."""
        if period == 'daily':
            date = timezone.now().date().isoformat()
            return f"community:{community_id}:peak:visitors:daily:{date}"
        elif period == 'weekly':
            week = timezone.now().isocalendar()
            return f"community:{community_id}:peak:visitors:weekly:{week[0]}:{week[1]}"
        elif period == 'monthly':
            month = timezone.now().strftime('%Y-%m')
            return f"community:{community_id}:peak:visitors:monthly:{month}"
        return f"community:{community_id}:peak:visitors:{period}"

    # ==================== Core Visitor Tracking ====================

    def add_visitor(
        self,
        user_id: str,
        community_id: str,
        visitor_division_id: Optional[str] = None,
        community_division_id: Optional[str] = None,
        is_authenticated: bool = True,
        device_fingerprint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Add a visitor to a community and track their division.

        Args:
            user_id: ID of visiting user (for auth) or identifier for anon
            community_id: ID of the community being visited
            visitor_division_id: Division where the visitor is from
            community_division_id: Division of the community being visited
            is_authenticated: Whether the visitor is authenticated
            device_fingerprint: Device fingerprint (required for anonymous)
            ip_address: Visitor's IP address
            user_agent: Visitor's user agent string

        Returns:
            Dict with current_count, cross_division flag, and division stats
        """
        try:
            now = timezone.now()
            timestamp = now.isoformat()

            # For anonymous users, use device fingerprint as identifier
            if not is_authenticated:
                if not device_fingerprint:
                    logger.warning(
                        f"No device fingerprint provided for anonymous "
                        f"visitor to community {community_id}"
                    )
                    return {
                        'current_count': 0,
                        'is_cross_division': False,
                        'error': 'Device fingerprint required for anonymous'
                    }
                visitor_key = f"anon_{device_fingerprint}"
            else:
                visitor_key = user_id

            # Store visitor data in hash
            visitors_key = self._get_community_visitors_key(community_id)
            visitor_data = {
                'user_id': user_id if is_authenticated else None,
                'device_fingerprint': device_fingerprint,
                'is_authenticated': is_authenticated,
                'joined_at': timestamp,
                'division_id': visitor_division_id or 'unknown',
                'pages_viewed': 1,
                'last_activity': timestamp,
                'ip_address': ip_address,
                'user_agent': user_agent
            }

            # Store as JSON in hash
            self.redis_client.hset(
                visitors_key,
                visitor_key,
                json.dumps(visitor_data)
            )
            self.redis_client.expire(visitors_key, self.visitor_timeout)

            # Track authenticated vs anonymous counts
            if is_authenticated:
                auth_key = f"community:{community_id}:visitors:authenticated"
                self.redis_client.sadd(auth_key, visitor_key)
                self.redis_client.expire(auth_key, self.visitor_timeout)
            else:
                anon_key = f"community:{community_id}:visitors:anonymous"
                self.redis_client.sadd(anon_key, visitor_key)
                self.redis_client.expire(anon_key, self.visitor_timeout)

            # Add community to user's visiting list (only for authenticated)
            if is_authenticated:
                user_communities_key = self._get_visitor_communities_key(
                    user_id
                )
                self.redis_client.sadd(user_communities_key, community_id)
                self.redis_client.expire(
                    user_communities_key,
                    self.visitor_timeout
                )

            # Update visitor's last activity (use appropriate ID)
            activity_key = self._get_visitor_activity_key(
                visitor_key,
                community_id
            )
            self.redis_client.setex(
                activity_key,
                self.visitor_timeout,
                timestamp
            )

            # Track division breakdown
            if visitor_division_id:
                division_key = self._get_division_visitors_key(community_id)
                self.redis_client.hincrby(division_key, visitor_division_id, 1)
                self.redis_client.expire(division_key, self.visitor_timeout)

            # Track cross-division visits
            is_cross_division = False
            if (visitor_division_id and community_division_id and
                visitor_division_id != community_division_id):
                is_cross_division = True
                cross_div_key = self._get_cross_division_key(community_id)
                cross_div_data = f"{visitor_division_id}→{community_division_id}"
                self.redis_client.zincrby(
                    cross_div_key,
                    1,
                    cross_div_data
                )
                self.redis_client.expire(cross_div_key, self.visitor_timeout)

            # Get current counts and update peaks
            current_count = self.get_visitor_count(community_id)
            self._update_peak_counts(community_id, current_count)

            # Broadcast visitor joined via WebSocket
            self._broadcast_visitor_update(
                community_id,
                current_count,
                change=1
            )

            logger.info(
                f"Visitor {user_id} from division {visitor_division_id} "
                f"visiting community {community_id} (division {community_division_id}). "
                f"Count: {current_count}, Cross-division: {is_cross_division}"
            )

            return {
                'current_count': current_count,
                'is_cross_division': is_cross_division,
                'visitor_division': visitor_division_id,
                'community_division': community_division_id,
                'timestamp': timestamp
            }

        except Exception as e:
            logger.error(
                f"Error adding visitor {user_id} to community {community_id}: {e}"
            )
            return {
                'current_count': 0,
                'is_cross_division': False,
                'error': str(e)
            }

    def remove_visitor(self, user_id: str, community_id: str) -> int:
        """
        Remove a visitor from a community.

        Args:
            user_id: ID of the visitor
            community_id: ID of the community

        Returns:
            Current visitor count after removal
        """
        try:
            # Get visitor data before removal (for division tracking)
            visitors_key = self._get_community_visitors_key(community_id)
            visitor_json = self.redis_client.hget(visitors_key, user_id)

            if visitor_json:
                visitor_data = json.loads(visitor_json)
                division_id = visitor_data.get('division_id')

                # Decrement division count
                if division_id and division_id != 'unknown':
                    division_key = self._get_division_visitors_key(community_id)
                    current = self.redis_client.hget(division_key, division_id)
                    if current and int(current) > 0:
                        self.redis_client.hincrby(division_key, division_id, -1)

            # Remove visitor from hash
            self.redis_client.hdel(visitors_key, user_id)

            # Remove community from user's visiting list
            user_communities_key = self._get_visitor_communities_key(user_id)
            self.redis_client.srem(user_communities_key, community_id)

            # Remove activity key
            activity_key = self._get_visitor_activity_key(user_id, community_id)
            self.redis_client.delete(activity_key)

            current_count = self.get_visitor_count(community_id)

            # Broadcast visitor left via WebSocket
            self._broadcast_visitor_update(
                community_id,
                current_count,
                change=-1
            )

            logger.info(
                f"Visitor {user_id} left community {community_id}. "
                f"Count: {current_count}"
            )

            return current_count

        except Exception as e:
            logger.error(
                f"Error removing visitor {user_id} from community {community_id}: {e}"
            )
            return 0

    def update_visitor_activity(
        self,
        user_id: str,
        community_id: str,
        increment_pages: bool = True
    ) -> Dict[str, any]:
        """
        Update visitor's activity timestamp and page view count.

        Args:
            user_id: ID of the visitor
            community_id: ID of the community
            increment_pages: Whether to increment pages_viewed counter

        Returns:
            Dict with updated visitor data
        """
        try:
            visitors_key = self._get_community_visitors_key(community_id)
            visitor_json = self.redis_client.hget(visitors_key, user_id)

            if visitor_json:
                # Update existing visitor
                visitor_data = json.loads(visitor_json)
                visitor_data['last_activity'] = timezone.now().isoformat()

                if increment_pages:
                    visitor_data['pages_viewed'] = visitor_data.get('pages_viewed', 0) + 1

                # Save updated data
                self.redis_client.hset(
                    visitors_key,
                    user_id,
                    json.dumps(visitor_data)
                )
                self.redis_client.expire(visitors_key, self.visitor_timeout)

                # Update activity timestamp
                activity_key = self._get_visitor_activity_key(user_id, community_id)
                self.redis_client.setex(
                    activity_key,
                    self.visitor_timeout,
                    visitor_data['last_activity']
                )

                return visitor_data
            else:
                # Visitor not found, might need to re-add
                return {'error': 'Visitor not found, session may have expired'}

        except Exception as e:
            logger.error(
                f"Error updating visitor {user_id} activity in "
                f"community {community_id}: {e}"
            )
            return {'error': str(e)}

    # ==================== Visitor Query Methods ====================

    def get_visitor_count(self, community_id: str) -> int:
        """Get current visitor count for a community."""
        try:
            visitors_key = self._get_community_visitors_key(community_id)
            return self.redis_client.hlen(visitors_key)
        except Exception as e:
            logger.error(
                f"Error getting visitor count for community {community_id}: {e}"
            )
            return 0

    def get_authenticated_visitor_count(self, community_id: str) -> int:
        """Get count of authenticated visitors."""
        try:
            auth_key = f"community:{community_id}:visitors:authenticated"
            return self.redis_client.scard(auth_key)
        except Exception as e:
            logger.error(
                f"Error getting authenticated visitor count for "
                f"community {community_id}: {e}"
            )
            return 0

    def get_anonymous_visitor_count(self, community_id: str) -> int:
        """Get count of anonymous visitors."""
        try:
            anon_key = f"community:{community_id}:visitors:anonymous"
            return self.redis_client.scard(anon_key)
        except Exception as e:
            logger.error(
                f"Error getting anonymous visitor count for "
                f"community {community_id}: {e}"
            )
            return 0

    def get_visitor_stats(self, community_id: str) -> Dict[str, int]:
        """
        Get visitor statistics including authenticated/anonymous breakdown.

        Returns:
            Dict with total, authenticated, and anonymous counts
        """
        try:
            total = self.get_visitor_count(community_id)
            authenticated = self.get_authenticated_visitor_count(community_id)
            anonymous = self.get_anonymous_visitor_count(community_id)

            return {
                'total_visitors': total,
                'authenticated_visitors': authenticated,
                'anonymous_visitors': anonymous,
                'authenticated_percentage': (
                    round((authenticated / total * 100), 2)
                    if total > 0 else 0
                ),
                'anonymous_percentage': (
                    round((anonymous / total * 100), 2)
                    if total > 0 else 0
                )
            }
        except Exception as e:
            logger.error(
                f"Error getting visitor stats for community {community_id}: {e}"
            )
            return {
                'total_visitors': 0,
                'authenticated_visitors': 0,
                'anonymous_visitors': 0,
                'authenticated_percentage': 0,
                'anonymous_percentage': 0
            }

    def get_visitor_list(self, community_id: str) -> List[Dict[str, any]]:
        """
        Get list of current visitors with their details.

        Returns:
            List of visitor data dictionaries
        """
        try:
            visitors_key = self._get_community_visitors_key(community_id)
            visitor_data_list = []

            # Get all visitor data from hash
            all_visitors = self.redis_client.hgetall(visitors_key)

            for user_id, visitor_json in all_visitors.items():
                try:
                    visitor_data = json.loads(visitor_json)
                    visitor_data['user_id'] = user_id.decode('utf-8') if isinstance(user_id, bytes) else user_id
                    visitor_data_list.append(visitor_data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON for visitor {user_id}")
                    continue

            # Sort by last activity (most recent first)
            visitor_data_list.sort(
                key=lambda x: x.get('last_activity', ''),
                reverse=True
            )

            return visitor_data_list

        except Exception as e:
            logger.error(
                f"Error getting visitor list for community {community_id}: {e}"
            )
            return []

    def get_division_breakdown(self, community_id: str) -> Dict[str, int]:
        """
        Get breakdown of visitors by their home division.

        Returns:
            Dict mapping division_id to visitor count
        """
        try:
            division_key = self._get_division_visitors_key(community_id)
            breakdown = self.redis_client.hgetall(division_key)

            # Convert bytes to strings and ints
            result = {}
            for division_id, count in breakdown.items():
                div_id = division_id.decode('utf-8') if isinstance(division_id, bytes) else division_id
                result[div_id] = int(count)

            return result

        except Exception as e:
            logger.error(
                f"Error getting division breakdown for community {community_id}: {e}"
            )
            return {}

    def get_cross_division_stats(self, community_id: str) -> Dict[str, any]:
        """
        Get statistics about cross-division visits.

        Returns:
            Dict with cross-division visit data and percentages
        """
        try:
            cross_div_key = self._get_cross_division_key(community_id)

            # Get all cross-division pairs with scores
            cross_visits = self.redis_client.zrange(
                cross_div_key,
                0,
                -1,
                withscores=True,
                desc=True
            )

            total_visitors = self.get_visitor_count(community_id)

            cross_division_data = []
            total_cross_div = 0

            for visit_pair, count in cross_visits:
                pair = visit_pair.decode('utf-8') if isinstance(visit_pair, bytes) else visit_pair
                from_div, to_div = pair.split('→')

                cross_division_data.append({
                    'from_division': from_div,
                    'to_division': to_div,
                    'count': int(count)
                })
                total_cross_div += int(count)

            cross_div_percentage = (
                (total_cross_div / total_visitors * 100)
                if total_visitors > 0
                else 0
            )

            return {
                'total_visitors': total_visitors,
                'cross_division_visits': total_cross_div,
                'cross_division_percentage': round(cross_div_percentage, 2),
                'breakdown': cross_division_data[:10]  # Top 10
            }

        except Exception as e:
            logger.error(
                f"Error getting cross-division stats for community {community_id}: {e}"
            )
            return {
                'total_visitors': 0,
                'cross_division_visits': 0,
                'cross_division_percentage': 0,
                'breakdown': []
            }

    def is_user_visiting(self, user_id: str, community_id: str) -> bool:
        """Check if a user is currently visiting a community."""
        try:
            visitors_key = self._get_community_visitors_key(community_id)
            return self.redis_client.hexists(visitors_key, user_id)
        except Exception as e:
            logger.error(
                f"Error checking if user {user_id} is visiting "
                f"community {community_id}: {e}"
            )
            return False

    def get_user_visiting_communities(self, user_id: str) -> Set[str]:
        """Get all communities a user is currently visiting."""
        try:
            user_communities_key = self._get_visitor_communities_key(user_id)
            communities = self.redis_client.smembers(user_communities_key)

            return {
                c.decode('utf-8') if isinstance(c, bytes) else c
                for c in communities
            }

        except Exception as e:
            logger.error(
                f"Error getting visiting communities for user {user_id}: {e}"
            )
            return set()

    # ==================== Peak Tracking ====================

    def _update_peak_counts(self, community_id: str, current_count: int):
        """Update peak visitor counts for daily/weekly/monthly periods."""
        try:
            for period in ['daily', 'weekly', 'monthly']:
                peak_key = self._get_visitor_peak_key(community_id, period)

                # Get current peak
                current_peak = self.redis_client.get(peak_key)
                current_peak = int(current_peak) if current_peak else 0

                # Update if new count is higher
                if current_count > current_peak:
                    ttl = {
                        'daily': 86400,      # 24 hours
                        'weekly': 604800,    # 7 days
                        'monthly': 2592000   # 30 days
                    }
                    self.redis_client.setex(
                        peak_key,
                        ttl[period],
                        current_count
                    )

        except Exception as e:
            logger.error(
                f"Error updating peak counts for community {community_id}: {e}"
            )

    def get_peak_counts(self, community_id: str) -> Dict[str, int]:
        """Get peak visitor counts for different time periods."""
        try:
            peaks = {}
            for period in ['daily', 'weekly', 'monthly']:
                peak_key = self._get_visitor_peak_key(community_id, period)
                peak = self.redis_client.get(peak_key)
                peaks[period] = int(peak) if peak else 0

            return peaks

        except Exception as e:
            logger.error(
                f"Error getting peak counts for community {community_id}: {e}"
            )
            return {'daily': 0, 'weekly': 0, 'monthly': 0}

    # ==================== Cleanup Methods ====================

    def cleanup_stale_visitors(self, community_id: str) -> int:
        """
        Remove visitors who haven't been active in the timeout period.

        Returns:
            Number of stale visitors removed
        """
        try:
            visitors = self.get_visitor_list(community_id)
            removed_count = 0
            cutoff_time = timezone.now() - timedelta(
                seconds=self.visitor_timeout
            )

            for visitor in visitors:
                last_activity_str = visitor.get('last_activity')
                if last_activity_str:
                    last_activity = datetime.fromisoformat(last_activity_str)

                    # Make timezone-aware if needed
                    if timezone.is_naive(last_activity):
                        last_activity = timezone.make_aware(last_activity)

                    if last_activity < cutoff_time:
                        visitor_key = (
                            visitor.get('visitor_key') or
                            visitor.get('user_id')
                        )
                        self.remove_visitor(visitor_key, community_id)
                        removed_count += 1

            logger.info(
                f"Cleaned up {removed_count} stale visitors from "
                f"community {community_id}"
            )

            return removed_count

        except Exception as e:
            logger.error(
                f"Error cleaning up stale visitors for "
                f"community {community_id}: {e}"
            )
            return 0

    # ==================== Analytics Integration ====================

    def update_community_analytics(self, community_id: str) -> bool:
        """
        Update CommunityAnalytics model from Redis visitor data.

        Should be called periodically (e.g., every 30 seconds) to sync
        real-time Redis data with database analytics.

        Args:
            community_id: ID of the community

        Returns:
            True if successful, False otherwise
        """
        try:
            from analytics.models import CommunityAnalytics
            from communities.models import Community
            from django.utils import timezone

            # Get community
            community = Community.objects.get(id=community_id)

            # Get or create analytics for today
            analytics, created = CommunityAnalytics.objects.get_or_create(
                community=community,
                date=timezone.now().date(),
                defaults={
                    'current_visitors': 0,
                    'current_authenticated_visitors': 0,
                    'current_anonymous_visitors': 0
                }
            )

            # Get visitor stats from Redis
            stats = self.get_visitor_stats(community_id)

            # Update analytics with Redis data
            analytics.update_from_redis(stats)

            logger.debug(
                f"Updated CommunityAnalytics for {community.name}: "
                f"{stats['total_visitors']} visitors "
                f"({stats['authenticated_visitors']} auth, "
                f"{stats['anonymous_visitors']} anon)"
            )

            return True

        except Exception as e:
            logger.error(
                f"Error updating CommunityAnalytics for "
                f"community {community_id}: {e}"
            )
            return False

    # ==================== WebSocket Broadcasting ====================

    def _broadcast_visitor_update(
        self,
        community_id: str,
        count: int,
        change: int = 0
    ) -> None:
        """
        Broadcast visitor count update via WebSocket.

        Args:
            community_id: UUID of the community
            count: Current visitor count
            change: Change in count (+1 for join, -1 for leave, 0 for update)
        """
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            from django.utils import timezone

            channel_layer = get_channel_layer()
            if not channel_layer:
                return

            room_group_name = f'visitors_{community_id}'

            # Determine event type
            if change > 0:
                event_type = 'visitor_joined'
            elif change < 0:
                event_type = 'visitor_left'
            else:
                event_type = 'visitor_count_update'

            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': event_type,
                    'community_id': str(community_id),
                    'count': count,
                    'change': change,
                    'timestamp': timezone.now().isoformat()
                }
            )

            logger.debug(
                f"Broadcasted {event_type} to {room_group_name}: "
                f"count={count}, change={change:+d}"
            )

        except Exception as e:
            # Don't let WebSocket errors break visitor tracking
            logger.warning(f"Error broadcasting visitor update: {e}")


# Global instance for easy import
visitor_tracker = CommunityVisitorTracker()
