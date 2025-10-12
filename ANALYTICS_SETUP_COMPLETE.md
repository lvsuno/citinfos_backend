# Visitor Analytics Components - Docker + Yarn Setup Complete

## ✅ What's Been Created

### Components (12 files)
- **VisitorAnalyticsDashboard** - Main dashboard combining all components
- **VisitorStatsCard** - Single stat display with change indicators
- **VisitorTrendsChart** - Chart.js line/bar charts for trends
- **DivisionBreakdown** - Location distribution with progress bars
- **RealtimeVisitorCounter** - WebSocket-powered live visitor count
- All components include CSS files with responsive design

### Services
- **visitorAnalyticsAPI.js** - API service with 11 methods for all endpoints

### Documentation
- **README.md** - Complete component documentation
- **DOCKER_SETUP.md** - Docker-specific setup guide
- **QUICK_REFERENCE.md** - Quick reference card

### Scripts
- **setup_analytics_components.sh** - Automated setup script

## 🚀 Quick Start (3 Steps)

### 1. Install Dependencies

**Option A: Using the setup script (recommended)**
```bash
./scripts/setup_analytics_components.sh
```

**Option B: Using yarn helper**
```bash
# From host machine
yarn install:analytics

# Or inside Docker container
docker-compose exec frontend yarn install:analytics
```

**Option C: Manual installation**
```bash
docker-compose exec frontend yarn add chart.js react-chartjs-2
```

### 2. Verify Installation

Check your browser console at `http://localhost:3000`:
- No Chart.js errors
- Components load without issues

### 3. Use the Components

```javascript
// Import
import { VisitorAnalyticsDashboard } from './components/analytics';

// Use in your component
function AdminPage() {
    return (
        <div>
            <h1>Analytics</h1>
            <VisitorAnalyticsDashboard />
        </div>
    );
}
```

## 📦 Components Overview

### Full Dashboard
```javascript
<VisitorAnalyticsDashboard communityId="optional-uuid" />
```
Includes: Stats cards, trends chart, division breakdown, real-time counter, CSV export

### Individual Components
```javascript
// Single stat
<VisitorStatsCard
    title="Total Visitors"
    value={1234}
    change={15.3}
    changeType="increase"
/>

// Trends chart
<VisitorTrendsChart
    data={trendsData}
    type="line"
    title="Weekly Trends"
/>

// Location breakdown
<DivisionBreakdown data={divisionsData} />

// Real-time counter
<RealtimeVisitorCounter />
```

## 🐳 Docker Integration

Your existing `docker-compose.yml` is already configured:

### Frontend Service
- **Port**: 3000
- **Volume mounting**: `./src:/app/src` (auto-sync)
- **Hot reload**: Enabled with polling
- **Package manager**: Yarn (via Corepack)

### Backend Service
- **Port**: 8000
- **WebSocket**: Daphne ASGI server
- **API**: All analytics endpoints ready

### Supporting Services
- **Redis**: For real-time counting and caching
- **PostgreSQL**: For analytics data storage
- **Celery**: For background analytics processing

## 🔌 API & WebSocket

### REST API Endpoints
All endpoints require authentication (moderator/admin):
```
GET /api/analytics/visitors/              # Main stats
GET /api/analytics/visitors/today/        # Today's stats
GET /api/analytics/trends/                # Time series data
GET /api/analytics/division-breakdown/    # By location
GET /api/analytics/realtime/              # Current count
GET /api/analytics/export/                # CSV download
```

### WebSocket Endpoints
Real-time updates:
```
ws://localhost:8000/ws/analytics/visitors/
ws://localhost:8000/ws/analytics/dashboard/
```

## 🧪 Testing

### Test the Setup Script
```bash
./scripts/setup_analytics_components.sh
```

This will:
- ✅ Check Docker is running
- ✅ Verify containers are up
- ✅ Install dependencies
- ✅ Test WebSocket connection
- ✅ Test API endpoints
- ✅ Verify all files exist

### Manual Testing

**Test Components:**
```javascript
// Create: src/pages/AnalyticsTest.jsx
import { VisitorAnalyticsDashboard } from '../components/analytics';

export default function AnalyticsTest() {
    return <VisitorAnalyticsDashboard />;
}

// Add route and visit: http://localhost:3000/analytics-test
```

**Test API:**
```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access')

# Get stats
curl -X GET http://localhost:8000/api/analytics/visitors/ \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Test WebSocket:**
```bash
# Install wscat
yarn global add wscat

# Connect
wscat -c ws://localhost:8000/ws/analytics/visitors/

# Expected: {"type": "visitor_count", "count": 0}
```

## 🔧 Common Commands

```bash
# View logs
docker-compose logs -f frontend
docker-compose logs -f backend

# Restart services
docker-compose restart frontend
docker-compose restart backend

# Rebuild
docker-compose build --no-cache frontend

