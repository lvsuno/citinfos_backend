# Mock Data Removal - Sherbrooke Feed

## Overview
Removed mock data fallback from the PostFeed component to ensure the application only uses real database data.

## Changes Made

### 1. PostFeed Component (`src/components/PostFeed.js`)

**Removed:**
- Import of mock data functions: `getPostsByMunicipality`, `getPostsByMunicipalityAndSection`
- Fallback logic that loaded mock data when API calls failed
- Console warning about using mock data

**Updated:**
```javascript
// BEFORE
import { getPostsByMunicipality, getPostsByMunicipalityAndSection } from '../data/postsData';

try {
    // API call
} catch (err) {
    console.log('⚠️ Using mock data as fallback');
    const mockPosts = section
        ? getPostsByMunicipalityAndSection(municipalityName, section)
        : getPostsByMunicipality(municipalityName);
    setPosts(mockPosts || []);
}

// AFTER
// No mock data import

try {
    // API call
} catch (err) {
    console.error('Error fetching posts:', err);
    setError(err);
    setPosts([]); // Show empty state instead
}
```

**Behavior Now:**
- If API call succeeds → Display posts from database
- If API call fails → Display empty state with "Create first post" message
- No more fallback to mock data

### 2. MunicipalityDashboard Component (`src/pages/MunicipalityDashboard.js`)

**Added `municipalityId` prop to PostFeed:**
```javascript
// BEFORE
<PostFeed
    municipalityName={municipality.nom}
    section={getSectionDisplayName(sectionLower)}
    onCreatePostClick={onOpenPostCreationModal}
/>

// AFTER
<PostFeed
    municipalityName={municipality.nom}
    municipalityId={pageDivision?.id}  // Added division ID
    section={getSectionDisplayName(sectionLower)}
    onCreatePostClick={onOpenPostCreationModal}
/>
```

**Why This Matters:**
- The API needs the division ID to filter posts correctly
- Previously only passed municipality name (string), which wasn't being used by backend
- Now passes `pageDivision.id` which matches the database structure

## Files Still Containing Mock Data

These files still have mock data but are **NOT being used** in the app:

1. **`src/data/sherbrookePosts.js`**
   - Contains: Mock post data for Sherbrooke
   - Also exports utility functions: `formatTimeAgo`, `getTotalReactions`, `getTopReactionIcons`
   - Status: Can be kept for reference or testing, not loaded in production

2. **`src/data/postsData.js`**
   - Contains: Aggregator of all mock posts
   - Status: Not imported anywhere in active code

## Components Using Mock Data Utilities (OK)

These components import **utility functions only**, not the mock data:

1. **`src/components/PostHeader.js`**
   - Imports: `formatTimeAgo` from sherbrookePosts
   - Status: OK - just a utility function

2. **`src/components/Post.js`**
   - Imports: `getTotalReactions`, `getTopReactionIcons`, `formatTimeAgo` from sherbrookePosts
   - Status: OK - just utility functions

## Testing

### To Verify Mock Data is Gone:

1. **Check Sherbrooke Feed:**
   ```
   Visit: http://localhost:3000/municipality/sherbrooke
   ```
   - Should show real posts from database (if import script was run)
   - Should show empty state if no posts exist
   - Should NOT show the 4 mock posts (Marie Bernard, Ville de Sherbrooke, etc.)

2. **Check Browser Console:**
   - Should NOT see: `⚠️ Using mock data as fallback`
   - Should see normal API calls to `/api/content/posts/`

3. **Network Tab:**
   - Should see API call: `GET /api/content/posts/?administrative_division=XXX&ordering=-created_at&limit=50`
   - Should NOT fallback to local data

### To Populate Real Data:

Run the import script to add real posts to database:
```bash
docker compose exec backend python scripts/import_sherbrooke_posts.py
```

This will:
- Create 4 posts in Sherbrooke community
- Assign posts to `elvist` and `tite29` users (alternating)
- Add comments and reactions
- Link to AdministrativeDivision for Sherbrooke

## API Parameters

The PostFeed component now sends these parameters to the backend:

```javascript
{
  administrative_division: 123,  // Division ID (if provided)
  municipality: "Sherbrooke",    // Fallback if no ID
  section: "événements",         // Optional section filter
  ordering: "-created_at",       // Newest first
  limit: 50                      // Max posts to fetch
}
```

## Next Steps

### Optional Cleanup (Future):
1. Move utility functions (`formatTimeAgo`, etc.) from `sherbrookePosts.js` to a proper utils file
2. Delete `src/data/sherbrookePosts.js` and `src/data/postsData.js` entirely
3. Create unit tests for the utility functions

### Required for Production:
1. ✅ Remove mock data fallback (DONE)
2. ✅ Pass division ID to PostFeed (DONE)
3. ⏳ Ensure import script has been run on production database
4. ⏳ Verify all communities have proper AdministrativeDivision links

## Error Handling

**Before:** Failed API call → Load mock data → User sees fake posts
**After:** Failed API call → Show empty state → User can create first post

This is the correct behavior because:
- Users should know when the API is not working
- Empty state encourages users to create content
- No confusion between real and fake data

## Related Files

**Modified:**
- ✅ `src/components/PostFeed.js` - Removed mock fallback
- ✅ `src/pages/MunicipalityDashboard.js` - Added division ID prop

**Unchanged (Still reference mock data but not used):**
- `src/data/sherbrookePosts.js` - Mock data + utilities
- `src/data/postsData.js` - Mock data aggregator

**Import Utilities From Mock Files (OK):**
- `src/components/PostHeader.js` - Uses formatTimeAgo
- `src/components/Post.js` - Uses reaction utilities

---

**Last Updated:** October 13, 2025
**Status:** ✅ Mock data removal complete
**Impact:** Feed now only shows real database data
