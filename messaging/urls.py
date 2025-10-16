from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for messaging API endpoints
router = DefaultRouter()

# Register viewsets
router.register(r'rooms', views.ChatRoomViewSet, basename='chatroom')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'read-status', views.MessageReadViewSet, basename='messageread')
router.register(r'presence', views.UserPresenceViewSet, basename='presence')
router.register(r'users', views.UserListViewSet, basename='messaging-users')

urlpatterns = [
    # Messaging API endpoints
    path('api/messaging/', include(router.urls)),
]
