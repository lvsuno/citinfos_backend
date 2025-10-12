"""Analytics models for tracking metrics and user behavior."""

import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.models import UserProfile

User = get_user_model()


class ContentAnalytics(models.Model):
    """
    Track content performance and engagement metrics for posts, comments, and interactions.
    Provides real-time insights into content success and user engagement patterns.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Content reference (using generic foreign key for flexibility)
    content_type = models.CharField(max_length=20, choices=[
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('thread', 'Thread'),
        ('community_post', 'Community Post'),
    ])
    content_id = models.UUIDField()  # UUID of the content object
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='content_analytics')

    # Engagement metrics
    view_count = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    dislike_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)

    # Performance metrics
    avg_read_time_seconds = models.FloatField(default=0.0)
    bounce_rate = models.FloatField(default=0.0)  # Percentage who viewed but didn't engage
    engagement_rate = models.FloatField(default=0.0)  # (likes + comments + shares) / views
    click_through_rate = models.FloatField(default=0.0)  # For posts with links

    # Time-based metrics
    engagement_velocity = models.FloatField(default=0.0)  # Engagements per hour
    peak_engagement_hour = models.PositiveIntegerField(null=True, blank=True)
    viral_coefficient = models.FloatField(default=0.0)  # Share rate indicator

    # Geographic and demographic data
    top_countries = models.JSONField(default=list, blank=True)  # Countries with most views
    demographic_data = models.JSONField(default=dict, blank=True)  # Age groups, etc.

    # Content quality indicators
    quality_score = models.FloatField(default=0.0)  # 0-100 based on engagement
    moderation_flags = models.PositiveIntegerField(default=0)
    positive_sentiment_ratio = models.FloatField(default=0.0)  # 0-1 based on reactions

    # Temporal data
    first_engagement_at = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('content_type', 'content_id')
        indexes = [
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['-engagement_rate']),
            models.Index(fields=['-quality_score']),
            models.Index(fields=['-view_count']),
        ]

    def __str__(self):
        return f"{self.content_type} analytics - {self.view_count} views"

    @property
    def engagement_score(self):
        """Calculate engagement score based on multiple factors."""
        if self.view_count == 0:
            return 0.0

        # Weight different engagement types
        weighted_engagement = (
            (self.dislike_count * -1.0) +
            (self.like_count * 1.0) +
            (self.comment_count * 2.0) +
            (self.share_count * 3.0) +
            (self.reply_count * 1.5)
        )

        return min((weighted_engagement / self.view_count) * 100, 100.0)


class SearchAnalytics(models.Model):
    """
    Track search queries, results, and user interactions with search functionality.
    Provides insights into search patterns and result relevance.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Search details
    query = models.TextField()
    query_hash = models.CharField(max_length=64, db_index=True)  # Hash for deduplication
    normalized_query = models.TextField()  # Cleaned/normalized version
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)

    # Search context
    SEARCH_TYPES = [
        ('users', 'User Search'),
        ('communities', 'Community Search'),
        ('posts', 'Post Search'),
        ('global', 'Global Search'),
    ]
    search_type = models.CharField(max_length=20, choices=SEARCH_TYPES)
    filters_applied = models.JSONField(default=dict, blank=True)
    sort_criteria = models.CharField(max_length=50, blank=True)

    # Results metrics
    total_results = models.PositiveIntegerField(default=0)
    results_page = models.PositiveIntegerField(default=1)
    results_per_page = models.PositiveIntegerField(default=20)

    # Performance metrics
    search_time_ms = models.FloatField(default=0.0)
    database_query_time_ms = models.FloatField(default=0.0)
    elasticsearch_time_ms = models.FloatField(null=True, blank=True)

    # User interaction tracking
    clicked_results = models.JSONField(default=list, blank=True)  # Position and item clicked
    click_through_rate = models.FloatField(default=0.0)
    first_click_position = models.PositiveIntegerField(null=True, blank=True)
    time_to_first_click_ms = models.FloatField(null=True, blank=True)

    # Search success indicators
    resulted_in_action = models.BooleanField(default=False)  # Purchase, contact, etc.
    user_refined_search = models.BooleanField(default=False)  # Modified query
    zero_results = models.BooleanField(default=False)

    # Geographic and device info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country_code = models.CharField(max_length=2, blank=True)
    device_type = models.CharField(max_length=20, blank=True)

    # Additional metadata
    suggested_terms = models.JSONField(default=list, blank=True)
    autocomplete_used = models.BooleanField(default=False)
    voice_search = models.BooleanField(default=False)

    # Timestamps
    searched_at = models.DateTimeField(auto_now_add=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['query_hash']),
            models.Index(fields=['search_type', '-searched_at']),
            models.Index(fields=['user', '-searched_at']),
            models.Index(fields=['-search_time_ms']),
            models.Index(fields=['zero_results', '-searched_at']),
            models.Index(fields=['-click_through_rate']),
        ]

    def __str__(self):
        return f"Search: '{self.query[:50]}' - {self.total_results} results"

    @property
    def relevance_score(self):
        """Calculate search result relevance based on user interactions."""
        if self.total_results == 0:
            return 0.0

        ctr_score = self.click_through_rate * 40  # 40% weight for CTR
        result_score = min((self.total_results / 10) * 20, 20)  # 20% for having results
        action_score = 40 if self.resulted_in_action else 0  # 40% if led to action

        return ctr_score + result_score + action_score


