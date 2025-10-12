# Article Posts with Embedded Media - Implementation Guide

## Architecture Overview

### 1. Data Flow

```
User creates article with embedded images/videos
    ↓
RichTextEditor creates blob placeholders
    ↓
On Submit → Upload media files to server
    ↓
Replace blob URLs with server URLs in HTML
    ↓
Save processed HTML content to Post.content field
```

### 2. Database Structure

**Post Model:**
```python
content = TextField(max_length=2000, blank=True)  # Stores rich HTML content
post_type = 'article'  # For rich text posts
```

**PostMedia Model:**
```python
# For EMBEDDED media in articles (referenced in content HTML)
post = ForeignKey(Post)
file = FileField()  # The actual media file
description = CharField(max_length=200, blank=True)
media_type = 'image' | 'video' | 'audio' | 'file'
order = PositiveIntegerField()  # Position in article
```

### 3. Frontend Implementation

#### Step 1: Update PostCreationModal to handle article media uploads

```jsx
const handleSubmit = async (e) => {
  e.preventDefault();

  if (activeType === 'article') {
    // Get processed content from RichTextEditor
    const { processedContent, mediaFiles } = await richTextEditorRef.current.getProcessedContent({
      uploadCallback: async (file, mediaType) => {
        // Upload file and return server URL
        const formData = new FormData();
        formData.append('file', file);
        formData.append('media_type', mediaType);

        const response = await socialAPI.posts.uploadArticleMedia(formData);
        return response.file_url;  // Return the server URL
      }
    });

    // Create post with processed HTML content
    const postData = {
      content: processedContent,  // HTML with server URLs
      post_type: 'article',
      visibility,
      // Media files are embedded in content, not separate attachments
    };

    await socialAPI.posts.create(postData);
  }
};
```

#### Step 2: Add upload handler to RichTextEditor

Your RichTextEditor already has `processContentForSubmission`. We need to enhance it:

```jsx
// In RichTextEditor.jsx - around line 1570
const processContentForSubmission = useCallback(async (uploadHandlers = {}) => {
  if (!editor) return { processedContent: '', mediaFiles: [] };

  let processedContent = editor.getHTML();
  const mediaFiles = [];

  for (const attachment of mediaAttachments) {
    const { id, file, type } = attachment;

    try {
      let mediaUrl = null;

      // Call the upload callback provided by parent
      if (uploadHandlers.uploadCallback) {
        mediaUrl = await uploadHandlers.uploadCallback(file, type);
      }

      if (mediaUrl) {
        // Replace placeholder with actual media element
        if (type === 'image') {
          // For images, preserve alignment and sizing
          const imgRegex = new RegExp(`<img[^>]*data-media-id="${id}"[^>]*>`, 'g');
          processedContent = processedContent.replace(imgRegex, (match) => {
            // Extract existing attributes (class, style)
            const classMatch = match.match(/class="([^"]*)"/);
            const styleMatch = match.match(/style="([^"]*)"/);

            return `<img src="${mediaUrl}" alt="${file.name}" class="${classMatch ? classMatch[1] : 'max-w-full h-auto rounded-lg'}" style="${styleMatch ? styleMatch[1] : ''}" />`;
          });
        } else if (type === 'video') {
          processedContent = processedContent.replace(
            new RegExp(`<div data-media-id="${id}"[^>]*>.*?</div>`, 's'),
            `<video src="${mediaUrl}" controls style="max-width: 100%; height: auto; border-radius: 0.5rem; margin: 1rem 0;"></video>`
          );
        } else if (type === 'audio') {
          processedContent = processedContent.replace(
            new RegExp(`<div data-media-id="${id}"[^>]*>.*?</div>`, 's'),
            `<audio src="${mediaUrl}" controls style="width: 100%; margin: 1rem 0;"></audio>`
          );
        }

        mediaFiles.push({
          id,
          file,
          type,
          url: mediaUrl
        });
      }
    } catch (error) {
      console.error(`Failed to process media ${id}:`, error);
    }
  }

  return { processedContent, mediaFiles };
}, [editor, mediaAttachments]);

// Expose this method to parent via ref
useImperativeHandle(ref, () => ({
  getProcessedContent: processContentForSubmission,
  getHTML: () => editor?.getHTML(),
  getJSON: () => editor?.getJSON(),
}));
```

### 4. Backend API Endpoint

Add a new endpoint for uploading article media:

