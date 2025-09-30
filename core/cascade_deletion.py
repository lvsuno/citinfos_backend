"""
Cascading soft deletion utilities for maintaining referential integrity.

This module provides utilities to automatically soft-delete related objects
when a parent object is soft-deleted, maintaining data consistency.
"""

from django.utils import timezone
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
import logging

logger = logging.getLogger(__name__)


def cascade_soft_delete_post(post_instance):
    """
    Cascade soft deletion for a post and all its related objects.
    Returns the number of objects that were soft deleted.
    """
    from django.contrib.contenttypes.models import ContentType
    from django.utils import timezone
    from content.models import Comment, Like, Dislike

    if post_instance.is_deleted:
        logger.info(f"Post {post_instance.id} is already soft deleted")
        return 0

    deleted_count = 0
    post_content_type = ContentType.objects.get_for_model(post_instance)
    current_time = timezone.now()

    with transaction.atomic():
        # Soft delete the post itself
        post_instance.is_deleted = True
        post_instance.save()
        deleted_count += 1
        logger.info(f"Soft deleted post {post_instance.id}")

        # Soft delete all comments on this post
        comments = Comment.objects.filter(
            post=post_instance,
            is_deleted=False
        )
        comments_count = comments.update(
            is_deleted=True,
            deleted_at=current_time
        )
        if comments_count > 0:
            deleted_count += comments_count
            logger.info(f"Soft deleted {comments_count} comments")

        # Soft delete all likes on this post (using GenericForeignKey)
        likes = Like.objects.filter(
            content_type=post_content_type,
            object_id=post_instance.id,
            is_deleted=False
        )
        likes_count = likes.update(
            is_deleted=True,
            deleted_at=current_time
        )
        if likes_count > 0:
            deleted_count += likes_count
            logger.info(f"Soft deleted {likes_count} likes")

        # Soft delete all dislikes on this post (using GenericForeignKey)
        dislikes = Dislike.objects.filter(
            content_type=post_content_type,
            object_id=post_instance.id,
            is_deleted=False
        )
        dislikes_count = dislikes.update(
            is_deleted=True,
            deleted_at=current_time
        )
        if dislikes_count > 0:
            deleted_count += dislikes_count
            logger.info(f"Soft deleted {dislikes_count} dislikes")

        # Handle complex relationships
        try:
            # Soft delete PostHashtag relationships
            from content.models import PostHashtag
            post_hashtags = PostHashtag.objects.filter(
                post=post_instance, is_deleted=False
            )
            hashtag_count = post_hashtags.update(
                is_deleted=True,
                deleted_at=current_time
            )
            if hashtag_count > 0:
                deleted_count += hashtag_count
                logger.info(f"Soft deleted {hashtag_count} post hashtags")
        except Exception as e:
            logger.warning(f"Could not soft delete hashtags: {e}")

        try:
            # Soft delete Mentions in this post
            from content.models import Mention
            mentions = Mention.objects.filter(
                post=post_instance, is_deleted=False
            )
            mention_count = mentions.update(
                is_deleted=True,
                deleted_at=current_time
            )
            if mention_count > 0:
                deleted_count += mention_count
                logger.info(f"Soft deleted {mention_count} mentions")
        except Exception as e:
            logger.warning(f"Could not soft delete mentions: {e}")

        try:
            # Soft delete DirectShares of this post
            from content.models import DirectShare, DirectShareRecipient
            direct_shares = DirectShare.objects.filter(
                post=post_instance, is_deleted=False
            )
            for share in direct_shares:
                # Delete recipients first
                recipients = DirectShareRecipient.objects.filter(
                    direct_share=share, is_deleted=False
                )
                recipient_count = recipients.update(
                    is_deleted=True,
                    deleted_at=current_time
                )
                deleted_count += recipient_count

                # Delete the share itself
                share.is_deleted = True
                share.deleted_at = current_time
                share.save()
                deleted_count += 1
            logger.info(f"Soft deleted direct shares and recipients")
        except Exception as e:
            logger.warning(f"Could not soft delete direct shares: {e}")

        try:
            # Soft delete ContentReports for this post
            from content.models import ContentReport
            reports = ContentReport.objects.filter(
                content_type=post_content_type,
                object_id=post_instance.id,
                is_deleted=False
            )
            report_count = reports.update(
                is_deleted=True,
                deleted_at=current_time
            )
            if report_count > 0:
                deleted_count += report_count
                logger.info(f"Soft deleted {report_count} content reports")
        except Exception as e:
            logger.warning(f"Could not soft delete content reports: {e}")

        # Soft delete post attachments if they exist
        try:
            if hasattr(post_instance, 'attachments'):
                attachments = post_instance.attachments.filter(
                    is_deleted=False
                )
                attachments_count = attachments.update(
                    is_deleted=True,
                    deleted_at=current_time
                )
                if attachments_count > 0:
                    deleted_count += attachments_count
                    logger.info(f"Soft deleted {attachments_count} "
                              f"attachments")
        except Exception as e:
            logger.warning(f"Could not soft delete attachments: {e}")

        logger.info(f"Cascade deletion completed for post {post_instance.id}. "
                   f"Total objects affected: {deleted_count}")
        return deleted_count


