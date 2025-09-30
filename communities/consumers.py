"""
WebSocket consumers for the communities app.

Provides community-specific presence and task update channels.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser

from communities.services import community_redis_service

logger = logging.getLogger(__name__)


class CommunityConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for community presence and task updates."""

    async def connect(self):
        self.user = self.scope.get('user')
        self.community_id = self.scope.get('url_route', {}).get('kwargs', {}).get('community_id')

        if not self.community_id:
            logger.warning('CommunityConsumer: missing community_id in URL')
            await self.close(code=4001)
            return

        if not self.user or isinstance(self.user, AnonymousUser):
            logger.warning('CommunityConsumer: unauthenticated connection attempt')
            await self.close(code=4001)
            return

        try:
            # Verify community exists and user is a member (or public community)
            self.community = await self.get_community(self.community_id)
            is_member = await self.user_is_member(self.community, self.user)

            if not is_member:
                logger.info("User not member of community: %s", self.community_id)
                await self.close(code=4003)
                return
                await self.close(code=4003)  # forbidden
                return

            self.group_name = f"community_{self.community_id}"

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            await self.accept()

            # Track presence in Redis (authoritative) and announce to group
            try:
                user_profile_id = str(await self.get_user_profile_id())
                # Add user to Redis online set
                await sync_to_async(community_redis_service.track_user_activity)(
                    self.community_id, user_profile_id
                )

                # Broadcast presence update to group
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'presence_update',
                        'data': {
                            'user_id': user_profile_id,
                            'username': self.user.username,
                            'status': 'online'
                        }
                    }
                )
            except Exception as e:
                logger.warning('Failed to track presence for user %s', self.user)

            logger.info("User %s connected to community %s", self.user.username, self.community_id)

        except Exception as e:
            logger.error(f"CommunityConsumer connect error: {e}")
            await self.close(code=4001)

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'group_name'):
                await self.channel_layer.group_discard(self.group_name, self.channel_name)

                # Remove from Redis online set and broadcast offline presence
                try:
                    user_profile_id = str(await self.get_user_profile_id())
                    await sync_to_async(community_redis_service.remove_user_activity)(
                        self.community_id, user_profile_id
                    )

                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            'type': 'presence_update',
                            'data': {
                                'user_id': user_profile_id,
                                'username': self.user.username,
                                'status': 'offline'
                            }
                        }
                    )
                except Exception:
                    # Best-effort cleanup; ignore errors during disconnect
                    pass

                logger.info(f"User {self.user.username} disconnected from community {self.community_id}")
        except Exception:
            # Best-effort cleanup; ignore errors during disconnect
            pass

    async def receive(self, text_data):
        """Handle incoming messages from WebSocket client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))

            elif message_type == 'get_members':
                # Return the authoritative members list from Redis
                try:
                    members = await sync_to_async(
                        community_redis_service.get_online_members
                    )(self.community_id)
                    await self.send(text_data=json.dumps({
                        'type': 'members_list',
                        'data': list(members)
                    }))
                except Exception as e:
                    logger.error('Error retrieving members for community %s: %s', self.community_id, e)

            elif message_type == 'task_action':
                # Broadcast a community task update to all members
                task_data = data.get('task')
                if task_data:
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            'type': 'community_task',
                            'data': task_data,
                            'actor': {
                                'user_id': str(await self.get_user_profile_id()),
                                'username': self.user.username
                            }
                        }
                    )

            else:
                logger.debug(f"CommunityConsumer unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error('CommunityConsumer received invalid JSON')
        except Exception as e:
            logger.error(f'CommunityConsumer receive error: {e}')

    # Handlers for group messages
    async def presence_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'presence_update',
            'data': event.get('data', {})
        }))

    async def community_task(self, event):
        await self.send(text_data=json.dumps({
            'type': 'community_task',
            'data': event.get('data', {}),
            'actor': event.get('actor')
        }))

    # Database helpers
    @database_sync_to_async
    def get_community(self, community_id):
        from communities.models import Community
        return Community.objects.get(id=community_id)

    @database_sync_to_async
    def user_is_member(self, community, user):
        # If community has public flag or user is a member
        try:
            if getattr(community, 'is_public', False):
                return True
            return community.members.filter(id=user.id).exists()
        except Exception:
            return False

    @database_sync_to_async
    def get_user_profile_id(self):
        from accounts.models import UserProfile
        profile = UserProfile.objects.get(user=self.user)
        return profile.id

    @database_sync_to_async
    def get_current_members(self):
        # Fallback: return stored members from DB if needed (limited use)
        from accounts.models import UserProfile
        members = self.community.members.all().select_related('user')[:200]
        return [
            {
                'user_id': str(m.userprofile.id) if hasattr(m, 'userprofile') else None,
                'username': m.username
            }
            for m in members
        ]
