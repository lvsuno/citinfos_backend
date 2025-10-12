# Frontend-Backend Inconsistency Report

**Date:** October 9, 2025
**Status:** 🔴 CRITICAL ISSUES FOUND

---

## Executive Summary

The current implementation has **significant inconsistencies** between frontend and backend data structures. The article media implementation will **NOT work** without fixing these issues.

---

## Critical Issues

### ❌ Issue #1: Content Field Structure Mismatch

**Frontend sends:**
```javascript
{
  type: 'article',  // ← Wrong field name
  content: {        // ← Wrong structure (nested object)
    article: "<p>HTML content</p>",
    poll: null,
    media: null
  }
}
```

**Backend expects:**
```python
{
  post_type: 'text',  // ← Correct field name
  content: "<p>HTML content</p>",  // ← Simple TextField string
  polls: [...],       // ← Separate field
  attachments: [...]  // ← Separate field (via PostMedia)
}
```

**Impact:** 🔴 **BREAKING**
- Posts cannot be created with current frontend code
- Backend will reject the request or store incorrectly
- Article media feature completely broken

---

### ❌ Issue #2: Post Type Field Name

**Frontend:**
```javascript
type: 'article'  // Using 'type'
```

**Backend:**
```python
post_type = models.CharField(...)  # Expects 'post_type'
```

**Impact:** 🔴 **BREAKING**
- Post type won't be set correctly
- May default to 'text' or cause validation error

---

### ❌ Issue #3: Post Type Values Don't Match

**Frontend sends:**
- `'article'` for rich text posts
- `'media'` for media-only posts
- `'poll'` for polls

**Backend expects:**
```python
POST_TYPES = [
    ('text', 'Text'),      # ← Should use 'text' not 'article'
    ('image', 'Image'),
    ('video', 'Video'),
    ('audio', 'Audio'),
    ('file', 'File'),
    ('link', 'Link'),
    ('poll', 'Poll'),      # ← This matches
    ('repost', 'Simple Repost'),
    ('repost_with_media', 'Repost + Media'),
    ('repost_quote', 'Quote Repost'),
    ('repost_remix', 'Remix Repost'),
    ('mixed', 'Mixed Media'),
]
```

**Impact:** 🟡 **MODERATE**
- `'article'` is not a valid post_type choice
- Should use `'text'` instead
- `'media'` is not valid either (should use 'image', 'video', etc.)

---

### ❌ Issue #4: Poll Structure Mismatch

**Frontend sends:**
```javascript
{
  content: {
    poll: {
      question: "Question?",
      options: ["Option 1", "Option 2"],  // ← Simple strings
      allowMultiple: false,                // ← Wrong field name
      expirationHours: 24                  // ← Wrong format
    }
  }
}
```

**Backend expects:**
```python
{
  polls: [{  # ← Separate field, array of poll objects
    question: "Question?",
    options: [
      {"text": "Option 1", "order": 0},  # ← Objects with text and order
      {"text": "Option 2", "order": 1}
    ],
    multiple_choice: False,              # ← Correct field name
    expires_at: "2025-10-10T10:00:00Z"   # ← ISO datetime string
  }]
}
```

**Impact:** 🔴 **BREAKING**
- Polls cannot be created
- Data structure completely incompatible

---

### ❌ Issue #5: Media/Attachments Structure Mismatch

**Frontend sends (media posts):**
```javascript
{
  content: {
    media: [
      {
        file: File,
        type: 'image',
        name: 'photo.jpg',
        description: 'My photo'
      }
    ]
  }
}
```

**Backend expects:**
```python
{
  attachments: [  # ← Different field name
    {
      media_type: 'image',  # ← Not 'type'
      file: <uploaded file>,
      description: 'My photo',
      order: 1  # ← Requires order field
    }
  ]
}
```

**Impact:** 🔴 **BREAKING**
- Media posts cannot be created
- Files won't upload correctly

---

### ❌ Issue #6: Update Endpoint Data Structure

**Frontend Phase 3 sends:**
```javascript
await contentAPI.updatePost(postId, {
  content: {           // ← Nested object
    article: processedContent
  }
});
```

**Backend expects:**
```python
{
  content: processedContent  # ← Simple string, not nested
}
```

**Impact:** 🔴 **BREAKING**
- Phase 3 update will fail
- Article media URLs won't be persisted
- Posts stuck with blob URLs

---

## How It Currently Works (Incorrectly)

The `handlePostCreation` function in Dashboard.jsx does transformation:

