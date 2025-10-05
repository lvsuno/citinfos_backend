"""Django settings for citinfos_backend project."""
import os
import sys
from pathlib import Path
from datetime import timedelta
import environ

# PostgreSQL with PostGIS support

# Celery Beat Schedule
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    DATABASE_URL=(str, ''),
    REDIS_URL=(str, 'redis://localhost:6379/0'),
    REDIS_HOST=(str, 'localhost'),
    REDIS_PORT=(int, 6379),
    REDIS_DB=(int, 0),
    SECRET_KEY=(str, ''),
    USE_REDIS_SESSIONS=(bool, True),
    SESSION_DURATION_HOURS=(int, 4),  # Default session duration in hours
    # AI Configuration
    OPENAI_API_KEY=(str, ''),
    OPENAI_ORG_ID=(str, ''),
    ANTHROPIC_API_KEY=(str, ''),
    GOOGLE_AI_API_KEY=(str, ''),
    AI_DEFAULT_MODEL=(str, 'gpt-3.5-turbo'),
    AI_MAX_TOKENS=(int, 4096),
    AI_TEMPERATURE=(float, 0.7),
    AI_ENABLE_STREAMING=(bool, True),
    AI_ENABLE_FUNCTION_CALLING=(bool, True),
    AI_ENABLE_VISION=(bool, False),
    AI_DAILY_COST_LIMIT=(float, 10.0),
    AI_USER_DAILY_LIMIT=(int, 100),
    AI_ENABLE_COST_TRACKING=(bool, True),
    AI_ENABLE_CONTENT_FILTER=(bool, True),
    AI_FILTER_LEVEL=(str, 'moderate'),
    # Cover media settings
    COVER_VIDEO_MAX_DURATION_SECONDS=(int, 60),
    PROFILE_COVER_IMAGE_MAX_BYTES=(int, 5242880),
    PROFILE_COVER_VIDEO_MAX_BYTES=(int, 15728640),
    # Twilio SMS Configuration
    TWILIO_ACCOUNT_SID=(str, ''),
    TWILIO_AUTH_TOKEN=(str, ''),
    TWILIO_PHONE_NUMBER=(str, ''),
    # JWT Token Lifetime Settings
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES=(int, 5),
    JWT_REFRESH_TOKEN_LIFETIME_DAYS=(int, 1),
    PERSISTENT_SESSION_DURATION_DAYS=(int, 30),
    JWT_SLIDING_TOKEN_LIFETIME_MINUTES=(int, 5),
    JWT_SLIDING_TOKEN_REFRESH_LIFETIME_DAYS=(int, 1),
    # JWT Auto-Renewal Configuration
    JWT_RENEWAL_CHECK_FREQUENCY_SECONDS=(int, 120),
    JWT_RENEWAL_THRESHOLD_SECONDS=(int, 300),
    # Session Extension Configuration
    SESSION_EXTENSION_CHECK_FREQUENCY_SECONDS=(int, 900),
    SESSION_EXTENSION_THRESHOLD_SECONDS=(int, 1800),
    EMAIL_BACKEND=(str, 'django.core.mail.backends.smtp.EmailBackend'),
    EMAIL_HOST=(str, 'your.smtp.server.com'),         # Your SMTP server
    EMAIL_PORT=(int, 587),                            # Usually 587 for TLS, 465 for SSL, or 25
    EMAIL_HOST_USER=(str, 'your_username'),           # Your SMTP username
    EMAIL_HOST_PASSWORD=(str, 'your_password'),       # Your SMTP password
    EMAIL_USE_TLS=(bool, True),                        # True for TLS, False for SSL or plain
    EMAIL_USE_SSL=(bool, False),                       # True for SSL, False for TLS or plain
    DEFAULT_FROM_EMAIL=(str, 'noreply@yourdomain.com'),
    # Domain Configuration
    DOMAIN_URL=(str, 'http://localhost:8000'),         # Base domain URL for email templates
    FRONTEND_DOMAIN=(str, 'localhost:3000'),           # Frontend domain for notification links
)

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# GeoIP2 database path
GEOIP2_DB_PATH = os.path.join(BASE_DIR, 'GeoLite2-City.mmdb')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Application definition
DJANGO_APPS = [
    'daphne',              # ASGI HTTP/WebSocket server - must be first
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',  # GeoDjango for spatial data support
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'csp',  # Content Security Policy for password protection
    'django_filters',
    'django_extensions',
    'django_celery_beat',  # Django Celery Beat for dynamic scheduling
    'channels',            # WebSocket support for real-time notifications
    # Django AllAuth for social authentication
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.twitter',
]

