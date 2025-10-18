# Rubrique Filtering & Draft Button Fix

**Date:** October 16, 2025
**Issues Fixed:**
1. ❌ All 8 posts were displayed in EVERY rubrique (no filtering)
2. ❌ "Save Draft" button not disabled when article is empty

---

## Problem 1: Posts Not Filtered by Rubrique

### Root Cause
The backend API endpoint `/api/content/posts/` was filtering by `community_id` but **NOT by rubrique**. All posts belong to the "Actualités" rubrique, but when clicking on other rubriques (like "Événements"), the API still returned all 8 posts.

### Solution

#### Backend Changes (`content/unified_views.py`)
Added rubrique filtering to `UnifiedPostViewSet.get_queryset()`:

```python
# Filter by rubrique template (either ID or template_type)
rubrique_id = self.request.query_params.get('rubrique_id')
rubrique_slug = (
    self.request.query_params.get('rubrique') or
    self.request.query_params.get('rubrique_slug')
)

if rubrique_id:
    # Filter by rubrique UUID
    queryset = queryset.filter(rubrique_template_id=rubrique_id)
elif rubrique_slug:
    # Filter by rubrique template_type (slug)
    # Special case: "accueil" shows ALL posts (no filter)
    if rubrique_slug.lower() != 'accueil':
        queryset = queryset.filter(
            rubrique_template__template_type=rubrique_slug
        )
```

**Supports 3 query parameters:**
- `?rubrique=actualites` - Filter by template_type (slug)
- `?rubrique_slug=actualites` - Alternative parameter name
- `?rubrique_id=<uuid>` - Filter by rubrique UUID

**Special case:** `?rubrique=accueil` shows ALL posts (no filter applied)

#### Frontend Changes

**1. MunicipalityDashboard.js** (line 519)
```javascript
// Before (WRONG - was passing display name)
<PostFeed
    municipalityName={municipality.nom}
    municipalityId={pageDivision?.id}
    section={getSectionDisplayName(sectionLower)}  // ❌ "Actualités"
    onCreatePostClick={onOpenPostCreationModal}
/>

// After (CORRECT - passes slug)
<PostFeed
    municipalityName={municipality.nom}
    municipalityId={pageDivision?.id}
    rubrique={sectionLower}  // ✅ "actualites"
    onCreatePostClick={onCreatePostClick}
/>
```

**2. PostFeed.js** (lines 14, 31, 64)
```javascript
// Changed prop name from `section` to `rubrique`
const PostFeed = ({
    municipalityName,
    municipalityId = null,
    communityId = null,
    rubrique = null,  // ✅ Changed from section
    onCreatePostClick
}) => {
    // ...

    const response = await contentAPI.getPosts({
        page: pageNum,
        page_size: 20,
        ...(communityId && { community_id: communityId }),
        ...(!communityId && municipalityId && { community_id: municipalityId }),
        ...(rubrique && { rubrique: rubrique }),  // ✅ Pass rubrique to API
        ordering: '-created_at',
    });

    // ...dependency array updated
    useEffect(() => {
        if (municipalityName || municipalityId || communityId) {
            fetchFeed(1, true);
        } else {
            setLoading(false);
        }
    }, [municipalityName, municipalityId, communityId, rubrique]);  // ✅
}
```

### API Testing Results

```bash
# Test 1: Actualités (has 8 posts)
curl "http://localhost:8000/api/content/posts/?community_id=xxx&rubrique=actualites"
# Result: ✅ 8 posts returned

# Test 2: Événements (has 0 posts)
curl "http://localhost:8000/api/content/posts/?community_id=xxx&rubrique=evenements"
# Result: ✅ 0 posts returned

# Test 3: Accueil (shows all posts)
curl "http://localhost:8000/api/content/posts/?community_id=xxx&rubrique=accueil"
# Result: ✅ 8 posts returned
```

---

## Problem 2: Draft Button Not Disabled When Empty

### Root Cause
The "Save Draft" button in `RichArticleModal.jsx` was only disabled during submission (`isSubmitting`), but not when the article was completely empty.

### Solution

Added `isEmpty()` helper function and updated button logic:

