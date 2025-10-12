# Tiptap Mention Implementation

## 🎯 What Was Implemented

I've added a **smart mention autocomplete system** directly into your **Tiptap RichTextEditor** that integrates with your existing backend API.

### Key Features

✅ **Real-time search** - Type `@` and start typing to search users
✅ **API integration** - Uses your existing `/api/profiles/search_mentionable/` endpoint
✅ **Smart categorization** - Groups results by: People you follow, Post author, Community members, Public profiles
✅ **Keyboard navigation** - Arrow keys to navigate, Enter to select, Esc to close
✅ **Visual feedback** - Beautiful dropdown with avatars, usernames, and priority badges
✅ **Debounced search** - 300ms delay to avoid excessive API calls
✅ **Mentions stored in content** - Saved as `<span class="mention">@username</span>` in HTML

---

## 📁 Files Modified

### 1. `src/components/ui/RichTextEditor.jsx`

**What was added:**

#### Imports
```javascript
import { Mention } from '@tiptap/extension-mention';
import { socialAPI } from '../../services/social-api';
```

#### State Management (lines ~680)
```javascript
// Mention autocomplete state
const [mentionQuery, setMentionQuery] = useState('');
const [mentionSuggestions, setMentionSuggestions] = useState([]);
const [showMentionDropdown, setShowMentionDropdown] = useState(false);
const [selectedMentionIndex, setSelectedMentionIndex] = useState(0);
const [mentionDropdownPosition, setMentionDropdownPosition] = useState({ top: 0, left: 0 });
const mentionDropdownRef = useRef(null);
```

#### API Search Hook (lines ~730)
```javascript
// Search for mentionable users when mention query changes
useEffect(() => {
  const searchMentions = async () => {
    if (!mentionQuery || mentionQuery.length < 1) {
      setMentionSuggestions([]);
      return;
    }

    try {
      const results = await socialAPI.searchMentionableUsers(mentionQuery);
      setMentionSuggestions(results || []);
    } catch (error) {
      console.error('Failed to search mentionable users:', error);
      setMentionSuggestions([]);
    }
  };

  const debounceTimer = setTimeout(searchMentions, 300);
  return () => clearTimeout(debounceTimer);
}, [mentionQuery]);
```

#### Tiptap Extension Configuration (lines ~940)
```javascript
Mention.configure({
  HTMLAttributes: {
    class: 'mention text-blue-600 font-medium',
  },
  suggestion: {
    char: '@',
    allowSpaces: false,
    items: ({ query }) => {
      setMentionQuery(query);
      setShowMentionDropdown(query.length > 0);
      return mentionSuggestions;
    },
    render: () => {
      return {
        onStart: (props) => { /* Position dropdown */ },
        onUpdate: (props) => { /* Update position */ },
        onKeyDown: (props) => { /* Handle keyboard navigation */ },
        onExit: () => { /* Close dropdown */ },
      };
    },
  },
}),
```

#### UI Dropdown Component (lines ~3100)
```jsx
{/* Mention Autocomplete Dropdown */}
{showMentionDropdown && mentionSuggestions.length > 0 && (
  <div className="fixed z-50 bg-white border rounded-lg shadow-lg">
    {/* Grouped by category */}
    {/* Shows avatars, usernames, display names */}
    {/* Keyboard navigation support */}
  </div>
)}
```

---

## 🚀 How to Use

### For End Users

1. **Open post composer** (wherever RichTextEditor is used)
2. **Type `@` symbol** in the editor
3. **Start typing username** (e.g., `@adm`)
4. **Dropdown appears** with matching users
5. **Navigate with arrow keys** (↑↓)
6. **Press Enter** to select, or **click** on a user
7. **Mention inserted** as `@username` in blue

### Example Flow

```
You type: @ad
         ↓
Dropdown shows:
┌─────────────────────────────┐
│ People you follow           │
│ ✓ @admin (Admin User)       │
│ ✓ @administrator            │
├─────────────────────────────┤
│ Public profiles             │
│   @adam (Adam Smith)        │
└─────────────────────────────┘
         ↓
Press Enter or Click
         ↓
Text becomes: "@admin " (with space)
```

---

## 🔧 Testing

### Prerequisites

Since you're using **Docker** and **Yarn**, make sure:

1. **Backend is running** (Django API server)
2. **Frontend is running** (React dev server)
3. **User is authenticated** (JWT token exists)
4. **At least one user exists** in the database with username containing "admin"

### Test Steps