LOCAL_APPS = [
    'core',                # Base models and managers
    'accounts',            # User profiles and authentication
    'content',             # Posts, comments, likes, shares, hashtags
    'communities',         # Community management and memberships
    'messaging',           # Chat rooms and messaging system
    'notifications',       # User notifications
    'analytics',           # Analytics, logging, and metrics
    'ai_conversations',    # AI conversation system
    'polls',               # Polling system
    'search',              # User search tracking and recommendations
    #           # Legacy app (disabled during migration)
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'csp.middleware.CSPMiddleware',  # CSP for password protection
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # OPTIMIZED: JWT-first authentication with session fallback (HIGH PRIORITY)
    'core.middleware.optimized_auth_middleware.OptimizedAuthenticationMiddleware',
    'core.middleware.optimized_auth_middleware.SessionContextMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Django AllAuth middleware
    'allauth.account.middleware.AccountMiddleware',
    # Update user activity tracking (must be after authentication)
    'accounts.middleware.UpdateLastActiveMiddleware',
    # IP-based geolocation detection (must be after authentication) - COMMENTED OUT
    # 'communities.middleware.GeoLocationMiddleware',
    # Geo-restriction middleware for communities (after geolocation detection) - COMMENTED OUT
    # 'communities.middleware.GeoRestrictionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # X-Frame-Options middleware helps prevent clickjacking. If you must allow
    # embedding (e.g. PDF viewer) you can change `X_FRAME_OPTIONS` or set the
    # value via environment, but it's enabled by default for better security.
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom event detection and rate limiting middleware
    'middleware.EventDetectionMiddleware',
    'middleware.APIRateLimitMiddleware',
    # SessionActivityMiddleware - REMOVED (consolidated into OptimizedAuth)
    # JWTAutoRenewMiddleware - REMOVED (consolidated into OptimizedAuth)
    # Analytics tracking middleware (must be after authentication)
    'analytics.middleware.AnalyticsTrackingMiddleware',
]

ROOT_URLCONF = 'citinfos_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.domain_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'citinfos_backend.wsgi.application'

# ASGI (for Django Channels)
ASGI_APPLICATION = 'citinfos_backend.asgi.application'

# Channel Layers Configuration for WebSocket
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(env('REDIS_HOST'), env('REDIS_PORT'))],
            "capacity": 1500,  # Maximum number of messages to store
            "expiry": 60,      # Message expiry time in seconds
        },
    },
}

# PostGIS Database Configuration - Single database for all data
# Database Configuration - Using PostGIS for all data including spatial
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': env('POSTGRES_DATABASE', default='loc_database'),
        'USER': env('POSTGRES_USER', default='loc_user'),
        'PASSWORD': env('POSTGRES_PASSWORD', default='loc_password'),
        'HOST': env('POSTGRES_HOST', default='postgis'),
        'PORT': env('POSTGRES_PORT', default='5432'),
    }
}

# Tests will use the configured PostGIS database from DATABASES.

# Use default Django user model - UserProfile extends it
# AUTH_USER_MODEL = 'auth.User'  # Using default Django User model

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'accounts.validators.PasswordStrengthValidator',
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'NumericPasswordValidator'
        ),
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'FORMAT_SUFFIX_KWARG': 'format',
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    # "http://localhost:3000",
    # "http://127.0.0.1:3000",
    "http://localhost:3000",  # Create React App dev server
    "http://127.0.0.1:3000",  # Create React App dev server
    "http://localhost:8000",  # Backend Django server for PDF embedding
    "http://127.0.0.1:8000",  # Backend Django server (alternative)
    # "http://localhost:5174",
    # "http://127.0.0.1:5174",
]

CORS_ALLOW_CREDENTIALS = True

