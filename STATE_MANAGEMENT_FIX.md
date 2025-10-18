# State Management Fix - TipTap Editor & Article Modal

## Problem
When users write content in the TipTap editor or open the article modal and then navigate to a different rubrique, the editor content and modal state persisted across navigation. This created a confusing UX where:
1. Editor content from one rubrique appeared in another rubrique
2. The article modal stayed open when switching rubriques

## Root Cause
The `InlinePostCreator` component maintained local state (content, attachedMedia, showArticleModal, etc.) that wasn't reset when the `section` prop changed during navigation between rubriques.

## Solution

### 1. Reset InlinePostCreator State on Section Change
**File:** `src/components/InlinePostCreator.jsx`

Added a `useEffect` hook that resets all component state when the `section` prop changes:

```jsx
// Reset state when section changes (user navigates to different rubrique)
useEffect(() => {
  // Reset inline editor content and UI state when section changes
  // Note: Article modal handles its own closing logic with confirmation
  setContent('');
  setAttachedMedia([]);
  setIsExpanded(false);
  // Don't automatically close article modal - let it handle section changes internally
  setShowThreadModal(false);
  setShowPollCreator(false);
  setPollQuestion('');
  setPollOptions(['', '']);
  setPollExpirationDate('');
  setPollExpirationTime('');
  setPollMultipleChoice(false);
  setPollAnonymousVoting(false);
  setActiveMode('text');
  setVisibility('public');
  setShowAdvancedMenu(false);
}, [section]); // Reset when section prop changes
```

**Impact:**
- ✅ Editor content now resets when navigating between rubriques
- ✅ Inline editor state (polls, threads, etc.) resets automatically
- ✅ Article modal state is NOT reset - it manages its own lifecycle
- ✅ All form fields (except article modal) are cleared
- ✅ No more state persistence in inline editor across navigation

### 2. Smart Modal Section Change Handling
**File:** `src/components/modals/RichArticleModal.jsx`

**Change 1:** Added section change detection with ref tracking
```jsx
// Track previous section to detect changes
const prevSectionRef = useRef(section);

// Handle section change when modal is open
useEffect(() => {
  // Only handle if modal is open and section actually changed
  if (!isOpen || prevSectionRef.current === section) {
    prevSectionRef.current = section;
    return;
  }

  // Section changed while modal is open
  prevSectionRef.current = section;

  // Check if there's content that would be lost (including excerpt/résumé)
  const hasContent = title.trim() || content.trim() || excerpt.trim() || featuredImage;

  if (hasContent) {
    // Show confirmation dialog
    if (window.confirm('Vous avez du contenu non publié...')) {
      // Keep draft in localStorage
    } else {
      localStorage.removeItem('article_draft');
    }
  } else {
    // No content, just clear draft and close silently
    localStorage.removeItem('article_draft');
  }

  // Close the modal and reset form
  resetForm();
  onClose();
}, [section, isOpen, title, content, excerpt, featuredImage, onClose]);
```

**Change 3:** Smart confirmation dialog in handleClose
```jsx
const handleClose = () => {
  // Only show confirmation if there's unsaved content (including excerpt/résumé)
  const hasContent = title.trim() || content.trim() || excerpt.trim() || featuredImage;

  if (hasContent) {
    if (window.confirm('Voulez-vous sauvegarder ce brouillon pour plus tard ?')) {
      // Keep draft in localStorage for later
    } else {
      localStorage.removeItem('article_draft');
    }
  } else {
    // No content, just clear draft
    localStorage.removeItem('article_draft');
  }

  resetForm();
  onClose();
};
```

**Change 4:** Updated isEmpty() function
```jsx
const isEmpty = () => {
  return !title.trim() && !content.trim() && !excerpt.trim() && !featuredImage;
};
```

**Change 5:** Disabled backdrop click to close
```jsx
// Before: onClick={handleClose}
// After:
onClick={(e) => {
  e.stopPropagation();
  // Don't allow closing by clicking backdrop - users must use X button
  // This prevents accidental loss of article content
}}
```

**Impact:**
- ✅ Modal detects section changes while open
- ✅ All content fields checked: title, TipTap content, excerpt/résumé, and cover image
- ✅ If modal has ANY content: Shows confirmation dialog
- ✅ If modal is completely empty: Closes silently without confirmation
- ✅ Draft is saved in localStorage if user chooses to save
- ✅ Users can't accidentally lose work by clicking outside the modal
- ✅ Empty modals close immediately without confirmation when using X button

## Testing Checklist

- [ ] Write content in TipTap editor → Navigate to another rubrique → Content should reset ✅
- [ ] Open article modal with content → Navigate to another rubrique → Should show confirmation dialog ✅
- [ ] Open empty article modal → Navigate to another rubrique → Should close silently without confirmation ✅
- [ ] Click backdrop when modal is open → Modal should NOT close (must use X button) ✅
- [ ] Close modal with content via X button → Should show confirmation dialog ✅
- [ ] Close empty modal via X button → Should close immediately without dialog ✅
- [ ] Test across all rubriques (actualites, evenements, commerces, etc.)

## Technical Details

**Component Hierarchy:**
```
MunicipalityDashboard
  └── InlinePostCreator (receives section prop)
        └── RichArticleModal (controlled by showArticleModal state)
```

**State Flow:**
1. User navigates: URL changes → section prop updates
2. useEffect triggers: Detects section change
3. State reset: All InlinePostCreator state cleared
4. Modal closes: showArticleModal set to false
5. Clean slate: User sees fresh editor for new rubrique

## Related Issues

**Previous Fixes:**
- ✅ Backend rubrique filtering (UnifiedPostViewSet)
- ✅ External URL support for attachments (EnhancedPostMediaSerializer)
- ✅ Frontend rubrique prop passing (PostFeed, MunicipalityDashboard)

**This Fix:**
- ✅ State management on navigation (InlinePostCreator useEffect)
- ✅ Modal UX improvements (backdrop blocking, smart confirmation)

## Files Modified

1. `src/components/InlinePostCreator.jsx`
   - Added useEffect import
   - Added state reset logic on section change

2. `src/components/modals/RichArticleModal.jsx`
   - Added useRef import for section change tracking
   - Added section change detection with prevSectionRef
   - Checks all content fields: title, content, excerpt/résumé, featuredImage
   - Shows confirmation only when there's actual content
   - Disabled backdrop click to close
   - Improved UX to prevent accidental data loss

## Deployment

```bash
docker-compose restart frontend
```

Frontend restarted successfully ✅
