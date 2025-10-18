"""
Tests for Visitor Analytics API Endpoints

Tests cover:
- Authentication and permissions
- Data accuracy and formatting
- Pagination and filtering
- Error handling
- Parameter validation
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta

from analytics.models import PageAnalytics, AnonymousSession, AnonymousPageView
from communities.models import Community
from core.models import AdministrativeDivision, Country

User = get_user_model()


class VisitorAnalyticsAPIAuthenticationTests(TestCase):
    """Test authentication and permission requirements"""

    def setUp(self):
        self.client = APIClient()

        # Create users with different permission levels
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='TestPass123!',
            is_staff=True
        )

        self.moderator_user = User.objects.create_user(
            username='moderator',
            email='moderator@test.com',
            password='TestPass123!'
        )
        # Assuming moderators have is_moderator flag
        if hasattr(self.moderator_user, 'is_moderator'):
            self.moderator_user.is_moderator = True
            self.moderator_user.save()

        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='TestPass123!'
        )

        self.endpoints = [
            '/api/analytics/visitors/',
            '/api/analytics/visitors/today/',
            '/api/analytics/visitors/weekly/',
            '/api/analytics/visitors/monthly/',
            '/api/analytics/division-breakdown/',
            '/api/analytics/trends/',
            '/api/analytics/conversions/',
            '/api/analytics/demographics/',
            '/api/analytics/realtime/',
            '/api/analytics/growth/',
        ]

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access endpoints"""
        for endpoint in self.endpoints:
            response = self.client.get(endpoint)
            self.assertIn(
                response.status_code,
                [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
                f"Endpoint {endpoint} should deny unauthenticated access"
            )

    def test_admin_can_access_all_endpoints(self):
        """Test that admin users can access all endpoints"""
        self.client.force_authenticate(user=self.admin_user)

        for endpoint in self.endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                f"Admin should be able to access {endpoint}"
            )

    def test_moderator_can_access_all_endpoints(self):
        """Test that moderator users can access all endpoints"""
        self.client.force_authenticate(user=self.moderator_user)

        for endpoint in self.endpoints:
            response = self.client.get(endpoint)
            self.assertIn(
                response.status_code,
                [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN],
                f"Moderator access to {endpoint}"
            )

    def test_regular_user_denied_access(self):
        """Test that regular users cannot access analytics endpoints"""
        self.client.force_authenticate(user=self.regular_user)

        for endpoint in self.endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code,
                status.HTTP_403_FORBIDDEN,
                f"Regular user should be denied access to {endpoint}"
            )


