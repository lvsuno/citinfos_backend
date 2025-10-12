"""URLs for the analytics app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import visitor_views

router = DefaultRouter()
router.register(r'daily', views.DailyAnalyticsViewSet, basename='daily')
router.register(
    r'user-analytics', views.UserAnalyticsViewSet, basename='user-analytics'
)
router.register(r'metrics', views.SystemMetricViewSet, basename='metric')
router.register(r'errors', views.ErrorLogViewSet, basename='error')
router.register(
    r'visitors',
    visitor_views.VisitorAnalyticsViewSet,
    basename='visitor-analytics'
)

urlpatterns = [
    path('api/', include(router.urls)),

    # ========================================================================
    # VISITOR ANALYTICS API ENDPOINTS (For Tests)
    # ========================================================================

    path('api/analytics/visitors/',
         views.visitors_api,
         name='analytics-visitors'),

    path('api/analytics/visitors/today/',
         views.visitors_today_api,
         name='analytics-visitors-today'),

    path('api/analytics/visitors/weekly/',
         views.visitors_weekly_api,
         name='analytics-visitors-weekly'),

    path('api/analytics/visitors/monthly/',
         views.visitors_monthly_api,
         name='analytics-visitors-monthly'),

    path('api/analytics/division-breakdown/',
         views.division_breakdown_api,
         name='analytics-division-breakdown'),

    path('api/analytics/trends/',
         views.trends_api,
         name='analytics-trends'),

    path('api/analytics/conversions/',
         views.conversions_api,
         name='analytics-conversions'),

    path('api/analytics/demographics/',
         views.demographics_api,
         name='analytics-demographics'),

    path('api/analytics/realtime/',
         views.realtime_visitors_api,
         name='analytics-realtime'),

    path('api/analytics/growth/',
         views.growth_api,
         name='analytics-growth'),

    path('api/analytics/export/',
         views.export_visitors_csv,
         name='analytics-export'),

    # ========================================================================
    # VISITOR ANALYTICS ENDPOINTS
    # ========================================================================

    # Convenience endpoints for quick access
    path(
        'api/communities/<uuid:community_id>/visitors/today/',
        visitor_views.community_visitors_today,
        name='community-visitors-today'
    ),

    path(
        'api/communities/<uuid:community_id>/visitors/weekly/',
        visitor_views.community_visitors_weekly,
        name='community-visitors-weekly'
    ),

    path(
        'api/communities/<uuid:community_id>/visitors/monthly/',
        visitor_views.community_visitors_monthly,
        name='community-visitors-monthly'
    ),

    path(
        'api/communities/<uuid:community_id>/visitors/growth/',
        visitor_views.community_visitor_growth,
        name='community-visitor-growth'
    ),

    # ========================================================================
    # ADMIN ANALYTICS ENDPOINTS
    # ========================================================================

    # Admin Analytics URLs (what the frontend is calling)
    path('api/analytics/admin/realtime/',
         views.admin_realtime,
         name='admin-realtime-analytics'),

    path('api/analytics/admin/system-performance/',
         views.admin_system_performance,
         name='admin-system-performance'),

    path('api/analytics/admin/top-content/',
         views.admin_top_content,
         name='admin-top-content'),

    path('api/analytics/admin/user-behavior/',
         views.admin_user_behavior,
         name='admin-user-behavior'),

    path('api/analytics/admin/search-trends/',
         views.admin_search_trends,
         name='admin-search-trends'),

    path('api/analytics/admin/authentication/',
         views.admin_authentication,
         name='admin-authentication-analytics'),

    path('api/analytics/admin/overview/',
         views.admin_overview,
         name='admin-overview'),

    # Additional endpoints that might be called
    path('api/analytics/admin/content/',
         views.admin_top_content,  # Reuse top content for now
         name='admin-content-analytics'),

    path('api/analytics/admin/search/',
         views.admin_search_trends,  # Reuse search trends
         name='admin-search-analytics'),

    path('api/analytics/admin/users/',
         views.admin_user_behavior,  # Reuse user behavior
         name='admin-users-analytics'),

    # PostSee Analytics endpoint for dashboard
    path('api/analytics/admin/postsee/',
         views.admin_postsee_analytics,
         name='admin-postsee-analytics'),

    # PostSee Analytics URLs
    path('api/postsee/', include('analytics.urls_postsee')),

    # Community Analytics URLs
    path('api/communities/<uuid:community_id>/online-count/',
         views.get_community_online_count,
         name='community-online-count'),

    path('api/communities/<uuid:community_id>/analytics/',
         views.get_community_analytics,
         name='community-analytics'),

    path('api/communities/<uuid:community_id>/track-activity/',
         views.track_community_activity,
         name='track-community-activity'),

    path('api/user/communities/status/',
         views.get_user_communities_status,
         name='user-communities-status'),
]