```javascript
const handlePostCreation = async (postData) => {
  const apiPost = {
    visibility: postData.visibility,
    customAudience: postData.customAudience,
  };

  // Transform article type
  if (postData.type === 'article' && postData.content.article) {
    apiPost.content = postData.content.article;  // ✅ Extract string
    apiPost.post_type = 'text';                  // ✅ Correct type
  }

  // Transform poll type
  if (postData.type === 'poll' && postData.content.poll) {
    const poll = postData.content.poll;
    apiPost.polls = [{  // ✅ Creates polls array
      question: poll.question,
      options: poll.options.map((text, index) => ({ text, order: index })),
      multiple_choice: poll.allowMultiple,  // ✅ Correct field name
      expires_at: new Date(Date.now() + poll.expirationHours * 60 * 60 * 1000).toISOString()
    }];
    apiPost.post_type = 'poll';
  }

  // Transform media type
  if (postData.type === 'media' && postData.content.media) {
    apiPost.attachments = postData.content.media;  // ✅ Creates attachments array
    apiPost.post_type = 'media';  // ❌ Still wrong, should be 'image'/'video'/etc.
  }

  await addLocalPost(apiPost);
};
```

**Problem:** This transformation only exists in Dashboard.jsx, NOT in PostCreationModal.jsx!

---

## Required Fixes

### Fix #1: Add Transformation Layer to PostCreationModal

**Location:** `src/components/PostCreationModal.jsx`, line ~168

**Before:**
```javascript
const postData = {
  type: activeType,
  content: {
    article: activeType === 'article' ? articleContent : null,
    poll: activeType === 'poll' ? {...} : null,
    media: activeType === 'media' ? [...] : null
  },
  visibility,
  customAudience: visibility === 'custom' ? customAudience : null
};

await onSubmit(postData);  // ❌ Wrong format
```

**After:**
```javascript
// Build modal-format data
const modalData = {
  type: activeType,
  content: {
    article: activeType === 'article' ? articleContent : null,
    poll: activeType === 'poll' ? {...} : null,
    media: activeType === 'media' ? [...] : null
  },
  visibility,
  customAudience: visibility === 'custom' ? customAudience : null
};

// Transform to API format
const apiPost = transformPostDataForAPI(modalData);

await onSubmit(apiPost);  // ✅ Correct format
```

---

### Fix #2: Create Transformation Function

**Location:** `src/utils/postTransformers.js` (NEW FILE)

```javascript
/**
 * Transform post data from modal format to API format
 */
export const transformPostDataForAPI = (modalData) => {
  const apiPost = {
    visibility: modalData.visibility,
    custom_audience: modalData.customAudience,
  };

  // Handle article posts
  if (modalData.type === 'article' && modalData.content.article) {
    apiPost.content = modalData.content.article;
    apiPost.post_type = 'text';
  }

  // Handle poll posts
  if (modalData.type === 'poll' && modalData.content.poll) {
    const poll = modalData.content.poll;
    apiPost.content = poll.question;  // Set question as content
    apiPost.post_type = 'poll';
    apiPost.polls = [{
      question: poll.question,
      options: poll.options.map((text, index) => ({ text, order: index })),
      multiple_choice: poll.allowMultiple,
      anonymous_voting: poll.anonymousVoting || false,
      expires_at: new Date(
        Date.now() + poll.expirationHours * 60 * 60 * 1000
      ).toISOString()
    }];
  }

  // Handle media posts
  if (modalData.type === 'media' && modalData.content.media?.length > 0) {
    const media = modalData.content.media;

    // Determine post_type based on first media item
    const firstMediaType = media[0].type;
    apiPost.post_type = firstMediaType === 'file' ? 'file' : firstMediaType;

    // Set global description as content
    apiPost.content = modalData.content.media[0].description || '';

    // Create attachments array
    apiPost.attachments = media.map((item, index) => ({
      media_type: item.type,
      file: item.file,
      description: item.description || '',
      order: index + 1
    }));
  }

  return apiPost;
};

/**
 * Transform update data for Phase 3
 */
export const transformArticleUpdateForAPI = (processedContent) => {
  return {
    content: processedContent  // Simple string, not nested
  };
};
```

---

### Fix #3: Update PostCreationModal to Use Transformer

**Location:** `src/components/PostCreationModal.jsx`

**Add import:**
```javascript
import { transformPostDataForAPI, transformArticleUpdateForAPI } from '../utils/postTransformers';
```