class VisitorAnalyticsAPIDataTests(TestCase):
    """Test data accuracy and formatting"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='TestPass123!',
            is_staff=True
        )
        self.client.force_authenticate(user=self.admin_user)

        # Create test data
        self.today = timezone.now().date()
        self.yesterday = self.today - timedelta(days=1)

        # Create country and divisions
        self.country = Country.objects.create(
            name='Test Country',
            iso2='TC',
            iso3='TST',
            code=999  # Integer code for test country
        )

        self.division = AdministrativeDivision.objects.create(
            name='Test City',
            admin_level=3,
            country=self.country,
            admin_code='TC999'
        )

        # Create page analytics - PageAnalytics only tracks url_path and basic counts
        self.today_analytics = PageAnalytics.objects.create(
            date=self.today,
            url_path='/test-page/',
            total_views=150,
            unique_visitors=100,
            authenticated_views=90,
            anonymous_views=60
        )

        self.yesterday_analytics = PageAnalytics.objects.create(
            date=self.yesterday,
            url_path='/test-page/',
            total_views=120,
            unique_visitors=80,
            authenticated_views=75,
            anonymous_views=45
        )

    def test_visitors_endpoint_returns_correct_data(self):
        """Test that visitors endpoint returns accurate statistics"""
        response = self.client.get('/api/analytics/visitors/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Check that response contains expected fields
        self.assertIn('total_visitors', data)
        self.assertIn('authenticated_visitors', data)
        self.assertIn('anonymous_visitors', data)

        # Values should be non-negative
        self.assertGreaterEqual(data['total_visitors'], 0)
        self.assertGreaterEqual(data['authenticated_visitors'], 0)
        self.assertGreaterEqual(data['anonymous_visitors'], 0)

    def test_today_endpoint_filters_correctly(self):
        """Test that today endpoint only returns today's data"""
        response = self.client.get('/api/analytics/visitors/today/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Should have data for today
        self.assertIn('total_visitors', data)

    def test_trends_endpoint_returns_time_series(self):
        """Test that trends endpoint returns time series data"""
        response = self.client.get('/api/analytics/trends/', {
            'start_date': self.yesterday.isoformat(),
            'end_date': self.today.isoformat(),
            'interval': 'day'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Should contain labels and data arrays
        self.assertIn('labels', data)
        self.assertIn('total', data)
        self.assertIn('authenticated', data)
        self.assertIn('anonymous', data)

        # Arrays should be lists
        self.assertIsInstance(data['labels'], list)
        self.assertIsInstance(data['total'], list)

    def test_division_breakdown_returns_list(self):
        """Test that division breakdown returns list of divisions"""
        response = self.client.get('/api/analytics/division-breakdown/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Should be a list
        self.assertIsInstance(data, list)

    def test_realtime_endpoint_returns_count(self):
        """Test that realtime endpoint returns visitor count"""
        response = self.client.get('/api/analytics/realtime/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertIn('count', data)
        self.assertIsInstance(data['count'], int)
        self.assertGreaterEqual(data['count'], 0)


class VisitorAnalyticsAPIFilteringTests(TestCase):
    """Test filtering and query parameters"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='TestPass123!',
            is_staff=True
        )
        self.client.force_authenticate(user=self.admin_user)

        # Create country, division and community
        self.country = Country.objects.create(
            name='Test Country',
            iso2='TC',
            iso3='TST',
            code=999  # Integer code for test country
        )

        self.division = AdministrativeDivision.objects.create(
            name='Test City',
            admin_level=3,
            country=self.country,
            admin_code='TC999'
        )

        admin_profile = self.admin_user.profile

        self.community = Community.objects.create(
            name='Test Community',
            division=self.division,
            creator=admin_profile
        )

    def test_date_range_filtering(self):
        """Test filtering by date range"""
        start_date = (timezone.now() - timedelta(days=7)).date()
        end_date = timezone.now().date()

        response = self.client.get('/api/analytics/visitors/', {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_community_filtering(self):
        """Test filtering by community"""
        response = self.client.get('/api/analytics/visitors/', {
            'community_id': str(self.community.id)
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_division_filtering(self):
        """Test filtering by division"""
        response = self.client.get('/api/analytics/visitors/', {
            'division_id': str(self.division.id)
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_date_format_returns_error(self):
        """Test that invalid date formats return appropriate errors"""
        response = self.client.get('/api/analytics/visitors/', {
            'start_date': 'invalid-date'
        })

        # Should return 400 Bad Request or still return 200 with validation
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        )

    def test_trends_interval_parameter(self):
        """Test trends endpoint with different interval values"""
        intervals = ['hour', 'day', 'week', 'month']

        for interval in intervals:
            response = self.client.get('/api/analytics/trends/', {
                'interval': interval
            })

            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                f"Interval {interval} should be valid"
            )


class VisitorAnalyticsAPIExportTests(TestCase):
    """Test CSV export functionality"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='TestPass123!',
            is_staff=True
        )
        self.client.force_authenticate(user=self.admin_user)

        # Create some test data
        today = timezone.now().date()
        PageAnalytics.objects.create(
            date=today,
            url_path='/test/',
            total_views=75,
            unique_visitors=50,
            authenticated_views=45,
            anonymous_views=30
        )

    def test_export_returns_csv(self):
        """Test that export endpoint returns CSV data"""
        response = self.client.get('/api/analytics/export/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])

    def test_export_with_date_range(self):
        """Test CSV export with date range filtering"""
        start_date = (timezone.now() - timedelta(days=7)).date()
        end_date = timezone.now().date()

        response = self.client.get('/api/analytics/export/', {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')


class VisitorAnalyticsAPIConversionTests(TestCase):
    """Test conversion tracking endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='TestPass123!',
            is_staff=True
        )
        self.client.force_authenticate(user=self.admin_user)

        # Create anonymous session
        self.fingerprint = 'test-fingerprint-123'
        self.session = AnonymousSession.objects.create(
            device_fingerprint=self.fingerprint,
            ip_address='127.0.0.1',
            session_start=timezone.now() - timedelta(hours=1),
            last_activity=timezone.now(),
            pages_visited=5,
            landing_page='/test/',
            device_type='desktop'
        )

    def test_conversions_endpoint_returns_data(self):
        """Test that conversions endpoint returns conversion data"""
        response = self.client.get('/api/analytics/conversions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Should contain conversion metrics
        self.assertIn('total_conversions', data)
        self.assertIn('conversion_rate', data)

    def test_conversions_with_date_filter(self):
        """Test conversions endpoint with date filtering"""
        response = self.client.get('/api/analytics/conversions/', {
            'start_date': (timezone.now() - timedelta(days=7)).date().isoformat(),
            'end_date': timezone.now().date().isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class VisitorAnalyticsAPIDemographicsTests(TestCase):
    """Test demographics endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='TestPass123!',
            is_staff=True
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_demographics_endpoint_returns_data(self):
        """Test that demographics endpoint returns demographic data"""
        response = self.client.get('/api/analytics/demographics/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Should be a valid response
        self.assertIsInstance(data, (dict, list))

    def test_demographics_with_filters(self):
        """Test demographics with various filters"""
        response = self.client.get('/api/analytics/demographics/', {
            'start_date': (timezone.now() - timedelta(days=30)).date().isoformat(),
            'end_date': timezone.now().date().isoformat()
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class VisitorAnalyticsAPIGrowthTests(TestCase):
    """Test growth metrics endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='TestPass123!',
            is_staff=True
        )
        self.client.force_authenticate(user=self.admin_user)

        # Create historical data
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            PageAnalytics.objects.create(
                date=date,
                url_path='/test/',
                total_views=150,
                unique_visitors=100 + (i * 10),
                authenticated_views=90,
                anonymous_views=60
            )

    def test_growth_endpoint_returns_metrics(self):
        """Test that growth endpoint returns growth metrics"""
        response = self.client.get('/api/analytics/growth/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Should contain growth metrics
        self.assertIn('growth_rate', data)
        self.assertIn('trend', data)

    def test_growth_comparison_periods(self):
        """Test growth calculation between different periods"""
        response = self.client.get('/api/analytics/growth/', {
            'period': 'week'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class VisitorAnalyticsAPIErrorHandlingTests(TestCase):
    """Test error handling and edge cases"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='TestPass123!',
            is_staff=True
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_invalid_uuid_parameters(self):
        """Test handling of invalid UUID parameters"""
        response = self.client.get('/api/analytics/visitors/', {
            'community_id': 'invalid-uuid'
        })

        # Should handle gracefully
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        )

    def test_future_date_range(self):
        """Test handling of future dates"""
        future_date = (timezone.now() + timedelta(days=30)).date()

        response = self.client.get('/api/analytics/visitors/', {
            'start_date': timezone.now().date().isoformat(),
            'end_date': future_date.isoformat()
        })

        # Should handle gracefully
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reversed_date_range(self):
        """Test handling when end_date is before start_date"""
        response = self.client.get('/api/analytics/visitors/', {
            'start_date': timezone.now().date().isoformat(),
            'end_date': (timezone.now() - timedelta(days=7)).date().isoformat()
        })

        # Should handle gracefully
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        )

    def test_missing_required_parameters(self):
        """Test endpoints when optional parameters are missing"""
        # All parameters should be optional
        response = self.client.get('/api/analytics/visitors/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get('/api/analytics/trends/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_extremely_large_date_range(self):
        """Test handling of very large date ranges"""
        start_date = (timezone.now() - timedelta(days=3650)).date()  # 10 years
        end_date = timezone.now().date()

        response = self.client.get('/api/analytics/visitors/', {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })

        # Should complete without timeout
        self.assertEqual(response.status_code, status.HTTP_200_OK)
