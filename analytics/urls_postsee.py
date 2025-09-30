"""
URL patterns for PostSee analytics API endpoints.
"""
from django.urls import path
from . import postsee_views

app_name = 'postsee_analytics'

urlpatterns = [
    # Post view tracking
    path('track-view/', postsee_views.track_post_view_api, name='track_post_view'),

    # Analytics endpoints
    path('analytics/', postsee_views.post_view_analytics, name='post_view_analytics'),
    path('analytics/<uuid:post_id>/', postsee_views.post_view_analytics, name='post_specific_analytics'),

    # User view history
    path('user/history/', postsee_views.user_view_history, name='user_view_history'),

    # Content analytics integration
    path('content-summary/', postsee_views.content_analytics_summary, name='content_analytics_summary'),

    # Admin utilities
    path('sync/', postsee_views.sync_analytics, name='sync_analytics'),
]
