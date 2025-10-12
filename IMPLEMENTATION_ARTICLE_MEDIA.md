# Implementation: Article Posts with Embedded Media

## Quick Summary

Your RichTextEditor **ALREADY HAS** the media embedding system! Here's how to use it properly:

## ✅ What Already Works

1. **Media Detection & Validation**
   - Accepts: images, videos, audio, PDF files
   - Duration validation: 5-minute limit for video/audio
   - File type detection via MIME types

2. **Placeholder System**
   - Creates blob URLs for instant preview
   - Inserts placeholders with `data-media-id` attributes
   - Tracks all media in `mediaAttachments` state

3. **Media Rendering in Editor**
   - Images: Full preview with alignment/resize support
   - Videos: Preview card with thumbnail
   - Audio: Icon-based card
   - Files: Document card

## 🔧 How to Use It (Step by Step)

### Option 1: Simple Two-Phase Upload (RECOMMENDED)

This is the cleanest approach and works with your existing backend:

```jsx
// In PostCreationModal.jsx (Article tab submission)

const handleArticleSubmit = async () => {
  try {
    setIsSubmitting(true);

    // PHASE 1: Create post first
    const postResponse = await socialAPI.posts.create({
      content: ' ',  // Temporary placeholder
      post_type: 'article',
      visibility,
      community_id: community?.id
    });

    const postId = postResponse.id;

    // PHASE 2: Get media from RichTextEditor
    const mediaAttachments = richTextEditorRef.current?.getMediaAttachments?.() || [];

    if (mediaAttachments.length === 0) {
      // No media, just update with content
      const content = richTextEditorRef.current.getHTML();
      await socialAPI.posts.update(postId, { content });
      onSubmit(postResponse);
      handleClose();
      return;
    }

    // PHASE 3: Upload all media files
    const uploadResults = [];

    for (const attachment of mediaAttachments) {
      try {
        const formData = new FormData();
        formData.append('file', attachment.file);
        formData.append('media_type', attachment.type);
        formData.append('order', uploadResults.length + 1);

        // Upload using existing add-attachment endpoint
        const mediaResponse = await socialAPI.posts.addAttachment(postId, formData);

        uploadResults.push({
          placeholderId: attachment.id,
          serverUrl: mediaResponse.file_url || mediaResponse.file,
          type: attachment.type
        });
      } catch (error) {
        console.error(`Failed to upload ${attachment.name}:`, error);
        // Continue with other uploads
      }
    }

    // PHASE 4: Replace blob URLs with server URLs in content
    let finalContent = richTextEditorRef.current.getHTML();

    uploadResults.forEach(({ placeholderId, serverUrl, type }) => {
      if (type === 'image') {
        // For images: Replace the blob src with server URL
        const imgRegex = new RegExp(
          `(<img[^>]*data-media-id="${placeholderId}"[^>]*src=")[^"]*("[^>]*>)`,
          'g'
        );
        finalContent = finalContent.replace(imgRegex, `$1${serverUrl}$2`);

        // Also remove data-media-id to clean up
        finalContent = finalContent.replace(
          new RegExp(`data-media-id="${placeholderId}"\\s*`, 'g'),
          ''
        );
      } else {
        // For video/audio/file: Replace entire placeholder div
        const placeholderRegex = new RegExp(
          `<div[^>]*data-media-id="${placeholderId}"[^>]*>.*?</div>`,
          's'
        );

        let replacement = '';
        if (type === 'video') {
          replacement = `<video src="${serverUrl}" controls style="max-width: 100%; height: auto; border-radius: 0.5rem; margin: 1rem 0;"></video>`;
        } else if (type === 'audio') {
          replacement = `<audio src="${serverUrl}" controls style="width: 100%; max-width: 500px; margin: 1rem 0;"></audio>`;
        } else if (type === 'file') {
          const fileName = uploadResults.find(r => r.placeholderId === placeholderId)?.fileName || 'File';
          replacement = `<a href="${serverUrl}" target="_blank" rel="noopener noreferrer" style="display: inline-block; padding: 0.5rem 1rem; background: #eff6ff; border: 1px solid #3b82f6; border-radius: 0.25rem; color: #1d4ed8; text-decoration: none; margin: 0.5rem 0;">📄 ${fileName}</a>`;
        }

        finalContent = finalContent.replace(placeholderRegex, replacement);
      }
    });

    // PHASE 5: Update post with final content
    await socialAPI.posts.update(postId, {
      content: finalContent
    });

    // Success!
    onSubmit({ ...postResponse, content: finalContent });
    handleClose();

  } catch (error) {
    console.error('Failed to create article post:', error);
    setErrors({ submit: 'Failed to create article. Please try again.' });
  } finally {
    setIsSubmitting(false);
  }
};
```

### Option 2: Single-Phase with processContentForSubmission

The RichTextEditor already has a `processContentForSubmission` method. To use it:

1. **Expose the method via ref:**

```jsx
// Add to RichTextEditor.jsx (after line 1600 or so)
import { useImperativeHandle, forwardRef } from 'react';

