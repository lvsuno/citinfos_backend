"""Serializers for user registration, profile management, and authentication.
This module contains serializers for user registration, profile updates,
authentication, and other user-related functionalities."""
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import (
    UserProfile, ProfessionalProfile, UserSettings, Follow, Block,
    UserSession, UserEvent, VerificationCode, BadgeDefinition, UserBadge
)
from core.utils import get_client_ip


# Registration serializer
class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration with extended profile fields."""



    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)
    phone_number = serializers.CharField(required=True, max_length=20)
    date_of_birth = serializers.DateField(required=True)

    # Additional fields for UserProfile
    bio = serializers.CharField(required=False, allow_blank=True, max_length=500)
    division_id = serializers.UUIDField(required=True)
    # Municipality name for display/fallback purposes
    municipality = serializers.CharField(
        required=False, allow_blank=True, max_length=200
    )
    accept_terms = serializers.BooleanField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2',
                  'password_confirm', 'first_name', 'last_name',
                  'phone_number', 'date_of_birth', 'bio', 'division_id',
                  'municipality', 'accept_terms')

    def validate(self, attrs):
        password = attrs.get('password')
        # Accept both password2 and password_confirm
        password_confirm = (
            attrs.get('password2') or attrs.get('password_confirm')
        )

        if not password_confirm:
            raise serializers.ValidationError({
                "password": "Password confirmation is required."
            })

        if password != password_confirm:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # Validate accept_terms
        if not attrs.get('accept_terms'):
            raise serializers.ValidationError({
                "accept_terms": "You must accept the terms and conditions."
            })

        # Custom password strength validation
        if password:
            from .utils import validate_password_strength
            strength_result = validate_password_strength(password)

            # Require STRONG password (score = 5 - all requirements met)
            if strength_result['score'] < 5:
                missing_requirements = []
                requirements = strength_result['requirements']

                if not requirements['length']:
                    missing_requirements.append("at least 8 characters")
                if not requirements['uppercase']:
                    missing_requirements.append(
                        "at least one uppercase letter (A-Z)"
                    )
                if not requirements['lowercase']:
                    missing_requirements.append(
                        "at least one lowercase letter (a-z)"
                    )
                if not requirements['numbers']:
                    missing_requirements.append("at least one number (0-9)")
                if not requirements['special']:
                    missing_requirements.append(
                        "at least one special character (!@#$%^&*)"
                    )

                strength = strength_result['strength']
                missing = ', '.join(missing_requirements)
                error_message = (
                    f"Password is too weak ({strength}). Missing: {missing}"
                )
                raise serializers.ValidationError({"password": error_message})

        return attrs

    def validate_email(self, value):
        """Check that email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        """Check that username is unique."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_phone_number(self, value):
        """Validate phone number is not empty and has reasonable format."""
        if not value or not value.strip():
            raise serializers.ValidationError("Phone number is required.")
        # Basic validation - must contain at least some digits
        import re
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Phone number must contain digits.")
        return value.strip()

    def validate_date_of_birth(self, value):
        """Validate date of birth is reasonable."""
        if not value:
            raise serializers.ValidationError("Date of birth is required.")

        from datetime import date
        today = date.today()

        # Check if date is not in the future
        if value > today:
            raise serializers.ValidationError("Date of birth cannot be in the future.")

        # Check if age is reasonable (between 13-120 years old)
        age = (
            today.year - value.year -
            ((today.month, today.day) < (value.month, value.day))
        )
        if age < 13:
            raise serializers.ValidationError("You must be at least 13 years old to register.")
        if age > 120:
            raise serializers.ValidationError("Please enter a valid date of birth.")

        return value

    def create(self, validated_data):
        # Import logger
        import logging
        logger = logging.getLogger('accounts')

        # Remove password confirmation fields and pop all extra fields for UserProfile
        password2 = validated_data.pop('password2', None)
        password_confirm = validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')

        # Use whichever confirmation password was provided
        confirm_password = password2 or password_confirm
        if password != confirm_password:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # These fields are required, so they must be present in validated_data
        phone_number = validated_data.pop('phone_number')
        date_of_birth = validated_data.pop('date_of_birth')
        bio = validated_data.pop('bio', None)
        division_id = validated_data.pop('division_id', None)
        municipality = validated_data.pop('municipality', None)
        accept_terms = validated_data.pop('accept_terms', False)

        # OPTIMIZATION: Use database transaction for atomic operations
        from django.db import transaction

        with transaction.atomic():
            # Create User
            user = User.objects.create(**validated_data)
            user.set_password(password)
            user.is_active = False  # User must verify email/code
            user.save()

            # Prepare UserProfile fields
            profile_data = {
                'phone_number': phone_number,
                'date_of_birth': date_of_birth,
                'accept_terms': accept_terms,
            }

            if bio is not None:
                profile_data['bio'] = bio

            # Handle administrative division assignment
            division_obj = None

            if division_id:
                try:
                    from core.models import AdministrativeDivision
                    division_obj = AdministrativeDivision.objects.get(
                        id=division_id
                    )
                    profile_data['administrative_division'] = division_obj
                    logger.info(
                        f"Assigned division {division_obj.name} to user {user.pk}"
                    )
                except AdministrativeDivision.DoesNotExist:
                    logger.warning(
                        f"Division with ID {division_id} not found "
                        f"for user {user.pk}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error assigning division {division_id} "
                        f"to user {user.pk}: {e}"
                    )

            # Get or create the profile (signal should have created it, but be defensive)
            try:
                profile = UserProfile.objects.get(user=user)
                # Update with registration-specific data
                for key, value in profile_data.items():
                    setattr(profile, key, value)
                profile.save()
            except UserProfile.DoesNotExist:
                # Fallback: create profile if signal failed
                profile = UserProfile.objects.create(user=user, **profile_data)

        # OPTIMIZATION: Queue async location tasks if no division provided
        if not division_obj:
            request = self.context.get('request')
            if request:
                try:
                    from accounts.location_tasks import (
                        async_location_processing_task
                    )
                    ip = get_client_ip(request)
                    async_location_processing_task.delay(
                        user.pk, ip, '',
                        profile_email=user.email
                    )
                    logger.info(
                        f"Queued location processing for user {user.pk} "
                        f"with IP {ip}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to queue location processing for "
                        f"user {user.pk}: {e}"
                    )        # Queue verification email generation and sending
        try:
            from notifications.async_email_tasks import (
                send_verification_email_async
            )
            from accounts.models import VerificationCode
            import random
            import string

            # Generate verification code first
            code = ''.join(
                random.choices(string.ascii_uppercase + string.digits, k=8)
            )

            # Create verification code in database
            # Remove any existing verification codes
            VerificationCode.objects.filter(user=profile).delete()
            from django.utils import timezone
            from datetime import timedelta
            vcode = VerificationCode.objects.create(
                user=profile,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=5),
                is_used=False
            )

            # Send verification email with the generated code
            send_verification_email_async.delay(
                str(profile.id),
                code,
                'verification',
                {'expires_at': vcode.expires_at}
            )
        except Exception:
            # Fallback to synchronous if needed
            from accounts.tasks import generate_verification_code_for_user
            generate_verification_code_for_user(str(profile.id))

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Complete serializer for UserProfile with all fields."""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    location = serializers.CharField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user_username', 'user_email', 'user_first_name',
            'user_last_name', 'full_name', 'display_name', 'location',
            'role', 'phone_number', 'date_of_birth', 'bio',
            'profile_picture', 'cover_media', 'cover_media_type',
            'administrative_division',
            'is_private', 'show_email', 'show_phone', 'show_location',
            'is_verified', 'is_suspended', 'suspension_reason',
            'follower_count', 'following_count', 'posts_count',
            'engagement_score', 'content_quality_score', 'interaction_frequency',
            'created_at', 'updated_at', 'last_active'
        ]
        read_only_fields = (
            'id', 'user_username', 'user_email', 'user_first_name', 'user_last_name',
            'full_name', 'display_name', 'location', 'follower_count',
            'following_count', 'posts_count', 'engagement_score',
            'content_quality_score', 'interaction_frequency', 'created_at',
            'updated_at'
        )


