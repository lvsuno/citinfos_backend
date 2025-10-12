# Corrected Post Architecture & Implementation

**Date:** October 9, 2025
**Status:** ✅ CORRECTED & IMPLEMENTED

---

## Backend Architecture (Correct Understanding)

### Post Structure

Every post has:
- `content` (TextField, max 2000 chars) - Can store HTML, text, or be blank
- `post_type` (CharField) - Defines the primary type
- `visibility` (CharField) - Public, followers, private, community
- **Optional Relations:**
  - `attachments` (PostMedia) - Many-to-many for embedded/attached media
  - `polls` (Poll) - Many-to-many for attached polls

### Three Post Types (Tabs)

#### 1. **Article Post** (`post_type: 'text'`)
- `content` = HTML string from RichTextEditor
- Can have embedded media (images, videos, audio) via `attachments`
- Embedded media shows inline in the HTML content
- Uses two-phase upload for embedded media

**Example API Request:**
```json
{
  "content": "<p>Check out this photo!</p><img src='https://server.com/media/photo.jpg' />",
  "post_type": "text",
  "visibility": "public"
}
```

---

#### 2. **Poll Post** (`post_type: 'poll'`)
- `content` = Question or optional description (can be blank)
- Must have `polls` array attached
- Poll options are stored separately in PollOption model

**Example API Request:**
```json
{
  "content": "What's your favorite color?",
  "post_type": "poll",
  "visibility": "public",
  "polls": [{
    "question": "What's your favorite color?",
    "options": [
      {"text": "Red", "order": 1},
      {"text": "Blue", "order": 2},
      {"text": "Green", "order": 3}
    ],
    "multiple_choice": false,
    "anonymous_voting": false,
    "expires_at": "2025-10-10T12:00:00Z"
  }]
}
```

---

#### 3. **Media Post** (`post_type: 'image'|'video'|'audio'|'file'`)
- `content` = Optional global description/caption
- Must have `attachments` array
- `post_type` determined by first media item type
- Each attachment can have individual description

**Example API Request:**
```json
{
  "content": "My vacation photos",
  "post_type": "image",
  "visibility": "public",
  "attachments": [
    {
      "media_type": "image",
      "file": <File>,
      "description": "Beach sunset",
      "order": 1
    },
    {
      "media_type": "image",
      "file": <File>,
      "description": "Mountain view",
      "order": 2
    }
  ]
}
```

---

## Frontend Modal Architecture

### Tab System (Radio Buttons - One Active at a Time)

```
┌─────────────────────────────────────────┐
│  [Article] [Poll] [Media]              │  ← Radio selection
├─────────────────────────────────────────┤
│                                         │
│  Tab Content (only one visible)        │
│                                         │
│  Article: RichTextEditor (HTML)        │
│  Poll: Question + Options inputs       │
│  Media: File upload + descriptions     │
│                                         │
└─────────────────────────────────────────┘
```

### Data Flow

1. **User selects ONE tab** (article, poll, or media)
2. **User fills content** for that specific type
3. **User clicks "Publish"**
4. **Frontend transforms** modal data to API format
5. **Backend creates** ONE post of that type

**Never mixed:** You cannot create a post with article + poll + media together. Each tab creates a separate post type.

---

## Implementation Details

### Transformation Layer

File: `src/utils/postTransformers.js`

**Transforms modal data (frontend) → API data (backend)**

```javascript
// Modal format (frontend UI)
const modalData = {
  type: 'article',  // or 'poll' or 'media'
  content: {
    article: "<p>HTML content</p>",
    poll: { question, options, ... },
    media: [{ file, type, description }]
  },
  visibility: 'public'
};

// API format (backend)
const apiData = transformPostDataForAPI(modalData);
// Returns:
{
  content: "<p>HTML content</p>",  // Simple string
  post_type: 'text',
  visibility: 'public'
}
```

### Type-Specific Transformers

#### `transformArticlePostForAPI()`
```javascript
{
  content: modalData.content.article,  // HTML string
  post_type: 'text',
  visibility: modalData.visibility
}
```

#### `transformPollPostForAPI()`
```javascript
{
  content: poll.question,
  post_type: 'poll',
  visibility: modalData.visibility,
  polls: [{
    question: poll.question,
    options: [...],
    multiple_choice: poll.allowMultiple,
    expires_at: calculatedDateTime
  }]
}
```

#### `transformMediaPostForAPI()`
```javascript
{
  content: globalDescription || '',
  post_type: firstMediaType,  // 'image', 'video', 'audio', 'file'
  visibility: modalData.visibility,
  attachments: media.map(item => ({
    media_type: item.type,
    file: item.file,
    description: item.description,
    order: index + 1
  }))
}
```

---

## Article Post with Embedded Media (Special Case)

### Three-Phase Upload Process

Only applies to **Article posts** with embedded images/videos/audio.

#### Phase 1: Create Post with Placeholders
```javascript
// Post content contains blob URLs (temporary)
{
  content: "<p>Check this out</p><img src='blob:http://localhost:3000/abc123' />",
  post_type: 'text',
  visibility: 'public'
}
```

**Backend creates post** → Returns `post.id`

---

#### Phase 2: Upload Media Files
```javascript
const { processedContent } = await processContentForSubmission(async (file, mediaType) => {
  // Upload each embedded media file
  const serverUrl = await onImageUpload(file);
  return serverUrl;  // Returns: "https://server.com/media/image.jpg"
});

// processedContent now has real URLs:
// "<p>Check this out</p><img src='https://server.com/media/image.jpg' />"
```

