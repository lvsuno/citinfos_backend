"""WebSocket URL routing for analytics app."""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Real-time visitor count for a community
    re_path(
        r'ws/communities/(?P<community_id>[0-9a-fA-F-]+)/visitors/$',
        consumers.VisitorAnalyticsConsumer.as_asgi()
    ),

    # Visitor analytics dashboard for moderators/admins
    re_path(
        r'ws/communities/(?P<community_id>[0-9a-fA-F-]+)/visitor-dashboard/$',
        consumers.VisitorDashboardConsumer.as_asgi()
    ),
]
