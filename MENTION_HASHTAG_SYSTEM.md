# Mention & Hashtag System

## Overview
The mention and hashtag system has been updated to use **client-side detection** instead of Tiptap's built-in Mention extension. This provides more control over the UX and better integration with the backend mention/hashtag storage system.

## Changes Made

### 1. Removed Tiptap Mention Extension ✅
**Files Modified:**
- `src/components/ui/RichTextEditor.jsx`

**Changes:**
- ❌ Removed `import { Mention } from '@tiptap/extension-mention'`
- ❌ Removed `import tippy from 'tippy.js'`
- ❌ Removed `enableMentions` prop
- ❌ Removed `mentionSuggestions` prop
- ❌ Removed `hashtagSuggestions` prop
- ❌ Removed `mentionSuggestion` useMemo configuration
- ❌ Removed `hashtagSuggestion` useMemo configuration
- ❌ Removed `Mention.configure()` from extensions array

### 2. Copied Components from Backup ✅
**New Files:**
- `src/components/ui/MentionAutocomplete.jsx` - Autocomplete component for @ mentions
- `src/hooks/useMentionInput.js` - Hook for managing text input with mention functionality

**Existing Files (Already in current client):**
- `src/services/social-api.js` - Already has `utils.extractMentions()` and `utils.extractHashtags()`

## How the New System Works

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER TYPES TEXT                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              TEXT INPUT (Textarea/RichTextEditor)               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  "Hey @john, check out this #javascript tutorial!"       │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                 useMentionInput Hook (if using)                 │
│  - Tracks cursor position                                       │
│  - Detects @ symbol context                                     │
│  - Manages text state                                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              MentionAutocomplete Component                      │
│  - Detects @username pattern                                    │
│  - Searches mentionable users via API                           │
│  - Shows dropdown with suggestions                              │
│  - Handles keyboard navigation (↑↓ Enter Esc)                  │
│  - Inserts "@username " on selection                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ON SUBMISSION (Before POST)                    │
│  1. Extract mentions: utils.extractMentions(content)            │
│     → Returns: ['john', 'sarah']                                │
│  2. Extract hashtags: utils.extractHashtags(content)            │
│     → Returns: ['javascript', 'tutorial']                       │
│  3. Send to backend with post/comment                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND PROCESSING                            │
│  1. Store mentions in Mention model (creates notifications)     │
│  2. Store hashtags in Hashtag model (for discovery)             │
│  3. Link mentions to post/comment                               │
└─────────────────────────────────────────────────────────────────┘
```

### Mention Detection Flow

1. **User Types @**:
   - MentionAutocomplete detects `@` followed by text
   - Validates context (must be at start or after whitespace)
   - Triggers search after 1+ characters

2. **Search API Called**:
   ```javascript
   const results = await socialAPI.searchMentionableUsers(
     query,        // The text after @
     communityId,  // Optional: filter by community members
     postId        // Optional: prioritize post author
   );
   ```

3. **Dropdown Displays**:
   - Grouped by category (Followers, Community Members, Post Author, Public)
   - Shows avatar, @username, display name
   - Priority badges for relevant users
   - Keyboard navigation (↑↓ to select, Enter to choose, Esc to close)

4. **Selection**:
   - Replaces `@query` with `@username `
   - Cursor moves after the space
   - Dropdown closes

### Hashtag Detection

Hashtags are detected **on submission** using regex:

```javascript
const extractHashtags = (content) => {
  const hashtagRegex = /#(\w+)/g;
  const hashtags = [];
  let match;
  while ((match = hashtagRegex.exec(content)) !== null) {
    hashtags.push(match[1]);
  }
  return hashtags;
};
```

**Note**: Hashtags are NOT autocompleted in the current implementation. They are:
- Detected client-side (regex)
- Sent to backend on submission
- Stored in database for discovery/trending

## Usage Examples

### Example 1: Using in a Simple Textarea (PostComposer style)

```jsx
import { useMentionInput } from '../hooks/useMentionInput';
import MentionAutocomplete from './ui/MentionAutocomplete';
import { socialAPI } from '../services/social-api';

