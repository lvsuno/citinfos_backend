"""
Comprehensive middleware for event detection and user activity tracking.
Tracks CRUD operations across all Django apps for analytics and notifications.
Includes bot detection and content safety integration.

Updated to include:
- A/B Testing experiment events and interactions
- Enhanced community management events
- AI conversation summaries and model performance tracking
- Improved analytics and error tracking
- Content moderation and bot detection
- Real-time rate limiting with A/B testing specific limits

Supported Apps:
- accounts: User management, profiles, authentication
- content: Posts, comments, likes, shares, hashtags, A/B testing experiments
- communities: Community management, memberships, roles, moderation
- ai_conversations: AI models, conversations, messages, analytics
- analytics: System metrics, user analytics, error logs
- polls: Poll creation and voting
- messaging: Direct messaging
- notifications: Notification management
- core: Core system utilities
"""

import sys
from django.utils import timezone
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from accounts.models import UserEvent, UserSession
from core.utils import get_client_ip
from core.session_manager import SessionManager, SESSION_DURATION_SECONDS
from django.conf import settings

# SimpleJWT imports for decoding/creating tokens in middleware
try:
    from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
    from rest_framework_simplejwt.exceptions import TokenError
except Exception:  # pragma: no cover - simplejwt not loaded in some envs
    AccessToken = None
    RefreshToken = None


