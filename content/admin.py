"""Admin interface for content moderation system."""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Post, Comment, Like, ContentReport, MediaMetadata,
    ContentModerationRule, ContentAnalysis, AutoModerationAction,
    ModerationQueue, Hashtag, PostHashtag, Mention,
    BotDetectionProfile, BotDetectionEvent, UserActivityPattern,
    PostSee, DirectShare
)


@admin.register(PostSee)
class PostSeeAdmin(admin.ModelAdmin):
    """Admin interface for post sees."""
    list_display = ['user', 'post', 'seen_at']
    search_fields = ['user__user__username', 'post__id']
    list_filter = ['seen_at']
    ordering = ['-seen_at']


@admin.register(ContentModerationRule)
class ContentModerationRuleAdmin(admin.ModelAdmin):
    """Admin interface for moderation rules."""
    list_display = [
        'name', 'rule_type', 'action', 'severity_level',
        'is_active', 'applies_to_posts', 'applies_to_comments'
    ]
    list_filter = [
        'rule_type', 'action', 'severity_level', 'is_active',
        'applies_to_posts', 'applies_to_comments'
    ]
    search_fields = ['name', 'description']
    ordering = ['severity_level', 'name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'rule_type', 'description')
        }),
        ('Action Configuration', {
            'fields': ('action', 'severity_level', 'configuration')
        }),
        ('Scope', {
            'fields': (
                'is_active', 'applies_to_posts', 'applies_to_comments', 'community'
            )
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ContentAnalysis)
class ContentAnalysisAdmin(admin.ModelAdmin):
    """Admin interface for content analysis results."""
    list_display = [
        'content_object_link', 'analysis_type', 'sentiment',
        'toxicity_score', 'spam_score', 'overall_risk_display',
        'requires_moderation', 'created_at'
    ]
    list_filter = [
        'analysis_type', 'sentiment', 'detected_language',
        'is_human_verified', 'created_at'
    ]
    search_fields = ['content_type__model', 'model_name']
    ordering = ['-created_at']

    def content_object_link(self, obj):
        """Create a link to the content object."""
        if obj.content_object:
            url = reverse(
                f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                args=[obj.object_id]
            )
            return format_html('<a href="{}">{}</a>', url, str(obj.content_object))
        return '-'
    content_object_link.short_description = 'Content'

    def overall_risk_display(self, obj):
        """Display overall risk score with color coding."""
        risk = obj.overall_risk_score
        if risk >= 0.8:
            color = 'red'
        elif risk >= 0.6:
            color = 'orange'
        elif risk >= 0.4:
            color = 'yellow'
        else:
            color = 'green'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
            color, risk
        )
    overall_risk_display.short_description = 'Risk Score'

    fieldsets = (
        ('Content Information', {
            'fields': ('content_type', 'object_id', 'analysis_type')
        }),
        ('Sentiment Analysis', {
            'fields': ('sentiment', 'sentiment_confidence'),
            'classes': ('collapse',)
        }),
        ('Toxicity Analysis', {
            'fields': (
                'toxicity_score', 'spam_score', 'hate_speech_score',
                'violence_score', 'adult_content_score'
            ),
            'classes': ('collapse',)
        }),
        ('Language & Topics', {
            'fields': ('detected_language', 'language_confidence', 'topics', 'emotions'),
            'classes': ('collapse',)
        }),
        ('Model Information', {
            'fields': ('model_name', 'model_version', 'processing_time'),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': ('is_human_verified', 'created_at', 'updated_at')
        })
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AutoModerationAction)
class AutoModerationActionAdmin(admin.ModelAdmin):
    """Admin interface for auto-moderation actions."""
    list_display = [
        'content_object_link', 'target_user', 'action_type',
        'severity_level', 'confidence_score', 'status', 'created_at'
    ]
    list_filter = [
        'action_type', 'status', 'severity_level', 'created_at'
    ]
    search_fields = [
        'target_user__user__username', 'reason', 'review_notes'
    ]
    ordering = ['-created_at']

    def content_object_link(self, obj):
        """Create a link to the content object."""
        if obj.content_object:
            url = reverse(
                f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                args=[obj.object_id]
            )
            return format_html('<a href="{}">{}</a>', url, str(obj.content_object))
        return '-'
    content_object_link.short_description = 'Content'

    fieldsets = (
        ('Action Details', {
            'fields': (
                'content_type', 'object_id', 'target_user',
                'action_type', 'reason'
            )
        }),
        ('Confidence & Severity', {
            'fields': ('confidence_score', 'severity_level')
        }),
        ('Triggers', {
            'fields': ('triggered_by_analysis', 'triggered_by_rule'),
            'classes': ('collapse',)
        }),
        ('Status & Review', {
            'fields': (
                'status', 'reviewed_by', 'review_decision', 'review_notes'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'reviewed_at', 'expires_at')
        })
    )
    readonly_fields = ['created_at']


