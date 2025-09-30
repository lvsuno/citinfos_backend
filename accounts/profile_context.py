"""
Profile context utilities for server-side filtering based on:
1. Profile visibility (public/private)
2. Social relationship (following/not following)
3. Ownership (own profile vs viewing others)
"""

from typing import Dict, Any, Optional
from django.contrib.auth.models import User
from .models import UserProfile, Follow


class ProfileContext:
    """
    Determines what content and interactions are allowed based on profile
    context.
    """

    def __init__(self, profile: UserProfile,
                 viewing_user: Optional[User] = None):
        self.profile = profile
        self.viewing_user = viewing_user

        # Determine context
        self.is_authenticated = (
            viewing_user and viewing_user.is_authenticated
        )
        self.is_owner = (
            self.is_authenticated and
            hasattr(viewing_user, 'profile') and
            viewing_user.profile == profile
        )
        self.is_following = (
            self._check_following() if self.is_authenticated else False
        )

    def _check_following(self) -> bool:
        """Check if viewing user follows the profile owner."""
        if not self.is_authenticated or self.is_owner:
            return False

        try:
            follow_relationship = Follow.objects.get(
                follower=self.viewing_user.profile,
                followed=self.profile,
                is_deleted=False
            )
            # Store the follow relationship for status checking
            self._follow_relationship = follow_relationship
            return follow_relationship.status == 'approved'
        except Follow.DoesNotExist:
            self._follow_relationship = None
            return False

    def get_follow_status(self) -> Optional[str]:
        """Get the current follow relationship status."""
        if not self.is_authenticated or self.is_owner:
            return None

        if hasattr(self, '_follow_relationship') and self._follow_relationship:
            return self._follow_relationship.status

        # Check again if not already checked
        try:
            follow_relationship = Follow.objects.get(
                follower=self.viewing_user.profile,
                followed=self.profile,
                is_deleted=False
            )
            return follow_relationship.status
        except Follow.DoesNotExist:
            return None

    def can_view_profile(self) -> bool:
        """Determine if user can view this profile."""
        # Public profiles can always be viewed
        if not self.profile.is_private:
            return True

        # Private profiles require authentication
        if not self.is_authenticated:
            # Return False, but the view should show a login message
            return False

        # Owner can always view their own profile
        if self.is_owner:
            return True

        # Private profiles require following relationship
        return self.is_following

    def get_private_profile_message(self) -> str:
        """Get appropriate message for private profiles that can't be viewed."""
        if not self.profile.is_private:
            return ""

        if not self.is_authenticated:
            return "This profile is private, please login to see it"

        # Authenticated non-followers can see basic profile info but not content
        if not self.is_following and not self.is_owner:
            return "This profile is private. You need to follow this user to see their content."

        return ""

    def can_view_posts(self) -> bool:
        """Determine if user can view posts from this profile."""
        # Public profiles: posts visible to everyone
        if not self.profile.is_private:
            return True

        # Private profiles: require authentication and following
        if not self.is_authenticated:
            return False

        # Owner can always see their own posts
        if self.is_owner:
            return True

        # Private profiles require following to see posts
        return self.is_following

    def can_view_badges(self) -> bool:
        """Determine if user can view badges from this profile.

        Badge visibility rules:
        - tinybadge: displayed under username in posts (handled client-side)
        - mediumbadge: displayed near username in profile page (public profiles + authenticated users for private profiles)
        - badgecard: full badge details in 'Badges & Achievements' (owner only)
        """
        # Owner can always see all their badges (including badgecard)
        if self.is_owner:
            return True

        # For public profiles: anyone can see badges (tinybadge + mediumbadge)
        if not self.profile.is_private:
            return True

        # For private profiles: authenticated users can see mediumbadge, followers can see all
        if self.profile.is_private:
            # Authenticated users can see mediumbadge
            if self.is_authenticated:
                return True
            # Unauthenticated users cannot see any badges on private profiles
            return False

        return False

    def can_interact_with_content(self) -> bool:
        """Determine if user can interact with content (like, comment)."""
        if not self.is_authenticated:
            return False

        # Owner can always interact with their own content
        if self.is_owner:
            return True

        # For public profiles: anyone authenticated can interact
        if not self.profile.is_private:
            return True

        # For private profiles: only followers can interact
        return self.is_following

    def can_edit_content(self) -> bool:
        """Determine if user can edit content (edit/delete posts)."""
        # Only owner can edit content
        return self.is_owner

    def get_post_visibility_filter(self) -> Dict[str, Any]:
        """Get the appropriate post filter based on context."""
        base_filter = {
            'author': self.profile,
            'is_deleted': False
        }

        if self.is_owner:
            # Owner sees all their posts
            return base_filter
        elif self.can_view_posts():
            # Others see only public posts
            base_filter['visibility'] = 'public'
            return base_filter
        else:
            # No posts visible
            return {'pk__in': []}  # Empty queryset

    def get_context_data(self) -> dict:
        """Return comprehensive context data for this profile view."""
        return {
            'is_owner': self.is_owner,
            'is_following': self.is_following,
            'follow_status': self.get_follow_status(),
            'can_view_profile': self.can_view_profile(),
            'can_view_posts': self.can_view_posts(),
            'can_view_badges': self.can_view_badges(),
            'can_interact': self.can_interact_with_content(),
            'can_edit': self.is_owner,
            'private_message': self.get_private_profile_message(),
            'profile_type': 'private' if self.profile.is_private else 'public',
            'viewing_mode': (
                'owner' if self.is_owner else
                'following' if self.is_following else
                'authenticated' if self.is_authenticated else
                'anonymous'
            )
        }


def get_profile_context(profile: UserProfile, request) -> ProfileContext:
    """Helper function to create ProfileContext from request."""
    viewing_user = (
        request.user if (
            hasattr(request, 'user') and
            request.user.is_authenticated
        ) else None
    )
    return ProfileContext(profile, viewing_user)
