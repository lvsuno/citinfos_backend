# Post Creation Modal - UX Redesign Proposal

## Current Problems

### 1. **Too Many Options Visible at Once**
- Mode selector (Post vs Thread)
- Community selector/indicator
- Thread selector (optional)
- Content type selector (Article, Poll, Media)
- Rich text editor OR poll inputs OR media uploader
- Visibility selector
- Submit buttons

**Result**: Overwhelming, confusing, hard to focus on actual content creation.

### 2. **Poor Progressive Disclosure**
- All options shown upfront
- No clear workflow or steps
- User must understand entire modal before starting

### 3. **Mixed Contexts**
- Thread creation mixed with post creation
- Different content types competing for attention
- No clear visual hierarchy

---

## Proposed Solution: Multi-Step Wizard with Smart Defaults

### **Concept: "Start Simple, Add More"**

Instead of one crowded modal, use a **progressive workflow** that reveals complexity only when needed.

---

## Design Pattern: Tabbed Interface with Smart Defaults

### **Tab 1: Quick Post (Default)**
**90% of users just want to post quickly**

```
┌────────────────────────────────────────────────┐
│  Créer une publication                      ✕  │
├────────────────────────────────────────────────┤
│  Publishing to: 📍 Sherbrooke Community        │
│  [Click to change]                             │
├────────────────────────────────────────────────┤
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │  Quoi de neuf ?                          │ │
│  │                                          │ │
│  │  [Rich text editor - simplified]        │ │
│  │                                          │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  [📷 Photos] [🎬 Video] [📊 Poll] [🎨 Article]│
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │  Advanced Options ▼                      │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│                    [Cancel] [Publier] →       │
└────────────────────────────────────────────────┘
```

**Features:**
- **One text box** for quick posting
- **Icon buttons** to add media/poll/rich article (switches mode)
- **Collapsed advanced options** (visibility, thread selection)
- **Auto-selected community** with easy change option

---

### **Tab 2: Rich Article (When "🎨 Article" clicked)**

```
┌────────────────────────────────────────────────┐
│  Créer un article                           ✕  │
├────────────────────────────────────────────────┤
│  [← Back to quick post]                        │
├────────────────────────────────────────────────┤
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │  [Full TipTap Rich Text Editor]         │ │
│  │  • Headers, lists, quotes                │ │
│  │  • Embed images, video, audio            │ │
│  │  • Code blocks, tables                   │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  Preview mode: [Edit] [Preview]               │
│                                                │
│                    [Cancel] [Publier] →       │
└────────────────────────────────────────────────┘
```

---

### **Tab 3: Create Poll (When "📊 Poll" clicked)**

```
┌────────────────────────────────────────────────┐
│  Créer un sondage                           ✕  │
├────────────────────────────────────────────────┤
│  [← Back to quick post]                        │
├────────────────────────────────────────────────┤
│                                                │
│  Question:                                     │
│  ┌──────────────────────────────────────────┐ │
│  │  Quelle est votre question ?             │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  Options:                                      │
│  ┌──────────────────────────────────────────┐ │
│  │  Option 1                             ✕  │ │
│  ├──────────────────────────────────────────┤ │
│  │  Option 2                             ✕  │ │
│  ├──────────────────────────────────────────┤ │
│  │  + Ajouter une option                    │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  ☐ Allow multiple votes                       │
│  Duration: [24 hours ▼]                       │
│                                                │
│                    [Cancel] [Publier] →       │
└────────────────────────────────────────────────┘
```

---

### **Thread Creation: Separate Modal**

**Instead of mixing thread creation in post modal:**

```
┌────────────────────────────────────────────────┐
│  Nouveau sujet de discussion                ✕  │
├────────────────────────────────────────────────┤
│                                                │
│  Titre du sujet:                               │
│  ┌──────────────────────────────────────────┐ │
│  │                                          │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  Description:                                  │
│  ┌──────────────────────────────────────────┐ │
│  │                                          │ │
│  │                                          │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  ☑ Create with first post                     │
│                                                │
│           [Cancel] [Create Thread] →          │
└────────────────────────────────────────────────┘
```

