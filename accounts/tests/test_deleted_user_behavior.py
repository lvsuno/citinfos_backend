"""Test deleted user behavior - login prevention and content hiding."""

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import UserProfile
from accounts.tests.base import AccountsAPITestCase


class DeletedUserBehaviorTests(AccountsAPITestCase):
    """Test that deleted users cannot login and their content is hidden."""

    def setUp(self):
        """Set up test data including a user that will be deleted."""
        super().setUp()

        # Create a third user that will be marked as deleted
        self.deleted_user = User.objects.create_user(
            username='deleteduser',
            email='deleted@example.com',
            password='testpass123',
            first_name='Deleted',
            last_name='User'
        )
        self.deleted_profile, _ = UserProfile.objects.get_or_create(user=self.deleted_user)
        UserProfile.objects.filter(user=self.deleted_user).update(
            role='normal',
            bio='This user will be deleted',
            phone_number='+1234567892',
            date_of_birth='1992-01-01',
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        self.deleted_profile.refresh_from_db()

        # Create JWT token before deletion
        self.deleted_user_jwt = self._create_jwt_token_with_session(self.deleted_user)

        # Mark profile as deleted
        self.deleted_profile.is_deleted = True
        self.deleted_profile.save()

    def test_deleted_user_cannot_login_with_credentials(self):
        """Test that a deleted user cannot log in using username/password."""
        url = reverse('jwt_login')

        data = {
            'username': 'deleteduser',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')

        # Should fail to login
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertIn('Account not available', response.data['error'])

    def test_deleted_user_jwt_token_rejected(self):
        """Test that existing JWT tokens from deleted users are rejected."""
        # Try to use the JWT token created before deletion
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.deleted_user_jwt["access"]}')

        # Try to access a protected endpoint
        url = reverse('jwt_user_info')
        response = self.client.get(url)

        # Should be rejected
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_deleted_user_profile_not_accessible(self):
        """Test that deleted user profiles are not accessible via API."""
        # Authenticate as a normal user
        self.authenticate_user1()

        # Try to access the deleted user's profile
        url = f'/api/profiles/{self.deleted_profile.pk}/'
        response = self.client.get(url)

        # Should return 404 (not found) rather than the profile data
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deleted_user_not_in_user_list(self):
        """Test that deleted users don't appear in user list endpoints."""
        # Authenticate as a normal user
        self.authenticate_user1()

        # Get list of users
        url = '/api/profiles/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that deleted user is not in the results
        user_ids = [user['id'] for user in response.data.get('results', response.data)]
        self.assertNotIn(str(self.deleted_profile.pk), user_ids)

        # Check that active users are still present
        self.assertIn(str(self.user1_profile.pk), user_ids)
        self.assertIn(str(self.user2_profile.pk), user_ids)

    def test_middleware_blocks_deleted_user_requests(self):
        """Test that middleware intercepts and blocks requests from deleted users."""
        # This test simulates a scenario where a user gets deleted while having an active session

        # First, create a fresh token for a user who isn't deleted yet
        temp_user = User.objects.create_user(
            username='tempuser',
            email='temp@example.com',
            password='testpass123'
        )
        temp_profile, _ = UserProfile.objects.get_or_create(user=temp_user)
        UserProfile.objects.filter(user=temp_user).update(
            role='normal',
            bio='Temporary user',
            phone_number='+1234567893',
            date_of_birth='1993-01-01',
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        temp_profile.refresh_from_db()

        # Get a valid token
        temp_jwt = self._create_jwt_token_with_session(temp_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {temp_jwt["access"]}')

        # Verify the user can access endpoints initially
        url = reverse('jwt_user_info')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Now mark the user as deleted
        temp_profile.is_deleted = True
        temp_profile.save()

        # Try to access the same endpoint again
        response = self.client.get(url)

        # Should be blocked by middleware
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('User profile has been deleted', response.data.get('detail', ''))

    def test_deleted_user_refresh_token_rejected(self):
        """Test that refresh tokens from deleted users are rejected."""
        url = reverse('jwt_refresh')

        data = {
            'refresh': self.deleted_user_jwt['refresh']
        }

        response = self.client.post(url, data, format='json')

        # Should fail to refresh
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_active_user_can_still_login(self):
        """Test that active users can still login normally (control test)."""
        url = reverse('jwt_login')

        data = {
            'username': 'testuser1',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')

        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_active_user_profile_accessible(self):
        """Test that active user profiles are accessible (control test)."""
        # Authenticate as a normal user
        self.authenticate_user1()

        # Access another active user's profile
        url = f'/api/profiles/{self.user2_profile.pk}/'
        response = self.client.get(url)

        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.user2_profile.pk))
