# Backend Post Restructuring Plan - PREFERRED SOLUTION

## Current Understanding

### What We Have Now
- **Regular Posts**: `content` field (plain text) + optional `attachments` array
- **Problem**: The imported "article" posts are actually just regular posts with attachments
- **Need**: True rich articles with embedded media vs regular posts with separate attachments

### User Requirements

1. **Regular Posts** (image, video, audio, poll, etc.)
   - `content` field: **Basic HTML** (bold, italic, links, emoji) - SHORT captions
   - `attachments` array: Separate media files with descriptions
   - Example: "Check this out! 😍 **Amazing sunset**" + [image attachment]

2. **Rich Articles** (article post_type)
   - `article_content` field: **Full HTML** from TipTap editor with EMBEDDED media
   - `content` field: Basic summary/excerpt (optional)
   - Example: `<h1>Title</h1><p>Intro...</p><img src="..." /><p>More content...</p>`

---

## Proposed Solution: Add `article_content` Field

### Why This Approach?

✅ **All posts get basic HTML** - `content` field supports bold, italic, emoji everywhere
✅ **Clear separation** - `article_content` is ONLY for rich articles with embedded media
✅ **Backwards compatible** - Existing posts keep working
✅ **Simple logic** - If `article_content` exists and not empty → render as rich article

---

## Database Schema Changes

### Migration: Add `article_content` Field

```python
# content/migrations/00XX_add_article_content_field.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('content', '00XX_previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='article_content',
            field=models.TextField(
                blank=True,
                null=True,
                help_text="Rich HTML content for article posts with embedded media from TipTap editor"
            ),
        ),
    ]
```

### Updated Post Model

```python
# content/models.py

class Post(models.Model):
    """Main post model."""
    POST_TYPES = [
        ('article', 'Article'),      # Rich article with embedded media
        ('image', 'Image'),          # Image post with attachments
        ('video', 'Video'),          # Video post with attachments
        ('audio', 'Audio'),          # Audio post with attachments
        ('file', 'File'),            # File post with attachments
        ('link', 'Link'),            # Link post
        ('poll', 'Poll'),            # Poll post
        ('repost', 'Simple Repost'),
        ('repost_with_media', 'Repost + Media'),
        ('repost_quote', 'Quote Repost'),
        ('repost_remix', 'Remix Repost'),
        ('mixed', 'Mixed Media'),
    ]

    # ... existing fields ...

    # Basic HTML content for ALL posts (captions, descriptions, poll questions)
    # Supports: <b>, <i>, <strong>, <em>, <a>, emoji, line breaks
    # Used by: ALL post types for captions/descriptions
    content = models.TextField(
        max_length=2000,
        blank=True,
        help_text="Basic HTML for post captions/descriptions (supports bold, italic, links, emoji)"
    )

    # Rich HTML content for ARTICLE posts ONLY
    # Supports: Full TipTap editor with embedded <img>, <video>, <audio>
    # Used by: ONLY 'article' post_type when user creates rich articles
    article_content = models.TextField(
        blank=True,
        null=True,
        help_text="Rich HTML content for article posts with embedded media (TipTap editor output)"
    )

    post_type = models.CharField(
        max_length=20,
        choices=POST_TYPES,
        default='text'
    )

    # ... rest of fields ...

    def save(self, *args, **kwargs):
        """Auto-generate excerpt for articles."""
        # If article has rich content but no summary, generate one
        if self.post_type == 'article' and self.article_content and not self.content:
            import re
            # Strip HTML tags to get plain text
            text = re.sub('<[^<]+?>', '', self.article_content)
            # Take first 200 characters as excerpt
            self.content = text[:200].strip() + '...' if len(text) > 200 else text.strip()

        super().save(*args, **kwargs)
```

---

## Post Type Definitions with Examples

### 1. Article Post (`post_type: 'article'`)

**Purpose:** Long-form content with embedded media

**Fields Used:**
- `article_content` ✅ **PRIMARY** - Full rich HTML from TipTap editor
- `content` ✅ (optional) - Auto-generated excerpt OR custom summary
- `attachments` ❌ Empty (media is embedded in `article_content`)

