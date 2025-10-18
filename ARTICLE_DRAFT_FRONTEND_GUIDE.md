# Article Draft Functionality - Frontend Implementation Guide

## Backend Implementation ✅

### Post Model Changes

**New Field Added:**
```python
title = models.CharField(
    max_length=300,
    blank=True,
    help_text="Title for article posts (required for post_type='article')"
)
```

**Existing Fields for Articles:**
```python
post_type = 'article'  # Post type
is_draft = models.BooleanField(default=False)  # Draft status
title = models.CharField(max_length=300, blank=True)  # NEW!
article_content = models.TextField(blank=True, null=True)  # Rich HTML
featured_image = models.ImageField(...)  # Cover image
excerpt = models.TextField(max_length=500, blank=True)  # Summary
```

### Backend Validations ✅

**For Published Articles** (`is_draft=False`):
```python
# Both title and article_content are REQUIRED
if not title or not title.strip():
    raise ValidationError("Article posts require a title. Save as draft if incomplete.")

if not article_content or not article_content.strip():
    raise ValidationError("Article posts require content. Save as draft if incomplete.")
```

**For Draft Articles** (`is_draft=True`):
```python
# No validation - can be empty
# Allows users to save incomplete articles
```

---

## Frontend Implementation Required 🎯

### 1. Article Editor UI Components

```jsx
// Example structure for article editor
<ArticleEditor>
  {/* Title Input */}
  <Input
    placeholder="Article Title"
    value={title}
    onChange={(e) => setTitle(e.target.value)}
    maxLength={300}
    required
  />

  {/* TipTap Rich Editor */}
  <TipTapEditor
    content={articleContent}
    onChange={setArticleContent}
    placeholder="Write your article..."
  />

  {/* Featured Image Upload */}
  <ImageUpload
    onUpload={setFeaturedImage}
    label="Featured Image (optional)"
  />

  {/* Excerpt */}
  <Textarea
    placeholder="Short excerpt (optional)"
    value={excerpt}
    onChange={(e) => setExcerpt(e.target.value)}
    maxLength={500}
  />

  {/* Action Buttons */}
  <ButtonGroup>
    <Button
      onClick={handleSaveDraft}
      disabled={isEmpty()}  // ⭐ DISABLE WHEN EMPTY
      variant="secondary"
    >
      Save as Draft
    </Button>

    <Button
      onClick={handlePublish}
      disabled={!isValid()}  // ⭐ DISABLE WHEN INVALID
      variant="primary"
    >
      Publish
    </Button>
  </ButtonGroup>
</ArticleEditor>
```

### 2. Validation Logic

```javascript
// Check if article is completely empty
const isEmpty = () => {
  const hasTitle = title && title.trim().length > 0;
  const hasContent = articleContent && stripHtml(articleContent).trim().length > 0;
  const hasImage = featuredImage !== null;

  // Empty if no title, no content, and no image
  return !hasTitle && !hasContent && !hasImage;
};

// Check if article is valid for publishing
const isValid = () => {
  const hasTitle = title && title.trim().length > 0;
  const hasContent = articleContent && stripHtml(articleContent).trim().length > 0;

  // Valid only if both title and content exist
  return hasTitle && hasContent;
};

// Strip HTML tags to get plain text
const stripHtml = (html) => {
  const div = document.createElement('div');
  div.innerHTML = html;
  return div.textContent || div.innerText || '';
};
```

### 3. Button States

| State | Title | Content | Featured Image | Save Draft Button | Publish Button |
|-------|-------|---------|----------------|-------------------|----------------|
| **Completely Empty** | ❌ | ❌ | ❌ | 🔒 **Disabled** | 🔒 **Disabled** |
| **Only Title** | ✅ | ❌ | ❌ | ✅ Enabled | 🔒 Disabled |
| **Only Content** | ❌ | ✅ | ❌ | ✅ Enabled | 🔒 Disabled |
| **Only Image** | ❌ | ❌ | ✅ | ✅ Enabled | 🔒 Disabled |
| **Title + Content** | ✅ | ✅ | ❌ | ✅ Enabled | ✅ **Enabled** |
| **Complete Article** | ✅ | ✅ | ✅ | ✅ Enabled | ✅ Enabled |

### 4. API Calls

```javascript
// Save as draft
const handleSaveDraft = async () => {
  if (isEmpty()) {
    // Should never reach here if button is disabled
    console.error('Cannot save empty draft');
    return;
  }

  try {
    const response = await api.post('/api/posts/', {
      post_type: 'article',
      is_draft: true,  // ⭐ DRAFT FLAG
      title: title,
      article_content: articleContent,
      featured_image: featuredImage,
      excerpt: excerpt,
      community: communityId,
      rubrique_template: rubriqueId,
      visibility: 'public'
    });

    showNotification('Draft saved successfully!');
  } catch (error) {
    showError(error.message);
  }
};

// Publish article
const handlePublish = async () => {
  if (!isValid()) {
    showError('Please add both title and content before publishing');
    return;
  }

  try {
    const response = await api.post('/api/posts/', {
      post_type: 'article',
      is_draft: false,  // ⭐ PUBLISHED
      title: title,
      article_content: articleContent,
      featured_image: featuredImage,
      excerpt: excerpt,
      community: communityId,
      rubrique_template: rubriqueId,
      visibility: 'public'
    });

    showNotification('Article published successfully!');
    navigate(`/posts/${response.data.id}`);
  } catch (error) {
    showError(error.message);
  }
};
```

### 5. User Experience Flow

