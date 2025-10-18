# TipTap Audio & Video Implementation Guide

## Overview
This document describes the implementation of interactive audio and video upload, resize, alignment, and drag-drop functionality in the TipTap rich text editor, following the same pattern as the existing image implementation.

## Files Created/Modified

### New Files
1. **`src/components/ui/tiptap-extensions/InteractiveAudioResize.js`** (600 lines)
   - Custom TipTap node extension for audio elements
   - Horizontal-only resizing (left/right handles)
   - Drag-and-drop repositioning with ghost preview
   - Alignment support (left, right, center, full)
   - Styled wrapper with purple gradient background
   - Music icon and filename display

2. **`src/components/ui/tiptap-extensions/InteractiveVideoResize.js`** (600 lines)
   - Custom TipTap node extension for video elements
   - Full 2D resizing with aspect ratio maintenance
   - 8 resize handles (corners + edges)
   - Drag-and-drop repositioning with ghost preview
   - Alignment support (left, right, center, full)
   - Video player with controls

### Modified Files
1. **`src/components/ui/RichTextEditor.jsx`**
   - Added imports for InteractiveAudioResize and InteractiveVideoResize
   - Registered both extensions in the extensions array
   - Added comprehensive CSS styles for audio and video containers

## Features Implemented

### Audio Features
- **Interactive Resize**: Horizontal resizing only (minimum width: 200px)
- **Drag & Drop**: Smooth drag with ghost preview and alignment zones
- **Alignment Options**: Left (float), Right (float), Center (margin auto), Full (100% width)
- **Visual Design**: Purple gradient wrapper with music icon and filename
- **Controls**: Audio player with native HTML5 controls

### Video Features
- **Interactive Resize**: Both dimensions with aspect ratio maintenance (minimum: 200x112px)
- **Drag & Drop**: Smooth drag with ghost preview and alignment zones
- **Alignment Options**: Left, Right, Center, Full width
- **Visual Design**: Rounded corners with video player controls
- **Controls**: Video player with native HTML5 controls

## How It Works

### Node Structure

#### Audio Node
```javascript
{
  name: 'interactiveAudio',
  group: 'block',
  draggable: true,
  attributes: {
    src: 'audio URL',
    style: 'CSS styles (width, margin, etc.)',
    class: 'alignment classes',
    title: 'filename'
  }
}
```

#### Video Node
```javascript
{
  name: 'interactiveVideo',
  group: 'block',
  draggable: true,
  attributes: {
    src: 'video URL',
    style: 'CSS styles (width, height, margin, etc.)',
    class: 'alignment classes',
    title: 'filename',
    poster: 'thumbnail URL (optional)'
  }
}
```

### Resizing Logic

#### Audio (Horizontal Only)
- West handle: Decreases width from left edge
- East handle: Increases width from right edge
- Minimum width: 200px
- Updates `style` attribute with `width: XXXpx !important`

#### Video (Both Dimensions)
- 8 handles: nw, ne, sw, se, n, s, w, e
- Corner handles: Maintain aspect ratio
- Edge handles: Resize in one direction while maintaining aspect ratio
- Minimum: 200px width, 112px height (16:9 ratio)
- Updates `style` with both `width` and `height`

### Drag-and-Drop Logic

1. **Start Drag**: User clicks drag handle (✥ symbol)
2. **Create Ghost**: Clone element follows cursor with dashed border
3. **Calculate Alignment**: On drop, calculate X position relative to editor
   - X < 25% of editor width → Align left
   - X > 75% of editor width → Align right
   - X in middle → Align center
4. **Update Node**: Set alignment class and style attributes

### Alignment Styles

#### Audio
- **Left**: `display: inline-block; margin: 0.75rem auto 0.75rem 0; max-width: 40-50%;`
- **Right**: `display: inline-block; margin: 0.75rem 0 0.75rem auto; max-width: 40-50%;`
- **Center**: `float: none; display: block; margin: 0.5rem auto; max-width: 100%;`
- **Full**: `display: block; width: 100%; max-width: 100%;`

