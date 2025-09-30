# Polls App Documentation

## Overview
The `polls` app enables creation, management, and analytics of polls attached to posts. It supports multiple polls per post, multiple choice voting, anonymous voting, poll options, and advanced analytics for engagement and performance.

## Key Features
- ✅ **Multiple Polls per Post**: Each post can have unlimited polls attached
- ✅ **Flexible Poll Options**: Multiple choice, anonymous voting, expiration dates
- ✅ **Poll Management**: Create, update, close polls with comprehensive options
- ✅ **Vote Tracking**: Track votes with user analytics and engagement metrics
- ✅ **Order Management**: Polls can be ordered within a post for better UX

## Models

### Core Models
- **Poll**: Main poll model with ForeignKey to Post (allowing multiple polls per post)
- **PollOption**: Individual options within a poll
- **PollVote**: Individual vote records linking users to poll options
- **PollVoter**: Track unique voters per poll for analytics

### Enhanced Relationships
- **Post → Polls**: One-to-Many relationship (ForeignKey on Poll model)
- **Poll → Options**: One-to-Many relationship for poll choices
- **Poll → Votes**: One-to-Many relationship for vote tracking
- **Poll → Voters**: Many-to-Many through PollVoter for analytics

---


## API Endpoints (CRUD Details)
All endpoints are prefixed with `/api/`.

### Polls
| Method | Endpoint           | Description                       |
|--------|--------------------|-----------------------------------|
| GET    | /api/polls/        | List all polls                    |
| POST   | /api/polls/        | Create a new poll                 |
| GET    | /api/polls/{id}/   | Retrieve a specific poll          |
| PUT    | /api/polls/{id}/   | Update a poll (full update)       |
| PATCH  | /api/polls/{id}/   | Update a poll (partial update)    |
| DELETE | /api/polls/{id}/   | Delete a poll                     |

### Poll Options
| Method | Endpoint                  | Description                       |
|--------|---------------------------|-----------------------------------|
| GET    | /api/poll-options/        | List all poll options             |
| POST   | /api/poll-options/        | Create a new poll option          |
| GET    | /api/poll-options/{id}/   | Retrieve a specific poll option   |
| PUT    | /api/poll-options/{id}/   | Update a poll option (full)       |
| PATCH  | /api/poll-options/{id}/   | Update a poll option (partial)    |
| DELETE | /api/poll-options/{id}/   | Delete a poll option              |

### Poll Votes
| Method | Endpoint                | Description                       |
|--------|-------------------------|-----------------------------------|
| GET    | /api/poll-votes/        | List all poll votes               |
| POST   | /api/poll-votes/        | Create a new poll vote            |
| GET    | /api/poll-votes/{id}/   | Retrieve a specific poll vote     |
| DELETE | /api/poll-votes/{id}/   | Delete a poll vote                |

### Poll Voters
| Method | Endpoint                | Description                       |
|--------|-------------------------|-----------------------------------|
| GET    | /api/poll-voters/       | List all poll voters              |
| POST   | /api/poll-voters/       | Add a poll voter                  |
| GET    | /api/poll-voters/{id}/  | Retrieve a specific poll voter    |
| DELETE | /api/poll-voters/{id}/  | Remove a poll voter               |

**Notes:**
- All endpoints require authentication unless otherwise specified.
- List endpoints support filtering, searching, and pagination.
- Poll creation can be linked to a post; poll options must be associated with a poll.
- Voting is restricted to one vote per user per poll unless multiple choice is enabled.

---

## Main ViewSets and Functions
- **PollViewSet**: CRUD for polls, attach to posts, close/expire polls
- **PollOptionViewSet**: CRUD for poll options
- **PollVoteViewSet**: CRUD for poll votes
- **PollVoterViewSet**: Track unique voters per poll

---

## Models (Key Fields)
- **Poll**: id, post, question, multiple_choice, anonymous_voting, expires_at, total_votes, voters_count, is_active, is_closed, order, created_at, updated_at
- **PollOption**: id, poll, text, order, votes_count, image, created_at
- **PollVote**: id, poll, option, voter, ip_address, user_agent, created_at
- **PollVoter**: id, poll, voter, voted_at

---


## Example Usage

### Create a poll for a specific post
```http
POST /api/polls/
Content-Type: application/json
{
  "post": "<post_id>",
  "question": "What's your favorite color?",
  "multiple_choice": false,
  "anonymous_voting": true,
  "expires_at": "2025-08-01T12:00:00Z",
  "order": 1
}
```