class EventDetectionMiddleware:
    """
    Middleware to detect and track user events across all CRUD operations.
    Captures events for accounts, content, polls, communities, equipment, messaging, etc.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Define events we want to track
        self.tracked_events = {
            # User management events
            'user_login': 'User Login',
            'user_logout': 'User Logout',
            'user_register': 'User Registration',
            'profile_update': 'Profile Update',
            'profile_view': 'Profile View',

            # Content events
            'post_create': 'Post Created',
            'post_update': 'Post Updated',
            'post_delete': 'Post Deleted',
            'post_like': 'Post Liked',
            'post_unlike': 'Post Unliked',
            'post_share': 'Post Shared',
            'comment_create': 'Comment Created',
            'comment_update': 'Comment Updated',
            'comment_delete': 'Comment Deleted',

            # A/B Testing events
            'experiment_create': 'Experiment Created',
            'experiment_update': 'Experiment Updated',
            'experiment_delete': 'Experiment Deleted',
            'experiment_start': 'Experiment Started',
            'experiment_stop': 'Experiment Stopped',
            'experiment_view': 'Experiment Viewed',
            'experiment_stats_view': 'Experiment Stats Viewed',
            'experiment_assignment': 'User Assigned to Experiment',
            'experiment_metric_record': 'Experiment Metric Recorded',
            'experiment_interaction_record': 'Experiment Interaction Recorded',
            'algorithm_request': 'User Algorithm Requested',
            'experiment_dashboard_view': 'Experiment Dashboard Viewed',

            # Community events
            'community_create': 'Community Created',
            'community_update': 'Community Updated',
            'community_delete': 'Community Deleted',
            'community_join': 'Community Joined',
            'community_leave': 'Community Left',
            'community_post': 'Community Post',
            'community_membership_create': 'Community Membership Created',
            'community_role_create': 'Community Role Created',
            'community_moderation': 'Community Moderation Action',
            'community_invitation_create': 'Community Invitation Created',

            # Equipment events
            'equipment_create': 'Equipment Added',
            'equipment_update': 'Equipment Updated',
            'equipment_delete': 'Equipment Deleted',
            'maintenance_log': 'Maintenance Logged',
            'condition_update': 'Condition Updated',
            'bill_create': 'Bill Created',
            'bill_update': 'Bill Updated',
            'bill_delete': 'Bill Deleted',
            'warranty_create': 'Warranty Created',
            'warranty_update': 'Warranty Updated',
            'warranty_delete': 'Warranty Deleted',
            'home_appliance_create': 'Home Appliance Added',
            'home_appliance_update': 'Home Appliance Updated',
            'home_appliance_delete': 'Home Appliance Deleted',
            'electronic_create': 'Electronic Device Added',
            'electronic_update': 'Electronic Device Updated',
            'electronic_delete': 'Electronic Device Deleted',
            'hvac_create': 'HVAC System Added',
            'hvac_update': 'HVAC System Updated',
            'hvac_delete': 'HVAC System Deleted',
            'vehicle_create': 'Vehicle Added',
            'vehicle_update': 'Vehicle Updated',
            'vehicle_delete': 'Vehicle Deleted',
            'smart_device_create': 'Smart Device Added',
            'smart_device_update': 'Smart Device Updated',
            'smart_device_delete': 'Smart Device Deleted',
            'power_tool_create': 'Power Tool Added',
            'power_tool_update': 'Power Tool Updated',
            'power_tool_delete': 'Power Tool Deleted',
            'medical_equipment_create': 'Medical Equipment Added',
            'medical_equipment_update': 'Medical Equipment Updated',
            'medical_equipment_delete': 'Medical Equipment Deleted',

            # AI Conversation events
            'ai_conversation_create': 'AI Conversation Started',
            'ai_conversation_update': 'AI Conversation Updated',
            'ai_conversation_delete': 'AI Conversation Deleted',
            'ai_message_create': 'AI Message Sent',
            'ai_message_rating': 'AI Message Rated',
            'ai_agent_create': 'AI Agent Created',
            'ai_agent_update': 'AI Agent Updated',
            'ai_agent_delete': 'AI Agent Deleted',
            'ai_model_create': 'AI Model Created',
            'ai_model_update': 'AI Model Updated',
            'ai_analytics_view': 'AI Analytics Viewed',
            'ai_model_performance_view': 'AI Model Performance Viewed',
            'ai_conversation_summary_create': 'AI Conversation Summary Created',

            # Analytics events
            'analytics_view': 'Analytics Viewed',
            'session_create': 'Session Started',
            'session_update': 'Session Updated',
            'event_track': 'Event Tracked',
            'error_log': 'Error Logged',
            'metric_record': 'Metric Recorded',
            'daily_analytics_view': 'Daily Analytics Viewed',
            'user_analytics_view': 'User Analytics Viewed',

            # Notification events
            'notification_create': 'Notification Created',
            'notification_read': 'Notification Read',
            'notification_delete': 'Notification Deleted',

            # Hashtag events
            'hashtag_create': 'Hashtag Created',
            'hashtag_follow': 'Hashtag Followed',
            'hashtag_unfollow': 'Hashtag Unfollowed',

            # Social events (renamed for UserEvent compatibility)
            'user_follow': 'User Followed',
            'user_unfollow': 'User Unfollowed',
            'user_block': 'User Blocked',
            'user_unblock': 'User Unblocked',

            # Messaging events
            'message_send': 'Message Sent',
            'chat_create': 'Chat Created',
            'chat_join': 'Chat Joined',
            'chat_leave': 'Chat Left',
            'message_read': 'Message Read',
            'message_delete': 'Message Deleted',

            # Poll events
            'poll_create': 'Poll Created',
            'poll_update': 'Poll Updated',
            'poll_delete': 'Poll Deleted',
            'poll_view': 'Poll Viewed',
            'poll_vote': 'Poll Vote Cast',
            'poll_option_create': 'Poll Option Created',
            'poll_option_update': 'Poll Option Updated',
            'poll_option_delete': 'Poll Option Deleted',
            'poll_voter_create': 'Poll Voter Added',
            'poll_close': 'Poll Closed',

            # Additional equipment types
            'home_create': 'Home Added',
            'home_update': 'Home Updated',
            'home_delete': 'Home Deleted',
            'brand_create': 'Brand Created',
            'brand_update': 'Brand Updated',
            'brand_delete': 'Brand Deleted',
            'equipment_model_create': 'Equipment Model Created',
            'equipment_model_update': 'Equipment Model Updated',
            'equipment_model_delete': 'Equipment Model Deleted',
            'bill_template_create': 'Bill Template Created',
            'bill_template_update': 'Bill Template Updated',
            'bill_template_delete': 'Bill Template Deleted',

            # Core system events
            'country_view': 'Country Data Viewed',
            'city_view': 'City Data Viewed',
            'system_metric_view': 'System Metrics Viewed',

            # Additional account events
            'password_change': 'Password Changed',
            'password_reset': 'Password Reset',
            'email_verification': 'Email Verified',
            'account_delete': 'Account Deleted',
            'account_reactivate': 'Account Reactivated',
            'session_expire': 'Session Expired',

            # Additional content events
            'post_view': 'Post Viewed',
            'post_bookmark': 'Post Bookmarked',
            'file_download': 'File Downloaded',
            'media_access': 'Media Accessed',

            # Community management expanded
            'community_role_update': 'Community Role Updated',
            'community_invitation_accept': 'Community Invitation Accepted',

            # Security events
            'security_login_failed': 'Login Failed',
            'security_suspicious_activity': 'Suspicious Activity',
            'security_account_locked': 'Account Locked',
            'security_password_breach': 'Password Breach Detected',
            'security_two_factor_enabled': 'Two-Factor Authentication Enabled',
            'security_session_hijack': 'Session Hijack Detected',

            # Content safety events
            'content_flagged': 'Content Flagged',
            'content_moderated': 'Content Moderated',
            'content_approved': 'Content Approved',
            'content_rejected': 'Content Rejected',
            'bot_detection': 'Bot Detected',
            'spam_detection': 'Spam Detected',
            'abuse_report': 'Abuse Reported',

            # System events
            'api_access': 'API Access',
            'search_perform': 'Search Performed',
            'file_upload': 'File Uploaded',
            'error_encountered': 'Error Encountered',
        }

        # Map URL patterns to events - Updated for distributed apps
        self.url_event_mapping = {
            # --- ACCOUNTS ---
            '/api/auth/login/': 'user_login',
            '/api/auth/logout/': 'user_logout',
            '/api/auth/register/': 'user_register',
            '/api/auth/register-professional/': 'user_register',
            '/api/auth/me/': 'profile_view',
            '/api/profiles/': 'profile_view',
            '/api/users/': 'profile_view',
            '/api/professional-profiles/': 'profile_view',
            '/api/follows/': 'user_follow',
            '/api/blocks/': 'user_block',
            '/api/sessions/': 'session_create',
            '/api/events/': 'event_track',
            '/api/settings/': 'profile_update',
            '/api/accounts/me/': 'profile_view',
            '/api/accounts/toggle-follow/': 'user_follow',
            '/api/accounts/update-me/': 'profile_update',

            # --- CONTENT ---
            '/api/posts/': 'post_create',
            '/api/posts/like/': 'post_like',
            '/api/posts/share/': 'post_share',
            '/api/posts/bookmark/': 'post_bookmark',
            '/api/posts/comment/': 'comment_create',
            '/api/comments/': 'comment_create',
            '/api/likes/': 'post_like',
            '/api/shares/': 'post_share',
            '/api/media/': 'file_upload',
            '/api/hashtags/': 'hashtag_create',
            '/api/hashtags/follow/': 'hashtag_follow',
            '/api/hashtags/unfollow/': 'hashtag_unfollow',
            '/api/content/like/': 'post_like',
            '/api/content/share/': 'post_share',
            '/api/content/': 'post_create',

            # --- A/B TESTING ---
            '/api/experiments/': 'experiment_create',
            '/api/experiment-assignments/': 'experiment_assignment',
            '/api/experiment-metrics/': 'experiment_metric_record',
            '/api/experiment-results/': 'experiment_view',
            '/api/experiment-dashboard/': 'experiment_dashboard_view',

            # --- COMMUNITIES ---
            '/api/communities/': 'community_create',
            '/api/communities/join/': 'community_join',
            '/api/communities/leave/': 'community_leave',
            '/api/communities/members/': 'community_membership_create',
            '/api/communities/posts/': 'community_post',
            '/api/community-memberships/': 'community_membership_create',
            '/api/community-roles/': 'community_role_create',
            '/api/community-roles/update/': 'community_role_update',
            '/api/community-moderation/': 'community_moderation',
            '/api/community-invitations/': 'community_invitation_create',
            '/api/community-invitations/accept/': 'community_invitation_accept',

            # --- EQUIPMENT ---
            '/api/homes/': 'home_create',
            '/api/brands/': 'brand_create',
            '/api/equipment-models/': 'equipment_model_create',
            '/api/equipment/': 'equipment_create',
            '/api/equipment/health-summary/': 'equipment_health_summary',
            '/api/equipment/run-maintenance-check/': 'maintenance_log',
            '/api/equipment/bulk-create/': 'equipment_create',
            '/api/equipment/analytics/': 'analytics_view',
            '/api/equipment/models/': 'equipment_model_create',
            '/api/equipment/statistics/': 'analytics_view',
            '/api/equipment/top-brands/': 'brand_create',
            '/api/bill-templates/': 'bill_template_create',
            '/api/bills/': 'bill_create',
            '/api/warranties/': 'warranty_create',
            '/api/home-appliances/': 'home_appliance_create',
            '/api/electronics/': 'electronic_create',
            '/api/hvac/': 'hvac_create',
            '/api/vehicles/': 'vehicle_create',
            '/api/smart-devices/': 'smart_device_create',
            '/api/power-tools/': 'power_tool_create',
            '/api/medical-equipment/': 'medical_equipment_create',

            # --- AI CONVERSATIONS ---
            '/api/llm-models/': 'ai_model_create',
            '/api/agents/': 'ai_agent_create',
            '/api/conversations/': 'ai_conversation_create',
            '/api/conversations/duplicate/': 'ai_conversation_update',
            '/api/conversations/archive/': 'ai_conversation_update',
            '/api/conversations/unarchive/': 'ai_conversation_update',
            '/api/conversations/by-provider/': 'ai_conversation_view',
            '/api/conversations/by-model/': 'ai_conversation_view',
            '/api/messages/': 'ai_message_create',
            '/api/ratings/': 'ai_message_rating',
            '/api/capabilities/': 'ai_analytics_view',

            # --- ANALYTICS ---
            '/api/analytics/': 'analytics_view',
            '/api/analytics/active/': 'analytics_view',
            '/api/analytics/by-device/': 'analytics_view',
            '/api/analytics/statistics/': 'analytics_view',
            '/api/analytics/by-type/': 'analytics_view',
            '/api/analytics/by-category/': 'analytics_view',
            '/api/analytics/timeline/': 'analytics_view',
            '/api/analytics/summary/': 'analytics_view',
            '/api/daily-analytics/': 'daily_analytics_view',
            '/api/user-analytics/': 'user_analytics_view',
            '/api/metrics/': 'metric_record',
            '/api/errors/': 'error_log',
            '/api/system-metrics/': 'system_metric_view',

            # --- POLLS ---
            '/api/polls/': 'poll_create',
            '/api/polls/vote/': 'poll_vote',
            '/api/polls/remove-vote/': 'poll_vote',
            '/api/polls/close/': 'poll_close',
            '/api/polls/results/': 'poll_view',
            '/api/polls/my-polls/': 'poll_view',
            '/api/poll-options/': 'poll_option_create',
            '/api/poll-votes/': 'poll_vote',
            '/api/poll-voters/': 'poll_voter_create',

            # --- MESSAGING ---
            '/api/chat-rooms/': 'chat_create',
            '/api/chat-rooms/join/': 'chat_join',
            '/api/chat-rooms/leave/': 'chat_leave',
            '/api/chat-rooms/messages/': 'messages',
            '/api/room-messages/': 'message_send',
            '/api/room-memberships/': 'chat_join',
            '/api/direct-messages/': 'create_direct_message',
            '/api/messages/mark-as-read/': 'message_read',
            '/api/messages/add-attachment/': 'message_send',

            # --- NOTIFICATIONS ---
            '/api/notifications/': 'notification_create',

            # --- SEARCH ---
            '/api/search/': 'search_perform',
            '/api/search/cached-recent/': 'search_perform',

            # --- CORE ---
            '/api/countries/': 'country_view',
            '/api/cities/': 'city_view',
            '/api/core/': 'api_access',
        }

    def __call__(self, request):
        # Store request start time
        request.start_time = timezone.now()

        # Determine event type before processing
        # Use status code 200 as placeholder for pre-processing
        dummy_response_200 = type('Response', (), {'status_code': 200})()
        event_type = self.determine_event_type(request, dummy_response_200)

        # Check for bot behavior (may return early response)
        bot_check_response = self.check_bot_behavior(request, event_type)
        if bot_check_response:
            return bot_check_response

        # Check content safety (may return early response)
        content_check_response = self.check_content_safety(request, event_type)
        if content_check_response:
            return content_check_response

        # Process the request
        response = self.get_response(request)

        # Track the event after processing
        self.track_event(request, response)

        return response

    def track_event(self, request, response):
        """Track user events based on request and response."""
        try:
            # Skip tracking for anonymous users on read operations
            if (
                isinstance(request.user, AnonymousUser)
                    and request.method == 'GET'
            ):
                return

            # Determine event type
            event_type = self.determine_event_type(request, response)
            if not event_type:
                return

            # Extract metadata
            metadata = self.extract_metadata(request, response)

            # Create UserEvent record (only for account-related events)
            if self.is_account_event(event_type):
                # Get UserProfile for UserEvent
                user_profile = None
                if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
                    user_profile = request.user.userprofile

                # Get or create user session
                session = None
                if user_profile and hasattr(request, 'session'):
                    session_id = request.session.session_key
                    if session_id:
                        try:
                            session = UserSession.objects.get(
                                session_id=session_id
                            )
                        except UserSession.DoesNotExist:
                            pass

                # Determine severity based on event type
                severity = self.get_event_severity(event_type)

                # Check if event was successful
                success = 200 <= response.status_code < 400

                if user_profile is not None:
                    UserEvent.objects.create(
                        user=user_profile,
                        session=session,
                        event_type=event_type,
                        severity=severity,
                        description=self.tracked_events.get(
                            event_type, event_type
                        ),
                        metadata=metadata,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                        success=success,
                        error_message=(
                            '' if success else f'HTTP {response.status_code}'
                        ),
                        requires_review=severity in ['high', 'critical']
                    )

        except Exception as e:
            # Log error but don't break the request
            print(f"Event tracking error: {e}")

    def check_bot_behavior(self, request, event_type):
        """Check for bot-like behavior patterns in real-time."""
        try:
            # Only check for authenticated users
            if not hasattr(request.user, 'userprofile'):
                return

            user = request.user.userprofile

            # Import here to avoid circular imports
            from content.utils import (
                check_rapid_posting, analyze_user_posting_patterns,
                is_user_blocked_as_bot
            )
            from content.models import BotDetectionEvent

            # Check if user is already blocked as bot
            if is_user_blocked_as_bot(user):
                return JsonResponse(
                    {'error': 'Account flagged for automated behavior'},
                    status=403
                )

            # Check for rapid posting if this is a content creation event
            if event_type in ['post_create', 'comment_create', 'message_send']:
                # Create a dummy content object for the check
                dummy_content = type('DummyContent', (), {
                    'id': None,
                    'user': user,
                    'created_at': timezone.now()
                })()

                if check_rapid_posting(user, dummy_content):
                    BotDetectionEvent.objects.create(
                        user=user,
                        event_type='rapid_posting',
                        severity=3,
                        confidence_score=0.8,
                        description='Rapid posting pattern detected'
                    )

            # Check posting patterns periodically (every 10th request)
            import random
            if random.randint(1, 10) == 1:
                analyze_user_posting_patterns(user)

        except Exception as e:
            # Don't break the request flow for bot detection errors
            print(f"Bot detection error: {e}")

    def check_content_safety(self, request, event_type):
        """Check content for safety violations before processing."""
        try:
            # Only check content creation/update events
            if event_type not in ['post_create', 'post_update',
                                  'comment_create', 'comment_update']:
                return None

            # Import here to avoid circular imports
            from content.utils import check_moderation_rules

            # Extract content from request
            content_text = None
            if hasattr(request, 'data'):
                content_text = (
                    request.data.get('content') or request.data.get('text')
                )
            elif request.method == 'POST' and request.POST:
                content_text = (
                    request.POST.get('content') or request.POST.get('text')
                )

            if not content_text:
                return None

            # Quick content analysis
            moderation_result = check_moderation_rules(content_text)

            # Block if high-confidence violation
            if (
                isinstance(moderation_result, dict)
                and moderation_result.get('action') == 'block'
            ):
                return JsonResponse(
                    {
                        'error': 'Content violates community guidelines',
                        'details': moderation_result.get('violations', [])
                    },
                    status=400
                )

            return None  # Allow content to proceed

        except Exception as e:
            # Don't break the request flow for content safety errors
            print(f"Content safety check error: {e}")
            return None

    def is_account_event(self, event_type):
        """Check if this is an account-related event."""
        account_events = [
            # Authentication & Security
            'user_login', 'user_logout', 'login_failed', 'user_register',
            'password_change', 'password_reset_request',
            'password_reset_complete', 'email_change', 'email_verify',
            'two_factor_enable', 'two_factor_disable',

            # Account Management
            'profile_update', 'profile_picture_change', 'privacy_update',
            'notification_settings_update', 'account_deactivation',
            'account_reactivation', 'account_deletion_request',
            'data_export_request',

            # Social Account Actions
            'follow_user', 'unfollow_user', 'block_user', 'unblock_user',
            'profile_view',

            # Professional Account
            'pro_upgrade', 'pro_verification_request',
            'pro_verification_complete',

            # Security Events
            'suspicious_login', 'device_change', 'location_change',
            'session_timeout', 'forced_logout',

            # Session and tracking
            'session_create', 'event_track', 'settings'
        ]
        return event_type in account_events

    def determine_event_type(self, request, response):
        """Determine the event type based on request details."""
        method = request.method
        path = request.path
        status_code = response.status_code

        # Check if request was successful
        if status_code >= 400:
            return 'error_encountered'

        # Check specific URL patterns first
        for url_pattern, event_type in self.url_event_mapping.items():
            if url_pattern in path:
                # Determine specific action based on method
                if method == 'POST':
                    return event_type
                elif method == 'PUT' or method == 'PATCH':
                    return event_type.replace('_create', '_update')
                elif method == 'DELETE':
                    return event_type.replace('_create', '_delete')
                elif method == 'GET':
                    # For custom actions, keep the event_type
                    if event_type.endswith('_view') or event_type.endswith('_stats_view'):
                        return event_type
                    return event_type.replace('_create', '_view')

        # Check for custom actions in URL (expanded)
        if '/start/' in path and '/experiments/' in path:
            return 'experiment_start'
        elif '/stop/' in path and '/experiments/' in path:
            return 'experiment_stop'
        elif '/stats/' in path and '/experiments/' in path:
            return 'experiment_stats_view'
        elif '/dashboard/' in path and '/experiments/' in path:
            return 'experiment_dashboard_view'
        elif '/algorithm/' in path:
            return 'algorithm_request'
        elif '/join/' in path:
            if '/communities/' in path or '/c/' in path:
                return 'community_join'
            elif '/chat-rooms/' in path:
                return 'chat_join'
        elif '/leave/' in path:
            if '/communities/' in path or '/c/' in path:
                return 'community_leave'
            elif '/chat-rooms/' in path:
                return 'chat_leave'
        elif '/accept/' in path and '/invitations/' in path:
            return 'community_invitation_accept'
        elif '/decline/' in path and '/invitations/' in path:
            return 'community_invitation_decline'
        elif '/follow/' in path:
            return 'user_follow'
        elif '/unfollow/' in path:
            return 'user_unfollow'
        elif '/like/' in path:
            return 'post_like'
        elif '/unlike/' in path:
            return 'post_unlike'
        elif '/vote/' in path:
            return 'poll_vote'
        elif '/remove-vote/' in path:
            return 'poll_vote'
        elif '/close/' in path and '/polls/' in path:
            return 'poll_close'
        elif '/results/' in path and '/polls/' in path:
            return 'poll_view'
        elif '/my-polls/' in path and '/polls/' in path:
            return 'poll_view'
        elif '/members/' in path and ('/communities/' in path or '/c/' in path):
            return 'community_membership_create'
        elif '/posts/' in path and ('/communities/' in path or '/c/' in path):
            return 'community_post'
        elif '/mark-as-read/' in path and '/messages/' in path:
            return 'message_read'
        elif '/add-attachment/' in path and '/messages/' in path:
            return 'message_send'
        elif '/bulk-create/' in path and '/equipment/' in path:
            return 'equipment_create'
        elif '/health-summary/' in path and '/equipment/' in path:
            return 'equipment_health_summary'
        elif '/run-maintenance-check/' in path and '/equipment/' in path:
            return 'maintenance_log'
        elif '/analytics/' in path and '/equipment/' in path:
            return 'analytics_view'
        elif '/models/' in path and '/equipment/' in path:
            return 'equipment_model_create'
        elif '/statistics/' in path and '/equipment/' in path:
            return 'analytics_view'
        elif '/top-brands/' in path and '/equipment/' in path:
            return 'brand_create'
        elif '/by-provider/' in path and '/conversations/' in path:
            return 'ai_conversation_view'
        elif '/by-model/' in path and '/conversations/' in path:
            return 'ai_conversation_view'
        elif '/duplicate/' in path and '/conversations/' in path:
            return 'ai_conversation_update'
        elif '/archive/' in path and '/conversations/' in path:
            return 'ai_conversation_update'
        elif '/unarchive/' in path and '/conversations/' in path:
            return 'ai_conversation_update'
        elif '/capabilities/' in path:
            return 'ai_analytics_view'
        elif '/summary/' in path and '/analytics/' in path:
            return 'analytics_view'
        elif '/timeline/' in path and '/analytics/' in path:
            return 'analytics_view'
        elif '/by-device/' in path and '/analytics/' in path:
            return 'analytics_view'
        elif '/by-type/' in path and '/analytics/' in path:
            return 'analytics_view'
        elif '/by-category/' in path and '/analytics/' in path:
            return 'analytics_view'

        # Generic API access tracking
        if path.startswith('/api/') and method == 'GET':
            return 'api_access'

        return None

    def get_event_category(self, event_type):
        """Get category for event type."""
        if event_type.startswith(('user_', 'profile_')):
            return 'user_management'
        elif event_type.startswith(('post_', 'comment_', 'like_', 'share_')):
            return 'content'
        elif event_type.startswith('experiment_'):
            return 'ab_testing'
        elif event_type.startswith('community_'):
            return 'community'
        elif event_type.startswith(
            ('equipment_', 'maintenance_', 'condition_')
        ):
            return 'equipment'
        elif event_type.startswith(('message_', 'chat_')):
            return 'messaging'
        elif event_type.startswith('poll_'):
            return 'polls'
        elif event_type.startswith('ai_'):
            return 'ai_conversations'
        elif event_type.startswith(('analytics_', 'session_', 'event_',
                                    'metric_', 'error_')):
            return 'analytics'
        elif event_type.startswith('notification_'):
            return 'notifications'
        elif event_type.startswith('hashtag_'):
            return 'content'
        elif event_type in [
            'api_access', 'search_perform', 'file_upload', 'algorithm_request'
        ]:
            return 'system'
        elif event_type == 'error_encountered':
            return 'error'
        else:
            return 'other'

    def extract_metadata(self, request, response):
        """Extract relevant metadata from request and response."""
        metadata = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
        }

        # Add query parameters
        if request.GET:
            metadata['query_params'] = dict(request.GET)

        # Add request data for non-GET requests (limited for privacy)
        if request.method != 'GET' and hasattr(request, 'data'):
            # Only track non-sensitive fields
            safe_fields = [
                'name', 'description', 'title', 'content', 'type', 'category'
            ]
            safe_data = {}
            for field in safe_fields:
                if field in request.data:
                    # Limit length
                    safe_data[field] = str(request.data[field])[:100]
            if safe_data:
                metadata['request_data'] = safe_data

        # Add response data for create operations
        if request.method == 'POST' and response.status_code == 201:
            try:
                if hasattr(response, 'data') and 'id' in response.data:
                    metadata['created_id'] = str(response.data['id'])
            except Exception:
                pass

        # Add file upload info
        if request.FILES:
            metadata['files_uploaded'] = len(request.FILES)
            metadata['file_types'] = [
                f.content_type for f in request.FILES.values()
            ]

        # Add user info if available
        if hasattr(request.user, 'userprofile'):
            metadata['user_id'] = str(request.user.userprofile.id)
            metadata['user_role'] = request.user.userprofile.role

        return metadata

    def get_event_severity(self, event_type):
        """Determine event severity based on event type."""
        # Critical security events
        critical_events = [
            'suspicious_login', 'account_deactivation', 'forced_logout',
            'account_deletion_request'
        ]

        # High-risk events
        high_events = [
            'login_failed', 'password_change', 'email_change',
            'two_factor_disable', 'user_block', 'error_encountered'
        ]

        # Medium-risk events
        medium_events = [
            'device_change', 'location_change', 'privacy_update',
            'password_reset_request', 'pro_verification_request'
        ]

        if event_type in critical_events:
            return 'critical'
        elif event_type in high_events:
            return 'high'
        elif event_type in medium_events:
            return 'medium'
        else:
            return 'low'

    def calculate_processing_time(self, request):
        """Calculate request processing time in milliseconds."""
        if hasattr(request, 'start_time'):
            end_time = timezone.now()
            delta = end_time - request.start_time
            return int(delta.total_seconds() * 1000)
        return None

class APIRateLimitMiddleware:
    """
    Middleware for API rate limiting and abuse prevention.
    Works in conjunction with event detection.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {
            'default': 100,  # requests per minute
            'post_create': 10,
            'message_send': 50,
            'login_attempt': 5,
            'experiment_create': 5,  # Limit A/B test creation
            'experiment_metric_record': 200,  # Allow frequent metrics
            'experiment_interaction_record': 500,  # High interaction limit
        }

    def __call__(self, request):
        # Check rate limits for authenticated users
        if hasattr(request.user, 'userprofile'):
            if self.is_rate_limited(request):
                return JsonResponse(
                    {'error': 'Rate limit exceeded. Please try again later.'},
                    status=429
                )

        response = self.get_response(request)
        return response

    def is_rate_limited(self, request):
        """Check if user has exceeded rate limits."""
        # Implementation would check recent events from UserEvent model
        # This is a simplified version
        return False

