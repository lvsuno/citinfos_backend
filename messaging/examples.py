"""
Example usage of Redis-based typing indicators and presence.

This shows how to integrate the Redis utilities in your Django views,
WebSocket consumers, or API endpoints.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

from .utils import TypingIndicatorManager, UserPresenceManager


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def start_typing(request):
    """API endpoint to start typing indicator."""
    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')

        if not room_id:
            return JsonResponse({'error': 'room_id required'}, status=400)

        success = TypingIndicatorManager.start_typing(
            user_id=request.user.id,
            room_id=room_id
        )

        if success:
            return JsonResponse({'status': 'typing_started'})
        else:
            return JsonResponse({'error': 'failed_to_start_typing'}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def stop_typing(request):
    """API endpoint to stop typing indicator."""
    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')

        if not room_id:
            return JsonResponse({'error': 'room_id required'}, status=400)

        success = TypingIndicatorManager.stop_typing(
            user_id=request.user.id,
            room_id=room_id
        )

        if success:
            return JsonResponse({'status': 'typing_stopped'})
        else:
            return JsonResponse({'error': 'failed_to_stop_typing'}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_typing_users(request, room_id):
    """API endpoint to get users currently typing in a room."""
    try:
        typing_usernames = TypingIndicatorManager.get_typing_usernames(room_id)

        return JsonResponse({
            'typing_users': typing_usernames,
            'count': len(typing_usernames)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def update_presence(request):
    """API endpoint to update user presence status."""
    try:
        data = json.loads(request.body)
        status = data.get('status', 'online')
        custom_status = data.get('custom_status', '')

        # Validate status
        valid_statuses = ['online', 'away', 'busy', 'offline', 'invisible']
        if status not in valid_statuses:
            return JsonResponse({'error': 'invalid_status'}, status=400)

        # Update presence based on status
        if status == 'online':
            success = UserPresenceManager.set_user_online(
                request.user.id, custom_status
            )
        elif status == 'away':
            success = UserPresenceManager.set_user_away(
                request.user.id, custom_status
            )
        elif status == 'busy':
            success = UserPresenceManager.set_user_busy(
                request.user.id, custom_status
            )
        elif status == 'offline':
            success = UserPresenceManager.set_user_offline(request.user.id)
        else:  # invisible
            success = UserPresenceManager._update_presence(
                request.user.id, 'invisible', custom_status
            )

        if success:
            return JsonResponse({'status': 'presence_updated'})
        else:
            return JsonResponse({'error': 'failed_to_update_presence'}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_user_presence(request, user_id):
    """API endpoint to get a user's presence status."""
    try:
        presence = UserPresenceManager.get_user_presence(int(user_id))
        return JsonResponse(presence)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_online_users(request):
    """API endpoint to get all online users."""
    try:
        online_user_ids = UserPresenceManager.get_online_users()
        return JsonResponse({
            'online_users': list(online_user_ids),
            'count': len(online_user_ids)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Example WebSocket usage (if using Django Channels)
"""
# In your WebSocket consumer:

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        await self.accept()

        # Set user as online
        await sync_to_async(UserPresenceManager.set_user_online)(
            self.scope['user'].id
        )

    async def disconnect(self, close_code):
        # Stop typing when disconnecting
        await sync_to_async(TypingIndicatorManager.stop_typing)(
            self.scope['user'].id,
            self.room_id
        )

        # Set user as offline
        await sync_to_async(UserPresenceManager.set_user_offline)(
            self.scope['user'].id
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data['type'] == 'start_typing':
            await sync_to_async(TypingIndicatorManager.start_typing)(
                self.scope['user'].id,
                self.room_id
            )

            # Broadcast typing indicator to room
            await self.channel_layer.group_send(
                f"chat_{self.room_id}",
                {
                    'type': 'typing_indicator',
                    'user_id': self.scope['user'].id,
                    'username': self.scope['user'].username,
                    'is_typing': True
                }
            )

        elif data['type'] == 'stop_typing':
            await sync_to_async(TypingIndicatorManager.stop_typing)(
                self.scope['user'].id,
                self.room_id
            )

            # Broadcast stop typing to room
            await self.channel_layer.group_send(
                f"chat_{self.room_id}",
                {
                    'type': 'typing_indicator',
                    'user_id': self.scope['user'].id,
                    'username': self.scope['user'].username,
                    'is_typing': False
                }
            )
"""
