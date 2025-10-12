"""Views for the communities app."""

import logging
from django.db import models
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from accounts.models import UserProfile
from accounts.permissions import NotDeletedUserPermission
from .models import (
    Community, CommunityMembership, Thread,
    # CommunityInvitation, CommunityJoinRequest,  # Commented out - not needed for public communities
    CommunityRole, CommunityModeration, CommunityAnnouncement
)

logger = logging.getLogger(__name__)
from .serializers import (
    CommunitySerializer, CommunityCreateUpdateSerializer,
    CommunityMembershipSerializer, CommunityModerationSerializer,
    # CommunityInvitationSerializer,  # Commented - public communities
    CommunityRoleSerializer,
    # CommunityJoinRequestSerializer,  # Commented - public communities
    CommunityAnnouncementSerializer,
    ThreadSerializer
)


from django.urls import reverse
from django.contrib.auth.decorators import login_required


# CRUD ViewSet for CommunityJoinRequest
# # Commented out - Public communities don't use join requests
# class CommunityJoinRequestViewSet(viewsets.ModelViewSet):
#     """ViewSet for managing community join requests."""
#     serializer_class = CommunityJoinRequestSerializer
#     permission_classes = [IsAuthenticated, NotDeletedUserPermission]

#     def get_queryset(self):
#         """Return join requests for the authenticated user or all if admin."""
#         user = self.request.user
#         profile = get_object_or_404(UserProfile, user=user)
#         # Admins see all, others see their own
#         if user.is_superuser:
#             return CommunityJoinRequest.objects.filter(is_deleted=False)
#         return CommunityJoinRequest.objects.filter(user=profile, is_deleted=False)

#     def perform_create(self, serializer):
#         profile = get_object_or_404(UserProfile, user=self.request.user)
#         serializer.save(user=profile)

#     def perform_destroy(self, instance):
#         from django.utils import timezone
#         instance.is_deleted = True
#         instance.deleted_at = timezone.now()
#         instance.save()

#     def perform_update(self, serializer):
#         # If status is changed to approved/rejected, set reviewed_by and reviewed_at
#         instance = serializer.save()
#         if 'status' in serializer.validated_data and serializer.validated_data['status'] in ['approved', 'rejected']:
#             instance.reviewed_by = get_object_or_404(UserProfile, user=self.request.user)
#             from django.utils import timezone
#             instance.reviewed_at = timezone.now()
#             instance.save()


