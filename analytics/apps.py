"""Django app configuration for analytics app."""

from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    """Configuration for analytics app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'

    def ready(self):
        """Import signal handlers when app is ready."""
        try:
            import analytics.signals  # noqa
        except ImportError:
            pass
