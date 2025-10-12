# Real-time Notification Integration Guide

## Overview

This document describes the real-time notification system integrated into the Citinfos application. The system uses WebSocket connections for real-time notifications and provides a complete notification management context.

**Date Completed:** October 9, 2025

---

## Architecture

### Components

1. **NotificationContext** (`src/contexts/NotificationContext.jsx`)
   - Global state management for notifications
   - WebSocket connection lifecycle management
   - API integration for notification history
   - Action creators for notification operations

2. **NotificationWebSocket** (`src/services/notificationWebSocket.js`)
   - WebSocket service with JWT authentication
   - Automatic reconnection with exponential backoff
   - Message queuing when disconnected
   - Ping/pong keep-alive mechanism

3. **NotificationBadge** (`src/components/NotificationBadge.jsx`)
   - Simple badge component for displaying unread count
   - Connection status indicator
   - Quick actions (mark all as read, reconnect)

4. **TopBar Integration** (`src/components/TopBar.js`)
   - Real-time notification bell with unread count
   - WebSocket connection status indicator (green dot = connected, gray dot = disconnected)
   - Uses existing notification UI infrastructure

---

## Authentication Integration

The notification system uses the **existing authentication infrastructure**:

- **apiService** (`src/services/apiService.js`) - JWT token management
- **AuthContext** (`src/contexts/AuthContext.js`) - Main auth provider with `useAuth()` hook
- **notificationWebSocket** - Updated to use `apiService` for JWT tokens

### Migration from Old Client

When copying from `backup_client`, the following changes were made:

| Old Client | New Client |
|------------|------------|
| `jwtAuthService.getToken()` | `apiService.getAccessToken()` |
| `jwtAuthService.clearTokens()` | `apiService.clearTokens()` |
| `useJWTAuth()` | `useAuth()` from `AuthContext` |
| `import api from 'axiosConfig'` | `apiService.api` |
| `/notifications/` endpoints | `/api/notifications/` endpoints |

---

## Usage

### 1. Using the NotificationContext

```javascript
import { useNotifications } from '../contexts/NotificationContext';

function MyComponent() {
  const {
    notifications,        // Array of notification objects
    unreadCount,          // Number of unread notifications
    isConnected,          // WebSocket connection status
    isConnecting,         // WebSocket connecting state
    connectionFailed,     // Connection failed flag
    settings,             // Notification settings
    actions               // Action creators
  } = useNotifications();

  // Mark a notification as read
  const handleMarkAsRead = async (notificationId) => {
    await actions.markAsRead(notificationId);
  };

  // Mark all notifications as read
  const handleMarkAllAsRead = async () => {
    await actions.markAllAsRead();
  };

  // Remove a notification from local state
  const handleRemove = (notificationId) => {
    actions.removeNotification(notificationId);
  };

  // Fetch notification history (paginated)
  const loadMore = async (page = 1) => {
    await actions.requestHistory(page, 20);
  };

  // Update notification settings
  const updateSettings = (newSettings) => {
    actions.updateSettings({
      showToasts: true,
      playSound: false,
      maxToasts: 5,
      toastDuration: 5000,
      ...newSettings
    });
  };

  // Manually reconnect WebSocket
  const handleReconnect = () => {
    actions.reconnect();
  };

  return (
    <div>
      <p>Unread: {unreadCount}</p>
      <p>Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
      {notifications.map(notif => (
        <div key={notif.id}>
          <h4>{notif.title}</h4>
          <p>{notif.message}</p>
          <button onClick={() => handleMarkAsRead(notif.id)}>
            Mark as read
          </button>
        </div>
      ))}
    </div>
  );
}
```

### 2. Notification Object Structure

```javascript
{
  id: "uuid-or-generated-id",
  title: "Notification Title",
  message: "Notification message content",
  notification_type: "system|social|community|equipment|messaging|poll|ai_conversation|analytics|moderation",
  priority: "low|medium|high|urgent",
  read: false,
  timestamp: "2025-10-09T10:30:00Z",
  sender: {
    id: 123,
    username: "username",
    display_name: "Display Name"
  },
  extra_data: {
    // Additional context-specific data
    post_id: 456,
    community_id: 789,
    // etc.
  }
}
```

### 3. WebSocket Message Types

The NotificationContext handles these WebSocket message types:

- `connection_established` - WebSocket connection opened
- `connection_lost` - WebSocket connection closed
- `connection_failed` - WebSocket connection failed
- `token_renewed` - JWT token was refreshed
- `notification` - New notification received
- `notification_read` - Notification marked as read
- `notifications_history` - Notification history response
- `unread_count` - Updated unread count