class CommunityViewSet(viewsets.ModelViewSet):
    """ViewSet for managing communities."""
    serializer_class = CommunitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'slug'

    def get_queryset(self):
        """Get queryset with optimized data loading, excluding soft-deleted.

        Query params:
        - division_id: Filter communities by division UUID (optional)
        """
        queryset = Community.objects.filter(
            is_deleted=False
        ).select_related(
            'creator__user', 'division'
        ).annotate(
            membership_count=Count(
                'memberships',
                filter=Q(
                    memberships__status='active',
                    memberships__is_deleted=False
                )
            )
        )

        # Filter by division if provided
        division_id = self.request.query_params.get('division_id')
        if division_id:
            queryset = queryset.filter(division_id=division_id)

        return queryset.order_by('-created_at')

    def perform_destroy(self, instance):
        """Soft delete a community."""
        from django.utils import timezone
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action in ['create', 'update', 'partial_update']:
            return CommunityCreateUpdateSerializer
        return CommunitySerializer

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a community""" # with geo-restriction check."""
        instance = self.get_object()

        # Check geo-restrictions for authenticated users
        # if request.user.is_authenticated and instance.is_geo_restricted:
        #     try:
        #         user_profile = UserProfile.objects.get(user=request.user)

        #         # Get current location from session data (for travelers)
        #         current_country = None
        #         current_city = None

        #         # Get location directly from session data instead of middleware
        #         try:
        #             from core.session_manager import session_manager
        #             session_data = session_manager.get_session(request.session.session_key)
        #             if session_data and session_data.get('location_data'):
        #                 location_data = session_data['location_data']
        #                 logger.info(f"Session location data found: {location_data}")

        #                 # Try to resolve country and city from session data
        #                 if location_data.get('country_id'):
        #                     try:
        #                         from core.models import Country
        #                         current_country = Country.objects.get(id=location_data['country_id'])
        #                         logger.info(f"Current country resolved: {current_country.name}")
        #                     except Country.DoesNotExist:
        #                         logger.warning(f"Country with ID {location_data.get('country_id')} not found")

        #                 if location_data.get('city_id'):
        #                     try:
        #                         from core.models import City
        #                         current_city = City.objects.get(id=location_data['city_id'])
        #                         logger.info(f"Current city resolved: {current_city.name}")
        #                     except City.DoesNotExist:
        #                         logger.warning(f"City with ID {location_data.get('city_id')} not found")

        #                 # Store raw location data for fallback use
        #                 raw_location_data = {
        #                     'country': location_data.get('country_code') or
        #                               (current_country.name if current_country else None),
        #                     'city': location_data.get('city_name') or
        #                            (current_city.name if current_city else None)
        #                 }
        #             else:
        #                 logger.warning("No session data or location_data found")
        #                 raw_location_data = {}
        #         except Exception as e:
        #             logger.warning(f"Failed to get location from session: {e}")
        #             raw_location_data = {}

        #         logger.info(f"Final location: current_country={current_country}, current_city={current_city}")
        #         logger.info(f"User registration: {user_profile.country}, {user_profile.city}")

        #         # Priority 1: Check if user is an active member (bypass geo-restrictions)
        #         is_active_member = CommunityMembership.objects.filter(
        #             community=instance,
        #             user=user_profile,
        #             status='active',
        #             is_deleted=False
        #         ).exists()

        #         if is_active_member:
        #             logger.info(
        #                 f"User {user_profile.user.username} is active member of "
        #                 f"{instance.name}, bypassing geo-restrictions"
        #             )
        #             can_access = True
        #             error_message = None
        #         else:
        #             # Apply geo-restriction logic for non-members
        #             can_access, _, error_message = (
        #                 instance.can_user_access_geographically(
        #                     user_profile, current_country, current_city
        #                 )
        #             )

        #         if not can_access:
        #             # Build location_info dict to match middleware pattern
        #             location_info = {
        #                 'profile_country': (user_profile.country
        #                                   if user_profile.country else None),
        #                 'profile_city': (user_profile.city
        #                                if hasattr(user_profile, 'city')
        #                                else None),
        #                 'current_country': current_country,
        #                 'current_city': current_city
        #             }

        #             # Create notification about geo-restriction (with duplicate prevention)
        #             from notifications.utils import CommunityNotifications
        #             from notifications.models import Notification
        #             from django.db import transaction
        #             from django.utils import timezone
        #             from datetime import timedelta

        #             def create_notification():
        #                 try:
        #                     # Check if notification was already sent recently (last 5 minutes)
        #                     recent_cutoff = timezone.now() - timedelta(minutes=5)
        #                     existing_notification = Notification.objects.filter(
        #                         recipient=user_profile,
        #                         notification_type='geo_restriction',
        #                         extra_data__community_id=str(instance.id),
        #                         created_at__gte=recent_cutoff
        #                     ).exists()

        #                     if existing_notification:
        #                         logger.info("Skipping duplicate geo-restriction notification for user %s, community %s",
        #                                   user_profile.user.username, instance.name)
        #                         return

        #                     # Build user location string
        #                     profile_country = location_info.get('profile_country')
        #                     profile_city = location_info.get('profile_city')
        #                     current_country = location_info.get('current_country')
        #                     current_city = location_info.get('current_city')

        #                     # Determine primary location for display
        #                     if profile_country:
        #                         if profile_city:
        #                             user_location = f"{profile_city.name}, {profile_country.name}"
        #                         else:
        #                             user_location = profile_country.name
        #                     elif current_country:
        #                         if current_city:
        #                             user_location = f"{current_city.name}, {current_country.name}"
        #                         else:
        #                             user_location = current_country.name
        #                     else:
        #                         user_location = "Unknown location"

        #                     # Check if user is traveling
        #                     is_traveling = (current_country and profile_country and
        #                                   current_country != profile_country)

        #                     if is_traveling:
        #                         current_loc = (f"{current_city.name}, {current_country.name}"
        #                                      if current_city else current_country.name)
        #                         profile_loc = (f"{profile_city.name}, {profile_country.name}"
        #                                      if profile_city else profile_country.name)
        #                         user_location = f"{current_loc} (registered from {profile_loc})"

        #                     CommunityNotifications.geo_restriction_notification(
        #                         user=user_profile,
        #                         community=instance,
        #                         restriction_type='location',
        #                         user_location=user_location,
        #                         is_traveling=is_traveling,
        #                         restriction_message=error_message,
        #                         send_email=True
        #                     )
        #                 except Exception as e:
        #                     logger.error(f"Failed to create geo-restriction notification: {e}")

        #             # Schedule notification creation after transaction
        #             transaction.on_commit(create_notification)

        #             # Build more detailed location info for response
        #             current_location_str = 'Unknown'

        #             # First try database objects (current_city, current_country)
        #             if current_city and current_country:
        #                 current_location_str = f"{current_city.name}, {current_country.name}"
        #             elif current_country:
        #                 current_location_str = current_country.name
        #             # Use raw location data from session if database objects unavailable
        #             elif 'raw_location_data' in locals() and raw_location_data:
        #                 city = raw_location_data.get('city')
        #                 country = raw_location_data.get('country')
        #                 if city and country:
        #                     current_location_str = f"{city}, {country}"
        #                 elif country:
        #                     current_location_str = country
        #             else:
        #                 # Final fallback to IP lookup or user profile
        #                 try:
        #                     from core.utils import (
        #                         get_client_ip, get_location_from_ip
        #                     )
        #                     ip_address = get_client_ip(request)
        #                     if ip_address:
        #                         raw_location = get_location_from_ip(ip_address)
        #                         city = raw_location.get('city')
        #                         country = raw_location.get('country')
        #                         if city and country:
        #                             current_location_str = f"{city}, {country}"
        #                         elif country:
        #                             current_location_str = country
        #                 except Exception as e:
        #                     logger.warning(f"Failed to get raw location data: {e}")

        #                 # Final fallback to user profile if everything else fails
        #                 if current_location_str == 'Unknown':
        #                     if user_profile.city and user_profile.country:
        #                         city_name = user_profile.city.name
        #                         country_name = user_profile.country.name
        #                         current_location_str = f"{city_name}, {country_name}"
        #                     elif user_profile.country:
        #                         current_location_str = user_profile.country.name

        #             profile_location_str = 'Not set'
        #             if user_profile.city and user_profile.country:
        #                 profile_location_str = (f"{user_profile.city.name}, "
        #                                       f"{user_profile.country.name}")
        #             elif user_profile.country:
        #                 profile_location_str = user_profile.country.name

        #             user_traveling = (current_country and
        #                             current_country != user_profile.country
        #                             if user_profile.country else False)

        #             return Response({
        #                 'error': 'geo_restricted',
        #                 'message': error_message,
        #                 'community_name': instance.name,
        #                 'user_traveling': user_traveling,
        #                 'current_location': current_location_str,
        #                 'profile_location': profile_location_str,
        #                 'actions': [
        #                     'Update your profile location',
        #                     'Browse other communities',
        #                     'Contact support if you believe this is an error'
        #                 ]
        #             }, status=status.HTTP_403_FORBIDDEN)

        #     except UserProfile.DoesNotExist:
        #         pass  # User has no profile, skip geo-check

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Create community with current user as creator and handle setup."""
        from django.db import transaction

        profile = get_object_or_404(UserProfile, user=self.request.user)

        # Use transaction to ensure all related objects are created atomically
        with transaction.atomic():
            # ============================================================================
            # PHASE 1: COMMUNITY CREATION
            # ============================================================================
            # The serializer handles all field processing:
            # - Basic community creation (name, description, community_type)
            # - Geo-restrictions (countries, cities, timezones) Removed for now
            # - Media uploads (cover_media, avatar)
            # - Tags and rules processing
            # - Moderator assignments
            # - Welcome message creation
            community = serializer.save(creator=profile)

            logger.info(
                "Phase 1 Complete: Community '%s' created with slug '%s'",
                community.name, community.slug
            )

            # ============================================================================
            # PHASE 2: COMMUNITY ROLES CREATION
            # ============================================================================
            # Create default member role for the community
            default_role = None
            moderator_role = None
            admin_role = None
            creator_role = None

            try:
                # Create default member role
                default_role, created = CommunityRole.objects.get_or_create(
                    community=community,
                    name='Member',
                    defaults={
                        'permissions': {
                            'can_post': True,
                            'can_comment': True,
                            'can_vote': True,
                            'can_report': True,
                            'can_moderate': False,
                            'can_manage_members': False,
                            'can_manage_community': False
                        },
                        'color': '#6b7280',  # Gray color for members
                        'is_default': True
                    }
                )

                # Create moderator role
                moderator_role, created = CommunityRole.objects.get_or_create(
                    community=community,
                    name='Moderator',
                    defaults={
                        'permissions': {
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
                        'color': '#2563eb',  # Blue color for moderators
                        'is_default': False
                    }
                )

                # Create admin role
                admin_role, created = CommunityRole.objects.get_or_create(
                    community=community,
                    name='Admin',
                    defaults={
                        'permissions': {
                            'can_post': True,
                            'can_comment': True,
                            'can_vote': True,
                            'can_report': True,
                            'can_moderate': True,
                            'can_manage_members': True,
                            'can_manage_community': True,
                            'can_delete_posts': True,
                            'can_ban_users': True,
                            'can_manage_roles': True
                        },
                        'color': '#dc2626',  # Red color for admins
                        'is_default': False
                    }
                )

                # Create creator role (has all admin permissions plus can delete community)
                creator_role, created = CommunityRole.objects.get_or_create(
                    community=community,
                    name='Creator',
                    defaults={
                        'permissions': {
                            'can_post': True,
                            'can_comment': True,
                            'can_vote': True,
                            'can_report': True,
                            'can_moderate': True,
                            'can_manage_members': True,
                            'can_manage_community': True,
                            'can_delete_posts': True,
                            'can_ban_users': True,
                            'can_manage_roles': True,
                            'can_delete_community': True
                        },
                        'color': '#7c2d12',  # Dark orange/brown color for creators
                        'is_default': False
                    }
                )

                logger.info(
                    "Phase 2 Complete: Created roles for community '%s' "
                    "(Member, Moderator, Admin, Creator)", community.name
                )

            except Exception as role_error:
                logger.error(
                    "Phase 2 Failed: Could not create community roles "
                    "for '%s': %s", community.name, role_error
                )
                # Use fallback - try to get existing roles or use None
                try:
                    default_role = CommunityRole.objects.filter(
                        community=community, name='Member'
                    ).first()
                    moderator_role = CommunityRole.objects.filter(
                        community=community, name='Moderator'
                    ).first()
                    admin_role = CommunityRole.objects.filter(
                        community=community, name='Admin'
                    ).first()
                    creator_role = CommunityRole.objects.filter(
                        community=community, name='Creator'
                    ).first()
                except Exception:
                    default_role = None
                    moderator_role = None
                    admin_role = None
                    creator_role = None

            # ============================================================================
            # PHASE 3: CREATOR MEMBERSHIP
            # ============================================================================
            # Add creator as creator member (with highest privileges)
            try:
                sid = transaction.savepoint()
                try:
                    # Assign creator to Creator role, fallback to Admin/Member
                    assigned_role = (creator_role if creator_role else
                                     admin_role if admin_role else
                                     default_role)

                    CommunityMembership.objects.create(
                        community=community,
                        user=profile,
                        role=assigned_role,
                        status='active'
                    )
                    transaction.savepoint_commit(sid)
                    logger.info(
                        "Phase 3 Complete: Added creator '%s' as creator to "
                        "community '%s'", profile.user.username, community.name
                    )
                except Exception:
                    transaction.savepoint_rollback(sid)
                    raise
            except Exception as creator_error:
                logger.error(
                    "Phase 3 Failed: Could not add creator membership "
                    "for '%s': %s", community.name, creator_error
                )

            # ============================================================================
            # PHASE 4: ANALYTICS INITIALIZATION
            # ============================================================================
            # Initialize community analytics
            try:
                # Update member count to include creator and moderators
                member_count = CommunityMembership.objects.filter(
                    community=community,
                    status='active'
                ).count()

                community.members_count = member_count
                community.save(update_fields=['members_count'])

                logger.info(
                    "Phase 4 Complete: Initialized analytics for "
                    "community '%s' (members_count=%d)",
                    community.name, member_count
                )

            except Exception as analytics_error:
                logger.error(
                    "Phase 4 Failed: Could not initialize analytics "
                    "for '%s': %s", community.name, analytics_error
                )

            # ============================================================================
            # PHASE 5: NOTIFICATION SYSTEM
            # ============================================================================
            # Send notifications to assigned moderators (if any were created)
            try:
                # Note: Moderator notifications are now handled by the signal system
                # communities.signals.handle_community_membership_created
                # This prevents duplicate notifications
                logger.info(
                    "Phase 5 Complete: Moderator assignment handled by "
                    "serializer, notifications handled by signals for '%s'",
                    community.name
                )

            except Exception as notification_error:
                logger.error(
                    "Phase 5 Failed: Notification processing error "
                    "for '%s': %s", community.name, notification_error
                )

            # ============================================================================
            # COMMUNITY CREATION COMPLETE
            # ============================================================================
            logger.info(
                "🎉 Community creation process completed successfully "
                "for '%s' (ID: %s, slug: %s)",
                community.name, community.id, community.slug
            )

    def create(self, request, *args, **kwargs):
        """Override create to return the full read serializer (includes generated slug).

        The default implementation returns the input-bound serializer.data which may
        not always include server-generated read-only fields in a predictable way.
        By returning `CommunitySerializer` we ensure the client receives the
        authoritative state of the created instance (including the slug).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # perform_create will save the instance and create membership
        self.perform_create(serializer)
        instance = serializer.instance

        read_serializer = CommunitySerializer(instance, context={'request': request})
        headers = self.get_success_headers(serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def join(self, request, slug=None):
        """Join a community."""
        community = self.get_object()
        profile = get_object_or_404(UserProfile, user=request.user)

        # Check if already a member
        membership = CommunityMembership.objects.filter(
            community=community,
            user=profile
        ).first()

        if membership:
            if membership.status == 'active':
                return Response(
                    {'detail': 'Already a member of this community.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Reactivate membership
                membership.status = 'active'
                membership.save()
                return Response({'detail': 'Rejoined community successfully.'})

        # Create new membership
        default_role = community.roles.filter(is_default=True).first()
        CommunityMembership.objects.create(
            community=community,
            user=profile,
            role=default_role
        )

        return Response({'detail': 'Joined community successfully.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def leave(self, request, slug=None):
        """Leave a community."""
        community = self.get_object()
        profile = get_object_or_404(UserProfile, user=request.user)

        membership = CommunityMembership.objects.filter(
            community=community,
            user=profile,
            status='active'
        ).first()

        if not membership:
            return Response(
                {'detail': 'Not a member of this community.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user is the creator
        if community.creator == profile:
            return Response(
                {'detail': 'Creator cannot leave the community.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        membership.status = 'left'
        membership.save()

        return Response({'detail': 'Left community successfully.'})

    @action(detail=True, methods=['get'])
    def members(self, request, slug=None):
        """Get community members."""
        community = self.get_object()
        memberships = community.memberships.filter(status='active')
        serializer = CommunityMembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def posts(self, request, slug=None):
        """Get community posts."""
        from content.serializers import PostSerializer
        community = self.get_object()
        posts = community.posts.filter(is_active=True).order_by('-created_at')
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def online_members(self, request, slug=None):
        """Get real-time online member count for a community."""
        community = self.get_object()

        # Track user activity if authenticated
        if request.user.is_authenticated:
            try:
                from .services import community_redis_service
                user_profile = UserProfile.objects.get(user=request.user)

                # Update user activity in this community
                community_redis_service.track_user_activity(
                    str(community.id), str(user_profile.id)
                )

                # Get online member data
                online_count = community_redis_service.get_online_member_count(
                    str(community.id)
                )
                online_members = community_redis_service.get_online_members(
                    str(community.id)
                )

                # Get peak counts for additional context
                stats = community_redis_service.get_multiple_community_stats([
                    str(community.id)
                ])
                community_stats = stats.get(str(community.id), {})

                return Response({
                    'community_id': community.id,
                    'community_name': community.name,
                    'online_count': online_count,
                    'online_members': list(online_members),
                    'peak_counts': community_stats.get('peak_counts', {}),
                    'is_user_online': community_redis_service.is_user_online_in_community(
                        str(community.id), str(user_profile.id)
                    ),
                    'timestamp': timezone.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Error getting online members: {e}")
                # Fallback response
                return Response({
                    'community_id': community.id,
                    'community_name': community.name,
                    'online_count': 0,
                    'online_members': [],
                    'peak_counts': {},
                    'is_user_online': False,
                    'timestamp': timezone.now().isoformat(),
                    'error': 'Unable to fetch real-time data'
                })

        else:
            # For anonymous users, provide basic info without tracking
            try:
                from .services import community_redis_service
                online_count = community_redis_service.get_online_member_count(
                    str(community.id)
                )

                return Response({
                    'community_id': community.id,
                    'community_name': community.name,
                    'online_count': online_count,
                    'is_user_online': False,
                    'timestamp': timezone.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting online count for anonymous user: {e}")
                return Response({
                    'community_id': community.id,
                    'community_name': community.name,
                    'online_count': 0,
                    'is_user_online': False,
                    'timestamp': timezone.now().isoformat()
                })

    @action(detail=False, methods=['get'])
    def bulk_online_stats(self, request):
        """Get online statistics for multiple communities efficiently."""
        community_ids = request.query_params.get('ids', '').split(',')
        community_ids = [cid.strip() for cid in community_ids if cid.strip()]

        if not community_ids:
            return Response({
                'error': 'No community IDs provided. Use ?ids=1,2,3 format.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Limit to reasonable number of communities
        if len(community_ids) > 50:
            return Response({
                'error': 'Too many community IDs. Maximum 50 allowed.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            from .services import community_redis_service

            # Get stats for all requested communities
            stats = community_redis_service.get_multiple_community_stats(
                community_ids
            )

            # Get community names for context
            communities = Community.objects.filter(
                id__in=community_ids, is_deleted=False
            ).values('id', 'name', 'slug')

            community_data = {str(c['id']): c for c in communities}

            # Combine stats with community info
            response_data = {}
            for community_id, stat_data in stats.items():
                community_info = community_data.get(community_id, {})
                response_data[community_id] = {
                    'community_id': community_id,
                    'name': community_info.get('name', 'Unknown'),
                    'slug': community_info.get('slug', ''),
                    'online_count': stat_data.get('online_count', 0),
                    'peak_counts': stat_data.get('peak_counts', {}),
                    'is_active': stat_data.get('is_active', False)
                }

            return Response({
                'communities': response_data,
                'timestamp': timezone.now().isoformat(),
                'total_requested': len(community_ids),
                'total_found': len(response_data)
            })

        except Exception as e:
            logger.error(f"Error getting bulk online stats: {e}")
            return Response({
                'error': 'Unable to fetch online statistics',
                'communities': {},
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ThreadViewSet(viewsets.ModelViewSet):
    """ViewSet for managing discussion threads within communities."""
    serializer_class = ThreadSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        """Get queryset filtered by community if specified.

        Query params:
        - community_id: Filter threads by community UUID (optional)
        - community_slug: Filter threads by community slug (optional)
        """
        from .models import Thread

        queryset = Thread.objects.filter(
            is_deleted=False
        ).select_related(
            'creator__user', 'community'
        ).order_by('-is_pinned', '-created_at')

        # Filter by community if provided
        community_id = self.request.query_params.get('community_id')
        community_slug = self.request.query_params.get('community_slug')

        if community_id:
            queryset = queryset.filter(community_id=community_id)
        elif community_slug:
            queryset = queryset.filter(community__slug=community_slug)

        return queryset

    def perform_create(self, serializer):
        """Create thread with current user as creator."""
        profile = get_object_or_404(UserProfile, user=self.request.user)
        serializer.save(creator=profile)

    def perform_destroy(self, instance):
        """Soft delete a thread."""
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()


class CommunityMembershipViewSet(viewsets.ModelViewSet):
    """ViewSet for managing community memberships."""
    serializer_class = CommunityMembershipSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def get_queryset(self):
        """Get user's memberships, excluding soft-deleted."""
        profile = get_object_or_404(UserProfile, user=self.request.user)
        return CommunityMembership.objects.filter(
            user=profile,
            status='active',
            is_deleted=False
        ).select_related('community', 'role', 'user__user')

    def perform_destroy(self, instance):
        """Soft delete a membership."""
        from django.utils import timezone
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()


class CommunityRoleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing community roles."""
    serializer_class = CommunityRoleSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def get_queryset(self):
        """Get roles for communities where user can manage, excluding soft-deleted."""
        profile = get_object_or_404(UserProfile, user=self.request.user)
        managed_communities = Community.objects.filter(
            Q(creator=profile) |
            Q(memberships__user=profile,
              memberships__role__permissions__can_manage_members=True),
            is_deleted=False
        )
        return CommunityRole.objects.filter(
            community__in=managed_communities,
            is_deleted=False
        ).select_related('community')

    def perform_destroy(self, instance):
        """Soft delete a role."""
        from django.utils import timezone
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

    def perform_create(self, serializer):
        """Ensure user can create roles for the community."""
        profile = get_object_or_404(UserProfile, user=self.request.user)
        community = serializer.validated_data['community']

        # Check if user can manage this community
        can_manage = Community.objects.filter(
            Q(id=community.id) & (
                Q(creator=profile) |
                Q(memberships__user=profile,
                  memberships__role__permissions__can_manage_members=True)
            )
        ).exists()

        if not can_manage:
            raise PermissionDenied("You don't have permission to create roles in this community.")

        serializer.save()

    @action(detail=False, methods=['post'],
            url_path='process-moderator-nomination')
    def process_moderator_nomination(self, request):
        """Process moderator nomination (called from frontend)."""
        membership_id = request.data.get('membership_id')
        action = request.data.get('action')  # 'accept' or 'decline'

        if not membership_id or action not in ['accept', 'decline']:
            return Response(
                {'error': 'membership_id and valid action (accept/decline) required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            membership = CommunityMembership.objects.get(id=membership_id)
        except CommunityMembership.DoesNotExist:
            return Response(
                {'error': 'Membership not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Ensure the authenticated user matches the membership user
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if membership.user != profile:
            return Response(
                {'error': 'You can only process your own moderator nominations'},
                status=status.HTTP_403_FORBIDDEN
            )

        if action == 'accept':
            # Assign moderator role
            moderator_role, _ = CommunityRole.objects.get_or_create(
                community=membership.community,
                name='Moderator',
                defaults={
                    'permissions': {
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
                    'color': '#2563eb',
                    'is_default': False
                }
            )

            membership.role = moderator_role
            membership.save()

            return Response({
                'message': 'Moderator nomination accepted successfully',
                'community': membership.community.name,
                'role': 'Moderator',
                'action': 'accepted'
            }, status=status.HTTP_200_OK)

        else:  # decline
            # Set role back to member if available
            try:
                member_role = CommunityRole.objects.get(
                    community=membership.community,
                    name='Member'
                )
                membership.role = member_role
                membership.save()
            except CommunityRole.DoesNotExist:
                # If no member role exists, try default role
                default_role = CommunityRole.objects.filter(
                    community=membership.community,
                    is_default=True
                ).first()
                if default_role:
                    membership.role = default_role
                    membership.save()

            return Response({
                'message': 'Moderator nomination declined',
                'community': membership.community.name,
                'role': membership.role.name if membership.role else 'Member',
                'action': 'declined'
            }, status=status.HTTP_200_OK)


class CommunityModerationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing community moderation actions."""
    serializer_class = CommunityModerationSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def get_queryset(self):
        """Get moderation actions for communities user can moderate, excluding soft-deleted."""
        profile = get_object_or_404(UserProfile, user=self.request.user)
        moderated_communities = Community.objects.filter(
            Q(creator=profile) |
            Q(memberships__user=profile,
              memberships__role__permissions__can_moderate=True),
            is_deleted=False
        )
        return CommunityModeration.objects.filter(
            community__in=moderated_communities,
            is_deleted=False
        ).select_related('community', 'moderator', 'target')

    def perform_destroy(self, instance):
        """Soft delete a moderation action."""
        from django.utils import timezone
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

    def perform_create(self, serializer):
        """Create moderation action with current user as moderator."""
        profile = get_object_or_404(UserProfile, user=self.request.user)
        serializer.save(moderator=profile)


# # Commented out - Public communities don't use invitations
# class CommunityInvitationViewSet(viewsets.ModelViewSet):
#     """ViewSet for managing community invitations."""
#     serializer_class = CommunityInvitationSerializer
#     permission_classes = [IsAuthenticated, NotDeletedUserPermission]

#     def get_queryset(self):
#         """Get user's invitations, excluding soft-deleted."""
#         profile = get_object_or_404(UserProfile, user=self.request.user)
#         return CommunityInvitation.objects.filter(
#             (models.Q(inviter=profile) | models.Q(invitee=profile)),
#             is_deleted=False
#         ).select_related('community', 'inviter', 'invitee')

#     def perform_destroy(self, instance):
#         """Soft delete an invitation."""
#         from django.utils import timezone
#         instance.is_deleted = True
#         instance.deleted_at = timezone.now()
#         instance.save()

#     def perform_create(self, serializer):
#         """Create invitation with current user as inviter."""
#         profile = get_object_or_404(UserProfile, user=self.request.user)
#         serializer.save(inviter=profile)

#     @action(detail=True, methods=['post'])
#     def accept(self, request, pk=None):
#         """Accept a community invitation."""
#         invitation = self.get_object()
#         profile = get_object_or_404(UserProfile, user=request.user)

#         if invitation.invitee != profile:
#             return Response(
#                 {'detail': 'You cannot accept this invitation.'},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         if invitation.status != 'pending':
#             return Response(
#                 {'detail': 'Invitation is no longer pending.'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # Create membership
#         default_role = invitation.community.roles.filter(is_default=True).first()
#         CommunityMembership.objects.get_or_create(
#             community=invitation.community,
#             user=profile,
#             defaults={'role': default_role}
#         )

#         # Update invitation status
#         invitation.status = 'accepted'
#         invitation.save()

#         return Response({'detail': 'Invitation accepted successfully.'})

#     @action(detail=True, methods=['post'])
#     def decline(self, request, pk=None):
#         """Decline a community invitation."""
#         invitation = self.get_object()
#         profile = get_object_or_404(UserProfile, user=request.user)

#         if invitation.invitee != profile:
#             return Response(
#                 {'detail': 'You cannot decline this invitation.'},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         if invitation.status != 'pending':
#             return Response(
#                 {'detail': 'Invitation is no longer pending.'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         invitation.status = 'declined'
#         invitation.save()

#         return Response({'detail': 'Invitation declined successfully.'})


class CommunityAnnouncementViewSet(viewsets.ModelViewSet):
    """ViewSet for managing community-specific announcements."""
    serializer_class = CommunityAnnouncementSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def get_queryset(self):
        """Get announcements for communities where user has access."""
        profile = get_object_or_404(UserProfile, user=self.request.user)

        # Filter by community if specified
        community_slug = self.request.query_params.get('community')
        if community_slug:
            try:
                community = Community.objects.get(slug=community_slug, is_deleted=False)
                # Check if user is a member or can access the community
                if self._can_access_community(profile, community):
                    return CommunityAnnouncement.objects.filter(
                        community=community,
                        is_deleted=False
                    ).order_by('-is_sticky', '-is_important', '-created_at')
                else:
                    return CommunityAnnouncement.objects.none()
            except Community.DoesNotExist:
                return CommunityAnnouncement.objects.none()

        # Get announcements for all communities user is a member of
        user_communities = Community.objects.filter(
            memberships__user=profile,
            memberships__status='active',
            memberships__is_deleted=False,
            is_deleted=False
        )

        return CommunityAnnouncement.objects.filter(
            community__in=user_communities,
            is_deleted=False
        ).order_by('-is_sticky', '-is_important', '-created_at')

    def _can_access_community(self, user_profile, community):
        """Check if user can access the community."""
        # Public communities are accessible to all
        if community.community_type == 'public':
            return True

        # Check if user is a member
        return CommunityMembership.objects.filter(
            community=community,
            user=user_profile,
            status='active',
            is_deleted=False
        ).exists()

    def perform_create(self, serializer):
        """Create announcement with permission checks."""
        profile = get_object_or_404(UserProfile, user=self.request.user)
        community = serializer.validated_data['community']

        # Check if user can manage announcements for this community
        if not self._can_manage_announcements(profile, community):
            raise PermissionDenied(
                "You don't have permission to create announcements for this community."
            )

        serializer.save(created_by=profile)

    def perform_update(self, serializer):
        """Update announcement with permission checks."""
        profile = get_object_or_404(UserProfile, user=self.request.user)
        instance = self.get_object()

        if not instance.can_user_edit(profile):
            raise PermissionDenied(
                "You don't have permission to edit this announcement."
            )

        serializer.save()

    def perform_destroy(self, instance):
        """Soft delete announcement with permission checks."""
        profile = get_object_or_404(UserProfile, user=self.request.user)

        if not instance.can_user_edit(profile):
            raise PermissionDenied(
                "You don't have permission to delete this announcement."
            )

        from django.utils import timezone
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

    def _can_manage_announcements(self, user_profile, community):
        """Check if user can manage announcements for the community."""
        # Community creator can always manage
        if community.creator == user_profile:
            return True

        # Check if user is a community moderator/admin
        try:
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