@admin.register(ModerationQueue)
class ModerationQueueAdmin(admin.ModelAdmin):
    """Admin interface for moderation queue."""
    list_display = [
        'content_object_link', 'priority_display', 'status',
        'assigned_to', 'reason_short', 'created_at'
    ]
    list_filter = [
        'priority', 'status', 'assigned_to', 'created_at'
    ]
    search_fields = ['reason', 'resolution_notes']
    ordering = ['-priority', '-created_at']

    def content_object_link(self, obj):
        """Create a link to the content object."""
        if obj.content_object:
            url = reverse(
                f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                args=[obj.object_id]
            )
            return format_html('<a href="{}">{}</a>', url, str(obj.content_object))
        return '-'
    content_object_link.short_description = 'Content'

    def priority_display(self, obj):
        """Display priority with color coding."""
        priority_colors = {
            1: 'green',
            2: 'blue',
            3: 'orange',
            4: 'red',
            5: 'darkred'
        }
        color = priority_colors.get(obj.priority, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_display.short_description = 'Priority'

    def reason_short(self, obj):
        """Display shortened reason."""
        return obj.reason[:50] + '...' if len(obj.reason) > 50 else obj.reason
    reason_short.short_description = 'Reason'

    fieldsets = (
        ('Queue Item', {
            'fields': ('content_type', 'object_id', 'priority', 'status', 'reason')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'assigned_at')
        }),
        ('Resolution', {
            'fields': ('resolved_by', 'resolution_notes', 'resolved_at')
        }),
        ('Related', {
            'fields': ('auto_moderation_action',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at')
        })
    )
    readonly_fields = ['created_at', 'assigned_at', 'resolved_at']


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    """Admin interface for content reports."""
    list_display = [
        'reporter', 'content_object_link', 'reason', 'status',
        'reviewed_by', 'created_at'
    ]
    list_filter = ['reason', 'status', 'created_at']
    search_fields = ['reporter__user__username', 'description', 'review_notes']
    ordering = ['-created_at']

    def content_object_link(self, obj):
        """Create a link to the content object."""
        if obj.content_object:
            url = reverse(
                f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                args=[obj.object_id]
            )
            return format_html('<a href="{}">{}</a>', url, str(obj.content_object))
        return '-'
    content_object_link.short_description = 'Content'


# Register other models with basic admin
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'post_type', 'visibility', 'is_deleted', 'created_at']
    list_filter = ['post_type', 'visibility', 'is_deleted', 'created_at']
    search_fields = ['author__user__username', 'content']
    ordering = ['-created_at']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'is_deleted', 'created_at'
    ]
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['author__user__username', 'content']
    ordering = ['-created_at']


@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ['name', 'posts_count', 'created_at']
    search_fields = ['name']
    ordering = ['-posts_count']


admin.site.register(Like)
admin.site.register(DirectShare)
admin.site.register(MediaMetadata)
admin.site.register(PostHashtag)
admin.site.register(Mention)


# Bot Detection Admin