**Then**: Opens post modal if "Create with first post" is checked.

---

## Implementation Strategy

### **Phase 1: Simplify Existing Modal (Quick Win)**

1. **Hide Thread Creation** - Separate button/modal
2. **Default to "Quick Post"** - Simple textarea
3. **Collapse Advanced Options** - Accordion for visibility, thread selection
4. **Content Type as Actions** - Buttons that switch modes, not checkboxes

### **Phase 2: Progressive Enhancement**

1. **Add Preview Mode** for rich articles
2. **Drag-and-drop** for media
3. **Inline Media Preview** with delete buttons
4. **Auto-save Drafts** to localStorage

### **Phase 3: Advanced Features**

1. **Scheduled Posts** (future posting)
2. **Post Templates** (save common formats)
3. **AI Assist** (writing suggestions)
4. **Multi-image Carousel** creator

---

## Visual Hierarchy Improvements

### **Current Issue:**
Everything has equal visual weight - hard to know what to do first.

### **Proposed Fix:**

1. **Primary Action**: Text editor (largest, most prominent)
2. **Secondary Actions**: Media/poll/article buttons (icons, subtle)
3. **Tertiary Options**: Advanced settings (collapsed by default)
4. **Context Info**: Community/thread (info box, not selector)

---

## Specific UX Improvements

### 1. **Smart Content Type Detection**

```javascript
// Auto-detect content type based on user action:
- User types text → Text post
- User uploads image → Image post
- User clicks poll → Poll creation
- User clicks article → Rich editor

// No need to explicitly "choose" type
```

### 2. **Contextual Toolbars**

```javascript
// Show relevant options based on mode:
Quick Post: [B] [I] [Link] [Emoji]
Rich Article: [Full TipTap toolbar]
Poll: [Add option] [Settings]
Media: [Upload more] [Edit] [Reorder]
```

### 3. **Inline Validation**

```javascript
// Show errors next to fields, not in a summary:
✗ Poll needs at least 2 options
✗ Community required
✓ Post looks good!
```

### 4. **One-Click Actions**

```javascript
// Common actions should be ONE click:
- Upload photo → file picker opens
- Create poll → poll form appears
- Post → submits with smart defaults
```

---

## Mobile Considerations

### **Current Modal**: Doesn't work well on mobile (too tall, scrolling issues)

### **Proposed Solution**: Bottom Sheet on Mobile

```
┌────────────────────────────┐
│                            │
│                            │
│  [Tap to dismiss]          │
│                            │
│                            │
├────────────────────────────┤ ← Slides up from bottom
│  Quoi de neuf ?            │
│  ┌──────────────────────┐  │
│  │                      │  │
│  └──────────────────────┘  │
│  [📷] [📊] [🎨]           │
│                [Publier]   │
└────────────────────────────┘
```

---

## Code Structure Proposal

### **New Component Architecture:**

```
PostCreationFlow/
├── QuickPost.jsx          // Simple textarea + media buttons
├── RichArticleEditor.jsx  // Full TipTap editor
├── PollCreator.jsx        // Poll-specific form
├── MediaUploader.jsx      // Drag-drop media handler
├── ThreadCreator.jsx      // Separate thread modal
└── PostCreationModal.jsx  // Orchestrator (simplified)
```

### **Benefits:**
- **Separation of concerns**: Each mode is isolated
- **Easier testing**: Test each mode independently
- **Code reuse**: Components can be used elsewhere
- **Performance**: Lazy load heavy components (TipTap, media uploader)

---

## User Flow Comparison

### **Current (Confusing):**
```
1. Open modal
2. See 10+ options
3. Wonder what to do
4. Select community
5. Choose mode
6. Select content type
7. Fill in content
8. Remember to set visibility
9. Submit
```

