# Notifications App Documentation 🔔

## Overview
The `notifications` app manages all user notifications across the platform, including likes, comments, follows, mentions, messages, system alerts, equipment events, community activities, and geo-restriction notifications. It provides a centralized service for creating, storing, and delivering notifications via push and email, with support for user preferences, notification digests, and advanced community integration.

## ✅ **Current Implementation Status (August 2025)**

### **Notification System** - **FULLY OPERATIONAL**
- **Centralized Service**: Complete notification management across all platform apps
- **Real-time Delivery**: Instant push notifications with Redis backend support
- **Email Notifications**: Background email delivery with customizable templates
- **Community Integration**: Advanced community-specific notifications with geo-restriction alerts
- **User Preferences**: Granular notification settings with frequency control
- **Activity Integration**: Automatic notifications triggered by user activity middleware
- **Geo-Restriction Alerts**: Location-based access notifications with city-level detail
- **Authentication Support**: Full JWT + Session compatibility with notification delivery

## Key Features
- ✅ **Multi-Type Notifications**: Likes, comments, follows, mentions, messages, system alerts
- ✅ **Community Notifications**: Join requests, invitations, moderation actions, member activities
- ✅ **Geo-Restriction Alerts**: Location-based access notifications with travel context
- ✅ **Equipment Notifications**: Warranty expiration and maintenance reminders
- ✅ **Real-time Delivery**: Instant push notifications via WebSocket and Redis
- ✅ **Email Notifications**: Background email delivery with HTML templates
- ✅ **User Preferences**: Customizable notification settings and frequency controls
- ✅ **Digest System**: Daily and weekly notification summaries
- ✅ **Authentication Integration**: JWT + Session compatible notification delivery
- ✅ **Background Processing**: Celery tasks for notification batching and cleanup

---

## 🌍 **Geo-Restriction Notifications** - **NEW FEATURE**

### **Location-Based Alerts**
The notification system now includes advanced geo-restriction notifications:

#### **Notification Types**
- **Access Blocked**: When users are blocked from communities based on location
- **Travel Notifications**: When users travel to restricted areas but maintain access
- **City-Level Alerts**: Detailed notifications for city-specific restrictions
- **Region Restrictions**: Notifications for region/state-based access control

#### **Notification Context**
```python
# Example geo-restriction notification
CommunityNotifications.geo_restriction_notification(
    user=user_profile,
    community=community,
    restriction_type='location',
    restriction_message='Access restricted from your current location',
    user_location='Los Angeles, United States (registered from New York, United States)',
    send_email=True
)
```

#### **Features**
- **Travel-Aware**: Notifications include both current and registration locations
- **City Granularity**: Specific city and region information in notifications
- **Email Integration**: Automatic email alerts for geo-restriction events
- **Context-Rich**: Detailed location context and restriction explanations

---

## 👥 **Community Notifications** - **ENHANCED**

### **Real-time Community Events**
Enhanced community notifications with real-time tracking:

#### **Notification Categories**
- **Membership**: Join requests, approvals, invitations, role changes
- **Activity**: New posts, comments, member online status
- **Moderation**: Warnings, bans, content removal
- **Analytics**: Weekly activity summaries, milestone achievements
- **Geo-Access**: Location-based access events and changes

#### **Example Usage**
```python
# Community join notification
CommunityNotifications.member_joined_notification(
    community=community,
    new_member=user_profile,
    invited_by=inviter_profile
)

# Geo-restriction notification with city context
CommunityNotifications.geo_restriction_notification(
    user=user_profile,
    community=community,
    restriction_type='city_blocked',
    user_location='Toronto, Canada',
    restriction_message='This community is not available in your city'
)
```

---

## API Endpoints (Enhanced CRUD)
All endpoints are prefixed with `/api/notifications/`.

| Resource           | Endpoint Prefix           | Description                        |
|--------------------|--------------------------|------------------------------------|
| Notifications      | /api/notifications/       | Manage user notifications (CRUD)   |
| Preferences        | /api/notification-preferences/ | **NEW**: Manage notification settings |

