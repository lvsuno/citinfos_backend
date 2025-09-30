from rest_framework import serializers
from accounts.models import UserProfile
from .models import (
    Post, Comment, Like, Dislike, PostSee, PostMedia, Mention,
    DirectShare, DirectShareRecipient,
    ContentReport, ModerationQueue, AutoModerationAction,
    ContentModerationRule, BotDetectionEvent, BotDetectionProfile,
    ContentRecommendation, ContentSimilarity, UserContentPreferences,
    RecommendationFeedback,
    ContentExperiment, UserContentExperimentAssignment,
    ContentExperimentMetric, ContentExperimentResult
)

# =====================
# CORE CONTENT SERIALIZERS
# =====================


class PostMediaSerializer(serializers.ModelSerializer):
    """Serializer for PostMedia model."""
    class Meta:
        model = PostMedia
        fields = [
            'id', 'post', 'media_type', 'file', 'thumbnail', 'order'
        ]
        read_only_fields = ['id']


class PostSeeSerializer(serializers.ModelSerializer):
    """Serializer for PostSee model."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )
    post_id = serializers.UUIDField(source='post.id', read_only=True)

    class Meta:
        model = PostSee
        fields = [
            'id', 'user', 'user_username', 'post', 'post_id', 'seen_at'
        ]
        read_only_fields = ['id', 'user_username', 'post_id', 'seen_at']


class PostSerializer(serializers.ModelSerializer):
    """Serializer for Post model with nested comments and interaction data."""
    author_username = serializers.CharField(
        source='author.user.username', read_only=True
    )
    author_name = serializers.CharField(
        source='author.display_name', read_only=True
    )
    community_name = serializers.CharField(
        source='community.name', read_only=True
    )
    user_has_liked = serializers.SerializerMethodField()
    user_has_disliked = serializers.SerializerMethodField()
    user_has_shared = serializers.SerializerMethodField()
    user_has_reposted = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    mentions = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'author_username', 'author_name', 'community',
            'community_name', 'content', 'post_type', 'visibility',
            'link_image', 'is_pinned', 'is_edited', 'likes_count',
            'dislikes_count', 'comments_count', 'shares_count',
            'repost_count', 'views_count', 'user_has_liked',
            'user_has_disliked', 'user_has_shared', 'user_has_reposted',
            'comments', 'mentions', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author_username', 'author_name', 'community_name',
            'is_edited', 'likes_count', 'dislikes_count', 'comments_count',
            'shares_count', 'repost_count', 'views_count', 'user_has_liked',
            'user_has_disliked', 'user_has_shared', 'user_has_reposted',
            'comments', 'created_at', 'updated_at'
        ]

    def validate(self, data):
        content = data.get('content', '').strip()
        post_type = data.get('post_type', 'text')
        if post_type == 'text' and not content:
            raise serializers.ValidationError(
                'Content cannot be empty for text posts.'
            )
        return data

    def _get_user_profile(self):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserProfile.objects.filter(user=request.user).first()
        return None

    def get_user_has_liked(self, obj):
        profile = self._get_user_profile()
        if not profile:
            return False
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(Post)
        return Like.objects.filter(
            user=profile, content_type=ct, object_id=obj.id
        ).exists()

    def get_user_has_disliked(self, obj):
        profile = self._get_user_profile()
        if not profile:
            return False
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(Post)
        return Dislike.objects.filter(
            user=profile, content_type=ct, object_id=obj.id
        ).exists()

    def get_user_has_shared(self, obj):
        profile = self._get_user_profile()
        if not profile:
            return False
        return DirectShare.objects.filter(
            sender=profile, post=obj
        ).exists()

    def get_user_has_reposted(self, obj):
        profile = self._get_user_profile()
        if not profile:
            return False
        return Post.objects.filter(author=profile, parent_post=obj, post_type='repost', is_deleted=False).exists()

    def get_comments(self, obj):
        """Get all comments for this post with full nested structure."""
        # Get all top-level comments (no parent)
        top_level_comments = Comment.objects.filter(
            post=obj,
            parent=None,
            is_deleted=False
        ).select_related(
            'author__user'
        ).prefetch_related(
            'replies'
        ).order_by('created_at')

        # Serialize the comments
        comments_data = []
        for comment in top_level_comments:
            comment_serializer = CommentNestedSerializer(comment, context=self.context)
            comments_data.append(comment_serializer.data)

        return comments_data

    def get_mentions(self, obj):
        """Get mention mappings (username -> user_profile_id) for this post."""
        mentions = {}
        for mention in obj.content_mentions.select_related('mentioned_user__user'):
            mentions[mention.mentioned_user.user.username] = str(mention.mentioned_user.id)
        return mentions


class CommentNestedSerializer(serializers.ModelSerializer):
    """Serializer for comments with nested replies and all interaction data."""
    author_username = serializers.CharField(
        source='author.user.username', read_only=True
    )
    author_name = serializers.CharField(
        source='author.display_name', read_only=True
    )
    user_has_liked = serializers.SerializerMethodField()
    user_has_disliked = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    mentions = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'author_username', 'author_name', 'parent',
            'content', 'is_edited', 'likes_count', 'dislikes_count',
            'replies_count', 'user_has_liked', 'user_has_disliked',
            'replies', 'mentions', 'created_at', 'updated_at'
        ]

    def _get_user_profile(self):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserProfile.objects.filter(user=request.user).first()
        return None

    def get_user_has_liked(self, obj):
        from django.contrib.contenttypes.models import ContentType
        profile = self._get_user_profile()
        if not profile:
            return False
        ct = ContentType.objects.get_for_model(Comment)
        return Like.objects.filter(
            user=profile, content_type=ct, object_id=obj.id
        ).exists()

    def get_user_has_disliked(self, obj):
        from django.contrib.contenttypes.models import ContentType
        profile = self._get_user_profile()
        if not profile:
            return False
        ct = ContentType.objects.get_for_model(Comment)
        return Dislike.objects.filter(
            user=profile, content_type=ct, object_id=obj.id
        ).exists()

    def get_replies(self, obj):
        """Get all replies to this comment."""
        replies = Comment.objects.filter(
            parent=obj,
            is_deleted=False
        ).select_related(
            'author__user'
        ).order_by('created_at')

        # Serialize the replies (recursive structure)
        replies_data = []
        for reply in replies:
            reply_serializer = CommentNestedSerializer(reply, context=self.context)
            replies_data.append(reply_serializer.data)

        return replies_data

    def get_mentions(self, obj):
        """Get mention mappings (username -> user_profile_id) for this comment."""
        mentions = {}
        for mention in obj.content_mentions.select_related('mentioned_user__user'):
            mentions[mention.mentioned_user.user.username] = str(mention.mentioned_user.id)
        return mentions


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating posts."""
    class Meta:
        model = Post
        fields = [
            'community', 'content', 'post_type', 'visibility',
            'link_image', 'is_pinned'
        ]

    def validate(self, data):
        content = data.get('content', '').strip()
        post_type = data.get('post_type', 'text')
        if post_type == 'text' and not content:
            raise serializers.ValidationError(
                'Content cannot be empty for text posts.'
            )
        return data


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model with user interaction data."""
    author_username = serializers.CharField(
        source='author.user.username', read_only=True
    )
    author_name = serializers.CharField(
        source='author.display_name', read_only=True
    )
    post_title = serializers.CharField(
        source='post.content', read_only=True
    )
    user_has_liked = serializers.SerializerMethodField()

    class Meta:
        """Serializer for Comment model."""
        model = Comment
        fields = [
            'id', 'post', 'post_title', 'author', 'author_username',
            'author_name', 'parent', 'content', 'is_edited', 'likes_count',
            'dislikes_count', 'replies_count', 'user_has_liked',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'post_title', 'author_username', 'author_name', 'is_edited',
            'likes_count', 'dislikes_count', 'replies_count', 'user_has_liked',
            'created_at', 'updated_at'
        ]

    def get_user_has_liked(self, obj):
        """Check if the requesting user has liked this comment."""
        from django.contrib.contenttypes.models import ContentType
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            profile = UserProfile.objects.filter(user=request.user).first()
            if not profile:
                return False
            ct = ContentType.objects.get_for_model(Comment)
            return Like.objects.filter(
                user=profile, content_type=ct, object_id=obj.id
            ).exists()
        return False


class CommentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating comments."""
    class Meta:
        model = Comment
        fields = ['id', 'post', 'parent', 'content']
        read_only_fields = ['id']


