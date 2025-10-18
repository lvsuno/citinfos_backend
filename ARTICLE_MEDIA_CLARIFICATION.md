# Article Media Display - Critical Clarification

## The Problem Discovered

After investigating the imported Sherbrooke posts, we found they are stored as **hybrid articles** with a critical difference from TipTap-created articles:

### Imported Sherbrooke Posts (Current)
```json
{
  "post_type": "article",
  "content": "Magnifique coucher de soleil... #Sherbrooke",
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

**Issue:** Media is stored in `attachments` array but NOT embedded in HTML content!

### TipTap-Created Articles (Frontend)
```json
{
  "post_type": "article",
  "content": "<p>Magnifique coucher de soleil...</p><img src='https://server.com/media/...' />",
  "attachments": []  // EMPTY - media is INSIDE the HTML
}
```

**Correct:** Media is embedded directly in HTML content at exact position.

---

## Two Types of Article Posts

### Type A: Article with Separate Attachments (Imported/Backend-created)
- `post.content` = Plain text OR simple HTML
- `post.attachments` = Array with media objects
- Media has `description` labels
- **Display:** Show content, then attachments below with labels

### Type B: Article with Embedded Media (TipTap Editor)
- `post.content` = Rich HTML with `<img>`, `<video>`, `<audio>` tags
- `post.attachments` = Empty array
- Media embedded at exact positions in HTML
- **Display:** Render HTML directly (media appears inline)

---

## Solution: Hybrid Article Display

### Updated ArticleContent Component

```javascript
// src/components/posts/ArticleContent.js
import React from 'react';
import { getMediaUrl } from '../../utils/mediaUtils';
import PostAttachments from './PostAttachments';
import styles from './ArticleContent.module.css';

/**
 * Renders article content with smart media handling:
 * - If media is embedded in HTML: Render HTML directly
 * - If media is in attachments: Show content + attachments below
 */
const ArticleContent = ({ post }) => {
  const { content, attachments } = post;

  // Detect if content has embedded media (contains img/video/audio tags)
  const hasEmbeddedMedia = React.useMemo(() => {
    if (!content) return false;
    return /<(img|video|audio)[^>]*>/i.test(content);
  }, [content]);

  // Process HTML to ensure media URLs are absolute
  const processedHTML = React.useMemo(() => {
    if (!hasEmbeddedMedia) return content;

    let processed = content;

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

    return processed;
  }, [content, hasEmbeddedMedia]);

  return (
    <div className={styles.articleWrapper}>
      {/* Render HTML content */}
      {hasEmbeddedMedia ? (
        <div
          className={styles.articleContent}
          dangerouslySetInnerHTML={{ __html: processedHTML }}
        />
      ) : (
        <div className={styles.articleContent}>
          {content.split('\n').map((line, index) => (
            <p key={index}>{line}</p>
          ))}
        </div>
      )}

      {/* Show attachments ONLY if not embedded in HTML */}
      {!hasEmbeddedMedia && attachments && attachments.length > 0 && (
        <PostAttachments
          attachments={attachments}
          showLabels={true}  // Show description as captions
        />
      )}
    </div>
  );
};

export default ArticleContent;
```

---

## Updated Post Type Handler

```javascript
// src/components/posts/Post.js
const Post = ({ post }) => {
  const renderPostContent = () => {
    switch (post.post_type) {
      case 'article':
        // Smart article rendering: handles both embedded and separate media
        return <ArticleContent post={post} />;

      case 'image':
      case 'video':
      case 'audio':
        return (
          <>
            {post.content && <PostCaption content={post.content} />}
            <PostAttachments
              attachments={post.attachments}
              postType={post.post_type}
              showLabels={true}
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
        return <ArticleContent post={post} />;  // Same hybrid logic

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
    </article>
  );
};
```

---

## Display Flow Chart

```
Article Post Received
    ↓
Check: Does content contain <img>/<video>/<audio> tags?
    ↓
┌─────────────────┴─────────────────┐
│                                    │
YES (TipTap-created)            NO (Imported/Simple)
│                                    │
Render HTML with                 Render plain text
embedded media                   THEN show attachments
│                                    below with labels
│                                    │
└─────────────────┬─────────────────┘
                  ↓
            Display Complete
```

---

## Examples

### Example 1: TipTap Article (Embedded Media)

**Backend Data:**
```json
{
  "content": "<p>Check this out!</p><img src='https://server.com/media/sunset.jpg' alt='Sunset' /><p>Beautiful!</p>",
  "attachments": []
}
```

**Display:**
```
┌─────────────────────────────┐
│ Check this out!             │
│                             │
│ [IMAGE: Sunset]             │
│                             │
│ Beautiful!                  │
└─────────────────────────────┘
```

### Example 2: Imported Article (Separate Attachments)

**Backend Data:**
```json
{
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

**Display:**
```
┌─────────────────────────────┐
│ Magnifique coucher de       │
│ soleil sur le lac des       │
│ Nations ! 🌅                │
│                             │
│ [IMAGE]                     │
│ Caption: Coucher de soleil  │
│          sur le lac         │
└─────────────────────────────┘
```

---

## Implementation Priority

1. ✅ Understand the hybrid article structure (DONE)
2. **Create `ArticleContent` component** with embedded media detection
3. **Update `PostAttachments`** to show media with description labels
4. Test with:
   - TipTap-created articles (create new via UI)
   - Imported Sherbrooke posts (existing data)
5. Create `ImageGallery`, `VideoPlayer` components
6. Create `PollWidget` component

---

## Key Takeaways

1. **Articles can have TWO formats:**
   - Embedded media (TipTap HTML)
   - Separate attachments (imported/backend-created)

2. **Detection method:**
   - Regex test: `/<(img|video|audio)[^>]*>/i.test(content)`

3. **Display logic:**
   - Embedded: Render HTML directly
   - Separate: Show text + attachments with labels

4. **Sherbrooke posts:**
   - Currently use separate attachments format
   - Have descriptions/labels ready to display
   - Work perfectly with hybrid approach

5. **Future TipTap posts:**
   - Will use embedded format
   - Media appears exactly where placed in editor
   - No attachments array
