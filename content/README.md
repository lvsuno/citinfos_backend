````markdown
# Content App Documentation 📄

> **Latest Update**: Complete Hashtag Filtering System with 3 public endpoints for post discovery and hashtag management.

## Overview
The `content` app is the social media engine of the Equipment Database Social Platform. It manages posts, comments, likes/dislikes, reposts (4 types), shares, media attachments, hashtags, mentions, content moderation, bot detection, A/B testing, and intelligent content recommendation systems.

## ✅ **Current Implementation Status (August 2025)**

### **Hashtag System** - **FULLY OPERATIONAL** 🏷️
- **3 Hashtag Endpoints**: Complete hashtag management and post filtering system
- **Public Access**: All hashtag endpoints accessible without authentication
- **Post Filtering**: Get paginated posts by specific hashtag with search and trending filters
- **Trending Detection**: Automatic trending hashtag identification and filtering
- **7/7 Tests Passed**: 100% success rate in comprehensive integration testing

### **Enhanced Repost System** - **FULLY OPERATIONAL** 🎉
- **4 Repost Types Supported**: Simple, Comment, Quote, and Media reposts
- **Feed Integration**: All repost types properly displayed in unified feed API
- **6 Reposts Confirmed Working**: Successfully tested with various repost types
- **Legacy Migration**: Complete migration from old repost system to enhanced model
- **Performance Optimized**: Efficient querying with proper relationships and indexing

### **Authentication Integration** - **COMPLETE** ✅
- **JWT + Session Support**: Full compatibility with hybrid authentication system
- **Activity Tracking**: User content interactions automatically tracked
- **Auto-Token Renewal**: Seamless content browsing with automatic token refresh

## Key Features
- ✅ **Enhanced Repost System**: 4 repost types (Simple, Comment, Quote, Media) with full feed integration
- ✅ **Rich Content Creation**: Posts with media attachments, hashtags, and mentions
- ✅ **Hashtag System**: Complete hashtag management with trending detection and post filtering
- ✅ **Engagement System**: Likes, dislikes, shares, and comments with threading
- ✅ **Content Moderation**: Automated and manual moderation with reporting system
- ✅ **Bot Detection**: Advanced bot detection with behavioral analysis
- ✅ **A/B Testing Framework**: Content experimentation and performance tracking
- ✅ **AI Recommendation System**: Intelligent content suggestions based on user preferences
- ✅ **Community Context**: Smart detection of community-related content
- ✅ **Content Analytics**: Comprehensive tracking and metrics

---

## Models

### Core Content Models
- **Post**: Main content posts with visibility controls, soft deletion, and support for multiple attachments
- **Repost**: Enhanced repost system with 4 types (Simple, Comment, Quote, Media)
- **PostSee**: Track which users have seen which posts
- **PostMedia**: Unified media attachments system (images, videos, documents, audio) with multiple files per post
- **Comment**: Threaded comments on posts with soft deletion
- **Like/Dislike**: User reactions to posts and comments
- **Share**: Content sharing tracking
- **Hashtag**: Hashtag management and trending
- **PostHashtag**: Association between posts and hashtags
- **Mention**: User mentions in posts and comments

### **Enhanced Repost System** 🔄
- **4 Repost Types**:
  - **Simple**: Basic repost without additional content
  - **Comment**: Repost with user's commentary
  - **Quote**: Repost with quoted original content
  - **Media**: Repost with additional media attachments
- **Feed Integration**: All repost types appear seamlessly in unified feed
- **Relationship Management**: Proper tracking of original post relationships
- **Performance Optimized**: Efficient database queries with proper indexing

### Enhanced Features
- **Multiple Attachments**: Posts can have unlimited media attachments of any supported type
- **Unified Media System**: Single PostMedia model handles all attachment types with metadata
- **Migration Support**: Legacy media migration system with tracking capabilities

### Moderation & Safety Models
- **ContentReport**: User-generated content reports
- **ModerationQueue**: Queue for content requiring manual review
- **AutoModerationAction**: Automated moderation actions and results
- **ContentModerationRule**: Configurable moderation rules
- **BotDetectionEvent**: Bot detection events and analysis
- **BotDetectionProfile**: User behavioral profiles for bot detection

