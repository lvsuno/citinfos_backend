# Enhanced RichTextEditor

## New Features

### Table Manipulation
When working with tables in the editor, a dropdown menu appears next to the table insert button with organized submenus:

**Row Operations** (submenu):
- **Add Above** - Insert a new row above the current row
- **Add Below** - Insert a new row below the current row
- **Delete Row** - Remove the current row

**Column Operations** (submenu):
- **Add Left** - Insert a new column to the left of current column
- **Add Right** - Insert a new column to the right of current column
- **Delete Column** - Remove the current column

## 🔍 **Menu Structure:**
```
📊 Table Actions ▼
├── Row Operations ▶
│   ├── ↑ Add Above
│   ├── ↓ Add Below
│   └── 🗑️ Delete Row
├── Column Operations ▶
│   ├── ← Add Left
│   ├── → Add Right
│   └── 🗑️ Delete Column
├── ─── (separator) ───
└── 🗑️ Delete Table
```
- **Delete Table** - Remove the entire table

Each operation category has its own submenu that expands to the right, keeping the interface clean and organized. The dropdown and submenus automatically close when you click outside or leave the table.

### Media Upload
The editor now supports uploading and embedding media files:

- **Upload Image** (☁️) - Upload image files and embed them
- **Upload Video** (📹) - Upload video files and embed them with controls
- **Upload Audio** (🔊) - Upload audio files and embed them with controls
- **Insert Image URL** (🖼️) - Insert image from URL (existing feature)

## Usage

### Basic Usage
```jsx
import RichTextEditor from './ui/RichTextEditor';

<RichTextEditor
  content={content}
  onChange={handleContentChange}
  placeholder="Start typing..."
  maxLength={2000}
  height="h-40"
/>
```

### With Media Upload
```jsx
const handleImageUpload = async (file) => {
  const formData = new FormData();
  formData.append('image', file);

  const response = await fetch('/api/upload/image', {
    method: 'POST',
    body: formData,
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const result = await response.json();
  return result.imageUrl;
};

const handleVideoUpload = async (file) => {
  // Similar implementation for video
  const formData = new FormData();
  formData.append('video', file);

  const response = await fetch('/api/upload/video', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  return result.videoUrl;
};

const handleAudioUpload = async (file) => {
  // Similar implementation for audio
  const formData = new FormData();
  formData.append('audio', file);

  const response = await fetch('/api/upload/audio', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  return result.audioUrl;
};

<RichTextEditor
  content={content}
  onChange={handleContentChange}
  onImageUpload={handleImageUpload}
  onVideoUpload={handleVideoUpload}
  onAudioUpload={handleAudioUpload}
  enableAdvancedFeatures={true}
/>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `content` | string | `''` | Initial content of the editor |
| `onChange` | function | - | Callback when content changes |
| `placeholder` | string | `'Start typing...'` | Placeholder text |
| `maxLength` | number | `1000` | Maximum character count |
| `className` | string | `''` | Additional CSS classes |
| `height` | string | `'h-32'` | Editor height class |
| `showToolbar` | boolean | `true` | Whether to show the toolbar |
| `editable` | boolean | `true` | Whether the editor is editable |
| `enableAdvancedFeatures` | boolean | `true` | Enable tables, images, etc. |
| `enableMentions` | boolean | `true` | Enable @mentions and #hashtags |
| `mentionSuggestions` | array | `[]` | Array of mention suggestions |
| `hashtagSuggestions` | array | `[]` | Array of hashtag suggestions |
| `onImageUpload` | function | - | Async function to handle image uploads |
| `onVideoUpload` | function | - | Async function to handle video uploads |
| `onAudioUpload` | function | - | Async function to handle audio uploads |

## Media Upload Handler Signature

```typescript
type MediaUploadHandler = (file: File) => Promise<string>;
```

The upload handlers should:
1. Accept a `File` object
2. Upload the file to your server/storage
3. Return a Promise that resolves to the public URL of the uploaded file

## Fallback Behavior

If no upload handler is provided, the editor will:
- For images: Create a local blob URL for preview
- For video/audio: Create a local blob URL and embed with controls

Note: Local blob URLs will not persist after page refresh and should only be used for testing.

## Table Controls

Table controls are organized in a hierarchical dropdown menu system that automatically appears when the cursor is inside a table. The menu has:

1. **Main Dropdown** - Appears when clicking the table button with chevron
2. **Row Operations Submenu** - Expands to the right showing row actions
3. **Column Operations Submenu** - Expands to the right showing column actions
4. **Direct Table Actions** - Delete table (no submenu needed)

**Smart Behavior:**
- Submenus expand to the right to avoid clipping
- Only one submenu can be open at a time
- Right chevron icons (▶) indicate expandable submenus
- All menus auto-close when:
  - Clicking outside the dropdown
  - Selecting an action
  - Moving the cursor outside the table
  - Editor loses focus

This hierarchical structure keeps the interface clean while providing quick access to all table manipulation features.

## Styling

The editor includes comprehensive CSS for all media types:
- Images: Responsive with rounded corners
- Videos: Responsive with controls, rounded corners
- Audio: Full width with controls
- Tables: Proper borders and spacing

All media is constrained to the editor width and maintains aspect ratios.