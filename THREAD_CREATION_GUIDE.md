# Thread Creation and Post Organization Guide

## Overview

Users can now create content in two ways:
1. **Create a Thread (Topic)** - With an optional first post
2. **Create a Direct Post** - Either to a community or to an existing thread

## Architecture

### Data Hierarchy

```
AdministrativeDivision (optional)
    ↓
Community (required for posts)
    ↓
Thread (optional - organizes posts into topics)
    ↓
Post (required - actual content)
```

### Key Relationships

- **Division → Community**: Optional (divisions can change)
- **Community → Thread**: One-to-many (community can have multiple threads)
- **Thread → Post**: One-to-many (thread can have multiple posts)
- **Community → Post**: One-to-many (posts can be community-level without thread)

## Backend Implementation

### 1. Thread Model (`communities/models.py`)

```python
class Thread(models.Model):
    id = UUIDField(primary_key=True)
    community = ForeignKey(Community)  # Required
    title = CharField(max_length=255)
    slug = SlugField()
    creator = ForeignKey(UserProfile)
    body = TextField(blank=True)

    # Configuration
    is_closed = BooleanField(default=False)
    is_pinned = BooleanField(default=False)
    allow_comments = BooleanField(default=True)

    # Metrics
    posts_count = PositiveIntegerField(default=0)
```

### 2. Thread Serializer (`communities/serializers.py`)

**Features:**
- Creates thread
- Optionally creates first post automatically
- Supports different post types for first post (text, image, video, etc.)

**Write-only fields:**
- `first_post_content`: Optional text content for first post
- `first_post_type`: Type of first post (default: 'text')

**Example Request:**
```json
{
  "community": "uuid-of-community",
  "title": "Discussion: Best Restaurants in Sherbrooke",
  "body": "Let's discuss the best places to eat in town!",
  "first_post_content": "I'll start: Pamplemousse has amazing brunch!",
  "first_post_type": "text"
}
```

### 3. Thread ViewSet (`communities/views.py`)

**Endpoints:**
- `GET /api/communities/api/threads/` - List all threads
- `GET /api/communities/api/threads/?community_id=<uuid>` - Filter by community
- `GET /api/communities/api/threads/?community_slug=<slug>` - Filter by community slug
- `GET /api/communities/api/threads/<slug>/` - Get specific thread
- `POST /api/communities/api/threads/` - Create thread (with optional first post)
- `PATCH /api/communities/api/threads/<slug>/` - Update thread
- `DELETE /api/communities/api/threads/<slug>/` - Soft delete thread

### 4. Post Model Updates (`content/models.py`)

**New Features:**
- `@property get_division` - Returns community.division or None
- `Post.clean()` - Validates user is not banned from community
- Supports both `community_id` and optional `thread_id`

**Validation:**
- If thread is provided, auto-assigns community from thread
- Ensures thread.community matches post.community
- Checks if user is banned from community (raises ValidationError with ban details)

## Frontend API (`src/services/social-api.js`)

### Communities API

```javascript
// List all communities
communities.list()

// List communities in a specific division
communities.list(divisionId)

// Get specific community
communities.get(slug)

// Get or create default community for division
communities.getOrCreateForDivision(divisionId)
```

### Threads API

```javascript
// List all threads
threads.list()

// List threads in a community (by ID)
threads.list(communityId)

// List threads in a community (by slug)
threads.list(null, communitySlug)

// Get specific thread
threads.get(slug)

// Create thread with first post
threads.create({
  community_id: "uuid",
  title: "Discussion Topic",
  body: "Optional description",
  first_post_content: "Optional first post",
  first_post_type: "text" // or image, video, audio, file
})

// Create thread without first post
threads.create({
  community_id: "uuid",
  title: "Topic",
  body: "Description"
})
```

### Posts API (Enhanced)

```javascript
// Create post in community (no thread)
posts.create({
  content: "Post content",
  community_id: "uuid",
  post_type: "text"
})

// Create post in thread
posts.create({
  content: "Post content",
  community_id: "uuid",
  thread_id: "uuid",
  post_type: "text"
})

// List posts with filters
posts.list({
  division_id: "uuid",     // Optional: filter by division
  community_id: "uuid",    // Optional: filter by community
  thread_id: "uuid",       // Optional: filter by thread
  author: "user_id",       // Optional: filter by author
  post_type: "text"        // Optional: filter by type
})
```

## User Flows

### Flow 1: Create Thread with First Post

