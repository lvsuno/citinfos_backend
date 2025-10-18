# Post Display Architecture - Complete Guide

## Overview

The system supports multiple post types with a unified attachment system. Here's how posts are displayed from backend to frontend.

---

## Backend Architecture

### 1. Post Model (`content/models.py`)

```python
class Post(models.Model):
    POST_TYPES = [
        ('article', 'Article'),    # Rich text with embedded media
        ('image', 'Image'),        # Single/multiple images
        ('video', 'Video'),        # Single/multiple videos
        ('audio', 'Audio'),        # Audio files
        ('file', 'File'),          # Document files
        ('link', 'Link'),          # Link preview
        ('poll', 'Poll'),          # Poll(s)
        ('mixed', 'Mixed Media'),  # Multiple types
        # Repost types...
    ]

    content = TextField()       # Main text content
    post_type = CharField()     # One of POST_TYPES
    # ... other fields
```

### 2. PostMedia Model (`content/models.py`)

```python
class PostMedia(models.Model):
    """Attachments for posts - can be uploaded files OR external URLs"""

    post = ForeignKey(Post, related_name='media')
    media_type = CharField([
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'File')
    ])

    # EITHER file OR external_url (not both)
    file = FileField(upload_to=..., blank=True, null=True)
    external_url = URLField(blank=True, null=True)

    description = CharField()  # Caption/label for the media
    order = PositiveIntegerField()  # Display order

    @property
    def media_url(self):
        """Returns external_url if set, otherwise file.url"""
        if self.external_url:
            return self.external_url
        elif self.file:
            return self.file.url
        return None
```

### 3. Poll Model (`polls/models.py`)

```python
class Poll(models.Model):
    """Polls attached to posts"""

    post = ForeignKey(Post, related_name='polls')
    question = CharField()
    allow_multiple = BooleanField()
    expires_at = DateTimeField()
    # ... other fields

class PollOption(models.Model):
    poll = ForeignKey(Poll, related_name='options')
    text = CharField()
    image = ImageField(blank=True)
    order = PositiveIntegerField()
    votes_count = PositiveIntegerField()
```

### 4. Unified Serializer (`content/unified_serializers.py`)

```python
class UnifiedPostSerializer(serializers.ModelSerializer):
    """Returns complete post with all attachments"""

    # ATTACHMENTS (PostMedia)
    attachments = EnhancedPostMediaSerializer(
        source='media',  # Django relation: Post.media
        many=True,
        read_only=True
    )
    attachment_count = serializers.ReadOnlyField()
    has_attachments = serializers.ReadOnlyField()
    attachments_by_type = serializers.SerializerMethodField()

    # POLLS
    polls = EnhancedPollSerializer(many=True, read_only=True)
    polls_count = serializers.ReadOnlyField()
    has_polls = serializers.ReadOnlyField()

    # ... other fields
```

### 5. API Response Structure

```json
{
  "id": "uuid",
  "author_username": "marie.bernard",
  "author_name": "Marie Bernard",
  "content": "Check out this sunset! 🌅 #beautiful",
  "post_type": "article",

  "attachments": [
    {
      "id": "uuid",
      "media_type": "image",
      "file_url": "http://localhost:8000/media/posts/image.jpg",
      "external_url": "https://images.unsplash.com/photo-123",
      "description": "Sunset over the lake",
      "order": 0,
      "thumbnail_url": "http://localhost:8000/media/thumbnails/image_thumb.jpg"
    }
  ],
  "attachment_count": 1,
  "has_attachments": true,
  "attachments_by_type": {
    "image": [...],
    "video": [...]
  },

  "polls": [
    {
      "id": "uuid",
      "question": "What's your favorite season?",
      "allow_multiple": false,
      "expires_at": "2025-10-20T12:00:00Z",
      "options": [
        {
          "id": "uuid",
          "text": "Summer",
          "votes_count": 42,
          "vote_percentage": 35.0,
          "user_has_voted": false
        }
      ]
    }
  ],
  "polls_count": 1,
  "has_polls": true,

  "likes_count": 24,
  "comments_count": 5,
  "created_at": "2025-10-14T10:30:00Z"
}
```

---

## Frontend Architecture

### Current Implementation

**File: `src/components/Post.js`**

```javascript
const Post = ({ post }) => {
  return (
    <article className={styles.post}>
      <PostHeader author={post.author} timestamp={post.timestamp} />

      {/* Text content */}
      <PostContent content={post.content} />

      {/* Media attachments */}
      <PostAttachments attachments={post.attachments} />

      {/* Reactions, comments, etc. */}
    </article>
  );
};
```

