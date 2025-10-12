"""
Core signals for automatic soft deletion timestamp handling.

This module provides Django signal handlers that automatically set deleted_at
timestamps whenever is_deleted is changed to True on any model.
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save)
def auto_set_deleted_at(sender, instance, **kwargs):
    """
    Automatically set deleted_at timestamp when is_deleted changes.

    This signal handler works with any Django model that has both
    is_deleted and deleted_at fields.
    """
    # Skip if model doesn't have the required fields
    if not (hasattr(instance, 'is_deleted') and
            hasattr(instance, 'deleted_at')):
        return

    # For new objects (no pk yet)
    if not instance.pk:
        if instance.is_deleted and not instance.deleted_at:
            instance.deleted_at = timezone.now()
        return

    # For existing objects, check if is_deleted field changed
    try:
        original = sender.objects.get(pk=instance.pk)

        # If is_deleted changed from False to True, set deleted_at
        if not original.is_deleted and instance.is_deleted:
            instance.deleted_at = timezone.now()

        # If is_deleted changed from True to False (restore), clear deleted_at
        elif original.is_deleted and not instance.is_deleted:
            instance.deleted_at = None

    except sender.DoesNotExist:
        # Object doesn't exist yet (rare edge case)
        if instance.is_deleted and not instance.deleted_at:
            instance.deleted_at = timezone.now()


# Bulk operation handler for QuerySet updates
def handle_bulk_soft_deletion(queryset, **update_fields):
    """
    Handle bulk soft deletion with automatic deleted_at setting.

    Usage:
        from core.signals import handle_bulk_soft_deletion
        handle_bulk_soft_deletion(Post.objects.filter(...), is_deleted=True)
    """
    if 'is_deleted' in update_fields and update_fields['is_deleted']:
        update_fields['deleted_at'] = timezone.now()
    elif 'is_deleted' in update_fields and not update_fields['is_deleted']:
        update_fields['deleted_at'] = None

    return queryset.update(**update_fields)


# Helper function for views to use consistent soft deletion
def soft_delete_instance(instance):
    """
    Soft delete a single model instance.

    Usage:
        from core.signals import soft_delete_instance
        soft_delete_instance(post)
    """
    instance.is_deleted = True
    instance.save()  # deleted_at will be set automatically by the signal


def restore_instance(instance):
    """
    Restore a soft-deleted model instance.

    Usage:
        from core.signals import restore_instance
        restore_instance(post)
    """
    instance.is_deleted = False
    instance.save()  # deleted_at will be cleared automatically by the signal


@receiver(post_save, sender='core.AdministrativeDivision')
def create_default_community_for_division(sender, instance, created, **kwargs):
    """
    Automatically create a default community when a new division is created.

    This ensures every division has at least one community for posts.
    """
    # pylint: disable=unused-argument
    if created:
        try:
            from communities.utils import get_or_create_default_community
            community = get_or_create_default_community(instance)
            logger.info(
                f"Auto-created community '{community.slug}' "
                f"for new division '{instance.name}'"
            )
        except Exception as e:
            logger.error(
                f"Failed to create default community for division "
                f"'{instance.name}': {str(e)}"
            )
