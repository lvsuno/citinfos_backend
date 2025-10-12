# Visitor Analytics Utility Functions - Documentation

## Overview

The `visitor_utils.py` module provides comprehensive utility functions for retrieving and analyzing visitor data across the platform. It supports both authenticated and anonymous visitors with division-level tracking.

## Main Class: VisitorAnalytics

### Core Methods

#### 1. `get_unique_visitors()`
Get unique visitor count for a community within a date range.

**Parameters:**
- `community_id` (str): UUID of the community
- `start_date` (datetime, optional): Start of date range (default: today)
- `end_date` (datetime, optional): End of date range (default: now)
- `include_anonymous` (bool): Include anonymous visitors (default: True)
- `include_authenticated` (bool): Include authenticated visitors (default: True)

**Returns:**
```python
{
    'community_id': 'uuid-string',
    'start_date': '2025-10-10T00:00:00',
    'end_date': '2025-10-10T23:59:59',
    'authenticated_visitors': 150,
    'anonymous_visitors': 300,
    'total_unique_visitors': 450
}
```

**Usage:**
```python
from analytics.visitor_utils import VisitorAnalytics
from django.utils import timezone
from datetime import timedelta

# Get today's visitors
today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
visitors = VisitorAnalytics.get_unique_visitors(
    community_id='abc-123',
    start_date=today_start,
    end_date=timezone.now()
)

print(f"Total visitors today: {visitors['total_unique_visitors']}")
print(f"Authenticated: {visitors['authenticated_visitors']}")
print(f"Anonymous: {visitors['anonymous_visitors']}")
```

---

#### 2. `get_division_breakdown()`
Get visitor breakdown by division for a community.

**Parameters:**
- `community_id` (str): UUID of the community
- `start_date` (datetime, optional): Start of date range
- `end_date` (datetime, optional): End of date range

**Returns:**
```python
{
    'community_id': 'uuid-string',
    'community_division_id': 'division-uuid',
    'start_date': '2025-10-10T00:00:00',
    'end_date': '2025-10-10T23:59:59',
    'breakdown': {
        'same_division': 80,      # Visitors from same division
        'cross_division': 50,     # Visitors from other divisions
        'no_division': 20,        # Visitors with no division
        'anonymous': 300          # Anonymous visitors
    },
    'total_visitors': 450
}
```

**Usage:**
```python
# Get division breakdown for today
breakdown = VisitorAnalytics.get_division_breakdown(
    community_id='abc-123'
)

same_div = breakdown['breakdown']['same_division']
cross_div = breakdown['breakdown']['cross_division']

print(f"Same division visitors: {same_div}")
print(f"Cross-division visitors: {cross_div}")
print(f"Cross-division rate: {cross_div / breakdown['total_visitors'] * 100:.1f}%")
```

---

#### 3. `get_visitor_trends()`
Get visitor trends over time with configurable granularity.

**Parameters:**
- `community_id` (str): UUID of the community
- `days` (int): Number of days to look back (default: 7)
- `granularity` (str): 'hourly', 'daily', or 'weekly' (default: 'daily')

**Returns:**
```python
{
    'community_id': 'uuid-string',
    'granularity': 'daily',
    'days': 7,
    'trends': [
        {
            'date': '2025-10-04',
            'authenticated': 120,
            'anonymous': 250,
            'total': 370
        },
        {
            'date': '2025-10-05',
            'authenticated': 135,
            'anonymous': 280,
            'total': 415
        },
        # ... more days
    ]
}
```

**Usage:**
```python
# Get daily trends for last 7 days
trends = VisitorAnalytics.get_visitor_trends(
    community_id='abc-123',
    days=7,
    granularity='daily'
)

for day in trends['trends']:
    print(f"{day['date']}: {day['total']} visitors")

# Get hourly trends for last 24 hours
hourly_trends = VisitorAnalytics.get_visitor_trends(
    community_id='abc-123',
    days=1,
    granularity='hourly'
)
```