class ProfessionalProfileSerializer(serializers.ModelSerializer):
    """Complete serializer for ProfessionalProfile."""
    profile_info = UserProfileSerializer(source='profile', read_only=True)

    class Meta:
        model = ProfessionalProfile
        fields = [
            'id', 'profile_info', 'description', 'phone', 'website',
            'business_address', 'company_name', 'job_title', 'years_experience',
            'certifications', 'services_offered', 'is_verified',
            'verification_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'profile_info', 'verification_date',
                           'created_at', 'updated_at')


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating User model fields."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating UserProfile fields."""
    user = UserUpdateSerializer()

    class Meta:
        model = UserProfile
        fields = [
            'user', 'phone_number', 'date_of_birth', 'bio',
            'profile_picture', 'cover_media', 'cover_media_type',
            'administrative_division',
            'is_private', 'show_email', 'show_phone', 'show_location'
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if user_data:
            user_serializer = UserUpdateSerializer(instance.user, data=user_data, partial=True)
            if user_serializer.is_valid():
                user_serializer.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance



class ProfessionalRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for professional user registration."""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    company_name = serializers.CharField(max_length=200)
    job_title = serializers.CharField(max_length=100)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password',
                 'password_confirm', 'company_name', 'job_title')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        company_name = validated_data.pop('company_name')
        job_title = validated_data.pop('job_title')
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Create user profile with professional role
        profile = UserProfile.objects.create(user=user, role='professional')

        # Create professional profile
        ProfessionalProfile.objects.create(
            profile=profile,
            company_name=company_name,
            job_title=job_title
        )
        return user


class VerificationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=8)


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    remember_me = serializers.BooleanField(required=False, default=False)

    # Allow extra device info fields but don't require them
    screen_resolution = serializers.CharField(required=False, allow_blank=True)
    timezone = serializers.CharField(required=False, allow_blank=True)
    platform = serializers.CharField(required=False, allow_blank=True)
    language = serializers.CharField(required=False, allow_blank=True)
    languages = serializers.CharField(required=False, allow_blank=True)
    color_depth = serializers.IntegerField(required=False, allow_null=True)
    hardware_concurrency = serializers.IntegerField(
        required=False, allow_null=True)
    device_memory = serializers.CharField(required=False, allow_blank=True)
    touch_support = serializers.CharField(required=False, allow_blank=True)
    cookie_enabled = serializers.CharField(required=False, allow_blank=True)
    webgl_vendor = serializers.CharField(required=False, allow_blank=True)
    webgl_renderer = serializers.CharField(required=False, allow_blank=True)
    canvas_fingerprint = serializers.CharField(
        required=False, allow_blank=True)
    audio_fingerprint = serializers.CharField(required=False, allow_blank=True)

    # Enhanced fingerprint fields for optimization
    client_fingerprint = serializers.CharField(required=False, allow_blank=True)
    available_fonts = serializers.CharField(required=False, allow_blank=True)
    plugins_hash = serializers.CharField(required=False, allow_blank=True)
    storage_quota = serializers.CharField(required=False, allow_blank=True)
    network_info = serializers.CharField(required=False, allow_blank=True)
    local_storage = serializers.CharField(required=False, allow_blank=True)
    session_storage = serializers.CharField(required=False, allow_blank=True)
    indexed_db = serializers.CharField(required=False, allow_blank=True)
    webgl_support = serializers.CharField(required=False, allow_blank=True)
    fonts = serializers.CharField(required=False, allow_blank=True)
    plugins = serializers.CharField(required=False, allow_blank=True)
    connection_type = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        username_or_email = attrs.get('username_or_email')
        password = attrs.get('password')

        if username_or_email and password:
            # First try to authenticate with username
            user = authenticate(username=username_or_email, password=password)

            # If that fails, try to find user by email and authenticate with username
            if not user:
                try:
                    from django.contrib.auth.models import User
                    user_obj = User.objects.get(email=username_or_email)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('Account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Username/email and password required')

        return attrs


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user serializer with profile information."""
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                 'date_joined', 'is_active', 'profile')
        read_only_fields = ('id', 'date_joined', 'is_active')