**Example:**
```json
{
  "post_type": "article",
  "content": "Découverte du lac des Nations - Un joyau au cœur de Sherbrooke...",
  "article_content": "<h1>Découverte du lac des Nations</h1><p>Un joyau au cœur de Sherbrooke...</p><img src='https://server.com/media/lake1.jpg' alt='Lac' /><p>Le lac des Nations...</p><img src='https://server.com/media/lake2.jpg' /><h2>Histoire</h2><p>...</p>",
  "attachments": []
}
```

**Display:**
- Render `article_content` as HTML with embedded media
- `content` is just for excerpts/previews (feed view, notifications, etc.)

---

### 2. Image Post (`post_type: 'image'`)

**Purpose:** Share images with caption

**Fields Used:**
- `content` ✅ **PRIMARY** - Caption with basic HTML (bold, italic, emoji)
- `attachments` ✅ - Image files with descriptions
- `article_content` ❌ Null

**Example:**
```json
{
  "post_type": "image",
  "content": "Magnifique coucher de soleil ! 🌅 <strong>Incroyable</strong>",
  "article_content": null,
  "attachments": [
    {
      "media_type": "image",
      "external_url": "https://images.unsplash.com/...",
      "description": "Coucher de soleil sur le lac",
      "order": 0
    }
  ]
}
```

**Display:**
- Show `content` as caption (render basic HTML: bold, italic, links)
- Show `attachments` as image gallery with descriptions as labels

---

### 3. Video Post (`post_type: 'video'`)

**Fields Used:**
- `content` ✅ - Caption with basic HTML
- `attachments` ✅ - Video files
- `article_content` ❌ Null

---

### 4. Poll Post (`post_type: 'poll'`)

**Fields Used:**
- `content` ✅ - Poll description/context with basic HTML
- `polls` ✅ - Poll questions and options
- `article_content` ❌ Null
- `attachments` ❌ Empty

---

### 5. Mixed Post (`post_type: 'mixed'`)

**Fields Used:**
- `content` ✅ - Caption/description with basic HTML
- `article_content` ❌ Null (use `content` only)
- `attachments` ✅ - Mixed media types
- `polls` ✅ (optional) - Polls

---

## Migration Strategy

### Step 1: Create Migration

```bash
# Create migration to add article_content field
docker compose exec backend python manage.py makemigrations content --name add_article_content_field

# This will generate: content/migrations/00XX_add_article_content_field.py
```

### Step 2: Apply Migration

```bash
# Apply the migration
docker compose exec backend python manage.py migrate content
```

### Step 3: Migrate Existing Data (Optional)

Since your current "article" posts are actually image/video posts with attachments, you can either:

**Option A: Keep them as-is** (Recommended - Simpler)
- Leave existing posts as `post_type='article'` with empty `article_content`
- Frontend will detect empty `article_content` and render as regular post with attachments
- No data migration needed

**Option B: Reclassify post types** (More accurate)

```python
# scripts/reclassify_article_posts.py
"""
Convert existing 'article' posts to proper post types based on their attachments
"""
from content.models import Post

def reclassify_article_posts():
    """
    Current 'article' posts with attachments should be reclassified as
    image/video/audio/mixed posts since they don't have embedded media.
    """

    article_posts = Post.objects.filter(post_type='article', article_content__isnull=True)

    for post in article_posts:
        # If post has attachments but no article_content, it's not a true article
        if post.media.exists():
            # Determine actual post type based on attachments
            media_types = set(post.media.values_list('media_type', flat=True))

            if len(media_types) == 1:
                # Single media type - change post_type to match
                media_type = list(media_types)[0]
                post.post_type = media_type  # 'image', 'video', 'audio', 'file'
                post.save()
                print(f"✅ Reclassified post {post.id} from 'article' to '{media_type}'")
            else:
                # Multiple media types - mark as mixed
                post.post_type = 'mixed'
                post.save()
                print(f"✅ Reclassified post {post.id} from 'article' to 'mixed'")
        else:
            # No attachments, no article_content - probably a text post
            print(f"⏭️  Skipped post {post.id} (no attachments, no article_content)")

if __name__ == '__main__':
    reclassify_article_posts()
```

**Run migration script:**
```bash
docker compose exec backend python scripts/reclassify_article_posts.py
```

---

## Update Serializers

### UnifiedPostSerializer (Add article_content)

