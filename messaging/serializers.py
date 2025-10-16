"""Serializers for the messaging app."""

from rest_framework import serializers
from accounts.models import UserProfile
from .models import ChatRoom, Message, MessageRead, UserPresence


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for user list in messaging context."""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source='profile_picture', read_only=True)
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'full_name', 'avatar', 'is_online']

    def get_full_name(self, obj):
        """Get user's full name."""
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return obj.user.username

    def get_is_online(self, obj):
        """Check if user is currently online."""
        try:
            presence = obj.presence
            return presence.status in ['online', 'away', 'busy']
        except UserPresence.DoesNotExist:
            return False


# MessageAttachment model not yet implemented
# class MessageAttachmentSerializer(serializers.ModelSerializer):
#     """Serializer for message attachments."""
#
#     class Meta:
#         model = MessageAttachment  # Not yet implemented
#         fields = [
#             'id', 'file', 'file_type', 'file_size', 'original_name',
#             'uploaded_at'
#         ]
#         read_only_fields = ['id', 'file_size', 'uploaded_at']


class MessageReadSerializer(serializers.ModelSerializer):
    """Serializer for message read status."""
    user_username = serializers.CharField(source='user.user.username', read_only=True)

    class Meta:
        model = MessageRead
        fields = ['id', 'user', 'user_username', 'read_at']
        read_only_fields = ['id', 'read_at']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for messages."""
    sender_username = serializers.CharField(source='sender.user.username', read_only=True)
    sender_avatar = serializers.ImageField(source='sender.profile_picture', read_only=True)
    # attachments = MessageAttachmentSerializer(many=True, read_only=True)  # Not yet implemented
    read_by = MessageReadSerializer(many=True, read_only=True)
    is_read_by_current_user = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'room', 'sender', 'sender_username', 'sender_avatar',
            'content', 'message_type', 'attachments', 'read_by',
            'is_read_by_current_user', 'is_edited', 'updated_at',
            'reply_to', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'created_at', 'is_edited', 'updated_at']

    def get_is_read_by_current_user(self, obj):
        """Check if current user has read this message."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                profile = request.user.profile
                return obj.read_by.filter(user=profile).exists()
            except UserProfile.DoesNotExist:
                return False
        return False


class MessageCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating messages."""

    class Meta:
        model = Message
        fields = ['content', 'message_type', 'reply_to']


class ChatRoomParticipantSerializer(serializers.ModelSerializer):
    """Serializer for chat room participants."""
    username = serializers.CharField(source='user.username', read_only=True)
    display_name = serializers.CharField(read_only=True)
    avatar = serializers.ImageField(source='profile_picture', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'display_name', 'avatar']


class ChatRoomSerializer(serializers.ModelSerializer):
    """Serializer for chat rooms."""
    created_by_username = serializers.CharField(source='created_by.user.username', read_only=True)
    participants_list = ChatRoomParticipantSerializer(source='participants', many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    is_participant = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'name', 'room_type', 'description', 'image',
            'created_by', 'created_by_username', 'participants_list',
            'messages_count', 'last_message', 'unread_count',
            'is_participant', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'messages_count', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        """Get the last message in the room."""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'id': last_message.id,
                'content': last_message.content,
                'sender_username': last_message.sender.user.username,
                'created_at': last_message.created_at,
                'message_type': last_message.message_type
            }
        return None

    def get_unread_count(self, obj):
        """Get unread message count for current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                profile = request.user.profile
                # Count messages not read by current user
                return obj.messages.exclude(
                    read_by__user=profile
                ).count()
            except UserProfile.DoesNotExist:
                return 0
        return 0

    def get_is_participant(self, obj):
        """Check if current user is a participant."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                profile = request.user.profile
                return obj.participants.filter(id=profile.id).exists()
            except UserProfile.DoesNotExist:
                return False
        return False


class ChatRoomCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating chat rooms."""
    participants = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = ChatRoom
        fields = ['name', 'room_type', 'description', 'image', 'participants']

    def validate_participants(self, value):
        """Validate participants."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Ensure current user is included in participants
            try:
                current_profile = request.user.profile
                if current_profile not in value:
                    value.append(current_profile)
            except UserProfile.DoesNotExist:
                pass
        return value

    def validate(self, data):
        """Validate chat room data."""
        if data.get('room_type') == 'direct' and len(data.get('participants', [])) != 2:
            raise serializers.ValidationError(
                "Direct message rooms must have exactly 2 participants."
            )
        return data


class UserPresenceSerializer(serializers.ModelSerializer):
    """Serializer for user presence/online status."""
    username = serializers.CharField(source='user.user.username', read_only=True)
    display_name = serializers.CharField(source='user.display_name', read_only=True)
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = UserPresence
        fields = [
            'id', 'user', 'username', 'display_name', 'status',
            'last_seen', 'custom_status', 'status_emoji', 'is_online'
        ]
        read_only_fields = ['id', 'user', 'last_seen']

    def get_is_online(self, obj):
        """Get if user is considered online."""
        return obj.is_online()


class UserPresenceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user presence."""

    class Meta:
        model = UserPresence
        fields = ['status', 'custom_status', 'status_emoji']
