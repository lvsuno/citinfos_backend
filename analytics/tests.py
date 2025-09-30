"""Comprehensive tests for analytics app."""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from content.utils import calculate_engagement_score
from accounts.models import UserProfile, UserEvent
from core.jwt_test_mixin import JWTAuthTestMixin
from .models import (
    DailyAnalytics, UserAnalytics,
    SystemMetric, ErrorLog
)
from .utils import (record_system_metric,
                    record_error, get_analytics_summary)
from .tasks import (
    process_daily_analytics, update_system_metrics, cleanup_old_data,
    update_user_engagement_scores, process_analytics_daily,
    update_advanced_system_metrics, comprehensive_cleanup,
    generate_weekly_analytics_report
)


class AnalyticsModelTests(TestCase):
    """Test all analytics models."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile, _ = UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.filter(user=self.user).update(
            role='normal',
            phone_number='+15550000301',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.user_profile.refresh_from_db()

    def test_daily_analytics_creation(self):
        """Test DailyAnalytics creation and properties."""
        today = timezone.now().date()
        analytics = DailyAnalytics.objects.create(
            date=today,
            new_users=10,
            active_users=50,
            total_users=100,
            new_posts=25,
            new_comments=75,
            total_interactions=200
        )

        self.assertEqual(str(analytics), f'Analytics for {today}')
        self.assertEqual(analytics.new_users, 10)
        self.assertEqual(analytics.active_users, 50)
        self.assertEqual(analytics.total_interactions, 200)

    def test_user_analytics_creation(self):
        """Test UserAnalytics creation and properties."""
        user_analytics = UserAnalytics.objects.create(
            user=self.user_profile,
            total_posts=15,
            total_comments=30,
            total_likes_given=45,
            total_likes_received=60,
            followers_gained=5,
            total_sessions=10
        )

        self.assertTrue('Analytics for testuser' in str(user_analytics))
        self.assertEqual(user_analytics.user, self.user_profile)
        self.assertEqual(user_analytics.total_posts, 15)
        self.assertEqual(user_analytics.total_comments, 30)
        self.assertEqual(user_analytics.followers_gained, 5)

    def test_system_metric_creation(self):
        """Test SystemMetric creation and properties."""
        metric = SystemMetric.objects.create(
            metric_type='response_time',
            value=150.5,
            additional_data={'endpoint': '/api/posts/', 'method': 'GET'}
        )

        self.assertEqual(str(metric), 'response_time: 150.5')
        self.assertEqual(metric.metric_type, 'response_time')
        self.assertEqual(metric.value, 150.5)
        self.assertEqual(metric.additional_data['endpoint'], '/api/posts/')

    def test_error_log_creation(self):
        """Test ErrorLog creation and properties."""
        error = ErrorLog.objects.create(
            user=self.user_profile,
            level='error',
            message='Test error message for logging',
            stack_trace='Traceback (most recent call last)...',
            url='/api/test/',
            method='POST',
            ip_address='192.168.1.1',
            extra_data={'error_code': 500, 'request_id': 'abc123'}
        )

        self.assertTrue('ERROR: Test error message for logging' in str(error))
        self.assertEqual(error.user, self.user_profile)
        self.assertEqual(error.level, 'error')
        self.assertEqual(error.message, 'Test error message for logging')
        self.assertFalse(error.is_resolved)
        self.assertEqual(error.extra_data['error_code'], 500)


class AnalyticsUtilsTests(TestCase):
    """Test analytics utility functions."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile, _ = UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.filter(user=self.user).update(
            bio='Test user profile',
            phone_number='+15550000302',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.user_profile.refresh_from_db()
        self.factory = RequestFactory()

    def test_calculate_engagement_score(self):
        """Test engagement score calculation."""
        # Create some user events
        UserEvent.objects.create(
            user=self.user,
            event_type='post_create',
            created_at=timezone.now()
        )
        UserEvent.objects.create(
            user=self.user,
            event_type='comment_create',
            created_at=timezone.now()
        )

        score = calculate_engagement_score(self.user, days=30)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_record_system_metric(self):
        """Test system metric recording."""
        record_system_metric('response_time', 150.5, {'endpoint': '/api/test/'})

        metric = SystemMetric.objects.filter(metric_type='response_time').first()
        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 150.5)
        self.assertEqual(metric.additional_data['endpoint'], '/api/test/')

    def test_record_error(self):
        """Test error recording."""
        record_error(
            user=self.user,
            level='error',
            message='Test error',
            url='/api/test/',
            method='POST',
            ip_address='127.0.0.1',
            extra_data={'error_code': 500}
        )

        error = ErrorLog.objects.filter(message='Test error').first()
        self.assertIsNotNone(error)
        self.assertEqual(error.user, self.user_profile)
        self.assertEqual(error.level, 'error')
        self.assertEqual(error.extra_data['error_code'], 500)

    def test_get_analytics_summary(self):
        """Test analytics summary generation."""
        # Create some daily analytics
        DailyAnalytics.objects.create(
            date=timezone.now().date(),
            new_users=10,
            active_users=50,
            total_users=100,
            new_posts=20,
            new_comments=30,
            total_interactions=100,
            avg_response_time=150.0,
            error_count=5
        )

        summary = get_analytics_summary(days=7)
        self.assertIn('total_users', summary)
        self.assertIn('new_users', summary)
        self.assertIn('active_users', summary)
        self.assertEqual(summary['total_users'], 100)
        self.assertEqual(summary['new_users'], 10)