# Allow custom headers for authentication and API functionality
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-session-id',  # Custom session ID header
    'x-new-access-token',  # Token renewal header
    'x-new-refresh-token',  # Refresh token header
]

# Allow all common HTTP methods
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Allow exposing response headers to frontend
CORS_EXPOSE_HEADERS = [
    'x-new-access-token',
    'x-new-refresh-token',
    'x-session-id',
]

# CSRF settings for Docker/cross-origin requests
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",  # Frontend Create React App dev server
    "http://127.0.0.1:3000",  # Frontend Create React App dev server (alt)
    "http://localhost:8000",  # Backend Django server for PDF embedding
    "http://127.0.0.1:8000",  # Backend Django server (alternative)
]

# Cache configuration with Redis
USE_REDIS_SESSIONS = env('USE_REDIS_SESSIONS')
SESSION_DURATION_HOURS = env('SESSION_DURATION_HOURS')
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL'),
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'KEY_PREFIX': 'session',
        'TIMEOUT': SESSION_DURATION_HOURS * 60 * 60,  # 4 hours
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_AGE = SESSION_DURATION_HOURS * 60 * 60  # 4 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Persistent session duration for "remember me" functionality (in days)
PERSISTENT_SESSION_DURATION_DAYS = env.int(
    'PERSISTENT_SESSION_DURATION_DAYS', default=30
)

# Session cookie settings for Docker/cross-origin requests
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_SAMESITE = 'Lax'  # Allow cross-origin for Docker
SESSION_COOKIE_NAME = 'sessionid'

# CSRF cookie settings for Docker/cross-origin requests
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access for SPA
CSRF_COOKIE_SECURE = False    # Set to True in production with HTTPS
CSRF_COOKIE_SAMESITE = 'Lax'  # Allow cross-origin for Docker

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=env('JWT_ACCESS_TOKEN_LIFETIME_MINUTES')
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=env('JWT_REFRESH_TOKEN_LIFETIME_DAYS')
    ),
    'ROTATE_REFRESH_TOKENS': True,  # Generate new refresh token on refresh
    'BLACKLIST_AFTER_ROTATION': True,  # Blacklist old refresh tokens
    'UPDATE_LAST_LOGIN': True,  # Update last login on token refresh

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,  # Use Django SECRET_KEY
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),  # Authorization: Bearer <token>
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(
        minutes=env('JWT_SLIDING_TOKEN_LIFETIME_MINUTES')
    ),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(
        days=env('JWT_SLIDING_TOKEN_REFRESH_LIFETIME_DAYS')
    ),
}

# JWT Auto-Renewal and Session Extension Configuration
JWT_RENEWAL_CHECK_FREQUENCY_SECONDS = env('JWT_RENEWAL_CHECK_FREQUENCY_SECONDS')
JWT_RENEWAL_THRESHOLD_SECONDS = env('JWT_RENEWAL_THRESHOLD_SECONDS')
SESSION_EXTENSION_CHECK_FREQUENCY_SECONDS = env('SESSION_EXTENSION_CHECK_FREQUENCY_SECONDS')
SESSION_EXTENSION_THRESHOLD_SECONDS = env('SESSION_EXTENSION_THRESHOLD_SECONDS')

# Django AllAuth Configuration
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# AllAuth Settings (Updated for latest version)
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*']
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

# Social Account Settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_QUERY_EMAIL = True

# Social Account Providers
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SDK_URL': '//connect.facebook.net/{locale}/sdk.js',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': [
            'id',
            'first_name',
            'last_name',
            'middle_name',
            'name',
            'name_format',
            'picture',
            'short_name',
            'email',
        ],
        'EXCHANGE_TOKEN': True,
        'LOCALE_FUNC': 'path.to.callable',
        'VERIFIED_EMAIL': False,
        'VERSION': 'v18.0',
    },
    'github': {
        'SCOPE': [
            'user:email',
        ],
    },
    'twitter': {
        'SCOPE': [
            'tweet.read',
            'users.read',
        ],
    },
}

# Redis settings for session management
REDIS_HOST = env('REDIS_HOST')
REDIS_PORT = env('REDIS_PORT')
REDIS_DB = env('REDIS_DB')
REDIS_URL = env('REDIS_URL')

