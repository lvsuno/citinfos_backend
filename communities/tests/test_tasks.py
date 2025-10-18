
"""Tests for communities tasks."""

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta

from communities.models import (
    Community, CommunityMembership, CommunityInvitation,
    CommunityJoinRequest, CommunityRole
)
from communities.tasks import (
    update_community_analytics, cleanup_expired_community_invitations,
    update_community_member_counts, cleanup_inactive_communities,
    process_community_join_requests, validate_community_access_rules
)
from accounts.models import UserProfile
from analytics.models import SystemMetric


class CommunityTasksTests(TestCase):
    def test_cleanup_expired_community_join_requests(self):
        """Test expired community join requests cleanup task."""
        from communities.tasks import cleanup_expired_community_join_requests
        # Create expired join request (older than 14 days)
        join_request = CommunityJoinRequest.objects.create(
            community=self.community,
            user=self.applicant_profile,
            status='pending',
        )
        CommunityJoinRequest.objects.filter(id=join_request.id).update(
            created_at=timezone.now() - timedelta(days=15)
        )
        # Create valid join request (recent)
        valid_request = CommunityJoinRequest.objects.create(
            community=self.community,
            user=self.member_profile,
            status='pending',
        )
        # Run the task
        result = cleanup_expired_community_join_requests()
        # Check results
        self.assertIn('Marked 1 community join requests as expired', result)
        join_request.refresh_from_db()
        valid_request.refresh_from_db()
        self.assertEqual(join_request.status, 'expired')
        self.assertEqual(valid_request.status, 'pending')

    def test_cleanup_expired_community_join_requests(self):
        """Test expired community join requests cleanup task."""
        from communities.tasks import cleanup_expired_community_join_requests
        # Create expired join request (older than 14 days)
        join_request = CommunityJoinRequest.objects.create(
            community=self.community,
            user=self.applicant_profile,
            status='pending',
        )
        CommunityJoinRequest.objects.filter(id=join_request.id).update(
            created_at=timezone.now() - timedelta(days=15)
        )
        # Create valid join request (recent)
        valid_request = CommunityJoinRequest.objects.create(
            community=self.community,
            user=self.member_profile,
            status='pending',
        )
        # Run the task
        result = cleanup_expired_community_join_requests()
        # Check results
        self.assertIn('Marked 1 community join requests as expired', result)
        join_request.refresh_from_db()
        valid_request.refresh_from_db()
        self.assertEqual(join_request.status, 'expired')
        self.assertEqual(valid_request.status, 'pending')

    def test_reactivate_expired_bans_future(self):
        """Test that users with future ban_expires_at are not reactivated."""
        from communities.tasks import reactivate_expired_bans
        membership = CommunityMembership.objects.create(
            community=self.community,
            user=self.member_profile,
            role=self.member_role,
            status='banned',
            banned_by=self.creator_profile,
            ban_reason='Test ban',
            banned_at=timezone.now() - timedelta(days=2),
            ban_expires_at=timezone.now() + timedelta(hours=1)
        )
        reactivate_expired_bans()
        membership.refresh_from_db()
        self.assertEqual(membership.status, 'banned')
        self.assertIsNotNone(membership.ban_expires_at)

    def test_reactivate_expired_bans_multiple(self):
        """Test that multiple banned users are reactivated if their ban_expires_at is reached."""
        from communities.tasks import reactivate_expired_bans
        user4 = User.objects.create_user(username='other', email='other@example.com', password='TestPass123!')
        other_profile, _ = UserProfile.objects.get_or_create(user=user4)
        UserProfile.objects.filter(user=user4).update(
            bio='Other member',
            phone_number='+1111113004',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        other_profile.refresh_from_db()
        membership1 = CommunityMembership.objects.create(
            community=self.community,
            user=self.member_profile,
            role=self.member_role,
            status='banned',
            banned_by=self.creator_profile,
            ban_reason='Test ban',
            banned_at=timezone.now() - timedelta(days=2),
            ban_expires_at=timezone.now() - timedelta(hours=1)
        )
        membership2 = CommunityMembership.objects.create(
            community=self.community,
            user=other_profile,
            role=self.member_role,
            status='banned',
            banned_by=self.creator_profile,
            ban_reason='Test ban',
            banned_at=timezone.now() - timedelta(days=2),
            ban_expires_at=timezone.now() - timedelta(hours=2)
        )
        reactivate_expired_bans()
        membership1.refresh_from_db()
        membership2.refresh_from_db()
        self.assertEqual(membership1.status, 'active')
        self.assertIsNone(membership1.ban_expires_at)
        self.assertEqual(membership2.status, 'active')
        self.assertIsNone(membership2.ban_expires_at)

    def test_reactivate_expired_bans_none(self):
        """Test that the task does nothing if there are no banned users."""
        from communities.tasks import reactivate_expired_bans
        # No banned users
        reactivate_expired_bans()
        # Should not raise or change anything
    def test_reactivate_expired_bans(self):
        """Test that banned users are reactivated when ban_expires_at is reached."""
        from communities.tasks import reactivate_expired_bans
        # Ban member with expiration in the past
        membership = CommunityMembership.objects.create(
            community=self.community,
            user=self.member_profile,
            role=self.member_role,
            status='banned',
            banned_by=self.creator_profile,
            ban_reason='Test ban',
            banned_at=timezone.now() - timedelta(days=2),
            ban_expires_at=timezone.now() - timedelta(hours=1)
        )
        # Run the task
        reactivate_expired_bans()
        membership.refresh_from_db()
        self.assertEqual(membership.status, 'active')
        self.assertIsNone(membership.ban_expires_at)
        self.assertIsNone(membership.banned_by)
        self.assertEqual(membership.ban_reason, '')
    """Test all community-related Celery tasks."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='creator',
            email='creator@example.com',
            password='TestPass123!'
        )
        self.user2 = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='TestPass123!'
        )

        self.user3 = User.objects.create_user(
            username='applicant',
            email='applicant@example.com',
            password='TestPass123!'
        )

        # Create or ensure user profiles
        self.creator_profile, _ = UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.filter(user=self.user1).update(
            bio='Community creator',
            phone_number='+1111113001',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.creator_profile.refresh_from_db()

        self.member_profile, _ = UserProfile.objects.get_or_create(user=self.user2)
        UserProfile.objects.filter(user=self.user2).update(
            bio='Community member',
            phone_number='+1111113002',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.member_profile.refresh_from_db()

        self.applicant_profile, _ = UserProfile.objects.get_or_create(user=self.user3)
        UserProfile.objects.filter(user=self.user3).update(
            bio='Community applicant',
            phone_number='+1111113003',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.applicant_profile.refresh_from_db()

        # Create test community (restricted type for join requests)
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            creator=self.creator_profile,
            community_type='restricted',  # Changed from 'public'
            is_active=True
        )

        # Create community role
        self.member_role = CommunityRole.objects.create(
            community=self.community,
            name='member',
            permissions={'can_post': True},
            is_default=True
        )

    def test_update_community_analytics(self):
        """Test community analytics update task."""
        # Create some memberships
        CommunityMembership.objects.create(
            community=self.community,
            user=self.creator_profile,
            role=self.member_role,
            status='active',
            last_active=timezone.now()
        )
        CommunityMembership.objects.create(
            community=self.community,
            user=self.member_profile,
            role=self.member_role,
            status='active',
            last_active=timezone.now() - timedelta(days=10)
        )

        # Run the task
        result = update_community_analytics()

        # Check that analytics were created
        self.assertIn('Updated analytics for', result)

        # Check that community metrics were updated
        self.community.refresh_from_db()
        self.assertEqual(self.community.members_count, 2)

        # Check that system metrics were created
        metrics = SystemMetric.objects.filter(
            metric_type='community_engagement'
        )
        self.assertGreater(metrics.count(), 0)

    def test_cleanup_expired_community_invitations(self):
        """Test expired invitations cleanup task."""
        # Create expired invitation
        expired_invitation = CommunityInvitation.objects.create(
            community=self.community,
            inviter=self.creator_profile,
            invitee=self.member_profile,
            expires_at=timezone.now() - timedelta(days=1),
            status='pending'
        )

        # Create valid invitation with different invitee
        valid_invitation = CommunityInvitation.objects.create(
            community=self.community,
            inviter=self.creator_profile,
            invitee=self.applicant_profile,
            expires_at=timezone.now() + timedelta(days=1),
            status='pending'
        )

        # Run the task
        result = cleanup_expired_community_invitations()

        # Check results
        self.assertIn('Marked 1 community invitations as expired', result)

        expired_invitation.refresh_from_db()
        valid_invitation.refresh_from_db()

        self.assertEqual(expired_invitation.status, 'expired')
        self.assertEqual(valid_invitation.status, 'pending')

    def test_update_community_member_counts(self):
        """Test member count update task."""
        # Create memberships
        CommunityMembership.objects.create(
            community=self.community,
            user=self.creator_profile,
            role=self.member_role,
            status='active'
        )
        CommunityMembership.objects.create(
            community=self.community,
            user=self.member_profile,
            role=self.member_role,
            status='banned'  # This should not be counted
        )

        # Set incorrect count
        self.community.members_count = 5
        self.community.save()

        # Run the task
        result = update_community_member_counts()

        # Check results
        self.assertIn('Updated member counts for', result)

        self.community.refresh_from_db()
        # Only active members counted
        self.assertEqual(self.community.members_count, 1)

    def test_cleanup_inactive_communities(self):
        """Test inactive communities cleanup task."""
        # Create an old community
        old_community = Community.objects.create(
            name='Old Community',
            slug='old-community',
            creator=self.creator_profile,
            is_active=True
        )

        # Manually set the updated_at to an old date (bypass auto_now)
        Community.objects.filter(id=old_community.id).update(
            updated_at=timezone.now() - timedelta(days=100)
        )

        # Run the task
        result = cleanup_inactive_communities()

        # Check results
        self.assertIn('communities as inactive', result)

        old_community.refresh_from_db()
        self.assertFalse(old_community.is_active)

        # Current community should still be active
        self.community.refresh_from_db()
        self.assertTrue(self.community.is_active)

    def test_process_community_join_requests(self):
        """Test join request processing task for restricted communities."""
        # Ensure the default role is marked as default
        self.member_role.is_default = True
        self.member_role.save()

        # Create old join request for restricted community
        join_request = CommunityJoinRequest.objects.create(
            community=self.community,  # This is now restricted type
            user=self.applicant_profile,
            status='pending'
        )

        # Manually set the created_at to an old date (bypass auto_now_add)
        CommunityJoinRequest.objects.filter(id=join_request.id).update(
            created_at=timezone.now() - timedelta(days=8)  # 8 days old
        )

        # Run the task
        result = process_community_join_requests()

        # Check results - task should mention processing
        self.assertIn('auto-approved', result)

        join_request.refresh_from_db()
        self.assertEqual(join_request.status, 'approved')

        # Check that membership was created
        membership = CommunityMembership.objects.filter(
            community=self.community,
            user=self.applicant_profile
        ).first()
        self.assertIsNotNone(membership)
        if membership:
            self.assertEqual(membership.status, 'active')

    def test_validate_community_access_rules(self):
        """Test community access rules validation task."""
        # Create expired invitation for private community
        private_community = Community.objects.create(
            name='Private Community',
            slug='private-community',
            creator=self.creator_profile,
            community_type='private'
        )

        # Create expired invitation
        expired_invitation = CommunityInvitation.objects.create(
            community=private_community,
            inviter=self.creator_profile,
            invitee=self.member_profile,
            expires_at=timezone.now() - timedelta(days=1),
            status='pending'
        )

        # Create invalid join request for public community
        public_community = Community.objects.create(
            name='Public Community',
            slug='public-community',
            creator=self.creator_profile,
            community_type='public'
        )

        invalid_join_request = CommunityJoinRequest.objects.create(
            community=public_community,
            user=self.applicant_profile,
            status='pending'
        )

        # Run the task
        result = validate_community_access_rules()

        # Check results - the actual message format
        self.assertIn('Rejected', result)
        self.assertIn('invalid join requests', result)

        # Check expired invitation was marked as expired
        expired_invitation.refresh_from_db()
        self.assertEqual(expired_invitation.status, 'expired')

        # Check invalid join request was rejected
        invalid_join_request.refresh_from_db()
        self.assertEqual(invalid_join_request.status, 'rejected')

    def test_task_error_handling(self):
        """Test that tasks handle errors gracefully."""
        # Delete the community to cause an error
        self.community.delete()

        # Tasks should handle errors and return appropriate messages
        result = update_community_analytics()
        # Analytics task handles missing data gracefully
        self.assertIn('Updated analytics for', result)

        result = cleanup_expired_community_invitations()
        # This shouldn't error even with no data
        self.assertIn('Marked 0 community invitations', result)

    def test_community_analytics_without_posts(self):
        """Test analytics task when no posts exist."""
        # Run task without any posts
        result = update_community_analytics()

        self.assertIn('Updated analytics for', result)

        # Should still create metrics even with no posts
        metrics = SystemMetric.objects.filter(
            metric_type='community_engagement'
        )
        self.assertGreater(metrics.count(), 0)