### Experimentation Models
- **ContentExperiment**: A/B testing experiments for content
- **UserContentExperimentAssignment**: User assignments to experiments
- **ContentExperimentMetric**: Metrics tracking for experiments
- **ContentExperimentResult**: Results and outcomes of experiments

### Recommendation Models
- **ContentRecommendation**: AI-generated content recommendations
- **ContentSimilarity**: Content similarity calculations
- **UserContentPreferences**: User preference learning
- **RecommendationFeedback**: User feedback on recommendations

---

## API Endpoints

### Core Content Management
| Resource           | Endpoint Prefix           | Description                        |
|--------------------|--------------------------|------------------------------------|
| Posts              | `/api/posts/`            | Create, read, update posts with media |
| Posts (Unified)    | `/api/content/posts/`    | Enhanced API with attachment management |
| **Reposts**        | `/api/reposts/`          | **Enhanced repost system with 4 types** |
| Comments           | `/api/comments/`         | Threaded comment system            |
| Likes              | `/api/likes/`            | Like/unlike posts and comments     |
| Dislikes           | `/api/dislikes/`         | Dislike posts and comments         |
| Shares             | `/api/shares/`           | Share posts and track sharing      |
| Media              | `/api/media/`            | Upload and manage post media       |
| **Hashtags**       | `/api/content/posts/hashtags/` | **Hashtag management and post filtering** |
| **Feed**           | `/api/content/posts/feed/` | **Unified feed with reposts integrated** |

### **Enhanced Repost API** 🔄
- `POST /api/reposts/` — Create any type of repost (Simple, Comment, Quote, Media)
- `GET /api/reposts/` — List user's reposts with filtering
- `GET /api/reposts/{id}/` — Get specific repost details
- `DELETE /api/reposts/{id}/` — Remove repost
- `GET /api/content/posts/feed/` — **Unified feed showing 6+ reposts successfully**

### **Hashtag API** 🏷️
- `GET /api/content/posts/hashtags/` — List all hashtags with optional trending filter and search
- `GET /api/content/posts/by_hashtag/` — Get paginated posts filtered by specific hashtag
- `GET /api/content/posts/trending_hashtags/` — Get trending hashtags with customizable limit

### **Repost Types Supported**:
```http
POST /api/reposts/
{
  "repost_type": "simple|comment|quote|media",
  "original_post": "<post_id>",
  "comment": "Optional comment for comment/quote types",
  "media_files": ["Optional media for media type"]
}
```

### **Hashtag Endpoints Examples**:
```http
# Get all hashtags with optional filters
GET /api/content/posts/hashtags/?trending=true&search=python&limit=50

# Get posts by specific hashtag (paginated)
GET /api/content/posts/by_hashtag/?hashtag=python&page=1&page_size=20

# Get trending hashtags only
GET /api/content/posts/trending_hashtags/?limit=20
```

### Enhanced V2 API Features
- `POST /api/content/posts/{id}/attachments/` — Add attachment to existing post
- `DELETE /api/content/posts/{id}/attachments/{attachment_id}/` — Remove specific attachment
- `GET /api/content/posts/{id}/attachments/` — List all post attachments
- `POST /api/content/posts/{id}/migrate-legacy-media/` — Migrate legacy media to unified system
- `GET /api/content/posts/hashtags/` — Get hashtags with optional trending filter and search
- `GET /api/content/posts/by_hashtag/` — Get posts filtered by hashtag with pagination
- `GET /api/content/posts/trending_hashtags/` — Get trending hashtags with customizable limits

### Moderation & Safety
| Resource           | Endpoint Prefix           | Description                        |
|--------------------|--------------------------|------------------------------------|
| Content Reports    | `/api/content-reports/`  | Report inappropriate content       |
| Moderation Queue   | `/api/moderation-queue/` | Manual moderation workflow         |
| Auto Moderation    | `/api/auto-moderation-actions/` | Automated moderation results |
| Moderation Rules   | `/api/content-moderation-rules/` | Configure moderation rules |
| Bot Detection      | `/api/bot-detection-events/` | Bot detection events and analysis |
| Bot Profiles       | `/api/bot-detection-profiles/` | User behavioral analysis |

