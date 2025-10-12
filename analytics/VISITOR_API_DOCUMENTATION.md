# Visitor Analytics API Documentation

This document describes the REST API endpoints for visitor analytics tracking and reporting.

## Table of Contents

- [Authentication](#authentication)
- [Permissions](#permissions)
- [Endpoints](#endpoints)
  - [Visitor Statistics](#visitor-statistics)
  - [Division Breakdown](#division-breakdown)
  - [Visitor Trends](#visitor-trends)
  - [Conversion Metrics](#conversion-metrics)
  - [Visitor Demographics](#visitor-demographics)
  - [Real-time Visitors](#real-time-visitors)
  - [Convenience Endpoints](#convenience-endpoints)
- [Response Formats](#response-formats)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Authentication

All endpoints require authentication using JWT tokens or session authentication.

```bash
# Using JWT
curl -H "Authorization: Bearer <your_jwt_token>" \
  https://api.example.com/analytics/api/communities/{id}/visitors/
```

## Permissions

- **Basic Member**: Can view basic visitor statistics
- **Moderator/Admin**: Can view detailed analytics including:
  - Division breakdown
  - Conversion metrics
  - Demographics

## Endpoints

### Visitor Statistics

Get unique visitor statistics for a community.

**Endpoint**: `GET /analytics/api/visitors/communities/{community_id}/visitors/`

**Query Parameters**:
- `start_date` (optional): ISO format date (e.g., `2025-10-01T00:00:00`)
- `end_date` (optional): ISO format date (e.g., `2025-10-10T23:59:59`)

**Response**:
```json
{
  "authenticated_visitors": 150,
  "anonymous_visitors": 320,
  "total_unique_visitors": 470,
  "date_range": {
    "start": "2025-10-01T00:00:00Z",
    "end": "2025-10-10T23:59:59Z"
  }
}
```

**Permissions**: Community member

---

### Division Breakdown

Get division-level breakdown of visitors.

**Endpoint**: `GET /analytics/api/visitors/communities/{community_id}/division-breakdown/`

**Query Parameters**:
- `start_date` (optional): ISO format date
- `end_date` (optional): ISO format date

**Response**:
```json
{
  "same_division_visitors": 80,
  "cross_division_visitors": 65,
  "no_division_visitors": 5,
  "total_authenticated_visitors": 150,
  "breakdown_percentage": {
    "same_division": 53.33,
    "cross_division": 43.33,
    "no_division": 3.34
  }
}
```

**Permissions**: Moderator or Admin

---

### Visitor Trends

Get visitor trends over time with different granularities.

**Endpoint**: `GET /analytics/api/visitors/communities/{community_id}/trends/`

**Query Parameters**:
- `start_date` (optional): ISO format date
- `end_date` (optional): ISO format date
- `granularity` (optional): `hourly`, `daily`, or `weekly` (default: `daily`)

**Response**:
```json
[
  {
    "period": "2025-10-01",
    "authenticated_count": 45,
    "anonymous_count": 78,
    "total_count": 123
  },
  {
    "period": "2025-10-02",
    "authenticated_count": 52,
    "anonymous_count": 85,
    "total_count": 137
  }
]
```

**Permissions**: Community member

---

### Conversion Metrics

Get anonymous-to-authenticated conversion statistics.

**Endpoint**: `GET /analytics/api/visitors/communities/{community_id}/conversions/`

**Query Parameters**:
- `start_date` (optional): ISO format date
- `end_date` (optional): ISO format date

**Response**:
```json
{
  "total_conversions": 45,
  "total_anonymous_sessions": 320,
  "overall_conversion_rate": 14.06,
  "top_conversion_pages": [
    {
      "page_url": "/communities/join",
      "conversions": 25,
      "views": 150,
      "conversion_rate": 16.67
    },
    {
      "page_url": "/communities/about",
      "conversions": 12,
      "views": 100,
      "conversion_rate": 12.0
    }
  ],
  "avg_time_to_conversion": 450.5
}
```

**Permissions**: Moderator or Admin

---

### Visitor Demographics

Get device, browser, and OS breakdown of visitors.

**Endpoint**: `GET /analytics/api/visitors/communities/{community_id}/demographics/`

**Query Parameters**:
- `start_date` (optional): ISO format date
- `end_date` (optional): ISO format date

**Response**:
```json
{
  "total_sessions": 500,
  "device_types": [
    {
      "device_type": "mobile",
      "count": 300,
      "percentage": 60.0
    },
    {
      "device_type": "desktop",
      "count": 180,
      "percentage": 36.0
    },
    {
      "device_type": "tablet",
      "count": 20,
      "percentage": 4.0
    }
  ],
  "browsers": [
    {
      "browser": "Chrome",
      "count": 280,
      "percentage": 56.0
    },
    {
      "browser": "Safari",
      "count": 150,
      "percentage": 30.0
    },
    {
      "browser": "Firefox",
      "count": 70,
      "percentage": 14.0
    }
  ],
  "operating_systems": [
    {
      "operating_system": "iOS",
      "count": 200,
      "percentage": 40.0
    },
    {
      "operating_system": "Android",
      "count": 180,
      "percentage": 36.0
    },
    {
      "operating_system": "Windows",
      "count": 80,
      "percentage": 16.0
    },
    {
      "operating_system": "macOS",
      "count": 40,
      "percentage": 8.0
    }
  ]
}
```

**Permissions**: Moderator or Admin

---

### Real-time Visitors

Get current real-time visitor count from Redis.

**Endpoint**: `GET /analytics/api/visitors/communities/{community_id}/realtime/`

**Response**:
```json
{
  "community_id": "123e4567-e89b-12d3-a456-426614174000",
  "current_online": 42,
  "timestamp": "2025-10-10T14:30:00Z"
}
```

**Permissions**: Community member

---

### Convenience Endpoints

#### Today's Visitors

**Endpoint**: `GET /analytics/api/communities/{community_id}/visitors/today/`

Returns visitor statistics for today only.

**Response**: Same as [Visitor Statistics](#visitor-statistics)

---

#### Weekly Visitors

**Endpoint**: `GET /analytics/api/communities/{community_id}/visitors/weekly/`

Returns visitor statistics for the past 7 days.

**Response**: Same as [Visitor Statistics](#visitor-statistics)

---

#### Monthly Visitors

**Endpoint**: `GET /analytics/api/communities/{community_id}/visitors/monthly/`

Returns visitor statistics for the past 30 days.

**Response**: Same as [Visitor Statistics](#visitor-statistics)

---

#### Visitor Growth Rate

**Endpoint**: `GET /analytics/api/communities/{community_id}/visitors/growth/`

**Query Parameters**:
- `days` (optional): Number of days to compare (default: 7)

**Response**:
```json
{
  "current_period_visitors": 150,
  "previous_period_visitors": 120,
  "growth_rate": 25.0,
  "growth_count": 30,
  "comparison_days": 7
}
```

---

## Response Formats

### Success Response

All successful responses follow this general format:

```json
{
  "data": { ... },
  "status": "success"
}
```

### Error Response

Error responses follow this format:

```json
{
  "error": "Error message description",
  "status": "error"
}
```

## Error Handling

### Common Error Codes

- `400 Bad Request`: Invalid parameters (e.g., malformed dates)
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Community not found
- `500 Internal Server Error`: Server error

### Error Examples

**Invalid Date Format**:
```json
{
  "error": "Invalid date format: '2025-13-45'. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
}
```

**Permission Denied**:
```json
{
  "error": "You are not a member of this community"
}
```

**Insufficient Permissions**:
```json
{
  "error": "Insufficient permissions"
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Anonymous users**: 100 requests per hour
- **Authenticated users**: 1000 requests per hour
- **Premium users**: 5000 requests per hour

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1696963200
```

## Examples

### Example 1: Get Weekly Visitor Trends

```bash
curl -X GET \
  'https://api.example.com/analytics/api/visitors/communities/123e4567-e89b-12d3-a456-426614174000/trends/?granularity=daily&start_date=2025-10-01T00:00:00&end_date=2025-10-07T23:59:59' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

### Example 2: Get Real-time Visitor Count

```bash
curl -X GET \
  'https://api.example.com/analytics/api/visitors/communities/123e4567-e89b-12d3-a456-426614174000/realtime/' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

### Example 3: Get Conversion Metrics for Last Month

```bash
curl -X GET \
  'https://api.example.com/analytics/api/visitors/communities/123e4567-e89b-12d3-a456-426614174000/conversions/?start_date=2025-09-01T00:00:00&end_date=2025-09-30T23:59:59' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

### Example 4: Using Python Requests

```python
import requests
from datetime import datetime, timedelta

# Configuration
API_BASE = "https://api.example.com"
COMMUNITY_ID = "123e4567-e89b-12d3-a456-426614174000"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# Get visitor trends for last 7 days
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

response = requests.get(
    f"{API_BASE}/analytics/api/visitors/communities/{COMMUNITY_ID}/trends/",
    headers=headers,
    params={
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "granularity": "daily"
    }
)

if response.status_code == 200:
    trends = response.json()
    for day in trends:
        print(f"{day['period']}: {day['total_count']} visitors")
else:
    print(f"Error: {response.json()['error']}")
```

### Example 5: Using JavaScript/Fetch

```javascript
const API_BASE = 'https://api.example.com';
const COMMUNITY_ID = '123e4567-e89b-12d3-a456-426614174000';
const TOKEN = 'your_jwt_token';

async function getRealtimeVisitors() {
  const response = await fetch(
    `${API_BASE}/analytics/api/visitors/communities/${COMMUNITY_ID}/realtime/`,
    {
      headers: {
        'Authorization': `Bearer ${TOKEN}`
      }
    }
  );

  if (response.ok) {
    const data = await response.json();
    console.log(`Current online: ${data.current_online}`);
  } else {
    const error = await response.json();
    console.error(`Error: ${error.error}`);
  }
}

getRealtimeVisitors();
```

## Pagination

For endpoints that return large datasets, pagination is supported:

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 200)

**Paginated Response**:
```json
{
  "count": 500,
  "next": "https://api.example.com/...?page=2",
  "previous": null,
  "results": [
    { ... }
  ]
}
```

## WebSocket Integration

For real-time updates, consider using WebSocket connections:

```javascript
const ws = new WebSocket(
  `wss://api.example.com/ws/communities/${COMMUNITY_ID}/visitors/`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Visitor update: ${data.current_online} online`);
};
```

See [WebSocket Documentation](./WEBSOCKET_DOCUMENTATION.md) for details.

## Best Practices

1. **Cache responses** where appropriate (especially real-time data)
2. **Use date ranges** to limit data volume
3. **Implement pagination** for large datasets
4. **Handle errors gracefully** with user-friendly messages
5. **Use WebSockets** for real-time updates instead of polling
6. **Respect rate limits** to avoid throttling

## Support

For API support and questions:
- Email: api-support@example.com
- Documentation: https://docs.example.com/analytics
- Status Page: https://status.example.com
