# Mention Autocomplete Debugging Guide

## Issue
When typing `@admin` in the post composer, no suggestions appear and no API call is made.

## Checklist to Debug

### 1. Check Browser Console
Open your browser's Developer Tools (F12 or Cmd+Option+I) and:

#### Console Tab
Look for:
- ❌ **JavaScript errors** (red text)
- ⚠️ **Warnings** (yellow text)
- 🔍 **`console.log`** messages from MentionAutocomplete

**Expected messages when typing `@admin`:**
```javascript
// None - component should silently work
```

#### Network Tab
When typing `@admin`, you should see:
```
GET /api/profiles/search_mentionable/?q=admin
Status: 200 OK
Response: { results: [...] }
```

**If NO network request appears:**
- The detection logic isn't triggering
- Check cursor position tracking
- Check if component is mounted

**If network request shows 401/403:**
- Authentication issue
- Check JWT token in localStorage
- Try logging out and back in

### 2. Verify Component is Mounted

Add this temporarily to `src/components/ui/MentionAutocomplete.jsx`:

```jsx
// Add at the top of the component function
useEffect(() => {
  console.log('MentionAutocomplete mounted!', { text, cursorPosition, isVisible });
}, []);

useEffect(() => {
  console.log('Detection check:', {
    text,
    cursorPosition,
    isVisible,
    mentionQuery,
    suggestions: suggestions.length
  });
}, [text, cursorPosition, isVisible, mentionQuery, suggestions]);
```

**Expected output when typing `@admin`:**
```
MentionAutocomplete mounted! { text: '', cursorPosition: null, isVisible: false }
Detection check: { text: '@a', cursorPosition: 2, isVisible: true, mentionQuery: 'a', suggestions: 0 }
Detection check: { text: '@ad', cursorPosition: 3, isVisible: true, mentionQuery: 'ad', suggestions: 0 }
Detection check: { text: '@adm', cursorPosition: 4, isVisible: true, mentionQuery: 'adm', suggestions: 0 }
Detection check: { text: '@admin', cursorPosition: 6, isVisible: true, mentionQuery: 'admin', suggestions: 2 }
```

### 3. Check Cursor Position Tracking

The `useMentionInput` hook must track cursor position correctly.

Add this to `src/hooks/useMentionInput.js`:

```jsx
// In handleChange function
const handleChange = (e) => {
  const newValue = e.target.value;
  setText(newValue);
  console.log('Text changed:', {
    value: newValue,
    cursorPos: e.target.selectionStart
  });
  setCursorPosition(e.target.selectionStart);
};
```

**Expected output when typing `@admin`:**
```
Text changed: { value: '@', cursorPos: 1 }
Text changed: { value: '@a', cursorPos: 2 }
Text changed: { value: '@ad', cursorPos: 3 }
Text changed: { value: '@adm', cursorPos: 4 }
Text changed: { value: '@admi', cursorPos: 5 }
Text changed: { value: '@admin', cursorPos: 6 }
```

### 4. Verify API Endpoint

Test the endpoint manually:

```bash
# In browser console:
fetch('/api/profiles/search_mentionable/?q=admin', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('access_token')
  }
})
.then(r => r.json())
.then(console.log)
.catch(console.error)
```

**Expected response:**
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

**If 401/403 error:**
- Token expired or invalid
- Log out and log back in
- Check `/api/auth/refresh/` endpoint

### 5. Check Detection Logic

The mention detection has these requirements:

```javascript
// From MentionAutocomplete.jsx checkForMention()

// 1. Cursor position must exist
if (cursorPosition === null || cursorPosition === undefined) {
  // ❌ FAILS: cursor tracking not working
}

// 2. Must have @ symbol before cursor
const textBeforeCursor = text.slice(0, cursorPosition);
const lastAtIndex = textBeforeCursor.lastIndexOf('@');
if (lastAtIndex === -1) {
  // ❌ FAILS: no @ symbol found
}

// 3. No spaces between @ and cursor
const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1);
if (textAfterAt.includes(' ') || textAfterAt.includes('\n')) {
  // ❌ FAILS: "@admin " (space after) won't trigger
}

// 4. @ must be at start or after whitespace
const charBeforeAt = lastAtIndex > 0 ? textBeforeCursor[lastAtIndex - 1] : ' ';
if (charBeforeAt !== ' ' && charBeforeAt !== '\n' && lastAtIndex !== 0) {
  // ❌ FAILS: "hello@admin" won't trigger (no space before @)
}
```

**Valid mention patterns:**
- ✅ `@admin` (at start)
- ✅ `Hey @admin` (space before)
- ✅ `Hello\n@admin` (newline before)

**Invalid patterns:**
- ❌ `hello@admin` (no space before)
- ❌ `@admin ` (space after - closes dropdown)
- ❌ `email@admin.com` (no space before)

### 6. Most Common Issues

#### Issue 1: Cursor Position is Always NULL
**Symptom:** `cursorPosition` is `null` or `undefined`

**Fix:** Check that textarea has these handlers:
```jsx
<textarea
  ref={mentionInputRef}
  onChange={handleTextChange}
  onKeyDown={handleKeyDown}
  onClick={handleClick}
  onSelect={handleSelectionChange}  // ← IMPORTANT!
/>
```

#### Issue 2: Component Not Receiving Props
**Symptom:** No dropdown appears even with valid `@mention`

