# Analytics App Documentation 📊

## Overview
The `analytics` app tracks system, user, content, and community metrics, providing daily, user-specific, and system-wide analytics, as well as error logging and geo-restriction tracking. It supports monitoring, reporting, and troubleshooting for the platform with real-time community analytics and location-based access analytics.

## ✅ **Current Implementation Status (December 2025)**

### **Analytics System** - **FULLY OPERATIONAL**
- **Real-time Metrics**: Live tracking of user activity, content engagement, and community member counts
- **Community Analytics**: Advanced community engagement tracking with online member monitoring
- **Geo-Restriction Analytics**: Location-based access tracking and restriction effectiveness analysis
- **User Analytics**: Comprehensive user behavior analysis with activity tracking integration
- **System Monitoring**: Complete system health and performance metrics
- **Error Tracking**: Advanced error logging with categorization and analysis
- **Activity Integration**: Seamless integration with user activity middleware and JWT authentication
- **Background Processing**: Scheduled analytics tasks for data aggregation and reporting

## Key Features
- ✅ **Daily Analytics**: Automated daily metrics collection and reporting
- ✅ **Real-time Community Analytics**: Live online member tracking with Redis backend
- ✅ **Geo-Restriction Analytics**: Location-based access patterns and restriction effectiveness
- ✅ **User Analytics**: Individual user behavior tracking and analysis
- ✅ **System Analytics**: Platform-wide metrics and performance monitoring
- ✅ **Error Logging**: Comprehensive error tracking with categorization
- ✅ **Real-time Tracking**: Live activity monitoring with middleware integration
- ✅ **Background Tasks**: Scheduled Celery tasks for analytics processing
- ✅ **Authentication Integration**: Full JWT + Session analytics tracking
- ✅ **Performance Metrics**: System performance and resource utilization tracking

---

## 📊 **Real-time Community Analytics** - **NEW FEATURE**

### **Live Member Tracking**
Advanced real-time analytics for community engagement:

#### **Features**
- **Online Member Count**: Real-time tracking of active community members
- **Activity Patterns**: Hourly, daily, and weekly activity analytics
- **Peak Hours Analysis**: Identification of community engagement peaks
- **Member Retention**: Tracking of member activity and retention rates

#### **Implementation**
```python
# Real-time analytics tracking
def track_community_analytics(community_id, user_id, activity_type):
    redis_client.hincrby(f'community_analytics:{community_id}', activity_type, 1)
    redis_client.setex(f'member_activity:{community_id}:{user_id}', 300, activity_type)

# Analytics retrieval
def get_community_analytics(community_id):
    return {
        'online_members': get_online_members_count(community_id),
        'hourly_activity': get_hourly_activity_pattern(community_id),
        'engagement_metrics': get_engagement_metrics(community_id)
    }
```

---

## 🌍 **Geo-Restriction Analytics** - **NEW FEATURE**

### **Location-Based Access Tracking**
Comprehensive analytics for geo-restriction effectiveness:

#### **Metrics Tracked**
- **Access Attempts**: Total attempts to access restricted communities
- **Blocked Attempts**: Number of blocked access attempts by location
- **Allowed Access**: Successful access from allowed locations
- **Travel Patterns**: Users accessing from different locations than registration
- **City-Level Analytics**: Detailed city and region access patterns

#### **Analytics Categories**
```python
# Geo-restriction analytics categories
GEO_ANALYTICS_TYPES = [
    'country_blocked', 'country_allowed',
    'city_blocked', 'city_allowed',
    'region_blocked', 'region_allowed',
    'traveler_access', 'restriction_bypass'
]
```

---

## 📈 **Enhanced Analytics Models** - **NEW FEATURES**

### **DailyAnalytics Model** - **ENHANCED**
Enhanced daily analytics with community and geo-restriction tracking:
```python
class DailyAnalytics(models.Model):
    date = models.DateField(unique=True)
    # User metrics (existing)
    total_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    new_registrations = models.IntegerField(default=0)

    # Community metrics (NEW)
    community_views = models.IntegerField(default=0)
    community_joins = models.IntegerField(default=0)
    average_online_members = models.IntegerField(default=0)
    peak_community_activity = models.IntegerField(default=0)

    # Geo-restriction metrics (NEW)
    geo_access_attempts = models.IntegerField(default=0)
    geo_blocked_attempts = models.IntegerField(default=0)
    geo_allowed_access = models.IntegerField(default=0)
    traveler_access_count = models.IntegerField(default=0)

    # Content and system metrics (existing)
    content_views = models.IntegerField(default=0)
    content_interactions = models.IntegerField(default=0)
    api_requests = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
```

