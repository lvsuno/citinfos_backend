from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import jwt_views
from . import public_views
from . import contact_change_views
from . import social_auth_views
from . import geolocation_views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'profiles', views.UserProfileViewSet)
router.register(r'professional-profiles', views.ProfessionalProfileViewSet)
router.register(r'follows', views.FollowViewSet, basename='follow')
router.register(r'blocks', views.BlockViewSet, basename='block')
router.register(r'sessions', views.UserSessionViewSet, basename='session')
router.register(r'events', views.UserEventViewSet, basename='event')
router.register(r'settings', views.UserSettingsViewSet, basename='settings')
router.register(r'verification-codes', views.VerificationCodeViewSet,
                basename='verification-code')
router.register(r'badge-definitions', views.BadgeDefinitionViewSet,
                basename='badge-definition')
router.register(r'user-badges', views.UserBadgeViewSet,
                basename='user-badge')

# Public profiles router (no authentication required)
public_router = DefaultRouter()
public_router.register(r'public-profiles', public_views.PublicUserProfileViewSet,
                      basename='public-profile')

urlpatterns = [
    # =========================================================================
    # ACTIVE AUTHENTICATION ENDPOINTS (JWT/Session Compatible)
    # =========================================================================

    # Primary JWT Authentication endpoints (ACTIVE - USE THESE)
    path('api/auth/register/', jwt_views.jwt_register,
         name='jwt_register'),
    path('api/auth/verify/', views.email_verify,
         name='email_verify'),  # For registration verification
    path('api/auth/resend-code/', views.resend_verification_code,
         name='resend_verification_code'),
    path('api/auth/login-with-verification-check/',
         jwt_views.login_with_verification_check,
         name='jwt_login_with_verification'),  # PRIMARY LOGIN
    path('api/auth/refresh/', jwt_views.CustomTokenRefreshView.as_view(),
         name='jwt_refresh'),
    path('api/auth/logout/', jwt_views.jwt_logout, name='jwt_logout'),
    path('api/auth/user-info/', jwt_views.jwt_user_info,
         name='jwt_user_info'),
    path('api/auth/change-password/', jwt_views.change_password,
         name='jwt_change_password'),
    path('api/auth/password-reset-confirm/', jwt_views.password_reset_confirm,
         name='jwt_password_reset_confirm'),
    path('api/auth/update-last-visited/', jwt_views.update_last_visited_url,
         name='update_last_visited_url'),

    # =========================================================================
    # UTILITY ENDPOINTS (ACTIVE - Commonly needed)
    # =========================================================================

    # Password utility endpoints
    path('api/auth/generate-passwords/',
         views.generate_password_suggestions_view, name='generate_passwords'),

    # Contact change endpoints (Email/Phone)
    path('api/auth/change-email/', contact_change_views.request_email_change,
         name='request_email_change'),
    path('api/auth/change-phone/', contact_change_views.request_phone_change,
         name='request_phone_change'),
    path('api/auth/verify-current/',
         contact_change_views.verify_current_contact,
         name='verify_current_contact'),
    path('api/auth/send-new-code/', contact_change_views.send_new_contact_code,
         name='send_new_contact_code'),
    path('api/auth/verify-new/', contact_change_views.verify_new_contact,
         name='verify_new_contact'),
    path('api/auth/change-status/',
         contact_change_views.get_change_request_status,
         name='change_request_status'),
    path('api/auth/cancel-change/', contact_change_views.cancel_change_request,
         name='cancel_change_request'),

    # User restoration endpoints (Admin only)
    path('api/auth/restore-user/', views.restore_user, name='restore_user'),
    path('api/auth/deleted-users/', views.list_deleted_users,
         name='list_deleted_users'),

    # =========================================================================
    # SOCIAL AUTHENTICATION ENDPOINTS (Django AllAuth Integration)
    # =========================================================================

    # Social authentication API endpoints
    path('api/auth/social/', social_auth_views.social_login,
         name='social_login'),
    path('api/auth/social/url/<str:provider>/', social_auth_views.social_login_url,
         name='social_login_url'),
    path('api/auth/social/apps/', social_auth_views.social_apps,
         name='social_apps'),

    # =========================================================================
    # GEOLOCATION ENDPOINTS (IP-based registration support)
    # =========================================================================

    # IP-based geolocation endpoints for user registration
    path('api/auth/location-data/', geolocation_views.get_user_location_data,
         name='get_user_location_data'),
    path('api/auth/search-divisions/', geolocation_views.search_divisions,
         name='search_divisions'),
    path('api/auth/division-neighbors/<uuid:division_id>/',
         geolocation_views.get_division_neighbors,
         name='get_division_neighbors'),

    # Administrative division browsing endpoints for map
    path('api/auth/countries/', geolocation_views.get_countries,
         name='get_countries'),
    path('api/auth/divisions/', geolocation_views.get_divisions_by_level,
         name='get_divisions_by_level'),
    path('api/auth/divisions/<uuid:division_id>/geometry/',
         geolocation_views.get_division_geometry,
         name='get_division_geometry'),
    path('api/auth/divisions/by-slug/',
         geolocation_views.get_division_by_slug,
         name='get_division_by_slug'),

    # Include router URLs for profiles
    path('api/', include(router.urls)),
    path('api/', include(public_router.urls)),

    # Additional public profile endpoints
    path('api/public/profiles/username/<str:username>/',
         public_views.public_profile_by_username,
         name='public-profile-by-username'),
    path('api/public/users/<uuid:user_id>/posts/',
         public_views.public_user_posts,
         name='public-user-posts'),

]
