# Visitor Analytics - Docker Setup Guide

This guide is specific to the Docker + Yarn environment.

## Quick Start

### 1. Install Dependencies

From your host machine (recommended):
```bash
yarn add chart.js react-chartjs-2
```

Or inside the container:
```bash
docker-compose exec frontend yarn add chart.js react-chartjs-2
```

### 2. Verify Installation

Check that the packages appear in `package.json`:
```bash
docker-compose exec frontend yarn list --pattern "chart.js|react-chartjs-2"
```

### 3. Restart Frontend Container (if needed)

If hot reload doesn't pick up the new dependencies:
```bash
docker-compose restart frontend
```

## WebSocket Configuration

### Development (Docker)

The WebSocket URL needs to point to your backend container:

```javascript
// RealtimeVisitorCounter.jsx
const wsUrl = `ws://backend:8000/ws/analytics/visitors/`;
```

However, since you're accessing from the browser (not from inside Docker), use:

```javascript
const wsUrl = `ws://localhost:8000/ws/analytics/visitors/`;
```

### Production

For production, use secure WebSocket:

```javascript
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsHost = window.location.host.replace(':3000', ':8000'); // Adjust port
const wsUrl = `${wsProtocol}//${wsHost}/ws/analytics/visitors/`;
```

Or use environment variables:

```javascript
// .env
REACT_APP_WS_URL=ws://localhost:8000

// In component
const wsUrl = `${process.env.REACT_APP_WS_URL}/ws/analytics/visitors/`;
```

## Backend Configuration

### Ensure Daphne is Running

Your `docker-compose.yml` already has Daphne configured for WebSocket support:

```yaml
backend:
  command: sh -c "... && daphne -b 0.0.0.0 -p 8000 ... citinfos_backend.asgi:application"
```

### Verify WebSocket Endpoint

Test the WebSocket connection:

```bash
# Using wscat (install with: yarn global add wscat)
docker-compose exec frontend npx wscat -c ws://backend:8000/ws/analytics/visitors/

# Or from host
wscat -c ws://localhost:8000/ws/analytics/visitors/
```

Expected response:
```json
{"type": "visitor_count", "count": 0}
```

## Testing Components

### 1. Create Test Page

Create a test page to verify components work:

```javascript
// src/pages/AnalyticsTest.jsx
import React from 'react';
import { VisitorAnalyticsDashboard } from '../components/analytics';

function AnalyticsTest() {
    return (
        <div style={{ padding: '20px' }}>
            <h1>Analytics Dashboard Test</h1>
            <VisitorAnalyticsDashboard />
        </div>
    );
}

export default AnalyticsTest;
```

### 2. Add Route (Temporary)

```javascript
// src/App.js
import AnalyticsTest from './pages/AnalyticsTest';

// Inside your router
<Route path="/analytics-test" element={<AnalyticsTest />} />
```

### 3. Access in Browser

```
http://localhost:3000/analytics-test
```

### 4. Check Browser Console

Look for:
- ✅ No Chart.js errors
- ✅ API calls to backend
- ✅ WebSocket connection established
- ❌ Any CORS errors
- ❌ Any network errors

## Common Issues & Solutions

### Issue: Chart.js Not Loading

**Error:** `Module not found: Can't resolve 'chart.js'`

**Solution:**
```bash
# Rebuild frontend container
docker-compose down
docker-compose up --build frontend
```

### Issue: WebSocket Connection Failed

**Error:** `WebSocket connection to 'ws://localhost:8000/ws/analytics/visitors/' failed`

**Check:**
1. Backend container is running: `docker-compose ps backend`
2. Daphne is running: `docker-compose logs backend | grep daphne`
3. Port 8000 is exposed in docker-compose.yml

**Solution:**
```bash
# Check backend logs
docker-compose logs -f backend

# Restart backend
docker-compose restart backend
```

### Issue: CORS Errors

**Error:** `Access to XMLHttpRequest at 'http://localhost:8000/api/...' from origin 'http://localhost:3000' has been blocked by CORS`

**Solution:** Update `citinfos_backend/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://frontend:3000',
]

CORS_ALLOW_CREDENTIALS = True
```

### Issue: Hot Reload Not Working

**Error:** Changes to components not reflected in browser

**Check `Dockerfile.frontend`:**
```dockerfile
ENV CHOKIDAR_USEPOLLING=true \
    WATCHPACK_POLLING=true
```

