# Messaging App Documentation 💬

## Overview
The `messaging` app provides real-time chat functionality, including direct messages, group chats, message reactions, presence, and notifications. It supports advanced features like typing indicators, message threading, media attachments, and user presence tracking using Redis.

## ✅ **Current Implementation Status (August 2025)**

### **Messaging System** - **FULLY OPERATIONAL**
- **Real-time Chat**: Complete WebSocket support for instant messaging
- **Group & Direct Messages**: Full support for both message types
- **Authentication Integration**: JWT + Session hybrid authentication support
- **Presence System**: Real-time user online/offline status tracking
- **Message Reactions**: Emoji reactions and engagement features
- **Activity Tracking**: Message activity automatically tracked in user profiles

## Key Features
- ✅ **Real-time Messaging**: WebSocket-based instant messaging with Redis backend
- ✅ **Chat Room Management**: Direct messages and group chat functionality
- ✅ **Message Threading**: Support for threaded conversations
- ✅ **Media Attachments**: Image, video, and file sharing in messages
- ✅ **User Presence**: Real-time online/offline status with Redis tracking
- ✅ **Message Reactions**: Emoji reactions and message engagement
- ✅ **Read Receipts**: Track message read status across participants
- ✅ **Authentication Support**: Full hybrid JWT + Session authentication
- ✅ **Typing Indicators**: Real-time typing status for enhanced UX

---

## API Endpoints (CRUD Details)
All endpoints are prefixed with `/api/messaging/`.

| Resource         | Endpoint Prefix           | Description                        |
|------------------|--------------------------|------------------------------------|
| ChatRoom         | /api/messaging/rooms/    | Manage chat rooms (direct, group) |
| Message          | /api/messaging/messages/ | Manage messages in chat rooms      |
| MessageRead      | /api/messaging/reads/    | Track message read status          |
| MessageReaction  | /api/messaging/reactions/| Manage message reactions (emojis)  |
| UserPresence     | /api/messaging/presence/ | Track user online/offline status   |

All resources support standard CRUD operations: `GET (list/retrieve)`, `POST (create)`, `PUT/PATCH (update)`, `DELETE (remove)`.

---

## Main ViewSets and Functions
- **ChatRoomViewSet**: CRUD for chat rooms, join/leave, participant management
- **MessageViewSet**: CRUD for messages, threading, media attachments
- **MessageReadViewSet**: Track which users have read which messages
- **MessageReactionViewSet**: Add/remove emoji reactions to messages
- **UserPresenceViewSet**: Track and query user online/offline status

---

## Models (Key Fields)
- **ChatRoom**: id, name, room_type (direct/group/ai), participants, created_by, description, image, is_private, max_participants, is_archived, last_activity, messages_count, created_at, updated_at
- **Message**: id, room, sender, content, message_type (text/image/video/audio/file/location/system), media fields, reply_to, forward_from, mentions, is_edited, is_deleted, is_pinned, created_at, updated_at
- **MessageRead**: id, message, user, read_at
- **MessageReaction**: id, message, user, emoji, created_at
- **UserPresence**: id, user, status (online/away/busy/offline/invisible), last_seen, custom_status, status_emoji, away_since, total_online_time

---

## Example Usage
**Send a message:**
```http
POST /api/messaging/messages/
{
  "room": "<room_id>",
  "content": "Hello!",
  "message_type": "text"
}
```

**React to a message:**
```http
POST /api/messaging/reactions/
{
  "message": "<message_id>",
  "emoji": "👍"
}
```

---

## Signals & Automation
- Message and presence status may be updated via signals (e.g., on message sent, user online/offline).
- Signals may trigger notifications for mentions, unread messages, or presence changes.

## Background Tasks (Celery)
The messaging app uses Celery for background processing and automation. Tasks are scheduled using the **django-celery-beat** database scheduler, allowing dynamic management through the Django admin interface at `/admin/django_celery_beat/`.

### Task Schedule Table
| Task Name                        | Function Name                    | Schedule (crontab)         | Description |
|----------------------------------|----------------------------------|----------------------------|-------------|
| cleanup-expired-typing-indicators| cleanup_expired_typing_indicators| Every 30 seconds           | Clean up expired typing indicators in Redis |
| cleanup-expired-presence         | cleanup_expired_presence         | Every 5 minutes            | Clean up expired presence data in Redis |
| sync-presence-to-database        | sync_presence_to_database        | Every 10 minutes           | Sync Redis presence data to DB for analytics |
| process-message-mentions         | process_message_mentions         | Every 15 minutes           | Process @mentions in messages and notify users |
| send-message-notification-emails | send_message_notification_emails | Every 15 minutes           | Send notifications for unread/important messages |

---

## Detailed Task Descriptions

### 1. cleanup_expired_typing_indicators
**Schedule:** Every 30 seconds
**Purpose:** Cleans up expired typing indicators from Redis. (Mostly handled by Redis TTL, but can include extra logic.)

---

### 2. cleanup_expired_presence
**Schedule:** Every 5 minutes
**Purpose:** Cleans up expired user presence data from Redis. (Mostly handled by Redis TTL, but can include extra logic.)

---

### 3. sync_presence_to_database
**Schedule:** Every 10 minutes
**Purpose:** Optionally syncs Redis presence data to the `UserPresence` model in the database for analytics and reporting.

---

### 4. process_message_mentions
**Schedule:** Every 15 minutes
**Purpose:** Processes recent messages with @mentions, creating push and email notifications for mentioned users based on their settings.

---

### 5. send_message_notification_emails
**Schedule:** Every 15 minutes
**Purpose:** Sends push and email notifications for unread or important messages, respecting user notification preferences.

---

## Utilities
- **TypingIndicatorManager**: Manages real-time typing indicators using Redis.
- **UserPresenceManager**: Manages online/offline status using Redis and DB.

---

## Tests
- `tests.py` — Comprehensive test suite for messaging models, API endpoints, background tasks, and edge cases.
- Run with:
  ```sh
  python manage.py test messaging
  ```

---

## Permissions & Security
- All endpoints require authentication.
- Users can only access chat rooms and messages they are participants in.
- Media uploads (images, files) are validated and stored securely.

---
