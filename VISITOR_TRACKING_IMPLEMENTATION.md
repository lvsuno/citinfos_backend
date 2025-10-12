# Community Visitor Tracking Implementation Summary

## Overview
Transitioned from tracking community **members** (join/leave) to tracking **visitors** (both authenticated and anonymous) with real-time division analytics.

---

## ✅ Completed Changes

### 1. **UserEvent Model Updates** (`accounts/models.py`)

**Removed (commented out):**
- `community_join` - Users no longer join communities
- `community_leave` - No leave events
- `community_invitation_create` - No invitation system
- `community_invitation_accept` - No invitation system
- `community_invitation_decline` - No invitation system

**Added:**
- `community_visit` - Tracks when users visit a community page

**Event Metadata Structure:**
```python
{
    'community_id': 'uuid',
    'community_slug': 'community-name',
    'visitor_division_id': 'visitor-home-division-id',
    'community_division_id': 'community-division-id',
    'is_cross_division': True/False,
    'is_authenticated': True/False,  # NEW: Track auth status
    'url': '/communities/slug/',
    'referrer': 'previous-url'
}
```

---

### 2. **Redis Visitor Tracker** (`communities/visitor_tracker.py`)

**New Class: `CommunityVisitorTracker`**

Tracks both **authenticated** and **anonymous** visitors:

**Redis Keys Structure:**
```
community:{id}:visitors                       # Hash: visitor_key -> visitor_data JSON
community:{id}:visitors:authenticated         # Set: authenticated visitor keys
community:{id}:visitors:anonymous            # Set: anonymous visitor keys (session IDs)
community:{id}:visitors:by_division          # Hash: division_id -> count
community:{id}:cross_division_visits         # Sorted Set: "divA→divB" -> count
community:{id}:peak:visitors:{period}        # Peak counts (daily/weekly/monthly)
user:{id}:visiting_communities               # Set of community IDs (authenticated only)
visitor:{key}:community:{id}:activity        # Last activity timestamp
```

**Visitor Data Structure (stored as JSON in hash):**
```json
{
    "user_id": "uuid",              // null for anonymous
    "session_id": "session-key",    // for all visitors
    "is_authenticated": true,       // NEW: Auth status
    "joined_at": "2025-10-10T10:30:00Z",
    "division_id": "division-uuid",
    "pages_viewed": 5,
    "last_activity": "2025-10-10T10:35:00Z"
}
```

**Visitor Key:**
- Authenticated: `user_id` (UUID)
- Anonymous: `session_id` (session key)

**Updated Methods:**

1. **`add_visitor(user_id, community_id, visitor_division_id, community_division_id, is_authenticated, session_id)`**
   - Now accepts `is_authenticated` flag and `session_id`
   - Tracks authenticated visitors in separate Redis set
   - Tracks anonymous visitors in separate Redis set
   - Uses session_id for anonymous visitor identification
   - Returns: `{current_count, is_cross_division, timestamp}`

2. **`get_authenticated_visitor_count(community_id)`** ✨ NEW
   - Returns count of authenticated visitors only

3. **`get_anonymous_visitor_count(community_id)`** ✨ NEW
   - Returns count of anonymous visitors only

4. **`get_visitor_stats(community_id)`** ✨ NEW
   - Returns:
     ```python
     {
         'total_visitors': 42,
         'authenticated_visitors': 28,
         'anonymous_visitors': 14,
         'authenticated_percentage': 66.67,
         'anonymous_percentage': 33.33
     }
     ```

2. **`remove_visitor(user_id, community_id)`**
   - Removes visitor from hash
   - Decrements division count
   - Cleans up tracking keys

3. **`update_visitor_activity(user_id, community_id, increment_pages=True)`**
   - Updates last_activity timestamp
   - Increments pages_viewed counter
   - Refreshes Redis TTL (5 minutes)

4. **`get_visitor_list(community_id)`**
   - Returns list of current visitors with full details
   - Sorted by last_activity (most recent first)

5. **`get_division_breakdown(community_id)`**
   - Returns: `{division_id: visitor_count, ...}`