@admin.register(BotDetectionProfile)
class BotDetectionProfileAdmin(admin.ModelAdmin):
    """Admin interface for bot detection profiles."""
    list_display = [
        'user_link', 'overall_bot_score_display', 'timing_score',
        'content_score', 'behavior_score', 'is_flagged_as_bot',
        'auto_blocked', 'last_analysis'
    ]
    list_filter = [
        'is_flagged_as_bot', 'auto_blocked', 'is_verified_human',
        'last_analysis'
    ]
    search_fields = ['user__user__username', 'user__user__email']
    ordering = ['-overall_bot_score']
    readonly_fields = ['analysis_count', 'last_analysis']

    def user_link(self, obj):
        """Create a link to the user."""
        url = reverse('admin:accounts_userprofile_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.user.username)
    user_link.short_description = 'User'

    def overall_bot_score_display(self, obj):
        """Display bot score with color coding."""
        score = obj.overall_bot_score
        if score >= 0.9:
            color = 'red'
            weight = 'bold'
        elif score >= 0.7:
            color = 'orange'
            weight = 'bold'
        elif score >= 0.5:
            color = 'yellow'
            weight = 'normal'
        else:
            color = 'green'
            weight = 'normal'

        return format_html(
            '<span style="color: {}; font-weight: {};">{:.2f}</span>',
            color, weight, score
        )
    overall_bot_score_display.short_description = 'Bot Score'

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Bot Scores', {
            'fields': (
                'overall_bot_score', 'timing_score',
                'content_score', 'behavior_score'
            )
        }),
        ('Timing Analysis', {
            'fields': (
                'avg_posting_interval', 'posting_regularity_score',
                'rapid_posting_incidents'
            ),
            'classes': ('collapse',)
        }),
        ('Content Analysis', {
            'fields': (
                'duplicate_content_ratio', 'link_spam_score'
            ),
            'classes': ('collapse',)
        }),
        ('Behavior Analysis', {
            'fields': (
                'follows_to_followers_ratio', 'profile_completeness_score'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': (
                'is_flagged_as_bot', 'is_verified_human', 'auto_blocked'
            )
        }),
        ('Metadata', {
            'fields': ('analysis_count', 'last_analysis'),
            'classes': ('collapse',)
        })
    )

    actions = ['mark_as_verified_human', 'flag_as_bot', 'unblock_user']

    def mark_as_verified_human(self, request, queryset):
        """Mark selected profiles as verified human."""
        updated = queryset.update(
            is_verified_human=True,
            is_flagged_as_bot=False,
            auto_blocked=False
        )
        self.message_user(request, f'{updated} profiles marked as verified human.')
    mark_as_verified_human.short_description = "Mark as verified human"

    def flag_as_bot(self, request, queryset):
        """Flag selected profiles as bots."""
        updated = queryset.update(is_flagged_as_bot=True)
        self.message_user(request, f'{updated} profiles flagged as bots.')
    flag_as_bot.short_description = "Flag as bot"

    def unblock_user(self, request, queryset):
        """Unblock selected users."""
        updated = queryset.update(auto_blocked=False)
        self.message_user(request, f'{updated} users unblocked.')
    unblock_user.short_description = "Unblock user"


@admin.register(BotDetectionEvent)
class BotDetectionEventAdmin(admin.ModelAdmin):
    """Admin interface for bot detection events."""
    list_display = [
        'user_link', 'event_type', 'severity_display',
        'confidence_score', 'description_short', 'created_at'
    ]
    list_filter = [
        'event_type', 'severity', 'created_at'
    ]
    search_fields = [
        'user__user__username', 'description', 'action_taken'
    ]
    ordering = ['-created_at']

    def user_link(self, obj):
        """Create a link to the user."""
        url = reverse('admin:accounts_userprofile_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.user.username)
    user_link.short_description = 'User'

    def severity_display(self, obj):
        """Display severity with color coding."""
        severity_colors = {1: 'green', 2: 'blue', 3: 'orange', 4: 'red'}
        color = severity_colors.get(obj.severity, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_display.short_description = 'Severity'

    def description_short(self, obj):
        """Display shortened description."""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'

    fieldsets = (
        ('Event Details', {
            'fields': ('user', 'event_type', 'severity', 'description')
        }),
        ('Detection Data', {
            'fields': ('confidence_score', 'metadata')
        }),
        ('Related Content', {
            'fields': ('related_post', 'related_comment'),
            'classes': ('collapse',)
        }),
        ('Actions', {
            'fields': ('action_taken',)
        })
    )


@admin.register(UserActivityPattern)
class UserActivityPatternAdmin(admin.ModelAdmin):
    """Admin interface for user activity patterns."""
    list_display = [
        'user_link', 'date', 'hour', 'posts_count',
        'comments_count', 'rapid_activity_detected'
    ]
    list_filter = [
        'date', 'hour', 'rapid_activity_detected'
    ]
    search_fields = ['user__user__username']
    ordering = ['-date', '-hour']

    def user_link(self, obj):
        """Create a link to the user."""
        url = reverse('admin:accounts_userprofile_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.user.username)
    user_link.short_description = 'User'
