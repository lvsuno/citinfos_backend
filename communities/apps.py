"""Django app configuration for communities app."""

from django.apps import AppConfig


class CommunitiesConfig(AppConfig):
    """Configuration for communities app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'communities'

    def ready(self):
        """Import signals when app is ready."""
        import communities.signals  # noqa: F401
