"""
API endpoint tests for accounts app with JWT authentication.

This module tests all CRUD operations for accounts models using JWT auth.
"""

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from .base import AccountsAPITestCase
from accounts.models import (
    UserProfile, ProfessionalProfile, UserSettings, Follow, Block,
    UserSession, UserEvent
)


class UserProfileAPITests(AccountsAPITestCase):
    """Test UserProfile API endpoints with JWT authentication."""

    def test_userprofile_list_endpoint(self):
        """Test GET /api/accounts/profiles/ - List user profiles."""
        self.authenticate_user1()

        url = reverse('userprofile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should return paginated results
        if 'results' in response.data:
            profiles = response.data['results']
        else:
            profiles = response.data
        self.assertIsInstance(profiles, list)

    def test_userprofile_detail_endpoint(self):
        """Test GET /api/accounts/profiles/{id}/ - Get profile details."""
        self.authenticate_user1()

        url = reverse('userprofile-detail',
                      kwargs={'pk': self.user1_profile.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], 'Test bio for user1')

    def test_userprofile_update_endpoint(self):
        """Test PATCH /api/accounts/profiles/{id}/ - Update profile."""
        self.authenticate_user1()

        url = reverse('userprofile-detail',
                      kwargs={'pk': self.user1_profile.pk})
        update_data = {'bio': 'Updated bio via JWT'}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user1_profile.refresh_from_db()
        self.assertEqual(self.user1_profile.bio, 'Updated bio via JWT')

    def test_userprofile_permissions(self):
        """Test that users can only modify their own profiles."""
        self.authenticate_user1()

        # Try to update another user's profile
        url = reverse('userprofile-detail',
                      kwargs={'pk': self.user2_profile.pk})
        update_data = {'bio': 'Unauthorized update'}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access profiles."""
        url = reverse('userprofile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserAPITests(AccountsAPITestCase):
    """Test User API endpoints with JWT authentication."""

    def test_user_list_endpoint(self):
        """Test GET /api/accounts/users/ - List users."""
        self.authenticate_user1()

        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_detail_endpoint(self):
        """Test GET /api/accounts/users/{id}/ - Get user details."""
        self.authenticate_user1()

        url = reverse('user-detail', kwargs={'pk': self.user1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser1')

    def test_user_update_endpoint(self):
        """Test PATCH /api/accounts/users/{id}/ - Update user."""
        self.authenticate_user1()

        url = reverse('user-detail', kwargs={'pk': self.user1.pk})
        update_data = {'first_name': 'Updated'}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user1.refresh_from_db()
        self.assertEqual(self.user1.first_name, 'Updated')


class ProfessionalProfileAPITests(AccountsAPITestCase):
    """Test ProfessionalProfile API endpoints with JWT authentication."""

    def setUp(self):
        """Set up test data with professional profile."""
        super().setUp()
        self.user1_profile.role = 'professional'
        self.user1_profile.save()

        self.prof_profile = ProfessionalProfile.objects.create(
            profile=self.user1_profile,
            company_name='Test Company',
            job_title='Test Engineer'
        )

    def test_professional_profile_list_endpoint(self):
        """Test GET /api/accounts/professional-profiles/ - List profiles."""
        self.authenticate_user1()

        url = reverse('professionalprofile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_professional_profile_create_endpoint(self):
        """Test POST /api/accounts/professional-profiles/ - Create profile."""
        # Create another user without professional profile
        user3 = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='TestPass123!'
        )
        # Safely get or create the profile (a post_save signal may auto-create it)
        user3_profile, _ = UserProfile.objects.get_or_create(user=user3)
        # Ensure required fields exist to satisfy DB NOT NULL constraints
        UserProfile.objects.filter(user=user3).update(
            role='professional',
            phone_number='0000000000',
            date_of_birth='1990-01-01'
        )
        user3_profile.refresh_from_db()
        jwt_token3 = self._create_jwt_token_with_session(user3)
        self.authenticate(jwt_token3)

        url = reverse('professionalprofile-list')
        data = {
            'profile': user3_profile.pk,
            'company_name': 'New Company',
            'job_title': 'Software Developer'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_professional_profile_update_endpoint(self):
        """Test PATCH /api/accounts/professional-profiles/{id}/ - Update."""
        self.authenticate_user1()

        url = reverse('professionalprofile-detail',
                      kwargs={'pk': self.prof_profile.pk})
        update_data = {'company_name': 'Updated Company'}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FollowAPITests(AccountsAPITestCase):
    """Test Follow API endpoints with JWT authentication."""

    def test_follow_create_endpoint(self):
        """Test POST /api/accounts/follows/ - Create follow relationship."""
        self.authenticate_user1()

        url = reverse('follow-list')
        data = {'followed': self.user2_profile.pk}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify follow was created
        self.assertTrue(
            Follow.objects.filter(
                follower=self.user1_profile,
                followed=self.user2_profile
            ).exists()
        )

    def test_follow_list_endpoint(self):
        """Test GET /api/accounts/follows/ - List follows."""
        # Create a follow relationship
        Follow.objects.create(
            follower=self.user1_profile,
            followed=self.user2_profile
        )

        self.authenticate_user1()
        url = reverse('follow-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_follow_delete_endpoint(self):
        """Test DELETE /api/accounts/follows/{id}/ - Delete follow."""
        follow = Follow.objects.create(
            follower=self.user1_profile,
            followed=self.user2_profile
        )

        self.authenticate_user1()
        url = reverse('follow-detail', kwargs={'pk': follow.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_follow_permissions(self):
        """Test follow permission restrictions."""
        follow = Follow.objects.create(
            follower=self.user1_profile,
            followed=self.user2_profile
        )

        # User2 should not be able to delete user1's follow
        self.authenticate_user2()
        url = reverse('follow-detail', kwargs={'pk': follow.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BlockAPITests(AccountsAPITestCase):
    """Test Block API endpoints with JWT authentication."""

    def test_block_create_endpoint(self):
        """Test POST /api/accounts/blocks/ - Create block relationship."""
        self.authenticate_user1()

        url = reverse('block-list')
        data = {'blocked': self.user2_profile.pk, 'reason': 'spam'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify block was created
        self.assertTrue(
            Block.objects.filter(
                blocker=self.user1_profile,
                blocked=self.user2_profile
            ).exists()
        )

    def test_block_list_endpoint(self):
        """Test GET /api/accounts/blocks/ - List blocks."""
        # Create a block relationship
        Block.objects.create(
            blocker=self.user1_profile,
            blocked=self.user2_profile,
            reason='test'
        )

        self.authenticate_user1()
        url = reverse('block-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_block_delete_endpoint(self):
        """Test DELETE /api/accounts/blocks/{id}/ - Delete block."""
        block = Block.objects.create(
            blocker=self.user1_profile,
            blocked=self.user2_profile,
            reason='test'
        )

        self.authenticate_user1()
        url = reverse('block-detail', kwargs={'pk': block.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class UserSessionAPITests(AccountsAPITestCase):
    """Test UserSession API endpoints with JWT authentication."""

    def test_session_list_endpoint(self):
        """Test GET /api/accounts/sessions/ - List user sessions."""
        # Create a session
        UserSession.objects.create(
            user=self.user1_profile,
            session_id='test-session',
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )

        self.authenticate_user1()
        url = reverse('session-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_session_create_endpoint(self):
        """Test POST /api/accounts/sessions/ - Create session."""
        self.authenticate_user1()

        url = reverse('session-list')
        data = {
            'user': self.user1.pk,
            'session_id': 'new-test-session',
            'ip_address': '192.168.1.1',
            'user_agent': 'New Test Agent'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_session_permissions(self):
        """Test session permission restrictions."""
        # Create session for user1
        session = UserSession.objects.create(
            user=self.user1_profile,
            session_id='user1-session',
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )

        # User2 should not be able to access user1's sessions
        self.authenticate_user2()
        url = reverse('session-detail', kwargs={'pk': session.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserEventAPITests(AccountsAPITestCase):
    """Test UserEvent API endpoints with JWT authentication."""

    def test_event_list_endpoint(self):
        """Test GET /api/accounts/events/ - List user events."""
        # Create an event
        UserEvent.objects.create(
            user=self.user1_profile,
            event_type='login',
            description='Test login event'
        )

        self.authenticate_user1()
        url = reverse('event-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_event_create_endpoint(self):
        """Test POST /api/accounts/events/ - Create event."""
        self.authenticate_user1()

        url = reverse('event-list')
        data = {
            'user': self.user1.pk,
            'event_type': 'profile_update',
            'description': 'Updated profile via API'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_event_permissions(self):
        """Test event permission restrictions."""
        # Create event for user1
        event = UserEvent.objects.create(
            user=self.user1_profile,
            event_type='login',
            description='User1 login'
        )

        # User2 should not be able to access user1's events
        self.authenticate_user2()
        url = reverse('event-detail', kwargs={'pk': event.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserSettingsAPITests(AccountsAPITestCase):
    """Test UserSettings API endpoints with JWT authentication."""

    def setUp(self):
        """Set up test data with user settings."""
        super().setUp()
        self.settings = UserSettings.objects.create(
            user=self.user1_profile,
            language='en',
            theme='dark'
        )

    def test_settings_list_endpoint(self):
        """Test GET /api/accounts/settings/ - List user settings."""
        self.authenticate_user1()

        url = reverse('settings-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_settings_update_endpoint(self):
        """Test PATCH /api/accounts/settings/{id}/ - Update settings."""
        self.authenticate_user1()

        url = reverse('settings-detail', kwargs={'pk': self.settings.pk})
        update_data = {'theme': 'light'}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.settings.refresh_from_db()
        self.assertEqual(self.settings.theme, 'light')

    def test_settings_permissions(self):
        """Test settings permission restrictions."""
        # User2 should not be able to access user1's settings
        self.authenticate_user2()
        url = reverse('settings-detail', kwargs={'pk': self.settings.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AccountsSecurityAPITests(AccountsAPITestCase):
    """Test security aspects of accounts API with JWT authentication."""

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access endpoints."""
        endpoints = [
            '/api/accounts/profiles/',
            '/api/accounts/users/',
            '/api/accounts/follows/',
            '/api/accounts/blocks/',
            '/api/accounts/sessions/',
            '/api/accounts/events/',
            '/api/accounts/settings/'
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cross_user_data_isolation(self):
        """Test that users cannot access other users' private data."""
        # Create private data for user1
        UserEvent.objects.create(
            user=self.user1_profile,
            event_type='sensitive_action',
            description='Private event'
        )

        # User2 should not see user1's events
        self.authenticate_user2()
        url = reverse('event-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify no events from user1 are visible
        if 'results' in response.data:
            events = response.data['results']
        else:
            events = response.data

        user1_events = [e for e in events if e.get('user') == self.user1.pk]
        self.assertEqual(len(user1_events), 0)

    def test_malicious_data_injection(self):
        """Test protection against malicious data injection."""
        self.authenticate_user1()

        # Try to inject malicious data in profile update
        url = reverse('userprofile-detail', kwargs={'pk': self.user1_profile.pk})
        malicious_data = {
            'bio': '<script>alert("xss")</script>',
            'role': 'admin'  # Try to escalate privileges
        }
        response = self.client.patch(url, malicious_data, format='json')

        # Should either succeed (with data sanitized) or fail validation
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ])

        # If successful, verify role wasn't changed to admin
        if response.status_code == status.HTTP_200_OK:
            self.user1_profile.refresh_from_db()
            self.assertNotEqual(self.user1_profile.role, 'admin')