---

#### 4. `get_conversion_metrics()`
Get anonymous-to-authenticated conversion metrics.

**Parameters:**
- `start_date` (datetime, optional): Start of date range
- `end_date` (datetime, optional): End of date range
- `page_url` (str, optional): Filter by specific page

**Returns:**
```python
{
    'start_date': '2025-10-10T00:00:00',
    'end_date': '2025-10-10T23:59:59',
    'total_conversions': 45,
    'total_anonymous_sessions': 500,
    'overall_conversion_rate': 9.0,  # percentage
    'avg_time_to_conversion_seconds': 1800.5,
    'avg_pages_before_conversion': 5.2,
    'top_conversion_pages': [
        {
            'page_url': '/communities/tech',
            'conversions': 15,
            'views': 120,
            'conversion_rate': 12.5
        },
        # ... more pages
    ]
}
```

**Usage:**
```python
# Get conversion metrics for today
metrics = VisitorAnalytics.get_conversion_metrics()

print(f"Conversion rate: {metrics['overall_conversion_rate']}%")
print(f"Avg time to convert: {metrics['avg_time_to_conversion_seconds'] / 60:.1f} min")
print(f"Avg pages viewed: {metrics['avg_pages_before_conversion']}")

# Top converting pages
for page in metrics['top_conversion_pages'][:3]:
    print(f"{page['page_url']}: {page['conversion_rate']}% conversion")
```

---

#### 5. `get_visitor_demographics()`
Get visitor demographics (device, browser, OS).

**Parameters:**
- `community_id` (str): UUID of the community
- `start_date` (datetime, optional): Start of date range
- `end_date` (datetime, optional): End of date range

**Returns:**
```python
{
    'community_id': 'uuid-string',
    'start_date': '2025-10-10T00:00:00',
    'end_date': '2025-10-10T23:59:59',
    'total_sessions': 300,
    'device_types': [
        {'device_type': 'mobile', 'count': 180},
        {'device_type': 'desktop', 'count': 100},
        {'device_type': 'tablet', 'count': 20}
    ],
    'browsers': [
        {'browser': 'Chrome', 'count': 200},
        {'browser': 'Safari', 'count': 80},
        {'browser': 'Firefox', 'count': 20}
    ],
    'operating_systems': [
        {'os': 'iOS', 'count': 120},
        {'os': 'Android', 'count': 80},
        {'os': 'Windows', 'count': 70},
        {'os': 'macOS', 'count': 30}
    ]
}
```

**Usage:**
```python
# Get demographics for today
demographics = VisitorAnalytics.get_visitor_demographics(
    community_id='abc-123'
)

# Mobile vs Desktop
mobile_count = next(
    (d['count'] for d in demographics['device_types'] if d['device_type'] == 'mobile'),
    0
)
desktop_count = next(
    (d['count'] for d in demographics['device_types'] if d['device_type'] == 'desktop'),
    0
)

mobile_percentage = mobile_count / demographics['total_sessions'] * 100
print(f"Mobile traffic: {mobile_percentage:.1f}%")

# Top browser
top_browser = demographics['browsers'][0]
print(f"Top browser: {top_browser['browser']} ({top_browser['count']} users)")
```

---

#### 6. `get_realtime_visitors()`
Get current real-time visitor count from Redis.

**Parameters:**
- `community_id` (str): UUID of the community

**Returns:**
```python
{
    'community_id': 'uuid-string',
    'timestamp': '2025-10-10T14:30:00',
    'total_online': 47,
    'authenticated_online': 20,
    'anonymous_online': 27
}
```

**Usage:**
```python
# Get current online visitors
realtime = VisitorAnalytics.get_realtime_visitors(
    community_id='abc-123'
)

print(f"Currently online: {realtime['total_online']}")
print(f"  - Authenticated: {realtime['authenticated_online']}")
print(f"  - Anonymous: {realtime['anonymous_online']}")
```

