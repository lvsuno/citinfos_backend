# Backend Auto-Save Implementation

## Overview
Implemented a hybrid auto-save strategy that saves article drafts to the Django backend instead of just localStorage. This ensures drafts persist across devices, browsers, and sessions.

## Configuration

### Auto-Save Strategy: Hybrid
- **Debounce delay**: 5 seconds after user stops typing
- **Max interval**: 60 seconds (forced save if typing continuously)
- **Change detection**: Only saves if content actually changed since last save
- **Draft model**: Single draft per article (create once, update repeatedly)

## How It Works

### 1. Debounce Timer (Primary)
```
User types: "Hello"
  ↓
[Wait 5 seconds]
  ↓
User stops typing
  ↓
✅ Save to backend API
```

### 2. Force Save Timer (Backup)
```
User types continuously for 2 minutes
  ↓
[60 seconds passed since last save]
  ↓
✅ Force save to backend API
  ↓
[User keeps typing...]
  ↓
[Another 60 seconds]
  ↓
✅ Force save again
```

### 3. Change Detection
- Tracks last saved content: `title`, `content`, `excerpt`
- Only saves if any field changed
- Avoids unnecessary API calls for identical content

### 4. Draft Lifecycle

#### Creating Draft
```javascript
// First auto-save creates a new draft
const response = await contentAPI.createPost(formData);
setDraftId(response.id); // Store ID for future updates
```

#### Updating Draft
```javascript
// Subsequent saves update the same draft
await contentAPI.updatePost(draftId, formData);
```

#### Publishing Draft
```javascript
// When user clicks "Publier l'article"
if (draftId && !saveAsDraft) {
  // Update draft with is_draft=false
  await contentAPI.updatePost(draftId, formData);
  setDraftId(null); // Clear tracking
}
```

#### Draft Removal
- ✅ Draft is automatically "published" when user clicks "Publier l'article"
- ✅ Backend sets `is_draft=false` on the existing draft post
- ✅ Draft ID is cleared from component state
- ❌ Draft is NOT deleted when modal closes (preserved for later editing)
- ❌ Draft is NOT deleted when user cancels (preserved for later editing)

## Features

### What's Saved Automatically
- ✅ Title
- ✅ Content (TipTap rich text HTML)
- ✅ Excerpt/Résumé
- ✅ Featured image (if uploaded)
- ✅ Visibility setting
- ✅ Division/section context

### Visual Feedback
Status indicator in modal header shows:
- 💾 **"Sauvegarde..."** - Currently saving to backend
- ✓ **"Brouillon sauvegardé"** - Successfully saved (displays for 3 seconds)
- ⚠ **"Erreur de sauvegarde"** - Save failed (displays for 3 seconds)

### API Calls
**Endpoint**: `/api/content/posts/`

**Create Draft** (first auto-save):
```
POST /api/content/posts/
FormData: {
  content: "Title or 'Brouillon sans titre'",
  article_content: "<p>Rich HTML content</p>",
  excerpt: "Optional excerpt",
  post_type: "article",
  visibility: "public",
  is_draft: true,
  featured_image: File (if exists),
  division_id: UUID,
  section: "actualites",
  community: UUID (if in community context)
}
```

**Update Draft** (subsequent auto-saves):
```
PATCH /api/content/posts/{draft_id}/
FormData: {
  // Same fields as create
}
```

**Publish Draft**:
```
PATCH /api/content/posts/{draft_id}/
FormData: {
  // Same fields but:
  is_draft: false
}
```

## Timing Examples

### Example 1: User types and pauses
```
0s:  User opens modal
2s:  User types "Hello"
7s:  [5 seconds after last keystroke] → ✅ Save draft (creates draft ID: 123)
10s: User types " world"
15s: [5 seconds after last keystroke] → ✅ Update draft 123
20s: User closes modal
     → Draft 123 remains in backend for later editing
```

### Example 2: User types continuously
```
0s:   User opens modal
5s:   User types continuously...
10s:  Still typing...
60s:  [60 seconds passed] → ✅ Force save (creates draft ID: 456)
65s:  Still typing...
120s: [60 seconds since last save] → ✅ Force save (updates draft 456)
125s: User stops typing
130s: [5 seconds after stopping] → ✅ Update draft 456
```

### Example 3: Publishing
```
0s:   User opens modal
10s:  User types article
15s:  [5 seconds after typing] → ✅ Save draft (creates draft ID: 789)
30s:  User clicks "Publier l'article"
      → ✅ Update draft 789 with is_draft=false
      → Draft 789 is now a published post
      → Modal closes, draftId cleared
```

## State Management

