# Accounts app - User management and identity

# Import async tasks for Celery autodiscovery (only if celery is available)
try:
    from . import async_tasks
except ImportError:
    # Celery not available, skip async tasks
    pass