### A/B Testing & Experimentation
| Resource           | Endpoint Prefix           | Description                        |
|--------------------|--------------------------|------------------------------------|
| Experiments        | `/api/experiments/`      | Create and manage A/B tests        |
| Experiment Assignments | `/api/experiment-assignments/` | User experiment assignments |
| Experiment Metrics | `/api/experiment-metrics/` | Track experiment performance     |
| Experiment Results | `/api/experiment-results/` | Analyze experiment outcomes      |

### AI Recommendation System
| Resource           | Endpoint Prefix           | Description                        |
|--------------------|--------------------------|------------------------------------|
| Recommendations    | `/api/recommendations/`  | Get personalized content recommendations |
| Content Similarity | `/api/similarities/`     | Content similarity analysis        |
| User Preferences   | `/api/user-content-preferences/` | User preference management |
| Recommendation Feedback | `/api/recommendation-feedback/` | Improve recommendations |

### Special Endpoints
- `POST /api/experiments/{id}/start/` — Start A/B testing experiment
- `POST /api/experiments/{id}/stop/` — Stop running experiment
- `GET /api/posts/{id}/analytics/` — Get detailed post analytics
- `POST /api/content/moderate/` — Trigger content moderation


## API Endpoints (CRUD Details)
All endpoints are prefixed with `/api/`.

### Posts (`posts/`)
| Method | Endpoint                | Description                |
|--------|-------------------------|----------------------------|
| GET    | /api/posts/             | List all posts             |
| POST   | /api/posts/             | Create a new post          |
| GET    | /api/posts/{id}/        | Retrieve a post            |
| PUT    | /api/posts/{id}/        | Update a post              |
| PATCH  | /api/posts/{id}/        | Partial update             |
| DELETE | /api/posts/{id}/        | Delete (soft) a post       |

### Comments (`comments/`)
| Method | Endpoint                | Description                |
|--------|-------------------------|----------------------------|
| GET    | /api/comments/          | List all comments          |
| POST   | /api/comments/          | Create a comment           |
| GET    | /api/comments/{id}/     | Retrieve a comment         |
| PUT    | /api/comments/{id}/     | Update a comment           |
| PATCH  | /api/comments/{id}/     | Partial update             |
| DELETE | /api/comments/{id}/     | Delete (soft) a comment    |

### Likes (`likes/`)
| Method | Endpoint                | Description                |
|--------|-------------------------|----------------------------|
| GET    | /api/likes/             | List all likes             |
| POST   | /api/likes/             | Like content               |
| GET    | /api/likes/{id}/        | Retrieve a like            |
| DELETE | /api/likes/{id}/        | Remove a like              |

### Dislikes (`dislikes/`)
| Method | Endpoint                | Description                |
|--------|-------------------------|----------------------------|
| GET    | /api/dislikes/          | List all dislikes          |
| POST   | /api/dislikes/          | Dislike content            |
| GET    | /api/dislikes/{id}/     | Retrieve a dislike         |
| DELETE | /api/dislikes/{id}/     | Remove a dislike           |

### Shares (`shares/`)
| Method | Endpoint                | Description                |
|--------|-------------------------|----------------------------|
| GET    | /api/shares/            | List all shares            |
| POST   | /api/shares/            | Share a post               |
| GET    | /api/shares/{id}/       | Retrieve a share           |
| DELETE | /api/shares/{id}/       | Remove a share             |

### Media (`media/`)
| Method | Endpoint                | Description                |
|--------|-------------------------|----------------------------|
| GET    | /api/media/             | List all media             |
| POST   | /api/media/             | Add media to a post        |
| GET    | /api/media/{id}/        | Retrieve media             |
| DELETE | /api/media/{id}/        | Remove media               |

### Moderation & Bot Detection
- `content-reports/`, `moderation-queue/`, `auto-moderation-actions/`, `content-moderation-rules/`, `bot-detection-events/`, `bot-detection-profiles/`
- All support full CRUD via `/api/{resource}/` endpoints.

