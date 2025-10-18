# Emoji Reaction System - UX Guide

## Overview
This document describes the two-level emoji reaction system implemented for posts and comments in the Citinfos social platform.

## User Interface Pattern

### Like Button Design
- **Default State**: Thumbs-up outline icon (👍)
- **Liked State**: Filled thumbs-up icon (blue)
- **Reacted State**: Shows the selected emoji (❤️, 😂, etc.)

### Two-Level Reaction Flow

#### Level 1: Quick Reaction Bar
When users click the like button, a quick reaction bar appears above the button with:
- **5 Popular Reactions**:
  - 👍 Like
  - ❤️ Love
  - 😂 Haha
  - 😮 Wow
  - 😢 Sad
- **"+" Button**: Opens the full emoji grid

**Design**:
- Horizontal row layout
- Rounded-full container with shadow
- Appears above the like button
- White background with border
- Hover effects on emoji buttons

#### Level 2: Full Reaction Grid
When users click the "+" button, the full grid appears with:
- **22 Total Emojis** organized by sentiment
- **3 Tabs**:
  - **Positive** (14 emojis): like, love, care, haha, wow, yay, celebrate, clap, strong, party, heart_eyes, fire, star, cool
  - **Negative** (4 emojis): sad, angry, cry, pouting
  - **Neutral** (4 emojis): thinking, confused, surprise, shrug

**Design**:
- Grid layout (5 columns)
- Tabs for sentiment categories
- Larger emoji display
- Same positioning as quick bar

## Technical Implementation

### Components Updated

#### 1. ReactionPicker.jsx
**Purpose**: Reusable emoji picker with two display modes

**Key Features**:
```javascript
// Two modes
mode: 'quick' | 'full'

// Quick reactions helper
getQuickReactions() // Returns 5 popular reactions

// Mode switching
onShowMore() // Callback to switch from quick to full
```

**Props**:
- `mode`: Display mode ('quick' or 'full')
- `onShowMore`: Callback when user clicks "+" button
- `onReact`: Callback when reaction selected
- `onClose`: Callback to close picker
- `currentReaction`: User's current reaction
- `position`: { top, left } for positioning

#### 2. PostActionBar.jsx
**Purpose**: Action buttons for posts (like, comment, share, repost)

**Reaction Button**:
```jsx
// State
const [pickerMode, setPickerMode] = useState('quick');

// Click handler
const handleLikeClick = (e) => {
  // Position above button
  const rect = e.currentTarget.getBoundingClientRect();
  setReactionPickerPosition({
    top: rect.top - 60 + window.scrollY,
    left: rect.left + window.scrollX
  });
  setPickerMode('quick'); // Start with quick bar
  setShowReactionPicker(true);
};

// Mode switcher
const handleShowMore = () => {
  setPickerMode('full'); // Switch to full grid
};
```

**Button Display**:
- Shows emoji when user has reacted with non-like reaction
- Shows filled thumbs-up when user liked
- Shows outline thumbs-up when not reacted

#### 3. PostCommentThread.jsx
**Purpose**: Comment thread with nested replies

**Implementation**: Same pattern as PostActionBar
- Like button for each comment/reply
- Quick bar → Full grid flow
- Position picker above clicked button
- State management per comment

### API Integration

**Endpoints**:
- `POST /api/social/posts/{id}/react/` - React to post
- `DELETE /api/social/posts/{id}/unreact/` - Remove reaction
- `POST /api/social/comments/{id}/react/` - React to comment
- `DELETE /api/social/comments/{id}/unreact/` - Remove reaction

**Request Body**:
```json
{
  "reaction_type": "like" | "love" | "haha" | ... (22 types)
}
```

**Response**:
```json
{
  "reaction_id": 123,
  "reaction_type": "love",
  "user": {...},
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Reaction Types

### All 22 Reaction Types
```javascript
// POSITIVE (14)
like, love, care, haha, wow, yay, celebrate, clap,
strong, party, heart_eyes, fire, star, cool

// NEGATIVE (4)
sad, angry, cry, pouting