**File: `src/components/PostAttachments.js`**

```javascript
const PostAttachments = ({ attachments }) => {
  // Currently displays attachments in a grid
  // Supports images and videos

  return (
    <div className={styles.attachments}>
      {attachments.map(attachment => (
        <img src={attachment.url} alt={attachment.alt} />
        // OR
        <video src={attachment.url} controls />
      ))}
    </div>
  );
};
```

---

## How Different Post Types Should Be Displayed

### 1. **Article Posts** (`post_type: 'article'`)

**Characteristics:**
- Rich HTML content from TipTap editor
- **Media is EMBEDDED within the HTML content**, not in separate `attachments` array
- Media appears exactly where user placed it during editing
- HTML contains `data-media-id` attributes to track media position

**How It Works - TipTap Editor Placeholders:**

When user creates article with embedded media:

1. **During Editing:** User drops image/video into editor at cursor position
   ```html
   <p>Check this out!</p>
   <img src="blob:http://localhost:3000/abc123"
        data-media-id="uuid-123"
        data-media-type="image"
        alt="sunset.jpg" />
   <p>More text here...</p>
   ```

2. **On Submit (3-Phase Upload):**
   - **Phase 1:** Create post with blob URLs (temporary)
   - **Phase 2:** Upload media files, get server URLs
   - **Phase 3:** Replace blob URLs with server URLs, update post

3. **Final Stored Content:**
   ```html
   <p>Check this out!</p>
   <img src="https://server.com/media/posts/sunset.jpg"
        alt="sunset.jpg"
        class="max-w-full h-auto rounded-lg" />
   <p>More text here...</p>
   ```

**Display Strategy:**

```javascript
// Articles use HTML content directly - media is ALREADY embedded
<PostContent
  htmlContent={post.content}  // Contains <img>, <video>, <audio> tags
  renderAsHTML={true}  // Render as HTML, not plain text
/>

// NO separate attachments for embedded media
// post.attachments will be empty for articles with embedded media
```

**Example Structure:**
```
┌─────────────────────────────────┐
│ Author Header                   │
├─────────────────────────────────┤
│ Article HTML Content            │
│                                 │
│ Lorem ipsum dolor sit amet...   │
│                                 │
│ <img src="..." /> ← EMBEDDED    │
│                                 │
│ More text content here...       │
│                                 │
│ <video src="..." /> ← EMBEDDED  │
│                                 │
│ Final paragraph text.           │
├─────────────────────────────────┤
│ Reactions | Comments | Share    │
└─────────────────────────────────┘
```

**IMPORTANT:**
- Articles do NOT use `post.attachments` for embedded media
- All media is in the HTML `post.content` field
- Must render as HTML to display media inline
- `data-media-id` attributes may still be present (safe to ignore when rendering)

### 2. **Media Posts** (`post_type: 'image'/'video'/'audio'`)

**Characteristics:**
- Focused on visual/audio content
- Brief caption/text
- Media is the primary content
- Each media item can have a label/description

**Display Strategy:**

```javascript
// Text caption (if any)
{post.content && <PostCaption content={post.content} />}

// Featured media display
<FeaturedMediaDisplay attachments={post.attachments} />
```

**Example Structure:**
```
┌─────────────────────────────────┐
│ Author Header                   │
├─────────────────────────────────┤
│ "Check out these photos! 📸"    │
├─────────────────────────────────┤
│ ┌─────────┬─────────┐           │
│ │ Photo 1 │ Photo 2 │           │
│ │ Label 1 │ Label 2 │           │
│ └─────────┴─────────┘           │
│ ┌─────────┬─────────┐           │
│ │ Photo 3 │ Photo 4 │           │
│ │ Label 3 │ Label 4 │           │
│ └─────────┴─────────┘           │
├─────────────────────────────────┤
│ Reactions | Comments | Share    │
└─────────────────────────────────┘
```

### 3. **Poll Posts** (`post_type: 'poll'`)

**Characteristics:**
- Question with multiple choice options
- Options may have images
- Shows vote percentages and counts
- Can have multiple polls in one post

**Display Strategy:**

```javascript
<PostContent content={post.content} />

{post.polls.map(poll => (
  <PollWidget
    poll={poll}
    onVote={handleVote}
    userHasVoted={poll.user_has_voted}
  />
))}
```