**Update handleSubmit:**
```javascript
const handleSubmit = async (e) => {
  e.preventDefault();
  if (!validateForm()) return;

  setIsSubmitting(true);

  try {
    // Build modal-format data
    const modalData = {
      type: activeType,
      content: {
        article: activeType === 'article' ? articleContent : null,
        poll: activeType === 'poll' ? {
          question: pollQuestion,
          options: pollOptions.filter(opt => opt.trim()),
          allowMultiple: allowMultipleVotes,
          expirationHours: pollExpirationHours
        } : null,
        media: activeType === 'media' ? attachedMedia.map(item => ({
          ...item,
          description: item.description || ''
        })) : null
      },
      visibility,
      customAudience: visibility === 'custom' ? customAudience : null
    };

    // Special handling for articles with embedded media
    if (activeType === 'article' && richTextEditorRef.current) {
      const { processContentForSubmission, getMediaAttachments } = richTextEditorRef.current;
      const embeddedMedia = getMediaAttachments();

      if (embeddedMedia && embeddedMedia.length > 0) {
        // Phase 1: Transform and create post
        const apiPost = transformPostDataForAPI(modalData);
        const createdPost = await onSubmit(apiPost);

        // Phase 2: Upload media
        const { processedContent } = await processContentForSubmission(async (file, mediaType) => {
          if (mediaType === 'image' && onImageUpload) {
            return await onImageUpload(file);
          } else if (mediaType === 'video' && onVideoUpload) {
            return await onVideoUpload(file);
          } else if (mediaType === 'audio' && onAudioUpload) {
            return await onAudioUpload(file);
          }
          throw new Error(`No upload handler for media type: ${mediaType}`);
        });

        // Phase 3: Update with correct format
        if (createdPost && createdPost.id && processedContent !== articleContent) {
          const updateData = transformArticleUpdateForAPI(processedContent);
          await contentAPI.updatePost(createdPost.id, updateData);
          console.log('✅ Article updated with final media URLs. Post ID:', createdPost.id);
        }

        handleClose();
        return;
      }
    }

    // Standard submission with transformation
    const apiPost = transformPostDataForAPI(modalData);
    await onSubmit(apiPost);
    handleClose();

  } catch (error) {
    setErrors({ submit: error.message || 'Échec de la création de la publication' });
  } finally {
    setIsSubmitting(false);
  }
};
```

---

### Fix #4: Update contentAPI.updatePost Call

**Current (Wrong):**
```javascript
await contentAPI.updatePost(createdPost.id, {
  content: {
    article: processedContent  // ❌ Nested object
  }
});
```

**Fixed:**
```javascript
await contentAPI.updatePost(createdPost.id, {
  content: processedContent  // ✅ Simple string
});
```

---

## Backend Verification

### Check if Backend Serializer Handles Nested Content

Let me verify if the serializer can handle the current structure...

**Current Serializer:** `UnifiedPostCreateUpdateSerializer`

```python
class Meta:
    model = Post
    fields = [
        'id', 'community', 'content', 'post_type', 'visibility',
        'link_image', 'attachments', 'polls', 'is_pinned'
    ]
```

**Fields mapping:**
- ✅ `content` → `Post.content` (TextField)
- ✅ `post_type` → `Post.post_type` (CharField)
- ✅ `visibility` → `Post.visibility` (CharField)
- ✅ `attachments` → `Post.media` (source='media')
- ✅ `polls` → `Post.polls` (Many-to-Many)

**Verdict:** Backend expects flat structure, NOT nested `content: { article, poll, media }`

---

## Testing Checklist

After implementing fixes:

- [ ] Test article post creation without media
- [ ] Test article post creation with embedded image
- [ ] Test article post update (Phase 3)
- [ ] Verify post content is saved correctly
- [ ] Test poll creation
- [ ] Verify poll options are created
- [ ] Test media post creation
- [ ] Verify attachments are saved
- [ ] Check database to confirm correct structure
- [ ] Test visibility settings
- [ ] Test custom audience

---

## Migration Path

### Option A: Fix Frontend (Recommended)
1. Create `postTransformers.js` utility
2. Update `PostCreationModal.jsx` to use transformer
3. Update Phase 3 to send flat content
4. Test all post types

**Pros:**
- Backend stays unchanged
- Consistent with existing API
- No database migrations needed

**Cons:**
- Need to update frontend code

---

### Option B: Fix Backend (Not Recommended)
1. Create custom serializer field for nested content
2. Parse `content.article`, `content.poll`, `content.media`
3. Update all views to handle nested structure

**Pros:**
- Frontend stays unchanged

**Cons:**
- Changes stable backend API
- Requires more complex serializer logic
- May break other clients
- Inconsistent with REST best practices

---

## Recommended Action Plan

1. **IMMEDIATE (30 min):**
   - Create `src/utils/postTransformers.js`
   - Implement `transformPostDataForAPI()`
   - Implement `transformArticleUpdateForAPI()`

2. **UPDATE POSTCREATIONMODAL (15 min):**
   - Import transformers
   - Update `handleSubmit` to transform data
   - Fix Phase 3 update call

3. **TESTING (30 min):**
   - Test each post type (article, poll, media)
   - Verify database entries
   - Test article with embedded media

4. **DOCUMENTATION (15 min):**
   - Update implementation guides
   - Document transformation layer
   - Add JSDoc comments

**Total Time:** ~90 minutes

---

## Conclusion

**Current Status:** 🔴 **IMPLEMENTATION BROKEN**

The article media feature cannot work without fixing the data structure mismatch. The frontend is sending nested `content: { article, poll, media }` but backend expects flat structure with `content` as string and separate `polls`/`attachments` fields.

**Required Action:** Implement transformation layer BEFORE testing the article media feature.

**Priority:** CRITICAL - blocks all post creation functionality

