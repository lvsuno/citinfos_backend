"""
URL configuration for unified attachment system.

This file provides URL patterns for the enhanced API endpoints
that support the unified PostMedia system and multiple polls.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from content.unified_views import UnifiedPostViewSet


# Create router for the unified API
unified_router = DefaultRouter()
unified_router.register(r'posts', UnifiedPostViewSet, basename='unified-post')

urlpatterns = [
    # Unified API endpoints - MIGRATED from /api/v2/ to /api/content/
    path('api/content/', include(unified_router.urls)),

    # Direct endpoints for specific operations
    path(
        'api/content/posts/<uuid:pk>/attachments/',
        UnifiedPostViewSet.as_view({'get': 'attachments'}),
        name='post-attachments'
    ),
    path(
        'api/content/posts/<uuid:pk>/add-attachment/',
        UnifiedPostViewSet.as_view({'post': 'add_attachment'}),
        name='post-add-attachment'
    ),
    path(
        'api/content/posts/<uuid:pk>/remove-attachment/',
        UnifiedPostViewSet.as_view({'delete': 'remove_attachment'}),
        name='post-remove-attachment'
    ),
    path(
        'api/content/posts/<uuid:pk>/polls/',
        UnifiedPostViewSet.as_view({'get': 'polls'}),
        name='post-polls'
    ),
    path(
        'api/content/posts/<uuid:pk>/add-poll/',
        UnifiedPostViewSet.as_view({'post': 'add_poll'}),
        name='post-add-poll'
    ),
    path(
        'api/content/posts/<uuid:pk>/migrate-legacy-media/',
        UnifiedPostViewSet.as_view({'post': 'migrate_legacy_media'}),
        name='post-migrate-legacy-media'
    ),
    path(
        'api/content/posts/migration-status/',
        UnifiedPostViewSet.as_view({'get': 'migration_status'}),
        name='migration-status'
    ),
    path(
        'api/content/posts/bulk-create/',
        UnifiedPostViewSet.as_view({'post': 'bulk_create_with_attachments'}),
        name='post-bulk-create'
    ),

    # Social interaction endpoints - MIGRATED from /api/v2/
    path(
        'api/content/posts/feed/',
        UnifiedPostViewSet.as_view({'get': 'feed'}),
        name='post-feed'
    ),
    path(
        'api/content/posts/<uuid:pk>/like/',
        UnifiedPostViewSet.as_view({'post': 'like'}),
        name='post-like'
    ),
    path(
        'api/content/posts/<uuid:pk>/dislike/',
        UnifiedPostViewSet.as_view({'post': 'dislike'}),
        name='post-dislike'
    ),
    path(
        'api/content/posts/<uuid:pk>/repost/',
        UnifiedPostViewSet.as_view({'post': 'repost'}),
        name='post-repost'
    ),
    path(
        'api/content/posts/comments/<uuid:comment_id>/like/',
        UnifiedPostViewSet.as_view({'post': 'like_comment'}),
        name='comment-like'
    ),
    path(
        'api/content/posts/comments/<uuid:comment_id>/dislike/',
        UnifiedPostViewSet.as_view({'post': 'dislike_comment'}),
        name='comment-dislike'
    ),
]


# Example API usage documentation
"""
API USAGE EXAMPLES - UPDATED ENDPOINTS:

1. Create a post with multiple attachments:
   POST /api/content/posts/
   {
       "content": "My awesome post!",
       "attachments": [
           {"media_type": "image", "file": "<upload>"},
           {"media_type": "video", "file": "<upload>"}
       ]
   }

2. Add attachment to existing post:
   POST /api/content/posts/{post_id}/add-attachment/
   {
       "media_type": "image",
       "file": "<upload>"
   }

3. Get all attachments for a post:
   GET /api/content/posts/{post_id}/attachments/

4. Create a post with multiple polls:
   POST /api/content/posts/
   {
       "content": "Help me decide!",
       "polls": [
           {
               "question": "Which color?",
               "options": [
                   {"text": "Red"},
                   {"text": "Blue"}
               ]
           }
       ]
   }

5. Add poll to existing post:
   POST /api/content/posts/{post_id}/add-poll/
   {
       "question": "What do you think?",
       "options": [
           {"text": "Option 1"},
           {"text": "Option 2"}
       ]
   }

6. Bulk create posts with attachments:
   POST /api/content/posts/bulk-create/
   {
       "posts": [
           {
               "content": "Post 1",
               "attachments": [...],
               "polls": [...]
           }
       ]
   }

7. Check migration status (staff only):
   GET /api/content/posts/migration-status/

8. Migrate specific post (staff only):
   POST /api/content/posts/{post_id}/migrate-legacy-media/

9. Get posts by hashtag (paginated):
   GET /api/content/posts/by_hashtag/?hashtag=python&page=1&page_size=20

10. Get all hashtags with filtering:
    GET /api/content/posts/hashtags/?trending=true&search=python&limit=50

11. Get trending hashtags only:
    GET /api/content/posts/trending_hashtags/?limit=20
"""
