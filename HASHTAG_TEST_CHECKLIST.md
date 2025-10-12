# Hashtag Autocomplete Test Checklist

## Quick Start Testing

### 1. **Start the Application**
```bash
# Terminal 1: Start backend
docker-compose up

# Terminal 2: Start frontend
cd src
yarn start
```

### 2. **Navigate to Post Composer**
- Open browser: http://localhost:3000
- Log in to your account
- Click "Create Post" or go to post creation page
- Find the RichTextEditor (Tiptap editor with formatting toolbar)

### 3. **Test Basic Hashtag Autocomplete**

#### Test 1: Simple Hashtag
1. Click in the editor
2. Type: `#java`
3. ✅ **Expected**: Dropdown appears below `#` symbol
4. ✅ **Expected**: Shows hashtags like `#javascript`, `#java`
5. Click on `#javascript`
6. ✅ **Expected**: `#java` is replaced with `#javascript` (in blue with background)

#### Test 2: Keyboard Navigation
1. Type: `#react`
2. ✅ **Expected**: Dropdown appears with matching hashtags
3. Press `↓` (down arrow)
4. ✅ **Expected**: Selection moves to next hashtag
5. Press `↑` (up arrow)
6. ✅ **Expected**: Selection moves to previous hashtag
7. Press `Enter`
8. ✅ **Expected**: Selected hashtag is inserted

#### Test 3: Escape Key
1. Type: `#test`
2. ✅ **Expected**: Dropdown appears
3. Press `Esc`
4. ✅ **Expected**: Dropdown closes
5. Hashtag query remains as `#test` (not inserted)

#### Test 4: Click Outside
1. Type: `#python`
2. ✅ **Expected**: Dropdown appears
3. Click outside the dropdown (e.g., in editor elsewhere)
4. ✅ **Expected**: Dropdown closes

#### Test 5: Multiple Hashtags
1. Type: `Check out #javascript and #react for #webdev`
2. For each hashtag:
   - ✅ **Expected**: Autocomplete appears
   - ✅ **Expected**: Can select from suggestions
   - ✅ **Expected**: All hashtags display in blue

#### Test 6: Trending Badge
1. Type: `#` followed by a trending hashtag name
2. ✅ **Expected**: Dropdown shows "Trending" orange badge
3. ✅ **Expected**: Shows post count (e.g., "142 posts")

#### Test 7: No Results
1. Type: `#xyznonexistenthashtag123`
2. ✅ **Expected**: Either empty dropdown or "No results" message

#### Test 8: Single Character
1. Type just: `#`
2. ✅ **Expected**: No dropdown appears (requires at least 1 character)

### 4. **Test API Integration**

#### Check Network Tab
1. Open browser DevTools (F12)
2. Go to Network tab
3. Type: `#java`
4. ✅ **Expected**: See API call: `GET /api/content/posts/hashtags/?search=java&limit=20`
5. ✅ **Expected**: Response shows hashtag data:
   ```json
   {
     "results": [
       {
         "name": "javascript",
         "posts_count": 142,
         "is_trending": true
       }
     ]
   }
   ```

#### Check Debouncing
1. Type quickly: `#javaS` → `#javasc` → `#javascript`
2. ✅ **Expected**: Only one or two API calls (not one per keystroke)
3. ✅ **Expected**: 300ms delay before API call

### 5. **Test Dropdown Positioning**

#### Cursor Position
1. Type some text: `Hello world`
2. Press Enter to new line
3. Type: `#test`
4. ✅ **Expected**: Dropdown appears right below `#test` text
5. ✅ **Expected**: Dropdown not far away from cursor

#### Scroll Position
1. Type enough content to scroll the editor
2. Scroll down
3. Type: `#hashtag`
4. ✅ **Expected**: Dropdown appears at correct position (not offset by scroll)

