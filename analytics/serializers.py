"""Serializers for the analytics app."""

from rest_framework import serializers
from accounts.models import UserSession, UserEvent
from .models import (
    DailyAnalytics, UserAnalytics, SystemMetric, ErrorLog
)




class DailyAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for daily analytics."""

    class Meta:
        model = DailyAnalytics
        fields = [
            'id', 'date', 'total_users', 'new_users', 'returning_users',
            'total_sessions', 'total_page_views', 'avg_session_duration',
            'bounce_rate', 'conversion_rate', 'top_pages',
            'top_referrers', 'device_breakdown', 'browser_breakdown',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserAnalyticsCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating user analytics."""

    class Meta:
        model = UserAnalytics
        fields = [
            'id', 'total_sessions', 'total_time_spent', 'avg_session_duration',
            'engagement_score', 'activity_level', 'total_posts', 'total_comments',
            'total_likes_given', 'total_likes_received', 'communities_joined',
             'total_searches',
            'preferred_platform', 'retention_score', 'last_activity_date'
        ]
        read_only_fields = ['id']


class UserAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for user analytics with full details."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )
    days_since_last_activity = serializers.SerializerMethodField()

    class Meta:
        model = UserAnalytics
        fields = [
            'id', 'user', 'user_username', 'total_sessions',
            'total_page_views', 'total_time_spent', 'avg_session_duration',
            'last_activity_date', 'engagement_score', 'activity_level',
            'total_posts', 'total_comments', 'total_likes_given',
            'total_likes_received', 'communities_joined',
            'total_searches', 'preferred_platform',
            'retention_score', 'days_since_last_activity', 'last_calculated'
        ]
        read_only_fields = ['id', 'user', 'last_calculated']

    def get_days_since_last_activity(self, obj):
        """Calculate days since last activity."""
        if obj.last_activity_date:
            from django.utils import timezone
            return (timezone.now().date() - obj.last_activity_date.date()).days
        return None


class SystemMetricCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating system metrics."""

    class Meta:
        model = SystemMetric
        fields = [
            'id', 'metric_type', 'value', 'additional_data', 'recorded_at'
        ]
        read_only_fields = ['id', 'recorded_at']


class SystemMetricSerializer(serializers.ModelSerializer):
    """Serializer for system metrics with full details."""

    class Meta:
        model = SystemMetric
        fields = [
            'id', 'metric_type', 'value', 'additional_data', 'recorded_at'
        ]
        read_only_fields = ['id', 'recorded_at']


class ErrorLogCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating error logs."""

    class Meta:
        model = ErrorLog
        fields = [
            'id', 'session', 'error_type', 'error_message',
            'error_stack', 'page_url', 'user_agent',
            'is_resolved', 'resolution_notes'
        ]
        read_only_fields = ['id']


class ErrorLogSerializer(serializers.ModelSerializer):
    """Serializer for error logs with full details."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )
    session_id = serializers.CharField(
        source='session.session_id', read_only=True
    )

    class Meta:
        model = ErrorLog
        fields = [
            'id', 'user', 'user_username', 'session', 'session_id',
            'error_type', 'error_message', 'error_stack', 'page_url',
            'user_agent', 'is_resolved', 'resolution_notes',
            'timestamp', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'timestamp', 'created_at', 'updated_at'
        ]