#### 1. Check Package Dependencies

The mention extension should already be installed:

```bash
# In your frontend container or locally
yarn list --pattern "@tiptap/extension-mention"
```

**Expected output:**
```
@tiptap/extension-mention@^3.4.4
```

If not installed (shouldn't happen since it's in package.json):
```bash
yarn add @tiptap/extension-mention
```

#### 2. Rebuild Docker Containers (if needed)

```bash
# From your project root
docker-compose build frontend
docker-compose up -d frontend
```

#### 3. Test in Browser

1. **Open your app** in browser (e.g., `http://localhost:3000`)
2. **Navigate to Post Creation Modal** or anywhere using RichTextEditor
3. **Type `@admin`** in the editor

**Expected behavior:**
- ✅ Dropdown appears below the `@` symbol
- ✅ Shows users matching "admin"
- ✅ Can navigate with arrow keys
- ✅ Can click to select
- ✅ Mention inserted as blue `@admin`

#### 4. Check Browser Console

Open DevTools (F12) and look for:

```javascript
// Should NOT see any errors
// Optionally, you might see search logs if debugging is enabled
```

#### 5. Check Network Tab

When typing `@admin`, you should see:

```
GET /api/profiles/search_mentionable/?q=a
GET /api/profiles/search_mentionable/?q=ad
GET /api/profiles/search_mentionable/?q=adm
GET /api/profiles/search_mentionable/?q=admi
GET /api/profiles/search_mentionable/?q=admin
```

Each request should return:
```json
{
  "results": [
    {
      "id": 123,
      "username": "admin",
      "display_name": "Admin User",
      "avatar_url": null,
      "priority": "public",
      "category": "Public profiles"
    }
  ]
}
```

---

## 🐛 Troubleshooting

### Issue 1: Dropdown doesn't appear

**Symptoms:** Type `@admin` but nothing happens

**Solutions:**

1. **Check if backend is running:**
   ```bash
   docker-compose ps
   ```

2. **Check authentication:**
   - Open DevTools → Application → Local Storage
   - Look for `access_token`
   - If missing, log out and log back in

3. **Check API endpoint:**
   ```javascript
   // In browser console:
   fetch('/api/profiles/search_mentionable/?q=admin', {
     headers: {
       'Authorization': 'Bearer ' + localStorage.getItem('access_token')
     }
   })
   .then(r => r.json())
   .then(console.log)
   ```

### Issue 2: "Module not found: @tiptap/extension-mention"

**Solution:**

```bash
# Inside frontend container or locally:
docker-compose exec frontend yarn add @tiptap/extension-mention

# Or rebuild containers:
docker-compose down
docker-compose build
docker-compose up -d
```

### Issue 3: Dropdown appears but is empty

**Causes:**
- No users in database matching the query
- API returns empty results
- User searching for themselves (excluded from results)

**Solution:**

Check database:
```sql
SELECT id, username FROM auth_user WHERE username ILIKE '%admin%';
```

If no results, create a test user:
```python
# In Django shell
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_user(username='admin', password='admin123')
```

### Issue 4: Dropdown position is wrong

**Symptoms:** Dropdown appears in wrong location

**Solution:**

The dropdown uses fixed positioning based on cursor rect. If it's mispositioned:

1. **Check CSS conflicts** - Ensure no parent has `transform` or `position: fixed`
2. **Check scrolling** - The position accounts for `window.scrollY`
3. **Browser zoom** - Reset zoom to 100%

### Issue 5: Can't select mention with keyboard

**Symptoms:** Arrow keys don't work

**Solution:**

The keyboard handler is in the Tiptap configuration. Check:

1. **Focus is on editor** - Click inside the editor
2. **Not inside code block** - Keyboard nav doesn't work in code blocks
3. **Check console for errors**

---

## 🎨 Customization

### Change Mention Style

In the CSS section of RichTextEditor.jsx (around line 2361):

```css
.rich-text-content .mention {
  color: #2563eb;  /* Change color */
  font-weight: 600;
  background-color: #eff6ff;  /* Add background */
  padding: 2px 4px;
  border-radius: 4px;
}
```

### Change Dropdown Appearance

In the JSX (around line 3110), modify the dropdown classes:

```jsx
<div
  className="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg"
  // Change to dark theme:
  className="fixed z-50 bg-gray-900 border border-gray-700 rounded-lg shadow-xl"
>
```

### Change Search Debounce Delay

In the useEffect (around line 730):

