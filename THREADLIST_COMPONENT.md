# ThreadList Component

## Overview
The ThreadList component displays all discussion threads within a community. It provides an organized view of topics with metadata like post count, creator info, and last activity timestamps.

## Purpose
- Display threads in a community
- Show thread engagement metrics (posts, views)
- Provide navigation to individual threads
- Handle loading and error states gracefully

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `communityId` | number | Yes | ID of the community whose threads to display |
| `onThreadSelect` | function | No | Callback when thread is clicked. Receives thread object. If not provided, navigates to `/community/{communityId}/thread/{threadId}` |

## Features

### 1. **Thread Display**
- Shows thread title with chat bubble icon
- Displays thread body preview (line-clamped to 2 lines)
- Metadata row with:
  - Post count (with icon)
  - Creator info (display name or username)
  - Last activity timestamp (relative, in French)
- Optional view count (if available)

### 2. **Interactive States**
- **Hover**: Border turns blue, shadow increases, title changes color, arrow icon highlights
- **Click**: Calls `onThreadSelect(thread)` or navigates to thread page
- **Loading**: Shows 3 skeleton cards with pulse animation
- **Error**: Red alert box with retry button
- **Empty**: Friendly message with chat bubble icon

### 3. **Visual Design**
- White cards with subtle shadows
- Purple chat bubble icons for threads
- Gray metadata text with icons
- Blue accent on hover
- Responsive layout with proper spacing

## Usage Examples

### Basic Usage
```jsx
import ThreadList from '../components/social/ThreadList';

function CommunityPage({ communityId }) {
  return (
    <div className="max-w-4xl mx-auto p-4">
      <h2 className="text-2xl font-bold mb-4">Sujets de discussion</h2>
      <ThreadList communityId={communityId} />
    </div>
  );
}
```

### With Custom Thread Selection
```jsx
function CommunityPage() {
  const [selectedThread, setSelectedThread] = useState(null);

  const handleThreadSelect = (thread) => {
    console.log('Thread selected:', thread);
    setSelectedThread(thread);
    // Custom logic: maybe filter SocialFeed by thread ID
  };

  return (
    <div>
      <ThreadList
        communityId={communityId}
        onThreadSelect={handleThreadSelect}
      />

      {selectedThread && (
        <SocialFeed threadId={selectedThread.id} />
      )}
    </div>
  );
}
```

### Integrated with SocialFeed Filtering
```jsx
function CommunityFeed({ communityId }) {
  const [threadId, setThreadId] = useState(null);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Thread Sidebar */}
      <div className="lg:col-span-1">
        <h3 className="font-semibold mb-3">Sujets</h3>
        <ThreadList
          communityId={communityId}
          onThreadSelect={(thread) => setThreadId(thread.id)}
        />
      </div>

      {/* Feed Main Area */}
      <div className="lg:col-span-2">
        <SocialFeed
          communityId={communityId}
          threadId={threadId}
        />
      </div>
    </div>
  );
}
```

### In Division/Community Browser
```jsx
function DivisionView({ divisionId }) {
  const [selectedCommunity, setSelectedCommunity] = useState(null);

  return (
    <div>
      {/* Community list */}
      <CommunityList
        divisionId={divisionId}
        onCommunitySelect={setSelectedCommunity}
      />

      {/* Show threads when community selected */}
      {selectedCommunity && (
        <div className="mt-6">
          <h3 className="text-xl font-bold mb-3">
            Sujets dans {selectedCommunity.name}
          </h3>
          <ThreadList communityId={selectedCommunity.id} />
        </div>
      )}
    </div>
  );
}
```

## API Integration

### Endpoint Used
- `GET /communities/api/threads/?community_id={communityId}`

### API Method
```javascript
socialAPI.threads.list(communityId)
```

### Response Format
```javascript
{
  results: [
    {
      id: 1,
      title: "Thread title",
      body: "Thread description or first message...",
      slug: "thread-title",
      community: 5,
      creator: {
        id: 10,
        username: "johndoe",
        display_name: "John Doe"
      },
      posts_count: 15,
      view_count: 234,
      created_at: "2024-01-15T10:30:00Z",
      updated_at: "2024-01-20T14:45:00Z"
    },
    // ... more threads
  ]
}
```