6. **`get_cross_division_stats(community_id)`**
   - Returns:
     ```python
     {
         'total_visitors': 42,
         'cross_division_visits': 18,
         'cross_division_percentage': 42.86,
         'breakdown': [
             {'from_division': 'A', 'to_division': 'B', 'count': 10},
             {'from_division': 'C', 'to_division': 'B', 'count': 8},
             ...
         ]
     }
     ```

7. **`is_user_visiting(user_id, community_id)`**
   - Check if user is currently visiting

8. **`get_peak_counts(community_id)`**
   - Returns: `{'daily': 50, 'weekly': 120, 'monthly': 300}`

9. **`cleanup_stale_visitors(community_id)`**
   - Removes visitors inactive for >5 minutes

---

### 3. **Analytics Middleware** (`analytics/middleware.py`)

**Updated `_track_page_view(request, response, user_profile)`:**
- ✅ Now tracks **both authenticated and anonymous** visitors
- ✅ Detects community pages for all visitors
- ✅ Creates sessions for anonymous users if needed
- ✅ Calls `_track_community_visit()` with auth status

**Flow for Authenticated Users:**
```
Request → _track_page_view()
       → _extract_community_context()
       → _track_community_visit(is_authenticated=True)
       → visitor_tracker.add_visitor(is_authenticated=True)
       → UserEvent.objects.create()
       → Redis updated with authenticated visitor
```

**Flow for Anonymous Users:**
```
Request → _track_page_view()
       → _extract_community_context()
       → _track_community_visit(is_authenticated=False)
       → Create session if needed
       → visitor_tracker.add_visitor(is_authenticated=False, session_id=...)
       → Redis updated with anonymous visitor
       → No UserEvent created (anonymous)
```

**Updated Method: `_track_community_visit(request, user_profile, community_data, is_authenticated)`**

**For Authenticated Users:**
- Gets visitor's home division from `user_profile.division`
- Uses `user_id` as visitor key
- Calls `visitor_tracker.add_visitor()` with `is_authenticated=True`
- Creates `UserEvent` with `event_type='community_visit'`
- Stores division metadata and auth status

**For Anonymous Users:**
- Gets or creates session ID
- Uses `session_id` as visitor key
- Calls `visitor_tracker.add_visitor()` with `is_authenticated=False`
- Logs visit (no UserEvent created)
- Can optionally detect division from IP geolocation

**Session Management:**
```python
session_id = request.session.session_key
if not session_id:
    request.session.create()
    session_id = request.session.session_key
```

---

## 📊 What Gets Tracked

### For Each Community Visit:

1. **Real-time visitor count** (Total: authenticated + anonymous)
2. **Authenticated visitor count** (logged-in users)
3. **Anonymous visitor count** (session-based tracking)
4. **Visitor details**:
   - User ID (authenticated only)
   - Session ID (all visitors)
   - Authentication status
   - Home division
   - Join time
   - Pages viewed
   - Last activity
5. **Division breakdown**: How many visitors from each division
6. **Cross-division visits**:
   - Count of users from division A visiting division B
   - Percentage of cross-division visitors
   - Top cross-division pairs
7. **Peak visitor counts**: Daily, weekly, monthly peaks
8. **UserEvent history**: Permanent record of authenticated visits only

### Example Data Flow:

**Authenticated User from "Montreal" visits "Quebec City" community:**
```python
# Redis gets:
community:quebec-city-uuid:visitors = {
    'user-123-uuid': {
        'user_id': 'user-123-uuid',
        'session_id': 'abc123session',
        'is_authenticated': True,
        'division_id': 'montreal-uuid',
        'joined_at': '2025-10-10T10:30:00Z',
        'pages_viewed': 1,
        'last_activity': '2025-10-10T10:30:00Z'
    }
}

community:quebec-city-uuid:visitors:authenticated = {'user-123-uuid'}
community:quebec-city-uuid:visitors:by_division = {'montreal-uuid': 1}
community:quebec-city-uuid:cross_division_visits = {
    'montreal-uuid→quebec-city-uuid': 1.0
}

# Database gets UserEvent:
{
    'event_type': 'community_visit',
    'user': user_profile,
    'metadata': {
        'community_id': 'quebec-city-uuid',
        'visitor_division_id': 'montreal-uuid',
        'community_division_id': 'quebec-city-uuid',
        'is_cross_division': True,
        'is_authenticated': True,
        ...
    }
}
```

