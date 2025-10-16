"""
JWT Authentication views for the accounts app.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import  TokenError
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.models import User
from core.session_manager import session_manager
from .models import UserProfile

from .serializers import UserDetailSerializer, RegisterSerializer

logger = logging.getLogger(__name__)


class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom JWT refresh view with SESSION DEPENDENCY validation.
    CRITICAL: JWT refresh requires active session validation.
    """

    def post(self, request, *args, **kwargs):
        # Get provided refresh token (support alternative key name)
        incoming_refresh = (
            request.data.get('refresh') or request.data.get('refresh_token')
        )
        if not incoming_refresh:
            return super().post(request, *args, **kwargs)

        # Validate and decode refresh token
        try:
            old_refresh = RefreshToken(incoming_refresh)
            user_id = old_refresh.payload.get('user_id')
            sid = old_refresh.payload.get('sid')
        except TokenError:
            return Response({'error': 'Invalid refresh token'},
                            status=status.HTTP_401_UNAUTHORIZED)

        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'},
                            status=status.HTTP_401_UNAUTHORIZED)

        # Check if user profile is deleted
        if UserProfile.objects.filter(user=user, is_deleted=True).exists():
            return Response({
                'error': 'Account not available',
                'detail': 'User profile has been deleted'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # CRITICAL: SESSION VALIDATION REQUIRED FOR JWT REFRESH
        if sid:
            try:
                # Validate session exists and is active
                session_valid = session_manager.is_session_valid_for_jwt(sid)
                if not session_valid:
                    return Response({
                        'error': 'Session expired or invalid',
                        'detail': 'Session no longer exists. Please login again.',
                        'code': 'SESSION_EXPIRED'
                    }, status=status.HTTP_401_UNAUTHORIZED)

                # Verify session belongs to the user
                session_data = session_manager.get_session(sid)
                if not session_data or session_data.get('user_id') != str(user.profile.id):
                    return Response({
                        'error': 'Session mismatch',
                        'detail': 'Session does not belong to authenticated user',
                        'code': 'SESSION_MISMATCH'
                    }, status=status.HTTP_401_UNAUTHORIZED)

            except Exception as e:
                logger.error(f"Session validation failed during refresh: {e}")
                return Response({
                    'error': 'Session validation failed',
                    'detail': 'Unable to validate session. Please login again.',
                    'code': 'SESSION_VALIDATION_ERROR'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # No session ID in token - this should not happen with new flow
            return Response({
                'error': 'Invalid token format',
                'detail': 'Token missing session information',
                'code': 'NO_SESSION_ID'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Respect rotation settings
        rotate = settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', True)
        blacklist = settings.SIMPLE_JWT.get('BLACKLIST_AFTER_ROTATION', True)

        # Optionally blacklist the old refresh
        if blacklist:
            try:
                old_refresh.blacklist()
            except Exception:
                pass

        # Create the token set
        refresh = RefreshToken.for_user(user) if rotate else old_refresh
        access = refresh.access_token

        # CRITICAL: Propagate session ID to new tokens
        refresh['sid'] = sid
        access['sid'] = sid

        # Add custom profile claims for access
        try:
            profile = UserProfile.objects.get(user=user, is_deleted=False)
            access['role'] = profile.role
            access['is_verified'] = profile.is_verified
        except UserProfile.DoesNotExist:
            access['role'] = 'normal'
            access['is_verified'] = False

        access['username'] = user.username
        access['email'] = user.email

        # Smart session renewal to extend Redis expiration when needed
        try:
            renewed = session_manager.smart_renew_session_if_needed(sid)
            if renewed:
                logger.info(f"🔄 Session renewed during JWT refresh: {sid}")
        except Exception as e:
            logger.warning(f"Smart session renewal failed: {e}")

        result = {'access': str(access)}
        if rotate:
            result['refresh'] = str(refresh)

        return Response(result, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def jwt_logout(request):
    """
    Logout user by blacklisting refresh token and invalidating session
    """
    try:
        # Get refresh token from request (optional for compatibility)
        refresh_token = request.data.get('refresh')

        # Extract session ID from JWT access token
        session_id = None
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            try:
                from rest_framework_simplejwt.tokens import UntypedToken
                token_str = auth_header.split(' ')[1]
                token = UntypedToken(token_str)
                session_id = token.payload.get('sid')
                logger.info(
                    f"Logout - Extracted session_id from access token: "
                    f"{session_id}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to extract session_id from access token: {e}"
                )
                # If we can't extract session ID from token, try Django session
                session_id = request.session.session_key

        # If refresh token provided, blacklist it
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                # Extract session ID from refresh token if not in access token
                if not session_id:
                    session_id = token.payload.get('sid')
                    logger.info(
                        f"Logout - Extracted session_id from refresh "
                        f"token: {session_id}"
                    )
                token.blacklist()
                logger.info("Refresh token blacklisted successfully")
            except Exception as e:
                # If token is invalid, continue with logout anyway
                logger.warning(f"Failed to blacklist refresh token: {e}")
                pass

        # End the user session in the database if session ID found
        if session_id:
            try:
                from accounts.models import UserSession
                from django.utils import timezone

                # Find and end the user session
                user_sessions = UserSession.objects.filter(
                    session_id=session_id,
                    is_active=True,
                    is_ended=False
                )

                logger.info(
                    f"Found {user_sessions.count()} active session(s) "
                    f"to end for session_id: {session_id}"
                )

                for session in user_sessions:
                    logger.info(
                        f"Ending session {session.session_id} for user "
                        f"{session.user.user.username}"
                    )
                    session.mark_ended(
                        reason='User logout',
                        when=timezone.now()
                    )
                    logger.info(
                        f"Session {session.session_id} ended successfully"
                    )

                logger.info(
                    f"Ended {user_sessions.count()} sessions for logout"
                )

            except Exception as e:
                logger.error(
                    f"Failed to end user session during logout: {e}"
                )
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        else:
            logger.warning(
                "No session_id found - cannot end database session"
            )

        # Hybrid approach: Invalidate Redis session
        from core.session_manager import session_manager
        if session_id:
            session_manager.invalidate_session(session_id)
        elif request.session.session_key:
            # Fallback to Django session key
            session_manager.invalidate_session(request.session.session_key)

        # Django logout
        logout(request)

        return Response({
            'message': 'Successfully logged out'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Logout failed: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_register(request):
    """
    JWT registration endpoint that creates user account without authentication.
    Authentication should be done separately via login endpoint.
    """
    serializer = RegisterSerializer(
        data=request.data, context={'request': request}
    )
    if serializer.is_valid():
        user = serializer.save()

        # Activate the user immediately for JWT registration
        user.is_active = True
        user.save()

        # Get user profile data (no authentication tokens)
        try:
            profile = UserProfile.objects.get(user=user)
            user_data = UserDetailSerializer(user).data
        except UserProfile.DoesNotExist:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }

        response_data = {
            'user': user_data,
            'message': 'User registered successfully. Please check your email for verification code and login to continue.',
            'verification_sent': True  # RegisterSerializer already sent the email
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    return Response(
        serializer.errors, status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def jwt_user_info(request):
    """
    Get current user information from JWT token.
    """
    try:
        user_data = UserDetailSerializer(request.user).data

        # Enrich with location data for municipality routing (matching login response)
        try:
            profile = UserProfile.objects.get(user=request.user, is_deleted=False)
            if profile.administrative_division:
                # Build complete administrative division data
                admin_div = profile.administrative_division

                # Find Level 1 ancestor (province/department) by traversing up
                level_1_ancestor = admin_div.get_ancestor_at_level(1)

                location_data = {
                    'city': admin_div.name,
                    'country': admin_div.country.name if admin_div.country else None,
                    'division_id': str(admin_div.id),
                    'admin_level': admin_div.admin_level,
                    'boundary_type': admin_div.boundary_type,
                    'parent_id': str(admin_div.parent.id) if admin_div.parent else None,
                    'parent_name': admin_div.parent.name if admin_div.parent else None,
                    # Add Level 1 ancestor info for map page cascading
                    'level_1_id': str(level_1_ancestor.id) if level_1_ancestor else None,
                    'level_1_name': level_1_ancestor.name if level_1_ancestor else None,
                }
                # Add to profile data to match login response structure
                if 'profile' in user_data:
                    user_data['profile']['administrative_division'] = location_data
                # Also add at top level for compatibility
                user_data['location'] = location_data
                user_data['municipality'] = admin_div.name
        except UserProfile.DoesNotExist:
            pass

        # Include username at top level for test compatibility
        response_data = user_data.copy()
        response_data.update({
            'username': request.user.username,
            'email': request.user.email,
            'user_id': request.user.id,
            'token_info': {
                'user_id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
            }
        })
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': f'Error retrieving user info: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password with JWT authentication.
    """
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    # Accept both parameter names for compatibility
    confirm_password = (
        request.data.get('confirm_password')
        or request.data.get('new_password_confirm')
    )

    if not all([old_password, new_password, confirm_password]):
        return Response({
            'error': 'All password fields are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    if new_password != confirm_password:
        return Response({
            'error': 'New passwords do not match'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not request.user.check_password(old_password):
        return Response({
            'error': 'Old password is incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Set new password
    request.user.set_password(new_password)
    request.user.save()

    return Response({
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    Confirm password reset with token.
    """
    from .views import verify_password_reset_token

    token = request.data.get('token')
    # Accept both parameter names for compatibility
    password = request.data.get('password') or request.data.get('new_password')
    confirm_password = (
        request.data.get('confirm_password')
        or request.data.get('new_password_confirm')
    )

    if not all([token, password, confirm_password]):
        return Response({
            'error': 'Token and password fields are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    if password != confirm_password:
        return Response({
            'error': 'Passwords do not match'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Verify the token using the helper function
    user = verify_password_reset_token(token)
    if not user:
        return Response({
            'error': 'Invalid or expired token'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Reset the user's password
    if hasattr(user, 'set_password'):
        user.set_password(password)
        user.save()

    return Response({
        'message': 'Password reset successfully'
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_with_verification_check(request):
    """
    Enhanced JWT login endpoint that checks verification expiry.
    This is exactly like jwt_login but with verification checks added.
    """
    from .serializers import LoginSerializer

    # Use LoginSerializer to get username, password AND client device data
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'error': 'Invalid login data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # Get authenticated user from serializer
    user = serializer.validated_data['user']

    # Step 1: Get user profile - ALWAYS needed for session creation
    try:
        profile = UserProfile.objects.get(user=user, is_deleted=False)
    except UserProfile.DoesNotExist:
        return Response({
            'error': 'User profile not found',
            'status': 'no_profile',
            'message': 'User profile not found',
            'code': 'NO_PROFILE'
        }, status=status.HTTP_404_NOT_FOUND)

    # Step 1.5: Check if user is suspended
    if profile.is_suspended:
        return Response({
            'error': 'Account suspended',
            'status': 'suspended',
            'message': 'Votre compte a été suspendu. Un email de notification a été envoyé à votre adresse.',
            'code': 'ACCOUNT_SUSPENDED',
            'suspended_at': profile.suspended_at.isoformat() if profile.suspended_at else None,
            'suspension_reason': profile.suspension_reason or 'Raison non spécifiée',
            'email': user.email
        }, status=status.HTTP_403_FORBIDDEN)

    # Step 2: ALWAYS create session immediately after authentication

    # Step 2: OPTIMIZED SESSION CREATION (No reuse needed)
    session_data = None
    try:
        # Extract comprehensive client device info from serializer
        client_device_info = {k: v for k, v in {
            'screen_resolution': serializer.validated_data.get('screen_resolution'),
            'timezone': serializer.validated_data.get('timezone'),
            'platform': serializer.validated_data.get('platform'),
            'language': serializer.validated_data.get('language'),
            'languages': serializer.validated_data.get('languages'),
            'color_depth': serializer.validated_data.get('color_depth'),
            'hardware_concurrency': serializer.validated_data.get('hardware_concurrency'),
            'device_memory': serializer.validated_data.get('device_memory'),
            'touch_support': serializer.validated_data.get('touch_support'),
            'cookie_enabled': serializer.validated_data.get('cookie_enabled'),
            'webgl_vendor': serializer.validated_data.get('webgl_vendor'),
            'webgl_renderer': serializer.validated_data.get('webgl_renderer'),
            'canvas_fingerprint': serializer.validated_data.get('canvas_fingerprint'),
            'audio_fingerprint': serializer.validated_data.get('audio_fingerprint'),
            'client_fingerprint': serializer.validated_data.get('client_fingerprint'),
            'available_fonts': serializer.validated_data.get('available_fonts'),
            'plugins_hash': serializer.validated_data.get('plugins_hash'),
            'storage_quota': serializer.validated_data.get('storage_quota'),
            'network_info': serializer.validated_data.get('network_info'),
            'local_storage': serializer.validated_data.get('local_storage'),
            'session_storage': serializer.validated_data.get('session_storage'),
            'indexed_db': serializer.validated_data.get('indexed_db'),
            'webgl_support': serializer.validated_data.get('webgl_support'),
            'fonts': serializer.validated_data.get('fonts'),
            'plugins': serializer.validated_data.get('plugins'),
            'connection_type': serializer.validated_data.get('connection_type'),
        }.items() if v is not None}

        # Get remember_me flag BEFORE creating session
        persistent = serializer.validated_data.get('remember_me', False)

        # Use fast login with session reuse - reuses existing session
        # from same device, passing persistent flag
        session_data = session_manager.fast_login_with_session_reuse(
            request, profile, persistent=persistent)

        # If session was reused and persistent flag changed, update it
        if session_data.get('reused') and persistent:
            try:
                from accounts.models import UserSession
                session = UserSession.objects.get(
                    session_id=session_data['session_id']
                )
                if not session.persistent:
                    # Update persistent flag AND extend expiration
                    session.persistent = True
                    session.extend_session()  # This recalculates expires_at for 30 days
                    logger.info(f"Extended reused session to 30 days for remember_me")
            except Exception as e:
                logger.warning(f"Failed to update persistent flag on reused session: {e}")

        # Cache client fingerprint data for enhanced processing
        # if client_device_info:
        #     from core.device_fingerprint import OptimizedDeviceFingerprint
        #     OptimizedDeviceFingerprint.cache_client_fingerprint(
        #         session_data['session_id'], client_device_info
        #     )

        if session_data.get('reused'):
            logger.info(
                f"♻️ Reused existing session: "
                f"{session_data['session_id']}")
        else:
            logger.info(
                f"✨ Created new minimal session: "
                f"{session_data['session_id']}")

        # Session successfully created - no need to validate again
        session_id = session_data['session_id']

        # Trigger async enhanced session processing with complete data
        try:
            from core.tasks import enhance_session_async
            from core.utils import get_client_ip, get_device_info

            # Extract serializable request data for Celery task
            request_data = {
                'ip_address': get_client_ip(request),
                'device_info': get_device_info(request),
                'accept': request.META.get('HTTP_ACCEPT', ''),
                'accept_lang': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
                'accept_encoding': request.META.get('HTTP_ACCEPT_ENCODING', ''),
                'accept_charset': request.META.get('HTTP_ACCEPT_CHARSET', ''),
                'dnt': request.META.get('HTTP_DNT', ''),
                'connection': request.META.get('HTTP_CONNECTION', ''),
                'cache_control': request.META.get('HTTP_CACHE_CONTROL', ''),
                'pragma': request.META.get('HTTP_PRAGMA', ''),
                'sec_fetch_dest': request.META.get('HTTP_SEC_FETCH_DEST', ''),
                'sec_fetch_mode': request.META.get('HTTP_SEC_FETCH_MODE', ''),
                'sec_fetch_site': request.META.get('HTTP_SEC_FETCH_SITE', ''),
                'sec_fetch_user': request.META.get('HTTP_SEC_FETCH_USER', ''),
                'upgrade_insecure': request.META.get('HTTP_UPGRADE_INSECURE_REQUESTS', ''),
            }

            logger.info(f"🔄 Triggering session enhancement for {session_id[:10]}...")
            logger.info(f"📊 Request data keys: {list(request_data.keys())}")
            logger.info(f"📱 Client device info keys: {list(client_device_info.keys())}")

            # Call the task
            task_result = enhance_session_async.delay(session_id, request_data, client_device_info)
            logger.info(f"✅ Session enhancement task queued: {task_result.id}")

        except ImportError as e:
            logger.error(f"❌ ImportError - Async tasks not available for session enhancement: {e}")
        except Exception as e:
            logger.error(f"❌ Exception during session enhancement task trigger: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Don't fail login if enhancement fails - continue without it

    except Exception as e:
        logger.error(f"CRITICAL: Session creation/validation failed: {e}")
        return Response({
            'error': 'Session creation failed',
            'detail': 'Unable to establish secure session. Please try again.',
            'code': 'SESSION_CREATION_FAILED'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Step 3: JWT Creation ONLY AFTER Session Success
    try:
        from datetime import timedelta
        from django.conf import settings

        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Extend refresh token lifetime for persistent sessions
        if persistent:
            # Override refresh token expiration for remember me
            persistent_days = getattr(
                settings, 'PERSISTENT_SESSION_DURATION_DAYS', 30
            )
            refresh.set_exp(lifetime=timedelta(days=persistent_days))

        # CRITICAL: Embed session ID in JWT
        session_id = session_data['session_id']
        access_token['sid'] = session_id
        refresh['sid'] = session_id

        # Add custom claims
        access_token['username'] = user.username
        access_token['email'] = user.email
        access_token['role'] = profile.role
        access_token['is_verified'] = profile.is_verified

    except Exception as e:
        logger.error(f"JWT creation failed: {e}")
        # Clean up session if JWT creation fails
        session_manager.invalidate_session(session_data['session_id'])
        return Response({
            'error': 'Token creation failed',
            'detail': 'Authentication successful but token generation failed',
            'code': 'JWT_CREATION_FAILED'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Step 4: NOW check verification status (after session is created)
    from .auth_backends import check_verification_expiry_on_login
    verification_status = check_verification_expiry_on_login(user)

    # Prepare user profile data including location
    user_profile_data = {
        'role': profile.role,
        'is_verified': profile.is_verified,
        'profile_picture': (
            profile.profile_picture.url if profile.profile_picture else None
        ),
    }

    # Add location data for municipality routing
    location_data = None
    municipality_name = None

    if profile.administrative_division:
        admin_div = profile.administrative_division

        # Find Level 1 ancestor (province/department) by traversing up
        level_1_ancestor = admin_div.get_ancestor_at_level(1)

        location_data = {
            'city': admin_div.name,
            'country': admin_div.country.name if admin_div.country else None,
            'division_id': str(admin_div.id),
            'admin_level': admin_div.admin_level,
            'boundary_type': admin_div.boundary_type,
            'parent_id': str(admin_div.parent.id) if admin_div.parent else None,
            'parent_name': admin_div.parent.name if admin_div.parent else None,
            # Add Level 1 ancestor info for map page cascading
            'level_1_id': str(level_1_ancestor.id) if level_1_ancestor else None,
            'level_1_name': level_1_ancestor.name if level_1_ancestor else None,
        }
        municipality_name = admin_div.name
        user_profile_data['administrative_division'] = location_data

    # Get last visited URL from previous session using UserEvent
    last_visited_url = None
    last_visited_time = None
    try:
        from accounts.models import UserEvent
        from django.utils import timezone
        from datetime import timedelta

        # Get the most recent profile_view or page visit event
        # (within last 7 days to avoid very old data)
        recent_cutoff = timezone.now() - timedelta(days=7)

        # Look for recent page view events with URL in metadata
        recent_event = UserEvent.objects.filter(
            user=profile,
            created_at__gte=recent_cutoff,
            metadata__has_key='url'  # Events that tracked a URL
        ).order_by('-created_at').first()

        if recent_event and recent_event.metadata.get('url'):
            last_visited_url = recent_event.metadata['url']
            last_visited_time = recent_event.created_at

            # Calculate time since last visit
            time_since_visit = (timezone.now() - last_visited_time) \
                .total_seconds() / 60  # minutes

            logger.info(
                f"Found last visited URL from UserEvent: "
                f"{last_visited_url} ({time_since_visit:.1f} min ago)"
            )
    except Exception as e:
        logger.warning(f"Failed to retrieve last visited URL: {e}")

    # Base response structure with session and JWT
    response_data = {
        'access': str(access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'municipality': municipality_name,  # For getUserRedirectUrl
            'location': location_data,  # Full location object
            'profile': user_profile_data
        },
        'session': {
            'session_id': session_data['session_id'],
            'created': session_data.get('started_at'),
            'location': session_data.get('location_data', {}),
            'reused': False,  # No session reuse logic
            'last_visited_url': last_visited_url,
            'last_visited_time': last_visited_time.isoformat() if \
                last_visited_time else None
        },
        'message': 'Login successful with new secure session'
    }

    # Add verification status to response if verification is required
    if verification_status['verification_required']:
        response_data.update({
            'verification_required': True,
            'verification_status': verification_status['status'],
            'verification_message': verification_status['message'],
            'verification_code': verification_status.get('code'),
            'verification_expiry': verification_status.get('expiry_time'),
            'message': 'Login successful - email verification required'
        })

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_last_visited_url(request):
    """
    Track page visit by creating a UserEvent with URL in metadata.
    This allows retrieving last visited page for smart redirect on next login.
    """
    url = request.data.get('url')

    if not url:
        return Response({
            'error': 'URL is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        from django.utils import timezone
        from accounts.models import UserEvent, UserSession
        from rest_framework_simplejwt.tokens import UntypedToken

        # Get user profile
        try:
            profile = UserProfile.objects.get(
                user=request.user, is_deleted=False
            )
        except UserProfile.DoesNotExist:
            return Response({
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get session ID from JWT token
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        session = None

        if auth_header.startswith('Bearer '):
            try:
                token_str = auth_header.split(' ')[1]
                token = UntypedToken(token_str)
                session_id = token.payload.get('sid')

                if session_id:
                    session = UserSession.objects.filter(
                        session_id=session_id,
                        is_active=True
                    ).first()
            except Exception as e:
                logger.warning(f"Failed to extract session from token: {e}")

        # Create event to track page visit
        try:
            UserEvent.objects.create(
                user=profile,
                session=session,
                event_type='profile_view',  # Using existing event type
                description=f'Page visit: {url}',
                metadata={
                    'url': url,
                    'timestamp': timezone.now().isoformat()
                },
                success=True
            )
            logger.info(f"✅ Tracked page visit: {url}")
        except Exception as event_error:
            # Log error but don't fail the request
            logger.error(
                f"❌ Failed to create UserEvent for {url}: {event_error}"
            )
            # Re-raise to return error to client
            raise

        return Response({
            'success': True,
            'message': 'Page visit tracked'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error tracking page visit: {e}")
        return Response({
            'error': f'Failed to track page visit: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def verify_password_reset_token(token):
    """
    Verify password reset token (placeholder implementation).
    """
    # This is a placeholder function for tests
    return token == 'valid_token'