### Create multiple polls for one post
```http
POST /api/polls/
Content-Type: application/json
{
  "post": "<post_id>",
  "question": "First poll: What's your favorite color?",
  "order": 1
}

POST /api/polls/
Content-Type: application/json
{
  "post": "<post_id>",
  "question": "Second poll: What's your favorite animal?",
  "order": 2
}
```

### List all polls
```http
GET /api/polls/
```

### Retrieve a poll
```http
GET /api/polls/{poll_id}/
```

### Update a poll
```http
PATCH /api/polls/{poll_id}/
Content-Type: application/json
{
  "question": "What's your favorite animal?"
}
```

### Delete a poll
```http
DELETE /api/polls/{poll_id}/
```

### Add a poll option
```http
POST /api/poll-options/
Content-Type: application/json
{
  "poll": "<poll_id>",
  "text": "Blue",
  "order": 1
}
```

### Vote on a poll
```http
POST /api/poll-votes/
Content-Type: application/json
{
  "poll": "<poll_id>",
  "option": "<option_id>"
}
```

### List poll votes
```http
GET /api/poll-votes/?poll=<poll_id>
```

### List poll voters
```http
GET /api/poll-voters/?poll=<poll_id>
```

---

## Signals & Automation
- Poll status and metrics are updated via signals (e.g., on vote, option added, poll expired).
- Signals may trigger notifications for poll expiration, new votes, or analytics updates.

## Background Tasks (Celery)
The polls app uses Celery for background processing and automation. Tasks are scheduled using the **django-celery-beat** database scheduler, allowing dynamic management through the Django admin interface at `/admin/django_celery_beat/`.

### Task Schedule Table
| Task Name                        | Function Name                        | Schedule (crontab)         | Description |
|----------------------------------|--------------------------------------|----------------------------|-------------|
| handle-poll-expiration           | handle_poll_expiration               | Every 10 minutes           | Handle expired polls and close them |
| update-poll-counters             | update_poll_counters                 | Every 5 minutes            | Update vote counts for poll options |
| analyze-poll-engagement          | analyze_poll_engagement              | 05:30 daily                | Analyze poll engagement metrics |
| generate-poll-analytics          | generate_poll_analytics              | 01:30 daily                | Generate analytics for polls |
| analyze-poll-option-performance  | analyze_poll_option_performance      | 02:30 daily                | Analyze performance of poll options |
| cleanup-empty-poll-options       | cleanup_empty_poll_options           | 03:00 daily                | Clean up poll options with no votes |
| reorder-poll-options-by-popularity| reorder_poll_options_by_popularity   | 04:00 daily                | Reorder poll options by popularity |
| generate-poll-option-insights    | generate_poll_option_insights        | 05:00 daily                | Generate insights for poll options |

---

## Detailed Task Descriptions

### 1. handle_poll_expiration
**Schedule:** Every 10 minutes
**Purpose:** Handles expired polls, closes them, and logs or notifies as needed.

---

### 2. update_poll_counters
**Schedule:** Every 5 minutes
**Purpose:** Updates vote counts and unique voter counts for active polls.

---

### 3. analyze_poll_engagement
**Schedule:** 05:30 daily
**Purpose:** Analyzes poll engagement metrics for reporting and recommendations.

---

### 4. generate_poll_analytics
**Schedule:** 01:30 daily
**Purpose:** Generates analytics for polls, including participation and trends.

---

### 5. analyze_poll_option_performance
**Schedule:** 02:30 daily
**Purpose:** Analyzes the performance of poll options for insights and optimization.

---

### 6. cleanup_empty_poll_options
**Schedule:** 03:00 daily
**Purpose:** Cleans up poll options that have no votes to keep data relevant.

---

### 7. reorder_poll_options_by_popularity
**Schedule:** 04:00 daily
**Purpose:** Reorders poll options based on popularity for better UX and analytics.

---

### 8. generate_poll_option_insights
**Schedule:** 05:00 daily
**Purpose:** Generates insights for poll options, such as trends and recommendations.

---

## Utilities
- **calculate_poll_engagement_score**: Calculates engagement score for a poll based on votes, comments, shares, and time.

---

## Tests
- `tests.py` — Comprehensive test suite for poll models, API endpoints, background tasks, and analytics.
- Run with:
  ```sh
  python manage.py test polls
  ```

---

## Permissions & Security
- All endpoints require authentication.
- Users can only vote once per poll (unless multiple choice is enabled).
- Poll results and voter identities are handled according to poll settings (anonymous or public).

---
