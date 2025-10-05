# Remember Me Functionality - Implementation Guide

## Overview
This document explains the secure "Remember Me" implementation that balances security and user convenience.

## How It Works

### Token Lifetime Strategy

#### Normal Login (without "Remember Me")
- **Access Token**: 5 minutes (short-lived for security)
- **Refresh Token**: 1 day
- **Session**: 4 hours

#### "Remember Me" Login (persistent=True)
- **Access Token**: 5 minutes (unchanged - still secure!)
- **Refresh Token**: 30 days (extended)
- **Session**: 30 days (extended)

### Security Design

**Why keep Access Tokens short?**
- Access tokens are used for every API request
- Short-lived tokens minimize the damage if stolen
- 5 minutes is enough for active usage between refreshes

**How does "Remember Me" work then?**
1. User logs in with `remember_me: true`
2. Backend creates a 30-day session and refresh token
3. Access token still expires in 5 minutes
4. Frontend automatically uses the refresh token to get new access tokens
5. User stays logged in for 30 days without re-entering password

### Configuration

**Environment Variables (.env)**
```bash
# Normal session duration
SESSION_DURATION_HOURS=4

# "Remember Me" session duration
PERSISTENT_SESSION_DURATION_DAYS=30

# Access token (always short)
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=5

# Refresh token (normal login)
JWT_REFRESH_TOKEN_LIFETIME_DAYS=1
```

### Implementation Details

#### Backend Changes

1. **Session Creation** (`core/session_manager.py`)
   - Checks `persistent` flag
   - Creates 30-day session if `persistent=True`
   - Creates 4-hour session if `persistent=False`

2. **Session Extension** (`accounts/models.py`)
   - Extends sessions based on `persistent` flag
   - Persistent sessions: +30 days
   - Normal sessions: +4 hours

3. **JWT Token Creation** (`accounts/jwt_views.py`)
   - Extends refresh token to 30 days for persistent sessions
   - Access token remains 5 minutes (security)
   - Embeds session ID in both tokens

4. **Session Reuse** (`accounts/jwt_views.py`)
   - Uses `fast_login_with_session_reuse()` instead of creating duplicates
   - Reuses existing session from same device
   - Updates `persistent` flag if needed

#### Frontend Implementation

The frontend should:
1. Provide a "Remember Me" checkbox on login
2. Send `remember_me: true` in login request
3. Store refresh token securely (httpOnly cookie or secure localStorage)
4. Automatically refresh access token when it expires (every 5 minutes)
5. Check session validity periodically

**Example Login Request:**
```javascript
const response = await axios.post('/api/auth/login/', {
  username: 'user@example.com',
  password: 'password123',
  remember_me: true,  // This enables 30-day session
  // Include device fingerprint data for session tracking
  screen_resolution: '1920x1080',
  timezone: 'America/New_York',
  // ... other fingerprint data
});
```

### Token Refresh Flow

```
1. User logs in with remember_me=true
   ↓
2. Backend creates:
   - Access token (5 min)
   - Refresh token (30 days)
   - Session (30 days)
   ↓
3. Frontend uses access token for API calls
   ↓
4. After 5 minutes, access token expires
   ↓
5. Frontend sends refresh token to /api/auth/token/refresh/
   ↓
6. Backend validates:
   - Refresh token (valid for 30 days)
   - Session (valid for 30 days)
   ↓
7. Backend returns new access token (5 min)
   ↓
8. Repeat steps 3-7 for up to 30 days
```

### Session Management

**Session Reuse Logic:**
- Uses device fingerprinting (User-Agent, Accept headers, etc.)
- Finds existing active session from same device
- Reuses session instead of creating duplicate
- Extends session expiration if needed

**Session Cleanup:**
- Old sessions automatically marked as expired
- Database cleanup runs periodically
- Users can manually end sessions via API

### Security Considerations

1. **Short Access Tokens**: Even with "Remember Me", access tokens expire quickly
2. **Session Validation**: Every token refresh validates the session
3. **Device Fingerprinting**: Detects and reuses sessions from same device
4. **Token Blacklisting**: Old refresh tokens are blacklisted on rotation
5. **HTTPS Required**: Use HTTPS in production for secure token transmission

### Testing

**Test Normal Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "password123",
    "remember_me": false
  }'
```

**Test "Remember Me" Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "password123",
    "remember_me": true
  }'
```

**Verify Session Duration:**
```python
# Django shell
from accounts.models import UserSession

# Get latest session
session = UserSession.objects.filter(is_active=True).latest('started_at')
print(f"Persistent: {session.persistent}")
print(f"Expires: {session.expires_at}")
print(f"Duration: {session.expires_at - session.started_at}")
```

### Troubleshooting

**Multiple sessions from same device?**
- Check `fast_login_with_session_reuse` is being called
- Verify device fingerprint is being generated correctly
- Review session reuse logic in `core/session_manager.py`

**Session expires too quickly?**
- Check `PERSISTENT_SESSION_DURATION_DAYS` in `.env`
- Verify `persistent` flag is set in database
- Check session extension logic

**Token refresh fails?**
- Verify session is still active
- Check refresh token hasn't expired
- Ensure session ID matches between token and database

## Summary

The "Remember Me" implementation:
- ✅ Keeps access tokens short (5 min) for security
- ✅ Extends refresh tokens (30 days) for convenience
- ✅ Extends sessions (30 days) to match refresh token
- ✅ Reuses sessions from same device (no duplicates)
- ✅ Configurable via environment variables
- ✅ Secure and user-friendly