# Email configuration
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST')         # Your SMTP server
EMAIL_PORT = env('EMAIL_PORT')                            # Usually 587 for TLS, 465 for SSL, or 25
EMAIL_HOST_USER = env('EMAIL_HOST_USER')           # Your SMTP username
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')       # Your SMTP password
EMAIL_USE_TLS = env('EMAIL_USE_TLS')                        # True for TLS, False for SSL or plain
EMAIL_USE_SSL = env('EMAIL_USE_SSL')                       # True for SSL, False for TLS or plain
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')           # Default from email address

# Domain Configuration
DOMAIN_URL = env('DOMAIN_URL')
FRONTEND_DOMAIN = env('FRONTEND_DOMAIN')

# Celery configuration
CELERY_BROKER_URL = env('REDIS_URL')
CELERY_RESULT_BACKEND = env('REDIS_URL')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Django Celery Beat - Database Scheduler Configuration
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

CELERY_BEAT_SCHEDULE = {
    # --- Search App Tasks ---
    'cache-all-users-recent-searches': {
        'task': 'search.tasks.cache_all_users_recent_searches',
        'schedule': crontab(minute='*/10'),
    },
    'analyze-search-queries': {
        'task': 'search.tasks.analyze_search_queries',
        'schedule': crontab(minute='*/30'),
    },
    'count-search-queries-by-type': {
        'task': 'search.tasks.count_search_queries_by_type',
        'schedule': crontab(hour=0, minute=0),
    },

    # --- Automatic Verification System ---
    'cleanup-expired-verification-codes': {
        'task': 'accounts.tasks.cleanup_expired_verification_codes',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },

    # --- Accounts/User Tasks ---
    'deactivate-expired-users-daily': {
        'task': 'accounts.tasks.deactivate_expired_users',
        'schedule': crontab(hour=3, minute=0),  # runs daily at 3am
    },

    'update-user-counters': {
        'task': 'accounts.tasks.update_user_counters',
        'schedule': crontab(minute='*/30'),
    },
    'update-user-engagement-scores': {
        'task': 'accounts.tasks.update_user_engagement_scores',
        'schedule': crontab(hour=2, minute=0),
    },
    'cleanup-old-user-events': {
        'task': 'accounts.tasks.cleanup_old_user_events',
        'schedule': crontab(hour=3, minute=15),
    },
    'analyze-user-security-events': {
        'task': 'accounts.tasks.analyze_user_security_events',
        'schedule': crontab(hour=0, minute=15),
    },
    'update-user-session-analytics': {
        'task': 'accounts.tasks.update_user_session_analytics',
        'schedule': crontab(minute='*/20'),
    },
    'process-user-event-alerts': {
        'task': 'accounts.tasks.process_user_event_alerts',
        'schedule': crontab(minute='*/5'),
    },

    'end-expired-sessions': {
        'task': 'accounts.tasks.end_expired_sessions',
        'schedule': crontab(minute='*/15'),  # Check every 15 minutes
    },
    'cleanup-ended-sessions': {
        'task': 'accounts.tasks.cleanup_ended_sessions',
        'schedule': crontab(hour=5, minute=30),  # Daily cleanup at 5:30 AM
    },
    'generate-user-analytics-report': {
        'task': 'accounts.tasks.generate_user_analytics_report',
        'schedule': crontab(hour=5, minute=0),
    },

    # --- Content/Recommendation Tasks ---
    'process-bot-detection-analysis': {
        'task': 'content.tasks.process_bot_detection_analysis',
        'schedule': crontab(hour=0, minute=0),
    },
    'cleanup-bot-detection-data': {
        'task': 'content.tasks.cleanup_bot_detection_data',
        'schedule': crontab(hour=1, minute=0),
    },
    'process-moderation-queue': {
        'task': 'content.tasks.process_moderation_queue',
        'schedule': crontab(minute='*/15'),
    },
    'update-moderation-analytics': {
        'task': 'content.tasks.update_moderation_analytics',
        'schedule': crontab(hour=2, minute=0),
    },
    'update-content-counters': {
        'task': 'content.tasks.update_content_counters',
        'schedule': crontab(minute='*/30'),
    },
    'update-trending-hashtags': {
        'task': 'content.tasks.update_trending_hashtags',
        'schedule': crontab(minute=0),
    },
    'process-mentions': {
        'task': 'content.tasks.process_mentions',
        'schedule': crontab(minute='*/15'),
    },
    'generate-content-recommendations': {
        'task': 'content.tasks.generate_content_recommendations',
        'schedule': crontab(hour=3, minute=0),
    },
    'update-content-similarity-scores': {
        'task': 'content.tasks.update_content_similarity_scores',
        'schedule': crontab(hour=4, minute=0),
    },
    'generate-trending-content-recommendations': {
        'task': 'content.tasks.generate_trending_content_recommendations',
        'schedule': crontab(hour=5, minute=0),
    },
    'update-user-content-preferences': {
        'task': 'content.tasks.update_user_content_preferences',
        'schedule': crontab(hour=6, minute=0),
    },
    'generate-collaborative-filtering-recommendations': {
        'task': (
            'content.tasks.generate_collaborative_filtering_recommendations'
        ),
        'schedule': crontab(hour=7, minute=0),
    },
    'cleanup-old-recommendations': {
        'task': 'content.tasks.cleanup_old_recommendations',
        'schedule': crontab(hour=8, minute=0),
    },
    'update-recommendation-performance-metrics': {
        'task': 'content.tasks.update_recommendation_performance_metrics',
        'schedule': crontab(hour=9, minute=0),
    },
    'cleanup-old-content': {
        'task': 'content.tasks.cleanup_old_content',
        'schedule': crontab(hour=10, minute=0),
    },
    'send-content-notification-emails': {
        'task': 'content.tasks.send_content_notification_emails',
        'schedule': crontab(hour=11, minute=0),
    },
    'auto-stop-content-experiments': {
        'task': 'content.tasks.auto_stop_content_experiments',
        'schedule': crontab(hour=12, minute=0),
    },
    'cleanup-content-experiment-metrics': {
        'task': 'content.tasks.cleanup_content_experiment_metrics',
        'schedule': crontab(hour=13, minute=0),
    },

    # --- Analytics Tasks ---
    'process-daily-analytics': {
        'task': 'analytics.tasks.process_daily_analytics',
        'schedule': crontab(hour=1, minute=0),
    },
    'update-system-metrics': {
        'task': 'analytics.tasks.update_system_metrics',
        'schedule': crontab(minute='*/10'),
    },
    'cleanup-old-data': {
        'task': 'analytics.tasks.cleanup_old_data',
        'schedule': crontab(hour=4, minute=0),
    },
    'update-user-engagement-scores-analytics': {
        'task': 'analytics.tasks.update_user_engagement_scores',
        'schedule': crontab(hour=2, minute=30),
    },
    'process-analytics-daily': {
        'task': 'analytics.tasks.process_analytics_daily',
        'schedule': crontab(hour=3, minute=0),
    },
    'update-advanced-system-metrics': {
        'task': 'analytics.tasks.update_advanced_system_metrics',
        'schedule': crontab(hour=3, minute=30),
    },
    'comprehensive-cleanup': {
        'task': 'analytics.tasks.comprehensive_cleanup',
        'schedule': crontab(hour=4, minute=30),
    },
    'generate-weekly-analytics-report': {
        'task': 'analytics.tasks.generate_weekly_analytics_report',
        'schedule': crontab(hour=5, minute=0, day_of_week=0),
    },

    # --- Notification Tasks ---
    'send-notification-emails': {
        'task': 'notifications.tasks.send_notification_emails',
        'schedule': crontab(minute='*/15'),
    },
    'cleanup-old-notifications': {
        'task': 'notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0),
    },
    'generate-notification-digest': {
        'task': 'notifications.tasks.generate_notification_digest',
        'schedule': crontab(hour=3, minute=0),
    },
    'update-notification-metrics': {
        'task': 'notifications.tasks.update_notification_metrics',
        'schedule': crontab(hour=4, minute=0),
    },

    # --- Poll Tasks ---
    'handle-poll-expiration': {
        'task': 'polls.tasks.handle_poll_expiration',
        'schedule': crontab(minute='*/10'),
    },
    'update-poll-counters': {
        'task': 'polls.tasks.update_poll_counters',
        'schedule': crontab(minute='*/5'),
    },
    'analyze-poll-engagement': {
        'task': 'polls.tasks.analyze_poll_engagement',
        'schedule': crontab(hour=5, minute=30),
    },
    'generate-poll-analytics': {
        'task': 'polls.tasks.generate_poll_analytics',
        'schedule': crontab(hour=1, minute=30),
    },
    'analyze-poll-option-performance': {
        'task': 'polls.tasks.analyze_poll_option_performance',
        'schedule': crontab(hour=2, minute=30),
    },
    'cleanup-empty-poll-options': {
        'task': 'polls.tasks.cleanup_empty_poll_options',
        'schedule': crontab(hour=3, minute=0),
    },
    'reorder-poll-options-by-popularity': {
        'task': 'polls.tasks.reorder_poll_options_by_popularity',
        'schedule': crontab(hour=4, minute=0),
    },
    'generate-poll-option-insights': {
        'task': 'polls.tasks.generate_poll_option_insights',
        'schedule': crontab(hour=5, minute=0),
    },

    # --- Community Tasks ---
    'reactivate-expired-bans': {
        'task': 'communities.tasks.reactivate_expired_bans',
        'schedule': crontab(hour=0, minute=0),
    },
    'update-community-basic-metrics': {
        'task': 'communities.tasks.update_community_basic_metrics',
        'schedule': crontab(hour=6, minute=0),
    },
    'sync-community-with-analytics': {
        'task': 'communities.tasks.sync_community_with_analytics',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'cleanup-expired-community-invitations': {
        'task': 'communities.tasks.cleanup_expired_community_invitations',
        'schedule': crontab(hour=3, minute=30),
    },
    'update-community-member-counts': {
        'task': 'communities.tasks.update_community_member_counts',
        'schedule': crontab(hour=7, minute=0),
    },
    'cleanup-inactive-communities': {
        'task': 'communities.tasks.cleanup_inactive_communities',
        'schedule': crontab(hour=8, minute=0),
    },
    'process-community-join-requests': {
        'task': 'communities.tasks.process_community_join_requests',
        'schedule': crontab(hour=9, minute=0),
    },
    'validate-community-access-rules': {
        'task': 'communities.tasks.validate_community_access_rules',
        'schedule': crontab(hour=10, minute=0),
    },
    'update-community-moderation-stats': {
        'task': 'communities.tasks.update_community_moderation_stats',
        'schedule': crontab(hour=11, minute=0),
    },
    'update-community-role-stats': {
        'task': 'communities.tasks.update_community_role_stats',
        'schedule': crontab(hour=12, minute=0),
    },

    # --- Community Analytics Tasks (Real-time) ---
    'cleanup-inactive-community-users': {
        'task': 'analytics.tasks.cleanup_inactive_users',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'update-realtime-community-analytics': {
        'task': 'analytics.tasks.update_community_analytics',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },

    # --- AI Conversation System Tasks ---
    'summarize-deleted-ai-conversations': {
        'task': 'ai_conversations.tasks.summarize_deleted_ai_conversations',
        'schedule': crontab(hour=0, minute=0),
    },
    'update-ai-usage-analytics': {
        'task': 'ai_conversations.tasks.update_ai_usage_analytics',
        'schedule': crontab(hour=0, minute=30),
    },
    'update-ai-model-performance': {
        'task': 'ai_conversations.tasks.update_ai_model_performance',
        'schedule': crontab(hour=1, minute=0),
    },
    'generate-conversation-summaries': {
        'task': 'ai_conversations.tasks.generate_conversation_summaries',
        'schedule': crontab(hour=4, minute=30),
    },
    'cleanup-old-ai-data': {
        'task': 'ai_conversations.tasks.cleanup_old_ai_data',
        'schedule': crontab(hour=5, minute=0),
    },
    'update-agent-statistics': {
        'task': 'ai_conversations.tasks.update_agent_statistics',
        'schedule': crontab(hour=6, minute=30),
    },
    # --- Community Analytics Tasks (Real-time Tracking) ---
    'cleanup-inactive-users': {
        'task': 'analytics.tasks.cleanup_inactive_users',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'update-community-analytics': {
        'task': 'analytics.tasks.update_community_analytics',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': (
                '{levelname} {asctime} {module} {process:d} {thread:d} '
                '{message}'
            ),
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'content': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'analytics': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
# Default X-Frame options; can be overridden via env if necessary
X_FRAME_OPTIONS = env('X_FRAME_OPTIONS', default='SAMEORIGIN')

# Proxy settings for proper IP detection behind Cloudflare/reverse proxies
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Use environment-configurable secure settings so deployments can opt-in
# to strict defaults. When DEBUG=False the sensible defaults below enable
# HTTPS-only behaviour; override via .env in non-production setups.
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=(31536000 if not DEBUG else 0))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=True)
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=(not DEBUG))

# Content Security Policy for Password Protection (Django CSP 4.0+ format)
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': ("'self'", "'unsafe-eval'" if DEBUG else "'self'"),
        'style-src': ("'self'", "'unsafe-inline'"),
        'img-src': ("'self'", "data:", "blob:", "https:"),
        'font-src': ("'self'", "data:", "https:"),
        'connect-src': ("'self'", "ws:", "wss:"),
        'media-src': ("'self'", "data:", "blob:"),
        'object-src': ("'none'",),
        'frame-ancestors': ("'self'",),
        'form-action': ("'self'",),
        'base-uri': ("'self'",),
    }
}