**Example Structure:**
```
┌─────────────────────────────────┐
│ Author Header                   │
├─────────────────────────────────┤
│ "What's your favorite season?"  │
├─────────────────────────────────┤
│ Poll expires in: 5 days         │
│                                 │
│ ○ Summer          (35%) ██████  │
│ ○ Winter          (25%) ████    │
│ ○ Spring          (20%) ███     │
│ ○ Fall            (20%) ███     │
│                                 │
│ 120 votes total                 │
├─────────────────────────────────┤
│ Reactions | Comments | Share    │
└─────────────────────────────────┘
```

### 4. **Mixed Posts** (`post_type: 'mixed'`)

**Characteristics:**
- Combines multiple media types
- Article content + images + videos + polls
- Most complex display case

**Display Strategy:**

```javascript
<PostContent content={post.content} />

{/* Group attachments by type */}
{post.attachments_by_type.image && (
  <ImageGallery images={post.attachments_by_type.image} />
)}

{post.attachments_by_type.video && (
  <VideoPlayer videos={post.attachments_by_type.video} />
)}

{post.polls && post.polls.map(poll => (
  <PollWidget poll={poll} />
))}
```

---

## Recommended Component Architecture

### New Component Structure

```
src/components/posts/
├── Post.js                    # Main post container - routes by post_type
├── PostHeader.js              # Author, timestamp, menu
├── ArticleContent.js          # NEW: Renders HTML with embedded media
├── PostContent.js             # Plain text formatter (for captions, etc.)
├── PostAttachments/
│   ├── index.js               # Smart attachment router
│   ├── ImageGallery.js        # Multi-image display with labels
│   ├── VideoPlayer.js         # Video with controls
│   ├── AudioPlayer.js         # Audio with waveform
│   ├── FileAttachment.js      # Document download
│   └── AttachmentLabel.js     # Media descriptions/captions
├── PostPoll/
│   ├── PollWidget.js          # Poll display & voting
│   ├── PollOption.js          # Individual option
│   └── PollResults.js         # Results visualization
└── PostActions.js             # Like, comment, share buttons
```

### Smart Attachment Display Component

```javascript
// src/components/posts/PostAttachments/index.js
import { getMediaUrl } from '../../../utils/mediaUtils';

const PostAttachments = ({ attachments, postType, showLabels = false }) => {
  if (!attachments || attachments.length === 0) return null;

  // Group by media type
  const grouped = attachments.reduce((acc, att) => {
    acc[att.media_type] = acc[att.media_type] || [];
    acc[att.media_type].push(att);
    return acc;
  }, {});

  return (
    <div className={styles.attachments}>
      {/* Images */}
      {grouped.image && (
        <ImageGallery
          images={grouped.image}
          showLabels={showLabels}
        />
      )}

      {/* Videos */}
      {grouped.video && grouped.video.map(video => (
        <VideoPlayer
          key={video.id}
          src={getMediaUrl(video.file_url || video.external_url)}
          label={showLabels ? video.description : null}
        />
      ))}

      {/* Audio */}
      {grouped.audio && grouped.audio.map(audio => (
        <AudioPlayer
          key={audio.id}
          src={getMediaUrl(audio.file_url || audio.external_url)}
          label={showLabels ? audio.description : null}
        />
      ))}

      {/* Files */}
      {grouped.file && grouped.file.map(file => (
        <FileAttachment
          key={file.id}
          file={file}
        />
      ))}
    </div>
  );
};
```

### Post Type Handler

```javascript
// src/components/posts/Post.js
const Post = ({ post }) => {
  const renderPostContent = () => {
    switch (post.post_type) {
      case 'article':
        // Articles: HTML content with EMBEDDED media (not attachments array)
        return (
          <ArticleContent
            htmlContent={post.content}  // Contains <img>, <video>, <audio> tags
          />
        );

      case 'image':
      case 'video':
      case 'audio':
        // Media posts: Use attachments array with labels
        return (
          <>
            {post.content && <PostCaption content={post.content} />}
            <PostAttachments
              attachments={post.attachments}
              postType={post.post_type}
              showLabels={true}  // Show description field as labels
            />
          </>
        );

      case 'poll':
        return (
          <>
            <PostContent content={post.content} />
            {post.polls && post.polls.map(poll => (
              <PollWidget key={poll.id} poll={poll} />
            ))}
          </>
        );

      case 'mixed':
        // Mixed: HTML content + attachments array + polls
        return (
          <>
            {post.content && (
              <ArticleContent htmlContent={post.content} />
            )}
            {post.attachments && post.attachments.length > 0 && (
              <PostAttachments
                attachments={post.attachments}
                showLabels={true}
              />
            )}
            {post.polls && post.polls.map(poll => (
              <PollWidget key={poll.id} poll={poll} />
            ))}
          </>
        );

      default:
        return <PostContent content={post.content} />;
    }
  };

  return (
    <article className={styles.post}>
      <PostHeader
        author={post.author}
        timestamp={post.created_at}
        section={post.community_name}
      />

      {renderPostContent()}

      <PostActions
        post={post}
        onLike={handleLike}
        onComment={handleComment}
        onShare={handleShare}
      />

      {showComments && (
        <PostComments comments={post.comments} />
      )}
    </article>
  );
};
```