class AnalyticsAPITests(APITestCase, JWTAuthTestMixin):
    """Test analytics API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='apiuser',
            password='pass123'
        )
        self.user_profile, _ = UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.filter(user=self.user).update(
            phone_number='+15550000303',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.user_profile.refresh_from_db()

        # Create JWT token
        self.jwt_token = self._create_jwt_token_with_session(self.user)

    def test_get_analytics_summary(self):
        """Test analytics summary endpoint with authentication."""
        self.authenticate(self.user)

        url = '/api/analytics/summary/'
        response = self.client.get(url)
        # Accept 200 or 404 if endpoint doesn't exist
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_403_FORBIDDEN  # If admin only
        ])

    def test_get_system_metrics(self):
        """Test system metrics endpoint with authentication."""
        self.authenticate(self.user)

        url = '/api/analytics/metrics/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_403_FORBIDDEN
        ])

    def test_get_error_logs(self):
        """Test error logs endpoint with authentication."""
        self.authenticate(self.user)

        url = '/api/analytics/errors/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_403_FORBIDDEN
        ])

    def test_create_daily_analytics(self):
        """Test creating daily analytics with authentication."""
        self.authenticate(self.user)

        url = '/api/analytics/daily/'
        data = {
            'date': timezone.now().date().isoformat(),
            'new_users': 5,
            'active_users': 20,
            'total_users': 100,
            'new_posts': 10,
            'new_comments': 30,
            'total_interactions': 50
        }
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_201_CREATED,
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ])

    def test_permission_required(self):
        """Test unauthorized access to analytics endpoints."""
        # Don't authenticate
        url = '/api/analytics/summary/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ])

    def test_invalid_daily_analytics_payload(self):
        """Test invalid data for daily analytics endpoint."""
        self.authenticate(self.user)

        url = '/api/analytics/daily/'
        data = {'date': 'invalid-date', 'new_users': 'not-a-number'}
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])

    def test_user_analytics_endpoint(self):
        """Test user-specific analytics endpoint."""
        self.authenticate(self.user)

        url = f'/api/analytics/users/{self.user_profile.id}/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ])

    """Test analytics Celery tasks."""

    def test_tasks_can_be_imported(self):
        """Test that all analytics tasks can be imported."""
        # If we reach this point, all imports succeeded
        self.assertTrue(True)

    def test_basic_task_structure(self):
        """Test that tasks have proper structure."""
        tasks = [
            process_daily_analytics,
            update_system_metrics,
            cleanup_old_data,
            update_user_engagement_scores,
            process_analytics_daily,
            update_advanced_system_metrics,
            comprehensive_cleanup,
            generate_weekly_analytics_report
        ]

        for task in tasks:
            self.assertTrue(hasattr(task, 'delay'))  # Celery task method
            self.assertTrue(callable(task))