# CSP Reporting configuration
if DEBUG:
    CONTENT_SECURITY_POLICY_REPORT_ONLY = CONTENT_SECURITY_POLICY
else:
    # Enforce CSP in production
    pass

# Additional Security Headers for Password Protection
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_FRAME_DENY = False  # Using X_FRAME_OPTIONS instead

# AWS S3 configuration (for production)
if env('AWS_ACCESS_KEY_ID'):
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')  # type: ignore
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')  # type: ignore
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')  # type: ignore
    AWS_S3_REGION_NAME = env.str('AWS_S3_REGION_NAME')  # type: ignore
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_S3_VERIFY = True

    # Static files
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    STATIC_URL_S3 = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

    # Media files
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL_S3 = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Custom settings for social network
SOCIAL_NETWORK_SETTINGS = {
    'MAX_POST_LENGTH': 2000,
}

# AI Conversation System Settings
AI_SETTINGS: dict[str, object] = {
    'OPENAI_API_KEY': env('OPENAI_API_KEY'),
    'OPENAI_ORG_ID': env('OPENAI_ORG_ID'),
    'ANTHROPIC_API_KEY': env('ANTHROPIC_API_KEY'),
    'GOOGLE_AI_API_KEY': env('GOOGLE_AI_API_KEY'),
    'DEFAULT_MODEL': env('AI_DEFAULT_MODEL'),
    'MAX_TOKENS': env('AI_MAX_TOKENS'),
    'TEMPERATURE': env('AI_TEMPERATURE'),
    'ENABLE_STREAMING': env('AI_ENABLE_STREAMING'),
    'ENABLE_FUNCTION_CALLING': env('AI_ENABLE_FUNCTION_CALLING'),
    'ENABLE_VISION': env('AI_ENABLE_VISION'),
    'DAILY_COST_LIMIT': env('AI_DAILY_COST_LIMIT'),
    'USER_DAILY_LIMIT': env('AI_USER_DAILY_LIMIT'),
    'ENABLE_COST_TRACKING': env('AI_ENABLE_COST_TRACKING'),
    'ENABLE_CONTENT_FILTER': env('AI_ENABLE_CONTENT_FILTER'),
    'FILTER_LEVEL': env('AI_FILTER_LEVEL'),
}

# Twilio SMS Configuration
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = env('TWILIO_PHONE_NUMBER')

# Performance monitoring
PERFORMANCE_MONITORING: dict[str, object] = {
    'TRACK_QUERIES': True,
    'SLOW_QUERY_THRESHOLD': 0.5,  # seconds
    'TRACK_CACHE_HITS': True,
    'TRACK_RESPONSE_TIME': True,
}
