# Rubrique Scalability Solution - Virtual Sections

## Problem
Current implementation creates Section records for each community:
- 10,000 divisions × 3 required sections = 30,000 Section records
- 100,000 divisions × 3 = 300,000 records
- Massive database bloat for mostly identical data

## Solution: Virtual Sections (Template-Only Architecture)

### Core Concept
**Don't create Section records at all!** Use RubriqueTemplates as virtual sections.

### Architecture Changes

#### 1. Remove Auto-Creation Signal
**Delete/disable** the signal that creates sections automatically:
```python
# communities/signals.py - DISABLE THIS
@receiver(post_save, sender='communities.Community')
def create_required_rubrique_sections(...)  # ← Remove this
```

#### 2. Update Thread Model
Add `rubrique_template` field directly to Thread (skip Section entirely):

```python
# communities/models.py - Thread model
class Thread(models.Model):
    community = ForeignKey(Community)

    # NEW: Direct template reference (no Section intermediary)
    rubrique_template = ForeignKey(
        RubriqueTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='threads',
        help_text="Rubrique category for this thread"
    )

    # OPTIONAL: Keep section for custom/sub-sections only
    section = ForeignKey(
        Section,
        null=True,
        blank=True,
        help_text="Only used for custom subsections"
    )
```

#### 3. Frontend Renders Templates as Sections
Frontend displays RubriqueTemplates as if they were sections:

```javascript
// Get templates for this community
GET /api/rubrique-templates/?is_required=true

// Display as sections
templates.map(template => ({
  id: template.id,
  name: template.default_name,
  icon: template.default_icon,
  color: template.default_color,
  slug: template.template_type,
  // Count threads in this template
  threads_count: threadsInTemplate.length
}))

// Filter threads by template
GET /api/threads/?community={id}&rubrique_template={template_id}
```

#### 4. API Endpoints

**Get "sections" (actually templates):**
```
GET /api/communities/{id}/rubriques/
→ Returns RubriqueTemplates marked as required or enabled for this community
```

**Get threads in rubrique:**
```
GET /api/threads/?community={id}&rubrique_template={template_id}
```

**Create thread in rubrique:**
```
POST /api/threads/
{
  "community": "uuid",
  "rubrique_template": "template_uuid",  // ← Direct reference
  "title": "...",
  "content": "..."
}
```

### Database Comparison

#### Current Approach:
```
RubriqueTemplates: 5 records
Sections: 10,000 × 3 = 30,000 records
Threads: 100,000 records
TOTAL: 130,005 records
```

#### Virtual Sections:
```
RubriqueTemplates: 5 records
Threads: 100,000 records (with rubrique_template FK)
TOTAL: 100,005 records
```

**Savings: 30,000 redundant records eliminated!**

### When to Create Actual Sections?

Only create Section records for:
1. **Custom subsections** (user-created, not in templates)
2. **Community-specific customizations** (if they change name/icon/color)

Example:
- Community "Montreal" uses default templates → 0 Section records
- Community "Paris" customizes "Actualités" → name it "Nouvelles" → 1 Section record
- Community "Quebec" adds custom subsection "Sports d'hiver" → 1 Section record

**Result: ~1-5% of communities customize = 500 Section records instead of 30,000**

### Migration Strategy

#### Step 1: Add rubrique_template to Thread
```python
# communities/models.py
class Thread(models.Model):
    rubrique_template = models.ForeignKey(RubriqueTemplate, ...)
```

#### Step 2: Migrate existing data
```python
# Data migration
for thread in Thread.objects.filter(section__isnull=False):
    if thread.section.template:
        thread.rubrique_template = thread.section.template
        thread.save()
```

#### Step 3: Update serializers
```python
# communities/serializers.py
class ThreadSerializer(serializers.ModelSerializer):
    rubrique_name = serializers.CharField(
        source='rubrique_template.default_name',
        read_only=True
    )
    rubrique_type = serializers.CharField(
        source='rubrique_template.template_type',
        read_only=True
    )
    rubrique_icon = serializers.CharField(
        source='rubrique_template.default_icon',
        read_only=True
    )
```

#### Step 4: Delete template-based sections
```python
# Clean up redundant sections
Section.objects.filter(is_template_based=True, is_customized=False).delete()
```

### Benefits

✅ **30,000x reduction** in Section records for 10k communities
✅ **Faster queries** - no JOIN through Section table
✅ **Simpler schema** - Thread → Template (direct)
✅ **Easier maintenance** - update template affects all instantly
✅ **Flexible** - still allows custom sections when needed
✅ **Scalable** - works for 1 million+ divisions

### Tradeoffs

⚠️ **Per-community thread counts** - Need to aggregate in real-time
⚠️ **Custom sections** - Requires hybrid approach (template + section)
⚠️ **Hierarchy** - Subsections need actual Section records

## Recommendation

For **10,000+ divisions**, definitely use **Virtual Sections (Option 1)**.

You already have RubriqueTemplates built - just:
1. Stop creating Section records automatically
2. Add `rubrique_template` FK to Thread
3. Query threads by `community + rubrique_template`
4. Only create Section for actual customizations

This gives you global standardization with minimal database overhead!
