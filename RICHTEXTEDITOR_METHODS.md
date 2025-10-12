# RichTextEditor - Add These Methods

## Add to src/components/ui/RichTextEditor.jsx

### 1. Import forwardRef at the top (line ~1)

```jsx
import React, {
  useCallback, useMemo, useState, useEffect, useRef,
  useImperativeHandle, forwardRef  // Add these two
} from 'react';
```

### 2. Change component declaration (line ~647)

**BEFORE:**
```jsx
const RichTextEditor = ({
  value = '',
  onChange = () => {},
  // ... other props
}) => {
```

**AFTER:**
```jsx
const RichTextEditor = forwardRef(({
  value = '',
  onChange = () => {},
  // ... other props
}, ref) => {
```

### 3. Add useImperativeHandle before return statement (~line 2800)

```jsx
  // Expose methods to parent component via ref
  useImperativeHandle(ref, () => ({
    // Get current HTML content
    getHTML: () => editor?.getHTML() || '',

    // Get current JSON content
    getJSON: () => editor?.getJSON() || {},

    // Get current media attachments
    getMediaAttachments: () => mediaAttachments,

    // Process content for submission - upload media and replace placeholders
    processContentForSubmission: async (uploadCallback) => {
      if (!editor) {
        return { processedContent: '', mediaFiles: [] };
      }

      let processedContent = editor.getHTML();
      const mediaFiles = [];

      for (const attachment of mediaAttachments) {
        try {
          // Call upload callback provided by parent
          const mediaUrl = await uploadCallback(attachment.file, attachment.type);

          if (mediaUrl) {
            // Replace placeholder with actual URL based on media type
            if (attachment.type === 'image') {
              // For images: Replace src attribute while preserving other attributes
              const imgRegex = new RegExp(
                `(<img[^>]*data-media-id="${attachment.id}"[^>]*src=")[^"]*("[^>]*>)`,
                'g'
              );
              processedContent = processedContent.replace(imgRegex, `$1${mediaUrl}$2`);

              // Remove data-media-id attribute to clean up
              processedContent = processedContent.replace(
                new RegExp(`\\s*data-media-id="${attachment.id}"`, 'g'),
                ''
              );
            } else if (attachment.type === 'video') {
              // Replace placeholder div with video element
              processedContent = processedContent.replace(
                new RegExp(`<div[^>]*data-media-id="${attachment.id}"[^>]*>.*?</div>`, 's'),
                `<video src="${mediaUrl}" controls style="max-width: 100%; height: auto; border-radius: 0.5rem; margin: 1rem 0;"></video>`
              );
            } else if (attachment.type === 'audio') {
              // Replace placeholder div with audio element
              processedContent = processedContent.replace(
                new RegExp(`<div[^>]*data-media-id="${attachment.id}"[^>]*>.*?</div>`, 's'),
                `<audio src="${mediaUrl}" controls style="width: 100%; max-width: 500px; margin: 1rem 0;"></audio>`
              );
            } else if (attachment.type === 'file') {
              // Replace placeholder div with download link
              processedContent = processedContent.replace(
                new RegExp(`<div[^>]*data-media-id="${attachment.id}"[^>]*>.*?</div>`, 's'),
                `<a href="${mediaUrl}" target="_blank" rel="noopener noreferrer" style="display: inline-block; padding: 0.5rem 1rem; background: #eff6ff; border: 1px solid #3b82f6; border-radius: 0.25rem; color: #1d4ed8; text-decoration: none; margin: 0.5rem 0;">📄 ${attachment.name}</a>`
              );
            }

            mediaFiles.push({
              ...attachment,
              url: mediaUrl
            });
          }
        } catch (error) {
          console.error(`Failed to process media ${attachment.name}:`, error);
        }
      }

      return { processedContent, mediaFiles };
    }
  }), [editor, mediaAttachments]);

  return (
    <div className="rich-text-editor-wrapper">
      {/* ... existing render code ... */}
    </div>
  );
});  // Close forwardRef here

// Add display name for better debugging
RichTextEditor.displayName = 'RichTextEditor';

export default RichTextEditor;
```

### 4. Update export (last line ~3073)

**BEFORE:**
```jsx
export default RichTextEditor;
```

**AFTER:**
```jsx
// Already changed above when wrapping with forwardRef
export default RichTextEditor;
```

## Usage in PostCreationModal.jsx

### 1. Create ref

```jsx
import { useRef } from 'react';

const PostCreationModal = ({ ... }) => {
  const richTextEditorRef = useRef(null);

  // ... rest of component
```

### 2. Pass ref to RichTextEditor

```jsx
<RichTextEditor
  ref={richTextEditorRef}
  value={articleContent}
  onChange={setArticleContent}
  placeholder="Écrivez votre article..."
  maxLength={5000}
/>
```

### 3. Use in submit handler

```jsx
const handleSubmit = async (e) => {
  e.preventDefault();

  if (activeType === 'article') {
    setIsSubmitting(true);

    try {
      // Step 1: Create post
      const postResponse = await socialAPI.posts.create({
        content: ' ',
        post_type: 'article',
        visibility,
        community_id: community?.id
      });

      // Step 2: Get media attachments
      const mediaAttachments = richTextEditorRef.current?.getMediaAttachments?.() || [];

      if (mediaAttachments.length === 0) {
        // No media, just update with content
        const content = richTextEditorRef.current.getHTML();
        await socialAPI.posts.update(postResponse.id, { content });
        onSubmit(postResponse);
        handleClose();
        return;
      }

      // Step 3: Upload media and get processed content
      const { processedContent, mediaFiles } = await richTextEditorRef.current.processContentForSubmission(
        async (file, mediaType) => {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('media_type', mediaType);

          const media = await socialAPI.posts.addAttachment(postResponse.id, formData);
          return media.file_url || media.file;
        }
      );

      // Step 4: Update post with processed content
      await socialAPI.posts.update(postResponse.id, {
        content: processedContent
      });

      // Success!
      onSubmit({ ...postResponse, content: processedContent });
      handleClose();

    } catch (error) {
      console.error('Failed to create article:', error);
      setErrors({ submit: 'Échec de la création de l\'article. Veuillez réessayer.' });
    } finally {
      setIsSubmitting(false);
    }
  }

  // ... handle other types (poll, media)
};
```

## Testing

1. Create a new article post
2. Write some text
3. Drop an image into the editor
4. Add more text
5. Drop a video
6. Click "Publier"
7. Watch console for upload progress
8. Verify final content has server URLs instead of blob URLs

## Troubleshooting

**Images not uploading?**
- Check `socialAPI.posts.addAttachment` returns correct structure
- Verify `file_url` field exists in response

**Placeholders not replaced?**
- Console log `mediaAttachments` to check IDs
- Console log HTML before and after processing
- Check regex patterns match your HTML structure

**forwardRef errors?**
- Make sure you imported it from 'react'
- Check closing parenthesis of forwardRef
- Add displayName for better error messages