### **UserAnalytics Model** - **ENHANCED**
Enhanced user analytics with community and location tracking:
```python
class UserAnalytics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()

    # Basic activity metrics (existing)
    page_views = models.IntegerField(default=0)
    actions_performed = models.IntegerField(default=0)

    # Community activity metrics (NEW)
    communities_viewed = models.IntegerField(default=0)
    communities_joined = models.IntegerField(default=0)
    community_online_time = models.IntegerField(default=0)
    community_interactions = models.IntegerField(default=0)

    # Geo-restriction metrics (NEW)
    geo_restricted_attempts = models.IntegerField(default=0)
    locations_accessed_from = models.JSONField(default=list)
    travel_detected = models.BooleanField(default=False)
```

---

## 📊 **Real-time Analytics Processing** - **NEW FEATURES**

### **Community Analytics Functions**
```python
def track_community_member_activity(community_id, user_id, activity_type):
    """Track real-time community member activity"""
    key = f'community_analytics:{community_id}:activity'
    timestamp = timezone.now().timestamp()

    # Log activity with timestamp
    redis_client.zadd(key, {f'{user_id}:{activity_type}': timestamp})

    # Update daily counters
    date_key = f'daily_analytics:{timezone.now().date()}'
    redis_client.hincrby(date_key, f'{activity_type}_count', 1)

def generate_community_analytics_report(community_id, date_range=7):
    """Generate comprehensive community analytics report"""
    return {
        'community_id': community_id,
        'metrics': {
            'total_views': get_total_views(community_id),
            'unique_visitors': get_unique_visitors(community_id),
            'peak_online_members': get_peak_members(community_id),
            'activity_patterns': get_activity_patterns(community_id)
        }
    }
```

### **Geo-Restriction Analytics Functions**
```python
def track_geo_restriction_analytics(user_id, community_id, location_data, access_result):
    """Track geo-restriction analytics with detailed location data"""
    timestamp = timezone.now()

    # Store detailed analytics data
    attempt_data = {
        'user_id': user_id,
        'country': location_data.get('country', 'Unknown'),
        'city': location_data.get('city', 'Unknown'),
        'access_result': access_result,
        'is_traveler': location_data.get('is_traveler', False),
        'timestamp': timestamp.isoformat()
    }

    # Store in Redis for real-time analytics
    analytics_key = f'geo_analytics:{community_id}:{timestamp.date()}'
    redis_client.lpush(analytics_key, json.dumps(attempt_data))

    # Update counters
    counter_key = f'geo_counters:{community_id}:{timestamp.date()}'
    redis_client.hincrby(counter_key, f'{access_result}_count', 1)

def generate_geo_restriction_report(community_id, date_range=30):
    """Generate comprehensive geo-restriction effectiveness report"""
    return {
        'community_id': community_id,
        'restriction_effectiveness': {
            'total_attempts': get_total_attempts(community_id),
            'blocked_attempts': get_blocked_attempts(community_id),
            'effectiveness_percentage': calculate_effectiveness(community_id)
        },
        'location_breakdown': get_location_analytics(community_id),
        'trends': get_geo_restriction_trends(community_id)
    }
```

---

All endpoints are prefixed with `/api/`.

### Daily Analytics (`daily/`)
| Method | Endpoint                | Description                |
|--------|-------------------------|----------------------------|
| GET    | /api/daily/             | List all daily analytics   |
| POST   | /api/daily/             | Create daily analytics     |
| GET    | /api/daily/{id}/        | Retrieve daily analytics   |
| PUT    | /api/daily/{id}/        | Update daily analytics     |
| PATCH  | /api/daily/{id}/        | Partial update             |
| DELETE | /api/daily/{id}/        | Delete daily analytics     |

### User Analytics (`user-analytics/`)
| Method | Endpoint                | Description                |
|--------|-------------------------|----------------------------|
| GET    | /api/user-analytics/    | List all user analytics    |
| POST   | /api/user-analytics/    | Create user analytics      |
| GET    | /api/user-analytics/{id}/| Retrieve user analytics   |
| PUT    | /api/user-analytics/{id}/| Update user analytics     |
| PATCH  | /api/user-analytics/{id}/| Partial update            |
| DELETE | /api/user-analytics/{id}/| Delete user analytics     |

### System Metrics (`metrics/`)
| Method | Endpoint                | Description                |
|--------|-------------------------|----------------------------|
| GET    | /api/metrics/           | List all system metrics    |
| POST   | /api/metrics/           | Create system metric       |
| GET    | /api/metrics/{id}/      | Retrieve system metric     |
| PUT    | /api/metrics/{id}/      | Update system metric       |
| PATCH  | /api/metrics/{id}/      | Partial update             |
| DELETE | /api/metrics/{id}/      | Delete system metric       |

