"""
Enhanced serializers for unified attachment system and multiple polls support.

These serializers replace the existing ones to provide:
1. Unified attachment handling via PostMedia
2. Multiple polls per post support
3. Backward compatibility during migration
"""

from rest_framework import serializers
from content.models import Post, PostMedia
from polls.models import Poll, PollOption
from accounts.models import UserProfile


class EnhancedPostMediaSerializer(serializers.ModelSerializer):
    """Enhanced serializer for PostMedia with additional metadata."""

    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    type = serializers.CharField(source='media_type', read_only=True)
    preview = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = PostMedia
        fields = [
            'id', 'media_type', 'type', 'file', 'file_url', 'thumbnail',
            'thumbnail_url', 'description', 'order', 'file_size',
            'preview', 'name'
        ]
        read_only_fields = [
            'id', 'file_url', 'thumbnail_url', 'file_size',
            'type', 'preview', 'name'
        ]

    def validate_file(self, value):
        """Validate file upload including duration for video/audio files."""
        if not value:
            return value

        # Get media type from initial_data or instance
        media_type = (self.initial_data.get('media_type') or
                      getattr(self.instance, 'media_type', None))

        if (media_type in ['video', 'audio'] and
                hasattr(value, 'temporary_file_path')):
            try:
                duration = self._get_file_duration(value.temporary_file_path())
                if duration and duration > 300:  # 5 minutes = 300 seconds
                    duration_str = f"{duration//60}:{duration%60:02d}"
                    raise serializers.ValidationError(
                        f'{media_type.title()} files must be 5 minutes '
                        f'or less. Duration: {duration_str}'
                    )
            except Exception:
                # If we can't validate duration, log and continue
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not validate {media_type} duration")

        return value

    def _get_file_duration(self, file_path):
        """Get duration of video/audio file in seconds."""
        try:
            import subprocess
            import json

            # Use ffprobe to get media information
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                info = json.loads(result.stdout)

                # Get duration from format
                if 'format' in info and 'duration' in info['format']:
                    return float(info['format']['duration'])

                # Fallback to stream duration
                for stream in info.get('streams', []):
                    if (stream.get('codec_type') in ['video', 'audio'] and
                            'duration' in stream):
                        return float(stream['duration'])

        except Exception:
            pass

        return None

    def get_file_url(self, obj):
        """Get the full URL for the file."""
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def get_thumbnail_url(self, obj):
        """Get the full URL for the thumbnail."""
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None

    def get_preview(self, obj):
        """Get preview URL (same as file_url for compatibility)."""
        return self.get_file_url(obj)

    def get_name(self, obj):
        """Get file name from the file field."""
        if obj.file:
            try:
                import os
                return os.path.basename(obj.file.name)
            except (AttributeError, ValueError):
                return None
        return None

    def get_file_size(self, obj):
        """Get file size if available."""
        try:
            return obj.file.size if obj.file else None
        except (ValueError, OSError):
            return None


class EnhancedPollOptionSerializer(serializers.ModelSerializer):
    """Enhanced serializer for poll options with percentage calculation."""

    vote_percentage = serializers.ReadOnlyField()
    user_has_voted = serializers.SerializerMethodField()

    class Meta:
        model = PollOption
        fields = [
            'id', 'text', 'order', 'votes_count', 'vote_percentage', 'image', 'user_has_voted'
        ]
        read_only_fields = ['id', 'votes_count', 'vote_percentage', 'user_has_voted']

    def get_user_has_voted(self, obj):
        """Check if current user has voted for this option."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        from polls.models import PollVote
        return PollVote.objects.filter(option=obj,
            voter=request.user, is_deleted=False).exists()


class PollOptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating poll options."""

    # Include id to support updates
    id = serializers.UUIDField(required=False)

    class Meta:
        model = PollOption
        fields = ['id', 'text', 'order', 'image']


class PollCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating polls with options."""

    options = PollOptionCreateSerializer(many=True, required=False)
    # Include id to support updates
    id = serializers.UUIDField(required=False)

    class Meta:
        model = Poll
        fields = [
            'id', 'question', 'multiple_choice', 'anonymous_voting',
            'expires_at', 'options'
        ]


class EnhancedPollSerializer(serializers.ModelSerializer):
    """Enhanced serializer for polls with options and voting status."""

    options = EnhancedPollOptionSerializer(many=True, read_only=True)
    is_expired = serializers.ReadOnlyField()
    user_has_voted = serializers.SerializerMethodField()
    user_votes = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = [
            'id', 'question', 'order', 'multiple_choice', 'anonymous_voting',
            'expires_at', 'total_votes', 'voters_count', 'is_active',
            'is_closed', 'is_expired', 'options', 'user_has_voted', 'user_votes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_votes', 'voters_count', 'is_expired',
            'user_has_voted', 'user_votes', 'created_at', 'updated_at'
        ]

    def get_user_has_voted(self, obj):
        """Check if current user has voted in this poll."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        from polls.models import PollVote
        return PollVote.objects.filter(poll=obj,
            voter=request.user, is_deleted=False).exists()

    def get_user_votes(self, obj):
        """Get current user's votes for this poll."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return []

        from polls.models import PollVote
        votes = PollVote.objects.filter(poll=obj, voter=request.user, is_deleted=False)
        return [vote.option.id for vote in votes]


class UnifiedPostSerializer(serializers.ModelSerializer):
    """
    Unified Post serializer that handles both legacy and new attachment systems.

    This serializer:
    1. Returns PostMedia attachments as the primary attachment system
    2. Includes legacy fields for backward compatibility during migration
    3. Supports multiple polls per post
    4. Provides attachment statistics and metadata
    """

    # Author information
    author_username = serializers.CharField(
        source='author.user.username', read_only=True
    )
    author_name = serializers.CharField(
        source='author.display_name', read_only=True
    )

    # Community information (for reposts from communities)
    community_name = serializers.CharField(
        source='community.name', read_only=True
    )
    community_slug = serializers.CharField(
        source='community.slug', read_only=True
    )
    community_type = serializers.CharField(
        source='community.community_type', read_only=True
    )

    # Unified attachment system
    attachments = EnhancedPostMediaSerializer(
        source='media', many=True, read_only=True
    )
    attachment_count = serializers.ReadOnlyField()
    has_attachments = serializers.ReadOnlyField()
    attachments_by_type = serializers.SerializerMethodField()

    # Multiple polls support
    polls = EnhancedPollSerializer(many=True, read_only=True)
    polls_count = serializers.ReadOnlyField()
    has_polls = serializers.ReadOnlyField()

    # User interaction status
    user_has_liked = serializers.SerializerMethodField()
    user_has_disliked = serializers.SerializerMethodField()
    user_has_shared = serializers.SerializerMethodField()
    user_has_reposted = serializers.SerializerMethodField()

    # Comments with nested structure
    comments = serializers.SerializerMethodField()
    mentions = serializers.SerializerMethodField()

    # Parent post for reposts
    parent_post = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            # Basic post fields
            'id', 'author', 'author_username', 'author_name', 'community',
            'community_name', 'community_slug', 'community_type',
            'content', 'post_type', 'visibility', 'parent_post',

            # Link preview
            'link_image',

            # Unified attachment system
            'attachments', 'attachment_count', 'has_attachments',
            'attachments_by_type',

            # Multiple polls
            'polls', 'polls_count', 'has_polls',

            # Engagement metrics
            'likes_count', 'dislikes_count', 'comments_count', 'shares_count',
            'repost_count', 'views_count', 'trend_score',

            # User interaction status
            'user_has_liked', 'user_has_disliked', 'user_has_shared',
            'user_has_reposted',

            # Comments with nested structure
            'comments', 'mentions',

            # Flags and metadata
            'is_pinned', 'is_edited', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author_username', 'author_name', 'community_name',
            'attachments', 'attachment_count', 'has_attachments',
            'attachments_by_type',
            'polls', 'polls_count', 'has_polls',
            'likes_count', 'dislikes_count', 'comments_count', 'shares_count',
            'repost_count', 'views_count', 'trend_score',
            'user_has_liked', 'user_has_disliked', 'user_has_shared',
            'user_has_reposted', 'comments', 'is_edited', 'created_at',
            'updated_at'
        ]

    def _get_user_profile(self):
        """Helper to get current user's profile."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserProfile.objects.filter(user=request.user, is_deleted=False).first()
        return None

    def get_attachments_by_type(self, obj):
        """Get attachments grouped by media type - properly serialized."""
        attachments_by_type = {}
        for media in obj.media.all():
            media_type = media.media_type
            if media_type not in attachments_by_type:
                attachments_by_type[media_type] = []

            # Serialize each media object
            serializer = EnhancedPostMediaSerializer(
                media, context=self.context
            )
            attachments_by_type[media_type].append(serializer.data)

        return attachments_by_type

    def get_user_has_liked(self, obj):
        """Check if user has liked this post."""
        profile = self._get_user_profile()
        if not profile:
            return False
        from django.contrib.contenttypes.models import ContentType
        from content.models import Like
        ct = ContentType.objects.get_for_model(Post)
        return Like.objects.filter(user=profile, content_type=ct, object_id=obj.id, is_deleted=False).exists()

    def get_user_has_disliked(self, obj):
        """Check if user has disliked this post."""
        profile = self._get_user_profile()
        if not profile:
            return False
        from django.contrib.contenttypes.models import ContentType
        from content.models import Dislike
        ct = ContentType.objects.get_for_model(Post)
        return Dislike.objects.filter(user=profile, content_type=ct, object_id=obj.id, is_deleted=False).exists()

    def get_user_has_shared(self, obj):
        """Check if user has shared this post."""
        profile = self._get_user_profile()
        if not profile:
            return False
        from content.models import DirectShare
        return DirectShare.objects.filter(sender=profile, post=obj, is_deleted=False).exists()

    def get_user_has_reposted(self, obj):
        """Check if user has reposted this post."""
        profile = self._get_user_profile()
        if not profile:
            return False
        profile = self.context['request'].user.profile
        return Post.objects.filter(author=profile, parent_post=obj, post_type='repost', is_deleted=False).exists()

    def get_comments(self, obj):
        """Get all comments for this post with nested structure."""
        from content.serializers import CommentNestedSerializer
        # Get top-level comments (no parent)
        top_level_comments = obj.comments.filter(parent=None, is_deleted=False)
        return CommentNestedSerializer(
            top_level_comments, many=True, context=self.context
        ).data

    def get_mentions(self, obj):
        """Get mention mappings (username -> user_profile_id) for this post."""
        mentions = {}
        for mention in obj.content_mentions.select_related('mentioned_user__user'):
            mentions[mention.mentioned_user.user.username] = str(mention.mentioned_user.id)
        return mentions

    def get_parent_post(self, obj):
        """Get the parent post for reposts with full serialization."""
        if obj.parent_post and obj.is_repost:
            # Use the same serializer class to serialize the parent post
            serializer = UnifiedPostSerializer(
                obj.parent_post, context=self.context)
            return serializer.data
        return None


class UnifiedPostCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating posts with unified attachment system.

    This serializer allows:
    1. Creating posts with multiple attachments via nested PostMedia
    2. Creating posts with multiple polls
    3. Backward compatibility with legacy media fields during migration
    """

    # Nested attachment creation
    attachments = EnhancedPostMediaSerializer(
        source='media', many=True, required=False
    )

    # Nested poll creation - use write-capable serializer
    polls = PollCreateSerializer(many=True, required=False)

    class Meta:
        model = Post
        fields = [
            # Basic post fields
            'id', 'community', 'content', 'post_type', 'visibility',
            'link_image',  # Link preview only
            'attachments', 'polls', 'is_pinned'
        ]

    def create(self, validated_data):
        """Create post with attachments and polls."""
        attachments_data = validated_data.pop('media', [])
        polls_data = validated_data.pop('polls', [])

        # Create the post
        post = Post.objects.create(**validated_data)

        # Create attachments
        for i, attachment_data in enumerate(attachments_data):
            PostMedia.objects.create(
                post=post,
                order=i + 1,
                **attachment_data
            )

        # Create polls
        for i, poll_data in enumerate(polls_data):
            options_data = poll_data.pop('options', [])
            # Remove order from poll_data to avoid conflict
            poll_data.pop('order', None)
            poll = Poll.objects.create(
                post=post,
                order=i + 1,
                **poll_data
            )

            # Create poll options
            for j, option_data in enumerate(options_data):
                # Remove order from option_data to avoid conflict
                option_data.pop('order', None)
                PollOption.objects.create(
                    poll=poll,
                    order=j + 1,
                    **option_data
                )

        return post

    def update(self, instance, validated_data):
        """Update post, attachments, and polls."""
        # Handle attachments update (simplified - full implementation would
        # handle adding/removing/reordering)
        attachments_data = validated_data.pop('media', None)
        polls_data = validated_data.pop('polls', None)

        # Update basic post fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update polls if provided
        if polls_data is not None:
            self._update_polls(instance, polls_data)

        # For attachments, we could implement add/remove logic here
        # Currently keeping the existing attachments unchanged

        return instance

    def _update_polls(self, post_instance, polls_data):
        """Update polls for a post."""
        from polls.models import Poll, PollOption

        # Get existing polls for this post
        existing_polls = post_instance.polls.filter(is_deleted=False)

        # Create a mapping of existing polls by ID for updates
        existing_poll_map = {str(poll.id): poll for poll in existing_polls}

        updated_poll_ids = set()

        for poll_data in polls_data:
            poll_id = poll_data.get('id')

            if poll_id and str(poll_id) in existing_poll_map:
                # Update existing poll
                poll = existing_poll_map[str(poll_id)]

                # Check if poll can be updated
                has_votes = poll.options.filter(votes_count__gt=0).exists()

                # Allow update if:
                # 1. No votes yet, OR
                # 2. Author is the only voter (voters_count = 1 and request user is post author)
                can_update = not has_votes

                if has_votes and poll.voters_count == 1:
                    # Check if the requesting user is the post author
                    request = self.context.get('request')
                    if request and request.user == poll.post.author.user:
                        can_update = True

                if can_update:
                    poll.question = poll_data.get('question', poll.question)
                    poll.multiple_choice = poll_data.get(
                        'multiple_choice', poll.multiple_choice
                    )
                    poll.anonymous_voting = poll_data.get(
                        'anonymous_voting', poll.anonymous_voting
                    )

                    # Handle expiration date with default extension
                    new_expires_at = poll_data.get('expires_at')
                    if new_expires_at:
                        poll.expires_at = new_expires_at
                    elif poll.expires_at:
                        # Extend existing expiration by 1 day
                        from django.utils import timezone
                        from datetime import timedelta
                        poll.expires_at = poll.expires_at + timedelta(days=1)
                    else:
                        # Set default expiration to 1 day from now
                        from django.utils import timezone
                        from datetime import timedelta
                        poll.expires_at = timezone.now() + timedelta(days=1)

                    poll.save()

                    # Update poll options
                    options_data = poll_data.get('options', [])
                    self._update_poll_options(poll, options_data)

                updated_poll_ids.add(str(poll_id))
            else:
                # Create new poll
                from django.utils import timezone
                from datetime import timedelta

                # Set default expiration to 1 day from now if not provided
                expires_at = poll_data.get('expires_at')
                if not expires_at:
                    expires_at = timezone.now() + timedelta(days=1)

                poll = Poll.objects.create(
                    post=post_instance,
                    question=poll_data['question'],
                    multiple_choice=poll_data.get(
                        'multiple_choice', False
                    ),
                    anonymous_voting=poll_data.get(
                        'anonymous_voting', False
                    ),
                    expires_at=expires_at
                )

                # Create poll options
                for option_data in poll_data.get('options', []):
                    option_text = (
                        option_data.get('text') or
                        option_data.get('option_text', '')
                    )
                    PollOption.objects.create(
                        poll=poll,
                        text=option_text
                    )

        # Note: We don't delete existing polls to preserve vote data
        # In production, you might want more sophisticated handling

    def _update_poll_options(self, poll, options_data):
        """Update options for a poll."""
        from polls.models import PollOption

        # Get existing options
        existing_options = poll.options.all()
        existing_option_map = {str(opt.id): opt for opt in existing_options}

        updated_option_ids = set()

        for option_data in options_data:
            option_id = option_data.get('id')

            if option_id and str(option_id) in existing_option_map:
                # Update existing option
                option = existing_option_map[str(option_id)]

                # Check if option can be updated
                can_update_option = option.votes_count == 0

                # Also allow update if author is the only voter in the poll
                if not can_update_option and poll.voters_count == 1:
                    request = self.context.get('request')
                    if request and request.user == poll.post.author.user:
                        can_update_option = True

                if can_update_option:
                    # Handle both 'option_text' and 'text' field names
                    new_text = (
                        option_data.get('text') or
                        option_data.get('option_text')
                    )
                    if new_text:
                        option.text = new_text
                        option.save()
                updated_option_ids.add(str(option_id))
            else:
                # Create new option
                option_text = (
                    option_data.get('text') or
                    option_data.get('option_text', '')
                )
                if option_text:
                    PollOption.objects.create(
                        poll=poll,
                        text=option_text
                    )

        # Remove options that weren't updated
        for option in existing_options:
            not_updated = str(option.id) not in updated_option_ids
            if not_updated:
                # Check if option can be deleted
                can_delete = option.votes_count == 0

                # Also allow deletion if author is the only voter in the poll
                if not can_delete and poll.voters_count == 1:
                    request = self.context.get('request')
                    if request and request.user == poll.post.author.user:
                        can_delete = True

                if can_delete:
                    option.delete()

    def validate(self, data):
        """Validate post creation/update."""
        content = data.get('content', '').strip()
        post_type = data.get('post_type', 'text')
        attachments = data.get('media', [])
        polls = data.get('polls', [])

        # Validate content requirements
        has_empty_content = not content and not attachments and not polls
        if post_type == 'text' and has_empty_content:
            raise serializers.ValidationError(
                'Text posts must have content, attachments, or polls.'
            )

        # Validate attachment limits
        if len(attachments) > 10:  # Configurable limit
            raise serializers.ValidationError(
                'Maximum 10 attachments allowed per post.'
            )

        # Validate poll limits
        if len(polls) > 5:  # Configurable limit
            raise serializers.ValidationError(
                'Maximum 5 polls allowed per post.'
            )

        return data


# Convenience aliases for backward compatibility
PostSerializer = UnifiedPostSerializer
PostCreateUpdateSerializer = UnifiedPostCreateUpdateSerializer
PostMediaSerializer = EnhancedPostMediaSerializer
