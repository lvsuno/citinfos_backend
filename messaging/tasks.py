"""Messaging-related Celery tasks."""

from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from messaging.utils import UserPresenceManager


@shared_task
def cleanup_expired_typing_indicators():
    """
    Clean up expired typing indicators from Redis.

    This task should run every 30 seconds to keep Redis clean.
    """
    try:
        # This is handled automatically by Redis TTL, but we can add
        # additional cleanup logic here if needed

        # For now, just return success since Redis auto-expires keys
        return "Typing indicators auto-cleaned by Redis TTL"

    except Exception as e:
        return f"Error cleaning typing indicators: {str(e)}"


@shared_task
def cleanup_expired_presence():
    """
    Clean up expired presence data from Redis.

    This task should run every 5 minutes.
    """
    try:
        # Redis auto-expires presence keys, but we can add
        # additional logic here if needed

        return "Presence data auto-cleaned by Redis TTL"

    except Exception as e:
        return f"Error cleaning presence data: {str(e)}"


@shared_task
def sync_presence_to_database():
    """
    Optionally sync Redis presence data back to UserPresence model.

    This task can run every 10 minutes to keep database in sync
    for analytics purposes.
    """
    try:
        from accounts.models import UserProfile
        from messaging.models import UserPresence

        # Get all online users from Redis
        online_user_ids = UserPresenceManager.get_online_users()
        synced_count = 0

        for user_id in online_user_ids:
            try:
                # Get presence from Redis
                redis_presence = UserPresenceManager.get_user_presence(user_id)

                # Update database model
                user = UserProfile.objects.get(id=user_id)
                presence, created = UserPresence.objects.get_or_create(
                    user=user,
                    defaults={
                        'status': redis_presence['status'],
                        'custom_status': redis_presence.get('custom_status', ''),
                    }
                )

                if not created:
                    presence.status = redis_presence['status']
                    presence.last_seen = redis_presence.get('last_seen', timezone.now())
                    presence.away_since = redis_presence.get('away_since', None)
                    presence.custom_status = redis_presence.get('custom_status', '')
                    presence.save(update_fields=['status', 'custom_status', 'last_seen', 'away_since'])

                synced_count += 1

            except UserProfile.DoesNotExist:
                continue
            except Exception as e:
                print(f"Error syncing presence for user {user_id}: {e}")
                continue

        return f"Synced presence for {synced_count} users to database"

    except Exception as e:
        return f"Error syncing presence to database: {str(e)}"


@shared_task
def process_message_mentions():
    """
    Process recent mentions in messages and create notifications.

    This task processes @mentions in chat messages and creates
    both push notifications (for frontend) and email notifications
    based on user settings.
    """
    try:
        from django.contrib.auth.models import User
        from .models import Message
        from notifications.utils import NotificationService

        # Get recent messages from the last hour with mentions
        recent_messages = Message.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=1),
            content__contains='@'
        ).select_related('sender', 'room')

        push_notifications_count = 0
        email_notifications_count = 0

        for message in recent_messages:
            # Extract mentions from message content (simplified)
            import re
            mentions = re.findall(r'@(\w+)', message.content)

            for username in mentions:
                try:
                    mentioned_user = User.objects.get(username=username)
                    mentioned_profile = getattr(mentioned_user, 'profile', None)
                    sender_profile = getattr(message.sender, 'profile', None)

                    # Check if mentioned user is in the room
                    if (mentioned_user in message.room.participants.all() and
                            mentioned_profile and sender_profile):

                        # Get user notification settings
                        user_settings = getattr(
                            mentioned_profile, 'settings', None
                        )

                        # Create push notification if enabled
                        if (user_settings and user_settings.push_notifications and
                                user_settings.notification_frequency != 'never'):

                            push_notification = NotificationService.create_notification(
                                recipient=mentioned_profile,
                                title="You were mentioned in a message",
                                message=(
                                    f"{sender_profile.display_name} mentioned you "
                                    f"in {message.room.name}"
                                ),
                                notification_type='mention',
                                sender=sender_profile,
                                related_object=message,
                                app_context='messaging'
                            )

                            if push_notification:
                                push_notifications_count += 1

                        # Send email notification if enabled and frequency allows
                        if (user_settings and user_settings.email_notifications and
                                user_settings.notification_frequency in ['real_time', 'hourly']):

                            email_sent = NotificationService.send_notification_email(
                                recipient=mentioned_profile,
                                subject=f"You were mentioned by {sender_profile.display_name}",
                                template='messaging/email/mention.html',
                                context={
                                    'mentioned_user': mentioned_profile,
                                    'sender': sender_profile,
                                    'message': message,
                                    'room': message.room
                                }
                            )

                            if email_sent:
                                email_notifications_count += 1

                except User.DoesNotExist:
                    continue

        return (f"Processed {recent_messages.count()} messages, "
                f"created {push_notifications_count} push notifications, "
                f"sent {email_notifications_count} emails")

    except Exception as e:
        return f"Error processing message mentions: {str(e)}"


