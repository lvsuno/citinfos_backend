"""
Django signals for automatic content moderation and real-time notifications.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Post, Comment, Like
from .utils import process_content_for_moderation, process_content_for_bot_detection, is_user_blocked_as_bot


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

@receiver(post_save, sender=Like)
def send_like_notification(sender, instance, created, **kwargs):
    """Send real-time notification when someone likes a post."""
    if created:
        try:
            from notifications.realtime import send_post_interaction_notification

            # Get the post author
            if hasattr(instance.content_object, 'author'):
                post_author = instance.content_object.author

                # Don't send notification for self-likes
                if post_author != instance.user:
                    send_post_interaction_notification(
                        post_author=post_author,
                        actor_profile=instance.user,
                        interaction_type='like',
                        post_id=str(instance.content_object.id)
                    )
        except Exception as e:
            print(f"Error sending like notification: {str(e)}")


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