const RichTextEditor = forwardRef(({ /* existing props */ }, ref) => {
  // ... existing code ...

  // Expose methods to parent
  useImperativeHandle(ref, () => ({
    getHTML: () => editor?.getHTML() || '',
    getJSON: () => editor?.getJSON() || {},
    getMediaAttachments: () => mediaAttachments,
    processContentForSubmission: async (uploadCallback) => {
      if (!editor) return { processedContent: '', mediaFiles: [] };

      let processedContent = editor.getHTML();
      const mediaFiles = [];

      for (const attachment of mediaAttachments) {
        try {
          // Call upload callback
          const mediaUrl = await uploadCallback(attachment.file, attachment.type);

          if (mediaUrl) {
            // Replace placeholder with actual URL
            if (attachment.type === 'image') {
              const imgRegex = new RegExp(
                `(<img[^>]*data-media-id="${attachment.id}"[^>]*src=")[^"]*("[^>]*>)`,
                'g'
              );
              processedContent = processedContent.replace(imgRegex, `$1${mediaUrl}$2`);
            } else if (attachment.type === 'video') {
              processedContent = processedContent.replace(
                new RegExp(`<div[^>]*data-media-id="${attachment.id}"[^>]*>.*?</div>`, 's'),
                `<video src="${mediaUrl}" controls style="max-width: 100%; height: auto; border-radius: 0.5rem; margin: 1rem 0;"></video>`
              );
            } else if (attachment.type === 'audio') {
              processedContent = processedContent.replace(
                new RegExp(`<div[^>]*data-media-id="${attachment.id}"[^>]*>.*?</div>`, 's'),
                `<audio src="${mediaUrl}" controls style="width: 100%; max-width: 500px; margin: 1rem 0;"></audio>`
              );
            }

            mediaFiles.push({ ...attachment, url: mediaUrl });
          }
        } catch (error) {
          console.error(`Failed to process ${attachment.name}:`, error);
        }
      }

      return { processedContent, mediaFiles };
    }
  }), [editor, mediaAttachments]);

  // ... rest of component ...
});

export default RichTextEditor;
```

2. **Use in PostCreationModal:**

```jsx
const richTextEditorRef = useRef(null);

// In render:
<RichTextEditor
  ref={richTextEditorRef}
  value={articleContent}
  onChange={setArticleContent}
  placeholder="Write your article..."
/>

// In submit handler:
const { processedContent, mediaFiles } = await richTextEditorRef.current.processContentForSubmission(
  async (file, mediaType) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('media_type', mediaType);

    const media = await socialAPI.posts.addAttachment(postId, formData);
    return media.file_url || media.file;
  }
);

await socialAPI.posts.update(postId, { content: processedContent });
```

## 🎨 Adding Video & Audio Alignment/Sizing

Currently only images have alignment controls. To add for video/audio:

```jsx
// Add to RichTextEditor.jsx toolbar

// Video/Audio sizing buttons
{editor.isActive('video') || editor.isActive('audio') && (
  <div className="flex items-center gap-1 px-2 border-l border-gray-200">
    <button
      onClick={() => setMediaWidth('50')}
      className={toolbarButtonClasses}
      title="50% width"
    >
      50%
    </button>
    <button
      onClick={() => setMediaWidth('75')}
      className={toolbarButtonClasses}
      title="75% width"
    >
      75%
    </button>
    <button
      onClick={() => setMediaWidth('100')}
      className={toolbarButtonClasses}
      title="Full width"
    >
      100%
    </button>
  </div>
)}

// Add the setMediaWidth function:
const setMediaWidth = useCallback((width) => {
  if (!editor) return;

  const { state } = editor;
  const { from } = state.selection;

  // Check if we're near a video or audio element
  const node = state.doc.nodeAt(from);

  if (node?.type.name === 'video' || node?.type.name === 'audio') {
    editor.chain().focus()
      .updateAttributes(node.type.name, {
        style: `max-width: ${width}%; height: auto; display: block; margin: 1rem auto;`
      })
      .run();
  }
}, [editor]);
```

## 📋 Complete Flow Diagram

```
User Writes Article
    ↓
User Drops Image/Video into Editor
    ↓
Blob URL Created → Preview Shown
    ↓
User Continues Writing
    ↓
User Clicks "Publier"
    ↓
1. Create Post (empty content)
    ↓
2. Upload All Media Files
    ↓
3. Get Server URLs
    ↓
4. Replace Blobs with Server URLs
    ↓
5. Update Post with Final HTML
    ↓
Done! ✅
```

## 🔍 Debugging Tips

1. **Check blob URLs:** Console log `mediaAttachments` to see tracked files
2. **Inspect HTML:** Check `editor.getHTML()` before and after processing
3. **Test uploads:** Try uploading one file at a time
4. **Regex testing:** Use regex101.com to test replacement patterns
5. **Network tab:** Watch for upload progress and errors

## 🚀 Next Steps

1. ✅ Backend already supports description field
2. ✅ Media upload endpoint exists
3. ✅ RichTextEditor tracks media
4. 🔲 Implement Option 1 in PostCreationModal
5. 🔲 Add video/audio alignment controls (optional)
6. 🔲 Add upload progress indicator
7. 🔲 Test with various media types

The system is 90% ready! You just need to wire up the submission logic in PostCreationModal.