class FollowSerializer(serializers.ModelSerializer):
    """Serializer for Follow relationships."""
    follower_username = serializers.CharField(
        source='follower.user.username',
        read_only=True
    )
    followed_username = serializers.CharField(
        source='followed.user.username',
        read_only=True
    )

    class Meta:
        model = Follow
        fields = [
            'id', 'follower', 'followed', 'follower_username',
            'followed_username', 'status', 'created_at'
        ]
        read_only_fields = ('id', 'follower', 'created_at')


class BlockSerializer(serializers.ModelSerializer):
    """Serializer for Block relationships."""
    blocker_username = serializers.CharField(
        source='blocker.user.username',
        read_only=True
    )
    blocked_username = serializers.CharField(
        source='blocked.user.username',
        read_only=True
    )

    class Meta:
        model = Block
        fields = [
            'id', 'blocker', 'blocked', 'blocker_username',
            'blocked_username', 'reason', 'created_at'
        ]
        read_only_fields = ('id', 'blocker', 'created_at')


class UserSessionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating user sessions."""
    class Meta:
        model = UserSession
        fields = [
            'id', 'session_id', 'ip_address', 'user_agent',
            'device_info', 'location_data', 'device_fingerprint',
            'pages_visited', 'is_active'
        ]
        read_only_fields = ['id']


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for user sessions with full details."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )

    class Meta:
        model = UserSession
        fields = [
            'id', 'user', 'user_username', 'session_id', 'ip_address',
            'user_agent', 'device_info', 'location_data', 'device_fingerprint',
            'pages_visited', 'started_at', 'ended_at', 'is_active'
        ]
        read_only_fields = ['id', 'user', 'started_at']


class UserEventCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating user events."""
    class Meta:
        model = UserEvent
        fields = [
            'id', 'session', 'event_type', 'severity', 'description',
            'metadata', 'success', 'error_message', 'target_user',
            'requires_review'
        ]
        read_only_fields = ['id']