# class SessionValidationMiddleware(MiddlewareMixin):
#     """
#     DEPRECATED: This middleware functionality has been consolidated into
#     core.middleware.optimized_auth_middleware.OptimizedAuthenticationMiddleware

#     Legacy middleware to validate sessions using Redis and ensure active sessions.
#     """

#     def __init__(self, get_response):
#         super().__init__(get_response)
#         self.session_manager = SessionManager()
#         # URLs that don't require session validation
#         self.exempt_urls = [
#             '/api/auth/csrf/',  # CSRF token endpoint
#             '/api/auth/register/',
#             '/api/auth/login/',  # Current login endpoint
#             '/api/auth/login-with-verification-check/',
#             '/api/auth/verify/',  # Email verification
#             '/api/auth/resend-code/',  # Resend verification code
#             '/api/auth/request-verification/',  # Request verification
#             '/api/auth/register-professional/',
#             '/api/auth/verification-status/',  # Fixed missing slash
#             '/api/auth/generate-passwords/',  # Password generation endpoint
#             '/api/auth/validate-password/',   # Password validation endpoint
#             '/api/auth/logout/',  # Logout endpoint
#             '/api/auth/me/',  # Current user endpoint
#             # JWT endpoints
#             '/api/auth/login/',
#             '/api/auth/refresh/',
#             '/api/auth/logout/',
#             '/api/auth/register/',
#             '/api/auth/user-info/',
#             '/api/auth/verify/',
#             '/api/auth/login/',
#             '/api/auth/token/',
#             '/api/auth/token/refresh/',
#             # Alternative auth endpoints
#             '/auth/login/',
#             '/auth/register/',
#             '/auth/logout/',
#             '/auth/user/',
#             '/auth/token/refresh/',
#             '/auth/token/verify/',
#             '/auth/change-password/',
#             '/auth/password-reset/',
#             # Public profile endpoints (no authentication required)
#             '/api/public-profiles/',
#             '/api/public/profiles/',
#             '/api/public/users/',
#             '/admin/',
#             '/swagger/',
#             '/redoc/',
#             '/static/',
#             '/media/',
#         ]