function SimplePostComposer({ communityId }) {
  const {
    text,
    setText,
    cursorPosition,
    textareaRef,
    handleChange,
    handleMentionSelect,
    handleKeyDown,
    handleClick,
  } = useMentionInput('');

  const handleSubmit = async () => {
    // Extract mentions and hashtags before submitting
    const mentions = socialAPI.utils.extractMentions(text);
    const hashtags = socialAPI.utils.extractHashtags(text);

    console.log('Mentions:', mentions); // ['john', 'sarah']
    console.log('Hashtags:', hashtags); // ['javascript', 'tutorial']

    // Create post
    const response = await socialAPI.posts.create({
      content: text,
      community_id: communityId,
      // ... other fields
    });

    // Process mentions (creates Mention records and notifications)
    await socialAPI.utils.processContentMentions(
      text,
      response.id,    // postId
      null,           // commentId (null for posts)
      communityId
    );

    // Note: Hashtags are auto-extracted by backend from content
    // No need to send them separately
  };

  return (
    <div className="relative">
      <textarea
        ref={textareaRef}
        value={text}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onClick={handleClick}
        placeholder="What's on your mind? Use @username or #hashtag"
        className="w-full p-3 border rounded-lg"
      />

      <MentionAutocomplete
        text={text}
        cursorPosition={cursorPosition}
        onMentionSelect={handleMentionSelect}
        communityId={communityId}
      />

      <button onClick={handleSubmit} className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg">
        Post
      </button>
    </div>
  );
}
```

### Example 2: Using with RichTextEditor

The RichTextEditor doesn't currently integrate MentionAutocomplete because it's a Tiptap editor. To add mention support:

**Option A: Add a parallel textarea for mentions (recommended)**

```jsx
function PostCreationModal() {
  const richTextRef = useRef(null);

  const [showMentionInput, setShowMentionInput] = useState(false);

  const {
    text: mentionText,
    setText: setMentionText,
    cursorPosition,
    textareaRef,
    handleChange,
    handleMentionSelect,
    handleKeyDown,
    handleClick,
  } = useMentionInput('');

  const handleSubmit = async () => {
    // Get HTML content from RichTextEditor
    const htmlContent = richTextRef.current?.getHTML();

    // Extract from both HTML and mention textarea
    const mentions = [
      ...socialAPI.utils.extractMentions(htmlContent),
      ...socialAPI.utils.extractMentions(mentionText)
    ];
    const hashtags = [
      ...socialAPI.utils.extractHashtags(htmlContent),
      ...socialAPI.utils.extractHashtags(mentionText)
    ];

    // Create post with HTML content
    const response = await socialAPI.posts.create({
      content: htmlContent,
      // ... other fields
    });

    // Process mentions
    await socialAPI.utils.processContentMentions(
      `${htmlContent} ${mentionText}`,
      response.id,
      null,
      communityId
    );
  };

  return (
    <div>
      <RichTextEditor
        ref={richTextRef}
        content=""
        onChange={() => {}}
        placeholder="Write your post..."
      />

      {/* Optional: Mention input field */}
      <div className="mt-3 relative">
        <label className="text-sm text-gray-600">Mention users (optional):</label>
        <textarea
          ref={textareaRef}
          value={mentionText}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onClick={handleClick}
          placeholder="@username"
          className="w-full p-2 border rounded-lg text-sm"
          rows={1}
        />

        <MentionAutocomplete
          text={mentionText}
          cursorPosition={cursorPosition}
          onMentionSelect={handleMentionSelect}
          communityId={communityId}
        />
      </div>

      <button onClick={handleSubmit}>Submit</button>
    </div>
  );
}
```

**Option B: Extract from HTML content only (simpler)**

```jsx
function PostCreationModal() {
  const richTextRef = useRef(null);

  const handleSubmit = async () => {
    // Get HTML content
    const htmlContent = richTextRef.current?.getHTML();

    // Extract mentions/hashtags from HTML
    const mentions = socialAPI.utils.extractMentions(htmlContent);
    const hashtags = socialAPI.utils.extractHashtags(htmlContent);

    // Note: Users type @username and #hashtag directly in the editor
    // No autocomplete, but mentions/hashtags are still detected and stored

    const response = await socialAPI.posts.create({
      content: htmlContent,
      // ... other fields
    });

    await socialAPI.utils.processContentMentions(
      htmlContent,
      response.id,
      null,
      communityId
    );
  };

  return (
    <div>
      <RichTextEditor
        ref={richTextRef}
        content=""
        onChange={() => {}}
        placeholder="Write your post... Use @username or #hashtag"
      />

      <button onClick={handleSubmit}>Submit</button>
    </div>
  );
}
```

### Example 3: Client-Side Hashtag Highlighting (CSS only)

Add this CSS to highlight hashtags in display:

```css
/* In your global CSS or component styles */
.post-content {
  /* Your existing styles */
}

