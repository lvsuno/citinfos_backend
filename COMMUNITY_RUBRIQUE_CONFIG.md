# Community-Specific Rubrique Configuration (Best of Both Worlds!)

## Your Vision (Perfect Solution! ✅)

**Global Templates:** Exhaustive library of all possible rubriques
**Per-Community:** Each division selects which rubriques to enable

### Example:
```
Global Templates (50+ available):
- Actualités, Événements, Commerces, Services, Emploi, Logement,
  Transport, Santé, Éducation, Sports, Culture, Tourisme,
  Agriculture, Industrie, Environnement, etc.

Community "Montreal" enables:
- Actualités, Événements, Commerces, Transport, Culture

Community "Rural Farm Town" enables:
- Actualités, Agriculture, Commerces, Environnement

Community "Tech Hub" enables:
- Actualités, Emploi, Services, Éducation, Innovation
```

**Result:** Same templates, different subsets per community!

## Implementation: Community-RubriqueTemplate M2M Relationship

### Model: CommunityRubriqueConfig

```python
# communities/models.py

class CommunityRubriqueConfig(models.Model):
    """Defines which rubrique templates are enabled for each community."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='rubrique_configs'
    )
    template = models.ForeignKey(
        RubriqueTemplate,
        on_delete=models.CASCADE,
        related_name='community_configs'
    )

    # Customization (optional per community)
    custom_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Override template name (e.g., 'Nouvelles' instead of 'Actualités')"
    )
    custom_icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Override template icon"
    )
    custom_color = models.CharField(
        max_length=7,
        blank=True,
        help_text="Override template color"
    )
    custom_description = models.TextField(
        max_length=500,
        blank=True,
        help_text="Custom description for this community"
    )

    # Ordering & Visibility
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within this community"
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Is this rubrique active for this community?"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Show prominently in community homepage"
    )

    # Behavior overrides (optional)
    allow_threads = models.BooleanField(
        null=True,
        blank=True,
        help_text="Override template setting (null = use template default)"
    )
    require_approval = models.BooleanField(
        default=False,
        help_text="Require moderator approval for threads in this rubrique"
    )

    # Statistics (denormalized for performance)
    threads_count = models.PositiveIntegerField(default=0)
    posts_count = models.PositiveIntegerField(default=0)
    last_activity_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_rubrique_configs'
    )

    class Meta:
        db_table = 'community_rubrique_configs'
        unique_together = [('community', 'template')]
        ordering = ['community', 'order', 'template__default_order']
        verbose_name = 'Community Rubrique Configuration'
        verbose_name_plural = 'Community Rubrique Configurations'

    def __str__(self):
        name = self.custom_name or self.template.default_name
        return f"{self.community.name} → {name}"

    @property
    def display_name(self):
        """Get the display name (custom or template default)."""
        return self.custom_name or self.template.default_name

    @property
    def display_icon(self):
        """Get the display icon (custom or template default)."""
        return self.custom_icon or self.template.default_icon

    @property
    def display_color(self):
        """Get the display color (custom or template default)."""
        return self.custom_color or self.template.default_color

    @property
    def effective_allow_threads(self):
        """Get effective allow_threads setting."""
        return self.allow_threads if self.allow_threads is not None else self.template.allow_threads
```

### Thread Model Update

```python
# communities/models.py

class Thread(models.Model):
    # Existing fields...
    community = models.ForeignKey(Community, ...)

    # NEW: Direct reference to template (no Section needed!)
    rubrique_template = models.ForeignKey(
        RubriqueTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='threads',
        help_text="Rubrique category"
    )

    # Keep section for custom subsections ONLY
    section = models.ForeignKey(
        Section,
        null=True,
        blank=True,
        help_text="Only for custom subsections"
    )

    def clean(self):
        """Validate rubrique is enabled for this community."""
        if self.rubrique_template and self.community:
            # Check if this rubrique is enabled for this community
            config = CommunityRubriqueConfig.objects.filter(
                community=self.community,
                template=self.rubrique_template,
                is_enabled=True
            ).first()

            if not config:
                raise ValidationError({
                    'rubrique_template': f"Rubrique '{self.rubrique_template.default_name}' "
                                        f"is not enabled for this community."
                })
```

## API Endpoints

### 1. Get Community's Enabled Rubriques

```python
# communities/views.py

class CommunityViewSet(viewsets.ModelViewSet):

    @action(detail=True, methods=['get'])
    def rubriques(self, request, pk=None):
        """Get all enabled rubriques for this community."""
        community = self.get_object()

        configs = CommunityRubriqueConfig.objects.filter(
            community=community,
            is_enabled=True
        ).select_related('template').order_by('order')

        serializer = CommunityRubriqueConfigSerializer(configs, many=True)
        return Response(serializer.data)
```

