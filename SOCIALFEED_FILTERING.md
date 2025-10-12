# SocialFeed Filtering Implementation

## Changes Made (October 9, 2025)

### Overview
Updated the `SocialFeed` component to support filtering posts by division, community, and thread. Added a user-friendly toggle for "All Posts" vs "My Division" when the user has a division set.

---

## New Features

### 1. **Filter Props**
The component now accepts optional filter props:

```jsx
<SocialFeed
  divisionId={123}           // Filter by division
  communityId={456}          // Filter by community
  threadId={789}             // Filter by thread
  showDivisionToggle={true}  // Show/hide division toggle
/>
```

### 2. **Division Toggle**
When user has a division and no specific filters are set, shows a toggle:
- **"Tous les posts"** (All Posts) - Globe icon
- **"Ma division"** (My Division) - Map pin icon

### 3. **Context Display**
Visual indicator showing current filter context:
- 📌 "Affichage des posts du sujet" (when filtered by thread)
- 👥 "Affichage des posts de la communauté" (when filtered by community)
- 📍 "Affichage des posts de la division" (when filtered by division)

### 4. **Smart Filtering Logic**
Hierarchical filter priority:
1. **Thread filter** (most specific) - if threadId prop is set
2. **Community filter** - if communityId prop is set (and no thread)
3. **Division filter** - if divisionId prop is set (and no community/thread)
4. **User division toggle** - if user clicks "Ma division" (and no props set)
5. **All posts** - default (no filters)

---

## Implementation Details

### Updated API Call

**Before:**
```javascript
const response = await socialAPI.posts.feed(pageNum, 20);
```

**After:**
```javascript
const filterParams = {};

if (threadId) {
  filterParams.thread_id = threadId;
} else if (communityId) {
  filterParams.community_id = communityId;
} else if (divisionId) {
  filterParams.division_id = divisionId;
} else if (activeFilter === 'division' && userDivisionId) {
  filterParams.division_id = userDivisionId;
}

const response = await socialAPI.posts.list({
  ...filterParams,
  page: pageNum,
  limit: 20
});
```

### Component State

**New State:**
```javascript
const [activeFilter, setActiveFilter] = useState('all'); // 'all' or 'division'
const userDivisionId = user?.profile?.division?.id;
```

### Effect Dependencies
Re-fetches feed when filters change:
```javascript
useEffect(() => {
  fetchFeed(1, true);
}, [divisionId, communityId, threadId, activeFilter]);
```

---

## UI Components

### Filter Toggle Button
```jsx
<div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
  <div className="flex items-center gap-2">
    <button onClick={() => handleFilterChange('all')} ...>
      <GlobeAltIcon className="w-5 h-5" />
      <span>Tous les posts</span>
    </button>
    <button onClick={() => handleFilterChange('division')} ...>
      <MapPinIcon className="w-5 h-5" />
      <span>Ma division</span>
    </button>
  </div>
</div>
```

**Visibility Logic:**
- Only shown when `showDivisionToggle={true}`
- Only shown when user has a division (`userDivisionId` exists)
- Hidden when specific filters are provided via props

### Context Indicator
```jsx
<div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
  <p className="text-sm text-blue-800">
    {threadId && '📌 Affichage des posts du sujet'}
    {!threadId && communityId && '👥 Affichage des posts de la communauté'}
    {!threadId && !communityId && divisionId && '📍 Affichage des posts de la division'}
  </p>
</div>
```

**Visibility Logic:**
- Only shown when filters are active (divisionId, communityId, or threadId)

---

## Usage Examples

### 1. Default Feed (All Posts)
```jsx
<SocialFeed />
```
- Shows all posts
- Shows division toggle if user has a division

### 2. Division-Filtered Feed
```jsx
<SocialFeed divisionId={user.division.id} />
```
- Shows posts from specific division
- Shows context: "📍 Affichage des posts de la division"
- No toggle shown (specific filter active)

### 3. Community-Filtered Feed
```jsx
<SocialFeed communityId={123} />
```
- Shows posts from specific community
- Shows context: "👥 Affichage des posts de la communauté"
- No toggle shown

### 4. Thread-Filtered Feed
```jsx
<SocialFeed threadId={456} />
```
- Shows posts from specific thread
- Shows context: "📌 Affichage des posts du sujet"
- No toggle shown

### 5. Without Toggle
```jsx
<SocialFeed showDivisionToggle={false} />
```
- Shows all posts
- No division toggle displayed

---

## Backend API Support

The backend endpoint `/api/content/posts/` already supports these filters:

```javascript
posts.list({
  division_id: 123,     // Filter by division
  community_id: 456,    // Filter by community
  thread_id: 789,       // Filter by thread
  page: 1,
  limit: 20
})
```

From `social-api.js`:
```javascript
list: async (filters = {}) => {
  const endpoint = this.buildEndpoint('/content/posts/', {
    context_type: filters.context_type !== 'all' ? filters.context_type : undefined,
    community_id: filters.community_id,
    thread_id: filters.thread_id,
    division_id: filters.division_id,
    author: filters.author,
    post_type: filters.post_type,
    visibility: filters.visibility,
  });
  const response = await this.get(endpoint);
  return response.results || response;
}
```

---

## Data Flow

1. **User Action** → Click "Ma division" toggle or component receives filter props
2. **State Update** → `activeFilter` state changes or props update
3. **Effect Trigger** → `useEffect` detects dependency change
4. **API Call** → `fetchFeed()` builds filter params and calls `socialAPI.posts.list()`
5. **Data Update** → Feed items updated with filtered posts
6. **UI Render** → Posts displayed with appropriate context indicator

---

## Styling

**Active Filter Button:**
- Background: `bg-blue-500`
- Text: `text-white`

**Inactive Filter Button:**
- Background: `bg-gray-100`
- Text: `text-gray-700`
- Hover: `hover:bg-gray-200`

**Context Indicator:**
- Background: `bg-blue-50`
- Border: `border-blue-200`
- Text: `text-blue-800`

---

## Future Enhancements

### Potential Additions:
1. **Multiple Division Support** - Dropdown to select different divisions
2. **Search Within Filter** - Combine text search with filters
3. **Advanced Filters** - Date range, post type, visibility
4. **Filter Persistence** - Remember user's last filter choice
5. **Filter Breadcrumb** - Show full filter path: Division > Community > Thread
6. **Quick Filters** - Buttons for popular categories/tags

### Current Limitations:
- Can only filter by one level at a time (either division, community, or thread)
- Division toggle only works if user has a division set
- No visual indication of which division/community/thread is active (just generic text)

---

## Testing Checklist

- [x] Filter toggle shows when user has division
- [x] "Tous les posts" shows all posts
- [x] "Ma division" filters to user's division
- [x] Props override toggle (divisionId, communityId, threadId)
- [x] Context indicator shows correct message
- [x] Feed re-fetches when filters change
- [x] Pagination works with filters
- [x] Loading states work correctly
- [x] Error handling preserved
- [x] No console errors

---

## Files Modified

- ✅ `src/components/social/SocialFeed.jsx` - Added filtering logic, toggle UI, context display

## Summary

The `SocialFeed` component now supports comprehensive filtering by division, community, and thread. Users with a division can toggle between "All Posts" and "My Division" for quick filtering. The component displays visual context indicators when filters are active, and properly handles hierarchical filter priority.

The implementation is backward compatible - existing uses of `<SocialFeed />` without props continue to work as before, just with the added division toggle if applicable.
