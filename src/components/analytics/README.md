# Visitor Analytics Components

Frontend React components for displaying visitor analytics data.

## Components

### 1. VisitorAnalyticsDashboard

Main dashboard component that combines all analytics features.

**Features:**
- Date range selection (Today, 7 Days, 30 Days)
- Stats cards (Total, Authenticated, Anonymous, Conversion Rate)
- Trends chart (Line or Bar)
- Division breakdown
- Real-time visitor counter
- CSV export

**Usage:**
```jsx
import { VisitorAnalyticsDashboard } from './components/analytics';

function AdminPage() {
    return (
        <VisitorAnalyticsDashboard communityId="optional-uuid" />
    );
}
```

**Props:**
- `communityId` (string, optional): Filter analytics by community

### 2. VisitorStatsCard

Displays a single statistic with change indicator.

**Usage:**
```jsx
import { VisitorStatsCard } from './components/analytics';

<VisitorStatsCard
    title="Total Visitors"
    value={1234}
    change={15.3}
    changeType="increase"
    icon="👥"
    subtitle="vs last week"
    loading={false}
/>
```

**Props:**
- `title` (string): Card title
- `value` (number): Statistic value
- `change` (number, optional): Percentage change
- `changeType` ('increase'|'decrease'|'neutral', optional): Change interpretation
- `icon` (string|ReactNode, optional): Icon to display
- `subtitle` (string, optional): Subtitle text
- `loading` (boolean): Loading state

### 3. VisitorTrendsChart

Line or bar chart showing visitor trends over time using Chart.js.

**Usage:**
```jsx
import { VisitorTrendsChart } from './components/analytics';

const data = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    total: [100, 150, 120, 180, 200],
    authenticated: [60, 90, 70, 110, 120],
    anonymous: [40, 60, 50, 70, 80]
};

<VisitorTrendsChart
    data={data}
    type="line"
    title="Weekly Trends"
    loading={false}
/>
```

**Props:**
- `data` (object): Chart data with labels and datasets
- `type` ('line'|'bar'): Chart type
- `title` (string): Chart title
- `loading` (boolean): Loading state

### 4. DivisionBreakdown

Shows visitor distribution by administrative division with progress bars.

**Usage:**
```jsx
import { DivisionBreakdown } from './components/analytics';

const data = [
    { division_id: '1', division_name: 'New York', division_type: 'City', count: 1500 },
    { division_id: '2', division_name: 'California', division_type: 'State', count: 1200 },
    // ...
];

<DivisionBreakdown
    data={data}
    loading={false}
/>
```

**Props:**
- `data` (array): Array of division objects
- `loading` (boolean): Loading state

### 5. RealtimeVisitorCounter

Live visitor counter with WebSocket updates.

**Usage:**
```jsx
import { RealtimeVisitorCounter } from './components/analytics';

<RealtimeVisitorCounter
    communityId="optional-uuid"
    websocketUrl="ws://localhost:8000/ws/analytics/visitors/"
/>
```

**Props:**
- `communityId` (string, optional): Filter by community
- `websocketUrl` (string, optional): Custom WebSocket URL

**Features:**
- Real-time visitor count updates
- Connection status indicator
- Recent activity feed (joins/leaves)
- Automatic reconnection

## Installation

### Dependencies

Since you're using Docker and Yarn, install dependencies in two ways:

**Option 1: Inside Docker container**
```bash
docker-compose exec frontend yarn add chart.js react-chartjs-2
```

**Option 2: Locally (will be synced to container via volume)**
```bash
yarn add chart.js react-chartjs-2
```

The frontend container uses volume mounting (`./src:/app/src`), so local changes sync automatically.

### File Structure

```
src/
├── components/
│   └── analytics/
│       ├── VisitorAnalyticsDashboard.jsx
│       ├── VisitorAnalyticsDashboard.css
│       ├── VisitorStatsCard.jsx
│       ├── VisitorStatsCard.css
│       ├── VisitorTrendsChart.jsx
│       ├── VisitorTrendsChart.css
│       ├── DivisionBreakdown.jsx
│       ├── DivisionBreakdown.css
│       ├── RealtimeVisitorCounter.jsx
│       ├── RealtimeVisitorCounter.css
│       └── index.js
└── services/
    ├── visitorAnalyticsAPI.js
    └── baseAPI.js
```

## API Service