### A/B Testing & Recommendation
- `experiments/`, `experiment-assignments/`, `experiment-metrics/`, `experiment-results/`
- `recommendations/`, `similarities/`, `user-content-preferences/`, `recommendation-feedback/`
- All support full CRUD via `/api/{resource}/` endpoints.

### Custom Endpoints
- `/api/experiments/{experiment_id}/start/` (POST): Start an experiment
- `/api/experiments/{experiment_id}/stop/` (POST): Stop an experiment
- `/api/experiments/{experiment_id}/stats/` (GET): Get experiment stats
- `/api/user/{user_id}/algorithm/` (GET): Get assigned algorithm for user
- `/api/record-interaction/` (POST): Record user interaction
- `/api/dashboard/` (GET): A/B testing dashboard

---

## Authentication Considerations
- Requests require `Authorization: Bearer <access_token>`
- Replace token when `X-Renewed-Access` header exists
- Access token expiration (5 minutes) will not interrupt active users because of auto-renew while session valid
- Refresh flow only needed if access expires without renewal header (session idle or invalid)

## Main ViewSets and Functions
- **PostViewSet**: CRUD for posts, like/share/comments actions
- **CommentViewSet**: CRUD for comments, like/replies actions
- **LikeViewSet**: CRUD for likes
- **DislikeViewSet**: CRUD for dislikes
- **ShareViewSet**: CRUD for shares
- **PostMediaViewSet**: CRUD for post media
- **ContentReportViewSet**: CRUD for content reports
- **ModerationQueueViewSet**: CRUD for moderation queue
- **AutoModerationActionViewSet**: CRUD for auto moderation actions
- **ContentModerationRuleViewSet**: CRUD for moderation rules
- **BotDetectionEventViewSet**: CRUD for bot detection events
- **BotDetectionProfileViewSet**: CRUD for bot detection profiles
- **ContentExperimentViewSet**: CRUD for A/B experiments
- **UserContentExperimentAssignmentViewSet**: CRUD for experiment assignments
- **ContentExperimentMetricViewSet**: CRUD for experiment metrics
- **ContentExperimentResultViewSet**: CRUD for experiment results
- **ContentRecommendationViewSet**: CRUD for recommendations
- **ContentSimilarityViewSet**: CRUD for content similarities
- **UserContentPreferencesViewSet**: CRUD for user content preferences
- **RecommendationFeedbackViewSet**: CRUD for recommendation feedback

---

## Models (Key Fields)
- **Post**: author, community, content, post_type, visibility, engagement metrics, media_migrated_to_postmedia, timestamps
- **Comment**: post, author, parent, content, engagement, timestamps
- **Like/Dislike**: user, content_object (post or comment), created_at
- **Share**: user, post, comment, created_at
- **PostMedia**: post, media_type, file, file_size, thumbnail, metadata, order, is_primary
- **ContentReport**: reporter, content_object, reason, status, reviewed_by, timestamps
- **ModerationQueue**: content_object, priority, status, reason, assigned_to, reviewed_by, timestamps
- **AutoModerationAction**: content_object, target_user, action_type, reason, status, reviewed_by, timestamps
- **ContentModerationRule**: name, rule_type, configuration, action, is_active, community, created_by
- **BotDetectionEvent/Profile**: user, event_type, severity, details, scores, status
- **ContentRecommendation**: user, content_object, score, recommendation_type, algorithm_version, metadata
- **ContentSimilarity**: content_object_1, content_object_2, similarity_score, similarity_type
- **UserContentPreferences**: user, preferred_hashtags, content_types, interaction_patterns, active_hours
- **RecommendationFeedback**: recommendation, user, feedback_type, comment
- **ContentExperiment**: name, control_algorithm, test_algorithm, traffic_split, status, created_by, start/end dates
- **UserContentExperimentAssignment**: user, experiment, group, assigned_at
- **ContentExperimentMetric**: experiment, user, metric_type, value, count, algorithm_used, recorded_at
- **ContentExperimentResult**: experiment, winner, metrics, p_value, summary, analyzed_by