class UserEventSerializer(serializers.ModelSerializer):
    """Serializer for user events with full details."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )
    session_id = serializers.CharField(
        source='session.session_id', read_only=True, allow_null=True
    )

    class Meta:
        model = UserEvent
        fields = [
            'id', 'user', 'user_username', 'session', 'session_id',
            'event_type', 'severity', 'description', 'metadata',
            'success', 'error_message', 'target_user', 'requires_review',
            'reviewed_at', 'reviewed_by', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class UserSettingsSerializer(serializers.ModelSerializer):
    """Serializer for UserSettings model."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )

    class Meta:
        model = UserSettings
        fields = [
            'id', 'user', 'user_username', 'email_notifications',
            'push_notifications', 'warranty_expiry_notifications',
            'maintenance_reminder_notifications', 'notification_frequency',
            'profile_visibility', 'language', 'theme', 'timezone',
            'auto_play_videos', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')


class VerificationCodeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating verification codes."""
    class Meta:
        model = VerificationCode
        fields = [
            'id', 'user', 'code', 'is_used', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VerificationCodeDetailSerializer(serializers.ModelSerializer):
    """Serializer for verification codes with full details."""
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )

    class Meta:
        model = VerificationCode
        fields = [
            'id', 'user', 'user_username', 'code', 'created_at',
            'updated_at', 'is_used', 'expires_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class BadgeDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for BadgeDefinition model."""
    awards_count = serializers.IntegerField(
        source='awards.count', read_only=True
    )

    class Meta:
        model = BadgeDefinition
        fields = [
            'id', 'code', 'full_name', 'name', 'tier', 'description', 'icon',
            'criteria', 'is_secret', 'points', 'is_active', 'awards_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = (
            'id', 'name', 'tier', 'awards_count', 'created_at', 'updated_at'
        )


class UserBadgeSerializer(serializers.ModelSerializer):
    """Serializer for UserBadge model."""
    user_username = serializers.CharField(
        source='profile.user.username', read_only=True
    )
    badge_name = serializers.CharField(
        source='badge.name', read_only=True
    )
    badge_tier = serializers.CharField(
        source='badge.tier', read_only=True
    )
    badge_code = serializers.CharField(
        source='badge.code', read_only=True
    )
    badge_icon = serializers.CharField(
        source='badge.icon', read_only=True
    )
    badge_points = serializers.IntegerField(
        source='badge.points', read_only=True
    )
    badge_description = serializers.CharField(
        source='badge.description', read_only=True
    )

    class Meta:
        model = UserBadge
        fields = [
            'id', 'profile', 'badge', 'user_username', 'badge_name',
            'badge_tier', 'badge_code', 'badge_icon', 'badge_points',
            'badge_description', 'first_trigger_event', 'metadata', 'earned_at'
        ]
        read_only_fields = (
            'id', 'user_username', 'badge_name', 'badge_tier',
            'badge_code', 'badge_icon', 'badge_points', 'badge_description',
            'earned_at'
        )