```python
# content/unified_serializers.py

class UnifiedPostSerializer(serializers.ModelSerializer):
    """Complete serializer with all fields including article_content"""

    attachments = EnhancedPostMediaSerializer(source='media', many=True, read_only=True)
    polls = EnhancedPollSerializer(many=True, read_only=True)

    # Add computed field to help frontend
    has_embedded_media = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'author_username', 'author_name', 'author_avatar',
            'content',          # Basic HTML for captions (ALL post types)
            'article_content',  # Rich HTML for articles only
            'post_type', 'visibility',
            'attachments', 'attachment_count', 'has_attachments', 'attachments_by_type',
            'polls', 'polls_count', 'has_polls',
            'has_embedded_media',  # NEW: Helper flag
            'likes_count', 'comments_count', 'shares_count',
            'user_has_liked', 'user_has_saved',
            'created_at', 'updated_at',
            # ... other fields
        ]

    def get_has_embedded_media(self, obj):
        """
        Returns True if this is an article with embedded media in article_content.
        Frontend uses this to decide rendering strategy.
        """
        if obj.post_type != 'article':
            return False

        if not obj.article_content:
            return False

        # Check if article_content has img/video/audio tags
        import re
        return bool(re.search(r'<(img|video|audio)[^>]*>', obj.article_content))
```

---

## Frontend Changes

### API Response Examples

#### Rich Article (TipTap-created)
```json
{
  "id": "uuid",
  "post_type": "article",
  "content": "Découverte du lac des Nations...",  // Auto-generated excerpt
  "article_content": "<h1>Découverte du lac des Nations</h1><p>...</p><img src='https://server.com/media/lake.jpg' />",
  "attachments": [],
  "has_embedded_media": true
}
```

#### Image Post (Regular with attachments)
```json
{
  "id": "uuid",
  "post_type": "image",
  "content": "Magnifique coucher de soleil ! 🌅 <strong>Incroyable</strong>",
  "article_content": null,
  "attachments": [
    {
      "media_type": "image",
      "file_url": "https://images.unsplash.com/...",
      "description": "Coucher de soleil sur le lac"
    }
  ],
  "has_embedded_media": false
}
```

### Frontend Display Logic

```javascript
// src/components/posts/Post.js
const Post = ({ post }) => {
  const renderPostContent = () => {
    switch (post.post_type) {
      case 'article':
        if (post.has_embedded_media && post.article_content) {
          // TRUE RICH ARTICLE: Render article_content HTML with embedded media
          return (
            <ArticleContent htmlContent={post.article_content} />
          );
        } else {
          // LEGACY: Old "article" posts with attachments (before migration)
          // OR: Article without embedded media
          return (
            <>
              <PostContent content={post.content} renderBasicHTML={true} />
              {post.attachments && post.attachments.length > 0 && (
                <PostAttachments
                  attachments={post.attachments}
                  showLabels={true}
                />
              )}
            </>
          );
        }

      case 'image':
      case 'video':
      case 'audio':
        // Regular media posts
        return (
          <>
            <PostContent content={post.content} renderBasicHTML={true} />
            <PostAttachments
              attachments={post.attachments}
              showLabels={true}
            />
          </>
        );

      case 'poll':
        return (
          <>
            <PostContent content={post.content} renderBasicHTML={true} />
            {post.polls.map(poll => (
              <PollWidget key={poll.id} poll={poll} />
            ))}
          </>
        );

      case 'mixed':
        return (
          <>
            <PostContent content={post.content} renderBasicHTML={true} />
            {post.attachments && post.attachments.length > 0 && (
              <PostAttachments attachments={post.attachments} showLabels={true} />
            )}
            {post.polls && post.polls.map(poll => (
              <PollWidget key={poll.id} poll={poll} />
            ))}
          </>
        );

      default:
        return <PostContent content={post.content} renderBasicHTML={true} />;
    }
  };

  return (
    <article className={styles.post}>
      <PostHeader author={post.author} timestamp={post.created_at} />
      {renderPostContent()}
      <PostActions post={post} />
    </article>
  );
};
```

### PostContent Component (Updated for Basic HTML)

