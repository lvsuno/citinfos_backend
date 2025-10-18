"""
Content app URL configuration with standardized patterns.

URL Structure:
- /api/content/ - Main content endpoints (posts, comments, likes, etc.)
- /api/v2/ - Unified attachment system (from unified_urls.py)

All social interactions follow: /api/content/posts/{id}/{action}/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .unified_views import UnifiedPostViewSet

# Main content router
router = DefaultRouter()

# Core content models - only keep what's actively used
# NOTE: Posts are handled by unified_urls.py at /api/content/posts/
router.register(r'comments', views.CommentViewSet, basename='content-comment')
router.register(r'direct-shares', views.DirectShareViewSet,
                basename='content-directshare')
router.register(r'media', views.PostMediaViewSet, basename='content-media')

# Moderation endpoints
router.register(r'reports', views.ContentReportViewSet,
                basename='content-report')
router.register(r'moderation-queue', views.ModerationQueueViewSet,
                basename='content-moderation-queue')
router.register(r'auto-moderation', views.AutoModerationActionViewSet,
                basename='content-auto-moderation')
router.register(r'moderation-rules', views.ContentModerationRuleViewSet,
                basename='content-moderation-rules')

# Bot detection endpoints
router.register(r'bot-events', views.BotDetectionEventViewSet,
                basename='content-bot-events')
router.register(r'bot-profiles', views.BotDetectionProfileViewSet,
                basename='content-bot-profiles')

# A/B Testing endpoints
router.register(r'experiments', views.ContentExperimentViewSet,
                basename='content-experiments')
router.register(r'experiment-assignments',
                views.UserContentExperimentAssignmentViewSet,
                basename='content-experiment-assignments')
router.register(r'experiment-metrics', views.ContentExperimentMetricViewSet,
                basename='content-experiment-metrics')
router.register(r'experiment-results', views.ContentExperimentResultViewSet,
                basename='content-experiment-results')

# Recommendation system endpoints
router.register(r'recommendations', views.ContentRecommendationViewSet,
                basename='content-recommendations')
router.register(r'similarities', views.ContentSimilarityViewSet,
                basename='content-similarities')
router.register(r'user-preferences', views.UserContentPreferencesViewSet,
                basename='content-user-preferences')
router.register(r'recommendation-feedback',
                views.RecommendationFeedbackViewSet,
                basename='content-recommendation-feedback')

urlpatterns = [
    # Main content API
     path('api/content/', include(router.urls)),
     # Also expose core content endpoints at the legacy root-level '/api/'
     # to support tests and older clients that expect '/api/posts/',
     # '/api/comments/' etc.
     path('api/', include(router.urls)),

    # Include unified attachment system (v2 API)
    path('', include('content.unified_urls')),

    # Social interaction endpoints using standardized paths
    path('api/content/posts/<uuid:pk>/like/',
         UnifiedPostViewSet.as_view({'post': 'like'}),
         name='content-post-like'),
    path('api/content/posts/<uuid:pk>/dislike/',
         UnifiedPostViewSet.as_view({'post': 'dislike'}),
         name='content-post-dislike'),
    path('api/content/posts/<uuid:pk>/repost/',
         UnifiedPostViewSet.as_view({'post': 'repost'}),
         name='content-post-repost'),
    path('api/content/posts/<uuid:pk>/comments/',
         UnifiedPostViewSet.as_view({'get': 'comments'}),
         name='content-post-comments'),
    path('api/content/posts/feed/',
         UnifiedPostViewSet.as_view({'get': 'feed'}),
         name='content-post-feed'),
    path('api/content/posts/user_posts/',
         UnifiedPostViewSet.as_view({'get': 'user_posts'}),
         name='content-post-user-posts'),

    # Draft management endpoints
    path('api/content/posts/drafts/',
         UnifiedPostViewSet.as_view({'get': 'drafts'}),
         name='content-post-drafts'),
    path('api/content/posts/<uuid:pk>/publish_draft/',
         UnifiedPostViewSet.as_view({'post': 'publish_draft'}),
         name='content-post-publish-draft'),

    # Thread voting and management endpoints
    path('api/content/posts/<uuid:pk>/upvote/',
         UnifiedPostViewSet.as_view({'post': 'upvote'}),
         name='content-post-upvote'),
    path('api/content/posts/<uuid:pk>/downvote/',
         UnifiedPostViewSet.as_view({'post': 'downvote'}),
         name='content-post-downvote'),
    path('api/content/posts/<uuid:pk>/mark_best_post/',
         UnifiedPostViewSet.as_view({'post': 'mark_best_post'}),
         name='content-post-mark-best'),
    path('api/content/posts/<uuid:pk>/toggle_pin/',
         UnifiedPostViewSet.as_view({'post': 'toggle_pin'}),
         name='content-post-toggle-pin'),

    # Comment interactions
    path('api/content/comments/<uuid:comment_id>/like/',
         UnifiedPostViewSet.as_view({'post': 'like_comment'}),
         name='content-comment-like'),
    path('api/content/comments/<uuid:comment_id>/dislike/',
         UnifiedPostViewSet.as_view({'post': 'dislike_comment'}),
         name='content-comment-dislike'),

    # A/B Testing specific endpoints with standardized paths
    path('api/content/experiments/<int:experiment_id>/start/',
         views.start_content_experiment,
         name='content-experiment-start'),
    path('api/content/experiments/<int:experiment_id>/stop/',
         views.stop_content_experiment,
         name='content-experiment-stop'),
    path('api/content/experiments/<int:experiment_id>/stats/',
         views.get_content_experiment_stats,
         name='content-experiment-stats'),
    path('api/content/user/<uuid:user_id>/algorithm/',
         views.get_user_algorithm,
         name='content-user-algorithm'),
    path('api/content/interactions/record/',
         views.record_content_interaction,
         name='content-record-interaction'),
    path('api/content/experiments/dashboard/',
         views.content_experiment_dashboard,
         name='content-experiment-dashboard'),
]