Notification-specific types (all handled the same way):
- `system_notification`
- `social_notification`
- `community_notification`
- `equipment_notification`
- `messaging_notification`
- `poll_notification`
- `ai_conversation_notification`
- `analytics_notification`
- `moderation_notification`

---

## API Endpoints

### GET /notifications/
Fetch notifications (paginated)

**Note:** When using `apiService`, do NOT include `/api/` prefix as it's already in the base URL.

**Query Parameters:**
- `limit` (int) - Number of notifications to return (default: 50)
- `page` (int) - Page number for pagination

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "title": "New Post",
      "message": "Someone posted in your community",
      "notification_type": "social",
      "priority": "medium",
      "is_read": false,
      "created_at": "2025-10-09T10:30:00Z",
      "sender": {
        "id": 123,
        "username": "username",
        "display_name": "Display Name"
      },
      "extra_data": {}
    }
  ],
  "count": 100,
  "next": "/api/notifications/?page=2",
  "previous": null
}
```

### POST /notifications/mark-read/
Mark notifications as read

**Request Body:**
```json
{
  "notification_ids": ["uuid1", "uuid2"]  // Empty array = mark all as read
}
```

**Response:**
```json
{
  "status": "success",
  "marked_read": 2
}
```

---

## WebSocket Connection

### Connection URL
```
wss://yourdomain.com/ws/notifications/
```

### Authentication
The WebSocket uses **dual authentication**:
1. **JWT Token** - Sent as query parameter: `?token=<access_token>`
2. **Session Cookie** - Automatically sent by browser

The WebSocket service automatically:
- Gets the JWT token from `apiService.getAccessToken()`
- Includes the session cookie from `apiService` requests
- Handles token refresh via apiService interceptors
- Reconnects when token is renewed

### Connection Lifecycle

1. **User logs in** → AuthContext updates → NotificationContext detects authentication
2. **NotificationContext** → Fetches existing notifications from API
3. **NotificationContext** → Calls `notificationWebSocket.connect(handleWebSocketMessage)`
4. **WebSocket service** → Gets JWT token and connects with authentication
5. **Server** → Validates JWT and session → Sends `connection_established`
6. **Real-time updates** → Server sends notifications as they occur
7. **User logs out** → WebSocket disconnects → Context clears notifications

### Reconnection Logic

The WebSocket service implements **exponential backoff** reconnection:

- Initial delay: 1 second
- Max attempts: 5
- Delay doubles with each attempt: 1s → 2s → 4s → 8s → 16s
- Resets to 0 on successful connection
- Stops after max attempts (shows connection failed state)
- Manual reconnect available via `actions.reconnect()`

### Message Queuing

Messages sent while WebSocket is disconnected are:
- Queued in memory
- Sent automatically when connection is re-established
- Useful for marking notifications as read during reconnection

---

## State Management

### Reducer Actions

```javascript
ActionTypes = {
  SET_CONNECTION_STATUS,    // Update connection state
  ADD_NOTIFICATION,         // Add new notification
  UPDATE_NOTIFICATION,      // Update existing notification
  MARK_AS_READ,            // Mark single notification as read
  MARK_ALL_AS_READ,        // Mark all notifications as read
  REMOVE_NOTIFICATION,     // Remove from local state
  SET_NOTIFICATIONS,       // Replace entire notification list
  UPDATE_UNREAD_COUNT,     // Update unread count
  UPDATE_SETTINGS,         // Update notification settings
  CONNECTION_FAILED,       // Mark connection as failed
  CLEAR_NOTIFICATIONS      // Clear all notifications
}
```

### Settings Management

Notification settings are persisted in `localStorage` as `notificationSettings`:

```javascript
{
  showToasts: true,          // Show toast notifications
  playSound: true,           // Play notification sound
  maxToasts: 5,              // Maximum simultaneous toasts
  toastDuration: 5000        // Toast display duration (ms)
}
```

### Sound Playback

The NotificationContext includes a simple notification sound using the **Web Audio API**:

- Two-tone beep (800Hz → 600Hz)
- 0.5 second duration
- Configurable via `settings.playSound`
- Gracefully handles audio context errors

---

## UI Integration

### TopBar Bell Icon

The existing notification bell in `TopBar.js` now shows:

1. **Unread Count Badge** - Red badge with number (from `useNotifications()`)
2. **Connection Status Indicator** - Small dot at bottom right:
   - 🟢 Green = WebSocket connected
   - ⚪ Gray = WebSocket disconnected
3. **Hover Tooltip** - Shows connection status

### Future Components

The notification system is ready for:

- **NotificationDropdown** - Full notification list with actions
- **NotificationToasts** - Real-time toast notifications
- **NotificationSettings** - User preferences UI
- **NotificationHistory** - Paginated notification history page

---

## Testing

### Manual Testing Checklist

1. **Connection Establishment**
   - [ ] Login → WebSocket connects (green dot appears)
   - [ ] Check console for "WebSocket connection established"
   - [ ] Existing notifications loaded from API

2. **Real-time Notifications**
   - [ ] Create test notification via API
   - [ ] Notification appears in real-time
   - [ ] Unread count updates
   - [ ] Sound plays (if enabled)

3. **Mark as Read**
   - [ ] Click notification → Mark as read
   - [ ] API called successfully
   - [ ] Unread count decreases
   - [ ] UI updates immediately

4. **Disconnection/Reconnection**
   - [ ] Stop backend → Connection lost (gray dot)
   - [ ] Start backend → Auto-reconnects (green dot)
   - [ ] Exponential backoff working correctly

5. **Logout**
   - [ ] Logout → WebSocket disconnects
   - [ ] Notifications cleared from state

### Test Notification Endpoint

The backend provides test endpoints for creating notifications:

```bash
# Create a single test notification
curl -X POST http://localhost:8000/api/notifications/test/create/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Create bulk test notifications
curl -X POST http://localhost:8000/api/notifications/test/bulk/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"count": 10}'
```

---

## Troubleshooting

### WebSocket Not Connecting

1. **Check authentication:**
   ```javascript
   console.log('Token:', apiService.getAccessToken());
   console.log('User:', user);
   ```

2. **Check WebSocket URL:**
   - Development: `ws://localhost:8000/ws/notifications/`
   - Production: `wss://yourdomain.com/ws/notifications/`