### Error Logs (`errors/`)
| Method | Endpoint                | Description                |
|--------|-------------------------|----------------------------|
| GET    | /api/errors/            | List all error logs        |
| POST   | /api/errors/            | Create error log           |
| GET    | /api/errors/{id}/       | Retrieve error log         |
| PUT    | /api/errors/{id}/       | Update error log           |
| PATCH  | /api/errors/{id}/       | Partial update             |
| DELETE | /api/errors/{id}/       | Delete error log           |

---

## Main ViewSets and Functions - **ENHANCED**
- **DailyAnalyticsViewSet**: CRUD for daily analytics with community and geo-restriction metrics
- **UserAnalyticsViewSet**: CRUD for user analytics with location and community tracking
- **CommunityAnalyticsViewSet**: Real-time community analytics and reporting *(NEW)*
- **GeoAnalyticsViewSet**: Geo-restriction analytics and effectiveness tracking *(NEW)*
- **SystemMetricViewSet**: CRUD for system metrics
- **ErrorLogViewSet**: CRUD for error logs

---

## Models (Detailed)

- **DailyAnalytics**: Aggregated daily metrics.
  - `date`, `new_users`, `active_users`, `total_users`
  - Content: `new_posts`, `new_comments`, `total_likes`, `total_shares`
  - Engagement: `total_interactions`, `avg_session_duration`, `bounce_rate`
  - System: `avg_response_time`, `error_count`
  - Timestamps: `created_at`

- **UserAnalytics**: Per-user analytics.
  - `user`, `total_posts`, `total_comments`, `total_likes_given`, `total_likes_received`
  - Social: `followers_gained`, `followers_lost`
  - Activity: `total_sessions`, `total_time_spent`, `avg_session_duration`
  - Recommendations: `recommendations_shown`, `recommendations_clicked`
  - Timestamps: `last_calculated`

- **SystemMetric**: System-wide performance metrics.
  - `metric_type`, `value`, `additional_data`, `recorded_at`

- **ErrorLog**: Error tracking and logging.
  - `user`, `level`, `message`, `stack_trace`, `url`, `method`, `ip_address`, `user_agent`, `extra_data`, `created_at`, `resolved_at`, `is_resolved`

---

## Example Usage - **ENHANCED**

**Get daily analytics:**
```http
GET /api/daily/
```

**Get real-time community analytics:** *(NEW)*
```http
GET /api/community-analytics/123/realtime/
Response: {
  "community_id": 123,
  "online_members": 45,
  "activity_score": 8.7,
  "peak_members_today": 67,
  "current_activity": "high"
}
```

**Get community analytics report:** *(NEW)*
```http
GET /api/community-analytics/123/report/?days=7
Response: {
  "community_id": 123,
  "date_range": {"start": "2024-12-01", "end": "2024-12-08"},
  "metrics": {
    "total_views": 1245,
    "unique_visitors": 289,
    "peak_online_members": 67,
    "average_session_duration": 12.5,
    "member_retention": 85.2
  }
}
```

**Get geo-restriction effectiveness:** *(NEW)*
```http
GET /api/geo-analytics/123/effectiveness/
Response: {
  "community_id": 123,
  "restriction_effectiveness": {
    "total_attempts": 450,
    "blocked_attempts": 127,
    "allowed_attempts": 323,
    "effectiveness_percentage": 28.2
  },
  "top_blocked_locations": [
    {"country": "Country A", "city": "City X", "attempts": 45},
    {"country": "Country B", "city": "City Y", "attempts": 32}
  ]
}
```

**Track community activity:** *(NEW)*
```http
POST /api/community-analytics/track/
{
  "community_id": 123,
  "user_id": 456,
  "activity_type": "view",
  "metadata": {"section": "posts", "duration": 120}
}
```

**Track geo-restriction attempt:** *(NEW)*
```http
POST /api/geo-analytics/track/
{
  "community_id": 123,
  "user_id": 456,
  "location": {
    "country": "United States",
    "city": "New York",
    "region": "New York"
  },
  "access_result": "allowed",
  "is_traveler": false
}
```

**Create a system metric:**
```http
POST /api/metrics/
{
  "metric_type": "cpu_usage",
  "value": 42.5
}
```

**Log an error:**
```http
POST /api/errors/
{
  "level": "error",
  "message": "Unhandled exception in view.",
  "stack_trace": "Traceback..."
}
```

