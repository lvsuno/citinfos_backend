# ThreadDetail Component

## Overview
The ThreadDetail component displays a single discussion thread with all its posts. It provides a full view of the thread conversation, allowing users to read all responses and add their own.

## Purpose
- Display thread title, body, and metadata
- List all posts within the thread (sorted by: pinned → best → votes → date)
- Allow users to create new posts in the thread
- Show thread creator badge
- Navigate back to community
- Handle loading and error states

## Route
```
/community/:communityId/thread/:threadId
```

## Props
This component uses React Router's `useParams()` hook to get:
- `communityId`: ID of the community containing the thread
- `threadId`: ID of the thread to display

## Features

### 1. **Thread Header**
- Large thread title with chat bubble icon
- Full thread body text (preserving whitespace and line breaks)
- Thread metadata:
  - Creator name (with "Créateur" badge if viewing own thread)
  - Creation timestamp (relative, in French)
  - Post count

### 2. **Post Creation**
- Inline post creator above the posts list
- Pre-filled with `threadId` to post in this thread
- Optional `showThreadOption={false}` to hide thread selector
- Calls `onPostCreated` to update UI with new post

### 3. **Posts List**
- **Header**: Shows post count ("X réponses")
- **Sorting**: Backend sorts posts by pinned → best → votes → created_at
- **Empty state**: Friendly message when no posts exist
- **Loading**: Skeleton cards while fetching
- **PostCard integration**: Uses existing PostCard component with all features

### 4. **Navigation**
- **Breadcrumb**: Shows Home → Community → Thread
- **Back button**: Returns to community page
- **Automatic**: Fetches community data for breadcrumb

### 5. **Realtime Updates**
- New posts added to top of list immediately
- Post count updates when posts created/deleted
- Posts can be edited/deleted inline (via PostCard)

## Usage Example

### Automatic (via ThreadList navigation)
```jsx
// User clicks thread in ThreadList
// ThreadList navigates to: /community/{communityId}/thread/{threadId}
// ThreadDetail auto-renders

<ThreadList
  communityId={communityId}
  onThreadSelect={(thread) => {
    // Default behavior navigates to ThreadDetail
  }}
/>
```

### Manual Navigation
```jsx
import { useNavigate } from 'react-router-dom';

function MyComponent() {
  const navigate = useNavigate();

  const openThread = (communityId, threadId) => {
    navigate(`/community/${communityId}/thread/${threadId}`);
  };

  return (
    <button onClick={() => openThread('comm-123', 'thread-456')}>
      View Thread
    </button>
  );
}
```

## API Integration

### Endpoints Used
1. **Get Thread**: `GET /api/threads/{threadId}/`
2. **Get Thread Posts**: `GET /api/threads/{threadId}/posts/`
   - Returns posts sorted by: pinned → best_post → net_votes → created_at
3. **Get Community** (for breadcrumb): `GET /api/communities/{communityId}/`

### API Methods
```javascript
// Fetch thread details
const thread = await socialAPI.threads.get(threadId);

// Fetch posts in thread (sorted)
const posts = await socialAPI.threads.posts(threadId);

// Fetch community info
const community = await socialAPI.communities.get(communityId);
```

### Response Format

**Thread Object:**
```javascript
{
  id: "thread-uuid",
  title: "Discussion Title",
  body: "Thread description or question...",
  slug: "discussion-title",
  community: "community-uuid",
  creator: {
    id: "profile-uuid",
    username: "johndoe",
    display_name: "John Doe"
  },
  posts_count: 15,
  view_count: 234,
  created_at: "2024-01-15T10:30:00Z",
  updated_at: "2024-01-20T14:45:00Z"
}
```

**Posts Array:**
```javascript
{
  results: [
    {
      id: "post-uuid",
      content: "Post content...",
      author: "profile-uuid",
      author_info: { username, display_name },
      is_pinned: false,
      is_best_post: false,
      upvotes_count: 10,
      downvotes_count: 2,
      comments_count: 5,
      created_at: "2024-01-15T11:00:00Z"
      // ... other post fields
    },
    // ... more posts (sorted)
  ]
}
```