## State Management

### Local State
```javascript
const [threads, setThreads] = useState([]);       // Thread list
const [loading, setLoading] = useState(true);     // Loading state
const [error, setError] = useState(null);         // Error message
```

### Data Flow
1. **Mount/Community Change** → `useEffect` triggers `fetchThreads()`
2. **Fetch Start** → Set `loading = true`, clear error
3. **API Call** → `socialAPI.threads.list(communityId)`
4. **Success** → Set threads, `loading = false`
5. **Error** → Set error message, `loading = false`
6. **Click** → Call `onThreadSelect(thread)` or navigate

## Visual States

### Loading Skeleton
```
┌─────────────────────────────────────┐
│ ████████████████░░░░░░░░░░░░░░░░░░ │
│ ██████████░░░░░░░░░░░░░░░░░░░░░░░░ │
└─────────────────────────────────────┘
(Repeated 3 times with pulse animation)
```

### Thread Card
```
┌─────────────────────────────────────────────┐
│ 💬 Thread Title                          → │
│    Thread body preview text that can span  │
│    up to two lines before being truncated  │
│                                             │
│    💬 5 posts  👤 par JohnDoe  🕐 il y a 2h│
│─────────────────────────────────────────────│
│    234 vues                                 │
└─────────────────────────────────────────────┘
```

### Empty State
```
┌─────────────────────────────────────┐
│              💬                      │
│                                      │
│         Aucun sujet                  │
│  Aucun sujet de discussion n'a été   │
│  créé dans cette communauté.         │
└─────────────────────────────────────┘
```

### Error State
```
┌─────────────────────────────────────┐
│ ⚠️ Impossible de charger les sujets │
│                                      │
│         [ Réessayer ]                │
└─────────────────────────────────────┘
```

## Dependencies
- `react` - Core React hooks
- `react-router-dom` - Navigation (`useNavigate`)
- `@heroicons/react/24/outline` - Icons
- `date-fns` - Date formatting
- `date-fns/locale` - French locale
- `../../services/social-api` - API calls

## Styling
- **Framework**: Tailwind CSS
- **Colors**: Gray scale, blue accents, purple thread icons
- **Transitions**: Smooth hover effects on all interactive elements
- **Responsive**: Mobile-first design, adapts to container width

## Testing Checklist

### Functional Tests
- [ ] Threads load correctly for a valid community ID
- [ ] Loading skeleton shows during fetch
- [ ] Empty state displays when no threads exist
- [ ] Error state shows on API failure
- [ ] Retry button works after error
- [ ] Thread click calls `onThreadSelect` with correct thread object
- [ ] Default navigation works when `onThreadSelect` not provided
- [ ] Post count, view count display correctly
- [ ] Creator info shows display_name or falls back to username
- [ ] Relative timestamps show in French

### Visual Tests
- [ ] Cards have proper spacing and shadows
- [ ] Hover effects work (border, shadow, text color, arrow)
- [ ] Icons align correctly with text
- [ ] Line-clamp works for long thread bodies
- [ ] Thread metadata row doesn't wrap awkwardly
- [ ] Empty/error states are centered and clear

### Edge Cases
- [ ] Handle threads with no body (body is optional)
- [ ] Handle threads with 0 posts_count
- [ ] Handle missing view_count (conditional render)
- [ ] Handle missing creator info gracefully
- [ ] Handle invalid/null communityId
- [ ] Handle network timeout errors
- [ ] Re-fetch when communityId changes

## Integration Points

### Works With
- **SocialFeed**: Can filter feed by selected thread ID
- **PostCreationModal**: Thread creation can trigger refresh
- **Breadcrumb**: Thread selection updates navigation path
- **CommunityView**: Shows threads for current community
- **DivisionBrowser**: Displays threads when community selected

### Future Enhancements
- [ ] Pagination for large thread lists
- [ ] Search/filter threads by title
- [ ] Sort options (newest, most active, most posts)
- [ ] Pin/sticky threads at top
- [ ] Thread categories/tags
- [ ] Inline thread preview on hover
- [ ] Thread subscription/follow feature
- [ ] Thread moderation actions (for admins)