```javascript
const debounceTimer = setTimeout(searchMentions, 300);  // Change 300 to 500 for slower search
```

### Add More Categories

The API already returns categories. To add custom ones, modify the backend:

```python
# accounts/views.py - search_mentionable method
mentionable_users.append({
    'id': user.id,
    'username': user.user.username,
    'display_name': display_name,
    'category': 'VIP Users',  # Custom category
    'priority': 'vip'
})
```

---

## 📊 How It Works (Technical)

### 1. User Types `@`

Tiptap detects the `@` character via the Mention extension's `char: '@'` configuration.

### 2. Query Extraction

As user types more characters (e.g., `@adm`), Tiptap extracts the query: `"adm"`

### 3. React State Update

```javascript
items: ({ query }) => {
  setMentionQuery(query);  // Triggers useEffect
  setShowMentionDropdown(query.length > 0);
  return mentionSuggestions;
}
```

### 4. API Search (Debounced)

```javascript
useEffect(() => {
  const searchMentions = async () => {
    const results = await socialAPI.searchMentionableUsers(mentionQuery);
    setMentionSuggestions(results || []);
  };
  const debounceTimer = setTimeout(searchMentions, 300);
  return () => clearTimeout(debounceTimer);
}, [mentionQuery]);
```

### 5. Dropdown Renders

React renders the dropdown with:
- Fixed positioning based on cursor rect
- Grouped categories
- Avatar images
- Priority badges

### 6. Selection

When user selects (Enter or click):

```javascript
editor.chain().focus().insertContent({
  type: 'mention',
  attrs: {
    id: user.id,
    label: user.username,
  },
}).run();
```

### 7. HTML Output

Tiptap generates:

```html
<span class="mention" data-type="mention" data-id="123" data-label="admin">
  @admin
</span>
```

### 8. Backend Processing

When post is submitted:
- Content includes the HTML with mention spans
- Backend extracts mentions using regex (from `content/utils.py`)
- Creates `Mention` records in database
- Sends notifications to mentioned users

---

## 🔗 Integration Points

### Frontend Files
- ✅ `src/components/ui/RichTextEditor.jsx` - Main implementation
- ✅ `src/services/social-api.js` - API service (already exists)
- ✅ `src/components/PostCreationModal.jsx` - Uses RichTextEditor (already exists)

### Backend Files
- ✅ `accounts/views.py` - `search_mentionable` endpoint (already exists)
- ✅ `content/utils.py` - `extract_mentions_from_content()` (already exists)
- ✅ `content/models.py` - `Mention` model (already exists)
- ✅ `content/tasks.py` - `process_mentions()` Celery task (already exists)

### Dependencies
- ✅ `@tiptap/extension-mention` - Already in package.json
- ✅ `@tiptap/react` - Already installed
- ✅ All other Tiptap extensions - Already installed

---

## 🚦 Next Steps

### 1. Test the Implementation

```bash
# Make sure containers are running
docker-compose ps

# Check frontend logs
docker-compose logs -f frontend

# Open browser and test
open http://localhost:3000
```

### 2. Remove Old Debug Logs (Optional)

If you want to remove the debug console.logs I added earlier:

**Files to clean:**
- `src/components/ui/MentionAutocomplete.jsx`
- `src/hooks/useMentionInput.js`

Search for and remove lines starting with:
- `console.log('🔍`
- `console.log('✅`
- `console.log('❌`
- `console.log('⌨️`
- `console.log('📍`

### 3. Remove Unused Components (Optional)

The old textarea-based mention system is no longer needed:
- `src/components/ui/MentionAutocomplete.jsx` - Can be removed if only using RichTextEditor
- `src/hooks/useMentionInput.js` - Can be removed if only using RichTextEditor

**Keep them if:** You're still using `PostComposer.jsx` with textarea.

---

## ✨ Summary

You now have a **fully integrated mention system** in your Tiptap editor that:

1. **Searches users** as you type `@username`
2. **Shows smart suggestions** grouped by relationship
3. **Supports keyboard navigation** and mouse clicks
4. **Integrates with your backend** API and notification system
5. **Works seamlessly** with your existing Docker + Yarn setup

**To test:** Just type `@admin` in any RichTextEditor and watch the magic happen! 🎉

---

## 📞 Support

If you encounter issues:

1. Check browser console for errors
2. Check network tab for failed API calls
3. Verify backend is returning data: `docker-compose logs backend`
4. Check the troubleshooting section above
5. Share console output and I'll help debug!