### **Proposed (Clear):**
```
1. Open modal → Focus on text box
2. Start typing OR click media/poll/article
3. Content interface appears
4. Submit (smart defaults applied)

Advanced users:
5. Click "Advanced" if needed
6. Adjust community/thread/visibility
```

---

## Key Principles

### **1. Progressive Disclosure**
Don't show options until they're needed.

### **2. Smart Defaults**
Most users want: public post, in current community, simple text.

### **3. Forgiveness Over Permission**
Let users start creating, validate later (not upfront).

### **4. Context-Aware UI**
Show relevant options based on what user is doing.

### **5. Mobile-First**
Design for small screens, enhance for desktop.

---

## Recommended Approach

### **Option A: Gradual Migration (Safer)**
1. Clean up existing modal (remove clutter)
2. Add tabbed interface for content types
3. Separate thread creation
4. Test with users
5. Iterate based on feedback

### **Option B: Fresh Start (Better UX)**
1. Build new simplified QuickPost component
2. Build dedicated RichArticleEditor
3. Build separate PollCreator
4. Launch as "New Post Experience" (beta flag)
5. Migrate users gradually

---

## Success Metrics

### **How to measure improvement:**
- ✅ **Time to first post**: Should decrease by 50%
- ✅ **Completion rate**: Users who open modal actually post
- ✅ **Error rate**: Fewer validation errors
- ✅ **User satisfaction**: Survey responses
- ✅ **Feature adoption**: More rich articles, polls created

---

## Immediate Action Items

### **Quick Wins (This Week):**
1. ✅ Remove thread creation from post modal
2. ✅ Hide advanced options by default (accordion)
3. ✅ Make community selector read-only (show change button)
4. ✅ Content type as action buttons (not radio/checkboxes)

### **Short Term (Next Week):**
1. ✅ Separate ThreadCreator modal
2. ✅ Add QuickPost mode (default)
3. ✅ Lazy load TipTap for rich articles
4. ✅ Improve mobile layout (bottom sheet)

### **Medium Term (2-4 Weeks):**
1. ✅ Preview mode for articles
2. ✅ Drag-drop media uploader
3. ✅ Auto-save drafts
4. ✅ Better validation UX

---

## Questions for Consideration

1. **Should thread creation be completely separate?** ✅ Yes (clearer UX)
2. **Is rich article editor needed by default?** ❌ No (progressive)
3. **Can we auto-detect post type?** ✅ Yes (based on content)
4. **Should visibility default to public?** ✅ Yes (most common)
5. **Mobile experience - bottom sheet or modal?** ✅ Bottom sheet

---

## Recommendation

**Start with Option A (Gradual Migration):**

### **Phase 1 (This Sprint):**
- Separate thread creation
- Simplify post modal to "Quick Post" default
- Content type switcher buttons
- Collapse advanced options

### **Phase 2 (Next Sprint):**
- Build dedicated article editor view
- Improve poll creator UI
- Add media upload preview

### **Phase 3 (Future):**
- Mobile-optimized bottom sheet
- Auto-save drafts
- Post templates

**Expected Impact:**
- 50% faster post creation
- 30% more posts completed (less abandonment)
- 20% more rich content (articles, polls)
- Better mobile experience

---

## Visual Mockup (ASCII)

### **Simplified Modal (Default State):**

```
┌─────────────────────────────────────────────────────────┐
│  Créer une publication                               ✕  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📍 Sherbrooke Community  [Change]                     │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Quoi de neuf ?                                   │ │
│  │  _______________________________________________  │ │
│  │                                                   │ │
│  │                                                   │ │
│  │  [B] [I] [Link] 😊                               │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Quick add:                                             │
│  [📷 Photo] [🎬 Video] [📊 Poll] [🎨 Rich Article]    │
│                                                         │
│  ▼ More options (visibility, thread, etc.)            │
│                                                         │
│                              [Cancel] [Post] →         │
└─────────────────────────────────────────────────────────┘
```

**Clean, focused, actionable.**

