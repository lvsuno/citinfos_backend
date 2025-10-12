# Mention Autocomplete - Debug Mode Enabled

## What I Did

I added **debug logging** to the mention autocomplete system to help diagnose why no suggestions appear when typing `@admin`.

## Files Modified

### 1. `src/components/ui/MentionAutocomplete.jsx`
Added console logs to show:
- 🔍 When mention detection runs
- ✅ When valid mention is detected
- ❌ Why mention detection fails
- 🔎 When API search is triggered
- ✅ API search results
- ❌ API search errors

### 2. `src/hooks/useMentionInput.js`
Added console logs to show:
- ⌨️ When text changes
- 📍 Cursor position updates

### 3. `MENTION_AUTOCOMPLETE_DEBUG.md`
Complete debugging guide with:
- Checklist of what to check
- Common issues and solutions
- Test scripts
- Expected console output

---

## How to Debug

### Step 1: Open Browser Console

1. Open your app in the browser
2. Press **F12** (or **Cmd+Option+I** on Mac)
3. Go to the **Console** tab

### Step 2: Type `@admin` in Post Composer

You should see console output like this:

**Expected Output (Working):**
```
⌨️ useMentionInput: Text changed { value: '@', cursorPos: 1 }
📍 useMentionInput: Cursor position updated to 1
🔍 MentionAutocomplete: Check for mention { cursorPosition: 1, textLength: 1, text: '@' }
📝 Text after @: ""
✅ Valid mention detected: ""
⏭️ Skipping search: { isVisible: true, queryLength: 0 }

⌨️ useMentionInput: Text changed { value: '@a', cursorPos: 2 }
📍 useMentionInput: Cursor position updated to 2
🔍 MentionAutocomplete: Check for mention { cursorPosition: 2, textLength: 2, text: '@a' }
📝 Text after @: "a"
✅ Valid mention detected: "a"
🔎 Searching for users: a
✅ Search results: [{ id: 123, username: 'admin', ... }]

⌨️ useMentionInput: Text changed { value: '@ad', cursorPos: 3 }
📍 useMentionInput: Cursor position updated to 3
🔍 MentionAutocomplete: Check for mention { cursorPosition: 3, textLength: 3, text: '@ad' }
📝 Text after @: "ad"
✅ Valid mention detected: "ad"
🔎 Searching for users: ad
✅ Search results: [{ id: 123, username: 'admin', ... }]

... etc
```

---

## Common Issues & What to Look For

### Issue 1: No Cursor Position
**Console shows:**
```
⌨️ useMentionInput: Text changed { value: '@admin', cursorPos: 6 }
📍 useMentionInput: Cursor position updated to 6
🔍 MentionAutocomplete: Check for mention { cursorPosition: null, textLength: 6 }
❌ No cursor position
```

**Problem:** Cursor position is not being tracked correctly

**Solution:** Check that textarea has all required event handlers:
```jsx
<textarea
  ref={mentionInputRef}
  onChange={handleTextChange}    // ✓
  onKeyDown={handleKeyDown}      // ✓
  onClick={handleClick}          // ✓
  onSelect={handleSelectionChange}  // ← MUST HAVE THIS!
/>
```

---

### Issue 2: No @ Symbol Detected
**Console shows:**
```
🔍 MentionAutocomplete: Check for mention { cursorPosition: 5, textLength: 5, text: 'admin' }
❌ No @ symbol found
```

**Problem:** User typed `admin` without `@`

**Solution:** Type `@admin` with the @ symbol

---

### Issue 3: Space Before @ Missing
**Console shows:**
```
🔍 MentionAutocomplete: Check for mention { cursorPosition: 11, textLength: 11, text: 'hello@admin' }
📝 Text after @: "admin"
❌ No space before @, char: o
```

**Problem:** `@` must be at start or after a space/newline

**Solution:** Type `hello @admin` (with space) instead of `hello@admin`

---

### Issue 4: Space After @ (Dropdown Closed)
**Console shows:**
```
🔍 MentionAutocomplete: Check for mention { cursorPosition: 7, textLength: 7, text: '@admin ' }
📝 Text after @: "admin "
❌ Space/newline in mention
```

**Problem:** Typing a space after `@admin` closes the dropdown (by design)

**Solution:** This is correct behavior - space completes the mention

---

### Issue 5: No API Call Despite Valid Mention
**Console shows:**
```
✅ Valid mention detected: "admin"
⏭️ Skipping search: { isVisible: true, queryLength: 5 }
```

**Problem:** The `queryLength` check is failing (should be `5` for "admin")

**Solution:** Check the `searchUsers` function logic - this shouldn't happen

---

### Issue 6: API Call Fails
**Console shows:**
```
🔎 Searching for users: admin
❌ Failed to search mentionable users: Error: Request failed with status code 401
```

**Problem:** Authentication token is missing or expired

**Solution:**
1. Log out and log back in
2. Check browser localStorage for `access_token`
3. Verify backend is running

---

### Issue 7: API Returns Empty Results
**Console shows:**
```
🔎 Searching for users: admin
✅ Search results: []
```

**Problem:** No users found matching "admin"

**Solution:** Check database:
```sql
SELECT id, username FROM auth_user WHERE username ILIKE '%admin%';
```

If no results, create a user with username `admin`

---

## Network Tab Inspection

### Step 1: Open Network Tab
1. In DevTools, click **Network** tab
2. Type `@admin` in the post composer

### Step 2: Check Requests
You should see:
```
GET /api/profiles/search_mentionable/?q=a
GET /api/profiles/search_mentionable/?q=ad
GET /api/profiles/search_mentionable/?q=adm
GET /api/profiles/search_mentionable/?q=admi
GET /api/profiles/search_mentionable/?q=admin
```

**Click on a request to see:**
- **Headers:** Check `Authorization: Bearer <token>`
- **Response:** Should show user data

---

## Test in Browser Console

Run this to test the API directly:

```javascript
// Test 1: Check cursor tracking
const textarea = document.querySelector('textarea');
console.log('Textarea exists:', !!textarea);
console.log('Cursor position:', textarea?.selectionStart);

// Test 2: Test API endpoint
fetch('/api/profiles/search_mentionable/?q=admin', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('access_token')
  }
})
.then(r => r.json())
.then(data => {
  console.log('✅ API works! Results:', data);
})
.catch(err => {
  console.error('❌ API failed:', err);
});
```

---

## Next Steps

1. **Try typing `@admin` now** - check the console output
2. **Copy the console output** and share it with me
3. **Check the Network tab** - are there any API requests?
4. **Run the browser console test** above

Based on the console output, I can tell you exactly what's wrong!

---

## Removing Debug Logs Later

Once the issue is fixed, you can remove the debug logs by:

1. Search for `console.log` in:
   - `src/components/ui/MentionAutocomplete.jsx`
   - `src/hooks/useMentionInput.js`

2. Remove all lines starting with:
   - `console.log('🔍`
   - `console.log('✅`
   - `console.log('❌`
   - `console.log('⌨️`
   - `console.log('📍`
   - `console.log('🔎`
   - `console.log('⏭️`

Or just keep them - they're helpful for debugging!