---

## Article HTML Rendering Component

### ArticleContent Component (NEW - REQUIRED)

```javascript
// src/components/posts/ArticleContent.js
import React from 'react';
import { getMediaUrl } from '../../utils/mediaUtils';
import styles from './ArticleContent.module.css';

/**
 * Renders article HTML content with embedded media
 * Handles <img>, <video>, <audio> tags from TipTap editor
 */
const ArticleContent = ({ htmlContent }) => {
  if (!htmlContent) return null;

  // Process HTML to ensure media URLs are absolute
  const processedHTML = React.useMemo(() => {
    let processed = htmlContent;

    // Find all <img> tags and ensure absolute URLs
    processed = processed.replace(
      /<img([^>]*)\ssrc=["']([^"']+)["']/gi,
      (match, attrs, src) => {
        const absoluteUrl = getMediaUrl(src);
        return `<img${attrs} src="${absoluteUrl}"`;
      }
    );

    // Find all <video> tags and ensure absolute URLs
    processed = processed.replace(
      /<video([^>]*)\ssrc=["']([^"']+)["']/gi,
      (match, attrs, src) => {
        const absoluteUrl = getMediaUrl(src);
        return `<video${attrs} src="${absoluteUrl}"`;
      }
    );

    // Find all <source> tags (inside video/audio) and ensure absolute URLs
    processed = processed.replace(
      /<source([^>]*)\ssrc=["']([^"']+)["']/gi,
      (match, attrs, src) => {
        const absoluteUrl = getMediaUrl(src);
        return `<source${attrs} src="${absoluteUrl}"`;
      }
    );

    // Find all <audio> tags and ensure absolute URLs
    processed = processed.replace(
      /<audio([^>]*)\ssrc=["']([^"']+)["']/gi,
      (match, attrs, src) => {
        const absoluteUrl = getMediaUrl(src);
        return `<audio${attrs} src="${absoluteUrl}"`;
      }
    );

    // Clean up data-media-id attributes (no longer needed for display)
    processed = processed.replace(/\s*data-media-id=["'][^"']*["']/gi, '');
    processed = processed.replace(/\s*data-media-type=["'][^"']*["']/gi, '');

    return processed;
  }, [htmlContent]);

  return (
    <div
      className={styles.articleContent}
      dangerouslySetInnerHTML={{ __html: processedHTML }}
    />
  );
};

export default ArticleContent;
```

### CSS for ArticleContent

```css
/* src/components/posts/ArticleContent.module.css */
.articleContent {
  font-size: 1rem;
  line-height: 1.6;
  color: #1f2937;
  word-wrap: break-word;
}

/* Paragraphs */
.articleContent p {
  margin: 0.75rem 0;
}

/* Headings */
.articleContent h1,
.articleContent h2,
.articleContent h3 {
  margin: 1.5rem 0 0.75rem;
  font-weight: 600;
  color: #111827;
}

/* Lists */
.articleContent ul,
.articleContent ol {
  margin: 0.75rem 0;
  padding-left: 1.5rem;
}

/* Embedded Images */
.articleContent img {
  max-width: 100%;
  height: auto;
  border-radius: 0.5rem;
  margin: 1rem 0;
  display: block;
}

/* Embedded Videos */
.articleContent video {
  max-width: 100%;
  height: auto;
  border-radius: 0.5rem;
  margin: 1rem 0;
  display: block;
}

/* Embedded Audio */
.articleContent audio {
  width: 100%;
  max-width: 500px;
  margin: 1rem 0;
  display: block;
}

/* Links */
.articleContent a {
  color: #3b82f6;
  text-decoration: underline;
}

/* Code blocks */
.articleContent pre {
  background: #f3f4f6;
  padding: 1rem;
  border-radius: 0.375rem;
  overflow-x: auto;
  margin: 1rem 0;
}

.articleContent code {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
}

/* Blockquotes */
.articleContent blockquote {
  border-left: 4px solid #3b82f6;
  padding-left: 1rem;
  margin: 1rem 0;
  color: #6b7280;
  font-style: italic;
}

/* Tables */
.articleContent table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.articleContent th,
.articleContent td {
  border: 1px solid #e5e7eb;
  padding: 0.5rem;
  text-align: left;
}

.articleContent th {
  background: #f9fafb;
  font-weight: 600;
}
```