---


## Background Tasks (Celery) - **ENHANCED**
The analytics app uses Celery for background processing of daily, user, system, community, and geo-restriction analytics, as well as error log management and reporting. Tasks are scheduled using the **django-celery-beat** database scheduler, allowing dynamic management through the Django admin interface at `/admin/django_celery_beat/`.

### Task Schedule Table - **UPDATED**

| Task Name                        | Function Name                        | Schedule (crontab)         | Description |
|----------------------------------|--------------------------------------|----------------------------|-------------|
| update-daily-analytics           | update_daily_analytics               | Every 30 minutes           | Aggregate and update daily analytics for the platform |
| update-user-analytics            | update_user_analytics                | Every hour                 | Update per-user analytics and engagement metrics |
| update-community-analytics       | update_community_analytics           | Every 15 minutes           | **NEW**: Update real-time community analytics and member tracking |
| process-geo-restriction-analytics| process_geo_restriction_analytics    | Every 20 minutes           | **NEW**: Process and analyze geo-restriction data |
| update-system-metrics            | update_system_metrics                | Every 15 minutes           | Collect and update system-wide performance metrics |
| cleanup-old-analytics            | cleanup_old_analytics                | Daily at 02:00             | Clean up old analytics records for performance |
| generate-analytics-reports       | generate_analytics_reports           | Daily at 03:00             | Generate and store analytics reports for admins |
| generate-community-reports       | generate_community_reports           | Daily at 03:30             | **NEW**: Generate detailed community analytics reports |
| generate-geo-effectiveness-reports| generate_geo_effectiveness_reports   | Daily at 04:00             | **NEW**: Generate geo-restriction effectiveness reports |
| process-error-logs               | process_error_logs                   | Every 10 minutes           | Process and aggregate error logs |
| cleanup-resolved-error-logs      | cleanup_resolved_error_logs          | Daily at 04:30             | Clean up resolved error logs from the database |
| cleanup-redis-analytics          | cleanup_redis_analytics              | Daily at 05:00             | **NEW**: Clean up old Redis analytics data |

---

## Detailed Task Descriptions - **ENHANCED**

### 1. update_daily_analytics
**Schedule:** Every 30 minutes
**Purpose:** Aggregates and updates daily analytics for the platform, including community and geo-restriction metrics.

### 2. update_user_analytics
**Schedule:** Every hour
**Purpose:** Updates per-user analytics, engagement metrics, and location tracking data.

### 3. **update_community_analytics** *(NEW)*
**Schedule:** Every 15 minutes
**Purpose:** Updates real-time community analytics including online member counts, activity patterns, and engagement metrics.

### 4. **process_geo_restriction_analytics** *(NEW)*
**Schedule:** Every 20 minutes
**Purpose:** Processes geo-restriction data to analyze effectiveness, location patterns, and traveler access behaviors.

### 5. update_system_metrics
**Schedule:** Every 15 minutes
**Purpose:** Collects and updates system-wide performance metrics.

### 6. cleanup_old_analytics
**Schedule:** Daily at 02:00
**Purpose:** Cleans up old analytics records to maintain database performance.

### 7. generate_analytics_reports
**Schedule:** Daily at 03:00
**Purpose:** Generates and stores comprehensive analytics reports for admins and stakeholders.

### 8. **generate_community_reports** *(NEW)*
**Schedule:** Daily at 03:30
**Purpose:** Generates detailed community analytics reports including member activity, peak hours, and engagement trends.

### 9. **generate_geo_effectiveness_reports** *(NEW)*
**Schedule:** Daily at 04:00
**Purpose:** Generates geo-restriction effectiveness reports showing blocked/allowed access patterns and location analytics.

### 10. process_error_logs
**Schedule:** Every 10 minutes
**Purpose:** Processes and aggregates error logs for monitoring and alerting.

### 11. cleanup_resolved_error_logs
**Schedule:** Daily at 04:30
**Purpose:** Cleans up resolved error logs from the database.

### 12. **cleanup_redis_analytics** *(NEW)*
**Schedule:** Daily at 05:00
**Purpose:** Cleans up old Redis analytics data including expired community activity and geo-restriction tracking data.

---

## Tests

### Test Files
- `tests.py` — Main test suite for analytics

### Running Tests
```sh
python manage.py test analytics
```

---

## Signals & Automation
- Daily and user analytics updated via Celery tasks
- System metrics and error logs recorded automatically

---

## Permissions & Security
- Most endpoints require authentication
- Error logs can be filtered by user

---

## See Also
- [Project main README](../README.md)
