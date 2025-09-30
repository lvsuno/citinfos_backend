"""Messaging utilities using Redis for real-time features."""

import time
from typing import List, Set
from django.core.cache import cache
from accounts.models import UserProfile  # Ensure correct import for UserProfile


class TypingIndicatorManager:
    """Redis-based typing indicator management for real-time chat."""

    # Redis key patterns
    TYPING_KEY_PATTERN = "typing:{room_id}"
    USER_TYPING_KEY_PATTERN = "user_typing:{user_id}:{room_id}"

    # Expiry settings
    TYPING_TIMEOUT = 10  # seconds
    CLEANUP_INTERVAL = 5  # seconds

    @classmethod
    def start_typing(cls, user_id: int, room_id: str) -> bool:
        """
        Mark user as typing in a room.

        Args:
            user_id: User ID
            room_id: ChatRoom UUID

        Returns:
            bool: True if successfully started typing
        """
        try:
            # Key for room's typing users
            room_key = cls.TYPING_KEY_PATTERN.format(room_id=room_id)
            # Key for individual user typing status
            user_key = cls.USER_TYPING_KEY_PATTERN.format(
                user_id=user_id,
                room_id=room_id
            )

            # Get current typing users
            typing_users = cache.get(room_key, set())
            if not isinstance(typing_users, set):
                typing_users = set()

            # Add user to typing set
            typing_users.add(user_id)

            # Store with expiry
            cache.set(room_key, typing_users, cls.TYPING_TIMEOUT)
            cache.set(user_key, True, cls.TYPING_TIMEOUT)

            return True

        except Exception as e:
            # Log error but don't break chat functionality
            print(f"Error starting typing indicator: {e}")
            return False

    @classmethod
    def stop_typing(cls, user_id: int, room_id: str) -> bool:
        """
        Stop user typing in a room.

        Args:
            user_id: User ID
            room_id: ChatRoom UUID

        Returns:
            bool: True if successfully stopped typing
        """
        try:
            room_key = cls.TYPING_KEY_PATTERN.format(room_id=room_id)
            user_key = cls.USER_TYPING_KEY_PATTERN.format(
                user_id=user_id,
                room_id=room_id
            )

            # Remove user from typing set
            typing_users = cache.get(room_key, set())
            if isinstance(typing_users, set) and user_id in typing_users:
                typing_users.discard(user_id)
                cache.set(room_key, typing_users, cls.TYPING_TIMEOUT)

            # Remove individual user typing status
            cache.delete(user_key)

            return True

        except Exception as e:
            print(f"Error stopping typing indicator: {e}")
            return False

    @classmethod
    def get_typing_users(cls, room_id: str) -> Set[int]:
        """
        Get list of users currently typing in a room.

        Args:
            room_id: ChatRoom UUID

        Returns:
            Set[int]: Set of user IDs currently typing
        """
        try:
            room_key = cls.TYPING_KEY_PATTERN.format(room_id=room_id)
            typing_users = cache.get(room_key, set())

            if not isinstance(typing_users, set):
                return set()

            # Clean up expired individual user keys
            valid_users = set()
            for user_id in typing_users:
                user_key = cls.USER_TYPING_KEY_PATTERN.format(
                    user_id=user_id,
                    room_id=room_id
                )
                if cache.get(user_key):
                    valid_users.add(user_id)

            # Update the room key with only valid users
            if valid_users != typing_users:
                cache.set(room_key, valid_users, cls.TYPING_TIMEOUT)

            return valid_users

        except Exception as e:
            print(f"Error getting typing users: {e}")
            return set()

    @classmethod
    def is_user_typing(cls, user_id: int, room_id: str) -> bool:
        """
        Check if a specific user is typing in a room.

        Args:
            user_id: User ID
            room_id: ChatRoom UUID

        Returns:
            bool: True if user is typing
        """
        try:
            user_key = cls.USER_TYPING_KEY_PATTERN.format(
                user_id=user_id,
                room_id=room_id
            )
            return bool(cache.get(user_key, False))

        except Exception as e:
            print(f"Error checking user typing status: {e}")
            return False

    @classmethod
    def get_typing_usernames(cls, room_id: str) -> List[str]:
        """
        Get usernames of users currently typing in a room.

        Args:
            room_id: ChatRoom UUID

        Returns:
            List[str]: List of usernames currently typing
        """
        try:
            typing_user_ids = cls.get_typing_users(room_id)
            if not typing_user_ids:
                return []

            # Get usernames from cache or database
            usernames = []
            for user_id in typing_user_ids:
                # Try to get name from cache first
                name_key = f"username:{user_id}"
                username = cache.get(name_key)

                if not username:
                    # Fallback to database
                    try:
                        user = UserProfile.objects.get(id=user_id)
                        username = user.user.username
                        # Cache username for future use
                        cache.set(name_key, username, 300)  # 5 minutes
                    except UserProfile.DoesNotExist:
                        continue

                usernames.append(username)

            return usernames

        except Exception as e:
            print(f"Error getting typing usernames: {e}")
            return []

    @classmethod
    def cleanup_room_typing(cls, room_id: str) -> int:
        """
        Clean up all typing indicators for a room.

        Args:
            room_id: ChatRoom UUID

        Returns:
            int: Number of users cleaned up
        """
        try:
            typing_users = cls.get_typing_users(room_id)
            count = 0

            for user_id in typing_users:
                if cls.stop_typing(user_id, room_id):
                    count += 1

            return count

        except Exception as e:
            print(f"Error cleaning up room typing: {e}")
            return 0