**Usage:**
```bash
GET /api/communities/{id}/rubriques/

Response:
[
  {
    "id": "uuid",
    "template": {
      "id": "uuid",
      "template_type": "actualites",
      "default_name": "Actualités"
    },
    "display_name": "Actualités",  # or custom name
    "display_icon": "📰",
    "display_color": "#3B82F6",
    "order": 1,
    "is_featured": true,
    "threads_count": 150,
    "posts_count": 2340,
    "allow_threads": true
  },
  {
    "id": "uuid",
    "template": {
      "template_type": "evenements"
    },
    "display_name": "Événements",
    "display_icon": "📅",
    "order": 2,
    "threads_count": 45
  }
]
```

### 2. Enable/Disable Rubriques (Admin)

```python
@action(detail=True, methods=['post'])
def add_rubrique(self, request, pk=None):
    """Add a rubrique template to this community."""
    community = self.get_object()
    template_id = request.data.get('template_id')

    config, created = CommunityRubriqueConfig.objects.get_or_create(
        community=community,
        template_id=template_id,
        defaults={
            'is_enabled': True,
            'order': CommunityRubriqueConfig.objects.filter(
                community=community
            ).count() + 1
        }
    )

    if not created:
        config.is_enabled = True
        config.save()

    return Response(CommunityRubriqueConfigSerializer(config).data)

@action(detail=True, methods=['post'])
def remove_rubrique(self, request, pk=None):
    """Disable a rubrique for this community."""
    community = self.get_object()
    config_id = request.data.get('config_id')

    config = CommunityRubriqueConfig.objects.get(
        id=config_id,
        community=community
    )
    config.is_enabled = False
    config.save()

    return Response({'status': 'disabled'})
```

### 3. Filter Threads by Rubrique

```python
class ThreadViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        queryset = Thread.objects.all()

        # Filter by community
        community_id = self.request.query_params.get('community')
        if community_id:
            queryset = queryset.filter(community_id=community_id)

        # Filter by rubrique template
        rubrique_id = self.request.query_params.get('rubrique')
        if rubrique_id:
            queryset = queryset.filter(rubrique_template_id=rubrique_id)

        return queryset
```

**Usage:**
```bash
# Get all threads in "Actualités" for Montreal
GET /api/threads/?community={montreal_id}&rubrique={actualites_template_id}
```

## Default Configuration Setup

### Signal: Auto-create default configs for new communities

```python
# communities/signals.py

@receiver(post_save, sender=Community)
def create_default_rubrique_configs(sender, instance, created, **kwargs):
    """Create default rubrique configurations for new communities."""
    if created:
        # Get templates marked as "required"
        required_templates = RubriqueTemplate.objects.filter(
            is_required=True,
            is_active=True
        ).order_by('default_order')

        for order, template in enumerate(required_templates, start=1):
            CommunityRubriqueConfig.objects.create(
                community=instance,
                template=template,
                order=order,
                is_enabled=True,
                is_featured=(order <= 3)  # First 3 are featured
            )
```

## Database Comparison

### For 10,000 Communities:

**Old Approach (Section per community):**
```
Sections: 10,000 × 3 = 30,000 records
```

**New Approach (Config per enabled rubrique):**
```
RubriqueTemplates: 50 records (global library)
CommunityRubriqueConfigs: 10,000 × 5 avg = 50,000 records
  (each community enables ~5 rubriques from the 50 available)

BUT: No redundant data! Each config is 1 small record with:
  - community_id
  - template_id
  - custom_name (if any)
  - order
  - is_enabled
```

**Benefits:**
✅ Each community picks from 50+ templates
✅ Only ~5-10 enabled per community
✅ Customize name/icon per community if needed
✅ Easy to enable/disable rubriques
✅ No redundant section data
✅ Threads reference template directly

## Admin Workflow

### 1. Super Admin: Create Templates
```
Create 50 global templates in Django admin:
- Actualités, Événements, Commerces, Services, Emploi,
  Logement, Transport, Santé, Éducation, Sports, Culture,
  Tourisme, Agriculture, Industrie, Innovation, etc.
```

### 2. Community Admin: Configure Rubriques
```
Montreal admin goes to:
/communities/montreal/settings/rubriques

Sees library of 50 templates:
[✓] Actualités
[✓] Événements
[✓] Commerces
[✓] Transport
[✓] Culture
[ ] Agriculture  ← Not relevant for urban Montreal
[ ] Industrie
...

Can customize:
- Actualités → rename to "Nouvelles"
- Change icon from 📰 to 📱
- Reorder (drag and drop)
```

### 3. User: Browse Community
```
User visits Montreal community:

Sees enabled rubriques:
- 📱 Nouvelles (custom name!)
- 📅 Événements
- 🏪 Commerces
- 🚇 Transport
- 🎭 Culture

(Agriculture, Industrie not shown - disabled)
```

## Summary

✅ **Global exhaustive library** - 50+ rubrique templates
✅ **Per-community subset** - Each division picks 5-10 relevant ones
✅ **Fully customizable** - Name, icon, color, order per community
✅ **Scalable** - Works for 1 million+ communities
✅ **No redundancy** - Threads reference templates directly
✅ **Flexible** - Easy to enable/disable rubriques

This is exactly what you described! Want me to implement it?
