# Authentication Integration - Migration Summary

## Overview
Successfully integrated authentication and WebSocket services for the new client using the existing `apiService` instead of creating duplicate authentication systems.

## Changes Made

### 1. WebSocket Service Integration (`src/services/notificationWebSocket.js`)

**Updated to use `apiService` instead of non-existent services:**
- ✅ Replaced `jwtAuthService` imports with `apiService`
- ✅ Replaced `tokenManager` with `apiService` token methods
- ✅ Updated `hasValidAuthentication()` to use `apiService.getAccessToken()`
- ✅ Added `isTokenExpired()` method for JWT validation
- ✅ Updated `redirectToLogin()` to use `apiService.clearTokens()`
- ✅ Updated `connect()` to use `apiService.getAccessToken()`
- ✅ Simplified `attemptTokenRefreshAndReconnect()` since apiService handles refresh automatically via interceptors
- ✅ Updated `scheduleReconnect()` to use `apiService.getAccessToken()`

**Key Features:**
- Uses same JWT tokens as HTTP API requests
- Automatically reconnects on token refresh
- Handles authentication failures gracefully
- Queues messages when disconnected
- Sends ping/pong to keep connection alive
- Supports WebSocket URL format: `ws://127.0.0.1:8000/ws/notifications/?token={token}&session_id={session_id}`

### 2. Authentication Hook Updates

**Updated `useJWTAuth.js` to use `apiService`:**
- ✅ Replaced `jwtAuthService` imports with `apiService`
- ✅ Updated all authentication methods to use `apiService`:
  - `login()` - uses `apiService.login()`
  - `register()` - uses `apiService.register()`
  - `logout()` - uses `apiService.logout()`
  - `verifyEmail()` - uses `apiService.verifyEmail()`
  - `resendVerificationCode()` - uses `apiService.resendVerificationCode()`
  - `refreshUser()` - uses `apiService.getCurrentUser()`
- ✅ Maintained WebSocket integration for notifications

**Note:** This hook exists for compatibility but is NOT used in the main app.

### 3. Component Updates

**Updated all components to use `useAuth` from `AuthContext`:**

1. **PostCreationModal.jsx**
   - Changed: `import { useJWTAuth } from '../hooks/useJWTAuth'`
   - To: `import { useAuth } from '../contexts/AuthContext'`
   - Changed: `const { user } = useJWTAuth()`
   - To: `const { user } = useAuth()`

2. **PostCard.jsx**
   - Changed: `import { useJWTAuth } from '../../hooks/useJWTAuth'`
   - To: `import { useAuth } from '../../contexts/AuthContext'`
   - Changed: `const { user, isAuthenticated } = useJWTAuth()`
   - To: `const { user, isAuthenticated } = useAuth()`

3. **RepostCard.jsx**
   - Changed: `import { useJWTAuth } from '../../hooks/useJWTAuth'`
   - To: `import { useAuth } from '../../contexts/AuthContext'`
   - Changed: `const { user, isAuthenticated } = useJWTAuth()`
   - To: `const { user, isAuthenticated } = useAuth()`

4. **ClickableAuthorName.jsx**
   - Changed: `import { useJWTAuth } from '../../hooks/useJWTAuth'`
   - To: `import { useAuth } from '../../contexts/AuthContext'`
   - Changed: `const { user: currentUser } = useJWTAuth()`
   - To: `const { user: currentUser } = useAuth()`

## Architecture

### Current Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                         App.js                              │
│                    (Entry Point)                            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                     AuthProvider                            │
│              (from AuthContext.js)                          │
│  - Manages user state                                       │
│  - Provides useAuth() hook                                  │
│  - Uses apiService for all API calls                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                     apiService                              │
│              (from apiService.js)                           │
│  - Axios instance with interceptors                         │
│  - JWT token management (localStorage)                      │
│  - Automatic token refresh via middleware headers           │
│  - Session management via cookies                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ├──────────────────┐
                  ▼                  ▼
┌──────────────────────────┐  ┌────────────────────────────┐
│   HTTP API Requests      │  │  notificationWebSocket     │
│   (with JWT in header)   │  │  (uses same JWT token)     │
└──────────────────────────┘  └────────────────────────────┘
```

### Token Storage
- **Access Token**: `localStorage.getItem('access_token')`
- **Refresh Token**: `localStorage.getItem('refresh_token')`
- **User Data**: `localStorage.getItem('currentUser')`

### Token Refresh Strategy
1. **HTTP Requests**: Automatic refresh via apiService interceptors
   - Backend middleware sends new tokens in response headers
   - `X-New-Access-Token` and `X-New-Refresh-Token` headers
   - Interceptor automatically updates localStorage

2. **WebSocket**: Reconnects when HTTP requests get new tokens
   - Can call `notificationWebSocket.reconnectWithNewToken()`
   - Automatically reconnects on auth failures with exponential backoff

## Benefits of This Architecture

1. **Single Source of Truth**: All authentication logic in `apiService`
2. **No Duplication**: Reuses existing authentication infrastructure
3. **Automatic Token Refresh**: Handled transparently by middleware
4. **WebSocket Integration**: Uses same JWT tokens as HTTP requests
5. **Session Support**: Backend can maintain sessions via cookies
6. **Error Handling**: Centralized in apiService interceptors

## Files Modified

### New/Copied Files:
- `src/services/notificationWebSocket.js` - WebSocket service (updated)
- `src/hooks/useJWTAuth.js` - Compatibility hook (not used, but available)

### Updated Files:
- `src/components/PostCreationModal.jsx` - Use `useAuth` instead of `useJWTAuth`
- `src/components/social/PostCard.jsx` - Use `useAuth` instead of `useJWTAuth`
- `src/components/social/RepostCard.jsx` - Use `useAuth` instead of `useJWTAuth`
- `src/components/ui/ClickableAuthorName.jsx` - Use `useAuth` instead of `useJWTAuth`

### Existing Files (No Changes Required):
- `src/contexts/AuthContext.js` - Already uses `apiService`
- `src/services/apiService.js` - Already handles JWT auth
- `src/App.js` - Already wrapped with `AuthProvider`

## Testing Checklist

- [x] Components compile without errors
- [ ] Login flow works correctly
- [ ] Logout clears tokens and user state
- [ ] Token refresh happens automatically
- [ ] WebSocket connects with JWT token
- [ ] WebSocket reconnects after token refresh
- [ ] Protected routes redirect to login
- [ ] User data persists across page reloads

## Next Steps

1. Test WebSocket connection in development
2. Verify token refresh mechanism
3. Test authentication flow end-to-end
4. Monitor WebSocket reconnection behavior
5. Update any remaining components that need authentication

## Notes

- The `useJWTAuth` hook still exists for backward compatibility but is NOT used in the app
- All components should use `useAuth` from `AuthContext`
- WebSocket service is ready but needs to be integrated into a NotificationContext if needed
- Backend WebSocket endpoint: `ws://127.0.0.1:8000/ws/notifications/`