@shared_task
def send_message_notification_emails():
    """
    Send notifications for important message events using user settings.

    This creates push notifications (for frontend) and email notifications
    based on individual user preferences.
    """
    try:
        from django.contrib.auth.models import User
        from messaging.models import MessageRead, Message
        from notifications.utils import NotificationService

        # Get users who are active and have notification settings
        active_users = User.objects.filter(
            is_active=True,
            profile__settings__isnull=False
        ).select_related('profile', 'profile__settings')

        push_notifications_created = 0
        emails_sent = 0

        for user in active_users:
            try:
                user_profile = getattr(user, 'profile', None)
                user_settings = getattr(user_profile, 'settings', None)

                if not user_profile or not user_settings:
                    continue

                # Skip if user has disabled all notifications
                if user_settings.notification_frequency == 'never':
                    continue

                # Get unread message count
                unread_count = Message.objects.filter(
                    room__participants=user_profile
                ).exclude(
                    id__in=MessageRead.objects.filter(
                        user=user
                    ).values_list('message_id', flat=True)
                ).count()

                if unread_count > 0:
                    # Get the most recent unread message
                    recent_message = Message.objects.filter(
                        room__participants=user_profile
                    ).exclude(
                        id__in=MessageRead.objects.filter(
                            user=user
                        ).values_list('message_id', flat=True)
                    ).order_by('-created_at').first()

                    if recent_message:
                        sender_profile = getattr(
                            recent_message.sender, 'profile', None
                        )
                        if sender_profile and sender_profile != user_profile:

                            # Create push notification if enabled
                            if user_settings.push_notifications:
                                push_notification = NotificationService.create_notification(
                                    recipient=user_profile,
                                    title="New Messages",
                                    message=(
                                        f"You have {unread_count} unread messages "
                                        f"from {sender_profile.display_name}"
                                    ),
                                    notification_type='message',
                                    sender=sender_profile,
                                    related_object=recent_message,
                                    app_context='messaging'
                                )

                                if push_notification:
                                    push_notifications_created += 1

                            # Send email notification based on frequency settings
                            if (user_settings.email_notifications and
                                    user_settings.notification_frequency in
                                    ['real_time', 'hourly']):

                                email_sent = NotificationService.send_email_notification(
                                    recipient=user_profile,
                                    subject=(
                                        f"New Messages in "
                                        f"{recent_message.room.name}"
                                    ),
                                    template='messaging/email/new_message.html',
                                    context={
                                        'recipient': user_profile,
                                        'sender': sender_profile,
                                        'message': recent_message,
                                        'unread_count': unread_count,
                                        'room': recent_message.room
                                    }
                                )

                                if email_sent:
                                    emails_sent += 1

            except Exception as e:
                print(f"Error creating notification for {user.username}: {e}")
                continue

        return (f"Created {push_notifications_created} push notifications and "
                f"sent {emails_sent} email notifications")

    except Exception as e:
        return f"Error creating message notifications: {str(e)}"


@shared_task
def cleanup_old_messages():
    """
    Clean up old message data based on retention policies.

    This removes old messages, read receipts, and other messaging data
    according to configured retention policies.
    """
    try:
        from messaging.models import Message, MessageRead, MessageReaction

        # Delete old message read receipts (keep 30 days)
        old_read_date = timezone.now() - timedelta(days=30)
        old_reads = MessageRead.objects.filter(read_at__lt=old_read_date)
        reads_count = old_reads.count()
        old_reads.delete()

        # Delete old message reactions (keep 90 days)
        old_reaction_date = timezone.now() - timedelta(days=90)
        old_reactions = MessageReaction.objects.filter(
            created_at__lt=old_reaction_date
        )
        reactions_count = old_reactions.count()
        old_reactions.delete()

        # Archive very old messages (older than 1 year) - mark as archived
        # instead of deleting to preserve chat history
        old_message_date = timezone.now() - timedelta(days=365)
        old_messages = Message.objects.filter(
            created_at__lt=old_message_date,
            is_deleted=False
        )
        archived_count = old_messages.count()
        from core.signals import handle_bulk_soft_deletion
        handle_bulk_soft_deletion(old_messages, is_deleted=True)

        return (f"Cleaned up {reads_count} read receipts, "
                f"{reactions_count} reactions, archived {archived_count} messages")

    except Exception as e:
        return f"Error cleaning up old messages: {str(e)}"


