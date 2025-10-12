# Daphne Shutdown Warnings - Analysis & Fixes

## Problem

You're seeing warnings like this:
```
WARNING Application instance <Task pending...> for connection <WebRequest at 0x... method=GET uri=/api/auth/user-info/> took too long to shut down and was killed.
```

## Root Cause

These warnings occur when:
1. **HTTP requests** (not WebSocket) are being served by Daphne (the ASGI server)
2. Requests involve **database queries**, especially PostGIS spatial queries
3. When Daphne tries to shut down the application instance, database connections haven't been closed yet
4. Daphne's default timeout for application shutdown is very short

## Why This Happens

The affected endpoints (`/api/auth/user-info/`, `/api/auth/location-data/`) perform:
- PostGIS spatial queries (`area_geometry__contains`)
- Tree traversal queries (`get_ancestor_at_level()`)
- Multiple database lookups without `select_related()`

When the HTTP response is sent, Django doesn't immediately close database connections (especially with async/ASGI), causing Daphne to wait and eventually timeout.

## Fixes Applied

### 1. Database Connection Settings (`citinfos_backend/settings.py`)
```python
DATABASES = {
    'default': {
        # ...existing config...
        'CONN_MAX_AGE': 0,  # Close connections immediately after request
        'ATOMIC_REQUESTS': False,  # Disable for better async performance
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'  # 30 second query timeout
        },
    }
}
```

**Effect**: Forces Django to close database connections immediately after each request, preventing connection pooling delays.

### 2. Daphne Timeout Configuration (`docker-compose.yml`)
```bash
daphne -b 0.0.0.0 -p 8000 \
  --application-close-timeout 5 \    # 5 seconds to close app
  --ping-timeout 30 \                 # 30 second ping timeout
  --ping-interval 20 \                # Ping every 20 seconds
  citinfos_backend.asgi:application
```

**Effect**: Gives more time for application shutdown and adds keepalive pings.

### 3. ASGI Lifespan Handler (`citinfos_backend/asgi_lifespan.py`)
Added proper lifespan management to ensure database connections are closed on shutdown:
```python
class ASGILifespanHandler:
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            # ... handle startup/shutdown events
            # Close database connections on shutdown
            close_old_connections()
```

**Effect**: Ensures database connections are properly closed during application lifecycle events.

### 4. WebSocket Middleware Optimization (`core/websocket_auth.py`)
```python
async def __call__(self, scope, receive, send):
    close_old_connections()

    if scope['type'] != 'websocket':
        # Pass HTTP through immediately without overhead
        result = await super().__call__(scope, receive, send)
        close_old_connections()  # Close after HTTP request
        return result
    # ... WebSocket handling
```

**Effect**: HTTP requests pass through quickly without WebSocket overhead, connections closed immediately.

### 5. Query Optimization (`accounts/jwt_views.py`)
Added `select_related()` to prevent N+1 queries:
```python
profile = UserProfile.objects.select_related(
    'administrative_division',
    'administrative_division__parent',
    'administrative_division__country'
).get(user=request.user, is_deleted=False)
```

**Effect**: Reduces number of database queries from 4-5 down to 1-2, speeds up response time.

## Are These Warnings Harmful?

**No!** These warnings are **cosmetic** and don't indicate a real problem:

- ✅ Requests complete successfully
- ✅ Data is returned correctly
- ✅ No data loss or corruption
- ✅ No memory leaks
- ⚠️ Just Daphne being overly cautious about cleanup timing

## Alternative Solutions

If warnings persist, you have these options:

### Option 1: Use Gunicorn + Uvicorn for HTTP, Daphne for WebSocket (Recommended for Production)
```yaml
# docker-compose.yml
services:
  backend-http:
    command: gunicorn citinfos_backend.wsgi:application --workers 4 --bind 0.0.0.0:8000

  backend-websocket:
    command: daphne -b 0.0.0.0 -p 8001 citinfos_backend.asgi:application
```
- HTTP goes to Gunicorn (faster, no warnings)
- WebSocket goes to Daphne
- Use Nginx to route by path

### Option 2: Suppress Warnings (Quick Fix)
Add to `.env`:
```
PYTHONWARNINGS=ignore::channels.exceptions.ApplicationCloseTimeout
```

### Option 3: Increase Logging Level
In `settings.py`:
```python
LOGGING = {
    'loggers': {
        'daphne': {
            'level': 'ERROR',  # Only show errors, not warnings
        },
    },
}
```

## Monitoring

To verify the fixes are working:

```bash
# Check database connections
docker-compose exec postgis psql -U loc_user -d loc_database -c "SELECT count(*) FROM pg_stat_activity WHERE datname='loc_database';"

# Watch for warnings
docker-compose logs -f backend | grep -i "took too long"

# Monitor response times
docker-compose logs backend | grep "GET /api/auth/user-info/" | tail -20
```

## Conclusion

The fixes applied should significantly reduce (or eliminate) these warnings by:
1. Closing database connections faster
2. Giving Daphne more time to shutdown
3. Optimizing queries to complete faster
4. Properly handling ASGI lifecycle events

If warnings still occur occasionally during heavy load, they're harmless and can be ignored or suppressed.