class LikeSerializer(serializers.ModelSerializer):
    """Serializer for Like model."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )
    content_object_str = serializers.CharField(
        source='content_object', read_only=True
    )

    class Meta:
        """Serializer for Like model."""
        model = Like
        fields = [
            'id', 'user', 'user_username', 'content_type', 'object_id',
            'content_object_str', 'created_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_username', 'content_object_str', 'created_at'
        ]


class DislikeSerializer(serializers.ModelSerializer):
    """Serializer for Dislike model."""
    class Meta:
        """Serializer for Dislike model."""
        model = Dislike
        fields = ['id', 'user', 'content_type', 'object_id', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class DirectShareRecipientSerializer(serializers.ModelSerializer):
    """Serializer for DirectShareRecipient model."""
    recipient_username = serializers.CharField(
        source='recipient.user.username', read_only=True
    )

    class Meta:
        """Serializer for DirectShareRecipient model."""
        model = DirectShareRecipient
        fields = [
            'id', 'direct_share', 'recipient', 'recipient_username',
            'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'direct_share', 'recipient_username', 'read_at',
            'created_at'
        ]


class DirectShareSerializer(serializers.ModelSerializer):
    """Serializer for DirectShare model with nested recipients."""
    sender_username = serializers.CharField(
        source='sender.user.username', read_only=True
    )
    deliveries = DirectShareRecipientSerializer(many=True, read_only=True)

    class Meta:
        """Serializer for DirectShare model."""
        model = DirectShare
        fields = [
            'id', 'sender', 'sender_username', 'post', 'note', 'created_at',
            'deliveries'
        ]
        read_only_fields = [
            'id', 'sender', 'sender_username', 'created_at', 'deliveries'
        ]


class DirectShareCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating DirectShare with recipient IDs."""
    recipient_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True,
        help_text='List of recipient profile IDs'
    )

    class Meta:
        """Serializer for creating DirectShare."""
        model = DirectShare
        fields = ['id', 'post', 'note', 'recipient_ids', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_recipient_ids(self, value):
        """Ensure at least one recipient is provided."""
        if not value:
            raise serializers.ValidationError(
                'At least one recipient is required'
            )
        return value

    def create(self, validated_data):
        """Create DirectShare and associated DirectShareRecipients."""
        recipient_ids = validated_data.pop('recipient_ids', [])
        sender = self.context['request'].user.profile
        direct_share = DirectShare.objects.create(
            sender=sender, **validated_data
        )
        recipients = UserProfile.objects.filter(id__in=recipient_ids)
        deliveries = [
            DirectShareRecipient(
                direct_share=direct_share, recipient=r
            ) for r in recipients
        ]
        DirectShareRecipient.objects.bulk_create(
            deliveries, ignore_conflicts=True
        )
        return direct_share


class MentionSerializer(serializers.ModelSerializer):
    """Serializer for Mention model."""
    mentioned_user_username = serializers.CharField(
        source='mentioned_user.user.username', read_only=True
    )
    mentioning_user_username = serializers.CharField(
        source='mentioning_user.user.username', read_only=True
    )
    post_content_preview = serializers.SerializerMethodField()
    comment_content_preview = serializers.SerializerMethodField()

    class Meta:
        """Serializer for Mention model."""
        model = Mention
        fields = [
            'id', 'post', 'comment', 'mentioned_user', 'mentioning_user',
            'mentioned_user_username', 'mentioning_user_username',
            'post_content_preview', 'comment_content_preview', 'created_at'
        ]
        read_only_fields = [
            'id', 'mentioning_user', 'mentioned_user_username',
            'mentioning_user_username', 'post_content_preview',
            'comment_content_preview', 'created_at'
        ]

    def get_post_content_preview(self, obj):
        """Get preview of post content if this is a post mention."""
        if obj.post:
            content = obj.post.content
            return content[:100] + "..." if len(content) > 100 else content
        return None

    def get_comment_content_preview(self, obj):
        """Get preview of comment content if this is a comment mention."""
        if obj.comment:
            content = obj.comment.content
            return content[:100] + "..." if len(content) > 100 else content
        return None


class MentionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating mentions."""

    class Meta:
        model = Mention
        fields = ['id', 'post', 'comment', 'mentioned_user', 'created_at']
        read_only_fields = ['id', 'mentioning_user', 'created_at']

    def validate(self, data):
        """Validate that either post or comment is provided, but not both."""
        post = data.get('post')
        comment = data.get('comment')

        if not post and not comment:
            raise serializers.ValidationError(
                "Either 'post' or 'comment' must be provided."
            )

        if post and comment:
            raise serializers.ValidationError(
                "Cannot mention in both post and comment simultaneously."
            )

        return data


# =====================
# MODERATION & BOT DETECTION SERIALIZERS
# =====================

class ContentReportSerializer(serializers.ModelSerializer):
    """Serializer for ContentReport model."""
    reporter_username = serializers.CharField(
        source='reporter.user.username', read_only=True
    )
    content_object_str = serializers.CharField(
        source='content_object', read_only=True
    )

    class Meta:
        """Serializer for ContentReport model."""
        model = ContentReport
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'reporter_username', 'content_object_str'
        ]


class ModerationQueueSerializer(serializers.ModelSerializer):
    """Serializer for ModerationQueue model."""
    content_object_str = serializers.CharField(
        source='content_object', read_only=True
    )
    assigned_to_username = serializers.CharField(
        source='assigned_to.user.username', read_only=True
    )
    reviewed_by_username = serializers.CharField(
        source='reviewed_by.user.username', read_only=True
    )
    resolved_by_username = serializers.CharField(
        source='resolved_by.user.username', read_only=True
    )

    class Meta:
        """Serializer for ModerationQueue model."""
        model = ModerationQueue
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'assigned_to_username',
            'reviewed_by_username', 'resolved_by_username',
            'content_object_str', 'assigned_to', 'reviewed_by',
            'resolved_by'
        ]


class AutoModerationActionSerializer(serializers.ModelSerializer):
    """Serializer for AutoModerationAction model."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        # Only require content_type and object_id on creation (POST)
        if request and request.method in ['PATCH', 'PUT']:
            self.fields['content_type'].required = False
            self.fields['object_id'].required = False

    content_object_str = serializers.CharField(
        source='content_object', read_only=True
    )
    target_user_username = serializers.CharField(
        source='target_user.user.username', read_only=True
    )
    reviewed_by_username = serializers.CharField(
        source='reviewed_by.user.username', read_only=True
    )

    class Meta:
        """Serializer for AutoModerationAction model."""
        model = AutoModerationAction
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'reviewed_by_username',
            'target_user_username', 'content_object_str', 'reviewed_by'
        ]