@shared_task
def update_message_counters():
    """
    Update denormalized counters for chat rooms and messages.

    This updates message counts, participant counts, and other
    cached statistics for better performance.
    """
    try:
        from messaging.models import ChatRoom

        # Update chat room counters
        rooms = ChatRoom.objects.all()
        for room in rooms:
            # Update message count
            room.message_count = room.messages.filter(is_deleted=False).count()

            # Update participant count
            room.participant_count = room.participants.count()

            # Update last message info
            last_message = room.messages.filter(is_deleted=False).order_by('-created_at').first()
            if last_message:
                room.last_message_at = last_message.created_at
                room.last_message_content = last_message.content[:100]

            room.save(update_fields=[
                'message_count', 'participant_count',
                'last_message_at', 'last_message_content'
            ])

        return f"Updated counters for {rooms.count()} chat rooms"

    except Exception as e:
        return f"Error updating message counters: {str(e)}"


@shared_task
def cleanup_inactive_chat_rooms():
    """
    Clean up inactive chat rooms and empty conversations.

    This removes empty rooms or rooms with no activity for extended periods.
    """
    try:
        from .models import ChatRoom

        # Find rooms with no messages for 90 days
        inactive_date = timezone.now() - timedelta(days=90)
        inactive_rooms = ChatRoom.objects.filter(
            Q(last_message_at__lt=inactive_date) | Q(last_message_at__isnull=True),
            created_at__lt=inactive_date
        )

        # Find empty rooms (no participants)
        empty_rooms = ChatRoom.objects.filter(participants__isnull=True)

        # Combine and delete
        rooms_to_delete = (inactive_rooms | empty_rooms).distinct()
        deleted_count = rooms_to_delete.count()
        rooms_to_delete.delete()

        return f"Cleaned up {deleted_count} inactive/empty chat rooms"

    except Exception as e:
        return f"Error cleaning up inactive chat rooms: {str(e)}"


@shared_task
def send_daily_message_digest():
    """
    Send daily digest emails for messaging activity based on user settings.

    This task sends email summaries only to users who have enabled
    daily email digests in their notification settings.
    """
    try:
        from django.contrib.auth.models import User
        from messaging.models import Message, ChatRoom
        from notifications.utils import NotificationService
        from datetime import datetime

        # Get users who want daily digests
        digest_users = User.objects.filter(
            is_active=True,
            profile__settings__email_notifications=True,
            profile__settings__notification_frequency='daily'
        ).select_related('profile', 'profile__settings')

        digests_sent = 0
        yesterday = timezone.now() - timedelta(days=1)

        for user in digest_users:
            try:
                user_profile = getattr(user, 'profile', None)
                user_settings = getattr(user_profile, 'settings', None)

                if not user_profile or not user_settings:
                    continue

                # Get user's active chat rooms
                user_rooms = ChatRoom.objects.filter(
                    participants=user_profile,
                    is_archived=False
                )

                # Get yesterday's messages in user's rooms
                yesterday_messages = Message.objects.filter(
                    room__in=user_rooms,
                    created_at__gte=yesterday,
                    created_at__lt=timezone.now(),
                    is_deleted=False
                ).exclude(
                    sender=user_profile  # Exclude user's own messages
                ).order_by('-created_at')

                if yesterday_messages.exists():
                    # Group messages by room for digest
                    room_activity = {}
                    for message in yesterday_messages[:50]:  # Limit messages
                        room_name = message.room.name or "Direct Message"
                        if room_name not in room_activity:
                            room_activity[room_name] = []
                        room_activity[room_name].append({
                            'sender': message.sender.display_name,
                            'content': message.content[:100],  # Truncate
                            'time': message.created_at
                        })

                    # Send digest email using Notifications app
                    digest_sent = NotificationService.send_digest_email(
                        recipient=user_profile,
                        subject=(
                            f"Daily Message Digest - "
                            f"{datetime.now().strftime('%B %d, %Y')}"
                        ),
                        template='messaging/email/daily_digest.html',
                        context={
                            'recipient': user_profile,
                            'room_activity': room_activity,
                            'total_messages': yesterday_messages.count(),
                            'date': yesterday.date()
                        }
                    )

                    if digest_sent:
                        digests_sent += 1

            except Exception as e:
                print(f"Error sending digest to {user.username}: {e}")
                continue

        return f"Sent daily message digest to {digests_sent} users"

    except Exception as e:
        return f"Error sending daily message digest: {str(e)}"


