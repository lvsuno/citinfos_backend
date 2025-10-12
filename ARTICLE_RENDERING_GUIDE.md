# Article Rendering Guide

**Date:** October 9, 2025
**Status:** Implementation Guide

---

## Overview

This document explains how to render article posts with embedded media using the existing carousel system from the previous client.

---

## Post Types & Rendering

### 1. **Article Post** (`post_type: 'text'`)

**Backend Data:**
```json
{
  "id": "uuid",
  "post_type": "text",
  "content": "<p>Check this out!</p><img src='https://server.com/media/photo.jpg' data-media-id='123' />",
  "attachments": [],  // Empty if media is embedded in content
  "created_at": "2025-10-09T..."
}
```

**Rendering Strategy:**
1. Parse HTML `content` field
2. Extract embedded media (`<img>`, `<video>`, `<audio>`)
3. Display HTML content with embedded media inline
4. **DO NOT use carousel** for embedded media in articles
5. Embedded media shows exactly where it's placed in the HTML

---

### 2. **Media Post** (`post_type: 'image'|'video'|'audio'`)

**Backend Data:**
```json
{
  "id": "uuid",
  "post_type": "image",
  "content": "My vacation photos",  // Optional description
  "attachments": [
    {
      "id": "att1",
      "media_type": "image",
      "file_url": "https://server.com/media/photo1.jpg",
      "description": "Beach sunset",
      "order": 1
    },
    {
      "id": "att2",
      "media_type": "image",
      "file_url": "https://server.com/media/photo2.jpg",
      "description": "Mountain view",
      "order": 2
    }
  ]
}
```

**Rendering Strategy:**
1. Display `content` as text description (if exists)
2. **USE CAROUSEL** (`AttachmentDisplay`) for `attachments` array
3. Carousel shows one media at a time with navigation
4. Dots indicator shows position
5. Click to open full preview modal

---

### 3. **Poll Post** (`post_type: 'poll'`)

**Backend Data:**
```json
{
  "id": "uuid",
  "post_type": "poll",
  "content": "What's your favorite color?",
  "polls": [{
    "id": "poll1",
    "question": "What's your favorite color?",
    "options": [...]
  }]
}
```

**Rendering Strategy:**
1. Display `content` as description (if different from question)
2. Use `PollDisplay` component for polls
3. **NO carousel** for polls

---

## When to Use Carousel

### ✅ **USE Carousel (AttachmentDisplay):**

1. **Media Posts** - `post_type: 'image'|'video'|'audio'|'file'`
   - Has `attachments` array
   - No embedded media in `content`
   - Example: Photo album, video gallery

2. **Article with Separate Attachments** (rare case)
   - `post_type: 'text'`
   - Has `attachments` array (not embedded)
   - Example: Article with downloadable files

---

### ❌ **DO NOT Use Carousel:**

1. **Article Posts with Embedded Media**
   - Media is in HTML `content` via `<img>`, `<video>`, `<audio>` tags
   - Render HTML as-is, media shows inline
   - Example: Blog post with images throughout

2. **Poll Posts**
   - Use `PollDisplay` component instead

---

## Implementation Strategy

### Component Structure

```jsx
<PostCard post={post}>
  {/* Post header (author, timestamp, etc.) */}

  {/* Content rendering based on post_type */}
  {post.post_type === 'text' && (
    <ArticleContent content={post.content} />
  )}

  {/* Attachments carousel for media posts */}
  {(post.post_type === 'image' || post.post_type === 'video' ||
    post.post_type === 'audio' || post.post_type === 'file') &&
    post.attachments?.length > 0 && (
    <AttachmentDisplay
      attachments={post.attachments}
      expanded={expanded}
      onToggle={() => setExpanded(!expanded)}
    />
  )}

  {/* Poll display for poll posts */}
  {post.post_type === 'poll' && post.polls?.length > 0 && (
    post.polls.map(poll => (
      <PollDisplay key={poll.id} poll={poll} />
    ))
  )}

  {/* Post actions (like, comment, share) */}
</PostCard>
```

---

## Article Content Rendering

### Simple Implementation