#### Screen Edge
1. Type hashtag near right edge of editor
2. ✅ **Expected**: Dropdown stays visible (doesn't go off-screen)

### 6. **Test Dark Mode** (if applicable)
1. Enable dark mode in application
2. Type: `#test`
3. ✅ **Expected**: Dropdown has dark background
4. ✅ **Expected**: Text is readable (light text on dark background)
5. ✅ **Expected**: Hover state works correctly

### 7. **Test Backend Processing**

#### Submit Post with Hashtag
1. Create post with content: `Loving #javascript today!`
2. Submit post
3. ✅ **Expected**: Post saves successfully
4. View post
5. ✅ **Expected**: Hashtag displays in blue
6. ✅ **Expected**: Hashtag is clickable (leads to hashtag page)

#### Hashtag Count
1. Note current count for `#javascript` (e.g., "142 posts")
2. Create new post with `#javascript`
3. Submit
4. Type `#java` again
5. ✅ **Expected**: Count incremented (e.g., "143 posts")

### 8. **Browser Console Checks**

#### No Errors
1. Open Console tab (F12)
2. Perform all tests above
3. ✅ **Expected**: No red errors in console
4. ✅ **Expected**: No warning about failed API calls

#### Debug Logs (if enabled)
1. Check console while typing `#test`
2. Should see logs like:
   - `"Hashtag query changed: test"`
   - `"Searching hashtags for: test"`
   - `"Found 5 hashtag suggestions"`

### 9. **React DevTools Checks**

#### State Updates
1. Install React DevTools extension
2. Open Components tab
3. Find `RichTextEditor` component
4. Type: `#react`
5. ✅ **Expected**: See state updates:
   - `hashtagQuery: "react"`
   - `hashtagSuggestions: [{name: "react", posts_count: 89, ...}]`
   - `showHashtagDropdown: true`
   - `selectedHashtagIndex: 0`

### 10. **Edge Cases**

#### Special Characters
1. Type: `#test@#$%`
2. ✅ **Expected**: Only word characters after `#` (stops at special char)

#### Numbers
1. Type: `#react18`
2. ✅ **Expected**: Autocomplete works with numbers

#### Case Sensitivity
1. Type: `#JAVASCRIPT`
2. ✅ **Expected**: Finds `#javascript` (case-insensitive search)

#### Empty Query
1. Type: `#` then delete it
2. ✅ **Expected**: Dropdown closes, state resets

## Common Issues & Solutions

### ❌ Dropdown not appearing
**Solution:**
- Check browser console for errors
- Verify backend is running: `docker-compose ps`
- Check API endpoint: `curl http://localhost:8000/api/content/posts/hashtags/?search=test`
- Inspect `hashtagSuggestions` in React DevTools

### ❌ Dropdown far from cursor
**Solution:**
- Check `hashtagDropdownPosition` in React DevTools
- Should have `top` and `left` values close to cursor
- Verify no extra `window.scrollY` offsets being added

### ❌ Double hashtag (##test)
**Solution:**
- Check `hashtagCommandRef.current` is being used
- Verify `props.command()` is called (not `editor.insertContent()`)

### ❌ API returning 404
**Solution:**
- Check Django backend logs
- Verify route exists in `content/unified_urls.py`
- Ensure hashtag model migrations are applied

### ❌ Styling not working
**Solution:**
- Check `.hashtag` CSS class is applied in HTML
- Inspect element in browser DevTools
- Verify Tailwind classes and custom CSS are loaded

## Success Criteria

All tests pass if:
- ✅ Hashtag autocomplete appears when typing `#`
- ✅ Suggestions are fetched from API
- ✅ Keyboard navigation works (↑↓, Enter, Esc)
- ✅ Mouse click selection works
- ✅ Hashtags display in blue with background color
- ✅ Multiple hashtags work in same post
- ✅ Dropdown positioning is correct
- ✅ No errors in console
- ✅ Backend processes hashtags correctly
- ✅ Post count and trending status display

## Next Steps After Testing

If all tests pass:
1. Remove debug console.log statements (optional)
2. Test with real users
3. Monitor hashtag trends and popular tags
4. Consider adding recent hashtags feature
5. Add hashtag analytics dashboard

If tests fail:
1. Check `TIPTAP_HASHTAG_IMPLEMENTATION.md` for detailed documentation
2. Review error messages in console
3. Check backend Django logs
4. Verify API responses in Network tab
5. Inspect React component state in DevTools