---

## Media URL Handling

**Always use the `getMediaUrl` utility:**

```javascript
import { getMediaUrl } from '../utils/mediaUtils';

// For attachments from API
const imageUrl = getMediaUrl(attachment.file_url || attachment.external_url);

// The utility handles:
// 1. External URLs (Unsplash, etc.) → returns as-is
// 2. Local files → prepends server URL
// 3. Blob URLs → returns as-is
```

---

## Summary

### Post Types & Display Logic

| Post Type | Content Field | Media Location | Display Component | Labels/Captions |
|-----------|--------------|----------------|-------------------|-----------------|
| `article` | HTML with embedded media | Inside `content` HTML | `ArticleContent` | N/A (embedded) |
| `image` | Caption text | `attachments` array | `ImageGallery` | ✓ `attachment.description` |
| `video` | Caption text | `attachments` array | `VideoPlayer` | ✓ `attachment.description` |
| `audio` | Caption text | `attachments` array | `AudioPlayer` | ✓ `attachment.description` |
| `poll` | Question text | N/A | `PollWidget` | N/A |
| `mixed` | HTML + caption | Both `content` & `attachments` | `ArticleContent` + attachments | ✓ `attachment.description` |

### Key Backend Fields

- `post.post_type` - Determines display strategy
- `post.content` - **For articles: HTML with `<img>`, `<video>`, `<audio>` tags**
- `post.attachments` - Array of PostMedia objects (for media/mixed posts)
- `post.polls` - Array of Poll objects
- `attachment.media_type` - 'image', 'video', 'audio', 'file'
- `attachment.description` - Caption/label for media in attachments array
- `attachment.file_url` or `attachment.external_url` - Media URL

### Critical Understanding

**Articles vs Media Posts:**

1. **Article Posts (`post_type: 'article'`)**
   - Media is **INSIDE the HTML** in `post.content` field
   - `post.attachments` is **empty** (no separate attachment array)
   - Media appears exactly where user placed it in the editor
   - Render using `dangerouslySetInnerHTML` with HTML processing
   - Example: `<p>Text</p><img src="..." /><p>More text</p>`

2. **Media Posts (`post_type: 'image'/'video'/'audio'`)**
   - Media is in `post.attachments` array
   - `post.content` contains brief caption text
   - Display attachments in gallery/player with labels from `attachment.description`
   - Example: `{ content: "Check this out!", attachments: [{media_type: 'image', description: 'Sunset', ...}] }`

3. **Imported Sherbrooke Posts**
   - Currently stored as `post_type: 'article'`
   - Have external media URLs in `PostMedia` records
   - BUT: Content HTML may not reference them (needs investigation)
   - May need to convert to proper article HTML or change to media posts

### Implementation Steps

1. ✅ Create `mediaUtils.js` utility (DONE)
2. **Create `ArticleContent.js` component** - Renders HTML with embedded media
3. Update `PostAttachments` to handle media types and show labels
4. Create `ImageGallery` component with labels
5. Create `VideoPlayer` component
6. Create `PollWidget` component
7. Update `Post.js` to route by `post_type`
8. **Check Sherbrooke posts** - Verify content HTML structure
9. Test with imported Sherbrooke posts

---

## Current Status

✅ Backend: Posts with media imported (4 posts with 6 attachments)
✅ Frontend: `mediaUtils.js` created
✅ Understanding: Complete TipTap placeholder system documented
⏳ **NEXT CRITICAL STEP:** Check how Sherbrooke posts were stored (HTML content vs attachments)
⏳ Next: Create `ArticleContent` component for HTML rendering
⏳ Next: Update `PostAttachments` to display media with labels
⏳ Next: Create poll display components
