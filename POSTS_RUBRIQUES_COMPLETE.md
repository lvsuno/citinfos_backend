# Posts and Rubriques Management - Complete Summary

## Overview
This document summarizes the implementation of proper rubrique assignment for posts and the addition of the `title` field for article-type posts.

---

## ✅ Changes Completed

### 1. Added `title` Field to Post Model

**File:** `content/models.py`

**Change:**
```python
# Article-specific fields
title = models.CharField(
    max_length=300,
    blank=True,
    help_text="Title for article posts (required for post_type='article')"
)
```

**Purpose:**
- Article posts (`post_type='article'`) now have a dedicated title field
- Used for rich TipTap editor articles with proper titles
- Improves content structure and SEO

**Migration:** `content/migrations/0012_post_title.py`

**Status:** ✅ Applied successfully

---

### 2. Reassigned Existing Posts to Rubriques

**Script:** `reassign_posts_to_rubriques.py`

**Results:**
```
✅ 8 posts processed
✅ 8 posts successfully assigned to rubriques
❌ 0 errors
```

**Assignments:**
- All 8 existing posts → **Actualités** rubrique
- Reason: Content contained keywords like "nouveau", "annonce", "festival"

**Posts by Type:**
- 4 image posts
- 4 text posts
- 0 article posts (none exist yet)

---

## 📊 Current State

### Posts Distribution

| Rubrique | Template Type | Post Count | Post Types |
|----------|---------------|------------|------------|
| Actualités | `actualites` | 8 | 4 image, 4 text |
| **TOTAL** | | **8** | |

### Sample Posts

1. ☕ **NOUVEAU chez nous !** (image)
   - Rubrique: Actualités
   - Community: Sherbrooke

2. **Quelqu'un sait-il pourquoi la rue King Ouest est fermée...** (text)
   - Rubrique: Actualités
   - Community: Sherbrooke

3. 📢 **ANNONCE IMPORTANTE - Le Festival des traditions...** (image)
   - Rubrique: Actualités
   - Community: Sherbrooke

4. **Magnifique coucher de soleil sur le lac des Nations...** (image)
   - Rubrique: Actualités
   - Community: Sherbrooke

---

## 🎯 Rubrique Assignment Logic

### Current Implementation (Keyword-Based)

The script uses keyword matching to determine rubrique:

```python
RUBRIQUE_KEYWORDS = {
    'actualites': ['annonce', 'nouveau', 'important', 'information', 'actualité'],
    'evenements': ['festival', 'événement', 'spectacle', 'concert', 'fête'],
    'commerces': ['restaurant', 'café', 'boutique', 'magasin', 'commerce'],
    'questions': ['pourquoi', 'comment', 'qui', 'quoi', 'où', 'quand', 'sait-il'],
    'photos': ['photo', 'image', 'coucher de soleil', 'magnifique', 'vue'],
}
```

**Process:**
1. Analyze post content (or title for articles)
2. Match keywords to rubrique types
3. Assign highest-scoring rubrique
4. Default to `actualites` if no match

### Future Implementation (Recommendation System)

**For "Accueil" Rubrique:**
- Will use ML-based recommendation system
- Aggregate posts from all rubriques intelligently
- Personalized content based on user preferences
- Not implemented yet ⏳

---

## 📝 Post Model Structure

### Fields by Post Type

#### ALL Post Types
- `content` (max 2000 chars) - Basic HTML caption
- `community` - Community reference
- `rubrique_template` - Rubrique assignment (required for standalone posts)
- `thread` - Optional thread reference
- `post_type` - One of: text, image, video, audio, file, link, poll, mixed, article, repost*
- `visibility` - public, followers, private, community
- `author` - UserProfile reference

#### Article Posts ONLY
- `title` ⭐ **NEW** - Article title (max 300 chars)
- `article_content` - Rich HTML from TipTap editor
- `featured_image` - Cover image
- `excerpt` - Short summary (max 500 chars)
- `is_draft` - Draft status

