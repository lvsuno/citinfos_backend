# How the Mention System Works

## 🎯 Complete Flow Overview

The mention system has **3 main phases**: Detection → Storage → Notification

```
┌─────────────────────────────────────────────────────────────────┐
│                   PHASE 1: CLIENT-SIDE DETECTION                │
│                    (React Frontend - Browser)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PHASE 2: SERVER-SIDE STORAGE                  │
│                    (Django Backend - Database)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PHASE 3: NOTIFICATION DELIVERY                │
│                  (Celery Tasks - Push/Email/WebSocket)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## PHASE 1: Client-Side Detection (Frontend)

### Step 1: User Types @ Symbol

**File**: `src/components/ui/MentionAutocomplete.jsx`

```javascript
// User types: "Hey @j"
// Component detects @ pattern
const mentionMatch = text.match(/@(\w+)$/);
```

**Detection Logic**:
- Looks for `@` followed by letters/numbers
- Must be at text start or after whitespace
- Minimum 1 character after @

### Step 2: Search for Mentionable Users

**File**: `src/services/social-api.js`

```javascript
searchMentionableUsers: async (query, communityId, postId) => {
  // API call to backend
  GET /api/profiles/search_mentionable/?q=j&community_id=123
}
```

**Backend Endpoint**: `accounts/views.py`

```python
@api_view(['GET'])
def search_mentionable_users(request):
    query = request.GET.get('q', '')
    community_id = request.GET.get('community_id')

    # Search users by username
    users = UserProfile.objects.filter(
        user__username__icontains=query
    )

    # Prioritize:
    # 1. Post author (if replying)
    # 2. Community members
    # 3. Followers
    # 4. Public users
```

### Step 3: Display Autocomplete Dropdown

**File**: `src/components/ui/MentionAutocomplete.jsx`

```javascript
// Shows dropdown with grouped results
<div className="mention-dropdown">
  {followers.length > 0 && (
    <div className="group">
      <h3>Your Followers</h3>
      {followers.map(user => (
        <div onClick={() => handleSelect(user)}>
          @{user.username}
        </div>
      ))}
    </div>
  )}
  {/* ... other groups */}
</div>
```

**Keyboard Navigation**:
- ↑↓ arrows: Navigate suggestions
- Enter: Select current
- Esc: Close dropdown
- Tab: Select first

### Step 4: Insert Username

```javascript
// User selects "@john" from dropdown
onMentionSelect({
  user: { username: 'john', id: 123 },
  startPos: 5,    // Position of @
  endPos: 7,      // End of @j
  replacement: '@john '  // Inserted text (with trailing space)
});

// Text becomes: "Hey @john "
```

### Step 5: Extract Mentions Before Submission

**File**: `src/services/social-api.js`

```javascript
// When submitting post/comment
const content = "Hey @john, check this @sarah!";

// Extract all mentions
const mentions = utils.extractMentions(content);
// Returns: ['john', 'sarah']

// Send to backend
POST /api/content/posts/ {
  content: "Hey @john, check this @sarah!",
  // Mentions are extracted on backend from content
}
```

---

## PHASE 2: Server-Side Storage (Backend)

### Step 1: Post/Comment is Created

**File**: `content/views.py`

```python
@api_view(['POST'])
def create_post(request):
    # Create post
    post = Post.objects.create(
        author=request.user.profile,
        content=request.data['content']
        # content contains: "Hey @john, check this @sarah!"
    )

    # Signal is triggered automatically
    # → content/signals.py::auto_moderate_post
```

### Step 2: Signal Processes Content

**File**: `content/signals.py`

```python
@receiver(post_save, sender=Post)
def auto_moderate_post(sender, instance, created, **kwargs):
    if created and instance.content:
        # Process mentions and hashtags
        from .utils import process_post_content
        content_result = process_post_content(instance)
        # → Calls process_mentions_in_post()
```

### Step 3: Extract Mentions from Content

**File**: `content/utils.py`

```python
def extract_mentions_from_content(content, mentioning_user):
    """
    Extract @username patterns from content.

    Input: "Hey @john, check this @sarah!"
    Process:
    1. Regex finds: ['john', 'sarah']
    2. Query database for UserProfile with those usernames
    3. Return UserProfile objects (not just strings!)
    """

    import re
    # Regex pattern: @[username]
    # Pattern: (?i)@([a-z0-9_]{2,30})
    # (?i) = case insensitive
    # @ = literal @
    # ([a-z0-9_]{2,30}) = username (2-30 chars)

    usernames = set(
        re.findall(r'(?i)@([a-z0-9_]{2,30})', content.lower())
    )
    # Result: {'john', 'sarah'}

    # Look up actual users
    mentioned_profiles = UserProfile.objects.filter(
        user__username__in=usernames
    )
    # Result: [<UserProfile: john>, <UserProfile: sarah>]

    return list(mentioned_profiles)
