"""
User verification and permission utilities.
Provides centralized verification logic for user interactions.
"""

from django.core.exceptions import ValidationError, PermissionDenied
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied


class UserVerificationError(ValidationError):
    """Custom exception for user verification failures."""
    pass


class UserSuspensionError(ValidationError):
    """Custom exception for user suspension."""
    pass


class NotDeletedUserPermission(permissions.BasePermission):
    """
    Permission class that blocks deleted users from accessing any resources.

    This permission should be added to ALL authenticated ViewSets to ensure
    that users with is_deleted=True cannot access any application resources.
    """

    message = "Your account has been deleted and you cannot access this resource."

    def has_permission(self, request, view):
        """
        Check if the user has permission to access the resource.

        Returns False if the user is authenticated but their profile is deleted.
        """
        if not request.user or not request.user.is_authenticated:
            return True  # Let other authentication handle this

        try:
            # Check if user has a deleted profile
            profile = getattr(request.user, 'userprofile', None) or getattr(request.user, 'profile', None)
            if profile and getattr(profile, 'is_deleted', False):
                return False

            # Also check direct query in case of caching issues
            from .models import UserProfile
            if UserProfile.objects.filter(user=request.user, is_deleted=True).exists():
                return False

        except (AttributeError, UserProfile.DoesNotExist):
            # If there's no profile, allow access (will be handled elsewhere)
            pass

        return True

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check.

        Always allow if has_permission passed, but double-check for object access.
        """
        return self.has_permission(request, view)


def check_user_can_interact(user_profile):
    """
    Check if a user can perform social interactions.

    Args:
        user_profile: UserProfile instance

    Raises:
        UserVerificationError: If user is not verified
        UserSuspensionError: If user is suspended
    """
    if not user_profile:
        raise UserVerificationError("User profile is required")

    if not user_profile.is_verified:
        raise UserVerificationError(
            "Only verified users can perform this action. "
            "Please verify your account first."
        )

    if user_profile.is_suspended:
        raise UserSuspensionError(
            "Your account is suspended and cannot perform this action."
        )

    return True


def check_user_can_create_content(user_profile):
    """
    Check if a user can create content (posts, comments).

    Args:
        user_profile: UserProfile instance

    Raises:
        UserVerificationError: If user is not verified
        UserSuspensionError: If user is suspended
    """
    return check_user_can_interact(user_profile)


def check_user_can_react(user_profile):
    """
    Check if a user can react to content (likes, dislikes, shares).

    Args:
        user_profile: UserProfile instance

    Raises:
        UserVerificationError: If user is not verified
        UserSuspensionError: If user is suspended
    """
    return check_user_can_interact(user_profile)


class VerifiedUserPermission(permissions.BasePermission):
    """
    DRF permission class to ensure only verified, non-suspended users
    can perform actions.
    """

    message = "Only verified users can perform this action."

    def has_permission(self, request, view):
        """Check if user has permission to perform the action."""
        # Allow read-only access for unauthenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Require authentication for write operations
        if not request.user.is_authenticated:
            return False

        # Check if user has a profile
        try:
            profile = request.user.profile
        except AttributeError:
            self.message = "User profile not found."
            return False

        # Check verification status
        if not profile.is_verified:
            self.message = (
                "Only verified users can perform this action. "
                "Please verify your account first."
            )
            return False

        # Check suspension status
        if profile.is_suspended:
            self.message = "Your account is suspended."
            return False

        return True


class VerifiedUserForContentPermission(VerifiedUserPermission):
    """
    Permission for content creation (posts, comments).
    """

    message = "Only verified users can create content."


class VerifiedUserForInteractionPermission(VerifiedUserPermission):
    """
    Permission for social interactions (likes, shares, etc.).
    """

    message = "Only verified users can interact with content."


def validate_user_for_interaction(user_profile, action_name="perform this action"):
    """
    Validate user can perform an interaction.
    Used in model clean() methods.

    Args:
        user_profile: UserProfile instance
        action_name: Description of the action being performed

    Raises:
        ValidationError: If user cannot perform the action
    """
    if not user_profile:
        raise ValidationError("User profile is required")

    if not user_profile.is_verified:
        raise ValidationError(
            f"Only verified users can {action_name}. "
            "Please verify your account first."
        )

    if user_profile.is_suspended:
        raise ValidationError(
            f"Your account is suspended and cannot {action_name}."
        )
