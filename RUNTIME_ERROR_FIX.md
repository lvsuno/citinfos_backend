# Runtime Error Fix - "section is not defined"

**Date:** October 16, 2025
**Error:** `Uncaught ReferenceError: section is not defined` in PostFeed component

---

## Problem

After updating PostFeed to use `rubrique` prop instead of `section`, there were still references to the old `section` variable in the code:

1. Line 155: `const sectionText = section ? ...` ❌
2. Line 162: Using `{sectionText}` in empty state message ❌
3. Missing `rubrique` prop in accueil case ❌

---

## Solution

### Fix 1: Updated Empty State Message in PostFeed.js

**Before (Line 155-162):**
```javascript
const sectionText = section ? ` dans la section "${section}"` : '';
return (
    <div className={styles.emptyState}>
        ...
        <p>Soyez le premier à partager quelque chose d'intéressant{sectionText} à <strong>{municipalityName}</strong> !</p>
    </div>
);
```

**After:**
```javascript
const rubriqueText = rubrique ? ` dans la rubrique "${rubrique}"` : '';
return (
    <div className={styles.emptyState}>
        ...
        <p>Soyez le premier à partager quelque chose d'intéressant{rubriqueText} à <strong>{municipalityName}</strong> !</p>
    </div>
);
```

### Fix 2: Added rubrique Prop for Accueil Case in MunicipalityDashboard.js

**Before (Line 403-408):**
```javascript
<PostFeed
    municipalityName={divisionName}
    municipalityId={pageDivision?.id}
    onCreatePostClick={onOpenPostCreationModal}
/>
```

**After:**
```javascript
<PostFeed
    municipalityName={divisionName}
    municipalityId={pageDivision?.id}
    rubrique="accueil"  // ✅ Added - shows all posts
    onCreatePostClick={onOpenPostCreationModal}
/>
```

---

## Verification

Checked that all references to `section` have been removed:
```bash
grep "section" src/components/PostFeed.js
# Result: No matches found ✅
```

---

## Files Modified

1. ✅ `src/components/PostFeed.js` - Changed `section` to `rubrique` in empty state (line 155)
2. ✅ `src/pages/MunicipalityDashboard.js` - Added `rubrique="accueil"` prop (line 405)

---

## Testing

The webpack dev server should have automatically reloaded. Please verify:

- [ ] Navigate to `/sherbrooke/accueil` - Should show all 8 posts
- [ ] Navigate to `/sherbrooke/actualites` - Should show 8 posts
- [ ] Navigate to `/sherbrooke/evenements` - Should show "Aucune publication pour le moment" message
- [ ] Empty state message should say "dans la rubrique evenements" not "dans la section"
- [ ] No console errors about undefined variables

---

## Status

✅ **Fixed** - All references to `section` removed, `rubrique` prop properly passed in all cases
