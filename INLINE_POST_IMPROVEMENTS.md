# InlinePostCreator Improvements Plan

## Issues to Address

### 1. Emoji picker not showing in inline TipTap mode
**Problem**: Emoji button doesn't show picker frame
**Solution**:
- Check if emoji picker is rendered for inline mode
- Add relative positioning container for inline toolbar
- Ensure z-index and positioning work correctly

### 2. Media buttons (image/video/audio) have no dialog
**Problem**: No visual feedback when clicking media buttons in quick mode
**Solution**:
- Add file input dialogs for each media type
- Show preview after selection
- Display upload progress
- Show selected file info (name, size, type)

### 3. Poll needs full integration
**Problem**: Poll button missing full functionality
**Solution**:
- Poll should expand below rich text (not modal)
- Add poll question field
- Add multiple option fields (add/remove dynamically)
- Add settings:
  - Expiry date/time picker
  - Multiple choice checkbox
  - Anonymous voting
  - Show results before voting
  - Allow vote changes
- Attach poll to post

### 4. Emoji menu position in article mode
**Problem**: Emoji picker opens to the right and gets cut off
**Solution**:
- Change positioning from `left-0` to `right-0` in full mode
- Keep `left-0` for inline mode

### 5. Server-side article enhancements
**Problem**: Missing featured image, excerpt, draft support
**Solution**:
- Backend: Add API endpoints for draft save/load/list
- Backend: Update article creation to handle featured_image, excerpt
- Frontend: Add UI for featured image upload
- Frontend: Add excerpt textarea
- Frontend: Add draft management (save, list, load, delete)
- Frontend: Auto-save draft every 30s
- Frontend: "My Drafts" button to view/manage drafts

## Implementation Order

1. Fix emoji picker in inline mode (quick)
2. Add media upload dialogs (moderate)
3. Fix emoji position in article mode (quick)
4. Implement poll UI expansion (complex)
5. Server-side drafts + featured image + excerpt (complex)

## Files to Modify

### Frontend
- `src/components/ui/RichTextEditor.jsx` - emoji positioning
- `src/components/InlinePostCreator.jsx` - media dialogs, poll UI
- `src/components/modals/RichArticleModal.jsx` - featured image, excerpt, drafts
- `src/components/PollCreator.jsx` - NEW: comprehensive poll component

### Backend
- `content/models.py` - ensure Article has featured_image, excerpt
- `content/serializers.py` - add featured_image, excerpt fields
- `content/views.py` - add draft endpoints
- `content/urls.py` - route draft endpoints

## Timeline
- Items 1-3: 1-2 hours
- Item 4: 2-3 hours
- Item 5: 3-4 hours
- Total: 6-9 hours of focused work