## Component State

```javascript
const [thread, setThread] = useState(null);           // Thread object
const [posts, setPosts] = useState([]);               // Posts array
const [community, setCommunity] = useState(null);     // Community for breadcrumb
const [loading, setLoading] = useState(true);         // Initial load
const [error, setError] = useState(null);             // Error message
const [postsLoading, setPostsLoading] = useState(false); // Posts fetch
```

## Event Handlers

### handleBack()
Navigates back to community page or browser history.

### handlePostCreated(newPost)
- Adds new post to top of posts array
- Increments thread post count
- Called by InlinePostCreator `onPostCreated` prop

### handlePostDeleted(postId)
- Removes post from array
- Decrements thread post count
- Called by PostCard `onDelete` prop

### handlePostUpdated(updatedPost)
- Replaces post in array with updated version
- Called by PostCard `onUpdate` prop

## Visual States

### Loading State
```
┌────────────────────────────────┐
│ ████████░░░░░░░░░░░░ (title)  │
│ ██████████████░░░░ (body)     │
│ ████░░░░░░ (metadata)         │
│                                │
│ ████████████████ (post)       │
│ ████████████████ (post)       │
│ ████████████████ (post)       │
└────────────────────────────────┘
```

### Thread Header
```
┌────────────────────────────────────────┐
│ 💬  Discussion Thread Title            │
│                                         │
│ This is the thread body/description    │
│ that can span multiple lines...        │
│                                         │
│ 👤 JohnDoe [Créateur] 🕐 il y a 2h 💬 15 posts │
└────────────────────────────────────────┘
```

### Empty Posts
```
┌────────────────────────────────────────┐
│            💬                          │
│   Aucune réponse pour le moment        │
│   Soyez le premier à répondre !        │
└────────────────────────────────────────┘
```

### Error State
```
┌────────────────────────────────────────┐
│ ⬅ Retour                               │
│                                         │
│   ❌ Impossible de charger le sujet     │
│                                         │
│   [Réessayer]                           │
└────────────────────────────────────────┘
```

## Dependencies
- `react` - Core React hooks
- `react-router-dom` - useParams, useNavigate
- `@heroicons/react/24/outline` - Icons
- `date-fns` - Date formatting
- `date-fns/locale` - French locale
- `../../services/social-api` - API calls
- `../../contexts/AuthContext` - User authentication
- `./PostCard` - Post display component
- `../InlinePostCreator` - Post creation
- `../common/Breadcrumb` - Navigation breadcrumb

## Styling
- **Framework**: Tailwind CSS
- **Colors**: Purple for thread icons, gray scale, blue accents
- **Layout**: Max-width container (5xl), responsive padding
- **Cards**: White background, subtle shadows, rounded corners
- **Transitions**: Smooth hover effects

## Integration Points

### Works With
- **ThreadList**: Navigates to ThreadDetail when thread clicked
- **PostCard**: Displays individual posts with all features
- **InlinePostCreator**: Creates new posts in thread
- **Breadcrumb**: Shows navigation path
- **SocialFeed**: Could filter by threadId (not used here)

### Parent Components
- **App.js**: Route defined at `/community/:communityId/thread/:threadId`
- **MunicipalityDashboard**: Could integrate thread view in community section

## Thread Creator Privileges

The thread creator gets a special badge and has additional privileges (handled in backend):
- **Pin posts** in their thread (backend sorts pinned posts first)
- **Mark best post** to highlight the most helpful answer
- **Edit/delete thread** (via three-dot menu in ThreadList)

Badge display:
```jsx
{isThreadCreator && (
  <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
    Créateur
  </span>
)}
```

## Post Sorting