#     def process_request(self, request):
#         """
#         Validate session for all requests except exempt URLs.
#         Authentication Flow:
#         1. If JWT + Session: Use JWT for auth, session for renewal capability
#         2. If JWT only: Validate JWT, check associated session, send session cookie back
#         3. If Session only: Validate session (fallback mode)
#         4. All session validation uses Redis only, never database
#         """
#         # Skip validation in test environment
#         if 'test' in sys.argv or hasattr(request, '_dont_enforce_csrf_checks'):
#             return None

#         # Skip validation for exempt URLs
#         if any(request.path.startswith(url) for url in self.exempt_urls):

#             return None

#         # Skip for OPTIONS requests (CORS preflight)
#         if request.method == 'OPTIONS':

#             return None

#         # Extract authentication credentials
#         session_id = request.session.session_key
#         auth_header = request.META.get('HTTP_AUTHORIZATION', '')

#         # Check for session ID in custom header (mobile apps)
#         if not session_id and 'HTTP_X_SESSION_ID' in request.META:
#             session_id = request.META['HTTP_X_SESSION_ID']

#         # Check if user provided any authentication credentials
#         has_auth_attempt = bool(session_id or auth_header.startswith('Bearer '))

#         # PREFERRED FLOW 1: Session ID + JWT - Only validate JWT
#         if session_id and auth_header.startswith('Bearer ') and AccessToken is not None:
#             raw_token = auth_header.split(' ', 1)[1].strip()
#             try:
#                 token = AccessToken(raw_token)
#                 # JWT is valid and user has session_id, assume session is valid
#                 return None
#             except TokenError:
#                 # JWT is expired - check if we can renew it using the associated session
#                 if self._handle_jwt_renewal(request, raw_token):