def cascade_soft_delete_comment(comment_instance):
    """
    Cascade soft deletion for a comment and all its related objects.
    Returns the number of objects that were soft deleted.
    """
    from django.contrib.contenttypes.models import ContentType
    from django.utils import timezone as django_timezone
    from content.models import Like, Dislike, Comment

    if comment_instance.is_deleted:
        logger.info(f"Comment {comment_instance.id} is already soft deleted")
        return 0

    deleted_count = 0
    comment_content_type = ContentType.objects.get_for_model(comment_instance)
    current_time = django_timezone.now()

    with transaction.atomic():
        # Soft delete the comment itself
        comment_instance.is_deleted = True
        comment_instance.save()
        deleted_count += 1
        logger.info(f"Soft deleted comment {comment_instance.id}")

        # Soft delete all likes on this comment (using GenericForeignKey)
        likes = Like.objects.filter(
            content_type=comment_content_type,
            object_id=comment_instance.id,
            is_deleted=False
        )
        likes_count = likes.update(
            is_deleted=True,
            deleted_at=current_time
        )
        if likes_count > 0:
            deleted_count += likes_count
            logger.info(f"Soft deleted {likes_count} likes on comment")

        # Soft delete all dislikes on this comment (using GenericForeignKey)
        dislikes = Dislike.objects.filter(
            content_type=comment_content_type,
            object_id=comment_instance.id,
            is_deleted=False
        )
        dislikes_count = dislikes.update(
            is_deleted=True,
            deleted_at=current_time
        )
        if dislikes_count > 0:
            deleted_count += dislikes_count
            logger.info(f"Soft deleted {dislikes_count} dislikes on comment")

        # Recursively cascade soft delete child comments if they exist
        try:
            # Find child comments (replies) - using parent relationship
            child_comments = Comment.objects.filter(
                parent=comment_instance,
                is_deleted=False
            )
            for child_comment in child_comments:
                child_deleted_count = cascade_soft_delete_comment(child_comment)
                deleted_count += child_deleted_count
        except Exception as e:
            logger.warning(f"Error cascading to child comments: {e}")

        # Handle mentions in this comment
        try:
            from content.models import Mention
            mentions = Mention.objects.filter(
                comment=comment_instance,
                is_deleted=False
            )
            mention_count = mentions.update(
                is_deleted=True,
                deleted_at=current_time
            )
            if mention_count > 0:
                deleted_count += mention_count
                logger.info(f"Soft deleted {mention_count} mentions")
        except Exception as e:
            logger.warning(f"Could not soft delete mentions: {e}")

        # Handle content reports for this comment
        try:
            from content.models import ContentReport
            reports = ContentReport.objects.filter(
                content_type=comment_content_type,
                object_id=comment_instance.id,
                is_deleted=False
            )
            report_count = reports.update(
                is_deleted=True,
                deleted_at=current_time
            )
            if report_count > 0:
                deleted_count += report_count
                logger.info(f"Soft deleted {report_count} content reports")
        except Exception as e:
            logger.warning(f"Could not soft delete content reports: {e}")

        logger.info(f"Cascade soft deleted comment {comment_instance.id} "
                   f"and {deleted_count-1} related objects")
        return deleted_count


