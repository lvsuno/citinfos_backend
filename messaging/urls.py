from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from . import views

# Create router for messaging API endpoints
router = DefaultRouter()

# Add viewsets when they exist
# router.register(r'chat-rooms', views.ChatRoomViewSet, basename='chatroom')
# router.register(r'messages', views.MessageViewSet, basename='message')
# router.register(r'presence', views.UserPresenceViewSet, basename='presence')
# router.register(r'reactions', views.MessageReactionViewSet, basename='reaction')

urlpatterns = [
    path('api/messaging/', lambda r: JsonResponse({'message': 'Messaging API'})),
    # When viewsets are implemented, use singular 'message' not 'messages':
    # path('api/message/', include(router.urls)),
]