#                     return None
#                 else:

#                     return self._session_validation_error()

#             except Exception:
#                 return self._session_validation_error()

#         # PREFERRED FLOW 2: JWT only - Validate JWT and check associated session
#         elif not session_id and auth_header.startswith('Bearer ') and AccessToken is not None:
#             raw_token = auth_header.split(' ', 1)[1].strip()
#             try:
#                 token = AccessToken(raw_token)
#                 token_session_id = token.payload.get('sid')

#                 if token_session_id:
#                     # Check if associated session is still valid using SessionManager
#                     session_data = self.session_manager.get_session(token_session_id)
#                     if session_data and session_data.get('is_active', False):

#                         # Valid JWT with valid custom session
#                         request.session_data = session_data
#                         request.user_profile_id = token.payload.get('user_id')
#                         # Mark to send session_id back to client
#                         request._jwt_session_to_set = token_session_id

#                         return None
#                     else:

#                         return self._session_validation_error()
#                 else:
#                     # JWT has no session ID - treat as valid for backwards compatibility

#                     return None

#             except TokenError as e:

#                 # JWT is expired - check if we can renew it using the associated session
#                 if self._handle_jwt_renewal(request, raw_token):

#                     return None
#                 else:

#                     return self._session_validation_error()
#             except Exception as e:

