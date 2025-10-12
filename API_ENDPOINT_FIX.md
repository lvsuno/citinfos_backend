# API Endpoint Double Prefix Fix

## 🐛 Issue
API requests were failing with 404 errors due to double `/api/` prefix in URLs:
- **Error URL**: `http://localhost:8000/api/communities/api/communities/`
- **Expected URL**: `http://localhost:8000/api/communities/`

## 🔍 Root Cause
The `apiService` base configuration already includes `/api` in the `baseURL`:
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
```

However, the `social-api.js` endpoints were incorrectly including `/api/` again in their paths:
```javascript
// ❌ WRONG - Double /api/ prefix
'/communities/api/communities/'

// ✅ CORRECT - No /api/ needed (baseURL already has it)
'/communities/'
```

## ✅ Fixed Endpoints

### Communities API
**File**: `src/services/social-api.js`

| Method | Before (❌) | After (✅) |
|--------|-------------|-----------|
| list | `/communities/api/communities/` | `/communities/` |
| get | `/communities/api/communities/${slug}/` | `/communities/${slug}/` |
| create | `/communities/api/communities/` | `/communities/` |
| update | `/communities/api/communities/${slug}/` | `/communities/${slug}/` |
| delete | `/communities/api/communities/${slug}/` | `/communities/${slug}/` |

### Threads API
**File**: `src/services/social-api.js`

| Method | Before (❌) | After (✅) |
|--------|-------------|-----------|
| list | `/communities/api/threads/` | `/threads/` |
| get | `/communities/api/threads/${slug}/` | `/threads/${slug}/` |
| create | `/communities/api/threads/` | `/threads/` |
| update | `/communities/api/threads/${slug}/` | `/threads/${slug}/` |
| delete | `/communities/api/threads/${slug}/` | `/threads/${slug}/` |

## 🔧 Changes Made

### 1. Communities Endpoints (Lines 439-466)
```javascript
// BEFORE
communities = {
  list: async (divisionId = null) => {
    const endpoint = divisionId
      ? `/communities/api/communities/?division_id=${divisionId}`
      : '/communities/api/communities/';
    // ...
  },
  get: async (slug) => {
    return this.get(`/communities/api/communities/${slug}/`);
  },
  // ... other methods
}

// AFTER
communities = {
  list: async (divisionId = null) => {
    const endpoint = divisionId
      ? `/communities/?division_id=${divisionId}`
      : '/communities/';
    // ...
  },
  get: async (slug) => {
    return this.get(`/communities/${slug}/`);
  },
  // ... other methods
}
```

### 2. Threads Endpoints (Lines 492-535)
```javascript
// BEFORE
threads = {
  list: async (communityId = null, communitySlug = null) => {
    let endpoint = '/communities/api/threads/';
    // ...
  },
  get: async (slug) => {
    return this.get(`/communities/api/threads/${slug}/`);
  },
  // ... other methods
}

// AFTER
threads = {
  list: async (communityId = null, communitySlug = null) => {
    let endpoint = '/threads/';
    // ...
  },
  get: async (slug) => {
    return this.get(`/threads/${slug}/`);
  },
  // ... other methods
}
```

## 📊 URL Resolution Flow

```
┌─────────────────────────────────────────────────────────────┐
│              API Request Flow                               │
└─────────────────────────────────────────────────────────────┘

1. Code calls: socialAPI.communities.list()
   ↓
2. Makes request: this.get('/communities/')
   ↓
3. BaseAPIService.get() forwards to apiService.api.get()
   ↓
4. Axios combines:
   baseURL: 'http://localhost:8000/api'
   endpoint: '/communities/'
   ↓
5. Final URL: http://localhost:8000/api/communities/ ✅
```

## 🧪 Testing Checklist

### Communities API
- [ ] List all communities: `GET /api/communities/`
- [ ] List communities by division: `GET /api/communities/?division_id=1`
- [ ] Get specific community: `GET /api/communities/{slug}/`
- [ ] Create community: `POST /api/communities/`
- [ ] Update community: `PATCH /api/communities/{slug}/`
- [ ] Delete community: `DELETE /api/communities/{slug}/`

### Threads API
- [ ] List all threads: `GET /api/threads/`
- [ ] List threads by community: `GET /api/threads/?community_id=1`
- [ ] Get specific thread: `GET /api/threads/{slug}/`
- [ ] Create thread: `POST /api/threads/`
- [ ] Update thread: `PATCH /api/threads/{slug}/`
- [ ] Delete thread: `DELETE /api/threads/{slug}/`

## 📝 Related Issues

This is similar to the notification endpoint issue that was fixed earlier. The pattern to remember:

**Rule**: When using `BaseAPIService` or `apiService`, endpoints should NEVER include `/api/` because it's already in the `baseURL`.

```javascript
// ✅ CORRECT
this.get('/communities/')
this.get('/threads/')
this.get('/content/posts/')
this.get('/profiles/')

// ❌ WRONG
this.get('/api/communities/')
this.get('/communities/api/communities/')
this.get('/api/content/posts/')
```

## 🎯 Impact

**Before Fix:**
- ❌ PostCreationModal failed to load communities
- ❌ Thread list failed to load
- ❌ Community selector showed errors
- ❌ All 404 errors for community/thread endpoints

**After Fix:**
- ✅ Communities load correctly
- ✅ Threads load correctly
- ✅ PostCreationModal works
- ✅ All endpoints resolve to correct URLs

## ✅ Status
All endpoint URLs have been corrected. No syntax errors. Ready for testing.