```javascript
// Check if article is completely empty
const isEmpty = () => {
  return !title.trim() && !content.trim() && !featuredImage;
};

// Updated button (line 397)
<button
  type="button"
  onClick={(e) => handleSubmit(e, true)}
  disabled={isSubmitting || isEmpty()}  // ✅ Added isEmpty() check
  className="px-4 py-2 bg-gray-600 text-white font-medium rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
  title={isEmpty() ? "Ajoutez du contenu avant de sauvegarder" : "Sauvegarder comme brouillon"}
>
  {isSubmitting ? 'Sauvegarde...' : 'Sauvegarder comme brouillon'}
</button>
```

**Button States:**

| Title | Content | Image | Save Draft | Publish |
|-------|---------|-------|------------|---------|
| ❌ | ❌ | ❌ | **DISABLED** ✅ | **DISABLED** |
| ✅ | ❌ | ❌ | ENABLED | **DISABLED** |
| ❌ | ✅ | ❌ | ENABLED | **DISABLED** |
| ❌ | ❌ | ✅ | ENABLED | **DISABLED** |
| ✅ | ✅ | ❌ | ENABLED | **ENABLED** ✅ |
| ✅ | ✅ | ✅ | ENABLED | **ENABLED** ✅ |

**Tooltip added:** Hovering over disabled "Save Draft" button shows: "Ajoutez du contenu avant de sauvegarder"

---

## Files Modified

### Backend
- ✅ `content/unified_views.py` - Added rubrique filtering (lines 114-127)

### Frontend
- ✅ `src/pages/MunicipalityDashboard.js` - Changed `section` to `rubrique` prop (line 519)
- ✅ `src/components/PostFeed.js` - Updated to use `rubrique` parameter (lines 14, 31, 64)
- ✅ `src/components/modals/RichArticleModal.jsx` - Added `isEmpty()` check for draft button (lines 82-85, 397-402)

---

## Testing Checklist

### Backend API ✅
- [x] `/api/content/posts/?rubrique=actualites` returns 8 posts
- [x] `/api/content/posts/?rubrique=evenements` returns 0 posts
- [x] `/api/content/posts/?rubrique=accueil` returns 8 posts (all)
- [x] Backend restarted and changes applied

### Frontend UI (TODO - Please Test)
- [ ] Navigate to `/sherbrooke/accueil` → Should show all 8 posts
- [ ] Navigate to `/sherbrooke/actualites` → Should show 8 posts
- [ ] Navigate to `/sherbrooke/evenements` → Should show "No posts" message
- [ ] Navigate to `/sherbrooke/commerces` → Should show "No posts" message
- [ ] Click between rubriques → Posts should update based on rubrique
- [ ] Open RichArticleModal with empty fields → "Save Draft" button should be disabled
- [ ] Type title → "Save Draft" button should become enabled
- [ ] Clear title and add content → "Save Draft" button should be enabled
- [ ] Add only image → "Save Draft" button should be enabled
- [ ] Hover over disabled "Save Draft" → Should show tooltip

---

## How It Works Now

### Rubrique Filtering Flow
1. User clicks "Actualités" in sidebar
2. URL changes to `/sherbrooke/actualites`
3. `MunicipalityDashboard` receives `section="actualites"` from URL params
4. Passes `rubrique="actualites"` to `PostFeed`
5. `PostFeed` calls API: `GET /api/content/posts/?community_id=xxx&rubrique=actualites`
6. Backend filters: `Post.objects.filter(rubrique_template__template_type='actualites')`
7. Returns only posts in Actualités rubrique
8. Frontend displays filtered posts

### Draft Button Logic
1. User opens article creation modal
2. All fields empty → `isEmpty()` returns `true` → "Save Draft" disabled
3. User types title → `isEmpty()` returns `false` → "Save Draft" enabled
4. User can save partial draft (title only, content only, or image only)
5. User completes title + content → "Publish" button enabled
6. Backend validation prevents publishing incomplete articles

---

## Next Steps

1. **Test frontend changes** - Navigate between rubriques and verify posts are filtered correctly
2. **Test draft button** - Open article modal and verify button states
3. **Frontend rebuild** - Run `docker-compose restart frontend` if needed
4. **User testing** - Have real users test the rubrique navigation

---

## Success Criteria

✅ **Backend:** Rubrique filtering implemented and tested
✅ **Frontend:** Props updated to pass rubrique slug
✅ **Draft Button:** Disabled when article is empty
⏳ **User Testing:** Pending frontend verification

**Status:** Backend complete, frontend code updated, ready for testing! 🚀
