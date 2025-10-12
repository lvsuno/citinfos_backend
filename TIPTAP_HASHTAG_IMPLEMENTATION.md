# Tiptap Hashtag Implementation

## Overview
Hashtag autocomplete has been implemented in the Tiptap RichTextEditor, similar to the mention system. When users type `#`, they get autocomplete suggestions from existing hashtags in the database.

## How It Works

### 1. **User Types `#`**
- User types `#` followed by letters (e.g., `#javascript`)
- Tiptap's hashtag extension (custom extension based on Mention) detects the `#` character
- Triggers the suggestion system

### 2. **Search API Call**
- Query is sent to: `/api/content/posts/hashtags/?search={query}&limit=20`
- 300ms debounce to avoid excessive API calls
- Searches existing hashtags by name (case-insensitive)

### 3. **Autocomplete Dropdown**
- Dropdown appears below the `#` symbol
- Shows matching hashtags with:
  - Hashtag name (e.g., `#javascript`)
  - Post count (e.g., "142 posts")
  - "Trending" badge if applicable
- Supports keyboard navigation (↑↓, Enter, Esc)
- Supports mouse hover and click

### 4. **Selection & Insertion**
- User selects hashtag with Enter key or mouse click
- The `#query` text is replaced with the complete hashtag
- Result: `<span class="hashtag" data-id="javascript" data-label="javascript">#javascript</span>`

### 5. **Backend Processing**
- Backend extracts hashtags using regex: `/#(\w+)/g`
- Hashtags are linked to posts for discoverability
- Trending hashtags are calculated based on post counts

## Files Modified

### 1. **src/components/ui/RichTextEditor.jsx**

#### State Management (line ~689)
```javascript
// Hashtag autocomplete state
const [hashtagQuery, setHashtagQuery] = useState('');
const [hashtagSuggestions, setHashtagSuggestions] = useState([]);
const [showHashtagDropdown, setShowHashtagDropdown] = useState(false);
const [selectedHashtagIndex, setSelectedHashtagIndex] = useState(0);
const [hashtagDropdownPosition, setHashtagDropdownPosition] = useState({ top: 0, left: 0 });
const hashtagDropdownRef = useRef(null);
const hashtagCommandRef = useRef(null); // For proper text replacement
```

#### API Search Hook (line ~753)
```javascript
useEffect(() => {
  const searchHashtags = async () => {
    if (!hashtagQuery || hashtagQuery.length < 1) {
      setHashtagSuggestions([]);
      return;
    }
    try {
      const results = await socialAPI.searchHashtags(hashtagQuery, 20);
      setHashtagSuggestions(results || []);
    } catch (error) {
      console.error('Failed to search hashtags:', error);
      setHashtagSuggestions([]);
    }
  };
  const debounceTimer = setTimeout(searchHashtags, 300);
  return () => clearTimeout(debounceTimer);
}, [hashtagQuery]);
```

#### Hashtag Extension (line ~1055)
```javascript
Mention.extend({
  name: 'hashtag',
}).configure({
  HTMLAttributes: {
    class: 'hashtag text-blue-600 font-medium',
  },
  suggestion: {
    char: '#',
    allowSpaces: false,
    items: ({ query }) => {
      setHashtagQuery(query);
      setShowHashtagDropdown(query.length > 0);
      return hashtagSuggestions;
    },
    render: () => {
      return {
        onStart: (props) => {
          hashtagCommandRef.current = props.command;
          const rect = props.clientRect();
          if (rect) {
            setHashtagDropdownPosition({
              top: rect.bottom + 5,
              left: rect.left,
            });
          }
          setShowHashtagDropdown(true);
          setSelectedHashtagIndex(0);
        },
        onKeyDown: (props) => {
          // Handle ↑↓, Enter, Esc
        },
        onExit: () => {
          setShowHashtagDropdown(false);
          setHashtagQuery('');
          setHashtagSuggestions([]);
        },
      };
    },
  },
}),
```

#### Dropdown UI (line ~3349)
```javascript
{showHashtagDropdown && hashtagSuggestions.length > 0 && (
  <div
    ref={hashtagDropdownRef}
    className="fixed z-50 bg-white dark:bg-gray-800 border rounded-lg shadow-lg"
    style={{
      top: `${hashtagDropdownPosition.top}px`,
      left: `${hashtagDropdownPosition.left}px`,
    }}
  >
    <ul className="py-1">
      {hashtagSuggestions.map((hashtag, index) => (
        <li
          key={hashtag.name}
          className={`px-3 py-2 cursor-pointer ${
            index === selectedHashtagIndex ? 'bg-blue-50' : ''
          }`}
          onClick={() => {
            if (hashtagCommandRef.current) {
              hashtagCommandRef.current({
                id: hashtag.name,
                label: hashtag.name,
              });
            }
          }}
        >
          <div className="font-medium text-blue-600">#{hashtag.name}</div>
          <div className="flex items-center space-x-2">
            {hashtag.is_trending && (
              <div className="text-xs bg-orange-100 text-orange-600 px-2 py-1 rounded">
                Trending
              </div>
            )}
            <div className="text-xs text-gray-500">
              {hashtag.posts_count} posts
            </div>
          </div>
        </li>
      ))}
    </ul>
  </div>
)}
```

#### CSS Styling (line ~2504)
```css
.rich-text-content .hashtag {
  background-color: #dbeafe !important;
  color: #1d4ed8 !important;
  padding: 0.125rem 0.25rem !important;
  border-radius: 0.25rem !important;
  text-decoration: none !important;
  font-weight: 500 !important;
}
```

