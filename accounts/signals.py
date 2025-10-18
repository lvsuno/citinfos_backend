"""Signals to maintain cached counters for UserProfile and trigger badge evaluations."""
import logging
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import F
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import UserProfile, UserEvent

logger = logging.getLogger(__name__)

try:
    from communities.models import CommunityMembership
except Exception:
    CommunityMembership = None

# Helper

def _inc(profile: UserProfile, field: str, delta: int):
    # For negative deltas, ensure we don't go below 0
    if delta < 0:
        current_value = getattr(profile, field)
        if current_value + delta < 0:
            # Set directly to 0 instead of allowing negative
            UserProfile.objects.filter(id=profile.id).update(**{field: 0})
            return

    UserProfile.objects.filter(id=profile.id).update(**{field: F(field) + delta})
    refreshed = UserProfile.objects.only('id', field).get(id=profile.id)
    if getattr(refreshed, field) < 0:
        setattr(refreshed, field, 0)
        refreshed.save(update_fields=[field])

def _trigger_badge_evaluation(profile):
    """Trigger badge evaluation for a user profile."""
    try:
        from .badge_triggers import trigger_badge_evaluation
        # Run badge evaluation in a separate transaction to avoid conflicts
        transaction.on_commit(
            lambda: trigger_badge_evaluation(profile, 'signal_trigger', async_evaluation=True, delay_seconds=2)
        )
    except Exception:
        # Fail silently to not break the main functionality
        pass

def _log_user_event(user, event_type, metadata=None):
    """Log a user event for badge tracking."""
    try:
        from .models import UserEvent
        UserEvent.objects.create(
            user=user,
            event_type=event_type,
            metadata=metadata or {}
        )
    except Exception:
        # Fail silently to not break the main functionality
        pass

# User model changes should update UserProfile.updated_at
@receiver(post_save, sender=User)
def user_updated(sender, instance, created, **kwargs):  # noqa: ARG001
    """Create UserProfile when User is created and update UserProfile.updated_at when User model is saved."""
    if created:
        # Create UserProfile for new users (no registration_index yet)
        from datetime import date
        from django.db import transaction

        try:
            with transaction.atomic():
                profile, created_profile = UserProfile.objects.get_or_create(
                    user=instance,
                    defaults={
                        'registration_index': 0,  # Will be assigned on verification
                        'date_of_birth': date(2000, 1, 1),  # Default placeholder date
                    }
                )
                if not created_profile:
                    # Profile already exists, this is fine for registration flows
                    pass
        except Exception as e:
            # Log the error but don't crash the user creation
            import logging
            logger = logging.getLogger('accounts')
            logger.error(f"Error creating UserProfile for user {instance.id}: {e}")
            # Don't re-raise the exception to avoid breaking user creation
    elif hasattr(instance, 'profile'):
        try:
            # Update the profile's updated_at field
            UserProfile.objects.filter(id=instance.profile.id).update(
                updated_at=timezone.now()
            )
        except UserProfile.DoesNotExist:
            pass

# UserProfile creation - no longer assigns registration_index (moved to verification)
# Registration index is now assigned only when user verifies their account

# Verification code completion - assign registration_index AND evaluate early adopter badge
from accounts.models import VerificationCode

@receiver(post_save, sender=VerificationCode)
def assign_registration_index_on_verification(sender, instance, created, **kwargs):
    """Assign registration_index AND evaluate early adopter badge when user verifies."""

    if not created and instance.is_used and instance.user:
        # IMPORTANT: Refresh user verification status first
        instance.user.sync_verification_status()

        if instance.user.registration_index == 0 and instance.user.is_verified:
            # OPTIMIZATION: Queue combined registration index + badge evaluation
            try:
                from accounts.async_tasks import assign_index_and_evaluate_early_adopter_async
                # Pass UserProfile.id (UUID) not User.id (integer)
                task_result = assign_index_and_evaluate_early_adopter_async.delay(str(instance.id))
                logger.info(f"Queued registration index assignment task {task_result.id} for user {instance.user.id}")
            except Exception as e:
                logger.error(f"Failed to queue registration index assignment for user {instance.user.id}: {e}")
                # Fallback to synchronous assignment
                try:
                    from accounts.models import assign_registration_index
                    assign_registration_index(instance.user)
                except Exception as fallback_error:
                    logger.error(f"Fallback registration index assignment also failed for user {instance.user.id}: {fallback_error}")

# Post counting - including regular posts_count
@receiver(post_save, sender='content.Post')
def post_count_created(sender, instance, created, **kwargs):  # noqa: ARG001
    if created and instance.author_id:
        _inc(instance.author, 'posts_count', 1)

@receiver(post_delete, sender='content.Post')
def post_count_deleted(sender, instance, **kwargs):  # noqa: ARG001
    if instance.author_id:
        _inc(instance.author, 'posts_count', -1)

