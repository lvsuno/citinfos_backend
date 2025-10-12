# Community-Division Architecture Update

## Overview
This document outlines the new architecture where communities are **optionally** tied to geographic divisions. Division linkage is optional since divisions can change over time.

## Core Relationships

```
AdministrativeDivision (municipality, commune, etc.)
    ↓ (has many - OPTIONAL)
Community (public, accessible to all)
    ↓ (has many)
Thread (optional topic organizer)
    ↓ (has many - optional)
Post (can be community-level or thread-level)
```

## Key Changes from Previous Architecture

### 1. Community Model Changes
**COMPLETED:**
- ✅ Added `division` ForeignKey to `AdministrativeDivision` (OPTIONAL: null=True, blank=True)
- ✅ Division uses SET_NULL on delete (preserves communities when divisions change)
- ✅ Removed `members_count` field (communities are public)
- ✅ Updated Meta.indexes to include division and use posts_count instead of members_count
- ✅ Migration 0002_add_optional_division_to_community applied successfully

**What this means:**
- Communities can optionally belong to a geographic division (e.g., Sherbrooke, Cotonou, etc.)
- Division linkage is flexible - can be updated as administrative boundaries change
- If a division is deleted, communities remain but division is set to NULL
- Users don't "join" communities anymore - they're public by default
- Community discovery can happen through geographic location OR by browsing all communities

### 2. CommunityMembership Model
**Current State:**
- Still exists but purpose has changed
- Status choices: `'active'`, `'banned'` (removed `'left'`)
- No longer tracks general membership

**New Purpose:**
- **Moderator/Admin Roles:** Users with special permissions in a community
- **Ban Tracking:** Users banned from posting in a community
- Regular users don't need a membership record to view or post

**Fields:**
- `role`: ForeignKey to CommunityRole (for moderators/admins)
- `status`: 'active' or 'banned'
- `banned_by`, `ban_reason`, `banned_at`, `ban_expires_at`: For moderation

### 3. Thread Model
**Status:** Already implemented correctly

**Key Points:**
- Threads are **optional** topic organizers within communities
- Posts can belong to a thread OR be community-level
- `thread.posts_count` tracks posts in that specific thread
- `community.posts_count` tracks ALL posts in the community (thread + non-thread)

### 4. Post Model
**Current State:** Already has `community` and `thread` ForeignKeys

**Validation Needed:**
- ✅ `post.community` is required (all posts belong to a community)
- ✅ `post.thread` is optional (posts can be thread-level or community-level)
- ⏳ Need to add: `post.get_division()` helper method
- ⏳ Need to add: Ban validation in `Post.clean()`

**Derived Relationships:**
```python
post.community                    # Direct FK - required
post.thread                       # Direct FK - optional
post.community.division           # Geographic division of the community
post.get_division()               # Helper method (returns post.community.division)
```

## User Workflows

### Creating a Post

**Old Flow (removed):**
1. User joins community
2. User posts to community

**New Flow:**
1. User selects/browses geographic division (e.g., Sherbrooke)
2. User sees communities in that division
3. User selects a community (public access, no join needed)
4. User optionally selects a thread within that community
5. User creates post (includes `community_id`, optional `thread_id`)

### Viewing Posts

**By Division:**
- Show all posts from all communities in a division
- Default view for most users

**By Community:**
- Show all posts from a specific community (thread + non-thread)

**By Thread:**
- Show only posts from a specific thread

### Moderation

**Ban System:**
- Moderators can ban users from posting in their community
- Ban is tracked in `CommunityMembership.status = 'banned'`
- Temporary bans supported via `ban_expires_at`
- Post creation validates user is not banned

## Database Migrations Needed

### Migration 1: Add division field
```bash
python manage.py makemigrations communities --name add_division_to_community
```

**Changes:**
- Add `Community.division` ForeignKey (nullable)
- Remove `Community.members_count` field
- Update indexes

### Migration 2: Update existing data (optional)
- Assign divisions to existing communities (if any)
- Clean up old membership records that aren't moderators/admins

## API Changes Needed

### Community Endpoints

**List communities by division:**
```
GET /api/communities/?division_id={uuid}
Response: {
  "results": [
    {
      "id": "uuid",
      "name": "Community Name",
      "division": {
        "id": "uuid",
        "name": "Sherbrooke",
        "boundary_type": "municipality",
        "admin_level": 4
      },
      "posts_count": 150,
      "threads_count": 12,
      ...
    }
  ]
}
```

**Create community (requires division):**
```
POST /api/communities/
{
  "name": "My Community",
  "description": "...",
  "division": "division-uuid",  // REQUIRED
  "community_type": "public"
}
```

### Thread Endpoints

**List threads in community:**
```
GET /api/communities/{community_id}/threads/
```

