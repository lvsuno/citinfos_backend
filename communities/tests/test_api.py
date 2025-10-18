"""API tests for communities app."""

from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from accounts.models import UserProfile
from core.jwt_test_mixin import JWTAuthTestMixin
from communities.models import (
    Community, CommunityMembership, CommunityInvitation,
    CommunityRole, CommunityModeration
)


class CommunityAPITestCase(JWTAuthTestMixin, APITestCase):
    """Test case for Community API endpoints."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='TestPass123!'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='TestPass123!'
        )

        # Create or ensure user profiles (safe pattern to avoid duplicate OneToOne/NOT NULL errors)
        self.profile1, _ = UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.filter(user=self.user1).update(
            bio='Test user 1',
            phone_number='+1111112001',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.profile1.refresh_from_db()

        self.profile2, _ = UserProfile.objects.get_or_create(user=self.user2)
        UserProfile.objects.filter(user=self.user2).update(
            bio='Test user 2',
            phone_number='+1111112002',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.profile2.refresh_from_db()

        # Create test community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='A test community',
            creator=self.profile1,
            community_type='public'
        )

        # Create community role
        self.member_role = CommunityRole.objects.create(
            community=self.community,
            name='Member',
            permissions={'can_post': True, 'can_comment': True},
            is_default=True
        )

        # API client already exists as self.client

    def authenticate_user1(self):  # retained name for existing tests
        self.authenticate(self.user1)

    def authenticate_user2(self):
        self.authenticate(self.user2)

    def clear_auth(self):
        self.client.credentials()  # remove Authorization header

    def test_community_list_api(self):
        """Test community list endpoint."""
        url = reverse('community-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Community')

    def test_community_create_api(self):
        """Test community creation endpoint."""
        self.authenticate_user1()

        url = reverse('community-list')
        data = {
            'name': 'New Community',
            'slug': 'new-community',
            'description': 'A new test community',
            'community_type': 'private'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Community')
        self.assertEqual(response.data['creator_username'], 'testuser1')

        # Verify community was created
        community = Community.objects.get(slug='new-community')
        self.assertEqual(community.name, 'New Community')
        self.assertEqual(community.creator, self.profile1)

    def test_community_create_unauthenticated(self):
        """Test community creation requires authentication."""
        url = reverse('community-list')
        data = {
            'name': 'Unauthorized Community',
            'description': 'Should not be created'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_community_detail_api(self):
        """Test community detail endpoint."""
        url = reverse('community-detail', kwargs={'slug': self.community.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Community')
        self.assertEqual(response.data['slug'], 'test-community')

    def test_community_update_api(self):
        """Test community update endpoint."""
        self.authenticate_user1()

        url = reverse('community-detail', kwargs={'slug': self.community.slug})
        data = {
            'name': 'Updated Community',
            'description': 'Updated description'
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Community')

        # Verify community was updated
        self.community.refresh_from_db()
        self.assertEqual(self.community.name, 'Updated Community')

    def test_community_delete_api(self):
        """Test community deletion endpoint."""
        self.authenticate_user1()

        url = reverse('community-detail', kwargs={'slug': self.community.slug})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify community was soft deleted
        self.community.refresh_from_db()
        self.assertTrue(self.community.is_deleted)

    def test_community_join_api(self):
        """Test community join endpoint."""
        self.authenticate_user2()

        url = reverse('community-join', kwargs={'slug': self.community.slug})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Joined community successfully', response.data['detail'])

        # Verify membership was created
        membership = CommunityMembership.objects.filter(
            community=self.community,
            user=self.profile2
        ).first()
        self.assertIsNotNone(membership)

    def test_community_leave_api(self):
        """Test community leave endpoint."""
        self.authenticate_user2()

        # First join the community
        CommunityMembership.objects.create(
            community=self.community,
            user=self.profile2,
            role=self.member_role
        )

        url = reverse('community-leave', kwargs={'slug': self.community.slug})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Left community successfully', response.data['detail'])

    def test_community_members_api(self):
        """Test community members endpoint."""
        # Create membership
        CommunityMembership.objects.create(
            community=self.community,
            user=self.profile2,
            role=self.member_role
        )

        url = reverse(
            'community-members',
            kwargs={'slug': self.community.slug}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class CommunityMembershipAPITestCase(JWTAuthTestMixin, APITestCase):
    """Test case for CommunityMembership API endpoints."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='TestPass123!'
        )

        # Create or ensure user profile (safe pattern)
        self.profile1, _ = UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.filter(user=self.user1).update(
            bio='Test user 1',
            phone_number='+1111112101',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.profile1.refresh_from_db()

        # Create test community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='A test community',
            creator=self.profile1,
            community_type='public'
        )

        # Create community role
        self.member_role = CommunityRole.objects.create(
            community=self.community,
            name='Member',
            permissions={'can_post': True},
            is_default=True
        )

        # Create membership
        self.membership = CommunityMembership.objects.create(
            community=self.community,
            user=self.profile1,
            role=self.member_role
        )

        # Authenticate default user
        self.authenticate(self.user1)

    def test_membership_list_api(self):
        """Test membership list endpoint."""
        url = reverse('community-membership-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_membership_detail_api(self):
        """Test membership detail endpoint."""
        url = reverse(
            'community-membership-detail',
            kwargs={'pk': self.membership.pk}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(self.membership.id))


class CommunityInvitationAPITestCase(JWTAuthTestMixin, APITestCase):
    """Test case for CommunityInvitation API endpoints."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='TestPass123!'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='TestPass123!'
        )

        # Create or ensure user profiles (safe pattern)
        self.profile1, _ = UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.filter(user=self.user1).update(
            bio='Test user 1',
            phone_number='+1111112201',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.profile1.refresh_from_db()

        self.profile2, _ = UserProfile.objects.get_or_create(user=self.user2)
        UserProfile.objects.filter(user=self.user2).update(
            bio='Test user 2',
            phone_number='+1111112202',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.profile2.refresh_from_db()

        # Create test community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='A test community',
            creator=self.profile1,
            community_type='private'
        )

        # Create invitation
        self.invitation = CommunityInvitation.objects.create(
            community=self.community,
            inviter=self.profile1,
            invitee=self.profile2,
            message='Join our community!',
            expires_at=timezone.now() + timedelta(days=7)
        )

    def login_user1(self):
        self.authenticate(self.user1)

    def login_user2(self):
        self.authenticate(self.user2)

    def test_invitation_list_api(self):
        """Test invitation list endpoint."""
        self.login_user1()

        url = reverse('community-invitation-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_invitation_create_api(self):
        """Test invitation creation endpoint."""
        self.login_user1()

        # Create another user to invite
        user3 = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='TestPass123!'
        )
        profile3, _ = UserProfile.objects.get_or_create(user=user3)
        UserProfile.objects.filter(user=user3).update(
            bio='Test user 3',
            phone_number='+1111112303',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        profile3.refresh_from_db()

        url = reverse('community-invitation-list')
        data = {
            'community': self.community.id,
            'invitee': profile3.id,
            'message': 'Please join us!',
            'expires_at': (timezone.now() + timedelta(days=7)).isoformat()
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['inviter_username'], 'testuser1')

    def test_invitation_accept_api(self):
        """Test invitation accept endpoint."""
        self.login_user2()

        url = reverse(
            'community-invitation-accept',
            kwargs={'pk': self.invitation.pk}
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('accepted successfully', response.data['detail'])

        # Verify invitation status changed
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, 'accepted')

    def test_invitation_decline_api(self):
        """Test invitation decline endpoint."""
        self.login_user2()

        url = reverse(
            'community-invitation-decline',
            kwargs={'pk': self.invitation.pk}
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('declined successfully', response.data['detail'])

        # Verify invitation status changed
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, 'declined')


class CommunityRoleAPITestCase(JWTAuthTestMixin, APITestCase):
    """Test case for CommunityRole API endpoints."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='TestPass123!'
        )

        # Create or ensure user profile (safe pattern)
        self.profile1, _ = UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.filter(user=self.user1).update(
            bio='Test user 1',
            phone_number='+1111112401',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.profile1.refresh_from_db()

        # Create test community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='A test community',
            creator=self.profile1,
            community_type='public'
        )

        # Create community role
        self.role = CommunityRole.objects.create(
            community=self.community,
            name='Member',
            permissions={'can_post': True},
            is_default=True
        )

        # Authenticate default user
        self.authenticate(self.user1)

    def test_role_list_api(self):
        """Test role list endpoint."""
        url = reverse('community-role-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_role_create_api(self):
        """Test role creation endpoint."""
        url = reverse('community-role-list')
        data = {
            'community': self.community.id,
            'name': 'Moderator',
            'permissions': {'can_post': True, 'can_moderate': True},
            'color': '#FF0000',
            'is_default': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Moderator')

    def test_role_detail_api(self):
        """Test role detail endpoint."""
        url = reverse('community-role-detail', kwargs={'pk': self.role.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Member')


class CommunityModerationAPITestCase(JWTAuthTestMixin, APITestCase):
    """Test case for CommunityModeration API endpoints."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='TestPass123!'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='TestPass123!'
        )

        # Create or ensure user profiles (safe pattern)
        self.profile1, _ = UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.filter(user=self.user1).update(
            bio='Test user 1',
            phone_number='+1111112501',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.profile1.refresh_from_db()

        self.profile2, _ = UserProfile.objects.get_or_create(user=self.user2)
        UserProfile.objects.filter(user=self.user2).update(
            bio='Test user 2',
            phone_number='+1111112502',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.profile2.refresh_from_db()

        # Create test community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='A test community',
            creator=self.profile1,
            community_type='public'
        )

        # Create moderation action
        self.moderation = CommunityModeration.objects.create(
            community=self.community,
            moderator=self.profile1,
            target=self.profile2,
            action_type='warning',
            reason='Spam posting'
        )

        # Authenticate default user
        self.authenticate(self.user1)

    def test_moderation_list_api(self):
        """Test moderation list endpoint."""
        url = reverse('community-moderation-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_moderation_create_api(self):
        """Test moderation creation endpoint."""
        url = reverse('community-moderation-list')
        data = {
            'community': self.community.id,
            'target': self.profile2.id,
            'action_type': 'ban',
            'reason': 'Inappropriate behavior'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['action_type'], 'ban')

    def test_moderation_detail_api(self):
        """Test moderation detail endpoint."""
        url = reverse(
            'community-moderation-detail',
            kwargs={'pk': self.moderation.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action_type'], 'warning')
