from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'User Accounts'

    def ready(self):  # noqa: D401
        # Import signals to register handlers
        from . import signals  # noqa: F401

        # Setup badge evaluation signals
        try:
            from .badge_signals import setup_badge_signals
            setup_badge_signals()
        except ImportError:
            pass  # Badge signals not available
        # Import tasks so Celery workers register shared_task functions.
        try:
            # Import location tasks to register process_user_location_async
            from . import location_tasks  # noqa: F401
        except ImportError:
            # If module not available, don't block app startup.
            import logging

            logger = logging.getLogger(__name__)
            logger.exception('Failed to import accounts.location_tasks')
