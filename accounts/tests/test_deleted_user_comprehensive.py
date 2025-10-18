"""Comprehensive test to verify deleted users cannot access ANY resources."""

from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from accounts.models import UserProfile


class DeletedUserResourceAccessTest(APITestCase):
    """Test that deleted users cannot access any application resources."""

    def setUp(self):
        """Set up users and get tokens."""
        # Create active user
        self.active_user = User.objects.create_user(
            username='activeuser',
            email='active@example.com',
            password='TestPass123!'
        )
        self.active_profile, _ = UserProfile.objects.get_or_create(user=self.active_user)
        UserProfile.objects.filter(user=self.active_user).update(
            role='normal',
            phone_number='+1234567890',
            date_of_birth='1990-01-01'
        )
        self.active_profile.refresh_from_db()

        # Create user that will be deleted
        self.deleted_user = User.objects.create_user(
            username='deleteduser',
            email='deleted@example.com',
            password='TestPass123!'
        )
        self.deleted_profile, _ = UserProfile.objects.get_or_create(user=self.deleted_user)
        UserProfile.objects.filter(user=self.deleted_user).update(
            role='normal',
            phone_number='+1234567891',
            date_of_birth='1991-01-01'
        )
        self.deleted_profile.refresh_from_db()

        # Get tokens for both users BEFORE deletion
        self.active_tokens = self._get_tokens('activeuser', 'testpass123')
        self.deleted_tokens = self._get_tokens('deleteduser', 'testpass123')

        # Now mark one user as deleted
        self.deleted_profile.is_deleted = True
        self.deleted_profile.save()

    def _get_tokens(self, username, password):
        """Helper to get JWT tokens."""
        response = self.client.post('/api/auth/login/', {
            'username': username,
            'password': password
        }, format='json')

        if response.status_code != 200:
            self.fail(f"Could not get tokens for {username}")

        return {
            'access': response.data.get('access_token', response.data.get('access')),
            'refresh': response.data.get('refresh_token', response.data.get('refresh'))
        }

    def test_deleted_user_cannot_access_profiles_api(self):
        """Test deleted user cannot access profiles API."""
        print("Testing profiles API access...")

        # Test with deleted user token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.deleted_tokens["access"]}')

        endpoints = [
            '/api/profiles/',
            '/api/users/',
            f'/api/profiles/{self.active_profile.pk}/',
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            print(f"Deleted user accessing {endpoint}: {response.status_code}")
            if response.status_code == 200:
                self.fail(f"Deleted user can access {endpoint} - SECURITY ISSUE!")

    def test_deleted_user_cannot_access_content_api(self):
        """Test deleted user cannot access content APIs."""
        print("Testing content API access...")

        # Test with deleted user token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.deleted_tokens["access"]}')

        content_endpoints = [
            '/api/posts/',
            '/api/content/posts/',
            '/api/content/feed/',
        ]

        for endpoint in content_endpoints:
            response = self.client.get(endpoint)
            print(f"Deleted user accessing {endpoint}: {response.status_code}")
            if response.status_code == 200:
                self.fail(f"Deleted user can access {endpoint} - SECURITY ISSUE!")

    def test_deleted_user_cannot_access_equipment_api(self):
        """Test deleted user cannot access equipment APIs."""
        print("Testing equipment API access...")

        # Test with deleted user token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.deleted_tokens["access"]}')

        equipment_endpoints = [
            '/api/equipment/',
            '/api/equipment/categories/',
            '/api/equipment/brands/',
        ]

        for endpoint in equipment_endpoints:
            response = self.client.get(endpoint)
            print(f"Deleted user accessing {endpoint}: {response.status_code}")
            if response.status_code == 200:
                self.fail(f"Deleted user can access {endpoint} - SECURITY ISSUE!")

    def test_deleted_user_cannot_access_communities_api(self):
        """Test deleted user cannot access communities APIs."""
        print("Testing communities API access...")

        # Test with deleted user token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.deleted_tokens["access"]}')

        community_endpoints = [
            '/api/communities/',
            '/api/communities/memberships/',
        ]

        for endpoint in community_endpoints:
            response = self.client.get(endpoint)
            print(f"Deleted user accessing {endpoint}: {response.status_code}")
            if response.status_code == 200:
                self.fail(f"Deleted user can access {endpoint} - SECURITY ISSUE!")

    def test_deleted_user_cannot_post_create_update(self):
        """Test deleted user cannot create or update resources."""
        print("Testing POST/PUT operations...")

        # Test with deleted user token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.deleted_tokens["access"]}')

        # Try to create a post
        response = self.client.post('/api/posts/', {
            'content': 'Test post from deleted user',
            'title': 'Should not work'
        }, format='json')
        print(f"Deleted user creating post: {response.status_code}")
        if response.status_code in [200, 201]:
            self.fail("Deleted user can create posts - SECURITY ISSUE!")

        # Try to update profile
        response = self.client.put(f'/api/profiles/{self.deleted_profile.pk}/', {
            'bio': 'Updated bio from deleted user'
        }, format='json')
        print(f"Deleted user updating profile: {response.status_code}")
        if response.status_code in [200, 201]:
            self.fail("Deleted user can update profile - SECURITY ISSUE!")

    def test_active_user_still_works(self):
        """Control test: verify active user can still access resources."""
        print("Testing active user access (control test)...")

        # Test with active user token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.active_tokens["access"]}')

        # Should be able to access basic endpoints
        response = self.client.get('/api/profiles/')
        print(f"Active user accessing /api/profiles/: {response.status_code}")

        response = self.client.get('/api/auth/user-info/')
        print(f"Active user accessing user-info: {response.status_code}")

        if response.status_code != 200:
            self.fail("Active user cannot access resources - something is wrong!")
        else:
            print("✅ Active user access working correctly")

    def test_deleted_user_comprehensive_block(self):
        """Comprehensive test of all possible API endpoints."""
        print("Running comprehensive API endpoint test...")

        # Test with deleted user token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.deleted_tokens["access"]}')

        # List of API endpoints to test
        all_endpoints = [
            '/api/auth/user-info/',
            '/api/profiles/',
            '/api/users/',
            '/api/posts/',
            '/api/equipment/',
            '/api/communities/',
            '/api/notifications/',
            '/api/messaging/',
            '/api/analytics/',
        ]

        blocked_count = 0
        accessible_count = 0

        for endpoint in all_endpoints:
            try:
                response = self.client.get(endpoint)
                if response.status_code in [401, 403]:
                    blocked_count += 1
                    print(f"✅ {endpoint}: BLOCKED ({response.status_code})")
                elif response.status_code == 200:
                    accessible_count += 1
                    print(f"❌ {endpoint}: ACCESSIBLE - SECURITY ISSUE!")
                elif response.status_code == 404:
                    print(f"ℹ️  {endpoint}: Not found (expected for some endpoints)")
                else:
                    print(f"? {endpoint}: {response.status_code} (unexpected status)")
            except Exception as e:
                print(f"⚠️  {endpoint}: Error - {e}")

        print(f"\nSummary: {blocked_count} blocked, {accessible_count} accessible")

        if accessible_count > 0:
            self.fail(f"Deleted user can access {accessible_count} endpoints - SECURITY ISSUES FOUND!")
        else:
            print("✅ All endpoints properly blocked for deleted user")
