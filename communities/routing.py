"""
WebSocket URL routing for the communities app.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Connect to a specific community by id
    re_path(r'ws/communities/(?P<community_id>[0-9a-fA-F-]+)/$', consumers.CommunityConsumer.as_asgi()),
]
