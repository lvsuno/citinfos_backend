"""Tests for community presence tracking using Redis."""
"""Tests for community presence tracking using Redis."""

from django.test import TestCase
from communities.services import community_redis_service


class CommunityPresenceTests(TestCase):
    def test_add_and_remove_user_presence(self):
        cid = '00000000-0000-0000-0000-000000000099'
        uid = 'unit-test-user'

        # Ensure clean state
        community_redis_service.remove_user_activity(cid, uid)

        # Add user (wrapper does not return value; verify via members)
        community_redis_service.track_user_activity(cid, uid)

        members = community_redis_service.get_online_members(cid)
        self.assertIn(uid, members)

        count = community_redis_service.get_online_member_count(cid)
        self.assertGreaterEqual(count, 1)

        # Remove user
        community_redis_service.remove_user_activity(cid, uid)
        members_after = community_redis_service.get_online_members(cid)
        self.assertNotIn(uid, members_after)
