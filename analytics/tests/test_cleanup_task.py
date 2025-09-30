"""Tests for analytics cleanup Celery tasks."""

from django.test import TestCase
from analytics.tasks import cleanup_inactive_users


class AnalyticsTaskTests(TestCase):
    def test_cleanup_task_importable(self):
        # Task should be importable and have delay attribute
        self.assertTrue(callable(cleanup_inactive_users))
        self.assertTrue(hasattr(cleanup_inactive_users, "delay"))
