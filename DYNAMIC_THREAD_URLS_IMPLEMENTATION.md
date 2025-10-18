# Dynamic Thread URLs Implementation

## Overview
All thread-related components and pages now use dynamic URLs that match the administrative division naming scheme (municipality/commune/city/etc.) instead of hardcoded `/community/` paths.

## Changes Made

### 1. **DynamicRoutes.js** ✅
Added thread-related routes to dynamic route generation:
- `/{urlPath}/:municipalitySlug/threads` - Full thread list page
- `/{urlPath}/:municipalitySlug/thread/:threadId` - Thread detail page

These routes are generated for all available URL paths (municipality, commune, city, etc.) based on country configuration.

### 2. **ThreadsPage.jsx** ✅
**Purpose:** Full page view of all threads with infinite scroll

**Changes:**
- Now uses `municipalitySlug` instead of `communityId` from URL params
- Fetches division data using `geolocationService.getDivisionBySlug()`
- Detects current URL path (`municipality`, `commune`, etc.) dynamically
- Uses dynamic URL for navigation: `/{currentUrlPath}/${municipalitySlug}/thread/${threadId}`
- Wrapped with `Layout` component for consistent UI
- One-to-one relationship: division ID = community ID

**URL Pattern:**
- Before: `/community/:communityId/threads`
- After: `/municipality/:municipalitySlug/threads` (or `/commune/...`, `/city/...`, etc.)

### 3. **ThreadDetail.jsx** ✅
**Purpose:** Display single thread with all its posts

**Changes:**
- Now uses `municipalitySlug` and `threadId` from URL params
- Added imports: `useLocation`, `Layout`, `geolocationService`, `getCountryISO3ByUrlPath`
- Fetches division data on mount using slug
- Detects current URL path dynamically
- Updated back navigation to use: `/{currentUrlPath}/${municipalitySlug}/threads`
- Wrapped entire component with `Layout`
- Removed standalone `fetchCommunity()` - community data comes from division
- Updated `InlinePostCreator` to receive `division` and `community` props

**URL Pattern:**
- Before: `/community/:communityId/thread/:threadId`
- After: `/municipality/:municipalitySlug/thread/:threadId`

### 4. **ThreadListCompact.jsx** ✅
**Purpose:** Compact thread list for Accueil sidebar (5 most recent)

**Changes:**
- Added `municipalitySlug` prop (passed from MunicipalityDashboard)
- Added `useLocation` to detect current URL path
- Updated `handleThreadClick`: `/{currentUrlPath}/${municipalitySlug}/thread/${threadId}`
- Updated `handleViewAll`: `/{currentUrlPath}/${municipalitySlug}/threads`

**Props:**
```jsx
<ThreadListCompact
  communityId={divisionId}
  municipalitySlug={municipalitySlug}
  limit={5}
/>
```

### 5. **ThreadCreatorModal.jsx** ✅
**Purpose:** Modal for creating new threads

**Changes:**
- Added `municipalitySlug` prop
- Added `useLocation` to detect current URL path
- Updated post-creation navigation: `/{currentUrlPath}/${municipalitySlug}/thread/${createdThread.id}`
- Fixed API call: changed `community` to `community_id` in threadData

**Props:**
```jsx
<ThreadCreatorModal
  isOpen={showThreadModal}
  onClose={() => setShowThreadModal(false)}
  division={division}
  section={section}
  community={community}
  municipalitySlug={municipalitySlug}
  onSubmit={handleThreadSubmit}
/>
```

### 6. **InlinePostCreator.jsx** ✅
**Purpose:** Inline post/thread creator component

**Changes:**
- Added `municipalitySlug` prop (optional)
- Passes `municipalitySlug` to `ThreadCreatorModal`
- Implemented real API call for thread creation (was mock before)
- Calls `socialAPI.threads.create()` in `handleThreadSubmit`

**Props:**
```jsx
<InlinePostCreator
  division={pageDivision}
  section={section}
  community={community}
  municipalitySlug={municipalitySlug}
  threadId={threadId}
  onPostCreated={handlePostCreated}
  placeholder="Quoi de neuf ?"
/>
```

### 7. **MunicipalityDashboard.js** ✅
**Changes:**
- Passes `municipalitySlug` to `ThreadListCompact` in Accueil section
- Passes `municipalitySlug` to `InlinePostCreator` in other sections

## URL Patterns Summary

| Component | Old URL | New URL |
|-----------|---------|---------|
| **ThreadsPage** | `/community/:communityId/threads` | `/:urlPath/:municipalitySlug/threads` |
| **ThreadDetail** | `/community/:communityId/thread/:threadId` | `/:urlPath/:municipalitySlug/thread/:threadId` |
| **ThreadListCompact navigation** | `/community/:communityId/thread/:id` | `/:urlPath/:municipalitySlug/thread/:id` |
| **ThreadCreatorModal navigation** | `/community/:communityId/thread/:id` | `/:urlPath/:municipalitySlug/thread/:id` |

Where `:urlPath` is one of: `municipality`, `commune`, `city`, `ville`, `municipio`, etc. (based on country configuration)