```javascript
// src/components/posts/PostContent.js
import React from 'react';
import DOMPurify from 'dompurify';
import styles from './PostContent.module.css';

/**
 * Renders basic HTML content (bold, italic, links, emoji)
 * Used for captions, descriptions, poll questions, etc.
 */
const PostContent = ({ content, renderBasicHTML = true }) => {
  if (!content) return null;

  if (renderBasicHTML) {
    // Sanitize HTML to allow only basic formatting tags
    const clean = DOMPurify.sanitize(content, {
      ALLOWED_TAGS: ['b', 'i', 'strong', 'em', 'a', 'br', 'p'],
      ALLOWED_ATTR: ['href', 'target', 'rel']
    });

    return (
      <div
        className={styles.postContent}
        dangerouslySetInnerHTML={{ __html: clean }}
      />
    );
  }

  // Fallback: Plain text with line breaks
  return (
    <div className={styles.postContent}>
      {content.split('\n').map((line, index) => (
        <p key={index}>{line}</p>
      ))}
    </div>
  );
};

export default PostContent;
```

### ArticleContent Component (For Rich Articles)

```javascript
// src/components/posts/ArticleContent.js
import React from 'react';
import DOMPurify from 'dompurify';
import { getMediaUrl } from '../../utils/mediaUtils';
import styles from './ArticleContent.module.css';

/**
 * Renders rich HTML article content with embedded media
 * Used ONLY for article posts with article_content field
 */
const ArticleContent = ({ htmlContent }) => {
  if (!htmlContent) return null;

  // Process HTML to ensure media URLs are absolute
  const processedHTML = React.useMemo(() => {
    let processed = htmlContent;

    // Ensure all media URLs are absolute
    processed = processed.replace(
      /<img([^>]*)\ssrc=["']([^"']+)["']/gi,
      (match, attrs, src) => {
        const absoluteUrl = getMediaUrl(src);
        return `<img${attrs} src="${absoluteUrl}"`;
      }
    );

    processed = processed.replace(
      /<video([^>]*)\ssrc=["']([^"']+)["']/gi,
      (match, attrs, src) => {
        const absoluteUrl = getMediaUrl(src);
        return `<video${attrs} src="${absoluteUrl}"`;
      }
    );

    processed = processed.replace(
      /<source([^>]*)\ssrc=["']([^"']+)["']/gi,
      (match, attrs, src) => {
        const absoluteUrl = getMediaUrl(src);
        return `<source${attrs} src="${absoluteUrl}"`;
      }
    );

    processed = processed.replace(
      /<audio([^>]*)\ssrc=["']([^"']+)["']/gi,
      (match, attrs, src) => {
        const absoluteUrl = getMediaUrl(src);
        return `<audio${attrs} src="${absoluteUrl}"`;
      }
    );

    // Clean up TipTap data attributes
    processed = processed.replace(/\s*data-media-id=["'][^"']*["']/gi, '');
    processed = processed.replace(/\s*data-media-type=["'][^"']*["']/gi, '');

    // Sanitize while allowing media tags
    return DOMPurify.sanitize(processed, {
      ALLOWED_TAGS: [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'p', 'br', 'div', 'span',
        'b', 'i', 'strong', 'em', 'u', 's', 'sub', 'sup',
        'a', 'img', 'video', 'audio', 'source',
        'ul', 'ol', 'li',
        'blockquote', 'pre', 'code',
        'table', 'thead', 'tbody', 'tr', 'th', 'td'
      ],
      ALLOWED_ATTR: [
        'href', 'src', 'alt', 'title', 'class', 'style',
        'controls', 'autoplay', 'loop', 'muted', 'poster',
        'type', 'target', 'rel'
      ]
    });
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

---

## Summary of Changes

### Backend (Django)

1. ✅ **Add `article_content` field** - TextField, nullable, for TipTap HTML
2. ✅ **Keep `content` field** - Allow basic HTML (bold, italic, links, emoji) for ALL posts
3. ✅ **Auto-generate excerpts** - Post.save() creates excerpt from article_content
4. ✅ **Update serializers** - Add `article_content` and `has_embedded_media` fields
5. ✅ **Optional: Reclassify** - Migrate existing "article" posts to proper types

### Frontend (React)

1. ✅ **Create ArticleContent component** - Renders rich HTML from `article_content`
2. ✅ **Update PostContent component** - Support basic HTML rendering for all posts
3. ✅ **Update Post component** - Check `has_embedded_media` flag to route rendering
4. ✅ **Keep PostAttachments** - For regular media posts with separate attachments

### Benefits

✅ **All posts get formatting** - `content` supports basic HTML everywhere (bold, italic, emoji)
✅ **Clear separation** - `article_content` is ONLY for rich articles
✅ **Backwards compatible** - Existing posts work (with optional reclassification)
✅ **Simple frontend logic** - One check: `has_embedded_media ? render article_content : render content + attachments`
✅ **No confusion** - Article posts are clearly distinguished from media posts

---

## Implementation Steps

### Phase 1: Backend (30-45 minutes)

1. **Create migration** (5 min)
   ```bash
   docker compose exec backend python manage.py makemigrations content --name add_article_content_field
   ```

2. **Review migration file** (2 min)
   ```bash
   # Check: content/migrations/00XX_add_article_content_field.py
   ```

3. **Apply migration** (2 min)
   ```bash
   docker compose exec backend python manage.py migrate content
   ```

4. **Update Post model** (10 min)
   - Add `article_content` field definition
   - Add `save()` method for auto-excerpt generation

5. **Update UnifiedPostSerializer** (10 min)
   - Add `article_content` to fields list
   - Add `has_embedded_media` computed field

6. **Test API response** (5 min)
   ```bash
   # Create test article with article_content via admin or shell
   # Check API returns article_content field
   ```

7. **Optional: Reclassify posts** (5-10 min)
   ```bash
   # Run reclassification script
   docker compose exec backend python scripts/reclassify_article_posts.py
   ```

### Phase 2: Frontend (1-2 hours)

1. **Install DOMPurify** (2 min)
   ```bash
   npm install dompurify
   ```

2. **Create ArticleContent component** (20 min)
   - File: `src/components/posts/ArticleContent.js`
   - CSS: `src/components/posts/ArticleContent.module.css`

3. **Update PostContent component** (15 min)
   - Add `renderBasicHTML` prop
   - Add DOMPurify for basic HTML sanitization

4. **Update Post component** (20 min)
   - Add rendering logic based on `has_embedded_media`
   - Test with different post types

5. **Create PostAttachments enhancements** (30 min)
   - Show attachment descriptions as labels
   - Style attachment captions

6. **Testing** (30 min)
   - Test article posts (new vs legacy)
   - Test image/video/poll posts
   - Test mixed posts

### Phase 3: Validation (15-30 minutes)

1. **Create test article via UI** (TipTap editor)
2. **Verify database** - Check `article_content` field populated
3. **Verify API** - Check `has_embedded_media` flag correct
4. **Verify display** - Article renders with embedded media
5. **Test Sherbrooke posts** - Verify they display correctly (as reclassified type)

**Total Estimated Time:** 2-3 hours

---

## Next Steps

Ready to implement? Let me know and I can:

1. Create the migration file
2. Update the Post model
3. Update the serializers
4. Create the reclassification script
5. Create the frontend components

Which part would you like to start with?    def get_content_for_display(self):
        """Get appropriate content for display based on post type."""
        if self.is_rich_content:
            # Return raw HTML for article posts
            return self.content
        else:
            # Return plain text content
            return self.content

    def clean(self):
        """Validate post data."""
        super().clean()

        # Ensure article posts have is_rich_content=True
        if self.post_type == 'article' and not self.is_rich_content:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                "Article posts must have is_rich_content=True"
            )
```