# Shell into containers
docker-compose exec frontend sh
docker-compose exec backend sh

# Install packages (from host)
yarn add <package>

# Install packages (in container)
docker-compose exec frontend yarn add <package>
```

## 📁 File Structure

```
citinfos_backend/
├── src/
│   ├── components/
│   │   └── analytics/
│   │       ├── VisitorAnalyticsDashboard.jsx
│   │       ├── VisitorAnalyticsDashboard.css
│   │       ├── VisitorStatsCard.jsx
│   │       ├── VisitorStatsCard.css
│   │       ├── VisitorTrendsChart.jsx
│   │       ├── VisitorTrendsChart.css
│   │       ├── DivisionBreakdown.jsx
│   │       ├── DivisionBreakdown.css
│   │       ├── RealtimeVisitorCounter.jsx
│   │       ├── RealtimeVisitorCounter.css
│   │       ├── index.js
│   │       ├── README.md
│   │       ├── DOCKER_SETUP.md
│   │       └── QUICK_REFERENCE.md
│   └── services/
│       ├── visitorAnalyticsAPI.js
│       ├── fingerprintService.js
│       └── apiService.js
├── scripts/
│   └── setup_analytics_components.sh
├── docker-compose.yml
├── Dockerfile.frontend
├── Dockerfile.backend
└── package.json (updated with install:analytics script)
```

## 🎯 Next Steps

### Immediate (Testing)
1. ✅ Run setup script: `./scripts/setup_analytics_components.sh`
2. ✅ Check browser console for errors
3. ✅ Test API endpoints with curl
4. ✅ Test WebSocket connection

### Short-term (Integration)
1. Create admin/moderator page
2. Add route for analytics dashboard
3. Add permission checks
4. Test with real data

### Long-term (Production)
1. Add error boundaries
2. Write component tests
3. Add loading states
4. Configure production WebSocket URLs
5. Add monitoring/alerts

## 🔐 Security Notes

### Permissions
Components should only be accessible to:
- Admin users (`is_staff=True`)
- Moderators (`is_moderator=True`)
- Community owners/moderators

### Implementation
```javascript
import { useAuth } from './hooks/useAuth';

function AnalyticsDashboard() {
    const { user } = useAuth();

    if (!user?.is_staff && !user?.is_moderator) {
        return <Navigate to="/unauthorized" />;
    }

    return <VisitorAnalyticsDashboard />;
}
```

## 📊 Features

### Dashboard Includes
- **4 Stat Cards**: Total, Authenticated, Anonymous visitors, Conversion rate
- **Date Range Selector**: Today, 7 days, 30 days
- **Trends Chart**: Line or bar chart with Chart.js
- **Division Breakdown**: Top 10 locations with progress bars
- **Real-time Counter**: Live visitor count via WebSocket
- **CSV Export**: Download analytics data

### Real-time Features
- WebSocket connection for live updates
- Visitor join/leave notifications
- Activity feed showing recent actions
- Auto-reconnect on disconnect
- Color-coded by visitor count

### Responsive Design
- Mobile-first approach
- Grid layouts for desktop
- Stacked layouts for mobile
- Touch-friendly controls

## 🆘 Troubleshooting

### Dependencies not installing
```bash
# Clear yarn cache
docker-compose exec frontend yarn cache clean

# Rebuild container
docker-compose build --no-cache frontend
docker-compose up frontend
```

### WebSocket not connecting
```bash
# Check Daphne is running
docker-compose logs backend | grep -i daphne

# Check WebSocket endpoint
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: test" \
  http://localhost:8000/ws/analytics/visitors/
```

### CORS errors
```python
# citinfos_backend/settings.py
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://frontend:3000',
]

CORS_ALLOW_CREDENTIALS = True
```

### Hot reload not working
```bash
# Check environment variables in Dockerfile.frontend
ENV CHOKIDAR_USEPOLLING=true
ENV WATCHPACK_POLLING=true

# Rebuild
docker-compose build frontend
docker-compose up frontend
```

## 📖 Documentation

- **Component Usage**: `src/components/analytics/README.md`
- **Docker Setup**: `src/components/analytics/DOCKER_SETUP.md`
- **Quick Reference**: `src/components/analytics/QUICK_REFERENCE.md`
- **This Summary**: `ANALYTICS_SETUP_COMPLETE.md`

## ✨ Summary

You now have:
- ✅ Complete visitor analytics components
- ✅ Docker + Yarn integration
- ✅ WebSocket real-time updates
- ✅ REST API integration
- ✅ Automated setup script
- ✅ Comprehensive documentation
- ✅ Ready for integration

**Components are complete but NOT integrated into your main app yet.**

When you're ready to integrate, simply:
1. Import the dashboard: `import { VisitorAnalyticsDashboard } from './components/analytics';`
2. Add to your admin page
3. Add permission checks
4. Test with real data

Everything is configured for your Docker + Yarn environment! 🎉
