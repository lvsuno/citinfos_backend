"""
Django admin configuration for Communities app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import RubriqueTemplate, Community


@admin.register(RubriqueTemplate)
class RubriqueTemplateAdmin(admin.ModelAdmin):
    """Admin interface for managing rubrique templates."""

    list_display = [
        'template_type',
        'default_name',
        'default_name_en',
        'parent',
        'depth',
        'is_required',
        'is_active',
        'default_order',
    ]

    list_filter = [
        'is_required',
        'is_active',
        'allow_threads',
        'allow_direct_posts',
        'depth',
    ]

    search_fields = [
        'template_type',
        'default_name',
        'default_name_en',
        'default_description',
    ]

    ordering = ['path', 'default_order', 'default_name']

    fieldsets = (
        ('Template Identification', {
            'fields': ('template_type',)
        }),
        ('Default Values (French)', {
            'fields': (
                'default_name',
                'default_description',
                'default_icon',
                'default_color',
            )
        }),
        ('Default Values (English)', {
            'fields': ('default_name_en',),
            'classes': ('collapse',)
        }),
        ('Hierarchy', {
            'fields': (
                'parent',
                'depth',
                'path',
            )
        }),
        ('Behavior', {
            'fields': (
                'is_required',
                'allow_threads',
                'allow_direct_posts',
            )
        }),
        ('Display', {
            'fields': ('default_order',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    readonly_fields = ['id', 'depth', 'path']


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    """Admin interface for managing communities."""

    list_display = [
        'name',
        'slug',
        'creator',
        'community_type',
        'enabled_rubriques_count',
        'threads_count',
        'posts_count',
        'is_active',
        'created_at',
    ]

    list_filter = [
        'community_type',
        'is_active',
        'is_featured',
        'created_at',
    ]

    search_fields = [
        'name',
        'slug',
        'description',
        'creator__user__username',
    ]

    ordering = ['-created_at']

    readonly_fields = [
        'id',
        'slug',
        'creator',
        'posts_count',
        'threads_count',
        'enabled_rubriques_display',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'slug',
                'description',
                'community_type',
                'creator',
            )
        }),
        ('Media', {
            'fields': (
                'avatar',
                'cover_media',
                'cover_media_type',
            )
        }),
        ('Rubriques', {
            'fields': (
                'enabled_rubriques',
                'enabled_rubriques_display',
            ),
            'description': 'Manage enabled rubriques for this community'
        }),
        ('Settings', {
            'fields': (
                'allow_posts',
                'require_post_approval',
                'allow_external_links',
            )
        }),
        ('Geographic Association', {
            'fields': ('division',),
            'classes': ('collapse',)
        }),
        ('Additional Data', {
            'fields': (
                'rules',
                'tags',
            ),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'posts_count',
                'threads_count',
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
                'is_featured',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def enabled_rubriques_count(self, obj):
        """Display count of enabled rubriques."""
        count = len(obj.enabled_rubriques) if obj.enabled_rubriques else 0
        return f"{count} rubriques"
    enabled_rubriques_count.short_description = 'Enabled Rubriques'

    def enabled_rubriques_display(self, obj):
        """Display enabled rubriques with nice formatting."""
        if not obj.enabled_rubriques:
            return format_html('<em>No rubriques enabled</em>')

        rubriques = obj.get_enabled_rubriques()
        items = []

        for rubrique in rubriques:
            icon = rubrique.default_icon or '📌'
            color = rubrique.default_color or '#888'
            items.append(
                f'<span style="background-color: {color}; '
                f'color: white; padding: 4px 8px; margin: 2px; '
                f'border-radius: 4px; display: inline-block;">'
                f'{icon} {rubrique.default_name}</span>'
            )

        return format_html('<br>'.join(items))
    enabled_rubriques_display.short_description = 'Enabled Rubriques Detail'