---

## Example Usage
**Create a post with multiple attachments:**
```http
POST /api/content/posts/
Content-Type: multipart/form-data

{
  "content": "Check out these amazing photos!",
  "post_type": "media",
  "visibility": "public",
  "attachments": [file1, file2, file3]
}
```

**Add attachment to existing post:**
```http
POST /api/content/posts/{post_id}/attachments/
Content-Type: multipart/form-data

{
  "file": <file_object>,
  "media_type": "image"
}
```

**Get posts by hashtag:**
```http
GET /api/content/posts/by_hashtag/?hashtag=photography&page=1&page_size=20

Response:
{
  "hashtag": "photography",
  "count": 150,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_previous": false,
  "results": [
    {
      "id": "post-uuid",
      "content": "Beautiful sunset photo...",
      "hashtags": ["photography", "nature"],
      ...
    }
  ]
}
```

**Get trending hashtags:**
```http
GET /api/content/posts/trending_hashtags/?limit=10

Response:
{
  "count": 10,
  "results": [
    {
      "id": "hashtag-uuid",
      "name": "photography",
      "posts_count": 150,
      "is_trending": true,
      ...
    }
  ]
}
```

**Like a comment:**
```http
POST /api/likes/
{
  "content_type": "comment",
  "object_id": "<comment_uuid>"
}
```

---


## How Recommendations Work
The content recommendation system provides personalized content to users using a combination of collaborative filtering, content-based filtering, trending analysis, and hybrid algorithms. The system is designed to maximize user engagement and relevance.

### Recommendation Algorithms
- **Collaborative Filtering:** Suggests content based on the behavior and preferences of similar users (e.g., likes, shares, comments).
- **Content-Based Filtering:** Recommends content similar to what the user has interacted with, using hashtags, content type, and metadata.
- **Trending/Popular Content:** Highlights posts that are trending globally or within a user's communities.
- **Hybrid Approach:** Combines multiple algorithms to balance personalization and discovery.

### Data Flow
1. **User Activity Tracking:** All user interactions (views, likes, comments, shares, etc.) are tracked and stored.
2. **Preference Modeling:** User preferences are updated based on recent activity (hashtags, content types, communities, etc.).
3. **Recommendation Generation:**
    - Periodic background tasks generate and update recommendations for each user.
    - Recommendations are stored in the `ContentRecommendation` model, with a score and reason for each item.
4. **Serving Recommendations:**
    - The `/api/recommendations/` endpoint provides the current recommendations for a user, ordered by score.
    - Recommendations can be filtered by type (e.g., trending, similar users, hashtag-based).
5. **Feedback Loop:**
    - User feedback (like, dislike, not interested, etc.) is collected via the `RecommendationFeedback` model.
    - Feedback is used to refine future recommendations and improve algorithm accuracy.

### Example Recommendation Object
```json
{
  "user": "<user_id>",
  "content_type": "post",
  "object_id": "<post_id>",
  "score": 0.92,
  "recommendation_type": "hybrid",
  "reason": "Similar to posts you've liked and trending in your community.",
  "algorithm_version": "v1.0",
  "metadata": {"hashtags": ["#ai", "#news"]},
  "is_viewed": false,
  "is_clicked": false
}
```

### Improving Recommendations
- The system continuously learns from user actions and feedback.
- A/B testing is used to compare different algorithms and optimize engagement.
- Admins can manually trigger recommendation updates or adjust algorithm parameters.

---

## Signals & Automation
Signals are used to update engagement metrics, trigger notifications, and enforce moderation rules on content creation, update, and deletion.
Automated moderation and bot detection are triggered via signals and background tasks.
Content recommendation and A/B testing assignments are updated via signals on user/content activity.

## Background Tasks
- **Moderation:**
    - Auto-moderation of content using ML and rule-based systems.
    - Cleanup of expired moderation queue items and auto-moderation actions.
- **Bot Detection:**
    - Periodic analysis of user activity for bot detection.
    - Cleanup of old bot detection events.
- **Recommendation System:**
    - Generation of personalized content recommendations for users.
    - Calculation of content similarity scores.
    - Update of user content preferences based on recent activity.