# Follow relationships - follower and following counts
@receiver(post_save, sender='accounts.Follow')
def follow_relationship_created(sender, instance, created, **kwargs):
    """Update follower/following counts when Follow status changes."""
    if instance.status == 'approved' and not instance.is_deleted:
        if created:
            _inc(instance.follower, 'following_count', 1)
            _inc(instance.followed, 'follower_count', 1)

@receiver(post_delete, sender='accounts.Follow')
def follow_relationship_deleted(sender, instance, **kwargs):
    """Update follower/following counts when Follow is deleted."""
    if instance.status == 'approved':
        _inc(instance.follower, 'following_count', -1)
        _inc(instance.followed, 'follower_count', -1)

# Polls
@receiver(post_save, sender='polls.Poll')
def poll_created(sender, instance, created, **kwargs):  # noqa: ARG001
    if created and instance.post and instance.post.author_id:
        _inc(instance.post.author, 'polls_created_count', 1)

@receiver(post_delete, sender='polls.Poll')
def poll_deleted(sender, instance, **kwargs):  # noqa: ARG001
    if instance.post and instance.post.author_id:
        _inc(instance.post.author, 'polls_created_count', -1)

@receiver(post_save, sender='polls.PollVote')
def poll_vote_created(sender, instance, created, **kwargs):  # noqa: ARG001
    if created and instance.voter_id:
        try:
            profile = instance.voter.profile
            _inc(profile, 'poll_votes_count', 1)
        except UserProfile.DoesNotExist:  # noqa: PERF203
            pass

@receiver(post_delete, sender='polls.PollVote')
def poll_vote_deleted(sender, instance, **kwargs):  # noqa: ARG001
    if instance.voter_id:
        try:
            profile = instance.voter.profile
            _inc(profile, 'poll_votes_count', -1)
        except UserProfile.DoesNotExist:  # noqa: PERF203
            pass

# Reactions (replacing Like/Dislike)
@receiver(post_save, sender='content.PostReaction')
def post_reaction_created(sender, instance, created, **kwargs):  # noqa: ARG001
    if created and instance.user_id:
        # Only count positive reactions for likes_given_count
        from content.models import PostReaction
        if instance.reaction_type in PostReaction.POSITIVE_REACTIONS:
            _inc(instance.user, 'likes_given_count', 1)
            _log_user_event(instance.user.user, 'REACTION_GIVEN', {
                'target_type': 'post',
                'target_id': str(instance.post_id),
                'reaction_type': instance.reaction_type
            })
            _trigger_badge_evaluation(instance.user)

@receiver(post_delete, sender='content.PostReaction')
def post_reaction_deleted(sender, instance, **kwargs):  # noqa: ARG001
    if instance.user_id:
        # Only decrement for positive reactions
        from content.models import PostReaction
        if instance.reaction_type in PostReaction.POSITIVE_REACTIONS:
            _inc(instance.user, 'likes_given_count', -1)

# Comments
@receiver(post_save, sender='content.Comment')
def comment_created(sender, instance, created, **kwargs):  # noqa: ARG001
    if created and instance.author_id:
        _inc(instance.author, 'comments_made_count', 1)
        _log_user_event(instance.author.user, 'COMMENT_CREATED', {
            'comment_id': instance.id,
            'content_type': 'comment'
        })
        _trigger_badge_evaluation(instance.author)

@receiver(post_delete, sender='content.Comment')
def comment_deleted(sender, instance, **kwargs):  # noqa: ARG001
    if instance.author_id:
        _inc(instance.author, 'comments_made_count', -1)

# Posts - trigger badge evaluation for post creation
@receiver(post_save, sender='content.Post')
def post_created(sender, instance, created, **kwargs):  # noqa: ARG001
    if created and instance.author_id and instance.post_type != 'repost':
        _log_user_event(instance.author.user, 'POST_CREATED', {
            'post_id': instance.id,
            'post_type': instance.post_type
        })
        _trigger_badge_evaluation(instance.author)

# Reposts (now handled via Post model with post_type='repost')
@receiver(post_save, sender='content.Post')
def repost_created_via_post(sender, instance, created, **kwargs):  # noqa: ARG001
    if created and instance.post_type == 'repost' and instance.author_id:
        _inc(instance.author, 'reposts_count', 1)
        _log_user_event(instance.author.user, 'REPOST_CREATED', {
            'post_id': instance.id,
            'original_post_id': getattr(instance, 'original_post_id', None)
        })
        _trigger_badge_evaluation(instance.author)

@receiver(post_delete, sender='content.Post')
def post_deleted(sender, instance, **kwargs):  # noqa: ARG001
    if instance.post_type == 'repost' and instance.author_id:
        _inc(instance.author, 'reposts_count', -1)

# Direct shares (sent)
@receiver(post_save, sender='content.DirectShare')
def direct_share_created(sender, instance, created, **kwargs):  # noqa: ARG001
    if created and instance.sender_id:
        _inc(instance.sender, 'shares_sent_count', 1)