@shared_task
def send_weekly_messaging_summary():
    """
    Send weekly messaging summary notifications based on user settings.

    This creates push notifications for users who have enabled
    weekly summaries in their notification settings.
    """
    try:
        from django.contrib.auth.models import User
        from messaging.models import Message, ChatRoom
        from notifications.utils import NotificationService

        # Get users who want weekly summaries
        week_ago = timezone.now() - timedelta(days=7)
        active_users = User.objects.filter(
            is_active=True,
            profile__settings__push_notifications=True,
            profile__settings__notification_frequency='weekly',
            profile__in=ChatRoom.objects.filter(
                last_message_at__gte=week_ago
            ).values_list('participants', flat=True)
        ).select_related('profile', 'profile__settings').distinct()

        summaries_created = 0

        for user in active_users:
            try:
                user_profile = getattr(user, 'profile', None)
                user_settings = getattr(user_profile, 'settings', None)

                if not user_profile or not user_settings:
                    continue

                # Calculate weekly stats
                user_rooms = ChatRoom.objects.filter(
                    participants=user_profile
                )

                messages_sent = Message.objects.filter(
                    sender=user_profile,
                    created_at__gte=week_ago,
                    is_deleted=False
                ).count()

                messages_received = Message.objects.filter(
                    room__in=user_rooms,
                    created_at__gte=week_ago,
                    is_deleted=False
                ).exclude(sender=user_profile).count()

                new_rooms_joined = user_rooms.filter(
                    created_at__gte=week_ago
                ).count()

                if messages_sent > 0 or messages_received > 0:
                    # Create weekly summary notification
                    summary_message = (
                        f"Weekly Summary: You sent {messages_sent} messages, "
                        f"received {messages_received} messages"
                    )

                    if new_rooms_joined > 0:
                        summary_message += (
                            f", and joined {new_rooms_joined} new conversations"
                        )

                    notification = NotificationService.create_notification(
                        recipient=user_profile,
                        title="Weekly Messaging Summary",
                        message=summary_message,
                        notification_type='summary',
                        app_context='messaging',
                        extra_data={
                            'messages_sent': messages_sent,
                            'messages_received': messages_received,
                            'new_rooms': new_rooms_joined,
                            'week_start': week_ago.isoformat()
                        }
                    )

                    if notification:
                        summaries_created += 1

            except Exception as e:
                print(f"Error creating summary for {user.username}: {e}")
                continue

        return f"Created weekly summaries for {summaries_created} users"

    except Exception as e:
        return f"Error creating weekly messaging summaries: {str(e)}"


@shared_task
def send_hourly_message_batch():
    """
    Send hourly batched email notifications for users with hourly frequency.

    This task batches notifications for users who have selected 'hourly'
    notification frequency to avoid email spam.
    """
    try:
        from django.contrib.auth.models import User
        from messaging.models import Message, MessageRead
        from notifications.utils import NotificationService

        # Get users who want hourly email batches
        hourly_users = User.objects.filter(
            is_active=True,
            profile__settings__email_notifications=True,
            profile__settings__notification_frequency='hourly'
        ).select_related('profile', 'profile__settings')

        emails_sent = 0
        hour_ago = timezone.now() - timedelta(hours=1)

        for user in hourly_users:
            try:
                user_profile = getattr(user, 'profile', None)
                if not user_profile:
                    continue

                # Get unread messages from the last hour
                hourly_messages = Message.objects.filter(
                    room__participants=user_profile,
                    created_at__gte=hour_ago,
                    is_deleted=False
                ).exclude(
                    sender=user_profile  # Exclude user's own messages
                ).exclude(
                    id__in=MessageRead.objects.filter(
                        user=user
                    ).values_list('message_id', flat=True)
                ).order_by('-created_at')

                if hourly_messages.exists():
                    # Group messages by room and sender
                    message_summary = {}
                    total_count = hourly_messages.count()

                    for message in hourly_messages[:20]:  # Limit to 20 messages
                        room_name = message.room.name or "Direct Message"
                        sender_name = message.sender.display_name

                        if room_name not in message_summary:
                            message_summary[room_name] = {}

                        if sender_name not in message_summary[room_name]:
                            message_summary[room_name][sender_name] = []

                        message_summary[room_name][sender_name].append({
                            'content': message.content[:80],  # Truncate
                            'time': message.created_at
                        })

                    # Send hourly batch email
                    email_sent = NotificationService.send_email_notification(
                        recipient=user_profile,
                        subject=f"Hourly Message Summary - {total_count} new messages",
                        template='messaging/email/hourly_batch.html',
                        context={
                            'recipient': user_profile,
                            'message_summary': message_summary,
                            'total_count': total_count,
                            'hour_period': hour_ago.strftime('%I:%M %p')
                        }
                    )

                    if email_sent:
                        emails_sent += 1

            except Exception as e:
                print(f"Error sending hourly batch to {user.username}: {e}")
                continue

        return f"Sent hourly message batches to {emails_sent} users"

    except Exception as e:
        return f"Error sending hourly message batches: {str(e)}"
