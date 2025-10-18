# Emoji Reaction System - UI Guide

## Visual Changes

### Before (Like/Dislike System)
```
┌─────────────────────────────────────────┐
│ 👤 Username                             │
│ This is a post content...               │
│                                         │
│ 👍 15   👎 2   💬 8   🔗 3   🔁 1      │
└─────────────────────────────────────────┘
```

### After (Emoji Reaction System)
```
┌─────────────────────────────────────────┐
│ 👤 Username                             │
│ This is a post content...               │
│                                         │
│ ⋯ 15   💬 8   🔗 3   🔁 1              │
└─────────────────────────────────────────┘
```

**When user reacts:**
```
┌─────────────────────────────────────────┐
│ 👤 Username                             │
│ This is a post content...               │
│                                         │
│ ❤️ 15   💬 8   🔗 3   🔁 1             │
└─────────────────────────────────────────┘
```

## Reaction Picker UI

### Picker Appearance (Click three dots)
```
┌───────────────────────────────────────────────┐
│ 😊 Positive | 😔 Negative | 🤷 Neutral      ✕ │
├───────────────────────────────────────────────┤
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    │
│ │ 👍  │ │ ❤️  │ │ 🤗  │ │ 😂  │ │ 😮  │    │
│ │Like │ │Love │ │Care │ │Haha │ │ Wow │    │
│ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘    │
│                                               │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    │
│ │ 🎉  │ │ 👏  │ │ 🔥  │ │ ⭐  │ │ 🥳  │    │
│ │ Yay │ │Clap │ │Fire │ │Star │ │Party│    │
│ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘    │
│                                               │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐            │
│ │ 😍  │ │ 🙏  │ │ 💪  │ │ 🎊  │            │
│ │Heart│ │Pray │ │Strong│Celebrate           │
│ └─────┘ └─────┘ └─────┘ └─────┘            │
├───────────────────────────────────────────────┤
│        [ Remove Reaction ]                    │
└───────────────────────────────────────────────┘
```

### Negative Tab
```
┌───────────────────────────────────────────────┐
│ 😊 Positive | 😔 Negative | 🤷 Neutral      ✕ │
├───────────────────────────────────────────────┤
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐            │
│ │ 😢  │ │ 😠  │ │ 😟  │ │ 😞  │            │
│ │ Sad │ │Angry│Worried│Disappointed          │
│ └─────┘ └─────┘ └─────┘ └─────┘            │
└───────────────────────────────────────────────┘
```

### Neutral Tab
```
┌───────────────────────────────────────────────┐
│ 😊 Positive | 😔 Negative | 🤷 Neutral      ✕ │
├───────────────────────────────────────────────┤
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐            │
│ │ 🤔  │ │ 🧐  │ │ 😲  │ │ 😕  │            │
│ │Think│Curious│Shock │Confused              │
│ └─────┘ └─────┘ └─────┘ └─────┘            │
└───────────────────────────────────────────────┘
```

## Interaction Flow

### 1. User sees three-dot button
```
⋯ 15
```

### 2. User clicks → Picker opens
```
⋯ 15  ← Click here
  ↓
  📋 Picker appears
```

### 3. User selects emoji (e.g., Love)
```
Picker: ❤️ (highlighted with indigo ring)
         ↓
      API call
         ↓
    Button updates
```

### 4. Button shows selected emoji
```
❤️ 16  (count incremented)
```

### 5. User clicks again → Can change or remove
```
❤️ 16  ← Click again
  ↓
  📋 Picker opens (Love is selected)

Options:
- Click 😂 → Changes to Haha
- Click ❤️ again → Removes reaction
- Click "Remove Reaction" → Removes reaction
```

## Comment Reactions

### Before
```
  💬 @username
     Comment text here
     [Edit] [Delete] [Reply] 👍 5 👎 1
```

### After
```
  💬 @username
     Comment text here
     [Edit] [Delete] [Reply] ⋯ 5
```

### When reacted
```
  💬 @username
     Comment text here
     [Edit] [Delete] [Reply] 🔥 5
```

## Color Coding

### Reaction States
- **Not reacted:** Gray three-dot icon + gray count
- **Reacted:** Emoji + indigo count `text-indigo-600`
- **Hover:** Button scales to 110%
- **Active (click):** Button scales to 95%

### Picker States
- **Not selected:** Light gray background `bg-gray-50`
- **Selected:** Indigo background `bg-indigo-100` + ring `ring-2 ring-indigo-500`
- **Hover:** Light indigo `bg-indigo-50` + scale 110%

