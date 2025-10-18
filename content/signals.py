"""
Django signals for automatic content moderation and real-time notifications.
"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Post, Comment, PostReaction, CommentReaction, PostMedia
from .utils import (
    process_content_for_moderation,
    process_content_for_bot_detection,
    is_user_blocked_as_bot
)


@receiver(pre_save, sender=Post)
def check_bot_before_post(sender, instance, **kwargs):
    """Check for bot behavior before allowing post creation."""
    if not instance.pk:  # Only for new posts
        # Check if user is blocked as bot
        if is_user_blocked_as_bot(instance.author):
            raise ValidationError("Account has been flagged as automated and cannot post content.")


@receiver(pre_save, sender=Comment)
def check_bot_before_comment(sender, instance, **kwargs):
    """Check for bot behavior before allowing comment creation."""
    if not instance.pk:  # Only for new comments
        # Check if user is blocked as bot
        if is_user_blocked_as_bot(instance.author):
            raise ValidationError("Account has been flagged as automated and cannot post content.")


@receiver(post_save, sender=Post)
def auto_moderate_post(sender, instance, created, **kwargs):
    """Automatically moderate new posts."""
    if created and instance.content:
        # Process the post for moderation in the background
        # In a production environment, you'd want to use Celery or similar
        try:
            # Regular content moderation
            moderation_result = process_content_for_moderation(instance)

            # Bot detection
            bot_result = process_content_for_bot_detection(instance)

            # Process mentions and hashtags
            from .utils import process_post_content
            content_result = process_post_content(instance)

            # Log the results (you could use proper logging here)
            analyses_count = len(moderation_result['analyses'])
            actions_count = len(moderation_result['actions'])
            print(f"Post {instance.id} moderation: {analyses_count} analyses, "
                  f"{actions_count} actions, "
                  f"requires_review: {moderation_result['requires_review']}")

            if content_result:
                mentions_count = len(content_result.get('mentions', []))
                hashtags_count = len(content_result.get('hashtags', []))
                print(f"Post {instance.id} processed: {mentions_count} mentions, "
                      f"{hashtags_count} hashtags")

            if bot_result['bot_detected']:
                print(f"Post {instance.id} bot detection: "
                      f"{bot_result['events']}")
                if bot_result.get('blocked'):
                    print(f"User {instance.author.user.username} "
                          f"blocked as bot")

        except Exception as e:
            # Log error but don't fail the post creation
            print(f"Error moderating post {instance.id}: {str(e)}")


@receiver(post_save, sender=Comment)
def auto_moderate_comment(sender, instance, created, **kwargs):
    """Automatically moderate new comments."""
    if created and instance.content:
        # Process the comment for moderation in the background
        try:
            # Regular content moderation
            moderation_result = process_content_for_moderation(instance)

            # Bot detection
            bot_result = process_content_for_bot_detection(instance)

            # Log the results
            print(f"Comment {instance.id} moderation: {len(moderation_result['analyses'])} analyses, "
                  f"{len(moderation_result['actions'])} actions, "
                  f"requires_review: {moderation_result['requires_review']}")

            if bot_result['bot_detected']:
                print(f"Comment {instance.id} bot detection: {bot_result['events']}")
                if bot_result.get('blocked'):
                    print(f"User {instance.author.user.username} blocked as bot")

        except Exception as e:
            # Log error but don't fail the comment creation
            print(f"Error moderating comment {instance.id}: {str(e)}")


# =============================================================================
# REAL-TIME NOTIFICATION SIGNALS
# =============================================================================

@receiver(post_save, sender=PostReaction)
def send_post_reaction_notification(sender, instance, created, **kwargs):
    """Send real-time notification when someone reacts to a post."""
    if created:
        try:
            from notifications.realtime import send_post_interaction_notification

            # Get the post author
            post_author = instance.post.author

            # Don't send notification for self-reactions
            if post_author != instance.user:
                # Get emoji for the reaction type
                emoji = dict(PostReaction.REACTION_TYPES).get(instance.reaction_type, '')

                send_post_interaction_notification(
                    post_author=post_author,
                    actor_profile=instance.user,
                    interaction_type='reaction',
                    post_id=str(instance.post.id),
                    reaction_type=instance.reaction_type,
                    reaction_emoji=emoji
                )
        except Exception as e:
            print(f"Error sending post reaction notification: {str(e)}")


@receiver(post_save, sender=CommentReaction)
def send_comment_reaction_notification(sender, instance, created, **kwargs):
    """Send real-time notification when someone reacts to a comment."""
    if created:
        try:
            from notifications.realtime import send_post_interaction_notification

            # Get the comment author
            comment_author = instance.comment.author

            # Don't send notification for self-reactions
            if comment_author != instance.user:
                # Get emoji for the reaction type
                emoji = dict(CommentReaction.REACTION_TYPES).get(instance.reaction_type, '')

                send_post_interaction_notification(
                    post_author=comment_author,
                    actor_profile=instance.user,
                    interaction_type='comment_reaction',
                    post_id=str(instance.comment.post.id),
                    comment_id=str(instance.comment.id),
                    reaction_type=instance.reaction_type,
                    reaction_emoji=emoji
                )
        except Exception as e:
            print(f"Error sending comment reaction notification: {str(e)}")


@receiver(post_save, sender=Comment)
def send_comment_notification(sender, instance, created, **kwargs):
    """Send real-time notification when someone comments on a post."""
    if created:
        try:
            from notifications.realtime import send_post_interaction_notification

            # Get the post author
            if hasattr(instance.post, 'author'):
                post_author = instance.post.author

                # Don't send notification for self-comments
                if post_author != instance.author:
                    send_post_interaction_notification(
                        post_author=post_author,
                        actor_profile=instance.author,
                        interaction_type='comment',
                        post_id=str(instance.post.id)
                    )
        except Exception as e:
            print(f"Error sending comment notification: {str(e)}")


@receiver(post_save, sender=Post)
def send_repost_notification(sender, instance, created, **kwargs):
    """Send real-time notification for reposts."""
    if created and instance.post_type in ['repost', 'repost_with_media', 'repost_quote']:
        try:
            from notifications.realtime import send_post_interaction_notification

            # Get the original post author
            if instance.original_post and instance.original_post.author:
                original_author = instance.original_post.author

                # Don't send notification for self-reposts
                if original_author != instance.author:
                    send_post_interaction_notification(
                        post_author=original_author,
                        actor_profile=instance.author,
                        interaction_type='repost',
                        post_id=str(instance.original_post.id)
                    )
        except Exception as e:
            print(f"Error sending repost notification: {str(e)}")


# =============================================================================
# REACTION COUNTER UPDATE SIGNALS
# =============================================================================


@receiver(post_save, sender=PostReaction)
def update_post_reaction_counts_on_save(sender, instance, created, **kwargs):
    """Update post likes_count and dislikes_count when reaction is created or updated."""
    post = instance.post

    # Recalculate counts based on reaction sentiment
    positive_count = PostReaction.objects.filter(
        post=post,
        reaction_type__in=PostReaction.POSITIVE_REACTIONS,
        is_deleted=False
    ).count()

    negative_count = PostReaction.objects.filter(
        post=post,
        reaction_type__in=PostReaction.NEGATIVE_REACTIONS,
        is_deleted=False
    ).count()

    # Update the cached counts
    post.likes_count = positive_count
    post.dislikes_count = negative_count
    post.save(update_fields=['likes_count', 'dislikes_count'])


@receiver(post_delete, sender=PostReaction)
def update_post_reaction_counts_on_delete(sender, instance, **kwargs):
    """Update post likes_count and dislikes_count when reaction is deleted."""
    post = instance.post

    # Recalculate counts
    positive_count = PostReaction.objects.filter(
        post=post,
        reaction_type__in=PostReaction.POSITIVE_REACTIONS,
        is_deleted=False
    ).count()

    negative_count = PostReaction.objects.filter(
        post=post,
        reaction_type__in=PostReaction.NEGATIVE_REACTIONS,
        is_deleted=False
    ).count()

    # Update the cached counts
    post.likes_count = positive_count
    post.dislikes_count = negative_count
    post.save(update_fields=['likes_count', 'dislikes_count'])


@receiver(post_save, sender=CommentReaction)
def update_comment_reaction_counts_on_save(sender, instance, created, **kwargs):
    """Update comment likes_count and dislikes_count when reaction is created or updated."""
    comment = instance.comment

    # Recalculate counts based on reaction sentiment
    positive_count = CommentReaction.objects.filter(
        comment=comment,
        reaction_type__in=CommentReaction.POSITIVE_REACTIONS,
        is_deleted=False
    ).count()

    negative_count = CommentReaction.objects.filter(
        comment=comment,
        reaction_type__in=CommentReaction.NEGATIVE_REACTIONS,
        is_deleted=False
    ).count()

    # Update the cached counts
    comment.likes_count = positive_count
    comment.dislikes_count = negative_count
    comment.save(update_fields=['likes_count', 'dislikes_count'])


@receiver(post_delete, sender=CommentReaction)
def update_comment_reaction_counts_on_delete(sender, instance, **kwargs):
    """Update comment likes_count and dislikes_count when reaction is deleted."""
    comment = instance.comment

    # Recalculate counts
    positive_count = CommentReaction.objects.filter(
        comment=comment,
        reaction_type__in=CommentReaction.POSITIVE_REACTIONS,
        is_deleted=False
    ).count()

    negative_count = CommentReaction.objects.filter(
        comment=comment,
        reaction_type__in=CommentReaction.NEGATIVE_REACTIONS,
        is_deleted=False
    ).count()

    # Update the cached counts
    comment.likes_count = positive_count
    comment.dislikes_count = negative_count
    comment.save(update_fields=['likes_count', 'dislikes_count'])


@receiver(post_save, sender=PostMedia)
def auto_generate_video_thumbnail(sender, instance, created, **kwargs):
    """
    Automatically generate thumbnail for video uploads.
    Only runs for newly created PostMedia with video type and uploaded file.
    """
    if (
        created and
        instance.media_type == "video" and
        instance.file and
        not instance.thumbnail and
        not instance.external_url  # Only for uploaded files
    ):
        # Generate thumbnail asynchronously to avoid blocking
        try:
            instance.generate_video_thumbnail(at_second=1)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Failed to auto-generate thumbnail for video {instance.id}: {e}"
            )

