from django.urls import path, include
from django.http import JsonResponse
from .views import (
    SessionValidationView, SessionRefreshView, check_session_status,
    DashboardStatsView, DashboardActivityView, DashboardTrendingView
)
from .views import api_timezones, api_countries, api_cities
from .debug_views import debug_ip_location, debug_custom_ip_location, debug_client_fingerprint
from .timezone_api import (
    UpdateSessionTimezoneView,
    validate_community_timezone_access_api
)
from .views import AnnouncementViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'announcements', AnnouncementViewSet, basename='announcement')

urlpatterns = [
    path(
        'api/core/',
        lambda r: JsonResponse({'message': 'Core API'})
    ),
    path(
        'api/core/session/validate/',
        SessionValidationView.as_view(),
        name='session-validate'
    ),
    path(
        'api/core/session/refresh/',
        SessionRefreshView.as_view(),
        name='session-refresh'
    ),
    path(
        'api/core/session/check/',
        check_session_status,
        name='session-check'
    ),

    # Dashboard endpoints
    path(
        'api/dashboard/stats/',
        DashboardStatsView.as_view(),
        name='dashboard-stats'
    ),
    path(
        'api/dashboard/activity/',
        DashboardActivityView.as_view(),
        name='dashboard-activity'
    ),
    path(
        'api/dashboard/trending/',
        DashboardTrendingView.as_view(),
        name='dashboard-trending'
    ),

    # Debug endpoints
    path(
        'api/debug/ip-location/',
        debug_ip_location,
        name='debug-ip-location'
    ),
    path(
        'api/debug/custom-ip-location/',
        debug_custom_ip_location,
        name='debug-custom-ip-location'
    ),
    path(
        'api/debug/client-fingerprint/',
        debug_client_fingerprint,
        name='debug-client-fingerprint'
    ),

    # Location/timezone endpoints
    path('api/timezones/', api_timezones, name='api-timezones'),
    path('api/countries/', api_countries, name='api-countries'),
    path('api/cities/', api_cities, name='api-cities'),

    # Timezone API endpoints
    path(
        'api/auth/update-session-timezone/',
        UpdateSessionTimezoneView.as_view(),
        name='update-session-timezone'
    ),
    path(
        'api/communities/<int:community_id>/validate-timezone-access/',
        validate_community_timezone_access_api,
        name='validate-community-timezone-access'
    ),

    # Announcement API
    path('api/', include(router.urls)),
]