// NEUTRAL (4)
thinking, confused, surprise, shrug
```

### Quick Reactions (5)
The 5 most popular reactions shown in the quick bar:
1. 👍 like
2. ❤️ love
3. 😂 haha
4. 😮 wow
5. 😢 sad

## User Experience Flow

### Adding a Reaction
1. User sees like button (👍 outline)
2. User clicks like button
3. Quick reaction bar appears above button (5 emojis + "+")
4. User can:
   - Click one of the 5 quick reactions → Reaction applied immediately
   - Click "+" → Full grid appears with all 22 reactions
5. Selected reaction appears on button

### Changing a Reaction
1. User clicks button showing current reaction
2. Quick bar appears (current reaction highlighted)
3. User selects new reaction or clicks "+" for more options
4. Button updates to show new reaction

### Removing a Reaction
1. User clicks button showing current reaction
2. Quick bar appears (current reaction highlighted)
3. User clicks the same highlighted reaction
4. Reaction removed, button returns to outline thumbs-up

## Design Decisions

### Why Like Button (Not Three Dots)?
- **Three dots** reserved for other actions (edit, delete, share)
- **Like button** is more familiar and discoverable
- Follows Facebook/LinkedIn UX patterns
- Clear affordance for reaction system

### Why Two-Level System?
- **Quick bar**: Fast access to most common reactions
- **Full grid**: Complete selection without overwhelming UI
- **Progressive disclosure**: Show simple first, reveal complex on demand
- **Mobile-friendly**: Fewer taps for common actions

### Positioning Strategy
- **Above button**: Prevents picker from being cut off at bottom of viewport
- **Aligned to button**: Clear visual connection between trigger and picker
- **Fixed position**: Stays in place when scrolling
- **Z-index management**: Appears above all other content

## Accessibility

- **Keyboard navigation**: Tab through reactions
- **ARIA labels**: Descriptive labels for screen readers
- **Focus management**: Returns focus to button after selection
- **Visual feedback**: Hover states and current selection highlighting

## Performance

- **Lazy loading**: Picker only renders when opened
- **Optimistic updates**: UI updates immediately, API call in background
- **Debouncing**: Prevents rapid clicking
- **Memoization**: getQuickReactions() cached

## Future Enhancements

### Potential Improvements
- Reaction counts by type (show breakdown on hover)
- Animated reactions (emoji pop when selected)
- Custom reactions (user-uploaded emojis)
- Reaction history (see who reacted with what)
- Keyboard shortcuts (press 1-5 for quick reactions)
- Recent reactions (personalized quick bar)

### Known Limitations
- Mobile touch handling (may need gesture improvements)
- Accessibility (keyboard navigation could be enhanced)
- Performance with many reactions (pagination needed)

## Testing

### Manual Testing Checklist
- [ ] Click like button → Quick bar appears
- [ ] Click "+" → Full grid appears
- [ ] Select reaction → Button shows emoji
- [ ] Click reacted button → Quick bar highlights current reaction
- [ ] Select different reaction → Button updates
- [ ] Click same reaction → Reaction removed
- [ ] Test on posts and comments
- [ ] Test on nested replies
- [ ] Test with different screen sizes
- [ ] Test with many reactions (count updates)

### Edge Cases
- User reacts while offline
- Multiple rapid clicks
- React while picker is open
- React then immediately unreact
- Page refresh with existing reactions

## Developer Notes

### Key Files
- `src/components/social/ReactionPicker.jsx` - Picker component
- `src/components/social/PostActionBar.jsx` - Post reactions
- `src/components/social/PostCommentThread.jsx` - Comment reactions
- `src/hooks/usePostInteractions.js` - API integration
- `src/services/api/social-api.js` - API endpoints

### State Management
- Local component state for picker visibility
- Mode state ('quick' | 'full') for picker display
- Position state for absolute positioning
- Current reaction from backend via API

### CSS Classes
- `rounded-full` - Quick bar container
- `hover:bg-gray-100` - Reaction hover state
- `text-blue-600` - Active/selected state
- `shadow-xl` - Picker elevation
- `z-50` - Picker stacking order

---

**Last Updated**: January 2025
**Version**: 2.0 (Two-level system)
**Status**: Implemented and deployed