class ContentModerationRuleSerializer(serializers.ModelSerializer):
    """Serializer for ContentModerationRule model."""
    community_name = serializers.CharField(
        source='community.name', read_only=True
    )
    created_by_username = serializers.CharField(
        source='created_by.user.username', read_only=True
    )

    class Meta:
        """Serializer for ContentModerationRule model."""
        model = ContentModerationRule
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'community_name',
            'created_by_username', 'created_by'
        ]


class BotDetectionEventSerializer(serializers.ModelSerializer):
    """Serializer for BotDetectionEvent model."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )
    related_post_id = serializers.UUIDField(
        source='related_post.id', read_only=True
    )
    related_comment_id = serializers.UUIDField(
        source='related_comment.id', read_only=True
    )

    class Meta:
        """Serializer for BotDetectionEvent model."""
        model = BotDetectionEvent
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'user_username', 'related_post_id',
            'related_comment_id'
        ]


class BotDetectionProfileSerializer(serializers.ModelSerializer):
    """Serializer for BotDetectionProfile model."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )

    class Meta:
        """Serializer for BotDetectionProfile model."""
        model = BotDetectionProfile
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'user_username', 'created_at', 'updated_at'
        ]

# =====================
# RECOMMENDATION SYSTEM SERIALIZERS
# =====================

class ContentRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for ContentRecommendation model."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )
    content_object_str = serializers.CharField(
        source='content_object', read_only=True
    )

    class Meta:
        """Serializer for ContentRecommendation model."""
        model = ContentRecommendation
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'user_username', 'content_object_str'
        ]


class ContentSimilaritySerializer(serializers.ModelSerializer):
    """Serializer for ContentSimilarity model."""
    content_object_1_str = serializers.CharField(
        source='content_object_1', read_only=True
    )
    content_object_2_str = serializers.CharField(
        source='content_object_2', read_only=True
    )

    class Meta:
        """Serializer for ContentSimilarity model."""
        model = ContentSimilarity
        fields = '__all__'
        read_only_fields = [
            'id', 'calculated_at', 'content_object_1_str',
            'content_object_2_str'
        ]


class UserContentPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for UserContentPreferences model."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )

    class Meta:
        model = UserContentPreferences
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'user_username', 'created_at', 'updated_at'
        ]


class RecommendationFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for RecommendationFeedback model."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )
    recommendation_id = serializers.UUIDField(
        source='recommendation.id', read_only=True
    )

    class Meta:
        """Serializer for RecommendationFeedback model."""
        model = RecommendationFeedback
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'user_username', 'recommendation_id', 'created_at'
        ]
