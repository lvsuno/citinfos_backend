"""
Real-time counter management for likes, dislikes, and shares.
Best practices implementation.
"""
from django.db import transaction
from django.db.models import F
from django.contrib.contenttypes.models import ContentType
from .models import Post, Comment, Like, Dislike, DirectShare


class RealTimeCounterManager:
    """
    Manages real-time counter updates for content interactions.

    This approach provides:
    1. Immediate UI feedback
    2. Data consistency
    3. Race condition protection
    4. Atomic operations
    """

    @staticmethod
    def increment_like_count(content_object):
        """
        Atomically increment like count using F() expressions.
        This prevents race conditions in high-traffic scenarios.
        """
        with transaction.atomic():
            content_object.__class__.objects.filter(
                pk=content_object.pk
            ).update(
                likes_count=F('likes_count') + 1
            )
            # Refresh the object to get updated count
            content_object.refresh_from_db(fields=['likes_count'])

    @staticmethod
    def decrement_like_count(content_object):
        """Atomically decrement like count."""
        with transaction.atomic():
            content_object.__class__.objects.filter(
                pk=content_object.pk,
                likes_count__gt=0  # Prevent negative counts
            ).update(
                likes_count=F('likes_count') - 1
            )
            content_object.refresh_from_db(fields=['likes_count'])

    @staticmethod
    def increment_dislike_count(content_object):
        """Atomically increment dislike count."""
        with transaction.atomic():
            content_object.__class__.objects.filter(
                pk=content_object.pk
            ).update(
                dislikes_count=F('dislikes_count') + 1
            )
            content_object.refresh_from_db(fields=['dislikes_count'])

    @staticmethod
    def decrement_dislike_count(content_object):
        """Atomically decrement dislike count."""
        with transaction.atomic():
            content_object.__class__.objects.filter(
                pk=content_object.pk,
                dislikes_count__gt=0
            ).update(
                dislikes_count=F('dislikes_count') - 1
            )
            content_object.refresh_from_db(fields=['dislikes_count'])

    @staticmethod
    def increment_share_count(post):
        """Atomically increment share count."""
        with transaction.atomic():
            Post.objects.filter(
                pk=post.pk
            ).update(
                shares_count=F('shares_count') + 1
            )
            post.refresh_from_db(fields=['shares_count'])

    @staticmethod
    def handle_like_action(user_profile, content_object):
        """
        Handle like/unlike action with real-time counter updates.
        Returns (like_object, created, action_taken)
        """
        content_type = ContentType.objects.get_for_model(content_object)

        with transaction.atomic():
            like, created = Like.objects.get_or_create(
                user=user_profile,
                content_type=content_type,
                object_id=content_object.id,
                defaults={'is_deleted': False}
            )

            if created:
                # New like
                RealTimeCounterManager.increment_like_count(content_object)
                return like, True, "liked"
            else:
                if like.is_deleted:
                    # Reactivate deleted like
                    like.is_deleted = False
                    like.save()
                    RealTimeCounterManager.increment_like_count(content_object)
                    return like, False, "liked"
                else:
                    # Remove existing like (soft delete)
                    like.is_deleted = True
                    like.save()
                    RealTimeCounterManager.decrement_like_count(content_object)
                    return like, False, "unliked"

    @staticmethod
    def handle_dislike_action(user_profile, content_object):
        """
        Handle dislike/undislike action with real-time counter updates.
        Returns (dislike_object, created, action_taken)
        """
        content_type = ContentType.objects.get_for_model(content_object)

        with transaction.atomic():
            dislike, created = Dislike.objects.get_or_create(
                user=user_profile,
                content_type=content_type,
                object_id=content_object.id,
                defaults={'is_deleted': False}
            )

            if created:
                # New dislike
                RealTimeCounterManager.increment_dislike_count(content_object)
                return dislike, True, "disliked"
            else:
                if dislike.is_deleted:
                    # Reactivate deleted dislike
                    dislike.is_deleted = False
                    dislike.save()
                    RealTimeCounterManager.increment_dislike_count(content_object)
                    return dislike, False, "disliked"
                else:
                    # Remove existing dislike (soft delete)
                    dislike.is_deleted = True
                    dislike.save()
                    RealTimeCounterManager.decrement_dislike_count(content_object)
                    return dislike, False, "undisliked"


# Signal-based approach (alternative/complementary)
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Like)
def update_like_count_on_save(sender, instance, created, **kwargs):
    """Update like count when Like object is saved."""
    if created and not instance.is_deleted:
        # New active like
        RealTimeCounterManager.increment_like_count(instance.content_object)
    elif not created:
        # Existing like updated - check if status changed
        if instance.is_deleted:
            RealTimeCounterManager.decrement_like_count(instance.content_object)


@receiver(post_save, sender=Dislike)
def update_dislike_count_on_save(sender, instance, created, **kwargs):
    """Update dislike count when Dislike object is saved."""
    if created and not instance.is_deleted:
        RealTimeCounterManager.increment_dislike_count(instance.content_object)
    elif not created:
        if instance.is_deleted:
            RealTimeCounterManager.decrement_dislike_count(instance.content_object)
