"""Test refresh token behavior for deleted users."""

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase
from accounts.models import UserProfile


class RefreshTokenDeletedUserTest(APITestCase):
    """Test refresh token behavior for deleted users."""

    def setUp(self):
        """Set up a user that will be marked as deleted."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.filter(user=self.user).update(
            role='normal',
            phone_number='+1234567890',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        self.profile.refresh_from_db()

    def test_refresh_token_deleted_user(self):
        """Test that refresh tokens from deleted users are rejected."""
        # Get initial tokens
        url = '/api/auth/login/'
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        if 'refresh_token' in response.data:
            refresh_token = response.data['refresh_token']
        elif 'refresh' in response.data:
            refresh_token = response.data['refresh']
        else:
            self.skipTest("No refresh token in response")

        print(f"Got refresh token, testing normal refresh...")

        # Test normal refresh works
        refresh_url = '/api/auth/refresh/'
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(refresh_url, refresh_data, format='json')
        print(f"Normal refresh: {response.status_code}")

        # Now mark user as deleted
        self.profile.is_deleted = True
        self.profile.save()
        print("User marked as deleted...")

        # Try to refresh again
        response = self.client.post(refresh_url, refresh_data, format='json')
        print(f"Deleted user refresh: {response.status_code}")

        if response.status_code == 200:
            self.fail("Deleted user refresh token still works - SECURITY ISSUE!")
        else:
            print(f"✅ Deleted user refresh token properly blocked with status {response.status_code}")