# =====================
# A/B TESTING SERIALIZERS
# =====================


class ContentExperimentSerializer(serializers.ModelSerializer):
    """Serializer for ContentExperiment model."""
    created_by_username = serializers.CharField(
        source='created_by.user.username', read_only=True
    )
    is_active = serializers.BooleanField(read_only=True)
    duration_days = serializers.SerializerMethodField()

    class Meta:
        """Serializer for ContentExperiment model."""
        model = ContentExperiment
        fields = [
            'id', 'name', 'description', 'control_algorithm',
            'test_algorithm', 'traffic_split', 'status', 'start_date',
            'end_date', 'created_at', 'updated_at', 'created_by',
            'created_by_username', 'is_active', 'duration_days'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by',
            'created_by_username', 'is_active', 'duration_days'
        ]

    def get_duration_days(self, obj):
        """Calculate duration in days between start_date and end_date."""
        if obj.start_date and obj.end_date:
            return (obj.end_date - obj.start_date).days
        return None

    def validate_traffic_split(self, value):
        """Ensure traffic split is between 0.0 and 1.0."""
        if not 0.0 <= value <= 1.0:
            raise serializers.ValidationError(
                'Traffic split must be between 0.0 and 1.0'
            )
        return value

    def validate(self, data):
        """Ensure control and test algorithms differ and dates are valid."""
        instance = getattr(self, 'instance', None)
        control_algorithm = data.get('control_algorithm')
        test_algorithm = data.get('test_algorithm')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if instance:
            control_algorithm = control_algorithm or instance.control_algorithm
            test_algorithm = test_algorithm or instance.test_algorithm
            start_date = start_date or instance.start_date
            end_date = end_date or instance.end_date
        if (control_algorithm and test_algorithm and
                control_algorithm == test_algorithm):
            raise serializers.ValidationError(
                'Control and test algorithms must be different'
            )
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError(
                'End date must be after start date'
            )
        return data


class UserContentExperimentAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for UserContentExperimentAssignment model."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )
    experiment_name = serializers.CharField(
        source='experiment.name', read_only=True
    )
    algorithm = serializers.SerializerMethodField()

    class Meta:
        """Serializer for UserContentExperimentAssignment model."""
        model = UserContentExperimentAssignment
        fields = [
            'id', 'user', 'user_username', 'experiment', 'experiment_name',
            'group', 'assigned_at', 'algorithm'
        ]
        read_only_fields = [
            'id', 'user_username', 'experiment_name', 'assigned_at',
            'algorithm'
        ]

    def get_algorithm(self, obj):
        """Get the algorithm used for the user's assignment."""
        return (
            obj.experiment.control_algorithm
            if obj.group == 'control'
            else obj.experiment.test_algorithm
        )


class ContentExperimentMetricSerializer(serializers.ModelSerializer):
    """Serializer for ContentExperimentMetric model."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )
    experiment_name = serializers.CharField(
        source='experiment.name', read_only=True
    )
    content_type_name = serializers.CharField(
        source='content_type.model', read_only=True
    )

    class Meta:
        """Serializer for ContentExperimentMetric model."""
        model = ContentExperimentMetric
        fields = [
            'id', 'experiment', 'experiment_name', 'user', 'user_username',
            'metric_type', 'value', 'count', 'algorithm_used', 'content_type',
            'content_type_name', 'object_id', 'recorded_at', 'metadata'
        ]
        read_only_fields = [
            'id', 'experiment_name', 'user_username', 'content_type_name',
            'recorded_at'
        ]


class ContentExperimentResultSerializer(serializers.ModelSerializer):
    """Serializer for ContentExperimentResult model."""
    experiment_name = serializers.CharField(
        source='experiment.name', read_only=True
    )
    analyzed_by_username = serializers.CharField(
        source='analyzed_by.user.username', read_only=True
    )
    improvement_direction = serializers.SerializerMethodField()
    significance_level = serializers.SerializerMethodField()

    class Meta:
        """Serializer for ContentExperimentResult model."""
        model = ContentExperimentResult
        fields = [
            'id', 'experiment', 'experiment_name', 'control_sample_size',
            'test_sample_size', 'control_avg_response_time',
            'test_avg_response_time', 'control_avg_accuracy',
            'test_avg_accuracy', 'control_engagement_rate',
            'test_engagement_rate', 'control_click_through_rate',
            'test_click_through_rate', 'control_conversion_rate',
            'test_conversion_rate', 'p_value', 'confidence_interval',
            'winner', 'improvement_percentage', 'improvement_direction',
            'significance_level', 'summary', 'detailed_analysis',
            'analyzed_at', 'analyzed_by', 'analyzed_by_username'
        ]
        read_only_fields = [
            'id', 'experiment_name', 'analyzed_by_username',
            'improvement_direction', 'significance_level', 'analyzed_at'
        ]

    def get_improvement_direction(self, obj):
        """Determine which algorithm performed better."""
        if obj.winner == 'test':
            return (
                f'Test algorithm ({obj.experiment.test_algorithm}) wins'
            )
        if obj.winner == 'control':
            return (
                'Control algorithm '
                f'({obj.experiment.control_algorithm}) wins'
            )
        return 'No significant difference'

    def get_significance_level(self, obj):
        """Interpret the p-value into significance levels."""
        if obj.p_value is None:
            return 'Unknown'
        if obj.p_value < 0.01:
            return 'Highly significant (p < 0.01)'
        if obj.p_value < 0.05:
            return 'Significant (p < 0.05)'
        if obj.p_value < 0.1:
            return 'Marginally significant (p < 0.1)'
        return 'Not significant (p >= 0.1)'


class ContentExperimentStatsSerializer(serializers.Serializer):
    """Serializer for summarizing experiment statistics."""
    experiment = serializers.DictField()
    sample_sizes = serializers.DictField()
    metrics = serializers.DictField()
    statistical_significance = serializers.DictField()

    class Meta:
        """Meta for ContentExperimentStatsSerializer."""
        fields = [
            'experiment', 'sample_sizes', 'metrics',
            'statistical_significance'
        ]
