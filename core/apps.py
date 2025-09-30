from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'

    def ready(self):
        """Import signal handlers when the app is ready."""
        import core.signals  # noqa

        # Initialize the enhanced cascading restoration system
        try:
            from core.cascade_restore import add_cascade_restore_methods
            add_cascade_restore_methods()
            print("Enhanced cascading restoration system loaded successfully!")
        except ImportError as e:
            print(f"Warning: Could not load cascading restoration system: {e}")
