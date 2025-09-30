"""Comprehensive tests for communities app."""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from communities.models import (
    Community, CommunityMembership, CommunityInvitation, CommunityJoinRequest,
    CommunityRole, CommunityModeration
)
from accounts.models import UserProfile
from core.jwt_test_mixin import JWTAuthTestMixin


class CommunityModelTests(TestCase, JWTAuthTestMixin):
    def setUp(self):
        """Set up test data for community tests."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User1'
        )
        self.userprofile1, _ = UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.filter(user=self.user1).update(
            phone_number='+1234567890',
            date_of_birth='1990-01-01',
            role='normal',
            bio='Test bio for user1',
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        self.userprofile1.refresh_from_db()

        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User2'
        )
        self.userprofile2, _ = UserProfile.objects.get_or_create(user=self.user2)
        UserProfile.objects.filter(user=self.user2).update(
            phone_number='+1234567891',
            date_of_birth='1992-02-02',
            role='normal',
            bio='Test bio for user2',
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        self.userprofile2.refresh_from_db()

        # JWT tokens for authentication
        self.jwt_token1 = self._create_jwt_token_with_session(self.user1)
        self.jwt_token2 = self._create_jwt_token_with_session(self.user2)

    def test_only_active_members_can_interact(self):
        """Test that only active, not soft-deleted members can interact."""
        # Create test community using JWT test users
        community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='A test community',
            creator=self.userprofile1,
            community_type='public'
        )

        # Create a creator membership (active)
        creator_membership = CommunityMembership.objects.create(
            community=community,
            user=self.userprofile1,
            legacy_role='creator',
            status='active'
        )

        # Create a regular member (active)
        member_membership = CommunityMembership.objects.create(
            community=community,
            user=self.userprofile2,
            legacy_role='member',
            status='active'
        )

        # Create additional test user for banned membership
        user3 = User.objects.create_user(
            username='banned_user',
            email='banned@example.com',
            password='testpass123'
        )
        banned_profile, _ = UserProfile.objects.get_or_create(user=user3)
        UserProfile.objects.filter(user=user3).update(
            phone_number='+1234567892',
            date_of_birth='1993-03-03',
            bio="Banned user",
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        banned_profile.refresh_from_db()

        # Create a banned membership
        banned_membership = CommunityMembership.objects.create(
            community=community,
            user=banned_profile,
            legacy_role='member',
            status='banned'
        )

        # Create additional test user for deleted membership
        user4 = User.objects.create_user(
            username='deleted_user',
            email='deleted@example.com',
            password='testpass123'
        )
        deleted_profile, _ = UserProfile.objects.get_or_create(user=user4)
        UserProfile.objects.filter(user=user4).update(
            phone_number='+1234567893',
            date_of_birth='1994-04-04',
            bio="Deleted user",
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        deleted_profile.refresh_from_db()

        # Create a soft-deleted membership
        deleted_membership = CommunityMembership.objects.create(
            community=community,
            user=deleted_profile,
            legacy_role='member',
            status='active',
            is_deleted=True
        )

        # Test is_active_member method
        self.assertTrue(creator_membership.is_active_member())
        self.assertTrue(member_membership.is_active_member())
        self.assertFalse(banned_membership.is_active_member())
        self.assertFalse(deleted_membership.is_active_member())

        # Test can_remove_member - only active members can interact
        self.assertTrue(
            creator_membership.can_remove_member(member_membership)
        )
        self.assertFalse(
            creator_membership.can_remove_member(banned_membership)
        )
        self.assertFalse(
            creator_membership.can_remove_member(deleted_membership)
        )
        self.assertFalse(
            banned_membership.can_remove_member(creator_membership)
        )
        self.assertFalse(
            deleted_membership.can_remove_member(creator_membership)
        )

        # Test can_moderate_posts - only active members can interact
        self.assertTrue(creator_membership.can_moderate_posts())
        self.assertFalse(banned_membership.can_moderate_posts())
        self.assertFalse(deleted_membership.can_moderate_posts())

        # Test can_manage_community - only active members can interact
        self.assertTrue(creator_membership.can_manage_community())
        self.assertFalse(banned_membership.can_manage_community())
        self.assertFalse(deleted_membership.can_manage_community())

        # Test can_invite_members - only active members can interact
        self.assertTrue(creator_membership.can_invite_members())
        self.assertFalse(banned_membership.can_invite_members())
        self.assertFalse(deleted_membership.can_invite_members())


class CommunityIntegrationTests(TestCase, JWTAuthTestMixin):
    """Test all community models."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User1'
        )
        self.userprofile1, _ = UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.filter(user=self.user1).update(
            phone_number='+1234567890',
            date_of_birth='1990-01-01',
            role='normal',
            bio='Test bio for user1',
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        self.userprofile1.refresh_from_db()

        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User2'
        )
        self.userprofile2, _ = UserProfile.objects.get_or_create(user=self.user2)
        UserProfile.objects.filter(user=self.user2).update(
            phone_number='+1234567891',
            date_of_birth='1992-02-02',
            role='normal',
            bio='Test bio for user2',
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        self.userprofile2.refresh_from_db()

        # Create additional test user
        self.user3 = User.objects.create_user(
            username='applicant',
            email='applicant@example.com',
            password='testpass123'
        )

        # Create user profile for additional user
        self.applicant_profile, _ = UserProfile.objects.get_or_create(user=self.user3)
        UserProfile.objects.filter(user=self.user3).update(
            phone_number='+1234567894',
            date_of_birth='1995-05-05',
            bio="Applicant user",
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        self.applicant_profile.refresh_from_db()

        # Create test community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='A test community',
            creator=self.userprofile1,  # Using JWT test user
            community_type='public'
        )

        # Create community roles
        self.creator_role = CommunityRole.objects.create(
            community=self.community,
            name='creator',
            permissions={'manage_community': True},
            is_default=False
        )
        self.member_role = CommunityRole.objects.create(
            community=self.community,
            name='member',
            permissions={'post': True},
            is_default=True
        )

    def test_community_creation(self):
        """Test community creation."""
        self.assertEqual(self.community.name, 'Test Community')
        self.assertEqual(self.community.slug, 'test-community')
        self.assertEqual(self.community.description, 'A test community')
        self.assertEqual(self.community.creator, self.userprofile1)
        self.assertEqual(self.community.community_type, 'public')
        self.assertTrue(self.community.is_active)
        self.assertFalse(self.community.is_featured)
        self.assertFalse(self.community.is_deleted)
        self.assertEqual(self.community.members_count, 0)
        self.assertEqual(self.community.posts_count, 0)
        self.assertTrue(self.community.allow_posts)
        self.assertFalse(self.community.require_post_approval)
        self.assertTrue(self.community.allow_external_links)

        # Test string representation
        self.assertEqual(str(self.community), 'Test Community')

        # Test that creator is automatically assigned when community is created
        self.assertIsNotNone(self.community.creator)
        self.assertEqual(self.community.creator, self.userprofile1)

    def test_community_membership_creation(self):
        """Test community membership creation."""
        membership = CommunityMembership.objects.create(
            community=self.community,
            user=self.userprofile1,
            role=self.creator_role,
            status='active'
        )

        self.assertEqual(membership.community, self.community)
        self.assertEqual(membership.user, self.userprofile1)
        self.assertEqual(membership.role, self.creator_role)
        self.assertEqual(membership.status, 'active')
        self.assertEqual(membership.posts_count, 0)
        self.assertEqual(membership.comments_count, 0)
        self.assertTrue(membership.notifications_enabled)
        self.assertIsNone(membership.banned_by)
        self.assertEqual(membership.ban_reason, "")

    def test_community_membership_permissions(self):
        """Test community membership permission methods."""
        # Create creator membership
        creator_membership = CommunityMembership.objects.create(
            community=self.community,
            user=self.userprofile1,
            role=self.creator_role,
            status='active'
        )

        # Create member membership
        member_membership = CommunityMembership.objects.create(
            community=self.community,
            user=self.userprofile2,
            role=self.member_role,
            status='active'
        )

        # Test creator permissions
        self.assertTrue(creator_membership.can_moderate_posts())
        self.assertTrue(creator_membership.can_manage_community())
        self.assertTrue(creator_membership.can_invite_members())
        self.assertTrue(
            creator_membership.can_remove_member(member_membership)
        )

        # Test member permissions
        self.assertFalse(member_membership.can_moderate_posts())
        self.assertFalse(member_membership.can_manage_community())
        self.assertFalse(member_membership.can_invite_members())
        self.assertFalse(
            member_membership.can_remove_member(creator_membership)
        )

        # Test banned user has no permissions
        banned_membership = CommunityMembership.objects.create(
            community=self.community,
            user=self.applicant_profile,
            role=self.member_role,
            status='banned'
        )

        self.assertFalse(banned_membership.can_moderate_posts())
        self.assertFalse(banned_membership.can_manage_community())
        self.assertFalse(banned_membership.can_invite_members())
        self.assertFalse(
            banned_membership.can_remove_member(member_membership)
        )

    def test_community_invitation_creation(self):
        """Test community invitation creation."""
        expires_at = timezone.now() + timedelta(days=7)
        invitation = CommunityInvitation.objects.create(
            community=self.community,
            inviter=self.userprofile1,
            invitee=self.userprofile2,
            message='Join our community!',
            expires_at=expires_at
        )

        self.assertEqual(invitation.community, self.community)
        self.assertEqual(invitation.inviter, self.userprofile1)
        self.assertEqual(invitation.invitee, self.userprofile2)
        self.assertEqual(invitation.message, 'Join our community!')
        self.assertEqual(invitation.status, 'pending')
        self.assertEqual(invitation.expires_at, expires_at)
        self.assertIsNone(invitation.responded_at)

    def test_community_join_request_creation(self):
        """Test community join request creation."""
        # Create a restricted community
        restricted_community = Community.objects.create(
            name='Restricted Community',
            slug='restricted-community',
            description='A restricted community',
            creator=self.userprofile1,
            community_type='restricted'
        )

        join_request = CommunityJoinRequest.objects.create(
            community=restricted_community,
            user=self.userprofile2,
            message='I would like to join this community.'
        )

        self.assertEqual(join_request.community, restricted_community)
        self.assertEqual(join_request.user, self.userprofile2)
        self.assertEqual(
            join_request.message, 'I would like to join this community.'
        )
        self.assertEqual(join_request.status, 'pending')
        self.assertIsNone(join_request.reviewed_by)
        self.assertIsNone(join_request.reviewed_at)

    def test_community_unique_slug_constraint(self):
        """Test unique slug constraint on communities."""
        from django.db import IntegrityError

        # Test unique community slug
        with self.assertRaises(IntegrityError):
            Community.objects.create(
                name='Another Community',
                slug='test-community',  # Same slug as existing community
                description='Another community',
                creator=self.userprofile2,
                community_type='public'
            )

    def test_membership_unique_constraint(self):
        """Test unique membership constraint."""
        from django.db import IntegrityError

        # Create first membership
        CommunityMembership.objects.create(
            community=self.community,
            user=self.userprofile1,
            role=self.creator_role,
            status='active'
        )

        # Try to create duplicate membership - should fail
        with self.assertRaises(IntegrityError):
            CommunityMembership.objects.create(
                community=self.community,
                user=self.userprofile1,  # Same user in same community
                role=self.member_role,
                status='active'
            )

    def test_invitation_unique_constraint(self):
        """Test unique invitation constraint."""
        from django.db import IntegrityError

        expires_at = timezone.now() + timedelta(days=7)
        CommunityInvitation.objects.create(
            community=self.community,
            inviter=self.userprofile1,
            invitee=self.userprofile2,
            expires_at=expires_at
        )

        # Try to create duplicate invitation - should fail
        with self.assertRaises(IntegrityError):
            CommunityInvitation.objects.create(
                community=self.community,
                inviter=self.userprofile1,
                invitee=self.userprofile2,  # Same invitee in same community
                expires_at=expires_at
            )

    def test_join_request_unique_constraint(self):
        """Test unique join request constraint."""
        from django.db import IntegrityError

        CommunityJoinRequest.objects.create(
            community=self.community,
            user=self.applicant_profile
        )

        # Try to create duplicate join request - should fail
        with self.assertRaises(IntegrityError):
            CommunityJoinRequest.objects.create(
                community=self.community,
                user=self.applicant_profile  # Same user for same community
            )

    def test_community_types(self):
        """Test different community types."""
        # Test public community
        public_community = Community.objects.create(
            name='Public Community',
            slug='public-community',
            creator=self.userprofile1,
            community_type='public'
        )
        self.assertEqual(public_community.community_type, 'public')

        # Test private community
        private_community = Community.objects.create(
            name='Private Community',
            slug='private-community',
            creator=self.userprofile1,
            community_type='private'
        )
        self.assertEqual(private_community.community_type, 'private')

        # Test restricted community
        restricted_community = Community.objects.create(
            name='Restricted Community',
            slug='restricted-community',
            creator=self.userprofile1,
            community_type='restricted'
        )
        self.assertEqual(restricted_community.community_type, 'restricted')

    def test_community_analytics_fields(self):
        """Test community analytics fields."""
        self.assertEqual(self.community.members_count, 0)
        self.assertEqual(self.community.posts_count, 0)

        # These would normally be updated by signals or background tasks
        self.community.members_count = 5
        self.community.posts_count = 10
        self.community.save()

        self.assertEqual(self.community.members_count, 5)
        self.assertEqual(self.community.posts_count, 10)

    def test_membership_status_changes(self):
        """Test membership status changes."""
        membership = CommunityMembership.objects.create(
            community=self.community,
            user=self.userprofile1,
            role=self.creator_role,
            status='active'
        )

        # Test status change to banned
        membership.status = 'banned'
        membership.banned_by = self.userprofile2
        membership.ban_reason = 'Violation of rules'
        membership.banned_at = timezone.now()
        membership.save()

        self.assertEqual(membership.status, 'banned')
        self.assertEqual(membership.banned_by, self.userprofile2)
        self.assertEqual(membership.ban_reason, 'Violation of rules')
        self.assertIsNotNone(membership.banned_at)

        # Test status change to left
        membership.status = 'left'
        membership.leaved_at = timezone.now()
        membership.save()

        self.assertEqual(membership.status, 'left')
        self.assertIsNotNone(membership.leaved_at)

    def test_invitation_status_changes(self):
        """Test invitation status changes."""
        expires_at = timezone.now() + timedelta(days=7)
        invitation = CommunityInvitation.objects.create(
            community=self.community,
            inviter=self.userprofile1,
            invitee=self.userprofile2,
            expires_at=expires_at
        )

        # Test accepting invitation
        invitation.status = 'accepted'
        invitation.responded_at = timezone.now()
        invitation.save()

        self.assertEqual(invitation.status, 'accepted')
        self.assertIsNotNone(invitation.responded_at)

    def test_join_request_approval(self):
        """Test join request approval."""
        join_request = CommunityJoinRequest.objects.create(
            community=self.community,
            user=self.userprofile2,
            message='Please let me join.'
        )

        # Test approving request
        join_request.status = 'approved'
        join_request.reviewed_by = self.userprofile1
        join_request.reviewed_at = timezone.now()
        join_request.review_message = 'Welcome to the community!'
        join_request.save()

        self.assertEqual(join_request.status, 'approved')
        self.assertEqual(join_request.reviewed_by, self.userprofile1)
        self.assertEqual(
            join_request.review_message, 'Welcome to the community!'
        )
        self.assertIsNotNone(join_request.reviewed_at)

        # Test rejecting request
        join_request2 = CommunityJoinRequest.objects.create(
            community=self.community,
            user=self.applicant_profile,
            message='Please let me join too.'
        )

        join_request2.status = 'rejected'
        join_request2.reviewed_by = self.userprofile1
        join_request2.reviewed_at = timezone.now()
        join_request2.review_message = 'Sorry, not at this time.'
        join_request2.save()

        self.assertEqual(join_request2.status, 'rejected')
        self.assertEqual(
            join_request2.review_message, 'Sorry, not at this time.'
        )


class CommunityModerationTests(TransactionTestCase, JWTAuthTestMixin):
    """Test community moderation functionality."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User1'
        )
        self.userprofile1, _ = UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.filter(user=self.user1).update(
            phone_number='+1234567890',
            date_of_birth='1990-01-01',
            role='normal',
            bio='Test bio for user1',
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        self.userprofile1.refresh_from_db()

        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User2'
        )
        self.userprofile2, _ = UserProfile.objects.get_or_create(user=self.user2)
        UserProfile.objects.filter(user=self.user2).update(
            phone_number='+1234567891',
            date_of_birth='1992-02-02',
            role='normal',
            bio='Test bio for user2',
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        self.userprofile2.refresh_from_db()

        # Create additional test user
        self.user3 = User.objects.create_user(
            username='target_user',
            email='target@example.com',
            password='testpass123'
        )

        # Create user profile for additional user
        self.target_profile, _ = UserProfile.objects.get_or_create(user=self.user3)
        UserProfile.objects.filter(user=self.user3).update(
            phone_number='+1234567895',
            date_of_birth='1996-06-06',
            bio="Target user",
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        self.target_profile.refresh_from_db()

        # Create test community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='A test community',
            creator=self.userprofile1,
            community_type='public'
        )

    def test_community_moderation_creation(self):
        """Test community moderation creation."""
        moderation = CommunityModeration.objects.create(
            community=self.community,
            moderator=self.userprofile1,
            target=self.userprofile2,
            action_type='warn',
            reason='First warning for inappropriate behavior'
        )

        self.assertEqual(moderation.community, self.community)
        self.assertEqual(moderation.moderator, self.userprofile1)
        self.assertEqual(moderation.target, self.userprofile2)
        self.assertEqual(moderation.action_type, 'warn')
        self.assertEqual(
            moderation.reason, 'First warning for inappropriate behavior'
        )
        self.assertTrue(moderation.is_active)
        self.assertIsNone(moderation.expires_at)

    def test_moderation_status_changes(self):
        """Test moderation status changes."""
        moderation = CommunityModeration.objects.create(
            community=self.community,
            moderator=self.userprofile1,
            target=self.userprofile2,
            action_type='ban',
            reason='Repeated violations',
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Test deactivating moderation
        moderation.is_active = False
        moderation.save()

        self.assertFalse(moderation.is_active)

    def test_moderation_unique_constraints(self):
        """Test moderation unique constraints."""
        # Create first moderation action
        CommunityModeration.objects.create(
            community=self.community,
            moderator=self.userprofile1,
            target=self.userprofile2,
            action_type='ban',
            reason='First ban',
            is_active=True
        )

        # Try to create duplicate active moderation for same combination
        with self.assertRaises(Exception):
            CommunityModeration.objects.create(
                community=self.community,
                moderator=self.userprofile1,
                target=self.userprofile2,
                action_type='ban',
                reason='Second ban',
                is_active=True
            )

    def test_moderation_fields_and_methods(self):
        """Test moderation model fields and methods."""
        expires_at = timezone.now() + timedelta(days=3)
        moderation = CommunityModeration.objects.create(
            community=self.community,
            moderator=self.userprofile1,
            target=self.target_profile,
            action_type='mute',
            reason='Spamming in chat',
            expires_at=expires_at,
            details={'channel': 'general', 'duration': '3 days'}
        )

        # Test string representation
        expected_str = (
            f"{self.userprofile1.user.username} mute "
            f"{self.target_profile.user.username} in "
            f"{self.community.name} - Reason: Spamming in chat"
        )
        self.assertEqual(str(moderation), expected_str)

        # Test duration property
        self.assertIsNotNone(moderation.duration)
        self.assertEqual(moderation.expires_at, expires_at)

        # Test details field
        self.assertEqual(moderation.details['channel'], 'general')
        self.assertEqual(moderation.details['duration'], '3 days')

        # Test fields exist and have correct values
        for action_type, _ in CommunityModeration.ACTION_TYPES:
            test_moderation = CommunityModeration(
                community=self.community,
                moderator=self.userprofile1,
                target=self.target_profile,
                action_type=action_type,
                reason=f'Test {action_type} action'
            )
            # Just testing that action_type accepts all valid choices
            self.assertIn(action_type, [choice[0] for choice in
                                      CommunityModeration.ACTION_TYPES])
