"""

This file provides optimized settings for running tests.
"""

from .settings import *

# Ensure DRF settings are available as top-level variables for test runs
FORMAT_SUFFIX_KWARG = 'format'
EXCEPTION_HANDLER = 'rest_framework.views.exception_handler'

# Use MySQL database for tests
if os.environ.get('MYSQL_TEST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'citinfos_backend',
            'USER': 'root',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': '3306',
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
else:
    # Use SQLite for testing
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'test_citinfos_backend',  # Django will create this
        }
    }

# Add testserver to ALLOWED_HOSTS
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Keep migrations enabled for MySQL tests
# MIGRATION_MODULES = DisableMigrations()

# Disable debug for tests
DEBUG = False

# Disable logging for tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Use simple password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable Celery for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Media files for tests
MEDIA_ROOT = '/tmp/citinfos_backend_test_media'