def cascade_soft_delete_user_profile(profile_instance):
    """
    Cascade soft deletion for a UserProfile instance.
    Soft deletes all related objects when a user profile is deleted.
    """
    with transaction.atomic():
        deleted_count = 0

        # 1. Soft delete all user's posts (which will cascade further)
        posts = profile_instance.posts.filter(is_deleted=False)
        for post in posts:
            deleted_count += cascade_soft_delete_post(post)

        # 2. Soft delete all user's comments
        comments = profile_instance.comments.filter(is_deleted=False)
        for comment in comments:
            deleted_count += cascade_soft_delete_comment(comment)

        # 3. Soft delete user's likes
        if hasattr(profile_instance, 'likes'):
            likes = profile_instance.likes.filter(is_deleted=False)
            for like in likes:
                like.is_deleted = True
                like.save()
                deleted_count += 1

        # 4. Soft delete user's follows
        if hasattr(profile_instance, 'following'):
            follows = profile_instance.following.filter(is_deleted=False)
            for follow in follows:
                follow.is_deleted = True
                follow.save()
                deleted_count += 1

        # 5. Soft delete follows of this user
        if hasattr(profile_instance, 'followers'):
            followers = profile_instance.followers.filter(is_deleted=False)
            for follower in followers:
                follower.is_deleted = True
                follower.save()
                deleted_count += 1

        # 6. Soft delete user's equipment - COMMENTED OUT (Equipment functionality removed)
        # if hasattr(profile_instance, 'equipment'):
        #     equipment = profile_instance.equipment.filter(is_deleted=False)
        #     for eq in equipment:
        #         eq.is_deleted = True
        #         eq.save()
        #         deleted_count += 1

        # 7. Soft delete user's badges
        if hasattr(profile_instance, 'badges'):
            badges = profile_instance.badges.filter(is_deleted=False)
            for badge in badges:
                badge.is_deleted = True
                badge.save()
                deleted_count += 1

        # Finally, soft delete the profile itself
        profile_instance.is_deleted = True
        profile_instance.save()

        logger.info(f"Cascade soft deleted user profile {profile_instance.id} and {deleted_count} related objects")
        return deleted_count + 1


# def cascade_soft_delete_equipment(equipment_instance):
#     """
#     Cascade soft deletion for Equipment instance.
#     Soft deletes all related objects when equipment is deleted.
#     """
#     # Equipment functionality removed - function commented out
#     pass


def cascade_soft_delete_community(community_instance):
    """
    Cascade soft deletion for Community instance.
    Soft deletes all related objects when community is deleted.
    """
    with transaction.atomic():
        deleted_count = 0

        # 1. Soft delete community posts
        if hasattr(community_instance, 'posts'):
            posts = community_instance.posts.filter(is_deleted=False)
            for post in posts:
                deleted_count += cascade_soft_delete_post(post)

        # 2. Soft delete community memberships
        if hasattr(community_instance, 'memberships'):
            memberships = community_instance.memberships.filter(is_deleted=False)
            for membership in memberships:
                membership.is_deleted = True
                membership.save()
                deleted_count += 1

        # 3. Soft delete community invitations
        if hasattr(community_instance, 'invitations'):
            invitations = community_instance.invitations.filter(is_deleted=False)
            for invitation in invitations:
                invitation.is_deleted = True
                invitation.save()
                deleted_count += 1

        # 4. Soft delete join requests
        if hasattr(community_instance, 'join_requests'):
            requests = community_instance.join_requests.filter(is_deleted=False)
            for request in requests:
                request.is_deleted = True
                request.save()
                deleted_count += 1

        # Finally, soft delete the community itself
        community_instance.is_deleted = True
        community_instance.save()

        logger.info(f"Cascade soft deleted community {community_instance.id} and {deleted_count} related objects")
        return deleted_count + 1


# Registry of cascade functions for different model types
CASCADE_FUNCTIONS = {
    'content.post': cascade_soft_delete_post,
    'content.comment': cascade_soft_delete_comment,
    'accounts.userprofile': cascade_soft_delete_user_profile,
    # 'equipment.equipment': cascade_soft_delete_equipment,  # Equipment functionality removed
    'communities.community': cascade_soft_delete_community,
}


def get_cascade_function(instance):
    """Get the appropriate cascade function for a model instance."""
    model_label = f"{instance._meta.app_label}.{instance._meta.model_name}"
    return CASCADE_FUNCTIONS.get(model_label)


def cascade_soft_delete(instance):
    """
    Generic cascade soft deletion function.

    Usage:
        from core.cascade_deletion import cascade_soft_delete
        cascade_soft_delete(post_instance)
    """
    cascade_func = get_cascade_function(instance)
    if cascade_func:
        return cascade_func(instance)
    else:
        # Just soft delete the instance itself
        instance.is_deleted = True
        instance.save()
        return 1