**Anonymous User visits "Quebec City" community:**
```python
# Redis gets:
community:quebec-city-uuid:visitors = {
    'abc123session': {
        'user_id': None,
        'session_id': 'abc123session',
        'is_authenticated': False,
        'division_id': None,  # or from IP geolocation
        'joined_at': '2025-10-10T10:32:00Z',
        'pages_viewed': 1,
        'last_activity': '2025-10-10T10:32:00Z'
    }
}

community:quebec-city-uuid:visitors:anonymous = {'abc123session'}

# No UserEvent created for anonymous visitors
# Only logged in server logs
```

---

## 🔄 Pending Tasks

### 5. **Update CommunityRedisService** (`communities/services.py`)
- Replace `get_online_members()` with `get_current_visitors()`
- Update method signatures to use visitor_tracker
- Keep backward compatibility where needed

### 6. **Create Visitor Utility Functions** (`communities/utils/visitor_utils.py`)
- High-level wrapper functions
- Database query helpers
- Analytics aggregations

### 7. **Update API Endpoints** (`communities/views.py`)
- Replace `@action online_members()` with `@action current_visitors()`
- Add `@action visitor_stats()` for division analytics

### 8. **Update Sync Task** (`communities/tasks.py`)
- Modify `sync_community_with_analytics()` to use visitor data
- Update Community model fields if needed

### 9. **WebSocket Updates** (`communities/consumers.py`)
- Broadcast `visitor_count_changed` events
- Broadcast `visitor_divisions_updated` events

### 10-11. **Frontend Components**
- Create React hooks for visitor tracking
- Create UI components showing visitor stats

### 12. **Tests**
- Test Redis operations
- Test division tracking
- Test cross-division analytics
- Test API endpoints
- Test WebSocket events

---

## 🎯 Key Benefits

1. **No Member System**: Users don't join/leave, they just visit
2. **Anonymous Visitor Tracking**: Track non-authenticated visitors via sessions
3. **Authenticated/Anonymous Split**: See how many visitors are logged in
4. **Division Analytics**: Track where visitors are from
5. **Cross-Division Insights**: Understand inter-division traffic
6. **Real-time Counts**: Live visitor numbers via Redis
7. **Historical Data**: UserEvents provide permanent visit history (auth only)
8. **Performance**: Redis caching for fast queries
9. **Auto-cleanup**: Stale visitors removed after 5 minutes
10. **Peak Tracking**: Know busy times for each community
11. **Privacy-Friendly**: Anonymous users tracked by session only

---

## 🗄️ Database Schema Impact

**No migrations needed** - Only Redis changes and new UserEvent type.

**Existing models unchanged**:
- Community model still has division FK
- UserProfile still has division FK
- UserEvent just uses new event_type

---

## 🚀 Usage Examples

### Backend - Track an authenticated visitor:
```python
from communities.visitor_tracker import visitor_tracker

# When authenticated user visits community page
result = visitor_tracker.add_visitor(
    user_id=str(user.profile.id),
    community_id=str(community.id),
    visitor_division_id=str(user.profile.division.id),
    community_division_id=str(community.division.id),
    is_authenticated=True,
    session_id=request.session.session_key
)

# Returns:
# {
#     'current_count': 42,
#     'is_cross_division': True,
#     'visitor_division': 'montreal-uuid',
#     'community_division': 'quebec-uuid',
#     'timestamp': '2025-10-10T10:30:00Z'
# }
```

### Backend - Track an anonymous visitor:
```python
# When anonymous user visits community page
result = visitor_tracker.add_visitor(
    user_id=f"anonymous_{request.session.session_key}",
    community_id=str(community.id),
    visitor_division_id=None,  # or from IP geolocation
    community_division_id=str(community.division.id),
    is_authenticated=False,
    session_id=request.session.session_key
)
```