## API Integration

### Backend Endpoints (unchanged)
- `GET /communities/api/threads/?community_id={id}` - List threads
- `GET /communities/api/threads/{slug}/` - Get thread
- `POST /communities/api/threads/` - Create thread
- `GET /communities/api/threads/{slug}/posts/` - Get thread posts

### Frontend API Calls
```javascript
// List threads
socialAPI.threads.list(communityId)

// Get thread
socialAPI.threads.get(threadId)

// Create thread
socialAPI.threads.create({
  community_id: community.id,  // ⚠️ Must be community_id, not community
  title: "Thread Title",
  body: "Description",
  first_post_content: "Optional first post",
  first_post_type: "text"
})

// Get thread posts
socialAPI.threads.posts(threadId)
```

## Division-Community Relationship

**Important:** There's a one-to-one relationship between administrative divisions and communities:
- Each division has exactly one community
- Division ID = Community ID
- When we fetch division data, we use its ID as the community ID

```javascript
// Example from ThreadsPage.jsx
const divisionData = await geolocationService.getDivisionBySlug(municipalitySlug, countryISO3);
setCommunity({ id: divisionData.id, name: divisionData.name });
```

## Navigation Flow

### Creating a Thread
1. User clicks "Nouveau Sujet" button in `ThreadsPage` or opens thread modal in `InlinePostCreator`
2. `ThreadCreatorModal` opens
3. User fills title, description, optional first post
4. Modal calls `onSubmit(threadData)` → `socialAPI.threads.create()`
5. Backend returns created thread with `id`
6. Modal navigates to: `/{currentUrlPath}/${municipalitySlug}/thread/{createdThread.id}`

### Viewing Threads
1. **Accueil page:** `ThreadListCompact` shows 5 most recent threads
   - Click thread → Navigate to thread detail
   - Click "Voir tous les sujets" → Navigate to ThreadsPage

2. **ThreadsPage:** Shows all threads with infinite scroll
   - Click thread → Navigate to thread detail
   - Click "Retour" → Navigate back to Accueil

3. **ThreadDetail:** Shows thread and all posts
   - Click "Retour" → Navigate to ThreadsPage
   - Breadcrumb navigation available

## Testing Checklist

- [x] ThreadListCompact appears on Accueil page
- [ ] Click thread in ThreadListCompact → Opens ThreadDetail with correct URL
- [ ] Click "Voir tous les sujets" → Opens ThreadsPage with correct URL
- [ ] ThreadsPage shows all threads
- [ ] Infinite scroll works on ThreadsPage
- [ ] Click thread in ThreadsPage → Opens ThreadDetail
- [ ] ThreadDetail displays thread title, body, posts
- [ ] Can create post in ThreadDetail
- [ ] Click "Retour" in ThreadDetail → Goes back to ThreadsPage
- [ ] Create new thread from ThreadsPage → Navigates to new thread
- [ ] Create new thread from InlinePostCreator → Navigates to new thread
- [ ] All URLs follow pattern: `/municipality/sherbrooke/thread/123` (not `/community/uuid/...`)
- [ ] Works for different URL paths (commune, city, etc.)

## Error Fixes

### 1. ✅ "sherbrooke is not a valid UUID"
**Problem:** ThreadCreatorModal was passing `community` instead of `community_id`
**Solution:** Changed to `community_id: community?.id` in API call

### 2. ✅ Thread creation not connecting to backend
**Problem:** `handleThreadSubmit` in InlinePostCreator was just a mock
**Solution:** Implemented real `socialAPI.threads.create()` call

### 3. ✅ Navigation using wrong URL format
**Problem:** Components were hardcoded to use `/community/:id/...`
**Solution:** Updated all components to use dynamic URL pattern detection

## Architecture Benefits

1. **Consistency:** All pages use the same URL structure
2. **Localization:** URLs match the administrative division terminology of each country
3. **SEO:** Friendly URLs with division slugs instead of UUIDs
4. **Maintainability:** Single source of truth for URL patterns in `DynamicRoutes.js`
5. **Scalability:** Easy to add new countries with different division types

## Files Modified

- ✅ `src/components/DynamicRoutes.js` - Added thread routes
- ✅ `src/pages/ThreadsPage.jsx` - Dynamic URL support
- ✅ `src/components/social/ThreadDetail.jsx` - Dynamic URL support
- ✅ `src/components/social/ThreadListCompact.jsx` - Dynamic navigation
- ✅ `src/components/modals/ThreadCreatorModal.jsx` - Dynamic navigation + API fix
- ✅ `src/components/InlinePostCreator.jsx` - Real API call + pass municipalitySlug
- ✅ `src/pages/MunicipalityDashboard.js` - Pass municipalitySlug to components

## Next Steps

1. Test thread creation flow end-to-end
2. Test navigation between all thread-related pages
3. Verify URLs are correct for different countries (Canada, Benin, etc.)
4. Add thread edit functionality (currently just console.log in ThreadList)
5. Consider adding thread search/filter functionality to ThreadsPage

---

**Date:** October 17, 2025
**Status:** ✅ Implementation Complete - Ready for Testing