**Fix:** Verify `PostComposer.jsx` passes all props:
```jsx
<MentionAutocomplete
  text={text}                        // ← Current text
  cursorPosition={cursorPosition}    // ← Cursor position
  onMentionSelect={handleMentionSelect}  // ← Selection handler
  communityId={community?.id}        // ← Optional
  className="mt-2"
/>
```

#### Issue 3: No API Call
**Symptom:** `isVisible=true` but no network request

**Fix:** Check the `searchUsers` useEffect:
```jsx
useEffect(() => {
  const searchUsers = async () => {
    if (!isVisible || mentionQuery.length < 1) {
      console.log('Skipping search:', { isVisible, queryLength: mentionQuery.length });
      setSuggestions([]);
      return;
    }

    console.log('Searching for:', mentionQuery); // Add this
    try {
      const results = await socialAPI.searchMentionableUsers(
        mentionQuery,
        communityId,
        postId
      );
      console.log('Search results:', results); // Add this
      setSuggestions(results);
    } catch (error) {
      console.error('Search failed:', error); // Check this
      setSuggestions([]);
    }
  };

  const debounceTimer = setTimeout(searchUsers, 300);
  return () => clearTimeout(debounceTimer);
}, [mentionQuery, isVisible, communityId, postId]);
```

#### Issue 4: API Returns Empty Results
**Symptom:** Network request succeeds but `results: []`

**Causes:**
1. No user with username containing `admin`
2. Current user is searching for themselves (excluded)
3. Privacy settings block the search

**Fix:** Check database:
```sql
SELECT id, username, first_name, last_name
FROM auth_user
WHERE username ILIKE '%admin%';
```

### 7. Quick Fix - Add Debugging

**File: `src/components/ui/MentionAutocomplete.jsx`**

Add this after line 55 (in the `checkForMention` function):

```jsx
const checkForMention = () => {
  console.log('🔍 Check for mention:', { cursorPosition, textLength: text.length });

  if (cursorPosition === null || cursorPosition === undefined) {
    console.log('❌ No cursor position');
    setIsVisible(false);
    return;
  }

  const textBeforeCursor = text.slice(0, cursorPosition);
  const lastAtIndex = textBeforeCursor.lastIndexOf('@');

  if (lastAtIndex === -1) {
    console.log('❌ No @ symbol found');
    setIsVisible(false);
    return;
  }

  const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1);
  console.log('📝 Text after @:', textAfterAt);

  if (textAfterAt.includes(' ') || textAfterAt.includes('\n')) {
    console.log('❌ Space/newline in mention');
    setIsVisible(false);
    return;
  }

  const charBeforeAt = lastAtIndex > 0 ? textBeforeCursor[lastAtIndex - 1] : ' ';
  if (charBeforeAt !== ' ' && charBeforeAt !== '\n' && lastAtIndex !== 0) {
    console.log('❌ No space before @, char:', charBeforeAt);
    setIsVisible(false);
    return;
  }

  console.log('✅ Valid mention detected:', textAfterAt);
  setMentionQuery(textAfterAt);
  setMentionStartPos(lastAtIndex);
  setIsVisible(true);
  setSelectedIndex(0);
};
```

### 8. Test Steps

1. Open browser DevTools (F12)
2. Go to Console tab
3. Type `@admin` in the post composer
4. Check console output:

**Expected:**
```
🔍 Check for mention: { cursorPosition: 1, textLength: 1 }
📝 Text after @: ''
✅ Valid mention detected:
🔍 Check for mention: { cursorPosition: 2, textLength: 2 }
📝 Text after @: 'a'
✅ Valid mention detected: a
Searching for: a
Search results: [{ id: 123, username: 'admin', ... }]
```

**If you see this, it's working!**

5. Go to Network tab
6. Filter by `search_mentionable`
7. Should see requests:
```
GET /api/profiles/search_mentionable/?q=a
GET /api/profiles/search_mentionable/?q=ad
GET /api/profiles/search_mentionable/?q=adm
GET /api/profiles/search_mentionable/?q=admi
GET /api/profiles/search_mentionable/?q=admin
```

---

## Solution Paths

### If cursor position is null:
1. Check `onSelect` handler is attached to textarea
2. Verify `useMentionInput` hook is being used
3. Check React DevTools to see hook state

### If detection doesn't trigger:
1. Add debug logs to `checkForMention()`
2. Check if `text` and `cursorPosition` are updating
3. Verify useEffect dependencies

### If API doesn't get called:
1. Add debug logs to `searchUsers` function
2. Check `isVisible` and `mentionQuery` values
3. Verify `socialAPI.searchMentionableUsers` exists

### If API returns empty:
1. Check database for matching users
2. Verify authentication token
3. Check backend logs for errors

---

## Final Test

Run this in browser console:

```javascript
// Test 1: Check if hook is tracking cursor
const textarea = document.querySelector('textarea');
console.log('Cursor position:', textarea.selectionStart);

// Test 2: Check if component is mounted
console.log('MentionAutocomplete visible:',
  document.querySelector('.mention-dropdown') !== null
);

// Test 3: Test API directly
fetch('/api/profiles/search_mentionable/?q=admin', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('access_token')
  }
})
.then(r => r.json())
.then(data => console.log('API Response:', data))
.catch(err => console.error('API Error:', err));
```

---

## Need Help?

If still not working, provide:
1. Console output (copy-paste)
2. Network tab screenshot
3. React DevTools state for PostComposer component
4. Database query result: `SELECT username FROM auth_user WHERE username ILIKE '%admin%';`