#                 return self._session_validation_error()

#         # FALLBACK: Session ID only - Validate session in Redis
#         elif session_id and not auth_header.startswith('Bearer '):
#             session_data = self.session_manager.get_session(session_id)
#             if not session_data or not session_data.get('is_active', False):
#                 return self._session_validation_error()
#             else:
#                 # Valid session - smart renew if needed and continue
#                 self.session_manager.smart_renew_session_if_needed(session_id)
#                 request.session_data = session_data
#                 request.user_profile_id = session_data.get('user_id')
#                 return None

#         # No valid authentication found
#         if has_auth_attempt:
#             # User tried to authenticate but failed - session validation error
#             return self._session_validation_error()
#         else:
#             # No authentication attempt - basic authentication error
#             return self._authentication_required_error()

#     def _handle_jwt_renewal(self, request, expired_token):
#         """
#         Handle JWT renewal when token is expired but session is still valid.
#         Returns True if renewal was successful, False otherwise.
#         """
#         try:
#             import jwt
#             from rest_framework_simplejwt.tokens import RefreshToken

#             # Try to decode the expired token without verification to get payload
#             try:
#                 payload = jwt.decode(expired_token, options={"verify_signature": False, "verify_exp": False})
#                 token_session_id = payload.get('sid')
#                 user_id = payload.get('user_id')