```
1. User clicks "Create Thread" button
2. Modal opens in "Thread Mode"
3. User fills:
   - Community selection (auto-filtered by user's division if available)
   - Thread title (required)
   - Thread body/description (optional)
   - Toggle "Add first post"
   - First post content (if toggled)
4. Submit → Backend creates:
   - Thread record
   - First Post record (if content provided)
   - Increments community.threads_count
   - Increments thread.posts_count (if first post created)
```

### Flow 2: Create Direct Post to Community

```
1. User clicks "Create Post" button
2. Modal opens in "Post Mode"
3. User fills:
   - Community selection (required)
   - Thread selection (optional - filtered by selected community)
   - Post content
   - Attachments (optional)
4. Submit → Backend creates:
   - Post record with community_id and optional thread_id
   - Increments appropriate counters
```

### Flow 3: Create Post in Existing Thread

```
1. User viewing thread page
2. User clicks "Reply to Thread"
3. Modal opens with:
   - Community pre-filled (from thread.community)
   - Thread pre-filled (current thread)
   - Post content editor
4. Submit → Backend creates:
   - Post record with community_id and thread_id
   - Increments thread.posts_count
```

## Automatic Community Creation

When a new division is created:
1. Signal triggers: `create_default_community_for_division()`
2. System creates community:
   - Name: Division name
   - Type: public
   - Creator: system user
   - Description: Auto-generated based on division

**Helper Functions** (`communities/utils.py`):
- `get_or_create_default_community(division)` - Core function
- `ensure_community_for_division(division_id)` - Wrapper
- `get_community_for_post(division_id, community_id)` - Smart selector

## Ban Validation

Users banned from a community cannot:
- Create threads in that community
- Create posts in that community
- Create posts in threads belonging to that community

**Error Response:**
```json
{
  "community": [
    "You are banned from posting in this community. Reason: Spam. Ban expires: 2025-12-31"
  ]
}
```

## Database Indexes

**Community:**
- `(division, -created_at)` - For filtering communities by division
- `(is_active, -posts_count)` - For popular communities

**Thread:**
- `(community, -created_at)` - For listing threads in community
- `(creator, -created_at)` - For user's created threads

## Frontend Components (To Be Implemented)

### 1. ThreadCreationModal
- Mode: Create new thread
- Fields: community, title, body, first_post (toggle)
- Smart community selector (division-aware)

### 2. PostCreationModal (Enhanced)
- Mode selector: "Post" or "Thread"
- Community selector (division-filtered)
- Thread selector (community-filtered, optional)
- Support for thread_id in submission

### 3. ThreadList
- Display threads for a community
- Show thread metadata (title, creator, posts_count, created_at)
- Pinned threads at top
- Click to view thread details

### 4. DivisionCommunitySelector
- If user has division → show communities in division
- Allow browsing all communities
- Quick access to user's local communities

## Testing Checklist

- [ ] Create thread with first post
- [ ] Create thread without first post
- [ ] Create post to community (no thread)
- [ ] Create post to existing thread
- [ ] Thread.posts_count increments correctly
- [ ] Community.threads_count increments correctly
- [ ] Ban validation prevents posting
- [ ] Division filtering works for communities
- [ ] Community filtering works for threads
- [ ] Thread filtering works for posts
- [ ] Auto-creation of community when division created
- [ ] post.get_division returns correct division
- [ ] post.get_division returns None for communities without division

## API Reference

### Thread Creation Response

```json
{
  "id": "uuid",
  "community": "uuid",
  "community_name": "Sherbrooke",
  "community_slug": "sherbrooke",
  "title": "Best Restaurants",
  "slug": "best-restaurants",
  "creator": "uuid",
  "creator_username": "john_doe",
  "body": "Let's discuss local restaurants",
  "is_closed": false,
  "is_pinned": false,
  "allow_comments": true,
  "posts_count": 1,
  "created_at": "2025-10-09T12:00:00Z",
  "updated_at": "2025-10-09T12:00:00Z"
}
```

### Post Creation with Thread

```json
{
  "id": "uuid",
  "author": "uuid",
  "community": "uuid",
  "thread": "uuid",
  "content": "Post content",
  "post_type": "text",
  "visibility": "community",
  "created_at": "2025-10-09T12:00:00Z"
}
```

## Migration Notes

- Communities created before this feature will have `division=null`
- Communities can exist without a division
- Threads always require a community
- Posts require a community (thread is optional)
- Existing posts without community will need manual data migration
