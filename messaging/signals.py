"""
Real-time notification signals for messaging app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

try:
    from .models import Message, ChatRoom, DirectMessage
    from notifications.realtime import send_message_notification

    @receiver(post_save, sender=Message)
    def send_chat_message_notification(sender, instance, created, **kwargs):
        """Send real-time notification for new chat messages."""
        if created:
            try:
                # Get all chat room members except the sender
                if hasattr(instance, 'chat_room'):
                    chat_members = instance.chat_room.members.exclude(
                        id=instance.sender.id
                    )

                    for member in chat_members:
                        send_message_notification(
                            recipient_profile=member,
                            sender_profile=instance.sender,
                            message_preview=instance.content[:100] + "..." if len(instance.content) > 100 else instance.content,
                            chat_id=str(instance.chat_room.id)
                        )

            except Exception as e:
                print(f"Error sending chat message notification: {str(e)}")

    @receiver(post_save, sender=DirectMessage)
    def send_direct_message_notification(sender, instance, created, **kwargs):
        """Send real-time notification for direct messages."""
        if created:
            try:
                send_message_notification(
                    recipient_profile=instance.recipient,
                    sender_profile=instance.sender,
                    message_preview=instance.content[:100] + "..." if len(instance.content) > 100 else instance.content
                )

            except Exception as e:
                print(f"Error sending direct message notification: {str(e)}")

except ImportError:
    # Messaging models not available - skip signal setup
    pass