@receiver(post_delete, sender='content.DirectShare')
def direct_share_deleted(sender, instance, **kwargs):  # noqa: ARG001
    if instance.sender_id:
        _inc(instance.sender, 'shares_sent_count', -1)

# Direct share deliveries (received)
@receiver(post_save, sender='content.DirectShareRecipient')
def direct_share_delivery_created(sender, instance, created, **kwargs):  # noqa: ARG001
    if created and instance.recipient_id:
        _inc(instance.recipient, 'shares_received_count', 1)

@receiver(post_delete, sender='content.DirectShareRecipient')
def direct_share_delivery_deleted(sender, instance, **kwargs):  # noqa: ARG001
    if instance.recipient_id:
        _inc(instance.recipient, 'shares_received_count', -1)


# Best comments - track when comments are marked/unmarked as best
@receiver(post_save, sender='content.Comment')
def comment_best_status_changed(sender, instance, created, **kwargs):
    """Handle changes to comment best status."""
    if created:
        return  # Skip for new comments

    # Check if we have previous state tracking
    if not hasattr(instance, '_pre_save_is_best'):
        return  # Can't determine state change without previous state

    previous_is_best = instance._pre_save_is_best
    current_is_best = instance.is_best

    if previous_is_best != current_is_best:
        if current_is_best and not previous_is_best:
            # Comment was marked as best
            _inc(instance.author, 'best_comments_count', 1)
            _log_user_event(instance.author.user, 'COMMENT_MARKED_BEST', {
                'comment_id': instance.id
            })
            _trigger_badge_evaluation(instance.author)
        elif previous_is_best and not current_is_best:
            # Comment was unmarked as best
            _inc(instance.author, 'best_comments_count', -1)

@receiver(pre_save, sender='content.Comment')
def capture_comment_best_status(sender, instance, **kwargs):
    """Capture previous is_best status for comparison."""
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
        instance._pre_save_is_best = getattr(old, 'is_best', False)
    except (sender.DoesNotExist,
            transaction.TransactionManagementError,
            IntegrityError):
        instance._pre_save_is_best = False

if CommunityMembership:
    @receiver(post_save, sender=CommunityMembership)
    def update_communities_joined_on_create(sender, instance, created, **kwargs):
        if not created:
            return
        # Consider only active/approved memberships counting toward join count
        active_statuses = {getattr(sender, 'STATUS_ACTIVE', 'active'), getattr(sender, 'STATUS_APPROVED', 'approved')}
        status_value = getattr(instance, 'status', None)
        if status_value is None or status_value in active_statuses:
            profile = getattr(instance.user, 'profile', None)
            if profile:
                UserProfile.objects.filter(pk=profile.pk).update(
                    communities_joined_count=F('communities_joined_count') + 1
                )

    @receiver(post_save, sender=CommunityMembership)
    def update_communities_joined_on_status_change(sender, instance, created, **kwargs):
        if created:
            return  # handled above
        # Detect status field changes; requires tracking previous value if model provides it
        if not hasattr(instance, '_pre_save_status'):
            return
        old = instance._pre_save_status
        new = getattr(instance, 'status', None)
        if old == new:
            return
        active_statuses = {getattr(sender, 'STATUS_ACTIVE', 'active'), getattr(sender, 'STATUS_APPROVED', 'approved')}
        profile = getattr(instance.user, 'profile', None)
        if not profile:
            return
        # Transition into active -> increment; transition out of active -> decrement
        became_active = old not in active_statuses and new in active_statuses
        lost_active = old in active_statuses and new not in active_statuses
        if became_active:
            UserProfile.objects.filter(pk=profile.pk).update(
                communities_joined_count=F('communities_joined_count') + 1
            )
        elif lost_active:
            UserProfile.objects.filter(pk=profile.pk).update(
                communities_joined_count=F('communities_joined_count') - 1
            )

    @receiver(post_delete, sender=CommunityMembership)
    def update_communities_joined_on_delete(sender, instance, **kwargs):
        active_statuses = {getattr(sender, 'STATUS_ACTIVE', 'active'), getattr(sender, 'STATUS_APPROVED', 'approved')}
        status_value = getattr(instance, 'status', None)
        if status_value is None or status_value in active_statuses:
            profile = getattr(instance.user, 'profile', None)
            if profile:
                UserProfile.objects.filter(pk=profile.pk).update(
                    communities_joined_count=F('communities_joined_count') - 1
                )

    @receiver(pre_save, sender=CommunityMembership)
    def capture_prev_status(sender, instance, **kwargs):
        if not instance.pk:
            return
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._pre_save_status = getattr(old, 'status', None)
        except (sender.DoesNotExist,
                transaction.TransactionManagementError,
                IntegrityError):
            # Handle DoesNotExist and database transaction errors gracefully
            instance._pre_save_status = None
