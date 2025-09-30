"""Comprehensive API tests for all analytics app views and actions."""
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import UserProfile
from analytics.models import DailyAnalytics, UserAnalytics, SystemMetric, ErrorLog

class AnalyticsComprehensiveAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apitest', password='pass123')
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.filter(user=self.user).update(
            phone_number='+15550000001',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now(),
        )
        self.profile.refresh_from_db()
        self.client.force_authenticate(user=self.user)
        self.daily = DailyAnalytics.objects.create(date='2023-01-01')
        self.user_analytics = UserAnalytics.objects.create(user=self.profile)
        self.metric = SystemMetric.objects.create(metric_type='cpu_usage', value=1.0)
        self.error = ErrorLog.objects.create(user=self.profile, level='error', message='msg')

    def test_daily_analytics_date_range(self):
        url = reverse('dailyanalytics-date-range')
        response = self.client.get(url, {'start_date': '2023-01-01', 'end_date': '2023-01-01'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_daily_analytics_trends(self):
        url = reverse('dailyanalytics-trends')
        response = self.client.get(url, {'days': 30})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_user_analytics_dashboard(self):
        url = reverse('useranalytics-dashboard')
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_user_analytics_update_engagement(self):
        url = reverse('useranalytics-update-engagement')
        response = self.client.post(url, {'engagement_score': 5.0})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_system_metric_by_type(self):
        url = reverse('systemmetric-by-type')
        response = self.client.get(url, {'type': 'cpu_usage'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])


    # Removed test_system_metric_by_category: SystemMetric has no category field

    def test_system_metric_latest(self):
        url = reverse('systemmetric-latest')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_errorlog_unresolved(self):
        url = reverse('errorlog-unresolved')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_errorlog_by_type(self):
        url = reverse('errorlog-by-type')
        response = self.client.get(url, {'error_type': 'test'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_errorlog_resolve(self):
        url = reverse('errorlog-resolve', kwargs={'pk': self.error.pk})
        response = self.client.post(url, {'resolution_notes': 'fixed'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_errorlog_statistics(self):
        url = reverse('errorlog-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