### Notifications (`notifications/`)
| Method | Endpoint                | Description                |
|--------|-------------------------|----------------------------|
| GET    | /api/notifications/     | List all notifications     |
| POST   | /api/notifications/     | Create a notification      |
| GET    | /api/notifications/{id}/| Retrieve a notification    |
| PUT    | /api/notifications/{id}/| Update a notification      |
| PATCH  | /api/notifications/{id}/| Partial update             |
| DELETE | /api/notifications/{id}/| Delete a notification      |

### **NEW: Enhanced Notification Actions**
| Method | Endpoint                          | Description                           |
|--------|-----------------------------------|---------------------------------------|
| POST   | /api/notifications/mark-all-read/ | **NEW**: Mark all notifications as read |
| GET    | /api/notifications/unread-count/  | **NEW**: Get unread notification count   |
| GET    | /api/notifications/by-type/       | **NEW**: Filter notifications by type    |
| POST   | /api/notifications/bulk-update/   | **NEW**: Bulk update notification status |
| GET    | /api/notifications/digest/        | **NEW**: Get notification digest summary |

### **NEW: Notification Preferences** (`notification-preferences/`)
| Method | Endpoint                | Description                |
|--------|-------------------------|----------------------------|
| GET    | /api/notification-preferences/    | Get user notification preferences |
| PUT    | /api/notification-preferences/    | Update notification preferences   |
| POST   | /api/notification-preferences/reset/ | Reset to default preferences |

---

## Main Functions & Utilities

### **Enhanced Notification Services**
- **NotificationService**: Centralized service for creating and managing notifications across all apps
- **CommunityNotifications**: **NEW** - Community-specific notification logic with geo-restriction support
- **SystemNotifications**: System-level notifications and alerts
- **MessagingNotifications**: Direct messaging and communication notifications
- **EquipmentNotifications**: Equipment-related notifications (warranty, maintenance)
- **GeoNotifications**: **NEW** - Location-based notification management

### **NEW: Utility Classes**
```python
# Community notifications with geo-restriction support
CommunityNotifications.geo_restriction_notification(
    user=user_profile,
    community=community,
    restriction_type='location',
    user_location='New York, United States',
    restriction_message='Access granted from allowed location'
)

# Real-time member activity notifications
CommunityNotifications.member_activity_notification(
    community=community,
    member=user_profile,
    activity_type='online',
    context={'online_duration': 3600}
)
```

---

## Models (Enhanced Fields)

### **Notification Model** - **UPDATED**
- **Core Fields**: id, recipient, sender, notification_type, title, message, content_type, object_id, content_object
- **Metadata**: extra_data, is_read, read_at, created_at, updated_at
- **NEW Fields**:
  - `priority`: low, medium, high, urgent
  - `category`: social, community, system, equipment, geo_restriction
  - `location_context`: JSON field for geo-related notifications
  - `community_context`: JSON field for community-specific data
  - `requires_action`: Boolean for actionable notifications

### **NEW: NotificationPreference Model**
- **User Settings**: user, notification_type, is_enabled, frequency, delivery_method
- **Preferences**: email_enabled, push_enabled, digest_frequency
- **Community Settings**: community_notifications, geo_restriction_alerts
- **Timing**: quiet_hours_start, quiet_hours_end, timezone

---

## Enhanced Notification Types

### **Core Types** (existing)
- `like`, `comment`, `follow`, `mention`, `message`, `system`

### **NEW: Community Types**
- `community_join_request`, `community_invitation`, `community_member_joined`
- `community_role_assigned`, `community_moderation`, `community_activity`

### **NEW: Geo-Restriction Types**
- `geo_access_granted`, `geo_access_blocked`, `geo_travel_notification`
- `geo_city_restriction`, `geo_region_restriction`, `geo_country_restriction`

### **Equipment Types** (existing)
- `warranty_expiration`, `maintenance_reminder`, `equipment_update`

---

## Example Usage

### **Basic Notification Creation**
```python
NotificationService.create_notification(
    recipient=user_profile,
    title='New Like',
    message='Your post was liked!',
    notification_type='like',
    related_object=post
)
```

