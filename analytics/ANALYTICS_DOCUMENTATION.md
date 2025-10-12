# Visitor Analytics System Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Components](#components)
3. [API Endpoints](#api-endpoints)
4. [WebSocket Events](#websocket-events)
5. [Frontend Integration](#frontend-integration)
6. [Deployment Considerations](#deployment-considerations)
7. [Performance Optimization](#performance-optimization)
8. [Security](#security)

---

## Architecture Overview

The Visitor Analytics system tracks and analyzes visitor behavior across the platform, supporting both authenticated and anonymous users through device fingerprinting.

### High-Level Architecture

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
       ├─── HTTP/HTTPS ───┐
       │                  │
       └─── WebSocket ────┤
                          │
                    ┌─────▼──────┐
                    │   Nginx    │
                    │  (Reverse  │
                    │   Proxy)   │
                    └─────┬──────┘
                          │
            ┌─────────────┴──────────────┐
            │                            │
      ┌─────▼──────┐             ┌──────▼────────┐
      │  Daphne    │             │    Daphne     │
      │  (ASGI)    │             │   (ASGI)      │
      │  HTTP      │             │  WebSocket    │
      └─────┬──────┘             └──────┬────────┘
            │                            │
      ┌─────▼──────┐             ┌──────▼────────┐
      │   Django   │             │   Channels    │
      │   Views    │             │   Consumers   │
      └─────┬──────┘             └──────┬────────┘
            │                            │
            └────────────┬───────────────┘
                         │
              ┌──────────▼──────────┐
              │   Analytics Core    │
              │  VisitorAnalytics   │
              │  visitor_tracker    │
              └──────────┬──────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
      ┌─────▼──────┐           ┌─────▼─────┐
      │ PostgreSQL │           │   Redis   │
      │ (Storage)  │           │  (Cache)  │
      └────────────┘           └───────────┘
                                     │
                              ┌──────▼───────┐
                              │    Celery    │
                              │  (Async      │
                              │  Processing) │
                              └──────────────┘
```

### Data Flow

1. **Request Handling**:
   - All requests pass through `AnalyticsMiddleware`
   - Fingerprint is extracted or generated
   - Visitor tracking is queued in Celery

2. **Real-time Updates**:
   - Visitor count stored in Redis
   - WebSocket consumers broadcast changes
   - Connected clients receive instant updates

3. **Data Aggregation**:
   - Celery tasks aggregate data periodically
   - PageAnalytics updated daily
   - CommunityAnalytics updated per community

---

## Components

### 1. Models

#### AnonymousSession
Tracks anonymous user sessions using device fingerprinting.

```python
class AnonymousSession(models.Model):
    fingerprint = models.CharField(max_length=64, unique=True, db_index=True)
    session_id = models.CharField(max_length=64, blank=True, db_index=True)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    first_seen = models.DateTimeField(auto_now_add=True, db_index=True)
    last_seen = models.DateTimeField(auto_now=True, db_index=True)
    page_views = models.IntegerField(default=0)
    converted_at = models.DateTimeField(null=True, blank=True, db_index=True)
```

#### PageAnalytics
Aggregated daily statistics per page URL.

```python
class PageAnalytics(models.Model):
    date = models.DateField(db_index=True)
    page_url = models.CharField(max_length=500, db_index=True)
    unique_visitors = models.IntegerField(default=0)
    authenticated_visitors = models.IntegerField(default=0)
    anonymous_visitors = models.IntegerField(default=0)
    page_views = models.IntegerField(default=0)
```

#### CommunityAnalytics
Community-specific visitor statistics.

```python
class CommunityAnalytics(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    same_division_visitors = models.IntegerField(default=0)
    cross_division_visitors = models.IntegerField(default=0)
```

### 2. Middleware

#### AnalyticsMiddleware
- **Location**: `analytics/middleware.py`
- **Purpose**: Track all page views and visitor sessions
- **Features**:
  - Fingerprint generation and caching
  - Anonymous session tracking
  - Page view counting
  - Real-time visitor updates

**Configuration**:
```python
# settings.py
MIDDLEWARE = [
    # ... other middleware
    'analytics.middleware.AnalyticsMiddleware',
]
```

### 3. Utilities

#### VisitorAnalytics Class
- **Location**: `analytics/utils.py`
- **Purpose**: Query and aggregate visitor data

**Key Methods**:
```python
# Get unique visitors
stats = VisitorAnalytics.get_unique_visitors(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31),
    community_id=uuid_obj,
    division_id=uuid_obj
)

# Get division breakdown
breakdown = VisitorAnalytics.get_division_breakdown(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31)
)

# Get trends
trends = VisitorAnalytics.get_trends(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31),
    interval='day'  # or 'hour', 'week', 'month'
)

# Get conversion metrics
conversions = VisitorAnalytics.get_conversions(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31)
)
```

#### visitor_tracker
- **Location**: `analytics/utils.py`
- **Purpose**: Real-time visitor counting

**Key Methods**:
```python
from analytics.utils import visitor_tracker

# Track visitor join
visitor_tracker.add_visitor(
    visitor_id='unique-id',
    community_id=uuid_obj  # optional
)

# Track visitor leave
visitor_tracker.remove_visitor(
    visitor_id='unique-id',
    community_id=uuid_obj  # optional
)

# Get current count
count = visitor_tracker.get_count(
    community_id=uuid_obj  # optional
)
```

### 4. Celery Tasks

#### Background Processing
- **Location**: `analytics/tasks.py`

**Available Tasks**:
```python
# Track anonymous visitor (called by middleware)
track_anonymous_visitor.delay(
    fingerprint='fp-123',
    page_url='/page/',
    referrer='https://google.com',
    user_agent='Mozilla...'
)

# Update community analytics
update_community_analytics.delay(community_id)

# Aggregate page analytics
aggregate_page_analytics.delay(date='2025-01-01')

# Calculate conversion metrics
calculate_conversion_metrics.delay()

# Cleanup old sessions (90+ days)
cleanup_old_sessions.delay()
```

---

## API Endpoints

All endpoints require authentication and moderator/admin permissions.

### Base URL
```
/api/analytics/
```

### Endpoints

#### 1. GET `/visitors/`
Get comprehensive visitor statistics.

**Query Parameters**:
- `start_date` (optional): ISO date format (YYYY-MM-DD)
- `end_date` (optional): ISO date format (YYYY-MM-DD)
- `community_id` (optional): UUID
- `division_id` (optional): UUID

**Response**:
```json
{
    "total_visitors": 1234,
    "authenticated_visitors": 800,
    "anonymous_visitors": 434,
    "conversion_rate": 64.8,
    "total_page_views": 5678,
    "avg_page_views_per_visitor": 4.6
}
```

#### 2. GET `/visitors/today/`
Get today's visitor statistics.

**Response**: Same as `/visitors/` for current date.

#### 3. GET `/visitors/weekly/`
Get last 7 days visitor statistics.

**Response**: Same as `/visitors/` for last 7 days.

#### 4. GET `/visitors/monthly/`
Get last 30 days visitor statistics.

**Response**: Same as `/visitors/` for last 30 days.

#### 5. GET `/division-breakdown/`
Get visitor distribution by administrative division.

**Query Parameters**:
- `start_date` (optional)
- `end_date` (optional)
- `limit` (optional, default: 10): Top N divisions

**Response**:
```json
[
    {
        "division_id": "uuid",
        "division_name": "New York",
        "division_type": "city",
        "count": 1500,
        "percentage": 25.3
    },
    ...
]
```

#### 6. GET `/trends/`
Get time-series visitor trends.

**Query Parameters**:
- `start_date` (optional)
- `end_date` (optional)
- `interval` (optional, default: 'day'): 'hour', 'day', 'week', 'month'
- `community_id` (optional)

**Response**:
```json
{
    "labels": ["2025-01-01", "2025-01-02", ...],
    "total": [100, 150, 200, ...],
    "authenticated": [60, 90, 120, ...],
    "anonymous": [40, 60, 80, ...]
}
```

#### 7. GET `/conversions/`
Get anonymous-to-authenticated conversion metrics.

**Query Parameters**:
- `start_date` (optional)
- `end_date` (optional)

**Response**:
```json
{
    "total_conversions": 256,
    "conversion_rate": 64.8,
    "avg_time_to_conversion": 3600,  // seconds
    "conversions_by_date": {
        "2025-01-01": 10,
        "2025-01-02": 15,
        ...
    }
}
```

#### 8. GET `/demographics/`
Get visitor demographics data.

**Query Parameters**:
- `start_date` (optional)
- `end_date` (optional)

**Response**:
```json
{
    "by_division_type": {
        "city": 500,
        "province": 300,
        "country": 200
    },
    "top_countries": [
        {"name": "Canada", "count": 800},
        {"name": "USA", "count": 200}
    ]
}
```

#### 9. GET `/realtime/`
Get current online visitor count.

**Query Parameters**:
- `community_id` (optional)

**Response**:
```json
{
    "count": 42,
    "timestamp": "2025-10-11T12:00:00Z"
}
```

#### 10. GET `/growth/`
Get visitor growth statistics.

**Query Parameters**:
- `period` (optional, default: 'week'): 'day', 'week', 'month'

**Response**:
```json
{
    "growth_rate": 15.3,  // percentage
    "trend": "increasing",  // or "decreasing", "stable"
    "current_period": 1000,
    "previous_period": 870
}
```

#### 11. GET `/export/`
Export analytics data as CSV.

**Query Parameters**:
- `start_date` (optional)
- `end_date` (optional)
- `community_id` (optional)

**Response**: CSV file download

```csv
date,total_visitors,authenticated_visitors,anonymous_visitors,page_views
2025-01-01,100,60,40,150
2025-01-02,120,70,50,180
...
```

### Authentication

All endpoints require:
1. Valid authentication token
2. User must be staff (`is_staff=True`) OR moderator (`is_moderator=True`)

**Example Request**:
```bash
curl -X GET http://localhost:8000/api/analytics/visitors/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## WebSocket Events

### Connection URLs

#### Visitor Count Updates
```
ws://localhost:8000/ws/analytics/visitors/
```

**Query Parameters**:
- `community_id` (optional): Filter by community

#### Dashboard Updates
```
ws://localhost:8000/ws/analytics/dashboard/
```

**Query Parameters**:
- `community_id` (optional): Filter by community

### Message Types

#### 1. Incoming: `visitor_count`
Sent when client connects or count changes.

```json
{
    "type": "visitor_count",
    "count": 42
}
```

#### 2. Incoming: `visitor_joined`
Sent when a new visitor joins.

```json
{
    "type": "visitor_joined",
    "visitor": {
        "id": "visitor-id",
        "timestamp": "2025-10-11T12:00:00Z"
    }
}
```

#### 3. Incoming: `visitor_left`
Sent when a visitor leaves.

```json
{
    "type": "visitor_left",
    "visitor": {
        "id": "visitor-id",
        "timestamp": "2025-10-11T12:05:00Z"
    }
}
```

#### 4. Outgoing: `request_count`
Request current visitor count.

```json
{
    "type": "request_count"
}
```

### JavaScript Example

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/analytics/visitors/');

// Handle connection
ws.onopen = () => {
    console.log('Connected to analytics');
};

// Handle messages
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch(data.type) {
        case 'visitor_count':
            console.log('Current visitors:', data.count);
            break;
        case 'visitor_joined':
            console.log('Visitor joined');
            break;
        case 'visitor_left':
            console.log('Visitor left');
            break;
    }
};

// Request count
ws.send(JSON.stringify({ type: 'request_count' }));

// Close connection
ws.close();
```

---

## Frontend Integration

### Installation

```bash
# Using Yarn (Docker)
docker-compose exec frontend yarn add chart.js react-chartjs-2

# Or run setup script
./scripts/setup_analytics_components.sh
```

### Basic Usage

```javascript
import { VisitorAnalyticsDashboard } from './components/analytics';

function AdminPage() {
    return (
        <div>
            <h1>Analytics Dashboard</h1>
            <VisitorAnalyticsDashboard />
        </div>
    );
}
```

### Individual Components

```javascript
import {
    VisitorStatsCard,
    VisitorTrendsChart,
    DivisionBreakdown,
    RealtimeVisitorCounter
} from './components/analytics';

function CustomDashboard() {
    return (
        <div>
            <VisitorStatsCard
                title="Total Visitors"
                value={1234}
                change={15.3}
            />

            <VisitorTrendsChart
                data={trendsData}
                type="line"
            />

            <DivisionBreakdown
                data={divisionData}
            />

            <RealtimeVisitorCounter />
        </div>
    );
}
```

### Permission Checks

```javascript
import { useAuth } from './hooks/useAuth';
import { Navigate } from 'react-router-dom';

function AnalyticsDashboard() {
    const { user } = useAuth();

    // Check permissions
    if (!user?.is_staff && !user?.is_moderator) {
        return <Navigate to="/unauthorized" />;
    }

    return <VisitorAnalyticsDashboard />;
}
```

### API Service Usage

```javascript
import visitorAnalyticsAPI from './services/visitorAnalyticsAPI';

// Get visitor stats
const stats = await visitorAnalyticsAPI.getVisitors({
    start_date: '2025-01-01',
    end_date: '2025-12-31'
});

// Get trends
const trends = await visitorAnalyticsAPI.getTrends({
    interval: 'day'
});

// Export CSV
const blob = await visitorAnalyticsAPI.exportCSV({
    start_date: '2025-01-01',
    end_date: '2025-12-31'
});
```

---

## Deployment Considerations

### 1. Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Analytics Settings
ANALYTICS_REALTIME_TTL=3600  # 1 hour
ANALYTICS_SESSION_TIMEOUT=86400  # 24 hours
ANALYTICS_CLEANUP_DAYS=90  # Keep sessions for 90 days
```

### 2. Database Indexes

Ensure proper indexes exist:

```sql
-- AnonymousSession indexes
CREATE INDEX idx_anonymous_fingerprint ON analytics_anonymoussession(fingerprint);
CREATE INDEX idx_anonymous_session_id ON analytics_anonymoussession(session_id);
CREATE INDEX idx_anonymous_first_seen ON analytics_anonymoussession(first_seen);
CREATE INDEX idx_anonymous_converted ON analytics_anonymoussession(converted_at);

-- PageAnalytics indexes
CREATE INDEX idx_page_date ON analytics_pageanalytics(date);
CREATE INDEX idx_page_url ON analytics_pageanalytics(page_url);
CREATE INDEX idx_page_date_url ON analytics_pageanalytics(date, page_url);
```

### 3. Celery Workers

```bash
# Start Celery worker
celery -A citinfos_backend worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A citinfos_backend beat --loglevel=info

# Monitor with Flower
celery -A citinfos_backend flower --port=5555
```

### 4. WebSocket Configuration

#### Nginx Configuration

```nginx
# WebSocket proxy
location /ws/ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
}
```

#### Daphne Configuration

```yaml
# docker-compose.yml
backend:
  command: daphne -b 0.0.0.0 -p 8000 citinfos_backend.asgi:application
```

### 5. Redis Configuration

```python
# settings.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('redis', 6379)],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}
```

### 6. Caching Strategy

```python
# Cache visitor counts
from django.core.cache import cache

# Set visitor count (1 hour TTL)
cache.set('visitor_count', count, timeout=3600)

# Get cached count
count = cache.get('visitor_count', default=0)
```

### 7. Monitoring

```python
# Log analytics events
import logging

logger = logging.getLogger('analytics')

logger.info(f'Visitor joined: {visitor_id}')
logger.info(f'Conversion tracked: {fingerprint}')
logger.error(f'Analytics error: {error}')
```

### 8. Performance Tuning

#### Database Query Optimization

```python
# Use select_related and prefetch_related
PageAnalytics.objects.select_related('community').filter(
    date__gte=start_date
)

# Use aggregation
from django.db.models import Sum, Avg, Count

PageAnalytics.objects.aggregate(
    total_visitors=Sum('unique_visitors'),
    avg_page_views=Avg('page_views')
)
```

#### Async Task Optimization

```python
# Batch operations
@shared_task
def batch_update_analytics(date_list):
    for date in date_list:
        aggregate_page_analytics(date)
```

### 9. Security

#### Rate Limiting

```python
# Use Django REST Framework throttling
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

#### CORS Configuration

```python
# Allow frontend to access WebSocket
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://yourdomain.com',
]

CORS_ALLOW_CREDENTIALS = True
```

### 10. Backup and Recovery

```bash
# Backup analytics data
pg_dump -U postgres -d citinfos_db -t analytics_* > analytics_backup.sql

# Backup Redis data
redis-cli --rdb /backup/dump.rdb
```

---

## Performance Optimization

### 1. Database Optimization

- **Partitioning**: Partition PageAnalytics by date
- **Archiving**: Move old data to archive tables
- **Indexing**: Ensure all foreign keys are indexed

### 2. Caching Strategy

- **Redis**: Cache real-time counts
- **Query Cache**: Cache expensive aggregations
- **CDN**: Serve static analytics assets via CDN

### 3. Async Processing

- **Celery**: All analytics updates should be async
- **Batch Processing**: Aggregate data in batches
- **Priority Queues**: Separate real-time from batch tasks

### 4. Frontend Optimization

- **Lazy Loading**: Load components on demand
- **Debouncing**: Debounce API calls
- **Pagination**: Paginate large datasets
- **Memoization**: Cache computed values

---

## Security

### 1. Permission Checks

```python
# All analytics views require IsAdminOrModerator
from analytics.permissions import IsAdminOrModerator

class VisitorAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrModerator]
```

### 2. Data Privacy

- **Anonymization**: Fingerprints are hashed
- **GDPR Compliance**: Users can request data deletion
- **Retention Policy**: Auto-delete old sessions after 90 days

### 3. WebSocket Security

- **Authentication**: Validate user tokens
- **Authorization**: Check permissions before broadcasting
- **Rate Limiting**: Limit connection attempts

---

## Troubleshooting

### Common Issues

#### 1. WebSocket not connecting
- Check Daphne is running
- Verify Redis is accessible
- Check CORS settings
- Ensure channel layers configured

#### 2. Celery tasks not running
- Verify Redis broker is running
- Check Celery worker is started
- Review task logs

#### 3. Missing data in analytics
- Check middleware is installed
- Verify Celery tasks are executing
- Review database for errors

#### 4. Performance issues
- Check database indexes
- Review Redis memory usage
- Optimize query patterns
- Enable query caching

---

## Support

For questions or issues:
1. Check documentation
2. Review test cases
3. Check Docker logs
4. Review Celery logs

## License

MIT License - See LICENSE file for details.
