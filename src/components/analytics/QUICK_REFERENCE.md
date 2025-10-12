# Visitor Analytics - Quick Reference

## 🚀 Quick Setup (Docker + Yarn)

```bash
# Run the automated setup script
./scripts/setup_analytics_components.sh

# Or manually:
docker-compose exec frontend yarn add chart.js react-chartjs-2
```

## 📦 Components

### Import
```javascript
import {
    VisitorAnalyticsDashboard,
    VisitorStatsCard,
    VisitorTrendsChart,
    DivisionBreakdown,
    RealtimeVisitorCounter
} from './components/analytics';
```

### Basic Usage
```javascript
// Full dashboard
<VisitorAnalyticsDashboard communityId="optional-uuid" />

// Individual components
<VisitorStatsCard title="Visitors" value={123} change={15} />
<VisitorTrendsChart data={trendsData} type="line" />
<DivisionBreakdown data={divisionData} />
<RealtimeVisitorCounter />
```

## 🔌 API Endpoints

### REST API (Requires Auth)
```
GET /api/analytics/visitors/              # Main stats
GET /api/analytics/visitors/today/        # Today's stats
GET /api/analytics/visitors/weekly/       # Last 7 days
GET /api/analytics/visitors/monthly/      # Last 30 days
GET /api/analytics/division-breakdown/    # By location
GET /api/analytics/trends/                # Time series
GET /api/analytics/conversions/           # Anonymous→Auth
GET /api/analytics/demographics/          # User demographics
GET /api/analytics/realtime/              # Current count
GET /api/analytics/growth/                # Growth stats
GET /api/analytics/export/                # CSV export
```

### WebSocket (Real-time)
```
ws://localhost:8000/ws/analytics/visitors/
ws://localhost:8000/ws/analytics/dashboard/?community_id={id}
```

## 🐳 Docker Commands

```bash
# Install dependencies
docker-compose exec frontend yarn add chart.js react-chartjs-2

# Rebuild containers
docker-compose build frontend

# View logs
docker-compose logs -f frontend
docker-compose logs -f backend

# Restart containers
docker-compose restart frontend
docker-compose restart backend

# Shell into container
docker-compose exec frontend sh
docker-compose exec backend sh
```

## 🧪 Testing

### Test WebSocket
```bash
# Install wscat
yarn global add wscat

# Connect
wscat -c ws://localhost:8000/ws/analytics/visitors/
```

### Test API (with curl)
```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  | jq -r '.access')

# Get stats
curl -X GET http://localhost:8000/api/analytics/visitors/ \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Test Components
```javascript
// Create test page: src/pages/AnalyticsTest.jsx
import { VisitorAnalyticsDashboard } from '../components/analytics';

function AnalyticsTest() {
    return <VisitorAnalyticsDashboard />;
}

// Add route
<Route path="/analytics-test" element={<AnalyticsTest />} />

// Visit: http://localhost:3000/analytics-test
```

## 🔧 Common Issues

### Chart.js not loading
```bash
docker-compose down
docker-compose up --build frontend
```

### WebSocket connection failed
```bash
# Check backend logs
docker-compose logs backend | grep -i websocket

# Verify Daphne is running
docker-compose logs backend | grep daphne
```

### CORS errors
```python
# citinfos_backend/settings.py
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
]
```

### Hot reload not working
```bash
# Check Dockerfile.frontend has:
ENV CHOKIDAR_USEPOLLING=true
ENV WATCHPACK_POLLING=true
```

## 📊 Data Format Examples

### Stats Response
```json
{
    "total_visitors": 1234,
    "authenticated_visitors": 800,
    "anonymous_visitors": 434,
    "conversion_rate": 64.8
}
```

### Trends Response
```json
{
    "labels": ["Mon", "Tue", "Wed"],
    "total": [100, 150, 200],
    "authenticated": [60, 90, 120],
    "anonymous": [40, 60, 80]
}
```

### Division Breakdown Response
```json
[
    {
        "division_id": "uuid",
        "division_name": "New York",
        "division_type": "City",
        "count": 1500
    }
]
```

### WebSocket Messages
```json
// Incoming
{"type": "visitor_count", "count": 42}
{"type": "visitor_joined", "visitor": {...}}
{"type": "visitor_left", "visitor": {...}}

// Outgoing
{"type": "request_count"}
```

## 🔐 Permissions

Components require moderator/admin access:

```javascript
import { useAuth } from './hooks/useAuth';

function Dashboard() {
    const { user } = useAuth();

    if (!user?.is_staff && !user?.is_moderator) {
        return <AccessDenied />;
    }

    return <VisitorAnalyticsDashboard />;
}
```

## 📁 File Structure

```
src/
├── components/analytics/
│   ├── VisitorAnalyticsDashboard.jsx
│   ├── VisitorAnalyticsDashboard.css
│   ├── VisitorStatsCard.jsx
│   ├── VisitorStatsCard.css
│   ├── VisitorTrendsChart.jsx
│   ├── VisitorTrendsChart.css
│   ├── DivisionBreakdown.jsx
│   ├── DivisionBreakdown.css
│   ├── RealtimeVisitorCounter.jsx
│   ├── RealtimeVisitorCounter.css
│   ├── index.js
│   ├── README.md
│   ├── DOCKER_SETUP.md
│   └── QUICK_REFERENCE.md (this file)
├── services/
│   └── visitorAnalyticsAPI.js
```

## 🎯 Next Steps

- [x] Install dependencies
- [ ] Test components
- [ ] Add to admin page
- [ ] Add permission checks
- [ ] Write tests
- [ ] Production config

## 📖 Full Documentation

- **Components**: `src/components/analytics/README.md`
- **Docker Setup**: `src/components/analytics/DOCKER_SETUP.md`
- **Backend API**: `analytics/README.md` (if exists)

## 🆘 Need Help?

1. Check container logs: `docker-compose logs -f`
2. Verify containers are running: `docker-compose ps`
3. Test API endpoints with curl
4. Check browser console for errors
5. Review documentation files
