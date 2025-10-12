from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'communities', views.CommunityViewSet, basename='community')
router.register(r'threads', views.ThreadViewSet, basename='thread')
router.register(r'community-memberships', views.CommunityMembershipViewSet, basename='community-membership')
router.register(r'community-roles', views.CommunityRoleViewSet, basename='community-role')
router.register(r'community-moderation', views.CommunityModerationViewSet, basename='community-moderation')
# router.register(r'community-invitations', views.CommunityInvitationViewSet, basename='community-invitation')  # Commented - public communities
# router.register(r'community-join-requests', views.CommunityJoinRequestViewSet, basename='community-join-request')  # Commented - public communities
router.register(r'community-announcements', views.CommunityAnnouncementViewSet, basename='community-announcement')

app_name = 'communities'

urlpatterns = [
    path('api/', include(router.urls)),
]