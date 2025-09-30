"""Django app configuration for content app."""

from django.apps import AppConfig


class ContentConfig(AppConfig):
    """Configuration for content app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'content'

    def ready(self):
        """Import signal handlers when Django starts."""
        import content.signals  # noqa