**Solution:**
```bash
# Rebuild with no cache
docker-compose build --no-cache frontend
docker-compose up frontend
```

### Issue: API Returns 403 Forbidden

**Error:** API endpoints return permission denied

**Cause:** Visitor analytics requires moderator/admin permissions

**Solution:** Create admin user:
```bash
docker-compose exec backend python manage.py createsuperuser
```

Then login with those credentials before accessing analytics.

## Development Workflow

### 1. Edit Components

Edit files on your host machine (VS Code, etc.). Changes sync via volume mounting:

```yaml
# docker-compose.yml
frontend:
  volumes:
    - ./src:/app/src  # ← Auto-sync
```

### 2. Watch Logs

Monitor both frontend and backend:

```bash
# Terminal 1: Frontend logs
docker-compose logs -f frontend

# Terminal 2: Backend logs
docker-compose logs -f backend

# Terminal 3: Celery logs (for async tasks)
docker-compose logs -f celery
```

### 3. Test API Endpoints

```bash
# Get visitor stats (requires authentication)
docker-compose exec backend python manage.py shell

>>> from analytics.utils import VisitorAnalytics
>>> stats = VisitorAnalytics.get_unique_visitors()
>>> print(stats)
```

Or use curl:
```bash
# Login first to get token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  | jq -r '.access')

# Get visitor stats
curl -X GET http://localhost:8000/api/analytics/visitors/ \
  -H "Authorization: Bearer $TOKEN" \
  | jq
```

### 4. Debug WebSocket

```bash
# Inside frontend container
docker-compose exec frontend sh

# Install wscat
yarn global add wscat

# Test connection
wscat -c ws://backend:8000/ws/analytics/visitors/
```

## Environment Variables

Create or update `.env`:

```bash
# Frontend API URL
REACT_APP_API_URL=http://localhost:8000

# WebSocket URL
REACT_APP_WS_URL=ws://localhost:8000

# Enable debug mode
REACT_APP_DEBUG=true
```

Use in components:

```javascript
const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
```

## Building for Production

### 1. Update docker-compose.yml for Production

```yaml
frontend:
  environment:
    - NODE_ENV=production
  command: yarn build && yarn global add serve && serve -s build -l 3000
```

### 2. Build Production Image

```bash
docker-compose build frontend
```

### 3. Update WebSocket URLs

Use environment-based configuration:

```javascript
const getWebSocketUrl = () => {
    if (process.env.NODE_ENV === 'production') {
        return `wss://${window.location.host}/ws/analytics/visitors/`;
    }
    return 'ws://localhost:8000/ws/analytics/visitors/';
};
```

## Useful Commands

```bash
# Install package
yarn add <package>

# Install dev dependency
yarn add -D <package>

# Remove package
yarn remove <package>

# Check for outdated packages
yarn outdated

# Update packages
yarn upgrade

# Clean install
docker-compose down -v
docker-compose up --build

# Shell into frontend container
docker-compose exec frontend sh

# Shell into backend container
docker-compose exec backend sh

# View all containers
docker-compose ps

# Stop all containers
docker-compose down

# Remove volumes (careful!)
docker-compose down -v
```

## Performance Tips

### 1. Use Production Build

For better performance:
```bash
docker-compose exec frontend yarn build
```

### 2. Enable Compression

Add to backend settings:
```python
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # Add this
    # ... other middleware
]
```

### 3. Cache API Responses

Use Redis for caching (already configured in docker-compose.yml):
```python
# In analytics/views.py
from django.core.cache import cache

class VisitorAnalyticsView(APIView):
    def get(self, request):
        cache_key = f'analytics_{params}'
        data = cache.get(cache_key)
        if not data:
            data = VisitorAnalytics.get_unique_visitors()
            cache.set(cache_key, data, 300)  # 5 min cache
        return Response(data)
```

## Next Steps

1. ✅ Install Chart.js dependencies
2. ✅ Test components with real API data
3. ✅ Verify WebSocket connections
4. 🔲 Add permission checks
5. 🔲 Integrate into admin/moderator pages
6. 🔲 Add error boundaries
7. 🔲 Write component tests
8. 🔲 Update production config

## Support

If you encounter issues:

1. Check container logs: `docker-compose logs -f`
2. Verify all containers are running: `docker-compose ps`
3. Check network connectivity between containers
4. Ensure volumes are properly mounted
5. Verify environment variables are set correctly
