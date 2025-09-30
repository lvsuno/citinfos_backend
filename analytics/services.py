"""Services for real-time community analytics using Redis."""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
import redis

logger = logging.getLogger(__name__)


class CommunityOnlineTracker:
    """Redis-based service for tracking online members in communities."""

    def __init__(self):
        """Initialize Redis connection for real-time tracking."""
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
        self.user_activity_timeout = 300  # 5 minutes
        self.analytics_update_interval = 30  # 30 seconds

    # Redis Key Patterns
    def _get_community_online_key(self, community_id: str) -> str:
        """Get Redis key for community online members set."""
        return f"community:{community_id}:online"

    def _get_user_communities_key(self, user_id: str) -> str:
        """Get Redis key for user's active communities set."""
        return f"user:{user_id}:communities"

    def _get_community_analytics_key(self, community_id: str) -> str:
        """Get Redis key for community analytics cache."""
        return f"community:{community_id}:analytics"

    def _get_user_last_activity_key(self, user_id: str, community_id: str) -> str:
        """Get Redis key for user's last activity in a community."""
        return f"user:{user_id}:community:{community_id}:activity"

    def _get_daily_peak_key(self, community_id: str) -> str:
        """Get Redis key for daily peak online count."""
        today = timezone.now().date().isoformat()
        return f"community:{community_id}:peak:daily:{today}"

    def _get_weekly_peak_key(self, community_id: str) -> str:
        """Get Redis key for weekly peak online count."""
        week = timezone.now().isocalendar()
        return f"community:{community_id}:peak:weekly:{week[0]}:{week[1]}"

    def _get_monthly_peak_key(self, community_id: str) -> str:
        """Get Redis key for monthly peak online count."""
        month = timezone.now().strftime('%Y-%m')
        return f"community:{community_id}:peak:monthly:{month}"

    # Core Tracking Methods
    def add_user_to_community(self, user_id: str, community_id: str) -> int:
        """Add user to community's online members and return current count."""
        try:
            # Add user to community's online set
            online_key = self._get_community_online_key(community_id)
            self.redis_client.sadd(online_key, user_id)
            self.redis_client.expire(online_key, self.user_activity_timeout)

            # Add community to user's active communities
            user_communities_key = self._get_user_communities_key(user_id)
            self.redis_client.sadd(user_communities_key, community_id)
            self.redis_client.expire(user_communities_key, self.user_activity_timeout)

            # Update user's last activity timestamp
            activity_key = self._get_user_last_activity_key(user_id, community_id)
            self.redis_client.setex(
                activity_key,
                self.user_activity_timeout,
                timezone.now().isoformat()
            )

            # Get current count and update peaks
            current_count = self.get_online_count(community_id)
            self._update_peak_counts(community_id, current_count)

            # Cache analytics update
            self._cache_community_analytics(community_id)

            logger.info(f"User {user_id} joined community {community_id}. "
                       f"Online count: {current_count}")

            return current_count

        except Exception as e:
            logger.error(f"Error adding user {user_id} to community {community_id}: {e}")
            return 0

    def remove_user_from_community(self, user_id: str, community_id: str) -> int:
        """Remove user from community's online members and return current count."""
        try:
            # Remove user from community's online set
            online_key = self._get_community_online_key(community_id)
            self.redis_client.srem(online_key, user_id)

            # Remove community from user's active communities
            user_communities_key = self._get_user_communities_key(user_id)
            self.redis_client.srem(user_communities_key, community_id)

            # Remove user's activity timestamp
            activity_key = self._get_user_last_activity_key(user_id, community_id)
            self.redis_client.delete(activity_key)

            # Get current count
            current_count = self.get_online_count(community_id)

            # Cache analytics update
            self._cache_community_analytics(community_id)

            logger.info(f"User {user_id} left community {community_id}. "
                       f"Online count: {current_count}")

            return current_count

        except Exception as e:
            logger.error(f"Error removing user {user_id} from community {community_id}: {e}")
            return 0

    def update_user_activity(self, user_id: str, community_id: str) -> int:
        """Update user's activity timestamp and return current count."""
        try:
            # Check if user is already in the community
            online_key = self._get_community_online_key(community_id)
            is_online = self.redis_client.sismember(online_key, user_id)

            if not is_online:
                # Add user to community if not already there
                return self.add_user_to_community(user_id, community_id)
            else:
                # Just update timestamps
                self.redis_client.expire(online_key, self.user_activity_timeout)

                user_communities_key = self._get_user_communities_key(user_id)
                self.redis_client.expire(user_communities_key, self.user_activity_timeout)

                activity_key = self._get_user_last_activity_key(user_id, community_id)
                self.redis_client.setex(
                    activity_key,
                    self.user_activity_timeout,
                    timezone.now().isoformat()
                )

                return self.get_online_count(community_id)

        except Exception as e:
            logger.error(f"Error updating activity for user {user_id} in community {community_id}: {e}")
            return 0

    def get_online_count(self, community_id: str) -> int:
        """Get current online member count for a community."""
        try:
            online_key = self._get_community_online_key(community_id)
            return self.redis_client.scard(online_key)
        except Exception as e:
            logger.error(f"Error getting online count for community {community_id}: {e}")
            return 0

    def get_online_members(self, community_id: str) -> Set[str]:
        """Get list of online member IDs for a community."""
        try:
            online_key = self._get_community_online_key(community_id)
            members = self.redis_client.smembers(online_key)
            return {member.decode('utf-8') for member in members}
        except Exception as e:
            logger.error(f"Error getting online members for community {community_id}: {e}")
            return set()

    def get_user_communities(self, user_id: str) -> Set[str]:
        """Get list of communities where user is currently active."""
        try:
            user_communities_key = self._get_user_communities_key(user_id)
            communities = self.redis_client.smembers(user_communities_key)
            return {community.decode('utf-8') for community in communities}
        except Exception as e:
            logger.error(f"Error getting communities for user {user_id}: {e}")
            return set()

    def is_user_online_in_community(self, user_id: str, community_id: str) -> bool:
        """Check if user is currently online in a specific community."""
        try:
            online_key = self._get_community_online_key(community_id)
            return self.redis_client.sismember(online_key, user_id)
        except Exception as e:
            logger.error(f"Error checking if user {user_id} is online in community {community_id}: {e}")
            return False

    # Peak Tracking Methods
    def _update_peak_counts(self, community_id: str, current_count: int):
        """Update peak counts for daily, weekly, and monthly."""
        try:
            # Daily peak
            daily_key = self._get_daily_peak_key(community_id)
            daily_peak = self.redis_client.get(daily_key)
            daily_peak = int(daily_peak) if daily_peak else 0
            if current_count > daily_peak:
                self.redis_client.setex(daily_key, 86400, current_count)  # 24 hours

            # Weekly peak
            weekly_key = self._get_weekly_peak_key(community_id)
            weekly_peak = self.redis_client.get(weekly_key)
            weekly_peak = int(weekly_peak) if weekly_peak else 0
            if current_count > weekly_peak:
                self.redis_client.setex(weekly_key, 604800, current_count)  # 7 days

            # Monthly peak
            monthly_key = self._get_monthly_peak_key(community_id)
            monthly_peak = self.redis_client.get(monthly_key)
            monthly_peak = int(monthly_peak) if monthly_peak else 0
            if current_count > monthly_peak:
                self.redis_client.setex(monthly_key, 2592000, current_count)  # 30 days

        except Exception as e:
            logger.error(f"Error updating peak counts for community {community_id}: {e}")

    def get_peak_counts(self, community_id: str) -> Dict[str, int]:
        """Get peak online counts for different time periods."""
        try:
            daily_key = self._get_daily_peak_key(community_id)
            weekly_key = self._get_weekly_peak_key(community_id)
            monthly_key = self._get_monthly_peak_key(community_id)

            daily_peak = self.redis_client.get(daily_key)
            weekly_peak = self.redis_client.get(weekly_key)
            monthly_peak = self.redis_client.get(monthly_key)

            return {
                'daily': int(daily_peak) if daily_peak else 0,
                'weekly': int(weekly_peak) if weekly_peak else 0,
                'monthly': int(monthly_peak) if monthly_peak else 0,
            }
        except Exception as e:
            logger.error(f"Error getting peak counts for community {community_id}: {e}")
            return {'daily': 0, 'weekly': 0, 'monthly': 0}

    # Analytics Caching
    def _cache_community_analytics(self, community_id: str):
        """Cache community analytics for quick retrieval."""
        try:
            analytics_key = self._get_community_analytics_key(community_id)

            analytics_data = {
                'current_online': self.get_online_count(community_id),
                'peaks': self.get_peak_counts(community_id),
                'last_updated': timezone.now().isoformat(),
            }

            # Cache for 30 seconds
            self.redis_client.setex(
                analytics_key,
                self.analytics_update_interval,
                json.dumps(analytics_data, default=str)
            )

        except Exception as e:
            logger.error(f"Error caching analytics for community {community_id}: {e}")

    def get_cached_analytics(self, community_id: str) -> Optional[Dict]:
        """Get cached community analytics."""
        try:
            analytics_key = self._get_community_analytics_key(community_id)
            cached_data = self.redis_client.get(analytics_key)

            if cached_data:
                return json.loads(cached_data.decode('utf-8'))
            return None

        except Exception as e:
            logger.error(f"Error getting cached analytics for community {community_id}: {e}")
            return None

    # Cleanup Methods
    def cleanup_inactive_users(self):
        """Remove inactive users from all communities (called by Celery task)."""
        try:
            # Get all community online keys
            pattern = "community:*:online"
            community_keys = self.redis_client.keys(pattern)

            cleaned_count = 0
            for key in community_keys:
                # Extract community_id from key
                community_id = key.decode('utf-8').split(':')[1]

                # Get all members
                members = self.redis_client.smembers(key)

                for member in members:
                    user_id = member.decode('utf-8')
                    activity_key = self._get_user_last_activity_key(user_id, community_id)

                    # Check if activity key exists (TTL-based cleanup)
                    if not self.redis_client.exists(activity_key):
                        self.remove_user_from_community(user_id, community_id)
                        cleaned_count += 1

            logger.info(f"Cleaned up {cleaned_count} inactive users")
            return cleaned_count

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0

    def get_all_community_stats(self) -> Dict[str, Dict]:
        """Get statistics for all communities."""
        try:
            pattern = "community:*:online"
            community_keys = self.redis_client.keys(pattern)

            stats = {}
            for key in community_keys:
                community_id = key.decode('utf-8').split(':')[1]

                # Get or create cached analytics
                cached = self.get_cached_analytics(community_id)
                if not cached:
                    self._cache_community_analytics(community_id)
                    cached = self.get_cached_analytics(community_id)

                if cached:
                    stats[community_id] = cached

            return stats

        except Exception as e:
            logger.error(f"Error getting all community stats: {e}")
            return {}


# Global instance
online_tracker = CommunityOnlineTracker()
