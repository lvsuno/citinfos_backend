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
    """Real-time and historical analytics for communities."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Community reference
    community = models.ForeignKey(
        'communities.Community',
        on_delete=models.CASCADE,
        related_name='analytics'
    )

    # Real-time metrics (updated frequently)
    current_online_members = models.PositiveIntegerField(default=0)
    peak_online_today = models.PositiveIntegerField(default=0)
    peak_online_this_week = models.PositiveIntegerField(default=0)
    peak_online_this_month = models.PositiveIntegerField(default=0)

    # Activity metrics (updated daily)
    daily_active_members = models.PositiveIntegerField(default=0)
    weekly_active_members = models.PositiveIntegerField(default=0)
    monthly_active_members = models.PositiveIntegerField(default=0)

    # Engagement metrics
    total_threads_today = models.PositiveIntegerField(default=0)
    total_posts_today = models.PositiveIntegerField(default=0)
    total_comments_today = models.PositiveIntegerField(default=0)
    total_likes_today = models.PositiveIntegerField(default=0)

    # Growth metrics
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
        """Indexes for performance and unique constraint on community and date."""
        unique_together = ('community', 'date')
        indexes = [
            models.Index(fields=['community', '-date']),
            models.Index(fields=['community', 'current_online_members']),
            models.Index(fields=['-last_updated']),
        ]

    def __str__(self):
        return f"Analytics for {self.community.name} on {self.date}"
