"""Serializers for the communities app."""

from rest_framework import serializers
from accounts.models import UserProfile
from core.timezone_utils import validate_timezone_restrictions

from .models import (
    Community, CommunityMembership, Thread,
    # CommunityInvitation, CommunityJoinRequest,  # Public communities only
    CommunityRole, CommunityModeration, CommunityAnnouncement
)

# # Serializer for CommunityJoinRequest - COMMENTED OUT (public communities only)
# class CommunityJoinRequestSerializer(serializers.ModelSerializer):
#     """Serializer for community join requests."""
#     user_username = serializers.CharField(source='user.user.username', read_only=True)
#     reviewed_by_username = serializers.CharField(source='reviewed_by.user.username', read_only=True)

#     class Meta:
#         model = CommunityJoinRequest
#         fields = [
#             'id', 'community', 'user', 'user_username', 'message', 'status',
#             'reviewed_by', 'reviewed_by_username', 'review_message',
#             'created_at', 'reviewed_at', 'is_deleted', 'deleted_at'
#         ]
#         read_only_fields = ['id', 'created_at', 'reviewed_at', 'reviewed_by', 'reviewed_by_username']


class CommunityMembershipSerializer(serializers.ModelSerializer):
    """Serializer for community membership."""
    user_username = serializers.CharField(source='user.user.username', read_only=True)

    class Meta:
        model = CommunityMembership
        fields = ['id', 'user', 'user_username', 'role', 'status', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class CommunityRoleSerializer(serializers.ModelSerializer):
    """Serializer for community roles."""

    class Meta:
        model = CommunityRole
        fields = [
            'id', 'community', 'name', 'permissions',
            'color', 'is_default', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ThreadSerializer(serializers.ModelSerializer):
    """Serializer for Thread (discussion topics) within communities."""
    creator_username = serializers.CharField(
        source='creator.user.username',
        read_only=True
    )
    community_name = serializers.CharField(
        source='community.name',
        read_only=True
    )
    community_slug = serializers.CharField(
        source='community.slug',
        read_only=True
    )

    # Optional: Include first post when creating thread
    first_post_content = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=2000,
        help_text="Optional first post content when creating thread"
    )
    first_post_type = serializers.ChoiceField(
        write_only=True,
        required=False,
        choices=['text', 'image', 'video', 'audio', 'file', 'poll'],
        default='text',
        help_text="Type of the first post"
    )

    class Meta:
        model = Thread
        fields = [
            'id', 'community', 'community_name', 'community_slug',
            'title', 'slug', 'creator', 'creator_username', 'body',
            'is_closed', 'is_pinned', 'allow_comments', 'posts_count',
            'created_at', 'updated_at',
            # Write-only fields for first post
            'first_post_content', 'first_post_type'
        ]
        read_only_fields = [
            'id', 'slug', 'creator', 'posts_count',
            'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        """Create thread and optionally create first post."""
        from content.models import Post
        from django.db import transaction

        # Extract first post data
        first_post_content = validated_data.pop('first_post_content', None)
        first_post_type = validated_data.pop('first_post_type', 'text')

        # Create thread
        with transaction.atomic():
            thread = super().create(validated_data)

            # Create first post if content provided
            if first_post_content and first_post_content.strip():
                Post.objects.create(
                    author=thread.creator,
                    community=thread.community,
                    thread=thread,
                    content=first_post_content,
                    post_type=first_post_type,
                    visibility='community'
                )

        return thread


class CommunitySerializer(serializers.ModelSerializer):
    """Serializer for Community model."""
    creator_username = serializers.CharField(source='creator.user.username', read_only=True)
    # membership_count removed - communities are public, no membership tracking
    posts_count = serializers.IntegerField(read_only=True)
    threads_count = serializers.IntegerField(read_only=True)
    user_is_member = serializers.SerializerMethodField()
    user_can_post = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()

    # Division info (optional - can be null)
    division_info = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = [
            'id', 'name', 'slug', 'description', 'community_type',
            'cover_media', 'cover_media_type', 'avatar', 'creator', 'creator_username',
            'rules', 'tags', 'allow_posts', 'require_post_approval',
            'allow_external_links', 'division', 'division_info', 'posts_count', 'threads_count',
            'user_is_member', 'user_can_post', 'user_role',
            'is_active', 'is_featured', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']

    def get_division_info(self, obj):
        """Get division details if division is set."""
        if obj.division:
            return {
                'id': str(obj.division.id),
                'name': obj.division.name,
                'boundary_type': obj.division.boundary_type,
                'admin_level': obj.division.admin_level,
            }
        return None

    def get_user_is_member(self, obj):
        """Check if the current user is a member of the community."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user)
                return obj.memberships.filter(user=profile, status='active').exists()
            except UserProfile.DoesNotExist:
                return False
        return False

    def get_user_can_post(self, obj):
        """Check if the current user can post in the community."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        if not obj.allow_posts:
            return False

        try:
            profile = UserProfile.objects.get(user=request.user)
            membership = obj.memberships.filter(user=profile, status='active').first()
            if not membership:
                return obj.community_type == 'public'

            # Check role permissions
            return membership.role.permissions.get('can_post', True) if membership.role else True
        except UserProfile.DoesNotExist:
            return False

    def get_user_role(self, obj):
        """Get the current user's role in the community."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user)
                membership = obj.memberships.filter(user=profile, status='active').first()
                if membership and membership.role:
                    # Extract the role type from the full role name
                    # e.g., "Moderator - community test husler" -> "moderator"
                    role_name = membership.role.name
                    if ' - ' in role_name:
                        role_type = role_name.split(' - ')[0].lower()
                    else:
                        role_type = role_name.lower()

                    # Map role types to standard values
                    role_mapping = {
                        'creator': 'creator',
                        'admin': 'admin',
                        'administrator': 'admin',
                        'moderator': 'moderator',
                        'mod': 'moderator',
                        'member': 'member',
                        'user': 'member'
                    }

                    return role_mapping.get(role_type, 'member')
                return None
            except UserProfile.DoesNotExist:
                return None
        return None


class CommunityCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating communities."""
    slug = serializers.SlugField(read_only=True)
    creator = serializers.PrimaryKeyRelatedField(read_only=True)
    creator_username = serializers.CharField(
        source='creator.user.username', read_only=True
    )

    # Geo-restriction fields for frontend convenience
    # allowed_countries = serializers.ListField(
    #     child=serializers.CharField(), required=False, write_only=True
    # )
    # blocked_countries = serializers.ListField(
    #     child=serializers.CharField(), required=False, write_only=True
    # )
    # allowed_cities = serializers.ListField(
    #     child=serializers.CharField(), required=False, write_only=True
    # )
    # blocked_cities = serializers.ListField(
    #     child=serializers.CharField(), required=False, write_only=True
    # )
    # allowed_timezones = serializers.ListField(
    #     child=serializers.CharField(), required=False, write_only=True
    # )
    # blocked_timezones = serializers.ListField(
    #     child=serializers.CharField(), required=False, write_only=True
    # )
    # selected_country_for_cities = serializers.CharField(
    #     required=False, write_only=True
    # )

    # Moderators field for assigning moderators during community creation
    moderators = serializers.ListField(
        child=serializers.CharField(), required=False, write_only=True,
        help_text="List of user profile IDs to assign as moderators"
    )

    # Welcome message fields for creating announcement during creation
    enable_welcome_message = serializers.BooleanField(
        required=False, write_only=True, default=False
    )
    welcome_message_title = serializers.CharField(
        required=False, write_only=True, max_length=200, default='Welcome!'
    )
    welcome_message_content = serializers.CharField(
        required=False, write_only=True, max_length=5000
    )
    welcome_message_banner_style = serializers.ChoiceField(
        required=False, write_only=True, default='none',
        choices=[
            ('none', 'None'),
            ('static', 'Static'),
            ('scrolling', 'Scrolling'),
            ('fade', 'Fade'),
            ('slide', 'Slide')
        ]
    )

    class Meta:
        model = Community
        fields = [
            'id', 'name', 'slug', 'description', 'community_type',
            'cover_media', 'cover_media_type', 'avatar', 'rules', 'tags',
            'allow_posts', 'require_post_approval', 'allow_external_links',
            'division',  # Optional division FK
            # 'is_geo_restricted', 'geo_restriction_type',
            # 'geo_restriction_message',
            'creator', 'creator_username', 'created_at', 'updated_at',
            # Geo-restriction convenience fields
            # 'allowed_countries', 'blocked_countries',
            # 'allowed_cities', 'blocked_cities',
            # 'allowed_timezones', 'blocked_timezones',
            # 'selected_country_for_cities',
            # Moderator assignment field
            'moderators',
            # Welcome message fields
            'enable_welcome_message', 'welcome_message_title',
            'welcome_message_content', 'welcome_message_banner_style'
        ]
    # slug is generated server-side; clients should not set it
    read_only_fields = ['id', 'creator', 'created_at', 'updated_at', 'slug']

    def validate_slug(self, value):
        """Validate that slug is unique."""
        if self.instance:
            # For updates, exclude current instance
            if Community.objects.filter(slug=value).exclude(
                id=self.instance.id
            ).exists():
                raise serializers.ValidationError(
                    "A community with this slug already exists."
                )
        else:
            # For creation
            if Community.objects.filter(slug=value).exists():
                raise serializers.ValidationError(
                    "A community with this slug already exists."
                )
        return value

    # def validate(self, data):
    #     """Validate geo-restriction data and check for timezone conflicts."""
    #     # Only validate if geo-restrictions are enabled
    #     if not data.get('is_geo_restricted', False):
    #         return data

    #     geo_restriction_type = data.get('geo_restriction_type', 'none')

    #     if geo_restriction_type == 'timezone_based':
    #         allowed_timezones = data.get('allowed_timezones', [])
    #         blocked_timezones = data.get('blocked_timezones', [])

    #         # Check for timezone equivalency conflicts
    #         try:
    #             validate_timezone_restrictions(
    #                 allowed_timezones, blocked_timezones
    #             )
    #         except ValueError as e:
    #             raise serializers.ValidationError({
    #                 'timezone_restrictions': str(e)
    #             })

    #         # Ensure at least one timezone restriction is specified
    #         if not allowed_timezones and not blocked_timezones:
    #             raise serializers.ValidationError({
    #                 'timezone_restrictions':
    #                 'Please specify at least one timezone (allowed or '
    #                 'blocked) for timezone-based restrictions.'
    #             })

    #     elif geo_restriction_type == 'countries':
    #         allowed_countries = data.get('allowed_countries', [])
    #         if not allowed_countries:
    #             raise serializers.ValidationError({
    #                 'allowed_countries':
    #                 'Please select at least one allowed country for '
    #                 'country-based restrictions.'
    #             })

    #     elif geo_restriction_type == 'cities':
    #         allowed_cities = data.get('allowed_cities', [])
    #         selected_country_for_cities = data.get(
    #             'selected_country_for_cities'
    #         )

    #         if not selected_country_for_cities:
    #             raise serializers.ValidationError({
    #                 'selected_country_for_cities':
    #                 'Please select a country for city-based restrictions.'
    #             })

    #         if not allowed_cities:
    #             raise serializers.ValidationError({
    #                 'allowed_cities':
    #                 'Please select at least one city for '
    #                 'city-based restrictions.'
    #             })

    #     return data

    def create(self, validated_data):
        """Create community and associated geo-restrictions and moderators."""
        # Debug: Check if files are in validated_data
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 Community creation validated_data keys: {list(validated_data.keys())}")
        logger.info(f"🔍 cover_media in validated_data: {validated_data.get('cover_media', 'NOT_FOUND')}")
        logger.info(f"🔍 avatar in validated_data: {validated_data.get('avatar', 'NOT_FOUND')}")

        # Extract geo-restriction data and moderators
        # geo_data = self._extract_geo_data(validated_data)
        moderator_ids = validated_data.pop('moderators', [])

        # Extract welcome message data
        welcome_data = self._extract_welcome_message_data(validated_data)

        # Create the community
        community = super().create(validated_data)

        # Debug: Check if files were saved
        logger.info(f"🔍 After creation - cover_media: {community.cover_media}")
        logger.info(f"🔍 After creation - avatar: {community.avatar}")

        # Create geo-restrictions if specified
        # if community.is_geo_restricted and geo_data:
        #     self._create_geo_restrictions(community, geo_data)

        # Assign moderators if specified
        if moderator_ids:
            self._assign_moderators(community, moderator_ids)

        # Create welcome message if specified
        if welcome_data.get('enable_welcome_message'):
            self._create_welcome_message(community, welcome_data)

        return community

    def update(self, instance, validated_data):
        """Update community and associated geo-restrictions and moderators."""
        # Extract geo-restriction data and moderators
        # geo_data = self._extract_geo_data(validated_data)
        moderator_ids = validated_data.pop('moderators', None)

        # Update the community
        community = super().update(instance, validated_data)

        # Update geo-restrictions
        # if community.is_geo_restricted and geo_data:
        #     # Clear existing restrictions for this community
        #     CommunityGeoRestriction.objects.filter(
        #         community=community
        #     ).delete()
        #     # Create new restrictions
        #     self._create_geo_restrictions(community, geo_data)
        # elif not community.is_geo_restricted:
        #     # Remove all restrictions if geo-restriction is disabled
        #     CommunityGeoRestriction.objects.filter(
        #         community=community
        #     ).delete()

        # Update moderators if specified
        if moderator_ids is not None:
            # Get the moderator role for this community
            moderator_role = CommunityRole.objects.filter(
                community=community,
                name='Moderator'
            ).first()

            # Get the default member role
            member_role = CommunityRole.objects.filter(
                community=community,
                is_default=True
            ).first()

            if moderator_role and member_role:
                # Update existing moderator memberships to member role
                CommunityMembership.objects.filter(
                    community=community,
                    role=moderator_role
                ).update(role=member_role)

            # Assign new moderators
            self._assign_moderators(community, moderator_ids)

        return community

    # def _extract_geo_data(self, validated_data):
        """Extract and remove geo-restriction data from validated_data."""
        geo_fields = [
            'allowed_countries', 'blocked_countries',
            'allowed_cities', 'blocked_cities',
            'allowed_timezones', 'blocked_timezones',
            'selected_country_for_cities'
        ]

        geo_data = {}
        for field in geo_fields:
            if field in validated_data:
                geo_data[field] = validated_data.pop(field)

        return geo_data

    # def _create_geo_restrictions(self, community, geo_data):
    #     """Create CommunityGeoRestriction objects from geo_data."""
    #     from core.models import Country, City

    #     # Handle country restrictions
    #     for country_id in geo_data.get('allowed_countries', []):
    #         try:
    #             country = Country.objects.get(id=country_id)
    #             CommunityGeoRestriction.objects.create(
    #                 community=community,
    #                 restriction_type='allow_country',
    #                 country=country,
    #                 is_active=True
    #             )
    #         except Country.DoesNotExist:
    #             continue

    #     for country_id in geo_data.get('blocked_countries', []):
    #         try:
    #             country = Country.objects.get(id=country_id)
    #             CommunityGeoRestriction.objects.create(
    #                 community=community,
    #                 restriction_type='block_country',
    #                 country=country,
    #                 is_active=True
    #             )
    #         except Country.DoesNotExist:
    #             continue

    #     # Handle city restrictions
    #     selected_country_id = geo_data.get('selected_country_for_cities')
    #     if selected_country_id:
    #         try:
    #             selected_country = Country.objects.get(id=selected_country_id)

    #             for city_id in geo_data.get('allowed_cities', []):
    #                 try:
    #                     city = City.objects.get(id=city_id)
    #                     CommunityGeoRestriction.objects.create(
    #                         community=community,
    #                         restriction_type='allow_city',
    #                         country=selected_country,
    #                         city=city,
    #                         is_active=True
    #                     )
    #                 except City.DoesNotExist:
    #                     continue

    #             for city_id in geo_data.get('blocked_cities', []):
    #                 try:
    #                     city = City.objects.get(id=city_id)
    #                     CommunityGeoRestriction.objects.create(
    #                         community=community,
    #                         restriction_type='block_city',
    #                         country=selected_country,
    #                         city=city,
    #                         is_active=True
    #                     )
    #                 except City.DoesNotExist:
    #                     continue
    #         except Country.DoesNotExist:
    #             pass

    #     # Handle timezone restrictions
    #     allowed_timezones = geo_data.get('allowed_timezones', [])
    #     blocked_timezones = geo_data.get('blocked_timezones', [])

    #     if allowed_timezones or blocked_timezones:
    #         # Create timezone restriction entry
    #         timezone_data = {}
    #         if allowed_timezones:
    #             timezone_data['allowed'] = allowed_timezones
    #         if blocked_timezones:
    #             timezone_data['blocked'] = blocked_timezones

    #         CommunityGeoRestriction.objects.create(
    #             community=community,
    #             restriction_type='timezone',
    #             timezone_list=timezone_data,
    #             is_active=True
    #         )

    def _assign_moderators(self, community, moderator_ids):
        """Assign users as moderators to the community."""
        from .models import CommunityMembership, CommunityRole

        # Get the moderator role for this community
        moderator_role = CommunityRole.objects.filter(
            community=community,
            name='Moderator'
        ).first()

        if not moderator_role:
            # Create moderator role if it doesn't exist
            moderator_role = CommunityRole.objects.create(
                community=community,
                name='Moderator',
                permissions={
                    'can_post': True,
                    'can_comment': True,
                    'can_vote': True,
                    'can_report': True,
                    'can_moderate': True,
                    'can_manage_members': True,
                    'can_manage_community': False,
                    'can_delete_posts': True,
                    'can_ban_users': True
                },
                color='#2563eb',
                is_default=False
            )

        for moderator_id in moderator_ids:
            try:
                moderator_profile = UserProfile.objects.get(id=moderator_id)

                # Check if user is already a member
                membership, created = CommunityMembership.objects.get_or_create(
                    community=community,
                    user=moderator_profile,
                    defaults={
                        'role': moderator_role,
                        'status': 'active'
                    }
                )

                # If membership already exists, update role to moderator
                if not created:
                    membership.role = moderator_role
                    membership.status = 'active'
                    membership.save()

            except UserProfile.DoesNotExist:
                # Skip invalid user profiles
                continue

    def _extract_welcome_message_data(self, validated_data):
        """Extract and remove welcome message data from validated_data."""
        welcome_fields = [
            'enable_welcome_message', 'welcome_message_title',
            'welcome_message_content', 'welcome_message_banner_style'
        ]

        welcome_data = {}
        for field in welcome_fields:
            if field in validated_data:
                welcome_data[field] = validated_data.pop(field)

        return welcome_data

    def _create_welcome_message(self, community, welcome_data):
        """Create a welcome message announcement for the community."""
        import re
        from .models import CommunityAnnouncement

        # Get required fields
        content = welcome_data.get('welcome_message_content', '').strip()
        if not content:
            return  # Skip if no content

        title = welcome_data.get('welcome_message_title', 'Welcome!').strip()
        banner_style = welcome_data.get('welcome_message_banner_style', 'none')

        # Validate banner style
        valid_banner_styles = [
            'none', 'static', 'scrolling', 'fade', 'slide'
        ]
        if banner_style not in valid_banner_styles:
            banner_style = 'none'

        # Validate character limit for animated banners
        animated_styles = ['scrolling', 'fade', 'slide']
        if banner_style in animated_styles:
            text_content = re.sub(r'<[^>]+>', '', content)
            if len(text_content) > 180:
                banner_style = 'static'

        # Sanitize the HTML content
        try:
            from core.html_sanitizer import sanitize_announcement_html
            cleaned_content = sanitize_announcement_html(content)
        except ImportError:
            # Fallback: basic HTML escaping
            import html
            cleaned_content = html.escape(content)

        # Create the announcement (using community creator as created_by)
        try:
            CommunityAnnouncement.objects.create(
                community=community,
                title=title,
                body_html=cleaned_content,
                created_by=community.creator,
                is_published=True,
                is_sticky=True,
                is_welcome_message=True,
                banner_style=banner_style
            )
        except Exception:
            # Silently fail if announcement creation fails
            pass


class CommunityModerationSerializer(serializers.ModelSerializer):
    """Serializer for community moderation actions."""
    moderator_username = serializers.CharField(source='moderator.user.username', read_only=True)
    target_username = serializers.CharField(source='target.user.username', read_only=True)

    class Meta:
        model = CommunityModeration
        fields = [
            'id', 'community', 'moderator', 'moderator_username',
            'target', 'target_username', 'action_type', 'reason',
            'duration', 'is_active', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'moderator', 'created_at']


# # Commented out - Public communities don't use invitations
# class CommunityInvitationSerializer(serializers.ModelSerializer):
#     """Serializer for community invitations."""
#     inviter_username = serializers.CharField(source='inviter.user.username', read_only=True)
#     invitee_username = serializers.CharField(source='invitee.user.username', read_only=True)

#     class Meta:
#         model = CommunityInvitation
#         fields = [
#             'id', 'community', 'inviter', 'inviter_username',
#             'invitee', 'invitee_username', 'message', 'status',
#             'created_at', 'expires_at', 'responded_at'
#         ]
#         read_only_fields = ['id', 'inviter', 'created_at', 'responded_at']


class CommunityAnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for community-specific announcements."""
    created_by_username = serializers.CharField(source='created_by.user.username', read_only=True)
    created_by_display_name = serializers.CharField(source='created_by.display_name', read_only=True)
    community_name = serializers.CharField(source='community.name', read_only=True)
    can_edit = serializers.SerializerMethodField()
    is_currently_published = serializers.SerializerMethodField()

    class Meta:
        model = CommunityAnnouncement
        fields = [
            'id', 'community', 'community_name', 'title', 'body_html',
            'created_by', 'created_by_username', 'created_by_display_name',
            'is_published', 'is_sticky', 'is_important', 'is_welcome_message',
            'banner_style', 'publish_at', 'expires_at', 'created_at', 'updated_at',
            'can_edit', 'is_currently_published'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_can_edit(self, obj):
        """Check if current user can edit this announcement."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        try:
            user_profile = UserProfile.objects.get(user=request.user)
            return obj.can_user_edit(user_profile)
        except UserProfile.DoesNotExist:
            return False

    def get_is_currently_published(self, obj):
        """Check if announcement is currently published."""
        return obj.is_currently_published()

    def validate(self, data):
        """Validate announcement data."""
        # Check if user can create/edit announcements for this community
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                community = data.get('community')

                if community and not self._can_manage_community_announcements(user_profile, community):
                    raise serializers.ValidationError(
                        "You don't have permission to manage announcements for this community."
                    )
            except UserProfile.DoesNotExist:
                raise serializers.ValidationError("User profile not found.")

        return data

    def _can_manage_community_announcements(self, user_profile, community):
        """Check if user can manage announcements for the community."""
        # Community creator can always manage
        if community.creator == user_profile:
            return True

        # Check if user is a community moderator/admin
        try:
            from .models import CommunityMembership
            membership = CommunityMembership.objects.get(
                community=community,
                user=user_profile,
                status='active',
                is_deleted=False
            )

            if membership.role:
                role_name = membership.role.name.lower()
                return role_name in ['admin', 'moderator']
        except CommunityMembership.DoesNotExist:
            pass

        return False