.post-content a[href^="#"],
.post-content .hashtag {
  color: #2563eb; /* Blue-600 */
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
}

.post-content a[href^="#"]:hover,
.post-content .hashtag:hover {
  color: #1d4ed8; /* Blue-700 */
  text-decoration: underline;
}
```

Or use a React component to parse and style:

```jsx
function PostContent({ htmlContent }) {
  // Parse HTML and wrap hashtags in styled spans
  const styledContent = htmlContent.replace(
    /#(\w+)/g,
    '<span class="hashtag" style="color: #2563eb; font-weight: 500; cursor: pointer;">#$1</span>'
  );

  return (
    <div
      className="post-content"
      dangerouslySetInnerHTML={{ __html: styledContent }}
    />
  );
}
```

## API Reference

### Social API Utils

```javascript
// Located in src/services/social-api.js

socialAPI.utils = {
  // Extract @mentions from text
  extractMentions: (content) => {
    // Returns: ['username1', 'username2']
  },

  // Extract #hashtags from text
  extractHashtags: (content) => {
    // Returns: ['hashtag1', 'hashtag2']
  },

  // Process mentions and create records in backend
  processContentMentions: async (content, postId = null, commentId = null, communityId = null) => {
    // 1. Extracts @mentions from content
    // 2. Resolves usernames to UserProfile IDs
    // 3. Creates Mention records in database
    // 4. Triggers notifications for mentioned users
    // Returns: Array of created mention objects
  },

  // Search mentionable users
  searchMentionableUsers: async (query, communityId = null, postId = null) => {
    // GET /profiles/search_mentionable/?q={query}&community_id={id}&post_id={id}
    // Returns: Array of user objects with priority categories
  }
};
```

### MentionAutocomplete Props

```jsx
<MentionAutocomplete
  text={string}                // Current text content
  cursorPosition={number}      // Cursor position in text
  onMentionSelect={function}   // Callback when user selects
  communityId={number}         // Optional: filter by community
  postId={number}              // Optional: prioritize post author
  className={string}           // Optional: custom className