### Get visitor stats with auth breakdown:
```python
# Get comprehensive visitor statistics
stats = visitor_tracker.get_visitor_stats(community_id)
# {
#     'total_visitors': 42,
#     'authenticated_visitors': 28,
#     'anonymous_visitors': 14,
#     'authenticated_percentage': 66.67,
#     'anonymous_percentage': 33.33
# }

# Get just authenticated count
auth_count = visitor_tracker.get_authenticated_visitor_count(community_id)
# 28

# Get just anonymous count
anon_count = visitor_tracker.get_anonymous_visitor_count(community_id)
# 14

# Current visitors list (includes auth status)
visitors = visitor_tracker.get_visitor_list(community_id)
# [
#     {
#         'user_id': 'uuid',
#         'session_id': 'abc123',
#         'is_authenticated': True,
#         'division_id': 'montreal',
#         'pages_viewed': 5,
#         ...
#     },
#     {
#         'user_id': None,
#         'session_id': 'xyz789',
#         'is_authenticated': False,
#         'division_id': None,
#         'pages_viewed': 2,
#         ...
#     }
# ]

# Division breakdown
divisions = visitor_tracker.get_division_breakdown(community_id)
# {'montreal-uuid': 15, 'laval-uuid': 8, 'gatineau-uuid': 5}

# Cross-division stats
cross_stats = visitor_tracker.get_cross_division_stats(community_id)
# {
#     'total_visitors': 28,
#     'cross_division_visits': 12,
#     'cross_division_percentage': 42.86,
#     'breakdown': [...]
# }

# Peak counts
peaks = visitor_tracker.get_peak_counts(community_id)
# {'daily': 50, 'weekly': 150, 'monthly': 400}
```

### Clean up stale visitors:
```python
# Remove visitors inactive >5 minutes
removed = visitor_tracker.cleanup_stale_visitors(community_id)
```

---

## 📝 Notes

- **TTL**: Visitors expire after 5 minutes of inactivity
- **Auto-tracking**: Middleware tracks all community page GETs
- **Backward Compatibility**: Old event types commented out, not deleted
- **Division Optional**: Handles cases where division is None
- **Error Handling**: All methods catch exceptions and log errors
- **Performance**: Redis operations are O(1) or O(log N)
- **Real-time**: WebSocket can broadcast changes immediately

---

## 🔍 Testing Locally

1. **Test Authenticated Visitor:**
   - Log in and visit a community page
   - Check Redis:
     ```bash
     docker-compose exec redis redis-cli
     > HGETALL community:{uuid}:visitors
     > SMEMBERS community:{uuid}:visitors:authenticated
     > HGETALL community:{uuid}:visitors:by_division
     > ZRANGE community:{uuid}:cross_division_visits 0 -1 WITHSCORES
     ```
   - Check UserEvent table:
     ```python
     UserEvent.objects.filter(
         event_type='community_visit',
         metadata__is_authenticated=True
     ).latest('timestamp')
     ```

2. **Test Anonymous Visitor:**
   - Log out and visit a community page
   - Check Redis:
     ```bash
     docker-compose exec redis redis-cli
     > HGETALL community:{uuid}:visitors
     > SMEMBERS community:{uuid}:visitors:anonymous
     ```
   - Verify no UserEvent created for anonymous visits

3. **Test Visitor Stats:**
   ```python
   from communities.visitor_tracker import visitor_tracker

   # Get breakdown
   stats = visitor_tracker.get_visitor_stats(community_id)
   print(stats)
   # {
   #     'total_visitors': 10,
   #     'authenticated_visitors': 7,
   #     'anonymous_visitors': 3,
   #     'authenticated_percentage': 70.0,
   #     'anonymous_percentage': 30.0
   # }
   ```

---

**Status**: Core implementation complete with anonymous visitor support ✅
**Next**: Update services, views, and WebSocket consumers to expose auth/anon stats
