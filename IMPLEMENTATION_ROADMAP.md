# Implementation Roadmap - Post Creation UX Redesign

## 🎯 Overview

Complete redesign of post creation UX from modal-based to inline-based system with progressive enhancement.

**Status:** Phase 1 Complete ✅

---

## 📅 Phase Timeline

### Phase 1: Foundation ✅ (Completed)
**Duration:** Week 1
**Status:** ✅ Complete

**Deliverables:**
- [x] InlinePostCreator component
- [x] RichTextEditor inline mode
- [x] Collapsed/Expanded states
- [x] Basic UI structure
- [x] Auto-context props

**Files Created:**
- `src/components/InlinePostCreator.jsx` (469 lines)

**Files Modified:**
- `src/components/ui/RichTextEditor.jsx` (inline mode support)

---

### Phase 2: Advanced Modals (Current)
**Duration:** Week 2
**Status:** 🔄 Not Started

**Tasks:**

#### 1. Create RichArticleModal (2-3 hours)
```jsx
src/components/modals/RichArticleModal.jsx

Features:
- Full TipTap editor (all features)
- Preview mode toggle
- Auto-save to localStorage
- Section/division auto-context
- Media embed inline (images, videos, audio)
- Submit to API

Props:
{
  isOpen: boolean
  onClose: () => void
  division: object
  section: string
  onSubmit: (articleData) => Promise
}
```

#### 2. Create ThreadCreatorModal (2 hours)
```jsx
src/components/modals/ThreadCreatorModal.jsx

Features:
- Thread title input (required)
- Description textarea (optional)
- "Create first post" checkbox
- Redirect to thread view on success
- Validation

Props:
{
  isOpen: boolean
  onClose: () => void
  division: object
  section: string
  onSubmit: (threadData) => Promise
}
```

#### 3. Connect Advanced Dropdown (1 hour)
```jsx
// In InlinePostCreator.jsx

Update handlers:
- handleRichArticle() → open modal
- handleNewThread() → open modal
- Add state: showArticleModal, showThreadModal
- Pass onSubmit callbacks
```

#### 4. Implement Media Upload (2 hours)
```jsx
Features:
- File picker integration
- File validation (type, size)
- Preview generation
- Upload progress
- Multiple file support
- Delete attachments

API Integration:
- POST /api/media/upload/
- Handle blob URLs → server URLs
- Error handling
```

**Deliverables:**
- [ ] RichArticleModal component
- [ ] ThreadCreatorModal component
- [ ] Advanced dropdown logic
- [ ] Media upload system

---

### Phase 3: Integration & API (Week 3)
**Duration:** Week 3
**Status:** ⏳ Pending

**Tasks:**

#### 1. Add to Section Pages (3 hours)
```jsx
// Add InlinePostCreator to:
- pages/ActualitesPage.jsx
- pages/EvenementsPage.jsx
- pages/PetitesAnnoncesPage.jsx

// NOT on:
- pages/AccueilPage.jsx (read-only)
```

#### 2. Auto-Context Detection (2 hours)
```jsx
// Detect from URL/sidebar:
const division = useDivisionContext(); // from sidebar
const section = useRouteSection(); // from URL
const community = await getCommunityFromDivisionSection(division, section);

// Pass to InlinePostCreator:
<InlinePostCreator
  division={division}
  section={section}
  community={community}
  onPostCreated={handlePostCreated}
/>
```

#### 3. API Integration (4 hours)
```jsx
// Implement API calls:

// 1. Post creation
const createPost = async (postData) => {
  const response = await contentAPI.posts.create({
    content: postData.content,
    post_type: determinePostType(postData),
    community: postData.community.id,
    visibility: postData.visibility,
    media: postData.media,
    poll: postData.poll,
  });
  return response;
};

// 2. Media upload
const uploadMedia = async (files) => {
  const uploads = await Promise.all(
    files.map(file => contentAPI.media.upload(file))
  );
  return uploads;
};

// 3. Poll creation
const createPoll = async (pollData) => {
  const response = await contentAPI.polls.create(pollData);
  return response;
};

// 4. Error handling
try {
  // API call
} catch (error) {
  showError(error.message);
  // Rollback if needed
}
```

