# Quick Test Checklist - Tiptap Mention System

## ✅ Pre-Test Checklist

- [ ] Docker containers are running: `docker-compose ps`
- [ ] Backend is healthy: `docker-compose logs backend | grep "Starting development server"`
- [ ] Frontend is healthy: `docker-compose logs frontend | grep "webpack compiled"`
- [ ] You're logged in to the app
- [ ] At least one user exists with username containing "admin"

---

## 🧪 Test Steps

### Test 1: Basic Mention Insertion

1. [ ] Open your app in browser
2. [ ] Navigate to post creation (anywhere with RichTextEditor)
3. [ ] Click inside the editor
4. [ ] Type `@` (at symbol)
5. [ ] **Expected:** Nothing appears yet (waiting for query)
6. [ ] Type `a` (so it's `@a`)
7. [ ] **Expected:** Dropdown appears with users whose username contains "a"
8. [ ] Continue typing: `@ad`, `@adm`, `@admin`
9. [ ] **Expected:** Dropdown filters to show only matching users

### Test 2: Keyboard Navigation

1. [ ] Type `@a` to show dropdown
2. [ ] Press `↓` (down arrow)
3. [ ] **Expected:** Highlights next user
4. [ ] Press `↑` (up arrow)
5. [ ] **Expected:** Highlights previous user
6. [ ] Press `Enter`
7. [ ] **Expected:** Mention inserted as blue `@username`, dropdown closes

### Test 3: Mouse Selection

1. [ ] Type `@admin` to show dropdown
2. [ ] Hover over a user
3. [ ] **Expected:** User highlights on hover
4. [ ] Click on the user
5. [ ] **Expected:** Mention inserted, dropdown closes

### Test 4: Escape Key

1. [ ] Type `@admin` to show dropdown
2. [ ] Press `Esc`
3. [ ] **Expected:** Dropdown closes, `@admin` remains as plain text

### Test 5: Space After @

1. [ ] Type `@admin ` (with space)
2. [ ] **Expected:** Dropdown closes immediately, no mention created (plain text)

### Test 6: Multiple Mentions

1. [ ] Type: `Hey @admin, can you check with @john?`
2. [ ] Insert both mentions using dropdown
3. [ ] **Expected:** Both `@admin` and `@john` appear in blue
4. [ ] Submit the post
5. [ ] **Expected:** Backend processes both mentions

### Test 7: Categories Display

1. [ ] Type `@a` to show dropdown
2. [ ] **Expected:** Users grouped by category:
   - "People you follow" (if you follow anyone)
   - "Post author" (if replying to a post)
   - "Community members" (if in community context)
   - "Public profiles" (fallback)

### Test 8: Priority Badges

1. [ ] Type `@` followed by someone you follow
2. [ ] **Expected:** User shows "Following" badge in green
3. [ ] Type `@` in a post reply
4. [ ] **Expected:** Post author shows "Author" badge in blue

---

## 🔍 Browser Console Checks

Open DevTools (F12) and check:

### Console Tab

- [ ] No red errors
- [ ] No warnings about missing dependencies
- [ ] (Optional) See search logs if debug mode enabled

### Network Tab

When typing `@admin`, check for:

- [ ] Multiple `GET /api/profiles/search_mentionable/` requests
- [ ] Status: `200 OK`
- [ ] Response contains user data:
```json
{
  "results": [
    {
      "id": 123,
      "username": "admin",
      "display_name": "Admin User",
      "category": "Public profiles"
    }
  ]
}
```

### Elements Tab

After inserting mention:

- [ ] Inspect the mention text
- [ ] **Expected HTML:**
```html
<span class="mention" data-type="mention" data-id="123" data-label="admin">
  @admin
</span>
```
- [ ] Has class: `mention text-blue-600 font-medium`

---

## 🐛 Common Issues & Quick Fixes

| Issue | Symptom | Quick Fix |
|-------|---------|-----------|
| **No dropdown** | Type `@admin`, nothing happens | Check: Backend running? Logged in? User exists? |
| **Empty dropdown** | Dropdown appears but empty | Database has no users matching query |
| **401 Error** | Network tab shows 401 | Token expired - log out and log back in |
| **Dropdown wrong position** | Appears far from cursor | Refresh page, check CSS conflicts |
| **Can't type** | Editor is frozen | Backend error - check `docker-compose logs backend` |

---

## ✨ Success Criteria

All these should be true:

✅ Dropdown appears when typing `@` + character
✅ Shows real users from your database
✅ Can navigate with keyboard (arrows, enter, escape)
✅ Can select with mouse click
✅ Mention appears in blue color
✅ Multiple mentions work in same content
✅ No console errors
✅ API requests succeed (200 status)
✅ Backend processes mentions after post submission

---

## 📸 Visual Examples

### Dropdown Appearance

```
┌────────────────────────────────────────┐
│ People you follow                      │
│ ┌─────┐                                │
│ │ A  │  @alice (Alice Smith)  Following│
│ └─────┘                                │
│ ┌─────┐                                │
│ │ AD │  @admin (Administrator) Following│
│ └─────┘                                │
├────────────────────────────────────────┤
│ Public profiles                        │
│ ┌─────┐                                │
│ │ A  │  @adam (Adam Johnson)           │
│ └─────┘                                │
├────────────────────────────────────────┤
│ Use ↑↓ to navigate, Enter to select   │
└────────────────────────────────────────┘
```

### In-Editor Appearance

```
Plain text: Hey @admin, how are you?
           ^^^^^^^
           Blue, bold mention
```

---

## 🎯 Quick Docker Commands

```bash
# Restart frontend container
docker-compose restart frontend

# View frontend logs in real-time
docker-compose logs -f frontend

# View backend logs
docker-compose logs -f backend

# Rebuild if dependencies changed
docker-compose build frontend
docker-compose up -d

# Check container status
docker-compose ps

# Access frontend shell
docker-compose exec frontend sh

# Access backend shell
docker-compose exec backend bash
```

---

## 🔧 If Nothing Works

### Nuclear Option: Full Restart

```bash
# Stop everything
docker-compose down

# Remove volumes (if needed)
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache

# Start fresh
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Verify Installation

```bash
# Inside frontend container
docker-compose exec frontend sh

# Check if mention extension exists
yarn list --pattern "@tiptap/extension-mention"

# Should show:
# @tiptap/extension-mention@^3.4.4

# If not found, install:
yarn add @tiptap/extension-mention

# Exit container
exit

# Restart
docker-compose restart frontend
```

---

## 📝 Report Issues

If tests fail, provide:

1. **Browser console output** (copy-paste errors)
2. **Network tab screenshot** (showing API calls)
3. **Docker logs:**
   ```bash
   docker-compose logs frontend > frontend.log
   docker-compose logs backend > backend.log
   ```
4. **Test step where it failed** (e.g., "Test 2, step 3")

Then I can help debug the specific issue! 🚀
