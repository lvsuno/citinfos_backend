"""
WebSocket URL routing for real-time notifications.

This module defines the WebSocket routes for the notifications system.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # User notification WebSocket
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),

    # Admin notification WebSocket
    re_path(r'ws/admin/notifications/$', consumers.AdminNotificationConsumer.as_asgi()),
]