#### 4. Loading & Error States (2 hours)
```jsx
Features:
- Loading spinner during submission
- Disable form during loading
- Error toast notifications
- Success feedback
- Retry mechanism
- Form persistence on error
```

**Deliverables:**
- [ ] Section page integration
- [ ] Auto-context detection
- [ ] Complete API integration
- [ ] Error handling
- [ ] Loading states

---

### Phase 4: Thread System (Week 3-4)
**Duration:** Week 3-4
**Status:** ⏳ Pending

**Tasks:**

#### 1. Create ThreadView Page (4 hours)
```jsx
src/pages/ThreadView.jsx

Components:
- ThreadHeader (title, creator, stats)
- InlineReplyCreator (similar to InlinePostCreator)
- ThreadPostsList (posts in thread)
- ThreadActions (pin, lock, close)

Route: /division/:divisionName/:section/thread/:threadId
```

#### 2. Create InlineReplyCreator (2 hours)
```jsx
src/components/InlineReplyCreator.jsx

Features:
- Similar to InlinePostCreator
- Simplified (no threads, articles)
- Auto-set thread_id
- "Reply" instead of "Post"
- Inline in thread view
```

#### 3. Thread Routing (2 hours)
```jsx
// Add routes:
<Route path="/division/:divisionName/:section/thread/:threadId" component={ThreadView} />

// Navigation:
- Click thread title → Navigate to thread view
- After thread creation → Redirect to thread view
- Back button → Return to section feed
```

#### 4. Thread Navigation (2 hours)
```jsx
Features:
- Thread list in section feeds
- Thread preview cards
- Click to open thread view
- Breadcrumbs (Division > Section > Thread)
- "Back to [Section]" button
```

**Deliverables:**
- [ ] ThreadView page
- [ ] InlineReplyCreator component
- [ ] Thread routing
- [ ] Thread navigation

---

## 🎨 Design System Reference

### Colors
```css
Primary: #2563EB (blue-600)
Primary Hover: #1D4ED8 (blue-700)
Primary Light: #DBEAFE (blue-100)

Gray: #6B7280 (gray-500)
Gray Light: #F3F4F6 (gray-100)
Gray Border: #E5E7EB (gray-200)

Success: #10B981 (green-500)
Error: #EF4444 (red-500)
Warning: #F59E0B (amber-500)
```

### Spacing
```css
Container: px-5 py-4
Inline padding: p-2, p-3
Gap between items: gap-2, gap-3
Margin bottom: mb-6
```

### Typography
```css
Heading: text-lg font-semibold
Body: text-base
Small: text-sm
Tiny: text-xs

Colors:
- Primary text: text-gray-900
- Secondary text: text-gray-600
- Muted text: text-gray-500
```

### Components
```css
Button:
- Primary: bg-blue-600 text-white hover:bg-blue-700
- Secondary: bg-white text-gray-700 border hover:bg-gray-50
- Danger: bg-red-600 text-white hover:bg-red-700

Input:
- Border: border-gray-300
- Focus: ring-2 ring-blue-500 border-blue-500
- Disabled: bg-gray-100 opacity-50

Card:
- Background: bg-white
- Border: border border-gray-200
- Shadow: shadow-sm (collapsed), shadow-md (expanded)
- Rounded: rounded-lg
```

---

## 🔧 API Endpoints Reference

### Posts
```javascript
// Create post
POST /api/content/posts/
Body: {
  content: string (HTML),
  article_content: string | null (rich HTML),
  post_type: 'text' | 'image' | 'video' | 'audio' | 'poll' | 'article',
  community: number,
  thread: number | null,
  visibility: 'public' | 'followers',
  media: array[{type, url, description}],
  poll: {question, options, allow_multiple, expiration_hours} | null
}

// Get community from division + section
GET /api/communities/?division_id={id}&section={section}
Response: {results: [{id, name, description, ...}]}
```