### **Community Geo-Restriction Notification**
```python
CommunityNotifications.geo_restriction_notification(
    user=user_profile,
    community=community,
    restriction_type='city_blocked',
    restriction_message='This community is not available in Toronto, Canada.',
    user_location='Toronto, Canada (registered from New York, United States)',
    send_email=True
)
```

### **Real-time Member Activity**
```python
CommunityNotifications.member_activity_notification(
    community=community,
    member=user_profile,
    activity_type='joined',
    context={'invitation_accepted': True, 'inviter': inviter_profile}
)
```

---

## Background Tasks (Celery)
The notifications app uses Celery for background processing and automation. Tasks are scheduled using the **django-celery-beat** database scheduler, allowing dynamic management through the Django admin interface at `/admin/django_celery_beat/`.

### Task Schedule Table
| Task Name                           | Function Name                       | Schedule (crontab)         | Description |
|-------------------------------------|-------------------------------------|----------------------------|-------------|
| send-notification-emails            | send_notification_emails            | Every 15 minutes           | Send email notifications for high-priority unread notifications |
| **send-geo-restriction-emails**     | **send_geo_restriction_emails**     | **Every 10 minutes**       | **NEW**: Send email alerts for geo-restriction events |
| **process-community-notifications** | **process_community_notifications** | **Every 5 minutes**        | **NEW**: Process real-time community notifications |
| cleanup-old-notifications           | cleanup_old_notifications           | 02:00 daily                | Clean up old notifications from the database |
| generate-notification-digest        | generate_notification_digest        | 03:00 daily                | Generate and send notification digests to users |
| **generate-community-digest**       | **generate_community_digest**       | **Weekly (Sunday 09:00)**  | **NEW**: Generate weekly community activity digests |
| update-notification-metrics         | update_notification_metrics         | 04:00 daily                | Update notification analytics and metrics |
| **update-geo-notification-metrics** | **update_geo_notification_metrics** | **Every hour**             | **NEW**: Update geo-restriction notification analytics |
| **cleanup-read-notifications**      | **cleanup_read_notifications**      | **Daily at 01:00**         | **NEW**: Clean up old read notifications to maintain performance |

---

## Detailed Task Descriptions

### 1. send_notification_emails
**Schedule:** Every 15 minutes
**Purpose:** Sends email notifications for high-priority unread notifications (e.g., system alerts, messages) to users, batching multiple notifications per user.

### **2. send_geo_restriction_emails** - **NEW**
**Schedule:** Every 10 minutes
**Purpose:** Sends immediate email alerts for geo-restriction events, including access blocked/granted notifications with detailed location context.

### **3. process_community_notifications** - **NEW**
**Schedule:** Every 5 minutes
**Purpose:** Processes real-time community notifications including member activities, join requests, and moderation actions.

### 4. cleanup_old_notifications
**Schedule:** 02:00 daily
**Purpose:** Cleans up old notifications from the database to keep it performant and relevant.

### 5. generate_notification_digest
**Schedule:** 03:00 daily
**Purpose:** Generates and sends notification digests (summary emails) to users, summarizing recent activity and unread notifications.

### **6. generate_community_digest** - **NEW**
**Schedule:** Weekly (Sunday 09:00)
**Purpose:** Generates weekly community activity digests including member activities, popular posts, and geo-restriction summaries.

### 7. update_notification_metrics
**Schedule:** 04:00 daily
**Purpose:** Updates notification analytics and metrics for reporting and monitoring.

### **8. update_geo_notification_metrics** - **NEW**
**Schedule:** Every hour
**Purpose:** Updates geo-restriction notification analytics, tracking blocked access attempts, successful notifications, and user location patterns.

### **9. cleanup_read_notifications** - **NEW**
**Schedule:** Daily at 01:00
**Purpose:** Cleans up old read notifications to maintain database performance while preserving important unread notifications.

---

## Tests
- `tests.py` — Comprehensive test suite for notification models, API endpoints, background tasks, and utilities.
- Run with:
  ```sh
  python manage.py test notifications
  ```

---

## Permissions & Security
- All endpoints require authentication.
- Users can only access their own notifications.
- Notification content and delivery are handled securely and respect user preferences.

---