```

### Step 4: Create Mention Records

**File**: `content/utils.py`

```python
def process_mentions_in_post(post):
    """
    Create Mention database records for each mentioned user.
    """
    # Extract mentioned users
    mentions = extract_mentions_from_content(
        post.content,      # "Hey @john, check @sarah!"
        post.author        # Current user
    )
    # mentions = [<UserProfile: john>, <UserProfile: sarah>]

    # Create Mention records
    from .models import Mention
    stored = []

    for profile in mentions:
        m, created = Mention.objects.get_or_create(
            post=post,                      # Link to post
            mentioned_user=profile,         # Who was mentioned
            mentioning_user=post.author     # Who mentioned them
        )
        stored.append(profile)

    return stored
```

### Step 5: Mention Model Storage

**File**: `content/models.py`

```python
class Mention(models.Model):
    """
    Database table: content_mention

    Stores who mentioned whom in which post/comment.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Link to content (either post OR comment)
    post = models.ForeignKey(Post, null=True, blank=True)
    comment = models.ForeignKey(Comment, null=True, blank=True)

    # Who was mentioned (@john)
    mentioned_user = models.ForeignKey(
        UserProfile,
        related_name='content_mentions_received'
    )

    # Who mentioned them (current user)
    mentioning_user = models.ForeignKey(
        UserProfile,
        related_name='content_mentions_sent'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # Soft delete support
    is_deleted = models.BooleanField(default=False)
```

**Example Database Records**:
```sql
-- After creating post "Hey @john, check this @sarah!"

content_mention table:
┌──────────┬─────────┬──────────┬──────────────────┬────────────────┐
│ id       │ post_id │ comment  │ mentioned_user   │ mentioning_user│
├──────────┼─────────┼──────────┼──────────────────┼────────────────┤
│ uuid-123 │ post-1  │ NULL     │ john_profile_id  │ alice_profile  │
│ uuid-456 │ post-1  │ NULL     │ sarah_profile_id │ alice_profile  │
└──────────┴─────────┴──────────┴──────────────────┴────────────────┘
```

---

## PHASE 3: Notification Delivery

### Step 1: Celery Task Processes Mentions

**File**: `content/tasks.py`

```python
@shared_task
def process_mentions():
    """
    Periodic task (runs every hour via Celery Beat).
    Finds recent mentions and sends notifications.
    """
    from notifications.utils import NotificationService

    # Get mentions from last hour
    recent_mentions = Mention.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).select_related(
        'mentioned_user',   # Load the mentioned user
        'mentioning_user',  # Load who mentioned them
        'post',             # Load the post
        'comment'           # Load the comment (if applicable)
    )

    for mention in recent_mentions:
        # Check user notification preferences
        mentioned_user = mention.mentioned_user
        user_settings = mentioned_user.settings

        # Skip if user disabled notifications
        if user_settings.notification_frequency == 'never':
            continue

        # Create notification
        if user_settings.push_notifications:
            create_push_notification(mention)

        if user_settings.email_notifications:
            send_email_notification(mention)
```

### Step 2: Create Push Notification

**File**: `content/tasks.py`

```python
# Create push notification
push_notification = NotificationService.create_notification(
    recipient=mentioned_user,  # @john
    title=f"Mentioned in post by {mention.mentioning_user.username}",
    message=f"@{mention.mentioning_user.username} mentioned you",
    notification_type='mention',  # Important!
    related_object=mention.post,  # Link to post
    extra_data={
        'mention_id': str(mention.id),
        'mentioner_id': str(mention.mentioning_user.id),
        'mentioner_username': mention.mentioning_user.username,
        'content_type': 'post'
    }
)
```

**Database**: Creates record in `notifications_notification` table

### Step 3: Send Real-Time WebSocket Notification

**File**: `notifications/realtime.py` (if implemented)

```python
# Send to WebSocket channel for real-time delivery
channel_layer = get_channel_layer()
async_to_sync(channel_layer.group_send)(
    f'notifications_{mentioned_user.user.id}',
    {
        'type': 'notification_message',
        'notification': {
            'id': str(notification.id),
            'type': 'mention',
            'title': 'You were mentioned',
            'message': f'@{mentioner} mentioned you',
            'timestamp': now.isoformat(),
        }
    }
)
```

**Frontend receives** via WebSocket connection in `NotificationContext.jsx`

### Step 4: Send Email Notification (Optional)

**File**: `content/tasks.py`

```python
# Only if user enabled email notifications
if user_settings.email_notifications:
    email_sent = NotificationService.send_email_notification(
        recipient=mentioned_user,
        subject=f'📢 Mentioned in post by @{mentioner}',
        template='content/email/mention_notification.html',
        context={
            'recipient': mentioned_user,
            'mentioner': mention.mentioning_user,
            'mention': mention,
            'content': mention.post,
            'content_type': 'post'
        }
    )
```

**Email Template**: `content/templates/content/email/mention_notification.html`

---

## 🔄 Complete Example Flow

### Scenario: Alice mentions John in a post

```
┌────────────────────────────────────────────────────────────────┐
│ 1. CLIENT: Alice types in React app                           │
├────────────────────────────────────────────────────────────────┤
│   Text: "Hey @j"                                               │
│   → MentionAutocomplete detects @                              │
│   → Searches API: /api/profiles/search_mentionable/?q=j       │
│   → Shows dropdown: [@john, @jane, @jerry]                     │
│   → Alice clicks @john                                         │
│   → Text becomes: "Hey @john, great work!"                     │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ 2. CLIENT: Alice submits post                                 │
├────────────────────────────────────────────────────────────────┤
│   POST /api/content/posts/                                     │
│   Body: {                                                      │
│     content: "Hey @john, great work!",                         │
│     community_id: 123                                          │
│   }                                                            │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ 3. SERVER: Post created (Django view)                         │
├────────────────────────────────────────────────────────────────┤
│   post = Post.objects.create(                                  │
│     author=alice_profile,                                      │
│     content="Hey @john, great work!",                          │
│     community_id=123                                           │
│   )                                                            │
│   → post_save signal fired                                     │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ 4. SERVER: Signal processes content (signals.py)              │
├────────────────────────────────────────────────────────────────┤
│   auto_moderate_post()                                         │
│   → process_post_content()                                     │
│   → process_mentions_in_post()                                 │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ 5. SERVER: Extract mentions (utils.py)                        │
├────────────────────────────────────────────────────────────────┤
│   extract_mentions_from_content()                              │
│   → Regex finds: ['john']                                      │
│   → Queries: UserProfile.objects.filter(username='john')       │
│   → Returns: [<UserProfile: john>]                             │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ 6. SERVER: Create Mention record (utils.py)                   │
├────────────────────────────────────────────────────────────────┤
│   Mention.objects.create(                                      │
│     post=post,                                                 │
│     mentioned_user=john_profile,                               │
│     mentioning_user=alice_profile                              │
│   )                                                            │
│   → Saved to database ✅                                       │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ 7. CELERY: Process mention task (runs hourly)                 │
├────────────────────────────────────────────────────────────────┤
│   process_mentions() task finds new mention                    │
│   → Checks john's notification settings                        │
│   → john has push_notifications=True                           │
│   → Creates Notification record                                │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ 8. NOTIFICATION: Delivered to John                            │
├────────────────────────────────────────────────────────────────┤
│   ✅ Push notification: "Alice mentioned you"                  │
│   ✅ WebSocket: Real-time bell notification                    │
│   ✅ Email (if enabled): Sent to john@example.com              │
│   ✅ In-app: Shows in notification dropdown                    │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ 9. CLIENT: John sees notification                             │
├────────────────────────────────────────────────────────────────┤
│   → Bell icon shows red dot                                    │
│   → Clicks bell                                                │
│   → Sees: "@alice mentioned you in a post"                     │
│   → Clicks notification                                        │
│   → Opens post: "Hey @john, great work!"                       │
└────────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Tables Involved

### 1. `content_post`
```sql
id          | content                  | author_id
------------|--------------------------|----------
post-123    | "Hey @john, great work!" | alice
```

### 2. `content_mention`
```sql
id       | post_id  | mentioned_user | mentioning_user | created_at
---------|----------|----------------|-----------------|------------
uuid-1   | post-123 | john_profile   | alice_profile   | 2025-10-09
```

### 3. `notifications_notification`
```sql
id       | recipient | type    | title                  | read | created_at
---------|-----------|---------|------------------------|------|------------
notif-1  | john      | mention | "Alice mentioned you"  | 0    | 2025-10-09
```

---

## 🔧 Key Files Summary

### Frontend (React)
| File | Purpose |
|------|---------|
| `src/components/ui/MentionAutocomplete.jsx` | Dropdown for @username suggestions |
| `src/hooks/useMentionInput.js` | Cursor tracking for textarea |
| `src/services/social-api.js` | API calls + regex extraction |
| `src/components/PostCreationModal.jsx` | Calls processContentMentions() |

### Backend (Django)
| File | Purpose |
|------|---------|
| `content/models.py` | Mention model definition |
| `content/utils.py` | Extract + process mentions |
| `content/signals.py` | Auto-process on post save |
| `content/tasks.py` | Celery task for notifications |
| `accounts/views.py` | Search mentionable users API |

---

## ⚙️ Configuration

### Settings Required
```python
# settings.py
CELERY_BEAT_SCHEDULE = {
    'process-mentions': {
        'task': 'content.tasks.process_mentions',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

### User Settings (Affects Delivery)
- `notification_frequency`: 'real_time', 'hourly', 'daily', 'never'
- `push_notifications`: True/False
- `email_notifications`: True/False

---

## 🎯 Summary

**Mention Flow in 3 Steps:**

1. **Client detects** → User types `@john` → Autocomplete helps → Inserted into text
2. **Server extracts** → Regex finds `@john` → Creates Mention record in database
3. **Task notifies** → Celery finds new mentions → Sends push/email/WebSocket notification

**The magic happens automatically!** Once a post is created with `@john` in the content, Django signals trigger the entire mention processing pipeline without any manual intervention.