```jsx
const ArticleContent = ({ content }) => {
  return (
    <div
      className="prose prose-sm max-w-none mt-3"
      dangerouslySetInnerHTML={{ __html: content }}
    />
  );
};
```

### Secure Implementation (Recommended)

```jsx
import DOMPurify from 'dompurify';

const ArticleContent = ({ content }) => {
  const sanitizedContent = DOMPurify.sanitize(content, {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'em', 'u', 's', 'a', 'ul', 'ol', 'li',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre',
      'img', 'video', 'audio', 'source'
    ],
    ALLOWED_ATTR: [
      'href', 'src', 'alt', 'title', 'class', 'style',
      'controls', 'autoplay', 'loop', 'muted', 'playsinline',
      'width', 'height', 'data-*'
    ],
    ALLOW_DATA_ATTR: true
  });

  return (
    <div
      className="prose prose-sm max-w-none mt-3 article-content"
      dangerouslySetInnerHTML={{ __html: sanitizedContent }}
    />
  );
};
```

---

## Styling for Article Content

### Tailwind Prose Classes

```css
/* Already handled by Tailwind Typography plugin */
.prose {
  /* Styles for paragraphs, headings, lists, etc. */
}

.prose img {
  @apply rounded-lg my-4;
  max-height: 520px;
  object-fit: contain;
}

.prose video {
  @apply rounded-lg my-4 w-full;
  max-height: 520px;
}

.prose audio {
  @apply w-full my-3;
}
```

### Custom Styles

```css
/* src/styles/article-content.css */

.article-content {
  /* Base text */
  color: #374151;
  line-height: 1.7;
}

.article-content p {
  margin-bottom: 1em;
}

.article-content img {
  display: block;
  max-width: 100%;
  height: auto;
  border-radius: 0.5rem;
  margin: 1.5rem auto;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.article-content img[data-align="left"] {
  float: left;
  margin-right: 1.5rem;
  margin-bottom: 1rem;
  max-width: 50%;
}

.article-content img[data-align="right"] {
  float: right;
  margin-left: 1.5rem;
  margin-bottom: 1rem;
  max-width: 50%;
}

.article-content img[data-align="center"] {
  display: block;
  margin-left: auto;
  margin-right: auto;
}

.article-content video {
  display: block;
  width: 100%;
  max-height: 520px;
  border-radius: 0.5rem;
  margin: 1.5rem 0;
  background: #000;
}

.article-content audio {
  display: block;
  width: 100%;
  max-width: 500px;
  margin: 1.5rem auto;
}

.article-content h1 {
  font-size: 1.875rem;
  font-weight: 700;
  margin-top: 2rem;
  margin-bottom: 1rem;
}

.article-content h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.article-content h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
}

.article-content a {
  color: #3b82f6;
  text-decoration: underline;
}

.article-content a:hover {
  color: #2563eb;
}

.article-content blockquote {
  border-left: 4px solid #e5e7eb;
  padding-left: 1rem;
  font-style: italic;
  color: #6b7280;
  margin: 1.5rem 0;
}

.article-content code {
  background: #f3f4f6;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-family: 'Courier New', monospace;
  font-size: 0.875em;
}

.article-content pre {
  background: #1f2937;
  color: #f3f4f6;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 1.5rem 0;
}

.article-content ul, .article-content ol {
  margin-left: 1.5rem;
  margin-bottom: 1rem;
}

.article-content li {
  margin-bottom: 0.5rem;
}
```

---

## Complete Implementation Example

### Updated PostCard Component