#### Video
- **Left**: `display: inline-block; margin: 0.75rem auto 0.75rem 0; max-width: 50%;`
- **Right**: `display: inline-block; margin: 0.75rem 0 0.75rem auto; max-width: 50%;`
- **Center**: `float: none; display: block; margin: 0.5rem auto;`
- **Full**: `display: block; width: 100%; max-width: 100%;`

## Usage

### Upload Audio
1. User clicks audio upload button (existing `handleAudioUpload` function)
2. File is validated (duration check, file type)
3. Placeholder inserted into content with `data-media-id`
4. On submit, `processContentForSubmission` uploads file and replaces placeholder

### Upload Video
1. User clicks video upload button (existing `handleVideoUpload` function)
2. File is validated (duration check, file type)
3. Placeholder inserted into content with `data-media-id`
4. On submit, `processContentForSubmission` uploads file and replaces placeholder

### Resize
1. Hover over audio/video container
2. Resize handles appear (2 for audio, 8 for video)
3. Click and drag handle to resize
4. Release to finalize size
5. Size stored in node's `style` attribute

### Align
1. Hover over audio/video container
2. Click and drag the drag handle (✥)
3. Ghost element follows cursor
4. Drop in left/right/center zone
5. Alignment stored in node's `class` and `style` attributes

## CSS Classes

### Audio
- `.interactive-audio-container` - Main container
- `.audio-wrapper` - Styled wrapper with gradient
- `.audio-left` - Float left alignment
- `.audio-right` - Float right alignment
- `.audio-center` - Center alignment
- `.audio-full` - Full width
- `.has-explicit-size` - Indicates manually resized

### Video
- `.interactive-video-container` - Main container
- `.video-left` - Left alignment
- `.video-right` - Right alignment
- `.video-center` - Center alignment
- `.video-full` - Full width
- `.has-explicit-size` - Indicates manually resized

## Integration with Existing Media Upload System

Both extensions integrate seamlessly with the existing media upload system:

1. **File Selection**: Use existing `handleAudioUpload()` and `handleVideoUpload()` functions
2. **Placeholder System**: Use `insertMediaPlaceholder()` with `data-media-id` tracking
3. **Upload & Replace**: `processContentForSubmission()` handles upload and URL replacement
4. **State Management**: `mediaAttachments` array tracks all uploaded media

## Testing Checklist

- [ ] Audio upload works correctly
- [ ] Audio player displays and plays audio
- [ ] Audio horizontal resize works (min 200px)
- [ ] Audio drag-drop repositioning works
- [ ] Audio alignment (left, right, center, full) works
- [ ] Video upload works correctly
- [ ] Video player displays and plays video
- [ ] Video 2D resize works (aspect ratio maintained)
- [ ] Video drag-drop repositioning works
- [ ] Video alignment (left, right, center, full) works
- [ ] Placeholder replacement works on submit
- [ ] Multiple audio/video elements can coexist
- [ ] Undo/redo works correctly
- [ ] Content saves and loads correctly

## Future Enhancements

Potential improvements for future versions:

1. **Alignment Toolbar Buttons**: Add dedicated alignment buttons (like for images)
2. **Custom Poster Images**: Allow custom video thumbnails
3. **Audio Waveform**: Display audio waveform visualization
4. **Playback Speed**: Add speed control for audio/video
5. **Captions/Subtitles**: Support for video subtitles
6. **Playlist**: Support for multiple audio files in sequence
7. **Volume Control**: Enhanced volume control UI
8. **Download Button**: Allow users to download media

## Pattern Consistency

This implementation follows the exact pattern established by `InteractiveImageResize`:

✅ Same container structure (container → media element → drag handle → resize overlay → handles)
✅ Same drag-drop logic with ghost preview
✅ Same alignment calculation zones
✅ Same style/class attribute management
✅ Same hover effects and visual feedback
✅ Same integration with TipTap editor state
✅ Same CSS organization and naming conventions

## Credits

Implementation based on the `InteractiveImageResize` extension pattern created for the citinfos_backend project.