class UserPresenceManager:
    """Redis-based user presence management for real-time status."""

    # Redis key patterns
    PRESENCE_KEY_PATTERN = "presence:{user_id}"
    ONLINE_USERS_KEY = "online_users"

    # Status constants
    STATUS_ONLINE = "online"
    STATUS_AWAY = "away"
    STATUS_BUSY = "busy"
    STATUS_OFFLINE = "offline"
    STATUS_INVISIBLE = "invisible"

    # Expiry settings
    PRESENCE_TIMEOUT = 300  # 5 minutes

    @classmethod
    def set_user_online(cls, user_id: int, custom_status: str = "") -> bool:
        """Set user as online with optional custom status."""
        return cls._update_presence(
            user_id,
            cls.STATUS_ONLINE,
            custom_status
        )

    @classmethod
    def set_user_away(cls, user_id: int, custom_status: str = "") -> bool:
        """Set user as away with optional custom status."""
        return cls._update_presence(
            user_id,
            cls.STATUS_AWAY,
            custom_status
        )

    @classmethod
    def set_user_busy(cls, user_id: int, custom_status: str = "") -> bool:
        """Set user as busy with optional custom status."""
        return cls._update_presence(
            user_id,
            cls.STATUS_BUSY,
            custom_status
        )

    @classmethod
    def set_user_offline(cls, user_id: int) -> bool:
        """Set user as offline and remove from online users."""
        try:
            # Remove from online users set
            online_users = cache.get(cls.ONLINE_USERS_KEY, set())
            if isinstance(online_users, set):
                online_users.discard(user_id)
                cache.set(cls.ONLINE_USERS_KEY, online_users, cls.PRESENCE_TIMEOUT)

            # Update presence
            return cls._update_presence(user_id, cls.STATUS_OFFLINE)

        except Exception as e:
            print(f"Error setting user offline: {e}")
            return False

    @classmethod
    def _update_presence(
        cls, user_id: int, status: str, custom_status: str = ""
    ) -> bool:
        """Internal method to update user presence."""
        try:
            presence_key = cls.PRESENCE_KEY_PATTERN.format(user_id=user_id)

            presence_data = {
                'status': status,
                'custom_status': custom_status,
                'last_seen': int(time.time()),
                'away_since': int(time.time()) if status == cls.STATUS_AWAY else None,
                'user_id': user_id
            }

            # Store presence data
            cache.set(presence_key, presence_data, cls.PRESENCE_TIMEOUT)

            # Add to online users if not offline
            if status != cls.STATUS_OFFLINE:
                online_users = cache.get(cls.ONLINE_USERS_KEY, set())
                if not isinstance(online_users, set):
                    online_users = set()
                online_users.add(user_id)
                cache.set(cls.ONLINE_USERS_KEY, online_users, cls.PRESENCE_TIMEOUT)

            return True

        except Exception as e:
            print(f"Error updating presence: {e}")
            return False

    @classmethod
    def get_user_presence(cls, user_id: int) -> dict:
        """Get user presence data."""
        try:
            presence_key = cls.PRESENCE_KEY_PATTERN.format(user_id=user_id)
            presence_data = cache.get(presence_key)

            if presence_data:
                return presence_data

            # Return default offline status
            return {
                'status': cls.STATUS_OFFLINE,
                'custom_status': '',
                'last_seen': 0,
                'user_id': user_id
            }

        except Exception as e:
            print(f"Error getting user presence: {e}")
            return {
                'status': cls.STATUS_OFFLINE,
                'custom_status': '',
                'last_seen': 0,
                'user_id': user_id
            }

    @classmethod
    def get_online_users(cls) -> Set[int]:
        """Get set of all online user IDs."""
        try:
            online_users = cache.get(cls.ONLINE_USERS_KEY, set())
            if isinstance(online_users, set):
                return online_users
            return set()

        except Exception as e:
            print(f"Error getting online users: {e}")
            return set()

    @classmethod
    def is_user_online(cls, user_id: int) -> bool:
        """Check if user is online (any status except offline)."""
        presence = cls.get_user_presence(user_id)
        return presence['status'] != cls.STATUS_OFFLINE