class DailyAnalytics(models.Model):
    """Daily aggregated analytics."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True)

    # User metrics
    new_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    total_users = models.PositiveIntegerField(default=0)

    # Content metrics
    new_posts = models.PositiveIntegerField(default=0)
    new_comments = models.PositiveIntegerField(default=0)
    total_likes = models.PositiveIntegerField(default=0)
    total_shares = models.PositiveIntegerField(default=0)

    # Engagement metrics
    total_interactions = models.PositiveIntegerField(default=0)
    avg_session_duration = models.DurationField(null=True, blank=True)
    bounce_rate = models.FloatField(default=0.0)

    # System metrics
    avg_response_time = models.FloatField(default=0.0)
    error_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history



    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        """Indexes for performance and unique constraint on date."""
        indexes = [
            models.Index(fields=['-date']),
        ]

    def __str__(self):
        return f"Analytics for {self.date}"


class UserAnalytics(models.Model):
    """
    Enhanced user-specific analytics with detailed behavior tracking.
    Tracks user engagement patterns, preferences, and platform usage.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='analytics'
    )

    # Content engagement metrics
    total_posts = models.PositiveIntegerField(default=0)
    total_comments = models.PositiveIntegerField(default=0)
    total_likes_given = models.PositiveIntegerField(default=0)
    total_likes_received = models.PositiveIntegerField(default=0)
    total_shares_made = models.PositiveIntegerField(default=0)
    total_shares_received = models.PositiveIntegerField(default=0)


    # Community engagement
    communities_joined = models.PositiveIntegerField(default=0)
    communities_created = models.PositiveIntegerField(default=0)
    community_posts = models.PositiveIntegerField(default=0)
    community_moderation_actions = models.PositiveIntegerField(default=0)

    # Social metrics
    followers_gained = models.PositiveIntegerField(default=0)
    followers_lost = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    mutual_connections = models.PositiveIntegerField(default=0)

    # Session and activity patterns
    total_sessions = models.PositiveIntegerField(default=0)
    total_page_views = models.PositiveIntegerField(default=0)
    total_time_spent = models.DurationField(default=timezone.timedelta(0))
    avg_session_duration = models.DurationField(null=True, blank=True)
    longest_session_duration = models.DurationField(null=True, blank=True)
    peak_activity_hour = models.PositiveIntegerField(null=True, blank=True)
    most_active_day_of_week = models.PositiveIntegerField(null=True, blank=True)

    # Search and discovery behavior
    total_searches = models.PositiveIntegerField(default=0)
    successful_searches = models.PositiveIntegerField(default=0)
    user_searches = models.PositiveIntegerField(default=0)
    avg_search_results_clicked = models.FloatField(default=0.0)

    # Recommendation engagement
    recommendations_shown = models.PositiveIntegerField(default=0)
    recommendations_clicked = models.PositiveIntegerField(default=0)
    recommendations_acted_upon = models.PositiveIntegerField(default=0)
    recommendation_feedback_given = models.PositiveIntegerField(default=0)

    # Content quality and reputation
    content_quality_score = models.FloatField(default=0.0)
    reputation_score = models.FloatField(default=0.0)
    trust_score = models.FloatField(default=0.0)  # Based on successful transactions
    helpfulness_score = models.FloatField(default=0.0)  # Based on helpful content

    # Device and platform usage
    mobile_sessions = models.PositiveIntegerField(default=0)
    desktop_sessions = models.PositiveIntegerField(default=0)
    tablet_sessions = models.PositiveIntegerField(default=0)
    preferred_platform = models.CharField(max_length=20, blank=True)

    # Geographic patterns
    countries_accessed_from = models.JSONField(default=list, blank=True)
    most_common_location = models.CharField(max_length=100, blank=True)
    timezone_preferences = models.JSONField(default=dict, blank=True)

    # Feature usage tracking
    features_used = models.JSONField(default=list, blank=True)
    advanced_features_adopted = models.PositiveIntegerField(default=0)
    feature_adoption_rate = models.FloatField(default=0.0)

    # Conversion and retention metrics
    days_since_registration = models.PositiveIntegerField(default=0)
    days_active = models.PositiveIntegerField(default=0)
    retention_score = models.FloatField(default=0.0)
    churn_risk_score = models.FloatField(default=0.0)

    # Personalization data
    interests = models.JSONField(default=list, blank=True)
    preferred_categories = models.JSONField(default=list, blank=True)
    browsing_patterns = models.JSONField(default=dict, blank=True)

    # Performance indicators
    engagement_score = models.FloatField(default=0.0)
    activity_level = models.CharField(
        max_length=20,
        choices=[
            ('very_low', 'Very Low'),
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('very_high', 'Very High'),
        ],
        default='low'
    )

    # Timestamps
    last_calculated = models.DateTimeField(auto_now=True)
    last_activity_date = models.DateTimeField(null=True, blank=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    class Meta:
        indexes = [
            models.Index(fields=['user', '-last_calculated']),
            models.Index(fields=['-engagement_score']),
            models.Index(fields=['-reputation_score']),
            models.Index(fields=['activity_level', '-last_calculated']),
            models.Index(fields=['-churn_risk_score']),
        ]

    def __str__(self):
        return f"Analytics for {self.user.user.username}"

    @property
    def overall_engagement_rate(self):
        """Calculate overall engagement rate across all activities."""
        total_actions = (
            self.total_posts + self.total_comments +
            self.total_likes_given + self.total_shares_made
        )
        if self.total_sessions == 0:
            return 0.0
        return (total_actions / self.total_sessions) * 100

    @property
    def recommendation_conversion_rate(self):
        """Calculate how often user acts on recommendations."""
        if self.recommendations_shown == 0:
            return 0.0
        return (self.recommendations_acted_upon / self.recommendations_shown) * 100

    def increment_page_views(self, count=1):
        """
        Increment the total page views counter.

        Args:
            count (int): Number of page views to add (default: 1)
        """
        self.total_page_views += count
        self.save(update_fields=['total_page_views'])

    @classmethod
    def increment_user_page_views(cls, user_profile, count=1):
        """
        Increment page views for a user (creates UserAnalytics if doesn't exist).

        Args:
            user_profile: UserProfile instance
            count (int): Number of page views to add (default: 1)
        """
        analytics, created = cls.objects.get_or_create(
            user=user_profile,
            defaults={'total_page_views': 0}
        )
        analytics.increment_page_views(count)
        return analytics

    @property
    def platform_preference_score(self):
        """Calculate platform preference distribution."""
        total_sessions = self.mobile_sessions + self.desktop_sessions + self.tablet_sessions
        if total_sessions == 0:
            return {'mobile': 0, 'desktop': 0, 'tablet': 0}

        return {
            'mobile': (self.mobile_sessions / total_sessions) * 100,
            'desktop': (self.desktop_sessions / total_sessions) * 100,
            'tablet': (self.tablet_sessions / total_sessions) * 100,
        }


class SystemMetric(models.Model):
    """System-wide performance metrics."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    METRIC_TYPES = [
        ('response_time', 'Response Time'),
        ('cpu_usage', 'CPU Usage'),
        ('memory_usage', 'Memory Usage'),
        ('database_query_time', 'Database Query Time'),
        ('cache_hit_rate', 'Cache Hit Rate'),
        ('error_rate', 'Error Rate'),
        ('active_users', 'Active Users'),
        ('concurrent_connections', 'Concurrent Connections'),
    ]

    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    value = models.FloatField()
    additional_data = models.JSONField(default=dict, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history



    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    # Restoration tracking fields
    class Meta:
        """Indexes for performance and ordering by recorded time."""
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['metric_type', '-recorded_at']),
        ]

    def __str__(self):
        return f"{self.metric_type}: {self.value}"


class ErrorLog(models.Model):
    """Error tracking and logging."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ERROR_LEVELS = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]

    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    level = models.CharField(max_length=10, choices=ERROR_LEVELS)
    message = models.TextField()
    stack_trace = models.TextField(blank=True)

    # Context
    url = models.URLField(blank=True)
    method = models.CharField(max_length=10, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Additional data
    extra_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history



    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    # Restoration tracking fields
    class Meta:
        """Indexes for performance and ordering by creation date."""
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['level', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_resolved', '-created_at']),
        ]

    def __str__(self):
        return f"{self.level.upper()}: {self.message[:50]}"


class AuthenticationMetric(models.Model):
    """
    Track authentication performance metrics for JWT-first optimization.
    Records timing data, authentication methods, and success rates.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Authentication details
    AUTH_METHODS = [
        ('jwt_valid', 'JWT Valid (Direct)'),
        ('jwt_expired_session_renewal', 'JWT Expired - Session Renewal'),
        ('session_only', 'Session Only (Legacy)'),
        ('unauthenticated', 'Unauthenticated'),
        ('authentication_failed', 'Authentication Failed'),
    ]

    auth_method = models.CharField(max_length=30, choices=AUTH_METHODS)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True
    )
    session_id = models.CharField(max_length=100, blank=True)

    # Performance metrics (in milliseconds)
    jwt_validation_time = models.FloatField(
        null=True, blank=True, help_text="Time to validate JWT token (ms)"
    )
    session_lookup_time = models.FloatField(
        null=True, blank=True, help_text="Time to lookup session data (ms)"
    )
    total_auth_time = models.FloatField(
        help_text="Total authentication processing time (ms)"
    )

    # Request context
    endpoint = models.CharField(max_length=200, blank=True)
    http_method = models.CharField(max_length=10, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Success tracking
    success = models.BooleanField()
    error_message = models.TextField(blank=True)

    # JWT details
    jwt_renewed = models.BooleanField(default=False)
    token_age_seconds = models.PositiveIntegerField(null=True, blank=True)
    token_remaining_seconds = models.PositiveIntegerField(
        null=True, blank=True
    )

    # Additional metadata
    additional_data = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['auth_method', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['success', '-timestamp']),
            models.Index(fields=['jwt_renewed', '-timestamp']),
            models.Index(fields=['-total_auth_time']),
        ]

    def __str__(self):
        return (f"{self.auth_method} - {self.total_auth_time:.2f}ms "
                f"({self.timestamp})")

    @property
    def performance_grade(self):
        """Calculate performance grade based on total auth time."""
        if self.total_auth_time <= 10:
            return 'A'  # Excellent
        elif self.total_auth_time <= 25:
            return 'B'  # Good
        elif self.total_auth_time <= 50:
            return 'C'  # Average
        elif self.total_auth_time <= 100:
            return 'D'  # Poor
        else:
            return 'F'  # Very Poor


class AuthenticationReport(models.Model):
    """
    Daily/hourly aggregated authentication analytics for reporting.
    Provides insights into authentication patterns and performance.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Time period
    REPORT_TYPES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    report_type = models.CharField(max_length=10, choices=REPORT_TYPES)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()

    # Authentication method usage counts
    jwt_valid_count = models.PositiveIntegerField(default=0)
    jwt_expired_session_renewal_count = models.PositiveIntegerField(default=0)
    session_only_count = models.PositiveIntegerField(default=0)
    unauthenticated_count = models.PositiveIntegerField(default=0)
    authentication_failed_count = models.PositiveIntegerField(default=0)

    # Performance metrics (averages in milliseconds)
    avg_jwt_validation_time = models.FloatField(default=0.0)
    avg_session_lookup_time = models.FloatField(default=0.0)
    avg_total_auth_time = models.FloatField(default=0.0)

    # Performance percentiles
    p50_auth_time = models.FloatField(default=0.0)
    p95_auth_time = models.FloatField(default=0.0)
    p99_auth_time = models.FloatField(default=0.0)

    # Success rates (percentages)
    overall_success_rate = models.FloatField(default=0.0)
    jwt_success_rate = models.FloatField(default=0.0)
    session_success_rate = models.FloatField(default=0.0)

    # JWT renewal tracking
    jwt_renewals_count = models.PositiveIntegerField(default=0)
    avg_token_age_at_renewal = models.FloatField(default=0.0)

    # Unique metrics
    unique_users_count = models.PositiveIntegerField(default=0)
    unique_sessions_count = models.PositiveIntegerField(default=0)

    # Top endpoints
    top_endpoints = models.JSONField(default=list, blank=True)
    error_patterns = models.JSONField(default=list, blank=True)

    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-period_start']
        unique_together = ('report_type', 'period_start')
        indexes = [
            models.Index(fields=['report_type', '-period_start']),
            models.Index(fields=['-generated_at']),
            models.Index(fields=['-avg_total_auth_time']),
        ]

    def __str__(self):
        return (f"{self.report_type.title()} Auth Report "
                f"({self.period_start.date()})")

    @property
    def total_requests(self):
        """Calculate total authentication requests in this period."""
        return (
            self.jwt_valid_count +
            self.jwt_expired_session_renewal_count +
            self.session_only_count +
            self.unauthenticated_count +
            self.authentication_failed_count
        )

    @property
    def jwt_optimization_impact(self):
        """Calculate performance improvement from JWT-first approach."""
        if self.session_only_count == 0:
            return 0.0

        jwt_requests = self.jwt_valid_count
        total_auth_requests = jwt_requests + self.session_only_count

        if total_auth_requests == 0:
            return 0.0

        # Assume session lookup takes 3x longer than JWT validation
        estimated_session_time = (
            self.avg_session_lookup_time or
            (self.avg_jwt_validation_time * 3)
        )
        jwt_time = self.avg_jwt_validation_time or 5.0

        time_saved = (jwt_requests * (estimated_session_time - jwt_time))
        total_time = (
            (jwt_requests * jwt_time) +
            (self.session_only_count * estimated_session_time)
        )

        if total_time == 0:
            return 0.0

        return (time_saved / total_time) * 100  # Percentage improvement


class SessionAnalytic(models.Model):
    """
    Track session lifecycle and management performance.
    Monitors session creation, renewal, and cleanup patterns.
    Single record per session with event-specific fields and counters.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Session details
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Lifecycle events (for reference - not used as field)
    SESSION_EVENTS = [
        ('created', 'Session Created'),
        ('renewed', 'Session Renewed'),
        ('expired', 'Session Expired'),
        ('ended', 'Session Ended'),
        ('cleanup', 'Automated Cleanup'),
    ]

    # Session metadata
    created_at = models.DateTimeField()
    last_activity = models.DateTimeField()
    expires_at = models.DateTimeField()

    # === EVENT-SPECIFIC FIELDS AND COUNTERS ===

    # Creation event (happens once)
    creation_time_ms = models.FloatField(
        help_text="Time to create session (ms)"
    )
    created_event_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When creation event was recorded"
    )

    # Renewal events (can happen multiple times)
    renewal_count = models.PositiveIntegerField(default=0)
    last_renewal_time_ms = models.FloatField(
        null=True, blank=True, help_text="Time for last renewal (ms)"
    )
    total_renewal_time_ms = models.FloatField(
        default=0.0, help_text="Cumulative renewal time (ms)"
    )
    avg_renewal_time_ms = models.FloatField(
        default=0.0, help_text="Average renewal time (ms)"
    )
    last_renewed_at = models.DateTimeField(null=True, blank=True)
    first_renewed_at = models.DateTimeField(null=True, blank=True)

    # Smart renewal tracking
    smart_renewals = models.PositiveIntegerField(default=0)
    last_smart_renewal_at = models.DateTimeField(null=True, blank=True)
    unnecessary_renewals_prevented = models.PositiveIntegerField(default=0)

    # Expiry events (can be checked multiple times)
    expiry_check_count = models.PositiveIntegerField(default=0)
    last_expiry_check_time_ms = models.FloatField(
        null=True, blank=True, help_text="Time for last expiry check (ms)"
    )
    total_expiry_check_time_ms = models.FloatField(
        default=0.0, help_text="Cumulative expiry check time (ms)"
    )
    last_expired_checked_at = models.DateTimeField(null=True, blank=True)
    session_actually_expired = models.BooleanField(default=False)
    session_expired_at = models.DateTimeField(null=True, blank=True)

    # Ended events (manual session termination)
    ended_count = models.PositiveIntegerField(default=0)
    last_ended_time_ms = models.FloatField(
        null=True, blank=True, help_text="Time for last session end (ms)"
    )
    last_ended_checked_at = models.DateTimeField(null=True, blank=True)
    manually_ended_at = models.DateTimeField(null=True, blank=True)
    ended_reason = models.CharField(
        max_length=100, blank=True,
        help_text="Specific reason for session termination"
    )

    # Cleanup events (automated cleanup)
    cleanup_count = models.PositiveIntegerField(default=0)
    last_cleanup_time_ms = models.FloatField(
        null=True, blank=True, help_text="Time for last cleanup (ms)"
    )
    total_cleanup_time_ms = models.FloatField(
        default=0.0, help_text="Cumulative cleanup time (ms)"
    )
    last_cleanup_checked_at = models.DateTimeField(null=True, blank=True)
    automated_cleanup_at = models.DateTimeField(null=True, blank=True)

    # General performance tracking
    lookup_count = models.PositiveIntegerField(default=0)
    total_processing_time_ms = models.FloatField(
        default=0.0, help_text="Sum of all event processing times"
    )

    # Location and device info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location_data = models.JSONField(default=dict, blank=True)

    # Session end details
    ended_at = models.DateTimeField(null=True, blank=True)
    end_reason = models.CharField(max_length=20, blank=True)

    # Additional data
    additional_metadata = models.JSONField(default=dict, blank=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['session_id']),
            models.Index(fields=['-last_activity']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['-lookup_count']),
        ]

    def __str__(self):
        return f"Session {self.session_id[:8]}... for {self.user.username}"

    @property
    def session_duration(self):
        """Calculate total session duration."""
        end_time = self.ended_at or timezone.now()
        return end_time - self.created_at

    @property
    def efficiency_score(self):
        """Calculate session efficiency based on renewals and lookups."""
        if self.lookup_count == 0:
            return 100.0

        # Smart renewals should reduce unnecessary operations
        efficiency = ((self.smart_renewals + self.unnecessary_renewals_prevented) /
                     max(self.lookup_count, 1)) * 100

        return min(efficiency, 100.0)


class CommunityAnalytics(models.Model):
    """
    Real-time and historical analytics for communities.

    Tracks visitor metrics (not member-based):
    - Real-time visitor counts (authenticated + anonymous) from Redis
    - Visitor division breakdown and cross-division analytics
    - Engagement metrics (threads, posts, comments, likes)

    Architecture:
    - Visitor tracking: Synced from Redis via visitor_tracker
    - Page views: Use PageAnalytics model (query by community URL)
    - Conversions: Use AnonymousSession model (query by content_id)

    This model focuses on visitor and engagement metrics only.
    No redundant page view or conversion fields.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Community reference
    community = models.ForeignKey(
        'communities.Community',
        on_delete=models.CASCADE,
        related_name='analytics'
    )

    # Real-time visitor metrics (from Redis visitor tracker)
    current_visitors = models.PositiveIntegerField(
        default=0,
        help_text="Total current visitors (auth + anonymous)"
    )
    current_authenticated_visitors = models.PositiveIntegerField(
        default=0,
        help_text="Current authenticated visitors"
    )
    current_anonymous_visitors = models.PositiveIntegerField(
        default=0,
        help_text="Current anonymous visitors"
    )

    # Peak visitor metrics
    peak_visitors_today = models.PositiveIntegerField(default=0)
    peak_visitors_this_week = models.PositiveIntegerField(default=0)
    peak_visitors_this_month = models.PositiveIntegerField(default=0)

    # Daily visitor activity (unique visitors)
    daily_unique_visitors = models.PositiveIntegerField(
        default=0,
        help_text="Unique visitors today (by fingerprint/user_id)"
    )
    daily_authenticated_visitors = models.PositiveIntegerField(default=0)
    daily_anonymous_visitors = models.PositiveIntegerField(default=0)

    # Weekly/Monthly visitor activity
    weekly_unique_visitors = models.PositiveIntegerField(default=0)
    monthly_unique_visitors = models.PositiveIntegerField(default=0)

    # Division visitor tracking
    visitor_divisions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dict of division_id: visitor_count"
    )
    cross_division_visits = models.PositiveIntegerField(
        default=0,
        help_text="Count of visitors from different divisions"
    )
    cross_division_percentage = models.FloatField(
        default=0.0,
        help_text="Percentage of cross-division visits"
    )

    # Engagement metrics (content creation)
    total_threads_today = models.PositiveIntegerField(default=0)
    total_posts_today = models.PositiveIntegerField(default=0)
    total_comments_today = models.PositiveIntegerField(default=0)
    total_likes_today = models.PositiveIntegerField(default=0)

    # Legacy member metrics (kept for backward compatibility)
    # TODO: Remove after migration to visitor-only tracking
    new_members_today = models.PositiveIntegerField(default=0)
    new_members_this_week = models.PositiveIntegerField(default=0)
    new_members_this_month = models.PositiveIntegerField(default=0)

    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    date = models.DateField(auto_now_add=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    class Meta:
        """Indexes for performance and unique constraint."""
        unique_together = ('community', 'date')
        indexes = [
            models.Index(fields=['community', '-date']),
            models.Index(fields=['community', 'current_visitors']),
            models.Index(fields=['community', '-daily_unique_visitors']),
            models.Index(fields=['-last_updated']),
            models.Index(fields=['-cross_division_visits']),
        ]

    def __str__(self):
        return f"Analytics for {self.community.name} on {self.date}"

    def update_from_redis(self, visitor_data):
        """
        Update analytics from Redis visitor tracker data.

        Args:
            visitor_data: Dict from visitor_tracker.get_visitor_stats()
                {
                    'total_visitors': int,
                    'authenticated_visitors': int,
                    'anonymous_visitors': int,
                    'visitor_divisions': dict,
                    'cross_division_count': int,
                    ...
                }
        """
        self.current_visitors = visitor_data.get('total_visitors', 0)
        self.current_authenticated_visitors = visitor_data.get(
            'authenticated_visitors', 0
        )
        self.current_anonymous_visitors = visitor_data.get(
            'anonymous_visitors', 0
        )

        # Update peak visitors
        if self.current_visitors > self.peak_visitors_today:
            self.peak_visitors_today = self.current_visitors

        # Update division tracking
        self.visitor_divisions = visitor_data.get('visitor_divisions', {})
        self.cross_division_visits = visitor_data.get(
            'cross_division_count', 0
        )

        # Calculate cross-division percentage
        if self.current_visitors > 0:
            self.cross_division_percentage = (
                self.cross_division_visits / self.current_visitors
            ) * 100
        else:
            self.cross_division_percentage = 0.0

        self.save(update_fields=[
            'current_visitors',
            'current_authenticated_visitors',
            'current_anonymous_visitors',
            'peak_visitors_today',
            'visitor_divisions',
            'cross_division_visits',
            'cross_division_percentage',
            'last_updated'
        ])


class AnonymousSession(models.Model):
    """
    Track anonymous browsing sessions for analytics.

    Stores temporary session data for users who are not logged in.
    Used for conversion tracking, content analytics, and behavior analysis.

    Privacy-friendly:
    - No personal identification
    - 90-day retention policy
    - Auto-cleanup via Celery tasks
    - Device fingerprint is non-personal hash
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identification (no user link until conversion)
    device_fingerprint = models.CharField(
        max_length=128,
        db_index=True,
        help_text="Device fingerprint hash for anonymous identification"
    )

    # Session lifecycle
    session_start = models.DateTimeField(auto_now_add=True, db_index=True)
    session_end = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)

    # Network/Device metadata
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('mobile', 'Mobile'),
            ('desktop', 'Desktop'),
            ('tablet', 'Tablet'),
            ('unknown', 'Unknown'),
        ],
        default='unknown'
    )
    browser = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=50, blank=True)

    # Location (optional, from IP geolocation)
    country = models.CharField(max_length=2, blank=True, db_index=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)

    # Behavioral metrics
    pages_visited = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(
        default=0,
        help_text="Total session duration in seconds"
    )

    # Page tracking
    landing_page = models.URLField(max_length=500)
    exit_page = models.URLField(max_length=500, blank=True)
    referrer = models.URLField(max_length=500, blank=True)

    # UTM tracking for marketing attribution
    utm_source = models.CharField(max_length=100, blank=True, db_index=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    utm_term = models.CharField(max_length=100, blank=True)
    utm_content = models.CharField(max_length=100, blank=True)

    # Conversion tracking
    converted_to_user = models.ForeignKey(
        UserProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='converted_from_anonymous',
        help_text="Links to user account if anonymous visitor signed up"
    )
    converted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Status flags
    is_active = models.BooleanField(default=True, db_index=True)
    is_bot = models.BooleanField(
        default=False,
        help_text="Flagged as bot based on behavior patterns"
    )
    bot_score = models.FloatField(
        default=0.0,
        help_text="Bot likelihood score 0-1 (1 = definitely bot)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['device_fingerprint', '-session_start']),
            models.Index(fields=['is_active', '-session_start']),
            models.Index(fields=['converted_to_user', '-converted_at']),
            models.Index(fields=['-session_start']),
            models.Index(fields=['utm_source', '-session_start']),
            models.Index(fields=['country', '-session_start']),
        ]
        ordering = ['-session_start']

    def __str__(self):
        status = "Active" if self.is_active else "Ended"
        converted = ""
        if self.converted_to_user:
            username = self.converted_to_user.user.username
            converted = f" → {username}"
        fp_short = self.device_fingerprint[:8]
        return f"Anonymous {fp_short}... ({status}){converted}"

    def finalize_session(self):
        """Mark session as ended and calculate final metrics."""
        if not self.is_active:
            return

        self.is_active = False
        self.session_end = timezone.now()

        if self.session_start:
            self.duration_seconds = int(
                (self.session_end - self.session_start).total_seconds()
            )

        self.save(update_fields=[
            'is_active', 'session_end',
            'duration_seconds', 'updated_at'
        ])

    def mark_conversion(self, user_profile):
        """Mark this anonymous session as converted to a user account."""
        self.converted_to_user = user_profile
        self.converted_at = timezone.now()
        self.is_active = False

        if not self.session_end:
            self.session_end = self.converted_at
            if self.session_start:
                self.duration_seconds = int(
                    (self.session_end - self.session_start).total_seconds()
                )

        self.save(update_fields=[
            'converted_to_user', 'converted_at', 'is_active',
            'session_end', 'duration_seconds', 'updated_at'
        ])

    @property
    def conversion_rate(self):
        """Calculate if this session converted (for aggregation queries)."""
        return 1.0 if self.converted_to_user else 0.0

    @property
    def engagement_score(self):
        """Calculate engagement score based on pages and duration."""
        if self.pages_visited == 0:
            return 0.0

        # Score based on pages (max 50 points) + duration (max 50 points)
        page_score = min(self.pages_visited * 5, 50)
        # 1 point per minute of engagement
        duration_score = min(self.duration_seconds / 60, 50)

        return page_score + duration_score


class AnonymousPageView(models.Model):
    """
    Track individual page views for anonymous sessions.

    Provides detailed analytics on anonymous user journey and behavior.
    Links to AnonymousSession for session-level aggregation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to session
    session = models.ForeignKey(
        AnonymousSession,
        on_delete=models.CASCADE,
        related_name='page_views'
    )

    # Page identification
    url = models.URLField(max_length=500)
    url_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Django URL name if available"
    )
    page_type = models.CharField(
        max_length=50,
        choices=[
            ('home', 'Homepage'),
            ('community', 'Community Page'),
            ('post', 'Post Detail'),
            ('profile', 'User Profile'),
            ('search', 'Search Results'),
            ('about', 'About/Info Page'),
            ('auth', 'Login/Signup Page'),
            ('other', 'Other'),
        ],
        db_index=True
    )
    page_title = models.CharField(max_length=200, blank=True)

    # Timing
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    time_on_page_seconds = models.PositiveIntegerField(
        default=0,
        help_text="Time spent on this page in seconds"
    )

    # Navigation
    referrer = models.URLField(max_length=500, blank=True)
    is_entry_page = models.BooleanField(
        default=False,
        help_text="First page in the session"
    )
    is_exit_page = models.BooleanField(
        default=False,
        help_text="Last page in the session"
    )

    # Engagement metrics (optional - from frontend tracking)
    scroll_depth = models.PositiveSmallIntegerField(
        default=0,
        help_text="Percentage of page scrolled (0-100)"
    )
    interactions = models.PositiveIntegerField(
        default=0,
        help_text="Number of clicks, hovers, etc."
    )

    # Content-specific tracking
    content_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of viewed content (post, community, etc.)"
    )
    content_type = models.CharField(max_length=50, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['session', '-viewed_at']),
            models.Index(fields=['page_type', '-viewed_at']),
            models.Index(fields=['-viewed_at']),
            models.Index(fields=['content_id', 'content_type']),
        ]
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.page_type}: {self.url[:50]} at {self.viewed_at}"