---

## Convenience Functions

### Quick Access Functions

#### `get_today_visitors(community_id)`
```python
from analytics.visitor_utils import get_today_visitors

visitors = get_today_visitors('abc-123')
# Returns same structure as get_unique_visitors()
```

#### `get_weekly_visitors(community_id)`
```python
from analytics.visitor_utils import get_weekly_visitors

visitors = get_weekly_visitors('abc-123')
# Last 7 days visitor data
```

#### `get_monthly_visitors(community_id)`
```python
from analytics.visitor_utils import get_monthly_visitors

visitors = get_monthly_visitors('abc-123')
# Last 30 days visitor data
```

#### `get_visitor_growth_rate(community_id, current_period_days=7)`
```python
from analytics.visitor_utils import get_visitor_growth_rate

growth = get_visitor_growth_rate('abc-123', current_period_days=7)
# Returns:
# {
#     'community_id': 'uuid-string',
#     'period_days': 7,
#     'current_period': {
#         'start': '2025-10-03T00:00:00',
#         'end': '2025-10-10T23:59:59',
#         'visitors': 450
#     },
#     'previous_period': {
#         'start': '2025-09-26T00:00:00',
#         'end': '2025-10-03T00:00:00',
#         'visitors': 380
#     },
#     'growth_rate': 18.42,  # percentage
#     'absolute_change': 70
# }

print(f"Growth rate: {growth['growth_rate']}%")
print(f"Change: {'+' if growth['absolute_change'] > 0 else ''}{growth['absolute_change']} visitors")
```

---

## Integration Examples

### Dashboard View
```python
from analytics.visitor_utils import (
    VisitorAnalytics,
    get_today_visitors,
    get_visitor_growth_rate
)

def get_community_dashboard(community_id):
    """Get complete dashboard data for a community."""

    # Real-time data
    realtime = VisitorAnalytics.get_realtime_visitors(community_id)

    # Today's visitors
    today = get_today_visitors(community_id)

    # Growth rate (week over week)
    growth = get_visitor_growth_rate(community_id, current_period_days=7)

    # Division breakdown
    divisions = VisitorAnalytics.get_division_breakdown(community_id)

    # 7-day trend
    trends = VisitorAnalytics.get_visitor_trends(
        community_id,
        days=7,
        granularity='daily'
    )

    # Demographics
    demographics = VisitorAnalytics.get_visitor_demographics(community_id)

    return {
        'realtime': realtime,
        'today': today,
        'growth': growth,
        'divisions': divisions,
        'trends': trends,
        'demographics': demographics
    }
```

### Conversion Analysis
```python
from analytics.visitor_utils import VisitorAnalytics
from datetime import timedelta
from django.utils import timezone

def analyze_conversion_funnel(days=30):
    """Analyze conversion funnel for the last N days."""

    start_date = timezone.now() - timedelta(days=days)

    # Get conversion metrics
    metrics = VisitorAnalytics.get_conversion_metrics(
        start_date=start_date
    )

    # Analyze top converting pages
    top_pages = metrics['top_conversion_pages'][:5]

    # Calculate optimization opportunities
    opportunities = []
    for page in metrics['top_conversion_pages']:
        if page['views'] > 100 and page['conversion_rate'] < 5:
            opportunities.append({
                'page': page['page_url'],
                'current_rate': page['conversion_rate'],
                'views': page['views'],
                'potential_conversions': int(page['views'] * 0.05)  # 5% target
            })

    return {
        'metrics': metrics,
        'top_performers': top_pages,
        'optimization_opportunities': opportunities
    }
```

