"""Django app configuration for polls app."""

from django.apps import AppConfig


class PollsConfig(AppConfig):
    """Configuration for polls app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'polls'

    def ready(self):
        """Import signal handlers when Django starts."""
        import polls.signals  # noqa