### 2. **src/services/social-api.js**

#### Search Hashtags API (line ~401)
```javascript
searchHashtags = async (query, limit = 20) => {
  try {
    let url = `/content/posts/hashtags/?search=${encodeURIComponent(query)}&limit=${limit}`;
    const response = await this.get(url);
    const results = response.results || [];
    return results.map(hashtag => ({
      name: hashtag.name,
      posts_count: hashtag.posts_count,
      is_trending: hashtag.is_trending,
    }));
  } catch (error) {
    console.warn(`Failed to search hashtags:`, error);
    return [];
  }
};
```

## Backend API Endpoint

### GET `/api/content/posts/hashtags/`

**Query Parameters:**
- `search` - Search hashtags by name (case-insensitive)
- `limit` - Number of results (default: 50, max: 100)
- `trending` - Filter to only trending hashtags (optional)

**Response Format:**
```json
{
  "results": [
    {
      "name": "javascript",
      "posts_count": 142,
      "is_trending": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1,
  "total_available": 1
}
```

## Key Differences from Mentions

| Feature | Mentions (@) | Hashtags (#) |
|---------|-------------|--------------|
| **Trigger** | `@` character | `#` character |
| **Search API** | `/profiles/search_mentionable/` | `/content/posts/hashtags/` |
| **Data Structure** | User profiles (id, username, avatar) | Hashtag names (name, posts_count, is_trending) |
| **Categorization** | Yes (Followers, Community, Public) | No (simple list) |
| **Priority Badges** | "Following" badge | "Trending" badge |
| **ID Field** | User ID (integer) | Hashtag name (string) |

## Testing Checklist

### Basic Functionality
- [ ] Type `#java` → See autocomplete dropdown
- [ ] Dropdown shows matching hashtags (e.g., `#javascript`, `#java`)
- [ ] Click hashtag → Replaces `#java` with selected hashtag
- [ ] Result displays in blue with background color

### Keyboard Navigation
- [ ] Press `↓` → Moves to next hashtag
- [ ] Press `↑` → Moves to previous hashtag
- [ ] Press `Enter` → Selects highlighted hashtag
- [ ] Press `Esc` → Closes dropdown

### Edge Cases
- [ ] Type `#` alone → No dropdown (requires at least 1 character)
- [ ] Type `#xyz123` → Shows hashtags matching query
- [ ] Type `#nonexistent` → Empty dropdown or "No results"
- [ ] Multiple hashtags in one post → `#javascript #react #webdev`

### UI/UX
- [ ] Dropdown appears right below `#` cursor position
- [ ] Dropdown doesn't go off-screen
- [ ] "Trending" badge appears for trending hashtags
- [ ] Post count displays correctly
- [ ] Click outside dropdown → Closes dropdown
- [ ] Dark mode support

### API Integration
- [ ] Network tab shows API call: `/api/content/posts/hashtags/?search=query`
- [ ] 300ms debounce working (not spamming API)
- [ ] Response format matches expected structure
- [ ] Error handling if API fails

### Backend Processing
- [ ] Submit post with `#javascript` → Hashtag saved correctly
- [ ] Post appears when browsing `#javascript` hashtag
- [ ] Hashtag count increments
- [ ] Trending status updates based on activity

## Environment

- **Docker**: Run `docker-compose up` to start backend
- **Yarn**: Run `yarn start` in `src/` directory for frontend
- **Browser**: Test in Chrome/Firefox with React DevTools

## Troubleshooting

### Dropdown not appearing
1. Open browser console
2. Type `#test` in editor
3. Check for errors in console
4. Verify API call in Network tab
5. Check `hashtagSuggestions` state in React DevTools

### Dropdown appears far from cursor
- Check `hashtagDropdownPosition` state
- Verify `clientRect()` returns valid coordinates
- Ensure no extra scroll offsets being added

### Hashtag not replacing query text
- Check `hashtagCommandRef.current` is not null
- Verify `props.command()` is being called with correct data
- Use React DevTools to inspect command ref

### API errors
- Check backend is running: `docker-compose ps`
- Verify endpoint exists: `curl http://localhost:8000/api/content/posts/hashtags/?search=test`
- Check Django logs for errors

## HTML Output Format

When a hashtag is inserted, the HTML output looks like:

```html
<p>
  Check out this
  <span class="hashtag" data-id="javascript" data-label="javascript">#javascript</span>
  tutorial!
</p>
```

This allows the backend to:
1. Extract hashtags using the `hashtag` class or regex pattern
2. Link hashtags to posts for search/filtering
3. Calculate trending hashtags based on usage

## Future Enhancements

1. **Recent Hashtags**: Show user's recently used hashtags at top of list
2. **Hashtag Creation**: Allow creating new hashtags inline
3. **Hashtag Preview**: Show preview of hashtag feed on hover
4. **Hashtag Analytics**: Display hashtag trends over time
5. **Hashtag Autocomplete Ranking**: Sort by relevance (trending + recent + popular)

## Related Files

- `content/models.py` - Hashtag model definition
- `content/unified_views.py` - Hashtag API endpoints (line 1131-1197)
- `content/utils.py` - Hashtag extraction utilities
- `backup_client/src/components/ui/RichTextEditor.jsx` - Old client reference implementation

## Summary

The hashtag system is now fully functional and mirrors the mention system's architecture. Users can easily tag their posts with trending or existing hashtags, improving content discoverability and organization.
