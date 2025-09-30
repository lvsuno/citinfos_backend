"""Django app configuration for messaging app."""

from django.apps import AppConfig


class MessagingConfig(AppConfig):
    """Configuration for messaging app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messaging'

    def ready(self):
        """Import signal handlers when Django starts."""
        import messaging.signals  # noqa