**Media files uploaded** → Get server URLs → Replace in HTML

---

#### Phase 3: Update Post with Final Content
```javascript
await contentAPI.updatePost(post.id, {
  content: processedContent  // HTML with real server URLs
});
```

**Post content updated** → Final version saved

---

## Updated PostCreationModal Implementation

### Key Changes

1. ✅ **Import transformer:**
   ```javascript
   import { transformPostDataForAPI, transformArticleUpdateForAPI } from '../utils/postTransformers';
   ```

2. ✅ **Build modal data (frontend structure):**
   ```javascript
   const modalData = {
     type: activeType,
     content: {
       article: activeType === 'article' ? articleContent : null,
       poll: activeType === 'poll' ? { ... } : null,
       media: activeType === 'media' ? [...] : null
     },
     visibility
   };
   ```

3. ✅ **Transform before submit:**
   ```javascript
   const apiPost = transformPostDataForAPI(modalData);
   await onSubmit(apiPost);
   ```

4. ✅ **Special handling for article with embedded media:**
   ```javascript
   if (activeType === 'article' && embeddedMedia.length > 0) {
     // Three-phase upload
     const apiPost = transformPostDataForAPI(modalData);
     const createdPost = await onSubmit(apiPost);  // Phase 1
     const { processedContent } = await processContentForSubmission(...);  // Phase 2
     await contentAPI.updatePost(createdPost.id,
       transformArticleUpdateForAPI(processedContent)  // Phase 3
     );
   }
   ```

---

## Backend Serializer Flow

### UnifiedPostCreateUpdateSerializer

**Handles all three types:**

```python
class UnifiedPostCreateUpdateSerializer(serializers.ModelSerializer):
    attachments = EnhancedPostMediaSerializer(source='media', many=True, required=False)
    polls = PollCreateSerializer(many=True, required=False)

    class Meta:
        fields = ['content', 'post_type', 'visibility', 'attachments', 'polls']

    def create(self, validated_data):
        attachments_data = validated_data.pop('media', [])
        polls_data = validated_data.pop('polls', [])

        # Create post
        post = Post.objects.create(**validated_data)

        # Create attachments if provided
        for i, attachment_data in enumerate(attachments_data):
            PostMedia.objects.create(post=post, order=i+1, **attachment_data)

        # Create polls if provided
        for i, poll_data in enumerate(polls_data):
            Poll.objects.create(post=post, order=i+1, **poll_data)

        return post
```

**Key Points:**
- `content` goes directly to Post.content (TextField)
- `attachments` creates PostMedia records
- `polls` creates Poll records
- All optional - only create what's provided

---

## Content Field Usage by Type

| Post Type | `content` Field Contains | Additional Relations |
|-----------|-------------------------|---------------------|
| Article (`text`) | HTML string from editor | Optional: `attachments` (embedded media) |
| Poll (`poll`) | Question or description | Required: `polls` array |
| Media (`image/video/etc.`) | Optional global description | Required: `attachments` array |

### Important Notes:

1. **HTML is allowed in `content`** - TextField can store HTML strings
2. **Max length: 2000 characters** - Frontend should validate
3. **Can be blank** - Content is optional for some post types
4. **No special processing** - Backend stores HTML as-is

---

## Testing Checklist

### Article Post Tests
- [ ] Create article with plain text
- [ ] Create article with HTML formatting
- [ ] Create article with embedded image (3-phase upload)
- [ ] Create article with multiple embedded images
- [ ] Verify blob URLs replaced with server URLs
- [ ] Check database: content has HTML with real URLs

### Poll Post Tests
- [ ] Create poll with 2 options
- [ ] Create poll with multiple choice enabled
- [ ] Create poll with custom expiration
- [ ] Verify poll options created in database
- [ ] Check post.content has question

### Media Post Tests
- [ ] Upload single image
- [ ] Upload multiple images
- [ ] Upload video
- [ ] Add individual descriptions to each media
- [ ] Add global description
- [ ] Verify post_type matches first media type
- [ ] Check attachments in database

---

## API Endpoint Reference

### Create Post
```
POST /api/content/posts/
Content-Type: application/json

Body: {
  "content": "string",
  "post_type": "text|poll|image|video|audio|file",
  "visibility": "public|followers|private",
  "attachments": [...],  // Optional
  "polls": [...]         // Optional
}
```

### Update Post
```
PATCH /api/content/posts/{id}/
Content-Type: application/json

Body: {
  "content": "updated HTML string"
}
```

### Add Attachment (Alternative)
```
POST /api/content/posts/{id}/add_attachment/
Content-Type: multipart/form-data

Body: FormData with file
```

---

## Summary

✅ **Backend correctly implements:**
- Single `content` field (TextField) for HTML/text
- Separate relations for `attachments` and `polls`
- Unified serializer handles all three types

✅ **Frontend now correctly:**
- Transforms modal data to API format
- Sends `content` as simple string (not nested object)
- Uses correct field names (`post_type` not `type`)
- Handles three-phase upload for article embedded media
- Creates ONE post type at a time (never mixed)

✅ **No backend changes needed** - it was already correct!

The issue was only in the frontend data transformation layer, which is now fixed with `postTransformers.js`.