#                 if not token_session_id:

#                     return False

#                 # Check if the associated session is still valid
#                 session_data = self.session_manager.get_session(token_session_id)
#                 if not session_data or not session_data.get('is_active', False):

#                     return False

#                 # Session is valid - generate new JWT tokens
#                 from accounts.models import User
#                 try:
#                     # Get user from session data
#                     user_profile_id = session_data.get('user_id')
#                     if not user_profile_id:

#                         return False

#                     # Find the Django User associated with this profile
#                     from accounts.models import UserProfile
#                     user_profile = UserProfile.objects.get(id=user_profile_id)
#                     django_user = user_profile.user

#                     # Generate new JWT tokens
#                     refresh = RefreshToken.for_user(django_user)
#                     # Add session ID to the new token
#                     refresh.payload['sid'] = token_session_id
#                     new_access_token = refresh.access_token
#                     new_access_token.payload['sid'] = token_session_id

#                     # Smart renew session if needed
#                     self.session_manager.smart_renew_session_if_needed(
#                         token_session_id)

#                     # Set up request context
#                     request.session_data = session_data
#                     request.user_profile_id = user_profile_id
#                     request._jwt_session_to_set = token_session_id
#                     request._new_jwt_token = str(new_access_token)
#                     request._new_refresh_token = str(refresh)

#                     # IMPORTANT: Update the Authorization header with the new token
#                     # so that DRF's JWT authentication can use it
#                     request.META['HTTP_AUTHORIZATION'] = f'Bearer {str(new_access_token)}'

#                     return True

#                 except Exception as e:

#                     return False

#             except Exception as e:

#                 return False

#         except Exception as e:

#             return False

#     def _session_validation_error(self):
#         """
#         Return session validation error for users who were authenticated
#         but their session/JWT expired or became invalid.
#         """
#         return JsonResponse({
#             'error': 'Session expired',
#             'detail': 'Your session has expired. Please refresh your token or log in again.',
#             'code': 'SESSION_EXPIRED',
#             'type': 'session_validation',
#             'redirect': '/login',
#             'suggestions': [
#                 'Try refreshing your access token',
#                 'Log out and log in again',
#                 'Clear your browser cache and cookies'
#             ]
#         }, status=401)

#     def _authentication_required_error(self):
#         """
#         Return authentication required error for users who haven't
#         provided any credentials.
#         """
#         return JsonResponse({
#             'error': 'Authentication required',
#             'detail': 'You must be logged in to access this resource.',
#             'code': 'AUTHENTICATION_REQUIRED',
#             'type': 'authentication',
#             'redirect': '/login',
#             'suggestions': [
#                 'Log in to your account',
#                 'Create an account if you don\'t have one',
#                 'Check if this resource requires authentication'
#             ]
#         }, status=401)

#     def process_response(self, request, response):
#         """
#         Handle response processing - set session cookies and JWT renewal headers when needed.
#         """
#         # If JWT authentication found a session to set, add it to response
#         if hasattr(request, '_jwt_session_to_set'):
#             session_id = request._jwt_session_to_set
#             # Set session cookie (httponly, secure in production)
#             response.set_cookie(
#                 'sessionid',
#                 session_id,
#                 max_age=SESSION_DURATION_SECONDS,
#                 httponly=True,
#                 secure=getattr(settings, 'SESSION_COOKIE_SECURE', False),
#                 samesite='Lax'
#             )

#         # If JWT was renewed, add new tokens to response headers
#         if hasattr(request, '_new_jwt_token'):
#             response['X-New-Access-Token'] = request._new_jwt_token
#             response['X-JWT-Renewed'] = 'true'

#         if hasattr(request, '_new_refresh_token'):
#             response['X-New-Refresh-Token'] = request._new_refresh_token

#         return response


# class SessionActivityMiddleware(MiddlewareMixin):
#     """
#     Efficient session extension middleware with periodic checking.
#     - Checks sessions every 15 minutes to minimize overhead
#     - Extends sessions if they have less than 30 minutes remaining
#     - Adds X-Session-Extended header when session is extended
#     """

#     def __init__(self, get_response):
#         super().__init__(get_response)
#         self.session_manager = SessionManager()

#     def process_request(self, request):
#         """
#         Periodically check and extend sessions to minimize overhead.
#         """
#         if hasattr(request, 'session_data'):
#             session_id = request.session.session_key
#             if session_id:
#                 # Smart renew session if needed (lightweight Redis operation)
#                 self.session_manager.smart_renew_session_if_needed(session_id)

#                 # Periodic check for extension (every 15 minutes)
#                 extended = self._periodic_session_check(session_id)
#                 if extended:
#                     request._session_extended = True

#         return None

#     def _periodic_session_check(self, session_id):
#         """
#         Check session extension needs periodically (every 15 minutes).
#         Extend if session has less than 30 minutes remaining.
#         Returns True if session was extended.
#         """
#         try:
#             import time
#             import redis

#             # Use Redis directly instead of Django cache
#             r = redis.Redis(host='redis', port=6379, db=0)

#             cache_key = f"session_last_checked:{session_id}"
#             now = time.time()

#             # Get last check time from Redis
#             last_checked_bytes = r.get(cache_key)
#             last_checked = (
#                 float(last_checked_bytes.decode()) if last_checked_bytes else 0
#             )

