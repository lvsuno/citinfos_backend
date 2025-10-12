# Breadcrumb Navigation Component

## Overview
The Breadcrumb component provides hierarchical navigation showing the user's current location in the application's geographic and community structure. It displays a clickable path from Home through Division → Community → Thread → Post.

## Purpose
- Show current location in the app hierarchy
- Enable quick navigation to parent levels
- Handle null divisions gracefully
- Provide visual context for user orientation

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `division` | object | No | Division object with `{ id, name, code }` |
| `community` | object | No | Community object with `{ id, name, slug }` |
| `thread` | object | No | Thread object with `{ id, title, slug }` |
| `post` | object | No | Post object with `{ id, title }` |
| `onNavigate` | function | No | Custom navigation handler. Receives `(item)` where item has `{ label, path, type, data }`. If not provided, uses React Router's `navigate()` |

## Features

### 1. **Hierarchical Display**
- **Home** (🏠) - Always first item
- **Division** (if exists) - Division name or code
- **All Communities** (if community exists without division)
- **Community** - Community name
- **Thread** - Thread title
- **Post** - Post title or "Post #{id}"

### 2. **Smart Null Handling**
- **Division is null**: Shows "Toutes les communautés" before community
- **No context**: Returns `null` (doesn't render if only Home)
- **Missing intermediate levels**: Builds path with available data

### 3. **Interactive Navigation**
- **Clickable items**: All except the last (current) item
- **Hover effect**: Blue background and text on hover
- **Disabled state**: Last item is bold, non-clickable (current location)
- **Custom handler**: Supports `onNavigate` for custom navigation logic

### 4. **Responsive Design**
- **Overflow handling**: Horizontal scroll for long paths
- **Text truncation**: Max-width 200px per item with ellipsis
- **Flexible layout**: Items wrap gracefully on small screens
- **Touch-friendly**: Proper spacing for mobile interaction

## Usage Examples

### Basic Usage (Division → Community)
```jsx
import Breadcrumb from '../components/common/Breadcrumb';

function CommunityPage({ community }) {
  return (
    <div>
      <Breadcrumb
        division={community.division_info}
        community={community}
      />
      <h1>{community.name}</h1>
      {/* Community content */}
    </div>
  );
}
```

### Community Without Division
```jsx
function PublicCommunityPage({ community }) {
  // community.division is null
  return (
    <div>
      <Breadcrumb
        division={null}
        community={community}
      />
      {/* Shows: Home > Toutes les communautés > {community.name} */}
    </div>
  );
}
```

### Full Hierarchy (Home → Division → Community → Thread)
```jsx
function ThreadPage({ division, community, thread }) {
  return (
    <div>
      <Breadcrumb
        division={division}
        community={community}
        thread={thread}
      />
      <h1>{thread.title}</h1>
      {/* Thread content */}
    </div>
  );
}
```

### Post View (Full Path)
```jsx
function PostPage({ post, thread, community, division }) {
  return (
    <div>
      <Breadcrumb
        division={division}
        community={community}
        thread={thread}
        post={post}
      />
      {/* Shows full path to this specific post */}
      <PostDetail post={post} />
    </div>
  );
}
```

### With Custom Navigation Handler
```jsx
function CustomNavigationPage() {
  const [activeView, setActiveView] = useState('thread');
  const [division, community, thread] = useContext(AppContext);

  const handleBreadcrumbNav = (item) => {
    console.log('Navigating to:', item.type);

    // Custom logic instead of React Router navigation
    switch (item.type) {
      case 'home':
        setActiveView('home');
        break;
      case 'division':
        setActiveView('division');
        // Maybe trigger a division change in context
        break;
      case 'community':
        setActiveView('community');
        break;
      case 'thread':
        setActiveView('thread');
        break;
    }
  };

  return (
    <div>
      <Breadcrumb
        division={division}
        community={community}
        thread={thread}
        onNavigate={handleBreadcrumbNav}
      />
      {/* Custom view rendering */}
    </div>
  );
}
```

### In Page Layout Header
```jsx
function PageLayout({ children, breadcrumbData }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6">
          {/* Breadcrumb in header */}
          <div className="mb-4 bg-white rounded-lg shadow-sm border border-gray-200 px-4">
            <Breadcrumb {...breadcrumbData} />
          </div>

          {/* Page content */}
          {children}
        </main>
      </div>
    </div>
  );
}

// Usage
<PageLayout breadcrumbData={{ division, community, thread }}>
  <ThreadContent />
</PageLayout>
```

### Integrated with SocialFeed Filtering
```jsx
function FeedWithBreadcrumb() {
  const [division, setDivision] = useState(null);
  const [community, setCommunity] = useState(null);
  const [thread, setThread] = useState(null);

  return (
    <div>
      <Breadcrumb
        division={division}
        community={community}
        thread={thread}
        onNavigate={(item) => {
          // Reset filters when navigating up the hierarchy
          if (item.type === 'division') {
            setCommunity(null);
            setThread(null);
          } else if (item.type === 'community') {
            setThread(null);
          }
        }}
      />

      <SocialFeed
        divisionId={division?.id}
        communityId={community?.id}
        threadId={thread?.id}
      />
    </div>
  );
}
```

## Path Building Logic

### Decision Tree
```
1. Always add: Home (🏠)
2. If division exists:
   → Add Division
3. Else if community exists without division:
   → Add "Toutes les communautés"
4. If community exists:
   → Add Community
5. If thread exists:
   → Add Thread
6. If post exists:
   → Add Post
```

### Example Paths

#### Full Hierarchy
```
🏠 Accueil > Montreal > Tech Enthusiasts > Best Practices Discussion > My Post Title
```

#### Community Without Division
```
🏠 Accueil > Toutes les communautés > Global Community > Thread Title
```

#### Division Only (User on Division Page)
```
🏠 Accueil > Quebec
```

#### Thread Without Division Info
```
🏠 Accueil > Toutes les communautés > Community Name > Thread Title
```

## Visual States

### Default Breadcrumb
```
🏠 Accueil  >  Montreal  >  Tech Community  >  Discussion Thread
────────     ──────────     ─────────────     ──────────────────
(clickable)   (clickable)    (clickable)       (current - bold)
```

### Hover State
```
🏠 Accueil  >  ┌─────────────┐  >  Tech Community  >  Discussion
               │  Montreal   │
               └─────────────┘
               (blue bg, blue text)
```

### Long Text Truncation
```
🏠 Accueil  >  Very Long Division Name That...  >  Community
                (max 200px, truncated with ellipsis)
```

### Overflow Scroll
```
← 🏠 Accueil > Division > Community > Very Long Thread Name > Post  →
  (Horizontal scroll when breadcrumb too wide)
```

## Item Data Structure

Each breadcrumb item has:
```javascript
{
  label: "Display text",          // String to show
  icon: HomeIcon,                  // React component (optional, only Home)
  path: "/division/123",           // Navigation path
  type: "division",                // Type identifier
  data: { /* original object */ }  // Original division/community/thread/post object
}
```

### Item Types
- `home` - Home/root
- `all-communities` - Placeholder when division is null
- `division` - Geographic division
- `community` - Community
- `thread` - Discussion thread
- `post` - Individual post

## Navigation Behavior

### Default Navigation (React Router)
```javascript
// Automatically uses navigate() from react-router-dom
onClick: (item) => navigate(item.path)
```

### Custom Navigation
```javascript
onNavigate={(item) => {
  console.log('Type:', item.type);
  console.log('Data:', item.data);
  console.log('Path:', item.path);

  // Custom logic
  if (item.type === 'community') {
    selectCommunity(item.data);
  }
}}
```

### Navigation Paths
- **Home**: `/`
- **Division**: `/division/{id}`
- **All Communities**: `/communities`
- **Community**: `/community/{slug}` or `/community/{id}`
- **Thread**: `/community/{community_slug}/thread/{thread_slug}`
- **Post**: `/post/{id}`

## Styling

### Tailwind Classes
- **Container**: `flex items-center space-x-2 text-sm`
- **Item Button**:
  - Default: `text-gray-600 hover:text-blue-600 hover:bg-blue-50`
  - Current: `text-gray-900 font-medium cursor-default`
- **Separator**: `text-gray-400` (ChevronRightIcon)
- **Responsive**: `overflow-x-auto` for horizontal scroll

### Color Scheme
- **Default text**: Gray-600
- **Hover text**: Blue-600
- **Current text**: Gray-900 (bold)
- **Separator**: Gray-400
- **Hover background**: Blue-50

## Edge Cases

### Null Division Handling
```javascript
// Case 1: Community with division
<Breadcrumb division={division} community={community} />
// → Home > {division.name} > {community.name}

// Case 2: Community without division
<Breadcrumb division={null} community={community} />
// → Home > Toutes les communautés > {community.name}

// Case 3: No division, no community (returns null)
<Breadcrumb division={null} community={null} />
// → (doesn't render)
```

### Missing Data
- **Division has no name**: Falls back to `division.code`
- **Post has no title**: Shows `Post #{post.id}`
- **Thread/Community slug missing**: Uses numeric `id` in path
- **Only Home item**: Component returns `null` (doesn't render)

### Long Paths
- Items truncate at 200px with ellipsis
- Container scrolls horizontally
- Separators remain visible during scroll
- Last item (current) always visible

## Dependencies
- `react` - Core React
- `react-router-dom` - Navigation (`useNavigate`)
- `@heroicons/react/24/outline` - Icons (ChevronRightIcon, HomeIcon)

## Testing Checklist

### Functional Tests
- [ ] Renders with division + community
- [ ] Renders with community (no division) - shows "Toutes les communautés"
- [ ] Renders full path: home → division → community → thread → post
- [ ] Returns null when only home (no context)
- [ ] Home item always has HomeIcon
- [ ] Clicking home navigates to `/`
- [ ] Clicking division navigates to `/division/{id}`
- [ ] Clicking community navigates to `/community/{slug}`
- [ ] Clicking thread navigates to correct path
- [ ] Last item is not clickable (disabled)
- [ ] Last item is bold
- [ ] Custom `onNavigate` handler is called with correct item
- [ ] Default React Router navigation works
- [ ] Division falls back to code if name missing
- [ ] Post shows "Post #{id}" if title missing

### Visual Tests
- [ ] Items have proper spacing
- [ ] Separators (ChevronRight) display between items
- [ ] Hover changes text color to blue
- [ ] Hover adds blue background
- [ ] Current item is bold and dark gray
- [ ] Icons align properly with text
- [ ] Text truncates at 200px with ellipsis
- [ ] Horizontal scroll appears when needed
- [ ] Responsive layout works on mobile

### Edge Cases
- [ ] Handle null division with community
- [ ] Handle missing division.name (use code)
- [ ] Handle missing community.slug (use id)
- [ ] Handle missing thread.slug (use id)
- [ ] Handle missing post.title (use "Post #{id}")
- [ ] Handle very long division/community/thread names
- [ ] Handle special characters in names
- [ ] Handle undefined props gracefully
- [ ] Handle rapid navigation clicks

## Integration Points

### Works With
- **SocialFeed**: Shows current filter context
- **ThreadList**: Displays community → thread path
- **PostDetail**: Shows full path to post
- **DivisionCommunitySelector**: Updates breadcrumb on selection
- **Page Layouts**: Header navigation context

### Component Composition
```
Breadcrumb
  └─ For each item:
      ├─ Button (clickable or disabled)
      │   ├─ Icon (optional, Home only)
      │   └─ Label (truncated)
      └─ Separator (ChevronRight, except last)
```

## Accessibility

### ARIA Support (Future Enhancement)
- [ ] Add `aria-label="breadcrumb navigation"`
- [ ] Add `aria-current="page"` to last item
- [ ] Ensure keyboard navigation works
- [ ] Add focus visible styles

### Current Accessibility
- ✅ Semantic `<nav>` element
- ✅ Clickable buttons (not divs)
- ✅ Disabled state for current item
- ✅ Proper hover states
- ✅ Touch-friendly sizing

## Performance

### Optimizations
- Early return when no context (doesn't render)
- Minimal re-renders (no internal state)
- Efficient array building
- No unnecessary API calls

### Best Practices
- Pass only necessary prop data
- Use `slug` for navigation when available
- Memoize parent component if props change frequently

## Future Enhancements
- [ ] Mobile breadcrumb collapse (show only last 2 items)
- [ ] Breadcrumb dropdown for middle items
- [ ] Copy path to clipboard
- [ ] Share link from breadcrumb
- [ ] Tooltip showing full text on hover (for truncated items)
- [ ] Animation when path changes
- [ ] Schema.org breadcrumb markup for SEO
- [ ] Custom icons per item type
- [ ] Breadcrumb history (back/forward navigation)