```jsx
import React, { useState } from 'react';
import AttachmentDisplay from './AttachmentDisplay';
import PollDisplay from './PollDisplay';
import DOMPurify from 'dompurify';

const PostCard = ({ post, onDelete, onUpdate, onVote }) => {
  const [expanded, setExpanded] = useState(false);

  // Sanitize HTML content for articles
  const sanitizeContent = (html) => {
    return DOMPurify.sanitize(html, {
      ALLOWED_TAGS: [
        'p', 'br', 'strong', 'em', 'u', 's', 'a', 'ul', 'ol', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre',
        'img', 'video', 'audio', 'source', 'span', 'div'
      ],
      ALLOWED_ATTR: [
        'href', 'src', 'alt', 'title', 'class', 'style',
        'controls', 'autoplay', 'loop', 'muted', 'playsinline',
        'width', 'height', 'data-*'
      ],
      ALLOW_DATA_ATTR: true
    });
  };

  const hasAttachments = post.attachments && post.attachments.length > 0;
  const hasPolls = post.polls && post.polls.length > 0;
  const isArticle = post.post_type === 'text';
  const isMediaPost = ['image', 'video', 'audio', 'file'].includes(post.post_type);
  const isPollPost = post.post_type === 'poll';

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
      {/* Post Header */}
      <div className="flex items-center gap-3 mb-3">
        <img
          src={post.author?.avatar || '/default-avatar.png'}
          alt={post.author?.display_name}
          className="w-10 h-10 rounded-full"
        />
        <div className="flex-1">
          <div className="font-medium text-gray-900">
            {post.author?.display_name}
          </div>
          <div className="text-xs text-gray-500">
            {new Date(post.created_at).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Article Content (HTML with embedded media) */}
      {isArticle && post.content && (
        <div
          className="prose prose-sm max-w-none mt-3 article-content"
          dangerouslySetInnerHTML={{
            __html: sanitizeContent(post.content)
          }}
        />
      )}

      {/* Media Post Content (carousel for attachments) */}
      {isMediaPost && (
        <>
          {/* Optional description text */}
          {post.content && (
            <div className="text-gray-700 mb-3">
              {post.content}
            </div>
          )}

          {/* Attachments carousel */}
          {hasAttachments && (
            <AttachmentDisplay
              attachments={post.attachments}
              expanded={expanded}
              onToggle={() => setExpanded(!expanded)}
              onOpenPdf={(att) => {
                // Handle PDF preview
                window.open(att.file_url, '_blank');
              }}
            />
          )}
        </>
      )}

      {/* Poll Post Content */}
      {isPollPost && (
        <>
          {/* Optional description */}
          {post.content && (
            <div className="text-gray-700 mb-3">
              {post.content}
            </div>
          )}

          {/* Polls */}
          {hasPolls && (
            <div className="space-y-3">
              {post.polls.map((poll) => (
                <PollDisplay
                  key={poll.id}
                  poll={poll}
                  onVote={onVote}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Post Actions (like, comment, share, etc.) */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        {/* Action buttons */}
      </div>
    </div>
  );
};

export default PostCard;
```

---

## Summary Table

| Post Type | Content Field | Attachments | Rendering Method |
|-----------|--------------|-------------|------------------|
| Article (`text`) | HTML string with embedded `<img>`, `<video>`, etc. | Usually empty | Render HTML inline, media shows where placed |
| Media (`image`/`video`/`audio`/`file`) | Optional text description | Array of media objects | **Carousel (AttachmentDisplay)** |
| Poll (`poll`) | Optional description | Empty | Use `PollDisplay` component |

---

## Key Points

1. ✅ **Article posts** → Render HTML content directly, embedded media shows inline
2. ✅ **Media posts** → Use carousel for `attachments` array
3. ✅ **Poll posts** → Use poll display component
4. ✅ **Carousel** = `AttachmentDisplay` component from previous client
5. ✅ **Carousel features**:
   - Shows one media at a time
   - Navigation arrows (previous/next)
   - Dots indicator
   - Click to open full preview modal
   - Supports images, videos, audio, PDFs
   - Responsive and touch-friendly

---

## Next Steps

1. Copy `AttachmentDisplay.jsx` to current client: `src/components/social/AttachmentDisplay.jsx`
2. Install DOMPurify: `npm install dompurify`
3. Update `PostCard.jsx` to handle article rendering
4. Add CSS styles for `.article-content`
5. Test with real article posts containing embedded media
6. Test with media posts using carousel

---

## Security Note

Always sanitize HTML content before rendering to prevent XSS attacks. Use DOMPurify with a whitelist of allowed tags and attributes.

```jsx
import DOMPurify from 'dompurify';

const sanitized = DOMPurify.sanitize(userContent, {
  ALLOWED_TAGS: ['p', 'br', 'img', 'video', ...],
  ALLOWED_ATTR: ['src', 'alt', 'controls', ...],
  ALLOW_DATA_ATTR: true
});
```