#             # Only check based on configured frequency
#             check_frequency = getattr(
#                 settings, 'SESSION_EXTENSION_CHECK_FREQUENCY_SECONDS', 900
#             )
#             if now - last_checked < check_frequency:
#                 return False

#             # Update last check time in Redis
#             r.setex(cache_key, 3600, str(now))  # Cache for 1 hour

#             # Get session creation time from Redis
#             session_cache_key = f"session_created:{session_id}"
#             created_time_bytes = r.get(session_cache_key)
#             created_time = (
#                 float(created_time_bytes.decode()) if created_time_bytes else None
#             )

#             if not created_time:
#                 # Session not in Redis cache, get from Redis/DB and cache it
#                 session_data = self.session_manager.get_session(session_id)
#                 if session_data and 'created_at' in session_data:
#                     created_at = session_data['created_at']
#                     if isinstance(created_at, str):
#                         from datetime import datetime
#                         created_dt = datetime.fromisoformat(
#                             created_at.replace('Z', '+00:00')
#                         )
#                         created_time = created_dt.timestamp()
#                     else:
#                         created_time = created_at

#                     # Cache creation time in Redis
#                     r.setex(session_cache_key, 14400, str(created_time))
#                 else:
#                     return False

#             # Calculate remaining session time
#             session_duration = (
#                 getattr(settings, 'SESSION_DURATION_HOURS', 4) * 3600
#             )
#             session_age = now - created_time
#             remaining_time = session_duration - session_age

#             # Extend if less than configured threshold remaining
#             extension_threshold = getattr(
#                 settings, 'SESSION_EXTENSION_THRESHOLD_SECONDS', 1800
#             )
#             if remaining_time < extension_threshold:
#                 self.session_manager.smart_renew_session_if_needed(session_id)
#                 # Update creation time in Redis to reflect extension
#                 r.setex(session_cache_key, 14400, str(now))
#                 return True  # Session was extended

#             return False  # Session was not extended

#         except Exception as e:
#             print(f"Periodic session check error: {e}")
#             return False

#     def process_response(self, request, response):
#         """
#         Add session extension header if session was extended.
#         """
#         if getattr(request, '_session_extended', False):
#             response['X-Session-Extended'] = 'true'

#         return response

# class JWTAutoRenewMiddleware(MiddlewareMixin):
#     """
#     DEPRECATED: This middleware functionality has been consolidated into
#     core.middleware.optimized_auth_middleware.OptimizedAuthenticationMiddleware

#     Legacy JWT renewal middleware with periodic checking.
#     - Checks JWT every 2 minutes to ensure tokens don't expire
#     - Renews tokens if they have less than 2 minutes remaining
#     """

#     exempt_urls = [
#         '/api/auth/login/',
#         '/api/auth/register/',
#         '/api/auth/verify/',  # Email verification
#         '/api/auth/resend-code/',  # Resend verification code
#         '/api/auth/request-verification/',  # Request verification
#         '/api/auth/register-professional/',
#         '/api/auth/verification-status/',  # Verification status check
#         '/api/auth/logout/',
#         '/api/auth/login-with-verification-check/',
#         '/api/auth/login/',
#         '/api/auth/refresh/',
#         '/api/auth/logout/',
#         '/api/auth/register/',
#         '/api/auth/user-info/',
#         '/api/auth/verify/',
#         '/api/auth/login/',
#         '/api/auth/token/',
#         '/api/auth/token/refresh/',
#         '/auth/login/',
#         '/auth/register/',
#         '/auth/logout/',
#         '/auth/token/refresh/',
#         '/admin/login/',
#         '/api/health/',
#         '/static/',
#         '/media/',
#     ]

#     def __init__(self, get_response):
#         super().__init__(get_response)

#     def process_request(self, request):
#         """
#         Periodically check and renew JWT tokens to prevent expiration.
#         """
#         # Skip exempt URLs
#         if any(request.path.startswith(url) for url in self.exempt_urls):
#             return None

#         # Get JWT from header
#         auth_header = request.META.get('HTTP_AUTHORIZATION', '')
#         if not auth_header.startswith('Bearer '):
#             return None

#         token = auth_header[7:]  # Remove 'Bearer ' prefix

#         # Periodic JWT check (every 2 minutes)
#         self._periodic_jwt_check(request, token)

#         return None

#     def _periodic_jwt_check(self, request, token):
#         """
#         Check JWT renewal needs periodically (every 2 minutes).
#         Renew if token has less than 2 minutes remaining.
#         """
#         try:
#             import time
#             from django.core.cache import cache
#             from rest_framework_simplejwt.tokens import UntypedToken
#             from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

#             # Use token hash as unique identifier
#             import hashlib
#             token_hash = hashlib.md5(token.encode()).hexdigest()
#             cache_key = f"jwt_last_checked:{token_hash}"

#             now = time.time()
#             last_checked = cache.get(cache_key, 0)

#             # Only check based on configured frequency
#             check_frequency = getattr(settings, 'JWT_RENEWAL_CHECK_FREQUENCY_SECONDS', 120)
#             if now - last_checked < check_frequency:
#                 return

#             # Update last check time
#             cache.set(cache_key, now, timeout=600)  # Cache for 10 minutes

#             # Validate and check token expiration
#             try:
#                 untyped_token = UntypedToken(token)
#                 exp_timestamp = untyped_token['exp']

#                 # Check if token expires within configured threshold
#                 renewal_threshold = getattr(settings, 'JWT_RENEWAL_THRESHOLD_SECONDS', 120)
#                 time_until_expiry = exp_timestamp - now

#                 if time_until_expiry < renewal_threshold:
#                     # Token needs renewal - add header for frontend
#                     request._jwt_renewal_needed = True

#             except (InvalidToken, TokenError, KeyError):
#                 # Invalid or malformed token - let other middleware handle
#                 pass

#         except Exception as e:
#             print(f"Periodic JWT check error: {e}")

#     def process_response(self, request, response):
#         """
#         Add renewal header if JWT needs renewal.
#         """
#         if getattr(request, '_jwt_renewal_needed', False):
#             response['X-JWT-Renewal-Needed'] = 'true'

#         return response