### Media
```javascript
// Upload media
POST /api/media/upload/
Body: FormData {
  file: File,
  media_type: 'image' | 'video' | 'audio'
}
Response: {
  id: number,
  url: string,
  media_type: string,
  thumbnail: string | null
}
```

### Threads
```javascript
// Create thread
POST /api/communities/threads/
Body: {
  title: string,
  body: string,
  community: number,
  include_first_post: boolean
}
Response: {
  id: number,
  title: string,
  slug: string,
  url: string
}

// Get thread
GET /api/communities/threads/{id}/
Response: {
  id, title, body, creator, community, posts_count, created_at
}
```

---

## 🧪 Testing Checklist

### Unit Tests
- [ ] InlinePostCreator renders correctly
- [ ] Collapsed state shows placeholder
- [ ] Expanded state shows editor
- [ ] Mode switching works
- [ ] Form validation works
- [ ] Submit handler called correctly

### Integration Tests
- [ ] Media upload works
- [ ] Poll creation works
- [ ] Article modal opens
- [ ] Thread modal opens
- [ ] API calls succeed
- [ ] Error handling works

### E2E Tests
- [ ] Create text post
- [ ] Create image post
- [ ] Create video post
- [ ] Create poll
- [ ] Create article
- [ ] Create thread
- [ ] Reply to thread
- [ ] All posts appear in feed

---

## 📊 Success Metrics

### Performance
- [ ] Time to first post < 5 seconds
- [ ] Modal load time < 500ms
- [ ] API response < 2 seconds
- [ ] No memory leaks
- [ ] Smooth animations (60fps)

### UX
- [ ] Post completion rate > 90%
- [ ] Error rate < 5%
- [ ] User satisfaction > 4/5
- [ ] Mobile usable
- [ ] Accessible (WCAG 2.1 AA)

### Business
- [ ] 50% more posts created
- [ ] 30% more articles
- [ ] 20% more threads
- [ ] 80% less support tickets
- [ ] Higher engagement

---

## 🐛 Common Issues & Solutions

### Issue: TipTap not loading
**Solution:** Check if extensions are properly imported

### Issue: Media upload fails
**Solution:** Check file size limits, MIME types, CORS

### Issue: Context not detected
**Solution:** Verify division/section state management

### Issue: Form not resetting
**Solution:** Check resetForm() calls and state updates

### Issue: Modal not closing
**Solution:** Verify onClose callback and state management

---

## 📚 Resources

### Documentation
- TipTap: https://tiptap.dev/
- React: https://react.dev/
- Tailwind CSS: https://tailwindcss.com/
- Heroicons: https://heroicons.com/

### Internal Docs
- POST_CREATION_UX_REVISED.md - Complete UX proposal
- PHASE1_INLINE_POST_CREATOR_SUMMARY.md - Phase 1 summary
- API documentation (backend)

---

## 🤝 Team Communication

### Daily Standup
- What did you complete?
- What are you working on?
- Any blockers?

### Code Reviews
- All PRs require 1 approval
- Focus on UX, performance, accessibility
- Test before approving

### Demos
- Weekly demo to stakeholders
- Show progress, get feedback
- Iterate based on input

---

## 🎯 Next Action Items

### Immediate (This Week):
1. ✅ Create RichArticleModal component
2. ✅ Create ThreadCreatorModal component
3. ✅ Connect Advanced dropdown logic
4. ✅ Implement media upload handler

### Short Term (Next Week):
1. ⏳ Integrate into section pages
2. ⏳ Auto-context detection
3. ⏳ Complete API integration
4. ⏳ Add error handling

### Medium Term (Weeks 3-4):
1. ⏳ ThreadView page
2. ⏳ Thread routing
3. ⏳ E2E testing
4. ⏳ Performance optimization

### Long Term (Month 2):
1. ⏳ Analytics dashboard
2. ⏳ A/B testing
3. ⏳ Mobile app integration
4. ⏳ Scheduled posts

---

**Last Updated:** $(date)
**Status:** Phase 1 Complete ✅
**Next Milestone:** Phase 2 - Advanced Modals

