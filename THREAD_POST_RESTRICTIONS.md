# Thread Post Type Restrictions

## Overview
This document explains the content type restrictions and character limits for posts in different contexts within the application.

## Post Types and Contexts

### 1. Regular Posts (Feed/Community)
**Location**: Main feed, community pages, section pages
**Character Limit**: 1,000 characters
**Available Features**:
- ✅ Text posts
- ✅ Media attachments (images, videos, audio, files)
- ✅ Polls
- ✅ Create article (via "Advanced" menu)
- ✅ Create thread (via "Advanced" menu)

**Implementation**: `InlinePostCreator` with `threadId={null}`

---

### 2. Posts Inside Threads (Thread Replies)
**Location**: Thread detail page - replies to existing thread
**Character Limit**: 2,000 characters
**Available Features**:
- ✅ Text posts
- ✅ Media attachments (images, videos, audio, files)
- ✅ Polls
- ❌ **Cannot create articles** (articles are standalone content)
- ❌ **Cannot create threads** (no nested threads)

**Restrictions**:
- `threadId` prop is present
- "Advanced" button is hidden
- Articles and threads cannot be created from within a thread
- Higher character limit (2,000) than regular posts to allow detailed responses

**Implementation**: `InlinePostCreator` with `threadId={threadId}`

```jsx
// Example usage in ThreadDetail
<InlinePostCreator
  division={division}
  community={community}
  threadId={threadId}  // <- This enables thread mode
  onPostCreated={handlePostCreated}
/>
```

---

### 3. First Post When Creating Thread
**Location**: Thread creation modal
**Character Limit**: 2,000 characters
**Available Features**:
- ✅ Text content with rich formatting
- ❌ No media attachments in initial post
- ❌ No polls in initial post
- Optional: Can create thread without initial post

**Implementation**: `ThreadCreatorModal` with `RichTextEditor`

**Usage Flow**:
1. User clicks "Nouveau sujet" from section page
2. Opens `ThreadCreatorModal`
3. Fills required title (5-200 characters)
4. Optional description (0-1,000 characters)
5. Optional first post (0-2,000 characters)

---

### 4. Articles (Long-Form Content)
**Location**: Community/section pages (not in threads)
**Character Limit**: 50,000 characters
**Available Features**:
- ✅ Rich text editing with full formatting
- ✅ Featured images
- ✅ Article metadata (excerpt, tags, etc.)
- ✅ Long-form content structure

**Restrictions**:
- ❌ **Cannot be created inside threads**
- ❌ Articles are standalone content, not thread replies
- Only accessible via "Advanced" → "Article enrichi" menu
- Menu hidden when `threadId` is present

**Implementation**: `RichArticleModal`

---

## Character Limits Summary

| Context | Limit | Reasoning |
|---------|-------|-----------|
| Regular Feed Posts | 1,000 chars | Quick updates, social sharing |
| Thread Replies | 2,000 chars | Detailed discussion responses |
| Thread First Post | 2,000 chars | Launch conversation with context |
| Thread Title | 200 chars | Concise, searchable topic |
| Thread Description | 1,000 chars | Additional context |
| Articles | 50,000 chars | Long-form, in-depth content |
| Poll Question | 500 chars | Clear question statement |
| Poll Option | 200 chars | Brief answer choice |

---

## Implementation Details

### InlinePostCreator Component
```jsx
{!threadId && (
  <div className="relative" ref={advancedMenuRef}>
    <button onClick={handleAdvancedClick}>
      <SparklesIcon />
      <span>Avancé</span>
    </button>

    {showAdvancedMenu && (
      <div className="dropdown-menu">
        <button onClick={handleRichArticle}>
          📝 Article enrichi
        </button>
        <button onClick={handleNewThread}>
          💬 Nouveau sujet
        </button>
      </div>
    )}
  </div>
)}
```

**Key Logic**:
- `!threadId` check hides "Advanced" button when inside thread
- `showAdvancedMenu && !threadId` double-checks dropdown visibility
- `maxLength={threadId ? 2000 : 1000}` adjusts character limit

