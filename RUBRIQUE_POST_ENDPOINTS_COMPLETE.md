# Rubrique-Based Post Endpoints - COMPLETE ✅

**Date:** October 16, 2025
**Status:** ✅ FULLY IMPLEMENTED AND TESTED

## Overview

Implemented endpoints to fetch posts by rubrique, with "Accueil" showing all community posts and rubrique-specific pages showing filtered posts. Posts now include thread information when applicable.

## New Endpoints

### 1. Accueil (Home) - All Recent Posts

**Endpoint:** `GET /api/communities/{slug}/posts/accueil/`
**Permission:** Public (AllowAny)
**Purpose:** Get all recent posts from a community, regardless of rubrique

**Query Parameters:**
- `limit` - Number of posts to return (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response:**
```json
{
  "community_id": "uuid",
  "community_name": "Sherbrooke",
  "total_posts": 8,
  "posts": [
    {
      "id": "uuid",
      "author_name": "Elvis Something",
      "content": "Post content...",
      "thread_id": null,
      "thread_title": null,
      "thread_slug": null,
      "rubrique_id": "uuid",
      "rubrique_name": "Événements",
      "rubrique_type": "evenements",
      "created_at": "2025-10-16T...",
      ...
    }
  ]
}
```

**Test Result:**
```bash
curl http://localhost:8000/api/communities/sherbrooke/posts/accueil/
```
- ✅ Returns 8 posts from Sherbrooke community
- ✅ Posts ordered by most recent first
- ✅ Includes thread information when applicable
- ✅ Includes rubrique information (from thread or direct post)

### 2. Rubrique-Specific Posts

**Endpoint:** `GET /api/communities/{slug}/rubriques/{rubrique_type}/posts/`
**Permission:** Public (AllowAny)
**Purpose:** Get posts for a specific rubrique (including posts in threads)

**URL Parameters:**
- `slug` - Community slug (e.g., "sherbrooke")
- `rubrique_type` - Rubrique template type (e.g., "evenements", "sport_hockey")

**Query Parameters:**
- `limit` - Number of posts to return (default: 20)
- `offset` - Offset for pagination (default: 0)

**Response:**
```json
{
  "community_id": "uuid",
  "community_name": "Sherbrooke",
  "rubrique_id": "uuid",
  "rubrique_name": "Hockey",
  "rubrique_type": "sport_hockey",
  "total_posts": 2,
  "posts": [
    {
      "id": "uuid",
      "author_name": "elvis togban",
      "content": "Post content...",
      "thread_id": null,
      "thread_title": null,
      "rubrique_id": "uuid",
      "rubrique_name": "Hockey",
      "rubrique_type": "sport_hockey",
      ...
    }
  ]
}
```

**Filtering Logic:**
Posts are included if EITHER:
1. `post.rubrique_template` matches the requested rubrique (direct posts)
2. `post.thread.rubrique_template` matches the requested rubrique (thread posts)

**Test Results:**
```bash
# Test Événements rubrique
curl http://localhost:8000/api/communities/sherbrooke/rubriques/evenements/posts/
```
- ✅ Returns 1 post with rubrique="Événements"
- ✅ Correctly filters by rubrique

```bash
# Test Hockey rubrique
curl http://localhost:8000/api/communities/sherbrooke/rubriques/sport_hockey/posts/
```
- ✅ Returns 2 posts with rubrique="Hockey"
- ✅ Correctly filters subsection rubriques

**Error Handling:**
- Returns 404 if rubrique doesn't exist or is inactive
- Returns 403 if rubrique is not enabled for the community
- Returns empty posts array if no posts in rubrique

## Serializer Updates

### UnifiedPostSerializer Enhancements

**New Fields Added:**

#### Thread Information
```python
thread_id = serializers.UUIDField(source='thread.id', read_only=True)
thread_title = serializers.CharField(source='thread.title', read_only=True)
thread_slug = serializers.CharField(source='thread.slug', read_only=True)
```

#### Rubrique Information
```python
rubrique_id = serializers.SerializerMethodField()
rubrique_name = serializers.SerializerMethodField()
rubrique_type = serializers.SerializerMethodField()
```

**Getter Methods:**
```python
def get_rubrique_id(self, obj):
    """Get rubrique ID - from thread if in thread, otherwise from post."""
    if obj.thread and obj.thread.rubrique_template:
        return str(obj.thread.rubrique_template.id)
    elif obj.rubrique_template:
        return str(obj.rubrique_template.id)
    return None

def get_rubrique_name(self, obj):
    """Get rubrique name - from thread or post."""
    if obj.thread and obj.thread.rubrique_template:
        return obj.thread.rubrique_template.default_name
    elif obj.rubrique_template:
        return obj.rubrique_template.default_name
    return None

def get_rubrique_type(self, obj):
    """Get rubrique type - from thread or post."""
    if obj.thread and obj.thread.rubrique_template:
        return obj.thread.rubrique_template.template_type
    elif obj.rubrique_template:
        return obj.rubrique_template.template_type
    return None
```

**Logic:**
- If post belongs to a thread → use thread's rubrique_template
- If post is direct (no thread) → use post's rubrique_template
- Returns None if neither exists

## Database Query Optimization

### Accueil Endpoint Query
```python
posts = Post.objects.filter(
    community=community,
    is_deleted=False
).select_related(
    'author__user',
    'thread',
    'thread__rubrique_template',
    'rubrique_template',
    'community'
).prefetch_related(
    'media',
    'polls__options'
).order_by('-created_at')[offset:offset + limit]
```

**Optimizations:**
- `select_related` - Reduces N+1 queries for foreign keys
- `prefetch_related` - Efficiently loads many-to-many relationships
- `[offset:offset + limit]` - Database-level pagination

### Rubrique-Specific Endpoint Query
```python
posts = Post.objects.filter(
    community=community,
    is_deleted=False
).filter(
    Q(rubrique_template=rubrique) |  # Direct posts
    Q(thread__rubrique_template=rubrique)  # Thread posts
).select_related(...).prefetch_related(...).order_by('-created_at')
```

**Features:**
- Uses Q objects for OR filtering
- Includes both direct posts and thread posts
- Same optimization as Accueil endpoint

## Frontend Integration

### Usage Examples

#### Fetch Accueil Posts
```javascript
// src/services/communityAPI.js
async getAccueilPosts(communitySlug, limit = 20, offset = 0) {
  const response = await apiService.get(
    `/communities/${communitySlug}/posts/accueil/`,
    { params: { limit, offset } }
  );
  return response.data;
}
```

#### Fetch Rubrique-Specific Posts
```javascript
async getRubriquePosts(communitySlug, rubriqueType, limit = 20, offset = 0) {
  const response = await apiService.get(
    `/communities/${communitySlug}/rubriques/${rubriqueType}/posts/`,
    { params: { limit, offset } }
  );
  return response.data;
}
```

#### Display Thread Link
```javascript
// In post component
{post.thread_id && (
  <Link to={`/${urlPath}/${communitySlug}/threads/${post.thread_slug}`}>
    <ThreadIcon />
    View full thread: {post.thread_title}
  </Link>
)}
```

## Data Flow

```
┌────────────────────────────────────────────────────────────┐
│                     ACCUEIL (HOME)                          │
└────────────────────────────────────────────────────────────┘

User → Navigate to /city/sherbrooke/accueil
  ↓
Frontend → GET /api/communities/sherbrooke/posts/accueil/
  ↓
Backend → Query ALL posts from community
  ↓
Response → {
  community_name: "Sherbrooke",
  total_posts: 8,
  posts: [all posts ordered by created_at DESC]
}


┌────────────────────────────────────────────────────────────┐
│                  RUBRIQUE-SPECIFIC                          │
└────────────────────────────────────────────────────────────┘

User → Navigate to /city/sherbrooke/evenements
  ↓
Frontend → GET /api/communities/sherbrooke/rubriques/evenements/posts/
  ↓
Backend → Query posts WHERE:
  - post.rubrique_template = "evenements" OR
  - post.thread.rubrique_template = "evenements"
  ↓
Response → {
  rubrique_name: "Événements",
  rubrique_type: "evenements",
  total_posts: 1,
  posts: [filtered posts]
}


┌────────────────────────────────────────────────────────────┐
│                    THREAD CONTEXT                           │
└────────────────────────────────────────────────────────────┘

Post in response includes:
{
  thread_id: "uuid" or null,
  thread_title: "Discussion title" or null,
  thread_slug: "discussion-slug" or null,
  rubrique_id: "uuid",
  rubrique_name: "Événements",
  rubrique_type: "evenements"
}

If thread_id exists:
  → Frontend can display "View full thread" link
  → Link to: /city/sherbrooke/threads/discussion-slug
```

## Verification Results

### Test Data
- **Community:** Sherbrooke
- **Total Posts:** 8
- **Posts by Rubrique:**
  - Événements: 1 post
  - Hockey (sport_hockey): 2 posts
  - Art: 1 post
  - Commerces: 1 post
  - Reconnaissance: 1 post
  - Concerts (evenements_concerts): 1 post
  - Photographie: 1 post

### Endpoint Tests

| Endpoint | Test | Result |
|----------|------|--------|
| `/posts/accueil/` | Returns all posts | ✅ 8 posts returned |
| `/posts/accueil/` | Ordered by recent | ✅ DESC created_at |
| `/posts/accueil/` | Includes thread info | ✅ thread_id, title, slug |
| `/posts/accueil/` | Includes rubrique info | ✅ rubrique_id, name, type |
| `/rubriques/evenements/posts/` | Filters by rubrique | ✅ 1 post |
| `/rubriques/sport_hockey/posts/` | Subsection filtering | ✅ 2 posts |
| `/rubriques/invalid/posts/` | Invalid rubrique | ✅ 404 error |
| Both endpoints | Public access | ✅ No auth required |
| Both endpoints | Pagination | ✅ limit/offset params |

## Implementation Files

### Modified Files

1. **communities/views.py:**
   - Added `accueil_posts()` action method
   - Added `rubrique_posts()` action method
   - Both use `@action` decorator with AllowAny permission

2. **content/unified_serializers.py:**
   - Added thread_id, thread_title, thread_slug fields
   - Added rubrique_id, rubrique_name, rubrique_type fields
   - Implemented getter methods for rubrique information
   - Logic prioritizes thread rubrique over post rubrique

### No Frontend Changes Required (Yet)
- Endpoints are ready to use
- Frontend needs to be updated to consume these endpoints
- Will replace hardcoded rubrique filtering

## Benefits

### 1. Accurate Post Distribution
- Posts appear in correct rubrique pages
- Thread posts inherit rubrique from thread
- Direct posts use their own rubrique

### 2. Thread Visibility
- Users can see when a post is part of a thread
- "View full thread" functionality enabled
- Better context for conversations

### 3. Performance
- Optimized queries with select_related/prefetch_related
- Database-level pagination
- No N+1 query problems

### 4. Flexibility
- Supports both direct posts and thread posts
- Works with hierarchical rubriques (subsections)
- Easy to add filtering/sorting options

### 5. User Experience
- Accueil shows everything (discovery)
- Rubrique pages show focused content (exploration)
- Thread links provide context (engagement)

## Next Steps

### Frontend Implementation

1. **Update Accueil Page:**
   ```javascript
   // src/pages/AccueilPage.js
   useEffect(() => {
     const fetchPosts = async () => {
       const data = await communityAPI.getAccueilPosts(communitySlug);
       setPosts(data.posts);
     };
     fetchPosts();
   }, [communitySlug]);
   ```

2. **Update Rubrique Pages:**
   ```javascript
   // src/pages/RubriquePage.js
   useEffect(() => {
     const fetchPosts = async () => {
       const data = await communityAPI.getRubriquePosts(
         communitySlug,
         rubriqueType
       );
       setPosts(data.posts);
     };
     fetchPosts();
   }, [communitySlug, rubriqueType]);
   ```

3. **Add Thread Link Component:**
   ```javascript
   // src/components/ThreadLink.js
   const ThreadLink = ({ post }) => {
     if (!post.thread_id) return null;

     return (
       <div className="thread-indicator">
         <ThreadIcon />
         <Link to={`/threads/${post.thread_slug}`}>
           View full thread: {post.thread_title}
         </Link>
       </div>
     );
   };
   ```

### API Enhancements (Future)

1. **Filtering Options:**
   - Filter by post_type (text, image, video, etc.)
   - Filter by date range
   - Filter by author

2. **Sorting Options:**
   - Sort by popularity (likes, comments)
   - Sort by trending score
   - Sort by views

3. **Advanced Features:**
   - Search within rubrique
   - Related posts
   - Popular threads

## Documentation

### API Documentation Format

```yaml
/api/communities/{slug}/posts/accueil/:
  get:
    summary: Get all recent posts for community (Accueil/Home)
    parameters:
      - name: slug
        in: path
        required: true
        schema:
          type: string
      - name: limit
        in: query
        schema:
          type: integer
          default: 20
      - name: offset
        in: query
        schema:
          type: integer
          default: 0
    responses:
      200:
        description: List of posts
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AccueilPostsResponse'

/api/communities/{slug}/rubriques/{rubrique_type}/posts/:
  get:
    summary: Get posts for specific rubrique
    parameters:
      - name: slug
        in: path
        required: true
      - name: rubrique_type
        in: path
        required: true
      - name: limit
        in: query
        schema:
          type: integer
          default: 20
      - name: offset
        in: query
        schema:
          type: integer
          default: 0
    responses:
      200:
        description: List of posts for rubrique
      404:
        description: Rubrique not found or inactive
      403:
        description: Rubrique not enabled for community
```

## Conclusion

✅ **COMPLETE AND TESTED**

Successfully implemented rubrique-based post endpoints with:
- Accueil showing all community posts
- Rubrique-specific pages showing filtered posts
- Thread information included in all post responses
- Optimized database queries
- Public API access (no authentication required)

All posts now correctly appear in their respective rubriques, and users can navigate to threads when applicable.

**Ready for frontend integration!** 🎉

---

**Implementation completed on October 16, 2025** 🚀