## Responsive Design

### Desktop (Full Size)
- Picker width: 320px (w-80)
- Grid: 5 columns
- Emoji size: text-2xl
- Label size: text-[9px]

### Mobile (Auto-adjusts)
- Picker width: 80vw (max 320px)
- Grid: Still 5 columns (scrollable if needed)
- Touch-friendly buttons: min 44x44px

## Accessibility

### Keyboard Support
- **Escape:** Close picker
- **Tab:** Navigate through reactions
- **Enter/Space:** Select reaction
- **Arrow keys:** Navigate grid (future enhancement)

### Screen Readers
- All buttons have `aria-label`
- Picker has `role="dialog"`
- Current reaction announced
- Count updates announced

## Animation Timing

### Picker Appearance
- **Duration:** 200ms
- **Effect:** Fade-in + slide-in from bottom
- **Easing:** ease-out

### Button Hover
- **Duration:** 150ms
- **Effect:** Scale + color change
- **Easing:** ease-in-out

### Selection Feedback
- **Duration:** 100ms
- **Effect:** Scale down (active state)
- **Easing:** ease-in-out

## Technical Classes

### Three-Dot Button
```jsx
className="flex items-center gap-1"
```
- Not reacted: `text-gray-600`
- Reacted: `text-indigo-600`
- Hover: `hover:text-indigo-600`

### Emoji Display
```jsx
reactionEmoji ? (
  <span className="text-lg">{reactionEmoji}</span>
) : (
  <EllipsisHorizontalIcon className="h-5 w-5" />
)
```

### Reaction Picker
```jsx
className="bg-white rounded-lg shadow-xl border border-gray-200 w-80"
```

### Tab Buttons
```jsx
// Active tab
className="bg-white text-indigo-600 border-b-2 border-indigo-600"

// Inactive tab
className="bg-gray-100 text-gray-600 hover:bg-gray-200"
```

### Reaction Buttons in Picker
```jsx
// Not selected
className="flex flex-col items-center gap-1 p-2 rounded-lg bg-gray-50 hover:bg-indigo-50 hover:scale-110 active:scale-95"

// Selected
className="flex flex-col items-center gap-1 p-2 rounded-lg bg-indigo-100 ring-2 ring-indigo-500 hover:scale-110 active:scale-95"
```

## API Response Example

### React to Post
```json
// POST /content/posts/{id}/react/
// Body: { "reaction_type": "love" }

{
  "message": "Reacted with love",
  "post": {
    "id": "abc123",
    "user_reaction": "love",
    "likes_count": 16,
    "dislikes_count": 2,
    "comments_count": 8,
    ...
  }
}
```

### Unreact from Post
```json
// POST /content/posts/{id}/unreact/

{
  "message": "Reaction removed",
  "post": {
    "id": "abc123",
    "user_reaction": null,
    "likes_count": 15,
    "dislikes_count": 2,
    "comments_count": 8,
    ...
  }
}
```

## Usage Examples

### Basic Usage
```jsx
import ReactionPicker, { getReactionEmoji } from './ReactionPicker';

// In your component
const [showPicker, setShowPicker] = useState(false);
const currentReaction = post.user_reaction; // 'love', 'haha', etc.

<button onClick={() => setShowPicker(true)}>
  {currentReaction ? (
    <span>{getReactionEmoji(currentReaction)}</span>
  ) : (
    <EllipsisHorizontalIcon />
  )}
</button>

{showPicker && (
  <ReactionPicker
    onReact={(type) => handleReact(type)}
    onClose={() => setShowPicker(false)}
    currentReaction={currentReaction}
  />
)}
```

### With Position
```jsx
const [position, setPosition] = useState({ top: 0, left: 0 });

const handleClick = (e) => {
  const rect = e.currentTarget.getBoundingClientRect();
  setPosition({
    top: rect.bottom + 4 + window.scrollY,
    left: rect.left + window.scrollX
  });
  setShowPicker(true);
};

<ReactionPicker
  position={position}
  // ... other props
/>
```

---

## Summary

✅ **Clean, modern UI** with three-dot button
✅ **22 emoji reactions** organized by sentiment
✅ **Smooth animations** and transitions
✅ **Mobile-friendly** touch targets
✅ **Accessible** keyboard navigation
✅ **Professional look** matches modern social platforms

The new system is more expressive while maintaining simplicity! 🎉