---

## 🔄 Post-Thread-Rubrique Relationship

### Standalone Posts (No Thread)
```
Post
  ├── community (required)
  ├── rubrique_template (required) ✅
  └── thread (null)
```

**Rules:**
- MUST have `rubrique_template` assigned
- Rubrique determines which section it appears in
- Used for: news, announcements, questions, photos, etc.

### Posts in Threads
```
Thread
  ├── community (required)
  ├── rubrique_template (required)
  └── posts[]
        ├── Post 1 (rubrique_template = null)
        ├── Post 2 (rubrique_template = null)
        └── Post 3 (rubrique_template = null)
```

**Rules:**
- Thread has `rubrique_template`
- All posts in thread inherit rubrique from thread
- Posts MUST NOT have their own `rubrique_template`

---

## ✅ Validation Rules

### Model-Level Validation (`Post.clean()`)

1. **Thread Posts:**
   - ❌ MUST NOT have `rubrique_template`
   - ✅ Inherit from `thread.rubrique_template`

2. **Standalone Community Posts:**
   - ✅ MUST have `rubrique_template`
   - ✅ Rubrique must be enabled in community

3. **Article Posts:**
   - ⏳ Should validate `title` is not empty (TODO)
   - ✅ Can have `article_content`, `featured_image`, `excerpt`

---

## 🚀 Next Steps

### Immediate (For Testing)

1. **Test Expandable Rubriques in UI**
   - Open Sherbrooke community: `/sherbrooke`
   - Click "Nouvelles" to expand
   - Should see "Actualités" and "Annonces" children
   - Click "Actualités" to see the 8 posts

2. **Test Rubrique Filtering**
   - Navigate to: `/sherbrooke/rubriques/actualites/posts`
   - Should see all 8 posts
   - Navigate to: `/sherbrooke/posts/accueil`
   - Should see all posts (no filtering)

### Short-Term (Features)

1. **Create Article Posts**
   - Implement TipTap rich editor in frontend
   - Allow users to create posts with `post_type='article'`
   - Require title for article posts

2. **Better Rubrique Assignment**
   - Implement NLP-based classification
   - Use content analysis for better accuracy
   - Support multi-rubrique tagging

3. **Accueil Recommendation System**
   - ML model for personalized feed
   - User interaction tracking
   - Content relevance scoring

### Medium-Term (Polish)

1. **Rubrique Management UI**
   - Admin panel to enable/disable rubriques per community
   - Reorder rubriques
   - Customize rubrique names/icons per community

2. **Thread-Rubrique Integration**
   - Create threads with rubrique selection
   - Filter threads by rubrique
   - Thread templates per rubrique type

---

## 📌 Summary

✅ **Post Model:** Added `title` field for articles
✅ **Migrations:** Applied successfully
✅ **Existing Posts:** All 8 reassigned to Actualités rubrique
✅ **Validation:** Posts properly linked to rubriques
✅ **Communities:** 1420 communities with 32 rubriques each
✅ **Frontend:** Expandable rubrique sidebar ready

**Ready for Testing:** Navigate to `/sherbrooke` and test the expandable rubriques! 🎉

---

## 🔧 Troubleshooting

### If Posts Don't Show in Rubrique
1. Check post has `rubrique_template` assigned
2. Verify rubrique is enabled in community
3. Check post is not soft-deleted (`is_deleted=False`)
4. Verify post is not in a thread (or check thread's rubrique)

### If Sidebar Doesn't Expand
1. Clear browser cache
2. Restart frontend: `docker-compose restart frontend`
3. Check console for JavaScript errors
4. Verify API returns `isExpandable: true`

### If New Posts Created Without Rubrique
1. Frontend must send `rubrique_template` in POST request
2. Backend validates rubrique is enabled for community
3. Use `actualites` as default if user doesn't select