---

## Updated Serializers

```python
# content/serializers.py or content/unified_serializers.py

class UnifiedPostSerializer(serializers.ModelSerializer):
    # ... existing fields ...

    is_rich_content = serializers.BooleanField(read_only=True)
    is_article = serializers.BooleanField(read_only=True)
    has_embedded_media = serializers.BooleanField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id',
            'author',
            'content',
            'post_type',
            'is_rich_content',  # NEW
            'is_article',       # NEW
            'has_embedded_media',  # NEW
            'attachments',
            'polls',
            # ... other fields ...
        ]
```

---

## Frontend API Response

### Regular Post with Attachments
```json
{
  "id": "uuid",
  "post_type": "image",
  "is_rich_content": false,
  "is_article": false,
  "content": "Magnifique coucher de soleil sur le lac des Nations ! 🌅",
  "attachments": [
    {
      "media_type": "image",
      "external_url": "https://images.unsplash.com/...",
      "description": "Coucher de soleil sur le lac"
    }
  ]
}
```

### Rich Article with Embedded Media
```json
{
  "id": "uuid",
  "post_type": "article",
  "is_rich_content": true,
  "is_article": true,
  "has_embedded_media": true,
  "content": "<p>Check this!</p><img src='https://server.com/media/sunset.jpg' /><p>Beautiful!</p>",
  "attachments": []
}
```

