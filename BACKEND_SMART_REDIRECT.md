# Backend-Powered Smart Redirect System

## Overview

The smart redirect system now uses **backend session data** instead of localStorage to determine where to redirect users after login. This is more reliable and secure.

## How It Works

### 1. Page Visit Tracking

When users navigate through the app, page visits are tracked in the `UserEvent` model:

```python
# POST /api/auth/update-last-visited/
{
    "url": "/municipality/sherbrooke/accueil"
}
```

Creates a `UserEvent` with:
- `event_type`: `'profile_view'`
- `metadata.url`: The visited URL
- `metadata.timestamp`: Visit timestamp
- `session`: Linked to current UserSession (via JWT)

### 2. Login Response Enhancement

When user logs in, the backend:
1. Queries the most recent `UserEvent` with a URL in metadata (last 7 days)
2. Includes this data in the login response:

```json
{
    "session": {
        "session_id": "abc123...",
        "last_visited_url": "/municipality/sherbrooke/accueil",
        "last_visited_time": "2025-10-05T14:30:00Z",
        "reused": false
    }
}
```

### 3. Frontend Smart Redirect

The frontend receives the session data and decides:

```javascript
if (result.session?.last_visited_url) {
    const timeSinceVisit = (Date.now() - new Date(lastVisitedTime)) / 1000 / 60;
    
    if (timeSinceVisit < 30) {
        // Recent session - continue where they left off
        redirectUrl = result.session.last_visited_url;
    } else {
        // Old session - go to home division
        redirectUrl = userHomeUrl;
    }
} else {
    // No previous session data - go to home
    redirectUrl = userHomeUrl;
}
```

## Benefits Over LocalStorage

1. **Cross-Device**: Works across different devices/browsers
2. **Server-Side Truth**: Backend controls the logic
3. **Security**: Can't be manipulated by client
4. **Analytics**: Page visits are logged for analytics
5. **No localStorage Cleanup**: No stale data issues

## Implementation Details

### Backend Endpoint

**Track Page Visit:**
```python
# accounts/jwt_views.py
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_last_visited_url(request):
    """Track page visit by creating UserEvent with URL metadata"""
    url = request.data.get('url')
    
    UserEvent.objects.create(
        user=profile,
        session=session,
        event_type='profile_view',
        metadata={'url': url, 'timestamp': timezone.now().isoformat()},
        success=True
    )
```

**Login Enhancement:**
```python
# In login_with_verification_check()
recent_event = UserEvent.objects.filter(
    user=profile,
    created_at__gte=recent_cutoff,
    metadata__has_key='url'
).order_by('-created_at').first()

if recent_event:
    last_visited_url = recent_event.metadata['url']
    last_visited_time = recent_event.created_at
```

### Frontend Hook

**Auto-Tracking Hook:**
```javascript
// hooks/usePageTracking.js
export const usePageTracking = (divisionData = null) => {
    const location = useLocation();
    
    useEffect(() => {
        // Skip login/register pages
        const skipPages = ['/login', '/register', '/'];
        if (skipPages.includes(location.pathname)) return;
        
        // Track with backend
        apiService.updateLastVisitedUrl(location.pathname);
    }, [location.pathname]);
};
```

**Usage in Components:**
```javascript
// In MunicipalityDashboard.js
import usePageTracking from '../hooks/usePageTracking';

function MunicipalityDashboard() {
    usePageTracking(divisionData);  // Auto-tracks page visits
    // ... rest of component
}
```

## Configuration

### Session Timeout
```javascript
// Default: 30 minutes
const SESSION_TIMEOUT_MINUTES = 30;
```

If time since last visit > 30 minutes:
- Redirect to user's home division

If time since last visit < 30 minutes:
- Continue to last visited page

### Event Cleanup

Old UserEvents can be cleaned up:
```python
# Delete events older than 30 days
UserEvent.objects.filter(
    event_type='profile_view',
    created_at__lt=timezone.now() - timedelta(days=30)
).delete()
```

## Testing

### Manual Test

1. **Login and navigate:**
   ```
   - Login as user with municipality
   - Navigate to /municipality/sherbrooke/polls
   - Logout
   ```

2. **Test recent session (< 30 min):**
   ```
   - Login again within 30 minutes
   - Should redirect to /municipality/sherbrooke/polls
   ```

3. **Test old session (> 30 min):**
   ```
   - Wait 31+ minutes
   - Login again
   - Should redirect to user's home division
   ```

### Check Backend Logs

```bash
# Watch for tracking logs
docker compose logs -f backend | grep "Tracked page visit"

# Check UserEvents in database
python manage.py shell
>>> from accounts.models import UserEvent
>>> UserEvent.objects.filter(event_type='profile_view').order_by('-created_at')[:5]
```

### API Test

```bash
# Track page visit
curl -X POST http://localhost:8000/api/auth/update-last-visited/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "/municipality/sherbrooke/accueil"}'

# Login and check response
curl -X POST http://localhost:8000/api/auth/login-with-verification-check/ \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "testuser",
    "password": "testpass123",
    "remember_me": false
  }' | jq '.session'
```

## Fallback Mechanism

If backend data is unavailable, the system falls back to localStorage:

```javascript
if (result.session?.last_visited_url) {
    // Use backend data (preferred)
    redirectUrl = calculateFromBackend();
} else {
    // Fallback to localStorage
    const smartRedirect = getSmartRedirectUrl(userHomeUrl);
    redirectUrl = smartRedirect.url;
}
```

## Migration from localStorage

No migration needed! The system works immediately:
- New logins use backend data
- Missing backend data falls back to localStorage
- Over time, all users will have backend data

## Troubleshooting

### Not Redirecting to Last Page

Check:
1. Page tracking is working: Look for `UserEvent` records
2. Time calculation: Verify `timeSinceVisit < 30` logic
3. Backend response: Check `session.last_visited_url` in login response

### Events Not Created

Check:
1. User is authenticated
2. JWT token has valid `sid` (session ID)
3. URL is not in skip list (`/login`, `/register`, etc.)

### Wrong URL Stored

Check:
1. `location.pathname` is correct
2. Event metadata has correct URL format
3. Most recent event is being retrieved

## Performance

- **Page Tracking**: Non-blocking, fire-and-forget
- **Login Query**: Single DB query for recent events
- **Throttling**: Max 1 update per 5 seconds per user

## Security

- Only authenticated users can track visits
- URLs are validated server-side
- Session ID must match JWT token
- Old events are automatically cleaned up
