from rest_framework import permissions
from rest_framework.exceptions import NotAuthenticated


class IsAuthenticatedOrPublicContent(permissions.BasePermission):
    """
    Custom permission to allow public content to be viewable by anyone,
    while requiring authentication for private/followers/community content.
    """

    def has_permission(self, request, view):
        """Check if the user has permission to access the view."""
        # For read operations (GET), allow access
        if request.method in permissions.SAFE_METHODS:
            return True

        # For write operations, check authentication
        if not request.user.is_authenticated:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        # Check if object has visibility attribute (for Posts)
        if hasattr(obj, 'visibility'):
            # Public content is accessible to everyone
            if obj.visibility == 'public':
                return True

            # For non-public content, user must be authenticated
            if not request.user or not request.user.is_authenticated:
                return False

            # Private content only for author
            if obj.visibility == 'private':
                return obj.author == request.user

            # Followers content - check if user follows the author
            if obj.visibility == 'followers':
                following_ids = request.user.userprofile.following.values_list('followed_id', flat=True)
                return (obj.author == request.user.userprofile or
                        obj.author.id in following_ids)

            # Community content - check if user is a member of the community
            if obj.visibility == 'community':
                # If user is the author, they can always access
                if obj.author == request.user.userprofile:
                    return True

                # Check if post belongs to a community
                if hasattr(obj, 'community') and obj.community:
                    # Import here to avoid circular imports
                    from communities.models import CommunityMembership

                    # Check if user is an active member of the community
                    return CommunityMembership.objects.filter(
                        community=obj.community,
                        user=request.user.userprofile,
                        status='active'
                    ).exists()

                # If no community is associated, deny access
                return False

        # For objects without visibility (like shares), check authentication
        # and either the author or has permission to view shared content
        if hasattr(obj, 'author'):
            if not request.user or not request.user.is_authenticated:
                return False
            return obj.author == request.user

        # Default: require auth for write operations, allow read for public
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.author == request.user


class IsRegionAllowed(permissions.BasePermission):
    """
    Custom permission to allow users to interact only with communities or posts
    created for their region or country.
    """

    def has_object_permission(self, request, view, obj):
        """Check if the user's region matches the object's allowed regions."""
        # Assume user region is stored in userprofile.region or userprofile.country
        user_region = getattr(getattr(request.user, 'userprofile', None), 'region', None)
        if not user_region:
            return False

        # For communities
        if hasattr(obj, 'region'):
            return obj.region == user_region

        # For posts with allowed regions (e.g., obj.allowed_regions is a list or queryset)
        if hasattr(obj, 'allowed_regions'):
            return user_region in obj.allowed_regions.all() if hasattr(obj.allowed_regions, 'all') else user_region in obj.allowed_regions

        # Default deny
        return False