class PageAnalytics(models.Model):
    """
    Aggregate page analytics by day.

    Privacy-friendly daily aggregates without individual tracking.
    One record per page per day with summarized metrics.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Page identification
    url_path = models.CharField(max_length=500, db_index=True)
    page_type = models.CharField(
        max_length=50,
        choices=[
            ('home', 'Homepage'),
            ('community', 'Community Page'),
            ('post', 'Post Detail'),
            ('profile', 'User Profile'),
            ('search', 'Search Results'),
            ('about', 'About/Info Page'),
            ('auth', 'Login/Signup Page'),
            ('other', 'Other'),
        ],
        db_index=True
    )

    # Date aggregation
    date = models.DateField(db_index=True)

    # View counts (aggregated)
    total_views = models.PositiveIntegerField(default=0)
    authenticated_views = models.PositiveIntegerField(default=0)
    anonymous_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(
        default=0,
        help_text="Unique device fingerprints"
    )

    # Engagement metrics (averages)
    avg_time_on_page = models.FloatField(
        default=0.0,
        help_text="Average time in seconds"
    )
    avg_scroll_depth = models.FloatField(
        default=0.0,
        help_text="Average scroll percentage"
    )
    avg_interactions = models.FloatField(default=0.0)

    # Device breakdown
    mobile_views = models.PositiveIntegerField(default=0)
    desktop_views = models.PositiveIntegerField(default=0)
    tablet_views = models.PositiveIntegerField(default=0)

    # Geographic breakdown (top 5 countries)
    top_countries = models.JSONField(
        default=list,
        blank=True,
        help_text="List of dicts: [{'country': 'US', 'count': 100}, ...]"
    )

    # Traffic sources (top 5)
    top_referrers = models.JSONField(
        default=list,
        blank=True,
        help_text="Top referring URLs"
    )

    # Bounce/Exit metrics
    bounce_count = models.PositiveIntegerField(
        default=0,
        help_text="Views where user left immediately"
    )
    exit_count = models.PositiveIntegerField(
        default=0,
        help_text="Views where user ended session on this page"
    )

    # Calculated rates
    bounce_rate = models.FloatField(default=0.0)
    exit_rate = models.FloatField(default=0.0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['url_path', 'date']]
        indexes = [
            models.Index(fields=['-date', 'page_type']),
            models.Index(fields=['url_path', '-date']),
            models.Index(fields=['-total_views']),
        ]
        ordering = ['-date', '-total_views']

    def __str__(self):
        return f"{self.url_path} on {self.date} ({self.total_views} views)"

    def update_metrics(self):
        """Recalculate derived metrics."""
        if self.total_views > 0:
            self.bounce_rate = (self.bounce_count / self.total_views) * 100
            self.exit_rate = (self.exit_count / self.total_views) * 100
        else:
            self.bounce_rate = 0.0
            self.exit_rate = 0.0

        self.save(update_fields=['bounce_rate', 'exit_rate', 'updated_at'])
