"""
URL patterns for post view tracking APIs.
"""
from django.urls import path
from . import views_tracking

app_name = 'tracking'

urlpatterns = [
    # Post view tracking endpoints
    path('posts/view/',
         views_tracking.track_post_view,
         name='track_post_view'),
    path('posts/interaction/',
         views_tracking.track_post_interaction,
         name='track_post_interaction'),
    path('posts/batch-views/',
         views_tracking.batch_track_views,
         name='batch_track_views'),
    path('posts/<uuid:post_id>/analytics/',
         views_tracking.get_post_analytics,
         name='get_post_analytics'),

    # Legacy endpoint for non-DRF compatibility
    path('legacy/track-view/',
         views_tracking.LegacyTrackPostView.as_view(),
         name='legacy_track_view'),
]