```python
# In content/unified_views.py

@action(detail=False, methods=['post'])
def upload_article_media(self, request):
    """
    Upload media file for embedding in article content.
    Returns the media URL to replace the blob placeholder.
    """
    serializer = EnhancedPostMediaSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        # Save media without attaching to a post yet
        # This is a temporary upload that will be associated
        # when the article is created
        media = serializer.save()

        return Response({
            'id': media.id,
            'file_url': request.build_absolute_uri(media.file.url),
            'media_type': media.media_type
        }, status=status.HTTP_201_CREATED)

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )
```

### 5. Alternative Approach: Two-Phase Upload

**Phase 1: Create Post First**
```jsx
// Create the post without processing media
const postResponse = await socialAPI.posts.create({
  content: ' ',  // Temporary placeholder
  post_type: 'article',
  visibility
});

const postId = postResponse.id;
```

**Phase 2: Upload Media & Update Content**
```jsx
// Upload all media files
const uploadedMedia = [];
for (const attachment of mediaAttachments) {
  const formData = new FormData();
  formData.append('file', attachment.file);
  formData.append('media_type', attachment.type);

  const media = await socialAPI.posts.addAttachment(postId, formData);
  uploadedMedia.push({ id: attachment.id, url: media.file_url });
}

// Replace placeholders with server URLs
let processedContent = editor.getHTML();
uploadedMedia.forEach(({ id, url }) => {
  processedContent = processedContent.replace(
    new RegExp(`data-media-id="${id}"`, 'g'),
    `src="${url}"`
  );
});

// Update post with processed content
await socialAPI.posts.update(postId, {
  content: processedContent
});
```

### 6. Video & Audio Alignment/Sizing

Add these functions to RichTextEditor (similar to image alignment):

```jsx
const setVideoWidth = useCallback((width) => {
  if (!editor) return;

  const { state } = editor;
  const { selection } = state;

  // Find video element at cursor
  const node = state.doc.nodeAt(selection.from);

  if (node && node.type.name === 'video') {
    editor.chain().focus()
      .updateAttributes('video', {
        style: `max-width: ${width}%; height: auto; margin: 1rem auto; display: block;`
      })
      .run();
  }
}, [editor]);

const setVideoAlignment = useCallback((alignment) => {
  if (!editor) return;

  let alignStyle = '';
  if (alignment === 'left') {
    alignStyle = 'float: left; margin: 0 1rem 1rem 0;';
  } else if (alignment === 'right') {
    alignStyle = 'float: right; margin: 0 0 1rem 1rem;';
  } else if (alignment === 'center') {
    alignStyle = 'display: block; margin: 1rem auto;';
  }

  editor.chain().focus()
    .updateAttributes('video', { style: alignStyle })
    .run();
}, [editor]);
```

### 7. Complete Example

```jsx
// PostCreationModal.jsx
const handleArticleSubmit = async () => {
  // Step 1: Create post first
  const postResponse = await socialAPI.posts.create({
    content: ' ',
    post_type: 'article',
    visibility
  });

  // Step 2: Upload embedded media
  const attachments = richTextEditorRef.current.getMediaAttachments();
  const uploadPromises = attachments.map(async (att) => {
    const formData = new FormData();
    formData.append('file', att.file);
    formData.append('media_type', att.type);

    const media = await socialAPI.posts.addAttachment(
      postResponse.id,
      formData
    );

    return { placeholderId: att.id, serverUrl: media.file_url };
  });

  const uploadedMedia = await Promise.all(uploadPromises);

  // Step 3: Replace placeholders with server URLs
  let content = richTextEditorRef.current.getHTML();
  uploadedMedia.forEach(({ placeholderId, serverUrl }) => {
    content = content.replace(
      new RegExp(`data-media-id="${placeholderId}"[^>]*src="[^"]*"`, 'g'),
      `src="${serverUrl}"`
    );
  });

  // Step 4: Update post with final content
  await socialAPI.posts.update(postResponse.id, { content });
};
```

## Best Practices

1. **Use blob URLs for preview** - Fast and no server load
2. **Upload on submit** - Don't upload until user confirms
3. **Show upload progress** - Let users know what's happening
4. **Handle errors gracefully** - Allow retry or removal
5. **Optimize images** - Resize before upload (already done)
6. **Validate file sizes** - Prevent large uploads
7. **Clean up blob URLs** - Revoke after upload to free memory

## Security Considerations

1. **Sanitize HTML** - Strip dangerous tags/attributes on backend
2. **Validate media types** - Check file headers, not just extensions
3. **Limit file sizes** - Prevent abuse
4. **Rate limiting** - Prevent spam uploads
5. **Check permissions** - Ensure user can upload to this post