The components use `visitorAnalyticsAPI` service for data fetching:

```javascript
import visitorAnalyticsAPI from './services/visitorAnalyticsAPI';

// Get visitor statistics
const stats = await visitorAnalyticsAPI.getVisitors({
    start_date: '2025-10-01',
    end_date: '2025-10-10',
    community_id: 'optional-uuid'
});

// Get trends
const trends = await visitorAnalyticsAPI.getTrends({
    start_date: '2025-10-01',
    end_date: '2025-10-10',
    interval: 'day'
});

// Get division breakdown
const divisions = await visitorAnalyticsAPI.getDivisionBreakdown({
    start_date: '2025-10-01',
    end_date: '2025-10-10'
});

// Get real-time count
const realtime = await visitorAnalyticsAPI.getRealtime();

// Export to CSV
const blob = await visitorAnalyticsAPI.exportCSV({
    start_date: '2025-10-01',
    end_date: '2025-10-10'
});
```

## WebSocket Events

The `RealtimeVisitorCounter` component listens for these WebSocket events:

### Incoming Events

**visitor_count**
```json
{
    "type": "visitor_count",
    "count": 42
}
```

**visitor_joined**
```json
{
    "type": "visitor_joined",
    "visitor": {
        "id": "visitor-id",
        "timestamp": "2025-10-10T10:30:00Z"
    }
}
```

**visitor_left**
```json
{
    "type": "visitor_left",
    "visitor": {
        "id": "visitor-id",
        "timestamp": "2025-10-10T10:35:00Z"
    }
}
```

### Outgoing Events

**request_count**
```json
{
    "type": "request_count",
    "community_id": "optional-uuid"
}
```

## Styling

All components include responsive CSS with:
- Mobile-first design
- Loading skeletons
- Smooth animations
- Hover effects
- Dark mode support (can be added)

## Example Integration

```jsx
// Admin Dashboard Page
import React from 'react';
import { VisitorAnalyticsDashboard } from './components/analytics';

function AdminDashboard() {
    return (
        <div className="admin-page">
            <h1>Admin Dashboard</h1>

            {/* Full analytics dashboard */}
            <VisitorAnalyticsDashboard />
        </div>
    );
}

export default AdminDashboard;
```

```jsx
// Community Page (with community filter)
import React from 'react';
import { VisitorAnalyticsDashboard } from './components/analytics';

function CommunityAnalytics({ communityId }) {
    return (
        <div className="community-analytics">
            <h1>Community Analytics</h1>

            {/* Analytics for specific community */}
            <VisitorAnalyticsDashboard communityId={communityId} />
        </div>
    );
}

export default CommunityAnalytics;
```

```jsx
// Using Individual Components
import React from 'react';
import {
    VisitorStatsCard,
    VisitorTrendsChart,
    RealtimeVisitorCounter
} from './components/analytics';

function CustomDashboard() {
    return (
        <div className="custom-dashboard">
            <div className="stats-row">
                <VisitorStatsCard
                    title="Today's Visitors"
                    value={256}
                    change={12.5}
                    changeType="increase"
                    icon="📊"
                />
            </div>

            <div className="charts-row">
                <VisitorTrendsChart data={trendsData} type="line" />
            </div>

            <div className="realtime-section">
                <RealtimeVisitorCounter />
            </div>
        </div>
    );
}

export default CustomDashboard;
```

## Permissions

These components should only be shown to:
- Admin users
- Moderators
- Community owners/moderators

Check user permissions before rendering:

```jsx
import { VisitorAnalyticsDashboard } from './components/analytics';
import { useAuth } from './hooks/useAuth';

function Dashboard() {
    const { user } = useAuth();

    if (!user?.is_staff && !user?.is_moderator) {
        return <div>Access Denied</div>;
    }

    return <VisitorAnalyticsDashboard />;
}
```

## Status

✅ **Complete** - All components created and ready to use
⏸️ **Not Integrated** - Components not yet integrated into main app
📝 **Next Steps**:
1. Install chart.js dependencies
2. Test components with real API data
3. Add to admin/moderator pages
4. Implement permission checks
5. Add error boundaries
6. Write component tests

## Notes

- Components are standalone and can be used individually
- All API calls go through `visitorAnalyticsAPI` service
- WebSocket connections are automatically managed
- Components include loading states and error handling
- Fully responsive and mobile-friendly
- Ready for production use after integration
