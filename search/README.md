# Search App Documentation

## Overview
The `search` app tracks and analyzes user search queries across the platform. It supports storing, filtering, and analyzing searches by type (post, user, equipment, community, message, poll, etc.), and provides endpoints for recent and popular searches, as well as background analytics and caching.

---

## API Endpoints (CRUD Details)
All endpoints are prefixed with `/api/`.

### User Search Queries
| Method | Endpoint                        | Description                                 |
|--------|----------------------------------|---------------------------------------------|
| GET    | /api/user-search-queries/       | List all search queries for the user        |
| POST   | /api/user-search-queries/       | Create a new search query                   |
| GET    | /api/user-search-queries/{id}/  | Retrieve a specific search query            |
| PATCH  | /api/user-search-queries/{id}/  | Update a search query (partial)             |
| DELETE | /api/user-search-queries/{id}/  | Soft-delete a search query                  |
| GET    | /api/user-search-queries/cached-recent/ | Get cached recent searches for user/type |

**Notes:**
- All endpoints require authentication.
- List endpoints support filtering by `search_type`, searching, and pagination.
- Soft delete is used for removing queries (not permanent).

---

## Main ViewSets and Functions
- **UserSearchQueryViewSet**: CRUD for user search queries, filter by type, cached recent searches
- **ParseAddressView**: Parse and extract address components from a string (for advanced search)

---

## Models (Key Fields)
- **UserSearchQuery**: user, query, search_type (post/user/equipment/community/message/poll/other), filters, results_count, created_at, is_deleted

---

## Example Usage
**Create a search query:**
```http
POST /api/user-search-queries/
Content-Type: application/json
{
  "query": "django celery",
  "search_type": "post",
  "filters": {"tag": "python"},
  "results_count": 12
}
```

**List recent search queries:**
```http
GET /api/user-search-queries/?search_type=post
```

**Get cached recent searches:**
```http
GET /api/user-search-queries/cached-recent/?search_type=post&limit=5
```

---

## Signals & Automation
- Search queries are tracked automatically when users perform searches.
- Signals may trigger analytics updates or cache refreshes.

## Background Tasks (Celery)
The search app uses Celery for background processing and analytics. Tasks are scheduled using the **django-celery-beat** database scheduler, allowing dynamic management through the Django admin interface at `/admin/django_celery_beat/`.

### Task Schedule Table
| Task Name                        | Function Name                        | Schedule (crontab)         | Description |
|----------------------------------|--------------------------------------|----------------------------|-------------|
| cache-all-users-recent-searches  | cache_all_users_recent_searches      | Every 10 minutes           | Cache recent searches for all users/types |
| analyze-search-queries           | analyze_search_queries               | Every 30 minutes           | Analyze and rank popular search queries |
| count-search-queries-by-type     | count_search_queries_by_type         | 00:00 daily                | Count search queries by type            |

---

## Detailed Task Descriptions

### 1. cache_all_users_recent_searches
**Schedule:** Every 10 minutes
**Purpose:** Caches recent search queries for all users and types in Redis for fast retrieval.

---

### 2. analyze_search_queries
**Schedule:** Every 30 minutes
**Purpose:** Analyzes and ranks the most popular search queries across the platform.

---

### 3. count_search_queries_by_type
**Schedule:** 00:00 daily
**Purpose:** Counts the number of search queries by type for analytics and reporting.

---

## Utilities
- **cache_popular_searches**: Caches popular search queries in Redis.
- **get_popular_searches**: Retrieves cached popular search queries from Redis.

---

## Tests
- `tests.py` — Comprehensive test suite for search query models, API endpoints, background tasks, and analytics.
- Run with:
  ```sh
  python manage.py test search
  ```

---

## Permissions & Security
- All endpoints require authentication.
- Users can only access their own search queries.
- Search data is handled securely and used for analytics and recommendations only.

---