/>
```

### useMentionInput Hook

```javascript
const {
  text,                  // Current text value
  setText,               // Update text
  cursorPosition,        // Current cursor position
  textareaRef,           // Ref for textarea element
  handleChange,          // onChange handler
  handleMentionSelect,   // Mention selection handler
  handleKeyDown,         // onKeyDown handler
  handleClick,           // onClick handler
  handleSelectionChange  // Selection change handler
} = useMentionInput(initialValue);
```

## Backend Integration

### Mention Model
```python
class Mention(models.Model):
    mentioned_user = models.ForeignKey(UserProfile)
    post = models.ForeignKey(Post, null=True, blank=True)
    comment = models.ForeignKey(Comment, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Hashtag Model
```python
class Hashtag(models.Model):
    tag = models.CharField(max_length=100, unique=True)
    posts = models.ManyToManyField(Post, related_name='hashtags')
    created_at = models.DateTimeField(auto_now_add=True)
```

### API Endpoints

**Search Mentionable Users:**
```
GET /api/profiles/search_mentionable/?q={query}&community_id={id}&post_id={id}
```

**Create Mention:**
```
POST /api/mentions/
{
  "mentioned_user": <user_profile_id>,
  "post": <post_id>,
  "comment": null
}
```

**Get Mentions for User:**
```
GET /api/mentions/?mentioned_user=<user_profile_id>
```

## Testing Checklist

### Mention System
- [ ] Type `@` in textarea - dropdown appears
- [ ] Type `@j` - filters to users starting with 'j'
- [ ] Use ↑↓ keys to navigate suggestions
- [ ] Press Enter - inserts `@username ` and closes dropdown
- [ ] Press Esc - closes dropdown without selection
- [ ] Click suggestion - inserts `@username ` and closes dropdown
- [ ] Type `@john` then space - dropdown disappears
- [ ] Submit post - mentions extracted correctly
- [ ] Backend creates Mention records
- [ ] Mentioned users receive notifications

### Hashtag System
- [ ] Type `#javascript` in text
- [ ] Submit post - hashtag extracted correctly
- [ ] Backend creates/links Hashtag record
- [ ] Hashtags display in blue color (if CSS added)
- [ ] Click hashtag - navigates to hashtag page (if implemented)

### Edge Cases
- [ ] Multiple mentions: `@john @sarah hey!`
- [ ] Multiple hashtags: `#js #webdev #coding`
- [ ] Mixed: `Hey @john check #javascript!`
- [ ] Invalid mention: `email@example.com` (should NOT trigger)
- [ ] Mention mid-word: `hello@world` (should NOT trigger)
- [ ] Hashtag in URL: `http://example.com/#anchor` (should NOT trigger)

## Migration Notes

### For Existing Components Using Old System

If you have components using the old Tiptap Mention extension:

1. **Remove props**:
   ```diff
   - <RichTextEditor
   -   enableMentions={true}
   -   mentionSuggestions={[...]}
   -   hashtagSuggestions={[...]}
   - />
   + <RichTextEditor />
   ```

2. **Add extraction on submission**:
   ```javascript
   const handleSubmit = async () => {
     const content = richTextRef.current?.getHTML();
     const mentions = socialAPI.utils.extractMentions(content);
     const hashtags = socialAPI.utils.extractHashtags(content);

     // ... create post ...

     await socialAPI.utils.processContentMentions(content, postId, null, communityId);
   };
   ```

3. **Optional: Add MentionAutocomplete** (for textarea-based inputs):
   ```jsx
   const { text, cursorPosition, ... } = useMentionInput('');

   <MentionAutocomplete
     text={text}
     cursorPosition={cursorPosition}
     onMentionSelect={handleMentionSelect}
     communityId={communityId}
   />
   ```

## Future Enhancements

### Hashtag Autocomplete
To add hashtag autocomplete similar to mentions:

1. Create `HashtagAutocomplete.jsx` component
2. Detect `#` symbol with text
3. Search trending/recent hashtags
4. Display dropdown with suggestions
5. Insert selected hashtag

### Rich Text Mention Integration
To integrate MentionAutocomplete directly into Tiptap:

1. Create custom Tiptap extension
2. Listen for `@` character insertion
3. Show MentionAutocomplete positioned at cursor
4. Insert mention as special node/mark
5. Style mentions in editor

### Mention Linking
Make @mentions clickable links to user profiles:

```javascript
const linkMentions = (content) => {
  return content.replace(
    /@(\w+)/g,
    '<a href="/profile/$1" class="mention">@$1</a>'
  );
};
```

## Summary

✅ **Removed**: Tiptap Mention extension with tippy.js dropdowns
✅ **Added**: Client-side mention detection with MentionAutocomplete component
✅ **How it works**:
- User types `@` → autocomplete dropdown appears
- Select user → inserts `@username `
- On submission → extract mentions/hashtags with regex
- Send to backend → create Mention/Hashtag records

✅ **Benefits**:
- More control over UX
- Better integration with backend storage
- Simpler codebase (no tippy.js dependency)
- Consistent mention behavior across all input types

✅ **Next Steps**:
- Integrate MentionAutocomplete in PostCreationModal
- Add CSS for hashtag highlighting
- Test mention extraction and notification flow