Posts are sorted by the backend in this priority order:
1. **Pinned posts** (is_pinned=true) → highest priority
2. **Best post** (is_best_post=true) → second priority
3. **Net votes** (upvotes - downvotes) → descending
4. **Created date** → oldest first (for same vote count)

This creates a Stack Overflow-style display where the most valuable content rises to the top.

## Testing Checklist

### Functional Tests
- [ ] Thread loads correctly with valid threadId
- [ ] Posts load and display in correct order
- [ ] Loading skeleton shows during initial fetch
- [ ] Error state displays on API failure
- [ ] Retry button works after error
- [ ] Back button navigates to community
- [ ] Breadcrumb shows correct path
- [ ] Thread creator badge shows for own threads
- [ ] InlinePostCreator creates posts in this thread
- [ ] New posts appear at top immediately
- [ ] Post count updates when posts created/deleted
- [ ] PostCard edit/delete functions work
- [ ] Empty state shows when no posts exist

### Visual Tests
- [ ] Thread header displays properly
- [ ] Thread body preserves whitespace and line breaks
- [ ] Metadata row doesn't wrap awkwardly
- [ ] Posts have proper spacing
- [ ] Loading skeletons animate smoothly
- [ ] Back button and breadcrumb align correctly
- [ ] Purple chat bubble icons consistent
- [ ] Responsive layout works on mobile
- [ ] Creator badge styled correctly

### Edge Cases
- [ ] Invalid threadId shows error
- [ ] Invalid communityId handled gracefully
- [ ] Thread with no posts shows empty state
- [ ] Long thread title/body display properly
- [ ] Very old threads show correct timestamps
- [ ] Missing creator info handled
- [ ] Network errors show retry option

## Future Enhancements
- [ ] Thread subscription/follow feature
- [ ] Thread edit modal (currently just console.log)
- [ ] Thread pinning (for mods/admins)
- [ ] Thread locking (prevent new posts)
- [ ] Thread tags/categories
- [ ] Thread view counter
- [ ] Thread sharing functionality
- [ ] Realtime post updates (WebSocket)
- [ ] Infinite scroll for large threads
- [ ] Jump to specific post (deep linking)
- [ ] Thread participants list
- [ ] Best answer highlighting (visual badge on post)

## Related Documentation
- `THREADLIST_COMPONENT.md` - Thread list component
- `POSTCARD_COMPONENT.md` - Individual post display
- `INLINE_POST_CREATOR.md` - Post creation UI
- `BREADCRUMB_COMPONENT.md` - Navigation breadcrumb
- `THREAD_CREATION_GUIDE.md` - Thread system overview

## Example Implementation

```jsx
// In App.js routing
<Route
  path="/community/:communityId/thread/:threadId"
  element={<ThreadDetail />}
/>

// User journey:
// 1. User views ThreadList in community
// 2. Clicks on a thread
// 3. ThreadList navigates to /community/123/thread/456
// 4. ThreadDetail loads and displays thread + posts
// 5. User can reply using InlinePostCreator
// 6. User can interact with posts (vote, comment, etc.)
// 7. User clicks back button to return to community
```

## Performance Considerations
- Thread and posts loaded in parallel (separate useEffects)
- Community fetch optional (only for breadcrumb)
- Posts use PostCard which has its own optimization
- No pagination yet (all posts load at once)
- Consider pagination for threads with 50+ posts

## Accessibility
- Semantic HTML structure
- Proper heading hierarchy (h1 for title, h2 for sections)
- Icon labels via title attributes
- Keyboard navigation support (via buttons)
- Focus management on back button
- Screen reader friendly loading states

## Browser Support
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Requires ES6+ support
- React 17+ compatible
- Tailwind CSS 3.x

---

**Status**: ✅ Implemented
**Last Updated**: October 16, 2025
**Component Path**: `/src/components/social/ThreadDetail.jsx`
**Route**: `/community/:communityId/thread/:threadId`