### ThreadCreatorModal Component
```jsx
<RichTextEditor
  mode="inline"
  content={firstPostContent}
  onChange={setFirstPostContent}
  placeholder="Partagez votre première pensée sur ce sujet..."
  minHeight="120px"
  maxHeight="200px"
  maxLength={2000}  // <- Limited to 2000 chars
/>
```

**Character Counter**:
```jsx
<p className="text-xs text-gray-500 mt-1">
  {firstPostContent.length}/2000 caractères
</p>
```

---

## Validation Rules

### Backend Validation
The backend should enforce these rules:
```python
# Thread post validation
if post.thread_id:
    assert post.post_type not in ['article'], "Articles cannot be posts in threads"
    assert len(post.content) <= 2000, "Thread replies limited to 2000 characters"
    assert not post.thread_id, "Cannot create thread inside another thread"

# Article validation
if post.post_type == 'article':
    assert not post.thread_id, "Articles cannot be thread replies"
    assert len(post.content) <= 50000, "Articles limited to 50000 characters"
```

### Frontend Validation
- Character counters display remaining characters
- Submit button disabled when over limit
- Warning messages for restricted actions
- Hidden UI elements based on context

---

## User Experience

### When Creating Regular Post
1. User sees full toolbar: media, poll, advanced
2. Can create articles or threads via "Advanced" menu
3. Character limit: 1,000

### When Replying to Thread
1. User sees simplified toolbar: media, poll only
2. "Advanced" button is hidden
3. Character limit increased to 2,000 for detailed responses
4. Clear indication this is a reply context

### When Creating Thread
1. Modal-based workflow for focused thread creation
2. Required title (clear, searchable)
3. Optional description and first post
4. First post limited to 2,000 characters
5. Preview of how thread will appear

---

## Benefits of These Restrictions

1. **Content Organization**:
   - Threads keep discussions focused
   - Articles are prominent standalone content
   - No confusing nested thread structures

2. **User Experience**:
   - Clear mental model: threads for discussion, articles for long content
   - Appropriate character limits for each context
   - Simplified UI in thread replies

3. **Performance**:
   - Prevents extremely long thread replies
   - Keeps thread data structures manageable
   - Faster loading and rendering

4. **Content Quality**:
   - Encourages concise discussion responses
   - Pushes long-form content to article format
   - Better organized content hierarchy

---

## Testing Checklist

- [ ] Regular post creator shows "Advanced" button
- [ ] Thread reply creator hides "Advanced" button
- [ ] Regular posts limited to 1,000 characters
- [ ] Thread replies limited to 2,000 characters
- [ ] Thread first post limited to 2,000 characters
- [ ] Articles can be created from feed/community pages
- [ ] Articles cannot be created inside threads
- [ ] Threads can be created from section pages
- [ ] Threads cannot be created inside other threads
- [ ] Character counters display correctly
- [ ] Submit buttons disabled when over limit

---

## File Changes

### Modified Files:
1. **src/components/InlinePostCreator.jsx**
   - Added `!threadId` check to hide "Advanced" button
   - Conditional `maxLength`: 2000 in threads, 1000 otherwise
   - Added character counter for thread replies
   - Updated placeholder text for thread context

2. **src/components/modals/ThreadCreatorModal.jsx**
   - Added `maxLength={2000}` to first post RichTextEditor
   - Added character counter showing `{firstPostContent.length}/2000`

### Validation Points:
- Frontend: Character limits enforced via `maxLength` prop
- Backend: Should validate post_type restrictions server-side
- UI: Context-appropriate toolbars and options

---

## Future Enhancements

1. **Rich Content in Threads**:
   - Consider allowing media-rich first posts when creating threads
   - Currently first post is text-only; could add media picker

2. **Thread Depth Limits**:
   - Currently flat reply structure
   - Could add limited nesting (e.g., 2 levels) in future

3. **Dynamic Limits**:
   - Could adjust character limits based on user reputation/badges
   - Premium users might get higher limits

4. **Content Type Badges**:
   - Visual indicators for post types (article badge, thread badge)
   - Help users understand content hierarchy

---

## Related Documentation
- `DYNAMIC_THREAD_URLS_IMPLEMENTATION.md` - Thread routing and URLs
- `THREAD_DETAIL_COMPONENT.md` - Thread display implementation
- `SOCIAL_AUTH_README.md` - Authentication for post creation