**Create thread:**
```
POST /api/communities/{community_id}/threads/
{
  "title": "Thread Title",
  "body": "Thread content..."
}
```

### Post Endpoints

**Create post:**
```
POST /api/content/posts/
{
  "content": "Post content",
  "community": "community-uuid",  // REQUIRED
  "thread": "thread-uuid",        // OPTIONAL
  "post_type": "text",
  ...
}
```

**List posts (with filters):**
```
GET /api/content/posts/?division_id={uuid}           # All posts in division
GET /api/content/posts/?community_id={uuid}          # All posts in community
GET /api/content/posts/?thread_id={uuid}             # Posts in specific thread
GET /api/content/posts/?division_id={uuid}&limit=20  # Paginated
```

## Frontend Components Needed

### 1. DivisionCommunitySelector
- Shows communities for current division
- Allows switching between communities
- Displays community info (posts_count, threads_count)

### 2. ThreadList
- Shows threads within selected community
- Option to create new thread
- Shows thread.posts_count for each thread

### 3. Updated PostCreationModal
**Current:** Just shows tabs (Article/Poll/Media)
**New:**
- Auto-selects current division's default community
- Shows community selector (communities in division)
- Shows optional thread selector (if community has threads)
- Keeps existing tabs (Article/Poll/Media)
- Sends `community_id` and optional `thread_id` with post

### 4. Updated SocialFeed
**Current:** Shows all posts
**New:**
- Filter by division (default: current division)
- Filter by community (optional)
- Filter by thread (optional)
- Toggle: "My Division" vs "All Posts"

### 5. Navigation Breadcrumb
```
Sherbrooke > Tech Community > Weekly Discussion > Post #123
[Division]   [Community]      [Thread]            [Post]
```

## Permissions & Validation

### Community Access
- **View:** Everyone (public)
- **Post:** Everyone (unless banned)
- **Moderate:** Only users with CommunityMembership.role (moderator/admin)

### Ban Checks (in Post.clean())
```python
def clean(self):
    super().clean()

    # Check if user is banned from this community
    if self.community:
        membership = CommunityMembership.objects.filter(
            community=self.community,
            user=self.author,
            status='banned'
        ).first()

        if membership:
            # Check if ban has expired
            if membership.ban_expires_at:
                if timezone.now() > membership.ban_expires_at:
                    # Ban expired, reactivate user
                    membership.status = 'active'
                    membership.save()
                else:
                    raise ValidationError(
                        f"You are banned from posting in {self.community.name} "
                        f"until {membership.ban_expires_at}"
                    )
            else:
                # Permanent ban
                raise ValidationError(
                    f"You are banned from posting in {self.community.name}"
                )
```

## Implementation Checklist

### Backend (Django)
- [x] Add `Community.division` field
- [x] Remove `Community.members_count` field
- [x] Update `Community` Meta indexes
- [ ] Create and run migrations
- [ ] Update `CommunityMembership` model docs/comments
- [ ] Add `Post.get_division()` helper method
- [ ] Add ban validation to `Post.clean()`
- [ ] Update Community serializers (add division, remove members_count)
- [ ] Update Community views (filter by division, remove join logic)
- [ ] Update Post views (require community_id)
- [ ] Add endpoint: GET /api/communities/?division_id=uuid
- [ ] Add endpoint: GET /api/communities/{id}/threads/
- [ ] Update permissions (public access, ban checks)

### Frontend (React)
- [ ] Update `social-api.js` with new endpoints
- [ ] Create `DivisionCommunitySelector` component
- [ ] Create `ThreadList` component
- [ ] Update `PostCreationModal` (community/thread selection)
- [ ] Update `SocialFeed` (division/community filtering)
- [ ] Create navigation breadcrumb component
- [ ] Update post transformers (include community_id, thread_id)
- [ ] Test complete workflow

### Testing
- [ ] Test community creation with division
- [ ] Test thread creation in community
- [ ] Test post creation (community-level)
- [ ] Test post creation (thread-level)
- [ ] Test ban functionality
- [ ] Test division filtering
- [ ] Test all social interactions with new structure

## Migration Strategy

### For Existing Communities
1. Run migration (adds nullable division field)
2. Manually assign divisions to existing communities via Django admin
3. Later: Make division required (new migration)

### For Existing Posts
- No changes needed (posts already have community FK)
- Just verify community has division assigned

### For Existing Memberships
- Keep memberships where role is not null (moderators/admins)
- Keep memberships where status = 'banned'
- Optionally delete regular member records (no longer needed)

## Next Steps

1. ✅ Update Community model (DONE)
2. Create migrations
3. Update serializers and views
4. Update frontend components
5. Test complete workflow
6. Deploy and monitor

---

**Last Updated:** October 9, 2025
**Status:** Backend model updates complete, migrations pending