---

## Frontend Display Logic

```javascript
// src/components/posts/Post.js

const Post = ({ post }) => {
  const renderPostContent = () => {
    // ARTICLES: Rich HTML with embedded media
    if (post.is_article || post.is_rich_content) {
      return <ArticleContent htmlContent={post.content} />;
    }

    // REGULAR POSTS: Content + attachments
    switch (post.post_type) {
      case 'text':
        return <PostContent content={post.content} />;

      case 'image':
      case 'video':
      case 'audio':
      case 'file':
      case 'mixed':
        return (
          <>
            {post.content && <PostContent content={post.content} />}
            <PostAttachments
              attachments={post.attachments}
              showLabels={true}
            />
          </>
        );

      case 'poll':
        return (
          <>
            {post.content && <PostContent content={post.content} />}
            {post.polls?.map(poll => (
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
      <PostHeader {...post} />
      {renderPostContent()}
      <PostActions {...post} />
    </article>
  );
};
```

---

## Creating Posts from Frontend

### Regular Post with Attachments

```javascript
// PostCreationModal.jsx - Image/Video/Media Tab
const createMediaPost = async () => {
  const formData = new FormData();
  formData.append('content', 'Caption text here');
  formData.append('post_type', 'image');  // or 'video', 'audio', etc.
  formData.append('is_rich_content', false);  // Regular post

  // Add attachments
  attachments.forEach((file, index) => {
    formData.append(`media_${index}`, file);
  });

  await socialAPI.posts.create(formData);
};
```

### Rich Article Post

```javascript
// PostCreationModal.jsx - Article Tab (TipTap Editor)
const createArticle = async () => {
  // Phase 1: Create post
  const post = await socialAPI.posts.create({
    content: '<p>Placeholder</p>',
    post_type: 'article',
    is_rich_content: true,  // Rich article
    visibility: 'public'
  });

  // Phase 2: Upload embedded media & get processed HTML
  const { processedContent } = await richTextEditorRef.current.processContentForSubmission(
    async (file, mediaType) => {
      return await onImageUpload(file);
    }
  );

  // Phase 3: Update with final HTML
  await socialAPI.posts.update(post.id, {
    content: processedContent
  });
};
```

---

## Summary of Changes

### Database Changes
1. ✅ Add `is_rich_content` boolean field to Post model
2. ✅ Create migration to add field
3. ✅ Create data migration to convert existing posts
4. ✅ Update model methods (`is_article`, `has_embedded_media`)

### Backend Changes
5. ✅ Update serializers to include new fields
6. ✅ Update API documentation
7. ✅ Add validation in model's `clean()` method

### Frontend Changes
8. ✅ Update Post component to check `is_rich_content`
9. ✅ Create ArticleContent component for rich HTML
10. ✅ Update PostCreationModal to set `is_rich_content` flag
11. ✅ Update API calls to send correct post_type and is_rich_content

### Testing
12. ✅ Test existing Sherbrooke posts (should become `post_type='image'`)
13. ✅ Test creating new article via TipTap (should be `post_type='article', is_rich_content=True`)
14. ✅ Verify rendering for both types

---

## Implementation Steps (Recommended Order)

1. **Add field to model** (5 minutes)
   ```bash
   # Edit content/models.py
   # Add is_rich_content field
   ```

2. **Create migrations** (5 minutes)
   ```bash
   docker compose exec backend python manage.py makemigrations content
   ```

3. **Create data migration** (10 minutes)
   ```bash
   docker compose exec backend python manage.py makemigrations content --empty --name convert_articles
   # Edit migration file
   ```

4. **Apply migrations** (2 minutes)
   ```bash
   docker compose exec backend python manage.py migrate content
   ```

5. **Update serializers** (5 minutes)
   ```python
   # Add is_rich_content, is_article to serializer fields
   ```

6. **Test with Django shell** (5 minutes)
   ```bash
   docker compose exec backend python manage.py shell
   # Verify posts are correctly categorized
   ```

7. **Update frontend** (30 minutes)
   - Update Post component
   - Create ArticleContent component
   - Update PostCreationModal

**Total time: ~1 hour**