### Component State
```javascript
// Draft tracking
const [draftId, setDraftId] = useState(null);           // Backend draft ID
const lastSaveRef = useRef(null);                       // Timestamp of last save
const lastContentRef = useRef({ title: '', content: '', excerpt: '' }); // Last saved content

// UI feedback
const [autoSaveStatus, setAutoSaveStatus] = useState(''); // 'saving' | 'saved' | 'error'
```

### Refs Usage
- **lastSaveRef**: Tracks when we last saved to enforce 60-second max interval
- **lastContentRef**: Tracks what we last saved to detect actual changes
- **prevSectionRef**: Tracks section changes for navigation handling (existing)

## Migration from localStorage

### Backward Compatibility
- Old localStorage draft loading still works (for existing drafts)
- New auto-save uses backend exclusively
- localStorage draft cleared on successful publish

### Migration Path
```javascript
// On modal open
useEffect(() => {
  if (!isOpen) return;

  // Load old localStorage draft (if exists)
  const savedDraft = localStorage.getItem('article_draft');
  if (savedDraft) {
    const draft = JSON.parse(savedDraft);
    setTitle(draft.title || '');
    setContent(draft.content || '');
    setExcerpt(draft.excerpt || '');
    // After loading, backend auto-save takes over
  }
}, [isOpen]);
```

## Error Handling

### Auto-Save Failures
```javascript
try {
  await saveDraftToBackend();
  setAutoSaveStatus('saved');
} catch (err) {
  console.error('Auto-save failed:', err);
  setAutoSaveStatus('error');
  // Draft remains in memory, retry on next timer
}
```

**Retry Logic**:
- Automatic retry on next debounce/force-save interval
- No manual retry needed - just keep typing
- Error status shows briefly, then clears

### Network Issues
- If save fails, content remains in browser memory
- Next auto-save attempt will retry with current content
- User can manually click "Sauvegarder comme brouillon" if concerned

## Testing Checklist

### Auto-Save Functionality
- [ ] Type content → Wait 5 seconds → Check backend for draft
- [ ] Type continuously for 70 seconds → Check draft saved at 60-second mark
- [ ] Type, save, type same content → No additional save (change detection)
- [ ] Upload featured image → Check image saved in draft
- [ ] Navigate away with content → Draft persists in backend
- [ ] Reopen modal → Draft should NOT auto-load (need to implement draft list)

### Publishing Workflow
- [ ] Create auto-saved draft → Click "Publier" → Draft converts to published post
- [ ] Check backend: `is_draft=false` on published post
- [ ] Check: draftId cleared after publish
- [ ] Check: Can't re-publish same draft

### Error Scenarios
- [ ] Disconnect network → Type → Error status shows
- [ ] Reconnect → Next save succeeds
- [ ] Backend error → Error status shows → Retry works

### UI Feedback
- [ ] Status shows "💾 Sauvegarde..." during save
- [ ] Status shows "✓ Brouillon sauvegardé" after success
- [ ] Status shows "⚠ Erreur de sauvegarde" on failure
- [ ] Status clears after 3 seconds

## Performance Considerations

### API Load
- **Worst case**: 1 save per 5 seconds (if typing and pausing repeatedly)
- **Typical case**: 1 save per 60 seconds (if typing continuously)
- **Best case**: 1-2 saves total (type once, pause, done)

### Database Impact
- Creates 1 draft record per article
- Updates same record on subsequent saves
- No draft accumulation (single draft per article session)

### Network Usage
- FormData with text: ~1-5 KB per save
- With featured image: ~100 KB - 5 MB per save (only on first save or image change)
- Reasonable for modern networks

## Future Enhancements

### Potential Improvements
1. **Draft List**: Show user's existing drafts to resume editing
2. **Draft Metadata**: Show last edited time, word count
3. **Draft Cleanup**: Auto-delete old drafts after X days
4. **Conflict Resolution**: Handle concurrent edits from multiple devices
5. **Offline Support**: Queue saves when offline, sync when online
6. **Version History**: Track draft revisions for rollback

## Files Modified

1. **`src/components/modals/RichArticleModal.jsx`**
   - Added contentAPI import
   - Added auto-save state: draftId, autoSaveStatus, refs
   - Replaced localStorage auto-save with backend auto-save
   - Added saveDraftToBackend() function
   - Updated handleSubmit() to use draftId for publishing
   - Updated resetForm() to clear draft tracking
   - Added auto-save status indicator in UI

## Deployment

```bash
docker-compose restart frontend
```

Frontend restarted successfully ✅

## Backend Requirements

### Existing Support
- ✅ `is_draft` boolean field on Post model
- ✅ Create post API: `POST /api/content/posts/`
- ✅ Update post API: `PATCH /api/content/posts/{id}/`
- ✅ Supports FormData with file uploads

### No Backend Changes Needed
The backend already supports everything needed for this feature!

