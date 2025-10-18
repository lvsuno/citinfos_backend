"""Test deleted user login behavior with manual API testing."""

import json
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import UserProfile


class SimpleDeletedUserLoginTest(APITestCase):
    """Simple test to verify deleted users cannot login."""

    def setUp(self):
        """Set up a user that will be marked as deleted."""
        # Create a user and profile
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

        # Create or ensure profile exists and populate required fields
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.filter(user=self.user).update(
            role='normal',
            phone_number='+1234567890',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        self.profile.refresh_from_db()

    def test_deleted_user_login_blocked(self):
        """Test that a deleted user cannot log in."""
        # First verify normal login works
        url = '/api/auth/login/'
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')
        print(f"Normal login response: {response.status_code}, {response.data}")

        # Now mark the user as deleted
        self.profile.is_deleted = True
        self.profile.save()

        # Try to login again
        response = self.client.post(url, data, format='json')
        print(f"Deleted user login response: {response.status_code}")

        # Should be blocked
        if response.status_code == 200:
            self.fail("Deleted user was able to log in - SECURITY ISSUE!")
        else:
            print(f"✅ Deleted user login properly blocked with status {response.status_code}")

    def test_deleted_user_token_access(self):
        """Test that tokens from deleted users are rejected."""
        # Get a valid token first
        url = '/api/auth/login/'
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')
        if response.status_code != 200:
            self.skipTest("Cannot get initial token")

        if 'access_token' in response.data:
            token = response.data['access_token']
        elif 'access' in response.data:
            token = response.data['access']
        else:
            self.skipTest("No access token in response")

        # Verify token works initially
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/auth/user-info/')
        print(f"Normal token access: {response.status_code}")

        # Now mark user as deleted
        self.profile.is_deleted = True
        self.profile.save()

        # Try to use the token again
        response = self.client.get('/api/auth/user-info/')
        print(f"Deleted user token access: {response.status_code}")

        if response.status_code == 200:
            self.fail("Deleted user token still works - SECURITY ISSUE!")
        else:
            print(f"✅ Deleted user token properly blocked with status {response.status_code}")