### Real-time Monitoring
```python
from analytics.visitor_utils import VisitorAnalytics

def monitor_visitor_spike(community_id, threshold=100):
    """Monitor for unusual visitor spikes."""

    # Get current online count
    realtime = VisitorAnalytics.get_realtime_visitors(community_id)
    current_online = realtime['total_online']

    # Get average for last hour
    hourly = VisitorAnalytics.get_visitor_trends(
        community_id,
        days=1,
        granularity='hourly'
    )

    # Calculate average
    recent_hours = hourly['trends'][-6:]  # Last 6 hours
    avg_online = sum(h['total'] for h in recent_hours) / len(recent_hours)

    # Check for spike
    if current_online > avg_online * 2:  # 200% increase
        return {
            'spike_detected': True,
            'current': current_online,
            'average': avg_online,
            'increase_percentage': (current_online / avg_online - 1) * 100
        }

    return {'spike_detected': False}
```

---

## Performance Considerations

### Redis Usage
- **Real-time data**: Fetched from Redis for current visitors
- **Historical data**: Fetched from PostgreSQL for past periods
- **Automatic fallback**: Falls back to DB if Redis unavailable

### Caching Strategy
```python
from django.core.cache import cache

def get_cached_visitor_stats(community_id, cache_timeout=60):
    """Get visitor stats with caching."""

    cache_key = f"visitor_stats:{community_id}:today"

    # Try cache first
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Fetch fresh data
    stats = get_today_visitors(community_id)

    # Cache for 1 minute
    cache.set(cache_key, stats, timeout=cache_timeout)

    return stats
```

### Query Optimization
- Uses `select_related()` for foreign keys
- Uses `values()` for aggregations
- Implements `distinct()` for unique counts
- Batches Redis scans with cursor pagination

---

## Error Handling

All functions include error handling:

```python
# Example error response
{
    'error': 'Community not found',
    'community_id': 'invalid-uuid'
}
```

Always check for errors:
```python
result = VisitorAnalytics.get_unique_visitors('abc-123')

if 'error' in result:
    print(f"Error: {result['error']}")
else:
    print(f"Visitors: {result['total_unique_visitors']}")
```

---

## Testing

### Unit Tests
```python
from django.test import TestCase
from analytics.visitor_utils import VisitorAnalytics
from communities.models import Community

class VisitorUtilsTestCase(TestCase):
    def test_get_unique_visitors(self):
        """Test unique visitor count calculation."""
        community = Community.objects.create(name='Test')

        result = VisitorAnalytics.get_unique_visitors(
            str(community.id)
        )

        self.assertIn('total_unique_visitors', result)
        self.assertGreaterEqual(result['total_unique_visitors'], 0)

    def test_division_breakdown(self):
        """Test division breakdown calculation."""
        community = Community.objects.create(name='Test')

        result = VisitorAnalytics.get_division_breakdown(
            str(community.id)
        )

        self.assertIn('breakdown', result)
        self.assertIn('same_division', result['breakdown'])
```

---

## Future Enhancements

### 1. Advanced Filtering
```python
# Filter by referrer source
VisitorAnalytics.get_unique_visitors(
    community_id='abc-123',
    referrer_contains='google.com'
)

# Filter by device type
VisitorAnalytics.get_unique_visitors(
    community_id='abc-123',
    device_type='mobile'
)
```

### 2. Predictive Analytics
```python
def predict_visitor_trend(community_id, days_ahead=7):
    """Predict visitor count for next N days using historical data."""
    # Implementation using linear regression or time series analysis
    pass
```

### 3. Comparative Analysis
```python
def compare_communities(community_ids, metric='total_visitors'):
    """Compare multiple communities on a specific metric."""
    # Implementation for multi-community comparison
    pass
```

---

## Conclusion

The visitor utility functions provide a comprehensive toolkit for analyzing visitor behavior across authenticated and anonymous users, with support for:

- ✅ Real-time and historical data
- ✅ Division-level tracking
- ✅ Conversion analysis
- ✅ Demographic insights
- ✅ Growth rate calculations
- ✅ Trend analysis
- ✅ Error handling and fallbacks

Use these utilities to build powerful analytics dashboards and insights!