3. **Check backend logs:**
   ```bash
   docker-compose logs -f backend
   ```

4. **Check browser console:**
   - Look for WebSocket connection errors
   - Verify JWT token is being sent
   - Check for CORS issues

### Notifications Not Appearing

1. **Check WebSocket connection:**
   ```javascript
   const { isConnected } = useNotifications();
   console.log('Connected:', isConnected);
   ```

2. **Check notification reception:**
   - Open browser DevTools → Network → WS
   - Verify messages are being received

3. **Check reducer state:**
   ```javascript
   const { notifications } = useNotifications();
   console.log('Notifications:', notifications);
   ```

### High Reconnection Attempts

If the WebSocket keeps disconnecting:

1. **Check token expiration:**
   - JWT tokens expire after 15 minutes
   - Refresh token expires after 7 days
   - apiService should auto-refresh tokens

2. **Check backend WebSocket consumer:**
   - Verify it's accepting connections
   - Check for authentication errors
   - Review WebSocket middleware

3. **Check network stability:**
   - Corporate firewalls may block WebSocket
   - VPNs can cause connection issues

---

## Next Steps

### Recommended Enhancements

1. **NotificationDropdown Component**
   - Show notification list in dropdown
   - Group by date/type
   - Pagination support
   - Quick actions (mark as read, delete)

2. **Toast Notifications**
   - Real-time toast popups
   - Configurable position
   - Different styles per type
   - Click to view full notification

3. **Notification Filtering**
   - Filter by type (social, system, etc.)
   - Filter by read/unread status
   - Date range filtering
   - Search notifications

4. **Rich Notifications**
   - Support images/avatars
   - Action buttons
   - Deep links to related content
   - Notification grouping/threading

5. **Settings UI**
   - Enable/disable notification types
   - Sound preferences
   - Desktop notifications (browser API)
   - Email notification preferences

---

## Files Modified/Created

### Created
- ✅ `src/contexts/NotificationContext.jsx` - Main notification context
- ✅ `src/components/NotificationBadge.jsx` - Simple badge component (optional)
- ✅ `NOTIFICATION_INTEGRATION.md` - This documentation

### Modified
- ✅ `src/App.js` - Wrapped with NotificationProvider
- ✅ `src/components/TopBar.js` - Integrated real-time notification count and status
- ✅ `src/services/notificationWebSocket.js` - Updated to use apiService authentication

### Backend (Already Exists)
- ✅ `notifications/urls.py` - Notification API endpoints
- ✅ `notifications/views.py` - Notification views
- ✅ `notifications/models.py` - Notification models
- ✅ `notifications/consumers.py` - WebSocket consumer

---

## Summary

The real-time notification system is now **fully integrated** and ready for use:

✅ **NotificationContext** - Global state management
✅ **WebSocket Integration** - Real-time notifications
✅ **Authentication** - JWT + Session cookies
✅ **Auto-reconnection** - Exponential backoff
✅ **API Integration** - Fetch/mark notifications
✅ **UI Integration** - TopBar bell with unread count
✅ **Settings** - Persistent user preferences
✅ **Sound Playback** - Notification sounds

The system is production-ready and can be extended with additional UI components as needed.