```
User Opens Article Editor
           ↓
   [ Empty Editor ]
           ↓
   Both buttons DISABLED ❌
           ↓
User Types Title or Content
           ↓
   "Save Draft" ENABLED ✅
   "Publish" still DISABLED ❌
           ↓
User Adds Both Title AND Content
           ↓
   Both buttons ENABLED ✅
           ↓
User Clicks "Publish"
           ↓
   Backend validates → Success!
   Article visible to community
```

### 6. Error Handling

```javascript
// Backend validation errors
const handleApiError = (error) => {
  if (error.response?.data) {
    const errors = error.response.data;

    if (errors.title) {
      setTitleError(errors.title);
    }

    if (errors.article_content) {
      setContentError(errors.article_content);
    }

    // Show global error message
    showError('Please fix the errors and try again');
  }
};
```

### 7. Draft Management

```javascript
// List user's drafts
const fetchDrafts = async () => {
  const response = await api.get('/api/posts/', {
    params: {
      is_draft: true,
      author: currentUserId
    }
  });

  setDrafts(response.data.results);
};

// Edit existing draft
const editDraft = (draftId) => {
  navigate(`/articles/edit/${draftId}`);
};

// Publish existing draft
const publishDraft = async (draftId) => {
  await api.patch(`/api/posts/${draftId}/`, {
    is_draft: false
  });

  showNotification('Draft published!');
};

// Delete draft
const deleteDraft = async (draftId) => {
  await api.delete(`/api/posts/${draftId}/`);
  showNotification('Draft deleted');
};
```

---

## UX Best Practices 📝

### Button States

✅ **DO:**
- Disable "Save Draft" when article is **completely empty**
- Disable "Publish" when **title OR content** is missing
- Show helpful tooltips on disabled buttons
- Provide real-time validation feedback

❌ **DON'T:**
- Ask "Save as draft?" when article is empty
- Show confusing error messages
- Let users save completely empty drafts
- Allow publishing incomplete articles

### Visual Feedback

```jsx
// Example with tooltips
<Tooltip
  content={isEmpty() ? "Add some content before saving" : "Save draft"}
>
  <Button
    onClick={handleSaveDraft}
    disabled={isEmpty()}
  >
    Save as Draft
  </Button>
</Tooltip>

<Tooltip
  content={!isValid() ? "Add title and content to publish" : "Publish article"}
>
  <Button
    onClick={handlePublish}
    disabled={!isValid()}
    variant="primary"
  >
    Publish
  </Button>
</Tooltip>
```

### Autosave (Optional Enhancement)

```javascript
// Autosave draft every 30 seconds (only if not empty)
useEffect(() => {
  const interval = setInterval(() => {
    if (!isEmpty() && hasChanges()) {
      handleSaveDraft();
    }
  }, 30000); // 30 seconds

  return () => clearInterval(interval);
}, [title, articleContent, featuredImage]);
```

---

## API Endpoints 📡

### Create Post (Article)
```
POST /api/posts/
```

**Request Body:**
```json
{
  "post_type": "article",
  "is_draft": false,
  "title": "My Amazing Article",
  "article_content": "<p>Rich HTML content...</p>",
  "featured_image": "base64_or_file",
  "excerpt": "Short summary",
  "community": "uuid",
  "rubrique_template": "uuid",
  "visibility": "public"
}
```

**Success Response (201):**
```json
{
  "id": "uuid",
  "post_type": "article",
  "is_draft": false,
  "title": "My Amazing Article",
  "article_content": "<p>Rich HTML content...</p>",
  "featured_image": "url",
  "excerpt": "Short summary",
  "author": {...},
  "community": {...},
  "rubrique_template": {...},
  "created_at": "2025-10-16T12:00:00Z",
  "likes_count": 0,
  "comments_count": 0
}
```

**Error Response (400):**
```json
{
  "title": ["Article posts require a title. Save as draft if incomplete."],
  "article_content": ["Article posts require content. Save as draft if incomplete."]
}
```

### Update Draft
```
PATCH /api/posts/{id}/
```

**Request Body:**
```json
{
  "is_draft": false  // Publish the draft
}
```

---

## Testing Checklist ✅

### Functional Tests

- [ ] Empty article → Both buttons disabled
- [ ] Title only → Save Draft enabled, Publish disabled
- [ ] Content only → Save Draft enabled, Publish disabled
- [ ] Title + Content → Both buttons enabled
- [ ] Save draft → Success, shows in drafts list
- [ ] Publish article → Success, visible in community
- [ ] Edit draft → Can modify and republish
- [ ] Delete draft → Removed from list
- [ ] Autosave (if implemented) → Works every 30s

### Edge Cases

- [ ] Very long title (300 chars) → Accepted
- [ ] Title > 300 chars → Truncated or error
- [ ] Only whitespace in title → Treated as empty
- [ ] Only whitespace in content → Treated as empty
- [ ] Upload large image → Validation/compression
- [ ] Network error during save → Proper error message
- [ ] Concurrent edits → Conflict resolution

### UX Tests

- [ ] Button tooltips show correct messages
- [ ] Validation errors are clear and helpful
- [ ] Success notifications appear
- [ ] Loading states during API calls
- [ ] Responsive design on mobile
- [ ] Keyboard shortcuts work (Ctrl+S for save)

---

## Summary

**Backend:** ✅ Complete
- `title` field added
- Validation for published articles
- Drafts can be empty

**Frontend:** 🎯 To Implement
- Disable "Save Draft" when completely empty
- Disable "Publish" when title or content missing
- Show validation feedback
- Implement draft management UI

**Key Rule:**
> **No empty drafts!** Users must add at least something (title, content, or image) before saving a draft.

---

## Questions?

If you need any clarification or additional backend support, let me know!