- **A/B Testing:**
    - Assignment of users to experiments and groups.
    - Aggregation and analysis of experiment metrics/results.

## Test Documentation
### Test Files
- `tests.py`, `test_dislike.py`, `test.py` — Main and feature-specific test suites for the content app

### Running Tests
```sh
python manage.py test content
```

### Test Coverage
- CRUD operations for all main models (Post, Comment, Like, Dislike, Share, Media, etc.)
- Moderation and bot detection logic
- Recommendation and A/B testing workflows
- Signals and background task triggers

---


## Background Tasks (Celery)
The content app uses Celery for background processing of moderation, bot detection, recommendations, and A/B testing. Tasks are scheduled via **django-celery-beat** (database-driven scheduling) and can be managed through Django Admin at `/admin/django_celery_beat/`.

### Task Schedule Table

| Task Name                                 | Function Name                        | Schedule (crontab)         | Description |
|-------------------------------------------|--------------------------------------|----------------------------|-------------|
| auto-moderate-content                     | auto_moderate_content                | Every 10 minutes           | Auto-moderation of content using ML and rule-based systems |
| cleanup-expired-moderation-queue-items    | cleanup_expired_moderation_queue_items| Daily at 01:00            | Cleanup of expired moderation queue items |
| cleanup-auto-moderation-actions           | cleanup_auto_moderation_actions      | Daily at 01:30             | Cleanup of expired auto-moderation actions |
| analyze-bot-detection-events              | analyze_bot_detection_events         | Every 30 minutes           | Periodic analysis of user activity for bot detection |
| cleanup-old-bot-detection-events          | cleanup_old_bot_detection_events     | Daily at 02:00             | Cleanup of old bot detection events |
| generate-content-recommendations          | generate_content_recommendations     | Every 20 minutes           | Generation of personalized content recommendations for users |
| calculate-content-similarity-scores       | calculate_content_similarity_scores  | Every hour                 | Calculation of content similarity scores |
| update-user-content-preferences           | update_user_content_preferences      | Every hour                 | Update of user content preferences based on recent activity |
| assign-ab-experiment-groups               | assign_ab_experiment_groups          | Every 2 hours              | Assignment of users to A/B experiment groups |
| aggregate-ab-experiment-metrics           | aggregate_ab_experiment_metrics      | Every 2 hours              | Aggregation and analysis of experiment metrics/results |

---

## Detailed Task Descriptions

### 1. auto_moderate_content
**Schedule:** Every 10 minutes
**Purpose:** Auto-moderation of content using ML and rule-based systems.

### 2. cleanup_expired_moderation_queue_items
**Schedule:** Daily at 01:00
**Purpose:** Cleanup of expired moderation queue items.

### 3. cleanup_auto_moderation_actions
**Schedule:** Daily at 01:30
**Purpose:** Cleanup of expired auto-moderation actions.

### 4. analyze_bot_detection_events
**Schedule:** Every 30 minutes
**Purpose:** Periodic analysis of user activity for bot detection.

### 5. cleanup_old_bot_detection_events
**Schedule:** Daily at 02:00
**Purpose:** Cleanup of old bot detection events.

### 6. generate_content_recommendations
**Schedule:** Every 20 minutes
**Purpose:** Generation of personalized content recommendations for users.

### 7. calculate_content_similarity_scores
**Schedule:** Every hour
**Purpose:** Calculation of content similarity scores.

### 8. update_user_content_preferences
**Schedule:** Every hour
**Purpose:** Update of user content preferences based on recent activity.

### 9. assign_ab_experiment_groups
**Schedule:** Every 2 hours
**Purpose:** Assignment of users to A/B experiment groups.

### 10. aggregate_ab_experiment_metrics
**Schedule:** Every 2 hours
**Purpose:** Aggregation and analysis of experiment metrics/results.


## Permissions & Security
- Most endpoints require authentication.
- Some endpoints allow read-only access for unauthenticated users (e.g., public posts).
- Role-based and object-level permissions enforced for create/update/delete.

---

## See Also
- [Project main README](../README.md)
