# Rubrique Template System Implementation Guide

## Overview
This document outlines the implementation of the Rubrique Template system for standardizing sections across thousands of administrative divisions worldwide.

## Current Status
✅ Backend Section model fully implemented
✅ All migrations applied
✅ Section CRUD API complete

## Proposed Changes

### 1. Add RubriqueTemplate Model

**Location:** `communities/models.py` (before Section model, around line 681)

```python
class RubriqueTemplate(models.Model):
    """Global templates for standard rubriques across all communities."""

    TEMPLATE_TYPES = [
        ('actualites', 'Actualités'),
        ('evenements', 'Événements'),
        ('commerces', 'Commerces'),
        ('services', 'Services'),
        ('aide', 'Aide & Support'),
        ('emploi', 'Emploi'),
        ('logement', 'Logement'),
        ('transport', 'Transport'),
        ('sante', 'Santé'),
        ('education', 'Éducation'),
        ('loisirs', 'Loisirs'),
        ('annonces', 'Petites Annonces'),
        ('custom', 'Custom'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Template identification
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)

    # Default values
    default_name = models.CharField(max_length=100)
    default_name_en = models.CharField(max_length=100, blank=True)
    default_description = models.TextField(max_length=500, blank=True)
    default_icon = models.CharField(max_length=50, blank=True)
    default_color = models.CharField(max_length=7, blank=True, default='#6366f1')

    # Behavior
    is_required = models.BooleanField(default=False)
    allow_customization = models.BooleanField(default=True)
    allow_threads = models.BooleanField(default=True)
    allow_direct_posts = models.BooleanField(default=False)
    supports_subsections = models.BooleanField(default=True)

    # Ordering
    default_order = models.PositiveIntegerField(default=0)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
```

### 2. Update Section Model

**Add these fields to Section model:**

```python
class Section(models.Model):
    # ... existing fields ...

    # NEW: Template relationship
    template = models.ForeignKey(
        'RubriqueTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sections',
        help_text="Template this section was created from (if any)"
    )

    is_template_based = models.BooleanField(
        default=False,
        help_text="True if created from a template"
    )

    is_customized = models.BooleanField(
        default=False,
        help_text="True if community has customized this template-based section"
    )
```

### 3. Create Migration

**File:** `communities/migrations/0007_rubrique_templates.py`

This migration will:
1. Create RubriqueTemplate table
2. Add template, is_template_based, is_customized fields to Section
3. Create initial rubrique templates (Actualités, Événements, Commerces)

### 4. Data Migration Strategy

**Convert existing "General" sections to template-based:**

```python
# Create "actualites" template for General sections
actualites_template = RubriqueTemplate.objects.create(
    template_type='actualites',
    default_name='Actualités',
    default_name_en='News',
    default_icon='📰',
    is_required=True,
    default_order=1
)

# Update existing General sections
Section.objects.filter(slug='general').update(
    template=actualites_template,
    is_template_based=True
)
```

### 5. Auto-Create Templates for New Communities

**Update Community.save() or use signals:**

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Community)
def create_required_sections(sender, instance, created, **kwargs):
    """Auto-create required rubrique sections for new communities."""
    if created:
        required_templates = RubriqueTemplate.objects.filter(
            is_required=True,
            is_active=True
        ).order_by('default_order')

        for template in required_templates:
            template.create_section_for_community(instance)
```

### 6. Admin Interface

**File:** `communities/admin.py`

```python
@admin.register(RubriqueTemplate)
class RubriqueTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_type', 'default_name', 'is_required', 'is_active', 'default_order']
    list_filter = ['is_required', 'is_active', 'allow_threads', 'allow_direct_posts']
    search_fields = ['template_type', 'default_name', 'default_name_en']
    ordering = ['default_order', 'default_name']
```

## Benefits

1. **Standardization:** Same rubriques across all communities worldwide
2. **Scalability:** Works with thousands of divisions
3. **Flexibility:** Communities can still customize if allowed
4. **Maintenance:** Update template → updates all non-customized sections
5. **Backward Compatible:** Existing Section functionality unchanged
6. **Future-proof:** Easy to add new templates

## Initial Templates

### Required Templates (auto-created for all communities):
1. **Actualités** (News) - 📰
2. **Événements** (Events) - 📅
3. **Commerces** (Businesses) - 🏪

### Optional Templates (communities can add):
4. **Services** - 🛠️
5. **Aide** - ❓
6. **Emploi** - 💼
7. **Logement** - 🏠
8. **Transport** - 🚗
9. **Santé** - 🏥
10. **Éducation** - 📚
11. **Loisirs** - 🎨
12. **Annonces** - 📋

## Next Steps

Would you like me to:
1. ✅ Create the migration file for RubriqueTemplate?
2. ✅ Update the Section model with template fields?
3. ✅ Create the signal for auto-creating required sections?
4. ✅ Add admin interface for managing templates?
5. ✅ Create initial data migration with standard templates?

Please confirm and I'll proceed with the implementation!
