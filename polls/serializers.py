from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Poll, PollOption, PollVote, PollVoter
from content.models import Post
from accounts.models import UserProfile


class PollOptionSerializer(serializers.ModelSerializer):
    """Serializer for PollOption model."""
    vote_percentage = serializers.ReadOnlyField()
    user_has_voted = serializers.SerializerMethodField()

    class Meta:
        model = PollOption
        fields = [
            'id', 'poll', 'text', 'order', 'votes_count',
            'vote_percentage', 'image', 'user_has_voted', 'created_at'
        ]
        read_only_fields = ['id', 'votes_count', 'vote_percentage',
                           'user_has_voted', 'created_at']

    def get_user_has_voted(self, obj):
        """Check if current user has voted for this option."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PollVote.objects.filter(
                option=obj,
                voter=request.user
            ).exists()
        return False


class PollOptionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating poll options."""
    class Meta:
        model = PollOption
        fields = ['text', 'order', 'image']


class PollVoteSerializer(serializers.ModelSerializer):
    """Serializer for PollVote model."""
    voter_username = serializers.CharField(source='voter.username', read_only=True)
    option_text = serializers.CharField(source='option.text', read_only=True)
    poll_question = serializers.CharField(source='poll.question', read_only=True)

    class Meta:
        model = PollVote
        fields = [
            'id', 'poll', 'poll_question', 'option', 'option_text',
            'voter', 'voter_username', 'ip_address', 'user_agent', 'created_at'
        ]
        read_only_fields = [
            'id', 'poll_question', 'option_text', 'voter_username', 'created_at'
        ]


class PollVoteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating poll votes."""
    class Meta:
        model = PollVote
        fields = ['poll', 'option']

    def validate(self, attrs):
        """Validate vote creation."""
        poll = attrs.get('poll')
        option = attrs.get('option')
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required to vote")

        # Check if poll is active
        if not poll.is_active or poll.is_closed:
            raise serializers.ValidationError("This poll is not active")

        # Check if poll has expired
        if poll.is_expired:
            raise serializers.ValidationError("This poll has expired")

        # Check if option belongs to the poll
        if option.poll != poll:
            raise serializers.ValidationError("Option does not belong to this poll")

        # Check if user has already voted (for single choice polls)
        if not poll.multiple_choice:
            existing_vote = PollVote.objects.filter(
                poll=poll,
                voter=request.user
            ).exists()
            if existing_vote:
                raise serializers.ValidationError(
                    "You have already voted in this poll"
                )

        return attrs


class PollSerializer(serializers.ModelSerializer):
    """Complete serializer for Poll model."""
    post_content = serializers.CharField(source='post.content', read_only=True)
    post_author = serializers.CharField(source='post.author.user.username', read_only=True)
    options = PollOptionSerializer(many=True, read_only=True)
    user_has_voted = serializers.SerializerMethodField()
    user_votes = serializers.SerializerMethodField()
    is_expired = serializers.ReadOnlyField()

    class Meta:
        model = Poll
        fields = [
            'id', 'post', 'post_content', 'post_author', 'question',
            'multiple_choice', 'anonymous_voting', 'expires_at', 'total_votes',
            'voters_count', 'is_active', 'is_closed', 'is_expired',
            'options', 'user_has_voted', 'user_votes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'post_content', 'post_author', 'total_votes', 'voters_count',
            'is_expired', 'options', 'user_has_voted', 'user_votes',
            'created_at', 'updated_at'
        ]

    def get_user_has_voted(self, obj):
        """Check if current user has voted in this poll."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PollVote.objects.filter(poll=obj, voter=request.user).exists()
        return False

    def get_user_votes(self, obj):
        """Get current user's votes for this poll."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            votes = PollVote.objects.filter(poll=obj, voter=request.user)
            return [vote.option.id for vote in votes]
        return []


class PollCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating polls."""
    options = PollOptionCreateUpdateSerializer(many=True, required=False)

    class Meta:
        model = Poll
        fields = [
            'post', 'question', 'multiple_choice', 'anonymous_voting',
            'expires_at', 'is_active', 'options'
        ]
        extra_kwargs = {
            'post': {'required': False}
        }

    def create(self, validated_data):
        """Create poll with options."""
        options_data = validated_data.pop('options', [])
        poll = Poll.objects.create(**validated_data)

        # Create options
        for i, option_data in enumerate(options_data):
            option_data['order'] = i
            PollOption.objects.create(poll=poll, **option_data)

        return poll

    def update(self, instance, validated_data):
        """Update poll and options."""
        options_data = validated_data.pop('options', None)

        # Update poll fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update options if provided
        if options_data is not None:
            # Delete existing options
            instance.options.all().delete()

            # Create new options
            for i, option_data in enumerate(options_data):
                option_data['order'] = i
                PollOption.objects.create(poll=instance, **option_data)

        return instance


class PollVoterSerializer(serializers.ModelSerializer):
    """Serializer for PollVoter model."""
    voter_username = serializers.CharField(source='voter.username', read_only=True)
    poll_question = serializers.CharField(source='poll.question', read_only=True)

    class Meta:
        model = PollVoter
        fields = [
            'id', 'poll', 'poll_question', 'voter', 'voter_username',
            'votes_count', 'first_vote_at', 'last_vote_at'
        ]
        read_only_fields = [
            'id', 'poll_question', 'voter_username', 'votes_count',
            'first_vote_at', 'last_vote_at'
        ]
