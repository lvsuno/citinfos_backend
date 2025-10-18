from rest_framework import serializers
from .models import Country


class CountrySerializer(serializers.ModelSerializer):
    """Serializer for Country model with phone data."""

    class Meta:
        model = Country
        fields = [
            'id',
            'iso2',
            'iso3',
            'name',
            'code',
            'phone_code',
            'flag_emoji',
            'region',
            'default_admin_level',
        ]
        read_only_fields = fields


class CountryPhoneDataSerializer(serializers.ModelSerializer):
    """Lightweight serializer for country phone data only."""

    class Meta:
        model = Country
        fields = [
            'iso2',
            'iso3',
            'name',
            'phone_code',
            'flag_emoji',
            'region',
        ]
        read_only_fields = fields


class AnnouncementSerializer(serializers.ModelSerializer):
    can_edit = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.user.username', read_only=True)
    target_specific_user_username = serializers.CharField(source='target_specific_user.user.username', read_only=True)
    target_community_name = serializers.CharField(source='target_community.name', read_only=True)

    class Meta:
        model = None  # set dynamically in views to avoid circular imports
        fields = [
            'id', 'title', 'body_html', 'created_by', 'created_by_username',
            'is_system_generated', 'is_published', 'is_sticky', 'is_important',
            'is_welcome_message', 'banner_style',
            'target_specific_user', 'target_specific_user_username',
            'target_community', 'target_community_name',
            'target_user_roles', 'target_countries', 'target_timezones',
            'target_cities', 'target_regions',
            'created_at', 'updated_at', 'can_edit'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'can_edit',
            'created_by_username', 'target_specific_user_username', 'target_community_name'
        ]

    def get_can_edit(self, obj):
        """Check if current user can edit this announcement."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        try:
            from accounts.models import UserProfile
            user_profile = UserProfile.objects.get(user=request.user)
            return obj.can_user_edit(user_profile)
        except UserProfile.DoesNotExist:
            return False

    def validate(self, data):
        """Validate announcement data."""
        # Only admins/moderators can create non-system announcements
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                from accounts.models import UserProfile
                user_profile = UserProfile.objects.get(user=request.user)

                # If not system-generated and user is not admin/moderator
                if not data.get('is_system_generated', False):
                    if user_profile.role not in ['admin', 'moderator']:
                        raise serializers.ValidationError(
                            "Only administrators and moderators can create global announcements."
                        )
                    # Set the created_by field for non-system announcements
                    data['created_by'] = user_profile
                else:
                    # System-generated announcements should not have a created_by user
                    data['created_by'] = None

            except UserProfile.DoesNotExist:
                raise serializers.ValidationError("User profile not found.")

        return data
