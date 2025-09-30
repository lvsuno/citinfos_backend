"""Admin configuration for accounts app."""

from django.contrib import admin
from .models import UserProfile, ProfessionalProfile, UserSettings


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""

    list_display = [
        'user', 'role', 'is_verified', 'is_suspended',
        'country', 'city', 'follower_count', 'last_active'
    ]
    list_filter = [
        'role', 'is_verified', 'is_suspended', 'is_private',
        'country', 'created_at'
    ]
    search_fields = ['user__username', 'user__email', 'bio']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'id')
        }),
        ('Profile Details', {
            'fields': ('phone_number', 'date_of_birth', 'bio',
                      'profile_picture', 'cover_media', 'cover_media_type')
        }),
        ('Location', {
            'fields': ('country', 'city')
        }),
        ('Privacy Settings', {
            'fields': ('is_private', 'show_email', 'show_phone',
                      'show_location')
        }),
        ('Account Status', {
            'fields': ('is_verified', 'is_suspended', 'suspension_reason')
        }),
        ('Analytics', {
            'fields': ('follower_count', 'following_count', 'posts_count')
        }),
        ('Recommendation Factors', {
            'fields': ('engagement_score', 'content_quality_score',
                      'interaction_frequency'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_active'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProfessionalProfile)
class ProfessionalProfileAdmin(admin.ModelAdmin):
    """Admin interface for ProfessionalProfile model."""

    list_display = [
        'profile', 'company_name', 'job_title',
        'is_verified', 'verification_date'
    ]
    list_filter = ['is_verified', 'verification_date', 'created_at']
    search_fields = [
        'profile__user__username', 'company_name',
        'job_title', 'description'
    ]
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Profile', {
            'fields': ('profile',)
        }),
        ('Professional Information', {
            'fields': ('company_name', 'job_title', 'years_experience',
                      'description')
        }),
        ('Contact Information', {
            'fields': ('phone', 'website', 'business_address')
        }),
        ('Professional Details', {
            'fields': ('certifications', 'services_offered')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verification_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    """Admin interface for UserSettings model."""

    list_display = [
        'user', 'language', 'theme', 'email_notifications',
        'push_notifications', 'profile_visibility'
    ]
    list_filter = [
        'language', 'theme', 'email_notifications',
        'push_notifications', 'profile_visibility',
        'notification_frequency'
    ]
    search_fields = ['user__user__username']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'push_notifications',
                      'notification_frequency')
        }),
        ('Privacy Settings', {
            'fields': ('profile_visibility',)
        }),
        ('Interface Settings', {
            'fields': ('language', 'theme', 'timezone')
        }),
        ('Content Settings', {
            'fields': ('mature_content', 'auto_play_videos')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
