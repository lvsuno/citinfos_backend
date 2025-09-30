"""Views for the messaging app with complete CRUD operations."""

from django.db import models
from django.db.models import Count, Q, Max
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from accounts.models import UserProfile
from accounts.permissions import NotDeletedUserPermission
from accounts.utils import get_active_profile_or_404
from .models import ChatRoom, Message, MessageRead
from .serializers import (
    ChatRoomSerializer, ChatRoomCreateUpdateSerializer,
    MessageSerializer, MessageCreateUpdateSerializer,
    MessageReadSerializer
)


class ChatRoomViewSet(viewsets.ModelViewSet):
    """ViewSet for managing chat rooms."""
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def get_queryset(self):
        """Get chat rooms where user is a participant."""
        profile = self.request.user.userprofile
        return ChatRoom.objects.filter(is_deleted=False,
            participants=profile).select_related('created_by').prefetch_related(
            'participants', 'messages'
        ).annotate(
            last_message_time=Max('messages__sent_at')
        ).order_by('-last_message_time', '-updated_at')

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action in ['create', 'update', 'partial_update']:
            return ChatRoomCreateUpdateSerializer
        return ChatRoomSerializer

    def perform_create(self, serializer):
        """Create chat room with current user as creator."""
        profile = self.request.user.userprofile
        chat_room = serializer.save(created_by=profile)

        # Add participants (including creator)
        participants = serializer.validated_data.get('participants', [])
        if profile not in participants:
            participants.append(profile)
        chat_room.participants.set(participants)

    def perform_destroy(self, instance):
        """Only allow room creator to delete the room."""
        if instance.created_by != self.request.user.userprofile:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only the room creator can delete the room")
        # Hard delete for chat rooms since they don't have is_deleted field
        super().perform_destroy(instance)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a chat room."""
        chat_room = self.get_object()
        profile = request.user.userprofile

        if chat_room.room_type == 'direct':
            return Response(
                {'error': 'Cannot join direct message rooms'},
                status=status.HTTP_400_BAD_REQUEST
            )

        chat_room.participants.add(profile)
        return Response({'message': 'Joined chat room successfully'})

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a chat room."""
        chat_room = self.get_object()
        profile = request.user.userprofile

        if chat_room.room_type == 'direct':
            return Response(
                {'error': 'Cannot leave direct message rooms'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if chat_room.created_by == profile:
            return Response(
                {'error': 'Room creator cannot leave the room'},
                status=status.HTTP_400_BAD_REQUEST
            )

        chat_room.participants.remove(profile)
        return Response({'message': 'Left chat room successfully'})

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get messages for a chat room."""
        chat_room = self.get_object()
        messages = chat_room.messages.select_related(
            'sender'
        ).prefetch_related(
            'attachments', 'read_by'
        ).order_by('-sent_at')

        serializer = MessageSerializer(
            messages, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def create_direct_message(self, request):
        """Create or get direct message room with another user."""
        other_user_id = request.data.get('user_id')
        if not other_user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            other_profile = get_active_profile_or_404(id=other_user_id)
        except Exception:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        current_profile = request.user.userprofile

        if other_profile == current_profile:
            return Response(
                {'error': 'Cannot create direct message with yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if direct message room already exists
        existing_room = ChatRoom.objects.filter(room_type='direct',
            participants__in=[current_profile, other_profile], is_deleted=False).annotate(
            participant_count=Count('participants')
        ).filter(participant_count=2).first()

        if existing_room:
            serializer = ChatRoomSerializer(
                existing_room, context={'request': request}
            )
            return Response(serializer.data)

        # Create new direct message room
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=current_profile
        )
        room.participants.set([current_profile, other_profile])

        serializer = ChatRoomSerializer(room, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing messages."""
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def get_queryset(self):
        """Get messages for rooms where user is a participant."""
        profile = self.request.user.userprofile
        return Message.objects.filter(room__participants=profile, is_deleted=False).select_related(
            'sender', 'room', 'reply_to'
        ).prefetch_related(
            'attachments', 'read_by'
        ).order_by('-sent_at')

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action in ['create', 'update', 'partial_update']:
            return MessageCreateUpdateSerializer
        return MessageSerializer

    def perform_create(self, serializer):
        """Create message with current user as sender."""
        profile = self.request.user.userprofile
        room_id = self.request.data.get('room')

        try:
            room = ChatRoom.objects.get(id=room_id, participants=profile)
        except ChatRoom.DoesNotExist:
            return Response(
                {'error': 'Chat room not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )

        message = serializer.save(sender=profile, room=room)

        # Update room's updated_at and message count
        room.messages_count = room.messages.count()
        room.save(update_fields=['updated_at', 'messages_count'])

    def perform_destroy(self, instance):
        """Soft delete message instead of hard delete."""
        if instance.sender != self.request.user.userprofile:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own messages")
        # Soft delete by setting is_deleted flag
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark message as read by current user."""
        message = self.get_object()
        profile = request.user.userprofile

        read_status, created = MessageRead.objects.get_or_create(
            message=message,
            user=profile
        )

        if created:
            return Response({'message': 'Message marked as read'})
        else:
            return Response({'message': 'Message already read'})

    @action(detail=True, methods=['post'])
    def add_attachment(self, request, pk=None):
        """Add attachment to message."""
        message = self.get_object()

        if message.sender != request.user.userprofile:
            return Response(
                {'error': 'You can only add attachments to your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )

        # MessageAttachment functionality not yet implemented
        return Response(
            {'message': 'Attachment functionality not yet implemented'},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )


# class MessageAttachmentViewSet(viewsets.ModelViewSet):
#     """ViewSet for managing message attachments."""
#     # MessageAttachment model not yet implemented
#     pass


class MessageReadViewSet(viewsets.ModelViewSet):
    """ViewSet for managing message read status."""
    serializer_class = MessageReadSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def get_queryset(self):
        """Get read status for messages in user's chat rooms."""
        profile = self.request.user.userprofile
        return MessageRead.objects.filter(is_deleted=False,
            message__room__participants=profile).select_related('message', 'user').order_by('-read_at')
