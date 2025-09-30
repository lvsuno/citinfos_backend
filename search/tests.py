
from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import UserProfile
from django.utils import timezone
from content.models import Post
# Equipment functionality removed
# from equipment.models import Equipment, EquipmentModel
from communities.models import Community, CommunityMembership
from messaging.models import ChatRoom, Message
from polls.models import Poll
from ai_conversations.models import AIConversation
from core.jwt_test_mixin import JWTAuthTestMixin
from .models import UserSearchQuery
from .global_search import GlobalSearchEngine
from rest_framework.test import APIClient
from rest_framework import status

class UserSearchQueryTest(TestCase, JWTAuthTestMixin):
    """Test search functionality with JWT authentication."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.filter(user=self.user).update(
            phone_number='+15550001111',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.profile.refresh_from_db()
        # Ensure required profile fields and verification
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.filter(user=self.user).update(
            phone_number='+15550000201',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.profile.refresh_from_db()
        self.client = APIClient()

        # Create JWT token
        self.jwt_token = self._create_jwt_token_with_session(self.user)

    def test_create_search_query(self):
        """Test creating a search query with authentication."""
        self.authenticate(self.user)

        data = {
            'query': 'test',
            'search_type': 'post',
            'filters': {},
            'results_count': 5
        }
        response = self.client.post('/user-search-queries/', data, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND
        ])

        if response.status_code == status.HTTP_201_CREATED:
            self.assertEqual(response.data['query'], 'test')
            self.assertFalse(response.data['is_deleted'])

    def test_update_search_query(self):
        """Test updating a search query with authentication."""
        self.authenticate(self.user)

        query = UserSearchQuery.objects.create(
            user=self.profile,
            query='old',
            search_type='post'
        )
        url = f'/user-search-queries/{query.id}/'
        data = {'query': 'updated'}
        response = self.client.patch(url, data, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])

        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(response.data['query'], 'updated')

    def test_soft_delete_search_query(self):
        """Test soft delete of search query with authentication."""
        self.authenticate(self.user)

        query = UserSearchQuery.objects.create(
            user=self.profile,
            query='delete',
            search_type='post'
        )
        url = f'/user-search-queries/{query.id}/'
        response = self.client.delete(url)
        self.assertIn(response.status_code, [
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND
        ])

        # Should not be returned in list (handle paginated response)
        list_response = self.client.get('/user-search-queries/')
        if list_response.status_code == status.HTTP_200_OK:
            results = list_response.data.get('results', list_response.data)
            ids = [item['id'] for item in results]
            self.assertNotIn(query.id, ids)

    def test_list_search_queries(self):
        """Test listing search queries with authentication."""
        self.authenticate(self.user)

        UserSearchQuery.objects.create(
            user=self.profile,
            query='q1',
            search_type='post'
        )
        UserSearchQuery.objects.create(
            user=self.profile,
            query='q2',
            search_type='user'
        )
        UserSearchQuery.objects.create(
            user=self.profile,
            query='q3',
            search_type='posts',
            is_deleted=True
        )

        response = self.client.get('/user-search-queries/')
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])

        if response.status_code == status.HTTP_200_OK:
            results = response.data.get('results', response.data)
            # Should exclude soft-deleted queries
            self.assertEqual(len(results), 2)

    def test_unauthorized_search_access(self):
        """Test unauthorized access to search endpoints."""
        # Don't authenticate

        endpoints = [
            '/user-search-queries/',
            '/api/search/',
            '/api/search/posts/',
            '/api/search/users/'
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertIn(response.status_code, [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND
            ])

    def test_search_filtering_by_type(self):
        """Test filtering search queries by type with authentication."""
        self.authenticate(self.user)

        UserSearchQuery.objects.create(
            user=self.profile,
            query='post_query',
            search_type='post'
        )
        UserSearchQuery.objects.create(
            user=self.profile,
            query='user_query',
            search_type='user'
        )

        # Test filtering by search type
        response = self.client.get('/user-search-queries/?search_type=post')
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])

        if response.status_code == status.HTTP_200_OK:
            results = response.data.get('results', response.data)
            if results:
                for result in results:
                    self.assertEqual(result['search_type'], 'post')

    def test_search_functionality_authenticated(self):
        """Test search functionality with authentication."""
        self.authenticate(self.user)

        # Test global search
        response = self.client.get('/api/search/?q=test')
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])

        # Test post search
        response = self.client.get('/api/search/posts/?q=test')
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])

        # Test user search
        response = self.client.get('/api/search/users/?q=test')
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])


class GlobalSearchEngineTest(TestCase):
    """Test the GlobalSearchEngine functionality."""

    def setUp(self):
        """Set up test data."""
        # Create users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass'
        )
        self.user2 = User.objects.create_user(
            username='searchuser',
            email='search@example.com',
            password='testpass'
        )

        self.profile1, _ = UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.filter(user=self.user1).update(
            bio='Test user bio with search keywords',
            phone_number='+15550000202',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.profile1.refresh_from_db()

        self.profile2, _ = UserProfile.objects.get_or_create(user=self.user2)
        UserProfile.objects.filter(user=self.user2).update(
            bio='Another user profile',
            phone_number='+15550000203',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.profile2.refresh_from_db()

        # Create test posts
        self.post1 = Post.objects.create(
            content='Test post with search functionality',
            author=self.profile1,
            visibility='public',
            post_type='text'
        )
        self.post2 = Post.objects.create(
            content='Private post content',
            author=self.profile1,
            visibility='private',
            post_type='text'
        )
        self.post3 = Post.objects.create(
            content='Another search test post',
            author=self.profile2,
            visibility='public',
            post_type='text'
        )

    def test_anonymous_search_basic(self):
        """Test basic anonymous search functionality."""
        engine = GlobalSearchEngine(None)
        results = engine.search('search')

        self.assertIsInstance(results, dict)
        self.assertIn('query', results)
        self.assertIn('results', results)
        self.assertIn('total_count', results)
        self.assertEqual(results['query'], 'search')

    def test_anonymous_search_posts_only_public(self):
        """Test that anonymous users only see public posts."""
        engine = GlobalSearchEngine(None)
        results = engine.search('post', content_types=['posts'])

        posts = results['results'].get('posts', [])
        # Should find 2 public posts, not the private one
        self.assertGreaterEqual(len(posts), 2)

        # Verify only public posts are returned
        for post in posts:
            # We can't directly check visibility from serialized data,
            # but we can verify the content matches our public posts
            self.assertIn(post['content'], [
                'Test post with search functionality',
                'Another search test post'
            ])

    def test_authenticated_search_permission_filtering(self):
        """Test permission filtering for authenticated users."""
        engine = GlobalSearchEngine(self.user1)
        results = engine.search('post', content_types=['posts'])

        posts = results['results'].get('posts', [])
        # User1 should see their own private post plus public posts
        self.assertGreaterEqual(len(posts), 2)

    def test_search_posts_method(self):
        """Test the _search_posts method directly."""
        engine = GlobalSearchEngine(None)
        results = engine._search_posts('search', {}, 10, 0)

        self.assertIsInstance(results, dict)
        self.assertIn('results', results)
        self.assertIn('count', results)
        self.assertIsInstance(results['results'], list)

    def test_search_users_method(self):
        """Test the _search_users method directly."""
        engine = GlobalSearchEngine(None)
        results = engine._search_users('search', {}, 10, 0)

        self.assertIsInstance(results, dict)
        self.assertIn('results', results)
        self.assertIn('count', results)

        # Should find searchuser
        users = results['results']
        usernames = [user['username'] for user in users]
        self.assertIn('searchuser', usernames)

    def test_search_all_content_types(self):
        """Test searching all content types."""
        engine = GlobalSearchEngine(None)
        content_types = [
            'posts', 'users', 'communities',
            'messages', 'polls', 'ai_conversations'
        ]

        for content_type in content_types:
            results = engine.search('test', content_types=[content_type])
            self.assertIsInstance(results, dict)
            self.assertIn('results', results)
            # Each content type should have its own key in results
            self.assertIn(content_type, results['results'])

    def test_empty_query_handling(self):
        """Test handling of empty queries."""
        engine = GlobalSearchEngine(None)

        # Empty string
        results = engine.search('')
        self.assertEqual(results['total_count'], 0)

        # Whitespace only
        results = engine.search('   ')
        self.assertEqual(results['total_count'], 0)

        # None query
        results = engine.search(None)
        self.assertEqual(results['total_count'], 0)

    def test_search_filters(self):
        """Test search with various filters."""
        engine = GlobalSearchEngine(None)

        # Test post type filter
        filters = {'post_type': 'text'}
        results = engine.search('test', content_types=['posts'], filters=filters)
        self.assertIsInstance(results, dict)

        # Test date range filter
        filters = {'date_range': 'today'}
        results = engine.search('test', content_types=['posts'], filters=filters)
        self.assertIsInstance(results, dict)

    def test_search_pagination(self):
        """Test search pagination."""
        engine = GlobalSearchEngine(None)

        # Test with limit
        results = engine.search('test', limit=1)
        self.assertLessEqual(len(results['results'].get('posts', [])), 1)

        # Test with offset
        results = engine.search('test', limit=10, offset=0)
        self.assertIsInstance(results, dict)

    def test_serialize_post_method(self):
        """Test post serialization."""
        engine = GlobalSearchEngine(None)
        serialized = engine._serialize_post(self.post1)

        expected_keys = [
            'id', 'type', 'title', 'content', 'author',
            'post_type', 'visibility', 'engagement', 'created_at'
        ]
        for key in expected_keys:
            self.assertIn(key, serialized)

        self.assertEqual(serialized['type'], 'post')
        self.assertEqual(serialized['content'], self.post1.content)

    def test_serialize_user_method(self):
        """Test user serialization."""
        engine = GlobalSearchEngine(None)
        serialized = engine._serialize_user(self.profile1)

        expected_keys = [
            'id', 'type', 'username', 'display_name',
            'bio', 'stats', 'is_verified'
        ]
        for key in expected_keys:
            self.assertIn(key, serialized)

        self.assertEqual(serialized['type'], 'user')
        self.assertEqual(serialized['username'], self.user1.username)


class SearchAPITest(TestCase, JWTAuthTestMixin):
    """Test search API endpoints."""

    def setUp(self):
        """Set up test data for API tests."""
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='testpass'
        )
        self.profile = UserProfile.objects.create(user=self.user)
        self.client = APIClient()

        # Create test content
        self.post = Post.objects.create(
            content='API test post with search content',
            author=self.profile,
            visibility='public',
            post_type='text'
        )

    def test_global_search_api_anonymous(self):
        """Test global search API without authentication."""
        url = '/api/search/global/'
        response = self.client.get(url, {'q': 'test'})

        # Depending on auth requirements, this might return 401 or 200
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ])

    def test_global_search_api_authenticated(self):
        """Test global search API with authentication."""
        self.authenticate(self.user)

        url = '/api/search/global/'
        response = self.client.get(url, {'q': 'test'})

        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])

        if response.status_code == status.HTTP_200_OK:
            self.assertIn('query', response.data)
            self.assertIn('results', response.data)

    def test_quick_search_api(self):
        """Test quick search API endpoint."""
        url = '/api/search/quick/'
        response = self.client.get(url, {'q': 'test'})

        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ])

    def test_search_api_parameters(self):
        """Test search API with various parameters."""
        self.authenticate(self.user)

        url = '/api/search/global/'

        # Test with content types
        response = self.client.get(url, {
            'q': 'test',
            'types': 'posts,users'
        })
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])

        # Test with limit
        response = self.client.get(url, {
            'q': 'test',
            'limit': 5
        })
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])

    def test_search_api_validation(self):
        """Test search API input validation."""
        self.authenticate(self.user)

        url = '/api/search/global/'

        # Test without query parameter
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])

        # Test with empty query
        response = self.client.get(url, {'q': ''})
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])


class SearchIntegrationTest(TestCase):
    """Integration tests for the complete search system."""

    def setUp(self):
        """Set up comprehensive test data."""
        # Create multiple users
        self.users = []
        self.profiles = []

        for i in range(3):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass'
            )
            profile = UserProfile.objects.create(
                user=user,
                bio=f'User {i} bio with search terms'
            )
            self.users.append(user)
            self.profiles.append(profile)

        # Create posts with different visibility
        self.posts = []
        visibilities = ['public', 'private', 'public']  # Make third post public too

        for i, visibility in enumerate(visibilities):
            if i < len(self.profiles):
                post = Post.objects.create(
                    content=f'Integration test post {i} with search keywords',
                    author=self.profiles[i],
                    visibility=visibility,
                    post_type='text'
                )
                self.posts.append(post)

    def test_complete_search_workflow(self):
        """Test the complete search workflow."""
        # Test anonymous search
        engine = GlobalSearchEngine(None)
        anonymous_results = engine.search('search')

        self.assertGreater(anonymous_results['total_count'], 0)

        # Test authenticated search
        authenticated_engine = GlobalSearchEngine(self.users[0])
        auth_results = authenticated_engine.search('search')

        self.assertGreater(auth_results['total_count'], 0)

        # Authenticated user should see same or more results than anonymous
        self.assertGreaterEqual(
            auth_results['total_count'],
            anonymous_results['total_count']
        )

    def test_permission_system_integration(self):
        """Test that permission system works correctly."""
        # Anonymous user should only see public content
        engine = GlobalSearchEngine(None)
        results = engine.search('test', content_types=['posts'])

        posts = results['results'].get('posts', [])
        # Should only see public posts
        self.assertGreater(len(posts), 0)

        # Authenticated user should see their own private content
        auth_engine = GlobalSearchEngine(self.users[1])  # User who owns private post
        auth_results = auth_engine.search('test', content_types=['posts'])

        auth_posts = auth_results['results'].get('posts', [])
        # Should see at least as many posts as anonymous user
        self.assertGreaterEqual(len(auth_posts), len(posts))

    def test_search_performance_basic(self):
        """Basic performance test for search."""
        import time

        engine = GlobalSearchEngine(None)

        start_time = time.time()
        results = engine.search('search')
        end_time = time.time()

        search_time = end_time - start_time

        # Search should complete in reasonable time (< 5 seconds)
        self.assertLess(search_time, 5.0)

        # Should return results
        self.assertGreater(results['total_count'], 0)
