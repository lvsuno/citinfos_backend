"""
Community-related services for efficient data access and operations.
"""

from analytics.services import CommunityOnlineTracker
from typing import Dict, List, Set


class CommunityRedisService:
    """
    Service for fast community data access using Redis.

    This service provides optimized access to frequently needed community data
    like online member counts, avoiding database queries where possible.
    """

    def __init__(self):
        self.online_tracker = CommunityOnlineTracker()

    def get_online_member_count(self, community_id: str) -> int:
        """
        Get the current number of online members for a community.

        Args:
            community_id: ID of the community

        Returns:
            int: Number of online members
        """
        return self.online_tracker.get_online_count(community_id)

    def get_online_members(self, community_id: str) -> Set[str]:
        """
        Get the list of online member IDs for a community.

        Args:
            community_id: ID of the community

        Returns:
            Set[str]: Set of user IDs who are currently online
        """
        return self.online_tracker.get_online_members(community_id)

    def is_user_online_in_community(self, community_id: str,
                                   user_id: str) -> bool:
        """
        Check if a specific user is currently online in a community.

        Args:
            community_id: ID of the community
            user_id: ID of the user

        Returns:
            bool: True if user is online in the community
        """
        return self.online_tracker.is_user_online_in_community(
            user_id, community_id
        )

    def get_user_active_communities(self, user_id: str) -> Set[str]:
        """
        Get all communities where the user is currently active/online.

        Args:
            user_id: ID of the user

        Returns:
            Set[str]: Set of community IDs where user is active
        """
        return self.online_tracker.get_user_communities(user_id)

    def get_multiple_community_stats(self, community_ids: List[str]) -> Dict[str, Dict]:
        """
        Get online statistics for multiple communities efficiently.

        Args:
            community_ids: List of community IDs

        Returns:
            Dict[str, Dict]: Dictionary with community stats
            {
                "community_id": {
                    "online_count": 5,
                    "peak_counts": {"daily": 12, "weekly": 20, "monthly": 35}
                }
            }
        """
        stats = {}

        for community_id in community_ids:
            try:
                peak_data = self.online_tracker.get_peak_counts(community_id)
                stats[community_id] = {
                    'online_count': self.online_tracker.get_online_count(
                        community_id
                    ),
                    'peak_counts': peak_data,
                    'is_active': self.online_tracker.get_online_count(
                        community_id
                    ) > 0
                }
            except Exception as e:
                # Fallback for individual community failures
                stats[community_id] = {
                    'online_count': 0,
                    'peak_counts': {'daily': 0, 'weekly': 0, 'monthly': 0},
                    'is_active': False,
                    'error': str(e)
                }

        return stats

    def track_user_activity(self, community_id: str, user_id: str):
        """
        Track user activity in a community (mark as online).

        Args:
            community_id: ID of the community
            user_id: ID of the user
        """
        self.online_tracker.add_user_to_community(user_id, community_id)

    def remove_user_activity(self, community_id: str, user_id: str):
        """
        Remove user activity tracking (mark as offline).

        Args:
            community_id: ID of the community
            user_id: ID of the user
        """
        self.online_tracker.remove_user_from_community(user_id, community_id)

    def update_user_activity(self, community_id: str, user_id: str):
        """
        Update user activity timestamp (extend online status).

        Args:
            community_id: ID of the community
            user_id: ID of the user
        """
        self.online_tracker.update_user_activity(user_id, community_id)


# Global service instance for easy import
community_redis_service = CommunityRedisService()
