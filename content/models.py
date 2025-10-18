"""Content models for posts, comments, likes, and shares.

This module contains the main content models for the social media platform.
"""

import re
import uuid
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from accounts.models import UserProfile
from core.models import PostManager, CommentManager, MentionManager
from core.html_sanitizer import sanitize_article_content, sanitize_basic_html


class PostSee(models.Model):
    """Tracks when a user sees a post.

    Enhanced tracking for post views with detailed analytics.
    Counts a view even without like/comment/share.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='post_sees'
    )
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='sees'
    )

    # Enhanced tracking fields
    seen_at = models.DateTimeField(auto_now_add=True)
    view_duration_seconds = models.PositiveIntegerField(default=0)
    scroll_percentage = models.FloatField(default=0.0)  # How much of post was scrolled

    # Interaction context
    source = models.CharField(max_length=20, choices=[
        ('feed', 'Main Feed'),
        ('profile', 'User Profile'),
        ('community', 'Community Feed'),
        ('search', 'Search Results'),
        ('notification', 'Notification'),
        ('direct_link', 'Direct Link'),
        ('share', 'Shared Link'),
    ], default='feed')

    # Device and session info
    device_type = models.CharField(max_length=10, choices=[
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
    ], default='desktop')

    session_id = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Engagement tracking
    clicked_links = models.JSONField(default=list, blank=True)  # Links clicked within post
    media_viewed = models.JSONField(default=list, blank=True)  # Media items viewed
    is_engaged = models.BooleanField(default=False)  # True if user interacted

    # Time tracking
    time_to_engagement_seconds = models.PositiveIntegerField(null=True, blank=True)
    last_interaction_at = models.DateTimeField(null=True, blank=True)

    def mark_engaged(self, interaction_type='unknown'):
        """Mark this view as having user engagement."""
        if not self.is_engaged:
            self.is_engaged = True
            self.last_interaction_at = timezone.now()
            if self.time_to_engagement_seconds is None:
                time_diff = timezone.now() - self.seen_at
                self.time_to_engagement_seconds = int(time_diff.total_seconds())
            self.save(update_fields=[
                'is_engaged', 'last_interaction_at', 'time_to_engagement_seconds'
            ])

    def update_view_duration(self, duration_seconds):
        """Update the view duration for this post see."""
        self.view_duration_seconds = max(self.view_duration_seconds, duration_seconds)
        self.save(update_fields=['view_duration_seconds'])

    def update_scroll_percentage(self, percentage):
        """Update the scroll percentage for this post view."""
        self.scroll_percentage = max(self.scroll_percentage, min(100.0, percentage))
        self.save(update_fields=['scroll_percentage'])

    def add_clicked_link(self, link_url, click_time=None):
        """Track a link click within the post."""
        if click_time is None:
            click_time = timezone.now()

        click_data = {
            'url': link_url,
            'timestamp': click_time.isoformat(),
            'time_from_view': (click_time - self.seen_at).total_seconds()
        }

        if not self.clicked_links:
            self.clicked_links = []
        self.clicked_links.append(click_data)
        self.mark_engaged('link_click')

    def add_media_view(self, media_id, media_type, view_duration=0):
        """Track media viewing within the post."""
        media_data = {
            'media_id': str(media_id),
            'media_type': media_type,
            'viewed_at': timezone.now().isoformat(),
            'duration_seconds': view_duration,
            'time_from_view': (timezone.now() - self.seen_at).total_seconds()
        }

        if not self.media_viewed:
            self.media_viewed = []
        self.media_viewed.append(media_data)
        self.mark_engaged('media_view')

    @property
    def engagement_quality(self):
        """Calculate engagement quality score (0-100)."""
        score = 0

        # Base score for viewing
        score += 10

        # Duration bonus (up to 30 points)
        if self.view_duration_seconds > 0:
            score += min(30, self.view_duration_seconds / 10)

        # Scroll percentage bonus (up to 20 points)
        score += (self.scroll_percentage / 100) * 20

        # Interaction bonuses
        if self.is_engaged:
            score += 20

        if self.clicked_links:
            score += len(self.clicked_links) * 5

        if self.media_viewed:
            score += len(self.media_viewed) * 5

        return min(100, score)

    @property
    def is_quality_view(self):
        """Determine if this is a quality view (not a bounce)."""
        return (
            self.view_duration_seconds >= 3 or
            self.scroll_percentage >= 25 or
            self.is_engaged
        )

    @classmethod
    def record_post_view(cls, user, post, **kwargs):
        """
        Record a post view with optional tracking data.
        Returns (post_see, created) tuple.
        """
        defaults = {
            'source': kwargs.get('source', 'feed'),
            'device_type': kwargs.get('device_type', 'desktop'),
            'session_id': kwargs.get('session_id', ''),
            'ip_address': kwargs.get('ip_address'),
            'user_agent': kwargs.get('user_agent', ''),
        }

        # Get or create PostSee
        post_see, created = cls.objects.get_or_create(
            user=user,
            post=post,
            defaults=defaults
        )

        # If already exists, update the last seen time
        if not created:
            post_see.seen_at = timezone.now()
            update_fields = ['seen_at']

            # Update fields if provided
            if 'session_id' in kwargs:
                post_see.session_id = kwargs['session_id']
                update_fields.append('session_id')

            post_see.save(update_fields=update_fields)

        return post_see, created

    @classmethod
    def get_post_view_analytics(cls, post):
        """Get analytics data for a specific post."""
        views = cls.objects.filter(post=post, is_deleted=False)

        total_views = views.count()
        unique_views = views.values('user').distinct().count()
        quality_views = views.filter(
            models.Q(view_duration_seconds__gte=3) |
            models.Q(scroll_percentage__gte=25) |
            models.Q(is_engaged=True)
        ).count()

        avg_duration = views.aggregate(
            avg_duration=models.Avg('view_duration_seconds')
        )['avg_duration'] or 0

        avg_scroll = views.aggregate(
            avg_scroll=models.Avg('scroll_percentage')
        )['avg_scroll'] or 0

        engagement_rate = views.filter(is_engaged=True).count() / max(total_views, 1) * 100

        # Source breakdown
        source_breakdown = views.values('source').annotate(
            count=models.Count('id')
        ).order_by('-count')

        # Device breakdown
        device_breakdown = views.values('device_type').annotate(
            count=models.Count('id')
        ).order_by('-count')

        return {
            'total_views': total_views,
            'unique_views': unique_views,
            'quality_views': quality_views,
            'quality_rate': (quality_views / max(total_views, 1)) * 100,
            'avg_duration_seconds': avg_duration,
            'avg_scroll_percentage': avg_scroll,
            'engagement_rate': engagement_rate,
            'source_breakdown': list(source_breakdown),
            'device_breakdown': list(device_breakdown),
        }
    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-seen_at']
        verbose_name = 'Post See'
        verbose_name_plural = 'Post Sees'

    def __str__(self):
        return f"{self.user} saw {self.post} at {self.seen_at}"


class Post(models.Model):
    """Main post model."""
    POST_TYPES = [
        # REGULAR POSTS (content + optional attachments/poll)
        ('text', 'Text Post'),           # Simple text post
        ('image', 'Image Post'),         # Post with image attachments
        ('video', 'Video Post'),         # Post with video attachments
        ('audio', 'Audio Post'),         # Post with audio attachments
        ('file', 'File Post'),           # Post with file attachments
        ('link', 'Link Post'),           # Post with link preview
        ('poll', 'Poll Post'),           # Post with poll
        ('mixed', 'Mixed Media Post'),   # Post with multiple attachment types

        # RICH ARTICLES (TipTap HTML with embedded media)
        ('article', 'Rich Article'),     # Rich HTML content from TipTap editor

        # REPOST TYPES
        ('repost', 'Simple Repost'),  # Basic repost with just comment
        ('repost_with_media', 'Repost + Media'),  # With attachments
        ('repost_quote', 'Quote Repost'),  # With substantial commentary
        ('repost_remix', 'Remix Repost'),  # Creative transformed content
    ]

    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('followers', 'Followers'),
        ('private', 'Private'),
        ('community', 'Community Only'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    community = models.ForeignKey(
        'communities.Community',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='posts'
    )

    # Optional thread reference: posts may belong to a thread
    thread = models.ForeignKey(
        'communities.Thread',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='posts'
    )

    # Rubrique template: ONLY for posts NOT in a thread (direct posts)
    # If post.thread exists, rubrique is inherited from thread.rubrique_template
    rubrique_template = models.ForeignKey(
        'communities.RubriqueTemplate',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='posts',
        help_text="Rubrique for direct posts (not in thread). Required if thread is null."
    )

    # REPOST SUPPORT: Parent post for reposts
    parent_post = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='child_reposts',
        help_text="Original post if this is a repost"
    )

    # Basic HTML content for ALL posts (captions, descriptions)
    # Supports: <b>, <i>, <strong>, <em>, <a>, emoji, line breaks
    # Used by: ALL post types for captions/descriptions
    content = models.TextField(
        max_length=2000,
        blank=True,
        help_text=(
            "Basic HTML for post captions/descriptions "
            "(supports bold, italic, links, emoji)"
        )
    )

    # Rich HTML content for ARTICLE posts ONLY
    # Supports: Full TipTap editor with embedded <img>, <video>, <audio>
    # Used by: ONLY 'article' post_type when user creates rich articles
    article_content = models.TextField(
        blank=True,
        null=True,
        help_text=(
            "Rich HTML content for article posts with embedded media "
            "(TipTap editor output)"
        )
    )

    # Article-specific fields
    title = models.CharField(
        max_length=300,
        blank=True,
        help_text="Title for article posts (required for post_type='article')"
    )

    featured_image = models.ImageField(
        upload_to='post_featured_images/',
        null=True,
        blank=True,
        help_text="Featured/cover image for article posts"
    )

    excerpt = models.TextField(
        max_length=500,
        blank=True,
        help_text="Short excerpt/summary for article posts (150-300 chars recommended)"
    )

    is_draft = models.BooleanField(
        default=False,
        help_text="True if this is a draft (not published yet)"
    )

    post_type = models.CharField(
        max_length=20,
        choices=POST_TYPES,
        default='text'
    )

    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='public'
    )

    # Custom manager
    objects = PostManager()

    # ======================================================================
    link_image = models.URLField(blank=True)

    # Engagement metrics
    likes_count = models.PositiveIntegerField(default=0)
    dislikes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    repost_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)

    # Thread voting metrics (for posts inside threads)
    upvotes_count = models.PositiveIntegerField(
        default=0,
        help_text="Upvotes for posts in threads (Stack Overflow style)"
    )
    downvotes_count = models.PositiveIntegerField(
        default=0,
        help_text="Downvotes for posts in threads"
    )

    trend_score = models.FloatField(
        default=0.0,
        help_text="Score based on engagement and recency"
    )

    # Flags
    is_pinned = models.BooleanField(default=False)
    is_best_post = models.BooleanField(
        default=False,
        help_text="Marked as best post by thread creator (Q&A, solutions, etc.)"
    )
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_hidden = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        content_preview = (
            self.content[:50] + "..." if len(self.content) > 50
            else self.content
        )
        return f"{self.author.user.username}: {content_preview}"

    # ======================================================================
    # UNIFIED ATTACHMENT SYSTEM METHODS
    # ======================================================================

    @property
    def has_attachments(self):
        """Check if post has any attachments (new PostMedia system)."""
        return self.media.exists()

    @property
    def attachment_count(self):
        """Get total number of attachments."""
        return self.media.count()

    @property
    def attachments_by_type(self):
        """Get attachments grouped by media type."""
        attachments = {}
        for media in self.media.all():
            media_type = media.media_type
            if media_type not in attachments:
                attachments[media_type] = []
            attachments[media_type].append(media)
        return attachments

    def get_attachments_of_type(self, media_type):
        """Get all attachments of a specific type."""
        return self.media.filter(media_type=media_type)

    def get_primary_attachment(self):
        """Get the first/primary attachment (by order)."""
        return self.media.first()

    def can_add_attachment(self, max_attachments=10):
        """Check if more attachments can be added."""
        return self.attachment_count < max_attachments

    # ======================================================================
    # RICH CONTENT / ARTICLE METHODS
    # ======================================================================

    @property
    def is_article(self):
        """Check if this is a rich article post with embedded media."""
        return (
            self.post_type == 'article' and
            self.article_content and
            self.article_content.strip()
        )

    @property
    def has_embedded_media(self):
        """Check if article_content has embedded media tags."""
        if not self.article_content:
            return False
        import re
        return bool(
            re.search(r'<(img|video|audio)[^>]*>', self.article_content)
        )

    def get_content_for_display(self):
        """Get appropriate content for display based on post type."""
        return self.content

    # ======================================================================
    # MULTIPLE POLLS SUPPORT METHODS
    # ======================================================================

    @property
    def has_polls(self):
        """Check if post has any polls."""
        return hasattr(self, 'polls') and self.polls.exists()

    @property
    def polls_count(self):
        """Get total number of polls."""
        return self.polls.count() if hasattr(self, 'polls') else 0

    @property
    def active_polls(self):
        """Get all active polls."""
        if not hasattr(self, 'polls'):
            return []
        return self.polls.filter(is_active=True, is_closed=False, is_deleted=False)

    def get_primary_poll(self):
        """Get the first/primary poll (by order)."""
        if not hasattr(self, 'polls'):
            return None
        return self.polls.first()

    def can_add_poll(self, max_polls=5):
        """Check if more polls can be added."""
        return self.polls_count < max_polls

    @property
    def is_community_post(self):
        """Check if this post belongs to a community."""
        return self.community is not None

    @property
    def context_type(self):
        """Return the context type of the post."""
        return 'community' if self.is_community_post else 'general'

    @property
    def context_name(self):
        """Return context name (community or General)."""
        return (
            self.community.name
            if self.is_community_post else 'General Feed'
        )

    # Repost properties
    @property
    def is_repost(self):
        """Check if this post is a repost of another post."""
        return self.parent_post is not None

    @property
    def original_post(self):
        """Get the original post if this is a repost, otherwise return self."""
        return self.parent_post if self.is_repost else self

    def validate_repost_content(self):
        """
        Reposts can contain any content that regular posts can contain.
        This method is kept for compatibility but no longer restricts content.
        """
        # No validation - reposts should support the same content as regular posts
        pass

    # ======================================================================
    # ENHANCED REPOST TYPE DETECTION
    # ======================================================================

    def get_repost_type(self):
        """Auto determine appropriate repost type based on content."""
        if not self.is_repost:
            return None

        has_attachments = self.has_attachments
        content_length = len(self.content.strip()) if self.content else 0

        if has_attachments and content_length > 100:
            return 'repost_remix'  # Creative content with media
        elif has_attachments:
            return 'repost_with_media'  # Simple repost with media
        elif content_length > 100:
            return 'repost_quote'  # Substantial commentary
        else:
            return 'repost'  # Simple repost

    def auto_set_repost_type(self):
        """Automatically set post_type based on repost content."""
        if self.is_repost:
            self.post_type = self.get_repost_type()

    @property
    def repost_category(self):
        """Get human-readable repost category."""
        repost_types = {
            'repost': 'Simple Share',
            'repost_with_media': 'Share + Media',
            'repost_quote': 'Quote Share',
            'repost_remix': 'Creative Remix'
        }
        return repost_types.get(self.post_type, 'Unknown')

    @property
    def is_enhanced_repost(self):
        """Check if this is any type of repost."""
        return self.post_type in [
            'repost', 'repost_with_media', 'repost_quote', 'repost_remix'
        ]

    @property
    def has_repost_additions(self):
        """Check if repost has additional content beyond the original."""
        return self.is_repost and (
            (self.content and self.content.strip()) or
            self.has_attachments
        )

    @property
    def get_division(self):
        """Get the geographic division for this post through its community.

        Returns:
            AdministrativeDivision instance or None if community has no division
        """
        if self.community and self.community.division:
            return self.community.division
        return None

    def clean(self):
        """Validate that only verified, non-suspended users can post."""
        super().clean()
        from django.core.exceptions import ValidationError
        from accounts.permissions import validate_user_for_interaction

        validate_user_for_interaction(self.author, "create posts")

        # If thread is provided, auto-assign community from thread
        if self.thread:
            # Auto-assign community from thread
            if not self.community:
                self.community = self.thread.community
            elif self.community.id != self.thread.community.id:
                raise ValidationError({
                    'thread': 'Thread community does not match post.community'
                })

            # Posts in threads should NOT have rubrique_template (inherited)
            if self.rubrique_template:
                raise ValidationError({
                    'rubrique_template': 'Posts in threads inherit rubrique from thread. '
                                       'Set rubrique_template to null.'
                })

        # If NOT in thread and posting to community, require rubrique_template
        elif self.community and not self.thread:
            if not self.rubrique_template:
                raise ValidationError({
                    'rubrique_template': 'Direct community posts require '
                                        'rubrique_template.'
                })

            # Validate rubrique is enabled for community
            if self.rubrique_template:
                enabled_rubriques = self.community.enabled_rubriques or []
                rubrique_id = str(self.rubrique_template.id)

                if rubrique_id not in enabled_rubriques:
                    raise ValidationError({
                        'rubrique_template':
                            f"Rubrique '{self.rubrique_template.default_name}' "
                            f"is not enabled for this community."
                    })

        # Check if user is banned from the community
        if self.community:
            from communities.models import CommunityMembership
            banned_membership = CommunityMembership.objects.filter(
                community=self.community,
                user=self.author,
                status='banned',
                is_deleted=False
            ).first()

            if banned_membership:
                ban_message = "You are banned from posting in this community."
                if banned_membership.ban_reason:
                    ban_message += f" Reason: {banned_membership.ban_reason}"
                if banned_membership.ban_expires_at:
                    ban_message += (
                        f" Ban expires: "
                        f"{banned_membership.ban_expires_at.strftime('%Y-%m-%d')}"
                    )
                raise ValidationError({'community': ban_message})

        # Validate article posts have title and content (unless draft)
        if self.post_type == 'article' and not self.is_draft:
            if not self.title or not self.title.strip():
                raise ValidationError({
                    'title': 'Article posts require a title. Save as draft if incomplete.'
                })
            if not self.article_content or not self.article_content.strip():
                raise ValidationError({
                    'article_content': 'Article posts require content. Save as draft if incomplete.'
                })

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation.

        Behavior additions:
        - Sanitize HTML content in both content and article_content fields
        - Auto-generate excerpt from article_content if needed
        - On create: if `thread` is set increment that thread.posts_count.
        - On update: if `thread` changed, decrement old thread.posts_count and
          increment new thread.posts_count (never allowing negative counts).
        """
        from django.apps import apps
        from django.db.models import F, Value
        from django.db.models.functions import Greatest
        import re

        # Sanitize basic HTML in content field (for ALL posts)
        if self.content:
            self.content = sanitize_basic_html(self.content)

        # Sanitize rich HTML in article_content field (for ARTICLE posts only)
        if self.article_content:
            self.article_content = sanitize_article_content(
                self.article_content
            )

        # Auto-generate excerpt for articles with article_content
        if (self.post_type == 'article' and self.article_content
                and not self.content):
            # Strip HTML tags to get plain text
            text = re.sub('<[^<]+?>', '', self.article_content)
            # Take first 200 characters as excerpt
            self.content = (
                text[:200].strip() + '...'
                if len(text) > 200
                else text.strip()
            )

        self.full_clean()

        is_create = self._state.adding
        old_thread_id = None
        old_is_deleted = None
        if not is_create and self.pk:
            # get previous thread id and deletion state before saving changes
            prev = Post.objects.filter(pk=self.pk).values_list('thread_id', 'is_deleted').first()
            if prev is not None:
                old_thread_id, old_is_deleted = prev

        super().save(*args, **kwargs)

        Thread = apps.get_model('communities', 'Thread')

    # On create, increment the new thread count if applicable
        if is_create:
            if self.thread_id:
                Thread.objects.filter(pk=self.thread_id).update(posts_count=F('posts_count') + 1)
            return

        # On update, if thread changed, adjust counts accordingly
        new_thread_id = self.thread_id
        if old_thread_id != new_thread_id:
            # Decrement old thread (if any), ensuring non-negative
            if old_thread_id:
                Thread.objects.filter(pk=old_thread_id).update(
                    posts_count=Greatest(F('posts_count') - 1, Value(0))
                )

            # Increment new thread (if any)
            if new_thread_id:
                Thread.objects.filter(pk=new_thread_id).update(posts_count=F('posts_count') + 1)

        # Handle soft-delete / restore transitions: adjust thread counts when is_deleted flips
        # old_is_deleted can be None for create/new objects
        if old_is_deleted is not None and old_is_deleted != getattr(self, 'is_deleted', False):
            # deleted: False -> True  => decrement thread count
            # restored: True -> False => increment thread count
            if getattr(self, 'thread_id', None):
                if getattr(self, 'is_deleted'):
                    # soft-delete
                    Thread.objects.filter(pk=self.thread_id).update(
                        posts_count=Greatest(F('posts_count') - 1, Value(0))
                    )
                else:
                    # restoration
                    Thread.objects.filter(pk=self.thread_id).update(posts_count=F('posts_count') + 1)

    class Meta:
        """Order newest first and add key indexes."""
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['visibility', '-created_at']),
            models.Index(fields=['post_type', '-created_at']),
            models.Index(fields=['community', '-created_at']),
        ]

    def delete(self, *args, **kwargs):
        """On hard delete, decrement thread.posts_count if applicable, then delete."""
        from django.apps import apps
        from django.db.models import F, Value
        from django.db.models.functions import Greatest

        thread_id = getattr(self, 'thread_id', None)
        if thread_id:
            Thread = apps.get_model('communities', 'Thread')
            Thread.objects.filter(pk=thread_id).update(
                posts_count=Greatest(F('posts_count') - 1, Value(0))
            )
        super().delete(*args, **kwargs)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone
        from django.apps import apps
        from django.db.models import F

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])



        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history


def postmedia_file_upload_to(instance, filename):
    """File upload path for post media."""
    post_id = str(instance.post.id)
    return f"posts/media/{post_id}/{filename}"


def postmedia_thumbnail_upload_to(instance, filename):
    """Thumbnail upload path for post media."""
    post_id = str(instance.post.id)
    return f"posts/media/{post_id}/thumbnails/{filename}"


class PostMedia(models.Model):
    """Multiple media attachments for posts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='media'
    )
    media_type = models.CharField(
        max_length=10,
        choices=[
            ('image', 'Image'),
            ('video', 'Video'),
            ('audio', 'Audio'),
            ('file', 'File')
        ]
    )

    # Either file OR external_url should be set (not both)
    file = models.FileField(
        upload_to=postmedia_file_upload_to,
        blank=True,
        null=True
    )
    external_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="External URL for media hosted elsewhere (e.g., CDN, Unsplash)"
    )
    thumbnail = models.ImageField(
        upload_to=postmedia_thumbnail_upload_to,
        blank=True,
        null=True
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional description/caption for this media attachment"
    )
    order = models.PositiveIntegerField(default=0)

    def clean(self):
        """Validate that either file or external_url is provided (not both)."""
        super().clean()
        from django.core.exceptions import ValidationError

        # Ensure either file OR external_url is provided
        if not self.file and not self.external_url:
            raise ValidationError(
                'Either file or external_url must be provided.'
            )

        if self.file and self.external_url:
            raise ValidationError(
                'Cannot have both file and external_url. '
                'Choose one or the other.'
            )

        # Validate media file duration for uploaded videos and audio
        if self.media_type in ['video', 'audio'] and self.file:
            try:
                # Check file duration using ffmpeg-python or similar
                duration = self._get_media_duration()
                if duration and duration > 300:  # 5 minutes = 300 seconds
                    from django.core.exceptions import ValidationError
                    duration_str = f"{duration//60}:{duration%60:02d}"
                    raise ValidationError({
                        'file': f'{self.media_type.title()} files must be 5 '
                                f'minutes or less. Duration: {duration_str}'
                    })
            except Exception as e:
                # If we can't check duration, allow the file but log the issue
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Could not validate {self.media_type} duration "
                    f"for file {self.file.name}: {e}"
                )

    def _get_media_duration(self):
        """Get duration of video/audio file in seconds."""
        if not self.file:
            return None

        try:
            # Try using ffmpeg-python for accurate duration detection
            import subprocess
            import json

            # Use ffprobe to get media information
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', self.file.path
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                info = json.loads(result.stdout)

                # Get duration from format or streams
                if 'format' in info and 'duration' in info['format']:
                    return float(info['format']['duration'])

                # Fallback to stream duration
                for stream in info.get('streams', []):
                    if (stream.get('codec_type') in ['video', 'audio'] and
                            'duration' in stream):
                        return float(stream['duration'])

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError,
                ImportError, FileNotFoundError, json.JSONDecodeError,
                ValueError):
            pass

        try:
            # Fallback: try using mutagen for audio files
            if self.media_type == 'audio':
                from mutagen import File as MutagenFile
                audio_file = MutagenFile(self.file.path)
                if (audio_file and hasattr(audio_file, 'info') and
                        hasattr(audio_file.info, 'length')):
                    return audio_file.info.length
        except (ImportError, Exception):
            pass

        return None

    @property
    def media_url(self):
        """Get the media URL (either uploaded file or external URL)."""
        if self.external_url:
            return self.external_url
        elif self.file:
            return self.file.url
        return None

    def generate_video_thumbnail(self, at_second=1):
        """
        Generate a thumbnail from a video file at a specific timestamp.

        Args:
            at_second: Second in the video to capture thumbnail (default: 1)

        Returns:
            bool: True if thumbnail was generated successfully

        Note: Requires ffmpeg/ffprobe to be installed
        """
        if self.media_type != 'video' or not self.file:
            return False

        try:
            import subprocess
            import tempfile
            from django.core.files import File
            from PIL import Image
            import io

            # Create temporary file for thumbnail
            with tempfile.NamedTemporaryFile(
                suffix='.jpg', delete=False
            ) as temp_thumb:
                # Extract frame at specified second using ffmpeg
                cmd = [
                    'ffmpeg',
                    '-i', self.file.path,
                    '-ss', str(at_second),
                    '-vframes', '1',
                    '-q:v', '2',  # High quality
                    '-y',  # Overwrite output
                    temp_thumb.name
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=30,
                    text=True
                )

                if result.returncode == 0:
                    # Open and resize thumbnail
                    img = Image.open(temp_thumb.name)

                    # Resize to standard thumbnail size (maintaining aspect)
                    img.thumbnail((400, 300), Image.Resampling.LANCZOS)

                    # Save to BytesIO
                    thumb_io = io.BytesIO()
                    img.save(thumb_io, format='JPEG', quality=85)
                    thumb_io.seek(0)

                    # Save to model
                    thumb_filename = f"thumb_{self.id}.jpg"
                    self.thumbnail.save(
                        thumb_filename,
                        File(thumb_io),
                        save=True
                    )

                    return True

        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
            ImportError,
            Exception
        ) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Failed to generate video thumbnail for {self.id}: {e}"
            )

        return False

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history



    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.post.id} - {self.media_type}"


class Comment(models.Model):
    """Comments on posts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    content = models.TextField(max_length=1000)

    # Custom manager
    objects = CommentManager()

    # Engagement
    likes_count = models.PositiveIntegerField(default=0)
    dislikes_count = models.PositiveIntegerField(default=0)
    replies_count = models.PositiveIntegerField(default=0)

    # Flags
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    # For achievements
    is_best = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        content_preview = (
            self.content[:50] + "..." if len(self.content) > 50
            else self.content
        )
        return f"{self.author.user.username}: {content_preview}"

    @property
    def is_community_comment(self):
        """Check if this comment belongs to a community post."""
        return self.post.community is not None

    @property
    def community(self):
        """Get the community this comment belongs to (if any)."""
        return self.post.community

    @property
    def context_type(self):
        """Return the context type of the comment."""
        return 'community' if self.is_community_comment else 'general'

    @property
    def context_name(self):
        """Return the name of the context."""
        if self.is_community_comment:
            return self.post.community.name
        return 'General Feed'

    def clean(self):
        """Validate that only verified, non-suspended users can comment."""
        super().clean()
        from accounts.permissions import validate_user_for_interaction
        validate_user_for_interaction(self.author, "create comments")

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        """Ordering comments by creation date descending."""
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history



# class Like(models.Model):
#     """Likes on posts and comments."""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
#     object_id = models.UUIDField()
#     content_object = GenericForeignKey('content_type', 'object_id')

#     # Soft delete field

#     is_deleted = models.BooleanField(default=False)

#     deleted_at = models.DateTimeField(null=True, blank=True)
#     # Restoration tracking fields
#     is_restored = models.BooleanField(default=False)
#     restored_at = models.DateTimeField(null=True, blank=True)
#     last_deletion_at = models.DateTimeField(null=True, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         """Unique constraint to prevent duplicate likes on the same content."""
#         unique_together = ('user', 'content_type', 'object_id')
#         indexes = [
#             models.Index(fields=['content_type', 'object_id']),
#             models.Index(fields=['user', '-created_at']),
#         ]

#     def clean(self):
#         """Validate that only verified, non-suspended users can like."""
#         super().clean()
#         from accounts.permissions import validate_user_for_interaction
#         validate_user_for_interaction(self.user, "like content")

#     def save(self, *args, **kwargs):
#         """Override save to call full_clean for validation."""
#         self.full_clean()
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.user.user.username} liked {self.content_object}"
#     def restore_instance(self, cascade=True):
#         """Restore this soft-deleted instance and optionally cascade to related objects."""
#         from django.utils import timezone

#         if not self.is_deleted:
#             return False, f"{self.__class__.__name__} is not deleted"

#         # Store the deletion timestamp before restoring
#         self.last_deletion_at = self.deleted_at

#         # Restore the instance
#         self.is_deleted = False
#         self.deleted_at = None
#         self.is_restored = True
#         self.restored_at = timezone.now()

#         self.save(update_fields=[
#             'is_deleted', 'deleted_at', 'is_restored',
#             'restored_at', 'last_deletion_at'
#         ])

#         restored_count = 1

#         if cascade:
#             # Cascade restore to related objects
#             related_count = self._cascade_restore_related()
#             restored_count += related_count

#         return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

#     def _cascade_restore_related(self):
#         """Cascade restore to related objects."""
#         restored_count = 0

#         # Get all reverse foreign key relationships
#         for rel in self._meta.get_fields():
#             if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
#                 if rel.remote_field and hasattr(rel.remote_field, 'name'):
#                     try:
#                         related_manager = getattr(self, rel.get_accessor_name())

#                         # Find soft-deleted related objects
#                         if hasattr(related_manager, 'filter'):
#                             deleted_related = related_manager.filter(is_deleted=True)

#                             for related_obj in deleted_related:
#                                 if hasattr(related_obj, 'restore_instance'):
#                                     success, message = related_obj.restore_instance(cascade=False)
#                                     if success:
#                                         restored_count += 1

#                     except (AttributeError, Exception):
#                         # Skip relationships that can't be processed
#                         continue

#         # Handle ManyToMany relationships
#         for field in self._meta.many_to_many:
#             try:
#                 related_manager = getattr(self, field.name)
#                 if hasattr(related_manager, 'filter'):
#                     deleted_related = related_manager.filter(is_deleted=True)

#                     for related_obj in deleted_related:
#                         if hasattr(related_obj, 'restore_instance'):
#                             success, message = related_obj.restore_instance(cascade=False)
#                             if success:
#                                 restored_count += 1

#             except (AttributeError, Exception):
#                 continue

#         return restored_count

#     @classmethod
#     def bulk_restore(cls, queryset=None, cascade=True):
#         """Bulk restore multiple instances."""
#         from django.utils import timezone

#         if queryset is None:
#             queryset = cls.objects.filter(is_deleted=True)
#         else:
#             queryset = queryset.filter(is_deleted=True)

#         if not queryset.exists():
#             return 0, "No deleted objects found to restore"

#         restored_objects = []
#         total_restored = 0

#         for obj in queryset:
#             try:
#                 success, message = obj.restore_instance(cascade=cascade)
#                 if success:
#                     restored_objects.append(obj)
#                     total_restored += 1
#             except Exception as e:
#                 print(f"Error restoring {obj}: {e}")
#                 continue

#         return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

#     def get_restoration_history(self):
#         """Get the restoration history of this object."""
#         history = {
#             'is_currently_deleted': self.is_deleted,
#             'is_restored': self.is_restored,
#             'last_restoration': self.restored_at,
#             'last_deletion': self.last_deletion_at,
#             'deletion_restoration_cycle': None
#         }

#         if self.last_deletion_at and self.restored_at:
#             if self.restored_at > self.last_deletion_at:
#                 history['deletion_restoration_cycle'] = {
#                     'deleted_at': self.last_deletion_at,
#                     'restored_at': self.restored_at,
#                     'cycle_duration': self.restored_at - self.last_deletion_at
#                 }

#         return history



# class Dislike(models.Model):
#     """Dislikes on posts and comments."""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
#     object_id = models.UUIDField()
#     content_object = GenericForeignKey('content_type', 'object_id')

#     # Soft delete field

#     is_deleted = models.BooleanField(default=False)

#     deleted_at = models.DateTimeField(null=True, blank=True)
#     # Restoration tracking fields
#     is_restored = models.BooleanField(default=False)
#     restored_at = models.DateTimeField(null=True, blank=True)
#     last_deletion_at = models.DateTimeField(null=True, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('user', 'content_type', 'object_id')
#         indexes = [
#             models.Index(fields=['content_type', 'object_id']),
#             models.Index(fields=['user', '-created_at']),
#         ]

#     def clean(self):
#         """Validate that only verified, non-suspended users can dislike."""
#         super().clean()
#         from accounts.permissions import validate_user_for_interaction
#         validate_user_for_interaction(self.user, "dislike content")

#     def save(self, *args, **kwargs):
#         """Override save to call full_clean for validation."""
#         self.full_clean()
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.user.user.username} disliked {self.content_object}"

#     def restore_instance(self, cascade=True):
#         """Restore this soft-deleted instance and optionally cascade to related objects."""
#         from django.utils import timezone

#         if not self.is_deleted:
#             return False, f"{self.__class__.__name__} is not deleted"

#         # Store the deletion timestamp before restoring
#         self.last_deletion_at = self.deleted_at

#         # Restore the instance
#         self.is_deleted = False
#         self.deleted_at = None
#         self.is_restored = True
#         self.restored_at = timezone.now()

#         self.save(update_fields=[
#             'is_deleted', 'deleted_at', 'is_restored',
#             'restored_at', 'last_deletion_at'
#         ])

#         restored_count = 1

#         if cascade:
#             # Cascade restore to related objects
#             related_count = self._cascade_restore_related()
#             restored_count += related_count

#         return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

#     def _cascade_restore_related(self):
#         """Cascade restore to related objects."""
#         restored_count = 0

#         # Get all reverse foreign key relationships
#         for rel in self._meta.get_fields():
#             if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
#                 if rel.remote_field and hasattr(rel.remote_field, 'name'):
#                     try:
#                         related_manager = getattr(self, rel.get_accessor_name())

#                         # Find soft-deleted related objects
#                         if hasattr(related_manager, 'filter'):
#                             deleted_related = related_manager.filter(is_deleted=True)

#                             for related_obj in deleted_related:
#                                 if hasattr(related_obj, 'restore_instance'):
#                                     success, message = related_obj.restore_instance(cascade=False)
#                                     if success:
#                                         restored_count += 1

#                     except (AttributeError, Exception):
#                         # Skip relationships that can't be processed
#                         continue

#         # Handle ManyToMany relationships
#         for field in self._meta.many_to_many:
#             try:
#                 related_manager = getattr(self, field.name)
#                 if hasattr(related_manager, 'filter'):
#                     deleted_related = related_manager.filter(is_deleted=True)

#                     for related_obj in deleted_related:
#                         if hasattr(related_obj, 'restore_instance'):
#                             success, message = related_obj.restore_instance(cascade=False)
#                             if success:
#                                 restored_count += 1

#             except (AttributeError, Exception):
#                 continue

#         return restored_count

#     @classmethod
#     def bulk_restore(cls, queryset=None, cascade=True):
#         """Bulk restore multiple instances."""
#         from django.utils import timezone

#         if queryset is None:
#             queryset = cls.objects.filter(is_deleted=True)
#         else:
#             queryset = queryset.filter(is_deleted=True)

#         if not queryset.exists():
#             return 0, "No deleted objects found to restore"

#         restored_objects = []
#         total_restored = 0

#         for obj in queryset:
#             try:
#                 success, message = obj.restore_instance(cascade=cascade)
#                 if success:
#                     restored_objects.append(obj)
#                     total_restored += 1
#             except Exception as e:
#                 print(f"Error restoring {obj}: {e}")
#                 continue

#         return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

#     def get_restoration_history(self):
#         """Get the restoration history of this object."""
#         history = {
#             'is_currently_deleted': self.is_deleted,
#             'is_restored': self.is_restored,
#             'last_restoration': self.restored_at,
#             'last_deletion': self.last_deletion_at,
#             'deletion_restoration_cycle': None
#         }

#         if self.last_deletion_at and self.restored_at:
#             if self.restored_at > self.last_deletion_at:
#                 history['deletion_restoration_cycle'] = {
#                     'deleted_at': self.last_deletion_at,
#                     'restored_at': self.restored_at,
#                     'cycle_duration': self.restored_at - self.last_deletion_at
#                 }

#         return history


class PostReaction(models.Model):
    """
    Emoji reactions to posts (replaces Like/Dislike binary system)
    Provides rich emotional expressions for better engagement
    """

    # Comprehensive emoji reaction types
    REACTION_TYPES = [
        # Thread voting (Stack Overflow style)
        ('upvote', '⬆️ Upvote'),
        ('downvote', '⬇️ Downvote'),

        # Positive reactions
        ('like', '👍 Like'),
        ('love', '❤️ Love'),
        ('care', '🤗 Care'),
        ('haha', '😂 Haha'),
        ('wow', '😮 Wow'),
        ('yay', '🎉 Yay'),
        ('clap', '👏 Clap'),
        ('fire', '🔥 Fire'),
        ('star', '⭐ Star'),
        ('party', '🥳 Party'),
        ('heart_eyes', '😍 Heart Eyes'),
        ('pray', '🙏 Pray'),
        ('strong', '💪 Strong'),
        ('celebrate', '🎊 Celebrate'),

        # Negative reactions
        ('sad', '😢 Sad'),
        ('angry', '😡 Angry'),
        ('worried', '😟 Worried'),
        ('disappointed', '😞 Disappointed'),

        # Neutral/Informative reactions
        ('thinking', '🤔 Thinking'),
        ('curious', '🧐 Curious'),
        ('shock', '😱 Shock'),
        ('confused', '😕 Confused'),
    ]

    # Sentiment classification (for recommendation system integration)
    POSITIVE_REACTIONS = [
        'upvote', 'like', 'love', 'care', 'haha', 'wow', 'yay', 'clap',
        'fire', 'star', 'party', 'heart_eyes', 'pray', 'strong', 'celebrate'
    ]

    NEGATIVE_REACTIONS = [
        'downvote', 'sad', 'angry', 'worried', 'disappointed'
    ]

    NEUTRAL_REACTIONS = [
        'thinking', 'curious', 'shock', 'confused'
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='post_reactions'
    )
    reaction_type = models.CharField(
        max_length=20,
        choices=REACTION_TYPES,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['post', 'user']
        indexes = [
            models.Index(fields=['post', 'reaction_type']),
            models.Index(fields=['user', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        emoji = dict(self.REACTION_TYPES).get(self.reaction_type, '')
        return f"{self.user.user.username} {emoji} on post {self.post.id}"

    @property
    def sentiment(self):
        """Get sentiment category for recommendation system"""
        if self.reaction_type in self.POSITIVE_REACTIONS:
            return 'positive'
        elif self.reaction_type in self.NEGATIVE_REACTIONS:
            return 'negative'
        else:
            return 'neutral'

    def clean(self):
        """Validate that only verified, non-suspended users can react."""
        super().clean()
        from accounts.permissions import validate_user_for_interaction
        validate_user_for_interaction(self.user, "react to content")

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted reaction."""
        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        continue

        return restored_count

    def get_deletion_history(self):
        """Get the deletion and restoration history of this reaction."""
        history = {
            'is_deleted': self.is_deleted,
            'current_deletion': self.deleted_at,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history


class CommentReaction(models.Model):
    """
    Emoji reactions to comments
    """

    # Use same reaction types as PostReaction
    REACTION_TYPES = PostReaction.REACTION_TYPES
    POSITIVE_REACTIONS = PostReaction.POSITIVE_REACTIONS
    NEGATIVE_REACTIONS = PostReaction.NEGATIVE_REACTIONS
    NEUTRAL_REACTIONS = PostReaction.NEUTRAL_REACTIONS

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(
        'Comment',
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='comment_reactions'
    )
    reaction_type = models.CharField(
        max_length=20,
        choices=REACTION_TYPES,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['comment', 'user']
        indexes = [
            models.Index(fields=['comment', 'reaction_type']),
            models.Index(fields=['user', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        emoji = dict(self.REACTION_TYPES).get(self.reaction_type, '')
        return f"{self.user.user.username} {emoji} on comment {self.comment.id}"

    @property
    def sentiment(self):
        """Get sentiment category"""
        if self.reaction_type in self.POSITIVE_REACTIONS:
            return 'positive'
        elif self.reaction_type in self.NEGATIVE_REACTIONS:
            return 'negative'
        else:
            return 'neutral'

    def clean(self):
        """Validate that only verified, non-suspended users can react."""
        super().clean()
        from accounts.permissions import validate_user_for_interaction
        validate_user_for_interaction(self.user, "react to content")

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted reaction."""
        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        continue

        return restored_count

    def get_deletion_history(self):
        """Get the deletion and restoration history of this reaction."""
        history = {
            'is_deleted': self.is_deleted,
            'current_deletion': self.deleted_at,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history



class DirectShare(models.Model):
    """Private share to recipients' inboxes (not a repost)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='direct_shares_sent'
    )
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='direct_shares'
    )
    note = models.TextField(
        max_length=500,
        blank=True,
        help_text="Optional note to recipients"
    )

    # Soft delete field

    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['-created_at'])
        ]

    def clean(self):
        """Validate that only verified, non-suspended users can share."""
        super().clean()
        from accounts.permissions import validate_user_for_interaction
        validate_user_for_interaction(self.sender, "share content")

    def save(self, *args, **kwargs):
        """Override save to call full_clean for validation."""
        self.full_clean()
        # On create increment ONLY shares_count (direct share count)
        is_create = self._state.adding
        super().save(*args, **kwargs)
        if is_create:
            Post.objects.filter(id=self.post_id).update(
                shares_count=models.F('shares_count') + 1
            )

    def __str__(self):
        return f"{self.sender.user.username} shared {self.post}"

    def delete(self, *args, **kwargs):
        post_id = self.post_id
        super().delete(*args, **kwargs)
        Post.objects.filter(id=post_id, shares_count__gt=0).update(
            shares_count=models.F('shares_count') - 1
        )

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history


class DirectShareRecipient(models.Model):
    """Delivery record for a DirectShare recipient."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    direct_share = models.ForeignKey(
        DirectShare,
        on_delete=models.CASCADE,
        related_name='deliveries'
    )
    recipient = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='direct_share_deliveries'
    )
    # Read tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('direct_share', 'recipient')
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['direct_share', '-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        status = 'read' if self.is_read else 'unread'
        return (
            f"Delivery {self.direct_share.id} -> "
            f"{self.recipient.user.username} ({status})"
        )

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class Hashtag(models.Model):
    """Hashtag management."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    posts_count = models.PositiveIntegerField(default=0)
    is_trending = models.BooleanField(default=False)

    # Soft delete field

    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.name}"

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history


class PostHashtag(models.Model):
    """Many-to-many relationship between posts and hashtags."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='content_hashtags'
    )
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE)

    # Soft delete field

    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Unique constraint to prevent duplicate hashtag associations."""
        unique_together = ('post', 'hashtag')

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history


class Mention(models.Model):
    """User mentions in posts and comments."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='content_mentions'
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='content_mentions'
    )
    mentioned_user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='content_mentions_received'
    )
    mentioning_user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='content_mentions_sent'
    )

    # Soft delete field

    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Custom manager
    objects = MentionManager()

    def __str__(self):
        mentioned = self.mentioned_user.user.username
        mentioning = self.mentioning_user.user.username
        return f"{mentioning} mentioned {mentioned}"

    @property
    def is_community_mention(self):
        """Check if this mention belongs to a community context."""
        if self.post:
            return self.post.community is not None
        elif self.comment:
            return self.comment.post.community is not None
        return False

    @property
    def community(self):
        """Get the community this mention belongs to (if any)."""
        if self.post:
            return self.post.community
        elif self.comment:
            return self.comment.post.community
        return None

    @property
    def context_type(self):
        """Return the context type of the mention."""
        return 'community' if self.is_community_mention else 'general'

    @property
    def context_name(self):
        """Return the name of the context."""
        community = self.community
        return community.name if community else 'General Feed'

    @property
    def source_content(self):
        """Return the source content (post or comment) of the mention."""
        return self.post if self.post else self.comment

    class Meta:
        indexes = [
            models.Index(fields=['mentioned_user', '-created_at']),
            models.Index(fields=['mentioning_user', '-created_at']),
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['comment', '-created_at']),
        ]

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history


class ContentReport(models.Model):
    """User reports for inappropriate content."""

    REPORT_REASONS = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('hate_speech', 'Hate Speech'),
        ('violence', 'Violence'),
        ('nudity', 'Nudity/Sexual Content'),
        ('misinformation', 'Misinformation'),
        ('copyright', 'Copyright Violation'),
        ('self_harm', 'Self-harm'),
        ('other', 'Other'),
    ]

    REPORT_STATUS = [
        ('pending', 'Pending Review'),
        ('reviewing', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
        ('escalated', 'Escalated'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='content_reports_made'
    )

    # Generic foreign key to report any content type
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Report details
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(
        max_length=500,
        blank=True,
        help_text="Additional details about the report"
    )

    # Status and review
    status = models.CharField(
        max_length=20,
        choices=REPORT_STATUS,
        default='pending'
    )

    # Moderation details
    reviewed_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_reviews'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    action_taken = models.CharField(
        max_length=100,
        blank=True,
        help_text="Action taken by moderator"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Prevent duplicate reports and index for performance."""
        unique_together = ('reporter', 'content_type', 'object_id')
        indexes = [
            models.Index(fields=['reporter', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['reason', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['reviewed_by', '-reviewed_at']),
        ]

    def __str__(self):
        return (
            f"Report by {self.reporter.user.username}: "
            f"{self.reason} - {self.status}"
        )


class MediaMetadata(models.Model):
    """Additional metadata for media files."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post_media = models.OneToOneField(
        PostMedia,
        on_delete=models.CASCADE,
        related_name='metadata'
    )

    # File information
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    original_filename = models.CharField(
        max_length=255,
        blank=True,
        help_text="Original filename when uploaded"
    )

    # Media-specific metadata
    duration = models.DurationField(
        null=True,
        blank=True,
        help_text="Duration for video/audio files"
    )
    dimensions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Width and height for images/videos"
    )

    # Accessibility
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alternative text for accessibility"
    )

    # Technical metadata
    mime_type = models.CharField(max_length=100, blank=True)
    encoding = models.CharField(max_length=50, blank=True)
    quality = models.CharField(
        max_length=20,
        blank=True,
        help_text="Quality setting (e.g., high, medium, low)"
    )

    # Processing flags
    is_processed = models.BooleanField(
        default=False,
        help_text="Whether media processing is complete"
    )
    processing_error = models.TextField(
        blank=True,
        help_text="Error message if processing failed"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Indexes for performance optimization."""

        indexes = [
            models.Index(fields=['post_media']),
            models.Index(fields=['mime_type']),
            models.Index(fields=['is_processed']),
        ]

    def __str__(self):
        return f"Metadata for {self.post_media}"


class BotDetectionProfile(models.Model):
    """Profile for tracking user behavior patterns to detect bots."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='bot_detection_profile'
    )

    # Bot detection scores (0.0-1.0, higher = more likely to be a bot)
    overall_bot_score = models.FloatField(
        default=0.0,
        help_text="Overall bot probability score 0.0-1.0"
    )
    timing_score = models.FloatField(
        default=0.0,
        help_text="Bot score based on posting timing patterns"
    )
    content_score = models.FloatField(
        default=0.0,
        help_text="Bot score based on content patterns"
    )
    behavior_score = models.FloatField(
        default=0.0,
        help_text="Bot score based on user behavior patterns"
    )

    # Additional pattern scores for tests
    activity_pattern_score = models.FloatField(
        default=0.0,
        help_text="Activity pattern analysis score"
    )
    content_pattern_score = models.FloatField(
        default=0.0,
        help_text="Content pattern analysis score"
    )
    interaction_pattern_score = models.FloatField(
        default=0.0,
        help_text="Interaction pattern analysis score"
    )
    temporal_pattern_score = models.FloatField(
        default=0.0,
        help_text="Temporal pattern analysis score"
    )

    # Behavior analysis JSON field
    behavior_analysis = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed behavior analysis data"
    )

    # Timing analysis
    avg_posting_interval = models.FloatField(
        null=True,
        blank=True,
        help_text="Average seconds between posts"
    )
    posting_regularity_score = models.FloatField(
        default=0.0,
        help_text=(
            "How regular posting intervals are "
            "(0=random, 1=very regular)"
        )
    )
    rapid_posting_incidents = models.IntegerField(
        default=0,
        help_text="Number of times user posted very rapidly"
    )

    # Content analysis
    duplicate_content_ratio = models.FloatField(
        default=0.0,
        help_text="Ratio of duplicate/similar content 0.0-1.0"
    )
    link_spam_score = models.FloatField(
        default=0.0,
        help_text="Score for excessive link posting"
    )
    engagement_ratio = models.FloatField(
        default=0.0,
        help_text="Ratio of posts to received engagement"
    )

    # Behavior patterns
    follows_to_followers_ratio = models.FloatField(
        default=0.0,
        help_text="Ratio of following to followers"
    )
    profile_completeness_score = models.FloatField(
        default=0.0,
        help_text="How complete the user profile is"
    )

    # Status
    is_flagged_as_bot = models.BooleanField(
        default=False,
        help_text="Whether user is flagged as suspected bot"
    )
    is_verified_human = models.BooleanField(
        default=False,
        help_text="Whether user has been verified as human"
    )
    auto_blocked = models.BooleanField(
        default=False,
        help_text="Whether user has been automatically blocked as bot"
    )

    # Additional status fields for tests
    is_flagged = models.BooleanField(
        default=False,
        help_text="General flagged status"
    )
    flagged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user was flagged"
    )

    # Analysis metadata
    last_analysis = models.DateTimeField(null=True, blank=True)
    analysis_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history



    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        indexes = [
            models.Index(fields=['overall_bot_score']),
            models.Index(fields=['is_flagged_as_bot']),
            models.Index(fields=['auto_blocked']),
            models.Index(fields=['last_analysis']),
        ]

    def __str__(self):
        return f"Bot Detection for {self.user.user.username} (Score: {self.overall_bot_score:.2f})"

    @property
    def is_likely_bot(self):
        """Check if user is likely a bot based on score threshold."""
        return self.overall_bot_score >= 0.7

    @property
    def requires_review(self):
        """Check if profile requires human review."""
        return self.overall_bot_score >= 0.5 and not self.is_verified_human


class BotDetectionEvent(models.Model):
    """Individual bot detection events and incidents."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    EVENT_TYPES = [
        ('rapid_posting', 'Rapid Posting'),
        ('duplicate_content', 'Duplicate Content'),
        ('spam_links', 'Spam Links'),
        ('unusual_timing', 'Unusual Timing Pattern'),
        ('fake_engagement', 'Fake Engagement'),
        ('profile_suspicious', 'Suspicious Profile'),
        ('mass_following', 'Mass Following'),
        ('copy_paste', 'Copy-Paste Content'),
        ('automated_behavior', 'Automated Behavior'),
    ]

    SEVERITY_LEVELS = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
    ]

    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='bot_detection_events'
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    severity = models.IntegerField(choices=SEVERITY_LEVELS, default=2)

    # Event details
    description = models.TextField(max_length=500)
    confidence_score = models.FloatField(
        help_text="Confidence in bot detection 0.0-1.0"
    )

    # Additional fields for tests
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed event information"
    )
    detected_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the bot behavior was detected"
    )

    # Related content
    related_post = models.ForeignKey(
        Post,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bot_detection_events'
    )
    related_comment = models.ForeignKey(
        Comment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bot_detection_events'
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional event-specific data"
    )

    # Actions taken
    action_taken = models.CharField(
        max_length=100,
        blank=True,
        help_text="Automatic action taken"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history



    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['confidence_score']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.user.user.username} (Severity: {self.severity})"


class UserActivityPattern(models.Model):
    """Track user activity patterns for bot detection."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='activity_patterns'
    )

    # Time-based patterns
    date = models.DateField()
    hour = models.IntegerField(help_text="Hour of day 0-23")

    # Activity counts
    posts_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    likes_count = models.IntegerField(default=0)
    follows_count = models.IntegerField(default=0)

    # Timing analysis
    avg_interval_between_actions = models.FloatField(
        null=True,
        blank=True,
        help_text="Average seconds between actions"
    )
    min_interval_between_actions = models.FloatField(
        null=True,
        blank=True,
        help_text="Minimum seconds between actions"
    )

    # Behavior flags
    rapid_activity_detected = models.BooleanField(default=False)
    suspicious_patterns = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history



    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        unique_together = ('user', 'date', 'hour')
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date', 'hour']),
            models.Index(fields=['rapid_activity_detected']),
        ]

    def __str__(self):
        return f"{self.user.user.username} - {self.date} {self.hour}:00"


class ContentModerationRule(models.Model):
    """Rules for automatic content moderation."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    RULE_TYPES = [
        ('keyword', 'Keyword Filter'),
        ('ml_toxicity', 'ML Toxicity Detection'),
        ('ml_spam', 'ML Spam Detection'),
        ('sentiment', 'Sentiment Analysis'),
        ('image_content', 'Image Content Analysis'),
        ('video_content', 'Video Content Analysis'),
        ('audio_content', 'Audio Content Analysis'),
        ('link_safety', 'Link Safety Check'),
        ('language_detection', 'Language Detection'),
    ]

    ACTION_TYPES = [
        ('flag', 'Flag for Review'),
        ('hide', 'Hide Content'),
        ('delete', 'Delete Content'),
        ('warn_user', 'Warn User'),
        ('restrict_user', 'Restrict User'),
        ('escalate', 'Escalate to Human Moderator'),
    ]

    name = models.CharField(max_length=100, unique=True)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    description = models.TextField(max_length=500)

    # Rule configuration (JSON field for flexibility)
    configuration = models.JSONField(
        default=dict,
        help_text="Rule-specific configuration (keywords, thresholds, etc.)"
    )

    # Additional fields for tests
    pattern_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Pattern matching data for the rule"
    )
    severity = models.IntegerField(
        default=1,
        help_text="Rule severity level"
    )

    # Action to take when rule is triggered
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    severity_level = models.IntegerField(
        default=1,
        help_text="Severity level 1-10, affects escalation priority"
    )

    # Rule status
    is_active = models.BooleanField(default=True)
    applies_to_posts = models.BooleanField(default=True)
    applies_to_comments = models.BooleanField(default=True)

    # Community-specific rules
    community = models.ForeignKey(
        'communities.Community',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='moderation_rules',
        help_text="If set, rule applies only to this community"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_moderation_rules'
    )

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history



    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['rule_type', 'is_active']),
            models.Index(fields=['community', 'is_active']),
            models.Index(fields=['severity_level', '-created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.rule_type})"


class ContentAnalysis(models.Model):
    """ML-based analysis results for content."""
    ANALYSIS_TYPES = [
        ('sentiment', 'Sentiment Analysis'),
        ('toxicity', 'Toxicity Detection'),
        ('spam', 'Spam Detection'),
        ('language', 'Language Detection'),
        ('topic', 'Topic Classification'),
        ('emotion', 'Emotion Detection'),
        ('hate_speech', 'Hate Speech Detection'),
        ('violence', 'Violence Detection'),
        ('adult_content', 'Adult Content Detection'),
    ]

    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
        ('mixed', 'Mixed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Generic foreign key to analyze any content type
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES)

    # Sentiment analysis results
    sentiment = models.CharField(
        max_length=10,
        choices=SENTIMENT_CHOICES,
        null=True,
        blank=True
    )
    sentiment_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence score 0.0-1.0"
    )

    # Toxicity/moderation scores
    toxicity_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Toxicity score 0.0-1.0"
    )
    spam_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Spam probability 0.0-1.0"
    )
    hate_speech_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Hate speech probability 0.0-1.0"
    )
    violence_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Violence content probability 0.0-1.0"
    )
    adult_content_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Adult content probability 0.0-1.0"
    )

    # Language detection
    detected_language = models.CharField(
        max_length=10,
        blank=True,
        help_text="ISO language code (e.g., 'en', 'fr', 'es')"
    )
    language_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Language detection confidence 0.0-1.0"
    )

    # Topic classification
    topics = models.JSONField(
        default=list,
        blank=True,
        help_text="List of detected topics with confidence scores"
    )

    # Emotion detection
    emotions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Emotion scores (joy, anger, fear, etc.)"
    )

    # ML model information
    model_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name/version of the ML model used"
    )
    model_version = models.CharField(max_length=50, blank=True)

    # Processing metadata
    processing_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Processing time in seconds"
    )
    is_human_verified = models.BooleanField(
        default=False,
        help_text="Whether results have been verified by human moderator"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history



    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # Allow multiple analysis types for the same content
        unique_together = ('content_type', 'object_id', 'analysis_type')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['analysis_type', '-created_at']),
            models.Index(fields=['sentiment', '-created_at']),
            models.Index(fields=['toxicity_score']),
            models.Index(fields=['spam_score']),
            models.Index(fields=['hate_speech_score']),
            models.Index(fields=['detected_language']),
            models.Index(fields=['is_human_verified']),
        ]

    def __str__(self):
        return f"{self.analysis_type} analysis for {self.content_object}"

    @property
    def overall_risk_score(self):
        """Calculate overall risk score based on all available scores."""
        scores = []
        if self.toxicity_score is not None:
            scores.append(self.toxicity_score)
        if self.spam_score is not None:
            scores.append(self.spam_score)
        if self.hate_speech_score is not None:
            scores.append(self.hate_speech_score)
        if self.violence_score is not None:
            scores.append(self.violence_score)
        if self.adult_content_score is not None:
            scores.append(self.adult_content_score)

        return max(scores) if scores else 0.0

    @property
    def requires_moderation(self):
        """Check if content requires human moderation based on scores."""
        high_risk_threshold = 0.7
        return self.overall_risk_score >= high_risk_threshold


class AutoModerationAction(models.Model):
    """Actions taken by the automatic moderation system."""
    ACTION_TYPES = [
        ('flagged', 'Content Flagged'),
        ('hidden', 'Content Hidden'),
        ('deleted', 'Content Deleted'),
        ('user_warned', 'User Warned'),
        ('user_restricted', 'User Restricted'),
        ('escalated', 'Escalated to Human'),
        ('approved', 'Content Approved'),
        ('rejected', 'Content Rejected'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('overridden', 'Overridden by Human'),
        ('expired', 'Expired'),
        ('appealed', 'Under Appeal'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Content that was moderated
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # User who created the content
    target_user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='auto_moderation_actions_received'
    )

    # Action details
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    reason = models.TextField(max_length=1000)

    # Additional fields for tests
    rule = models.ForeignKey(
        ContentModerationRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actions_taken'
    )
    action_taken = models.CharField(
        max_length=50,
        blank=True,
        help_text="Specific action taken"
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional action details"
    )

    # Related analysis and rules
    triggered_by_analysis = models.ForeignKey(
        ContentAnalysis,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_actions'
    )
    triggered_by_rule = models.ForeignKey(
        ContentModerationRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_actions'
    )

    # Confidence and severity
    confidence_score = models.FloatField(
        help_text="Confidence in the moderation decision 0.0-1.0"
    )
    severity_level = models.IntegerField(
        default=1,
        help_text="Severity level 1-10"
    )

    # Status and review
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # Human review
    reviewed_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auto_moderation_actions_reviewed'
    )
    review_decision = models.CharField(
        max_length=20,
        blank=True,
        help_text="Human moderator's decision"
    )
    review_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When action expires (for temporary actions)"
    )

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history


    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['target_user', '-created_at']),
            models.Index(fields=['action_type', 'status']),
            models.Index(fields=['severity_level', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['reviewed_by', '-reviewed_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        target = (self.target_user.user.username
                  if self.target_user else "Unknown")
        return f"{self.action_type} for {target} - {self.status}"


class ModerationQueue(models.Model):
    """Queue for content that needs human review."""
    PRIORITY_LEVELS = [
        (1, 'Low'),
        (2, 'Normal'),
        (3, 'High'),
        (4, 'Critical'),
        (5, 'Emergency'),
    ]

    QUEUE_STATUS = [
        ('pending', 'Pending Review'),
        ('in_review', 'In Review'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Content to be reviewed
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Queue details
    priority = models.IntegerField(choices=PRIORITY_LEVELS, default=2)
    status = models.CharField(
        max_length=20,
        choices=QUEUE_STATUS,
        default='pending'
    )

    # Reason for review
    reason = models.TextField(max_length=500)
    auto_moderation_action = models.ForeignKey(
        AutoModerationAction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='queue_entries'
    )

    # Additional fields for tests
    created_by_rule = models.ForeignKey(
        ContentModerationRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_queue_items'
    )
    escalated = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_queue_items'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Assignment
    assigned_to = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_moderation_queue'
    )

    # Resolution
    resolved_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_moderation_queue'
    )
    resolution_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When queue item expires if not reviewed"
    )

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'priority', '-created_at']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['resolved_by', '-resolved_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Queue item: {self.reason} - {self.status} (Priority: {self.priority})"


class ContentRecommendation(models.Model):
    """Store content recommendations for users."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    RECOMMENDATION_TYPES = [
        ('content_based', 'Content Based'),
        ('collaborative', 'Collaborative Filtering'),
        ('trending', 'Trending Content'),
        ('trending_24h', 'Trending 24 Hours'),
        ('trending_week', 'Trending This Week'),
        ('geo_based', 'Geographical Based'),
        ('popular', 'Popular Content'),
        ('similar_users', 'Similar Users'),
        ('hashtag_based', 'Hashtag Based'),
        ('manual', 'Manual Recommendation'),
    ]

    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Recommendation metadata
    score = models.FloatField(help_text="Recommendation score between 0 and 1")
    reason = models.TextField(
        blank=True,
        help_text="Human-readable reason for recommendation"
    )
    recommendation_type = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_TYPES,
        default='content_based'
    )
    rank = models.PositiveIntegerField(
        default=0,
        help_text="Rank in the recommendation list"
    )

    # Algorithm details
    algorithm_version = models.CharField(max_length=20, default="v1.0")
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional algorithm-specific metadata"
    )

    # Tracking fields
    is_viewed = models.BooleanField(default=False)
    is_clicked = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this recommendation expires"
    )

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        indexes = [
            models.Index(fields=['user', '-score', '-created_at']),
            models.Index(fields=['user', 'recommendation_type']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-score', '-created_at']

    def __str__(self):
        return (
            f"Rec {self.user.user.username}: {self.content_object} "
            f"({self.score:.2f})"
        )

    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def mark_viewed(self):
        if not self.is_viewed:
            self.is_viewed = True
            self.viewed_at = timezone.now()
            self.save(update_fields=['is_viewed', 'viewed_at'])

    def mark_clicked(self):
        updates = []
        now = timezone.now()
        if not self.is_viewed:
            self.is_viewed = True
            self.viewed_at = now
            updates += ['is_viewed', 'viewed_at']
        if not self.is_clicked:
            self.is_clicked = True
            self.clicked_at = now
            updates += ['is_clicked', 'clicked_at']
        if updates:
            self.save(update_fields=updates)


class ContentSimilarity(models.Model):
    """Store similarity scores between content items."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type_1 = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='similarity_as_content_1'
    )
    object_id_1 = models.UUIDField()
    content_object_1 = GenericForeignKey('content_type_1', 'object_id_1')

    content_type_2 = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='similarity_as_content_2'
    )
    object_id_2 = models.UUIDField()
    content_object_2 = GenericForeignKey('content_type_2', 'object_id_2')

    similarity_score = models.FloatField(
        help_text="Similarity score between 0 and 1"
    )
    similarity_type = models.CharField(
        max_length=20,
        choices=[
            ('content', 'Content Similarity'),
            ('hashtag', 'Hashtag Similarity'),
            ('author', 'Author Similarity'),
            ('engagement', 'Engagement Similarity'),
            ('combined', 'Combined Similarity'),
        ],
        default='combined'
    )

    calculated_at = models.DateTimeField(auto_now_add=True)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(
                fields=['content_type_1', 'object_id_1', '-similarity_score']
            ),
            models.Index(
                fields=['content_type_2', 'object_id_2', '-similarity_score']
            ),
            models.Index(fields=['calculated_at']),
        ]
        unique_together = (
            'content_type_1', 'object_id_1',
            'content_type_2', 'object_id_2',
            'similarity_type'
        )

    def __str__(self):
        return (
            f"Sim {self.similarity_type} {self.object_id_1} -> "
            f"{self.object_id_2} {self.similarity_score:.3f}"
        )


class UserContentPreferences(models.Model):
    """Store user content preferences derived from behavior analysis."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='content_preferences'
    )

    # Hashtag preferences (JSON field with hashtag names and scores)
    preferred_hashtags = models.JSONField(
        default=dict,
        help_text="Dictionary of hashtag names to preference scores"
    )

    # Content type preferences
    preferred_content_types = models.JSONField(
        default=dict,
        help_text="Dictionary of content types to preference scores"
    )

    # Engagement pattern preferences
    interaction_patterns = models.JSONField(
        default=dict,
        help_text="User interaction behavior patterns"
    )

    # Time-based preferences
    active_hours = models.JSONField(
        default=list,
        help_text="Hours (0-23) when user is most active"
    )

    # Content length preferences
    preferred_content_length = models.PositiveIntegerField(
        default=0,
        help_text="Avg preferred content length"
    )

    # Community preferences
    preferred_communities = models.JSONField(
        default=dict,
        help_text="Map of community IDs to preference scores"
    )

    total_interactions = models.PositiveIntegerField(default=0)
    analysis_period_days = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_analysis_at = models.DateTimeField(auto_now=True)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return (
            f"Prefs {self.user.user.username} (interactions="
            f"{self.total_interactions})"
        )

    def get_top_hashtags(self, limit=10):
        """Get user's top preferred hashtags"""
        if not self.preferred_hashtags:
            return []

        sorted_hashtags = sorted(
            self.preferred_hashtags.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [hashtag for hashtag, score in sorted_hashtags[:limit]]

    def get_hashtag_score(self, hashtag_name):
        """Get preference score for a specific hashtag"""
        return self.preferred_hashtags.get(hashtag_name, 0.0)

    def is_analysis_stale(self, days=7):
        """Check if preferences analysis is stale"""
        from django.utils import timezone
        return (timezone.now() - self.last_analysis_at).days > days


class RecommendationFeedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='recommendation_feedback'
    )
    recommendation = models.ForeignKey(
        ContentRecommendation,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    rating = models.IntegerField(
        default=0,
        help_text="Rating (-1,0,1 or extended scale)"
    )
    feedback = models.CharField(
        max_length=50,
        blank=True,
        help_text="Short tag (relevant/not_relevant/spam)"
    )
    comments = models.TextField(
        blank=True,
        help_text="Optional comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'recommendation')
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['rating']),
            models.Index(fields=['feedback']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"Feedback {self.rating} by {self.user.user.username} "
            f"on {self.recommendation_id}"
        )


# =============================================================================
# A/B TESTING MODELS FOR CONTENT RECOMMENDATION EXPERIMENTATION
# =============================================================================

class ContentExperiment(models.Model):
    """Model to track A/B testing experiments for content recommendation algorithms."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ALGORITHM_CHOICES = [
        ('content_based', 'Content Based'),
        ('collaborative', 'Collaborative Filtering'),
        ('trending', 'Trending Content'),
        ('trending_24h', 'Trending 24 Hours'),
        ('trending_week', 'Trending This Week'),
        ('geo_based', 'Geographical Based'),
        ('popular', 'Popular Content'),
        ('similar_users', 'Similar Users'),
        ('hashtag_based', 'Hashtag Based'),
        ('manual', 'Manual Recommendation'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Experiment name"
    )
    description = models.TextField(
        blank=True,
        help_text="Experiment description"
    )

    # Algorithm configurations for testing
    control_algorithm = models.CharField(
        max_length=50,
        choices=ALGORITHM_CHOICES,
        default='hybrid',
        help_text="Control algorithm (baseline)"
    )

    test_algorithm = models.CharField(
        max_length=50,
        choices=ALGORITHM_CHOICES,
        help_text="Test algorithm (variant)"
    )

    # Experiment configuration
    traffic_split = models.FloatField(
        default=0.5,
        help_text="Percentage of users in test group (0.0-1.0)"
    )

    # Status and timing
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='created_content_experiments'
    )

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""
        from django.utils import timezone

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Content Experiment'
        verbose_name_plural = 'Content Experiments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"

    def clean(self):
        """Validate model fields."""
        from django.core.exceptions import ValidationError  # needed later
        if self.traffic_split < 0 or self.traffic_split > 1:
            raise ValidationError("Traffic split must be between 0 and 1")
        if self.control_algorithm == self.test_algorithm:
            raise ValidationError("Control and test algorithms must be different")

    @property
    def is_active(self):
        """Check if experiment is currently active."""
        now = timezone.now()
        return (
            self.status == 'active' and
            (self.start_date is None or self.start_date <= now) and
            (self.end_date is None or self.end_date >= now)
        )


class UserContentExperimentAssignment(models.Model):
    """Model to track which users are assigned to which content experiment groups."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    GROUP_CHOICES = [
        ('control', 'Control Group'),
        ('test', 'Test Group'),
    ]

    user = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='content_experiment_assignments'
    )
    experiment = models.ForeignKey(
        ContentExperiment,
        on_delete=models.CASCADE,
        related_name='user_assignments'
    )

    group = models.CharField(
        max_length=20,
        choices=GROUP_CHOICES
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'User Content Experiment Assignment'
        verbose_name_plural = 'User Content Experiment Assignments'
        unique_together = ['user', 'experiment']
        indexes = [
            models.Index(fields=['user', 'experiment']),
            models.Index(fields=['experiment', 'group']),
        ]

    def __str__(self):
        return f"{self.user.user.username} - {self.experiment.name} ({self.group})"


class ContentExperimentMetric(models.Model):
    """Model to track metrics and results for content A/B testing experiments."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    METRIC_TYPE_CHOICES = [
        ('recommendation_view', 'Recommendation View'),
        ('recommendation_click', 'Recommendation Click'),
        ('post_like', 'Post Like'),
        ('post_dislike', 'Post Dislike'),
        ('post_comment', 'Post Comment'),
        ('post_share', 'Post Share'),
        ('post_repost', 'Post Repost'),
        ('content_engagement', 'Content Engagement'),
        ('session_duration', 'Session Duration'),
        ('algorithm_response_time', 'Algorithm Response Time'),
        ('recommendation_accuracy', 'Recommendation Accuracy'),
        ('user_satisfaction', 'User Satisfaction'),
        ('click_through_rate', 'Click Through Rate'),
        ('conversion_rate', 'Conversion Rate'),
    ]

    experiment = models.ForeignKey(
        ContentExperiment,
        on_delete=models.CASCADE,
        related_name='metrics'
    )
    user = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='content_experiment_metrics'
    )

    # Metric types
    metric_type = models.CharField(
        max_length=50,
        choices=METRIC_TYPE_CHOICES
    )

    # Metric values
    value = models.FloatField(
        help_text="Metric value (response time, accuracy score, etc.)"
    )
    count = models.IntegerField(
        default=1,
        help_text="Number of occurrences"
    )

    # Additional context
    algorithm_used = models.CharField(
        max_length=50,
        choices=ContentExperiment.ALGORITHM_CHOICES
    )

    # Related content
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Metadata
    recorded_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metric context"
    )

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Content Experiment Metric'
        verbose_name_plural = 'Content Experiment Metrics'
        indexes = [
            models.Index(fields=['experiment', 'metric_type']),
            models.Index(fields=['user', 'experiment']),
            models.Index(fields=['recorded_at']),
            models.Index(fields=['algorithm_used', 'metric_type']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.experiment.name} - {self.metric_type}: {self.value}"


class ContentExperimentResult(models.Model):
    """Model to store aggregated results and analysis for content experiments."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    WINNER_CHOICES = [
        ('control', 'Control Algorithm'),
        ('test', 'Test Algorithm'),
        ('inconclusive', 'Inconclusive'),
    ]

    experiment = models.OneToOneField(
        ContentExperiment,
        on_delete=models.CASCADE,
        related_name='result'
    )

    # Statistical results
    control_sample_size = models.IntegerField(default=0)
    test_sample_size = models.IntegerField(default=0)

    # Key metrics comparison
    control_avg_response_time = models.FloatField(null=True, blank=True)
    test_avg_response_time = models.FloatField(null=True, blank=True)

    control_avg_accuracy = models.FloatField(null=True, blank=True)
    test_avg_accuracy = models.FloatField(null=True, blank=True)

    control_engagement_rate = models.FloatField(null=True, blank=True)
    test_engagement_rate = models.FloatField(null=True, blank=True)

    control_click_through_rate = models.FloatField(null=True, blank=True)
    test_click_through_rate = models.FloatField(null=True, blank=True)

    control_conversion_rate = models.FloatField(null=True, blank=True)
    test_conversion_rate = models.FloatField(null=True, blank=True)

    # Statistical significance
    p_value = models.FloatField(
        null=True,
        blank=True,
        help_text="Statistical significance p-value"
    )
    confidence_interval = models.JSONField(
        default=dict,
        blank=True,
        help_text="95% confidence interval"
    )

    # Conclusions
    winner = models.CharField(
        max_length=20,
        choices=WINNER_CHOICES,
        null=True,
        blank=True
    )

    improvement_percentage = models.FloatField(
        null=True,
        blank=True,
        help_text="Percentage improvement of winner over loser"
    )

    # Analysis details
    summary = models.TextField(
        blank=True,
        help_text="Executive summary of results"
    )
    detailed_analysis = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed statistical analysis"
    )

    # Metadata
    analyzed_at = models.DateTimeField(auto_now_add=True)
    analyzed_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def restore_instance(self, cascade=True):
        """Restore this soft-deleted instance and optionally cascade to related objects."""
        from django.utils import timezone

        if not self.is_deleted:
            return False, f"{self.__class__.__name__} is not deleted"

        # Store the deletion timestamp before restoring
        self.last_deletion_at = self.deleted_at

        # Restore the instance
        self.is_deleted = False
        self.deleted_at = None
        self.is_restored = True
        self.restored_at = timezone.now()

        self.save(update_fields=[
            'is_deleted', 'deleted_at', 'is_restored',
            'restored_at', 'last_deletion_at'
        ])

        restored_count = 1

        if cascade:
            # Cascade restore to related objects
            related_count = self._cascade_restore_related()
            restored_count += related_count

        return True, f"{self.__class__.__name__} and {restored_count} related objects restored successfully"

    def _cascade_restore_related(self):
        """Cascade restore to related objects."""
        restored_count = 0

        # Get all reverse foreign key relationships
        for rel in self._meta.get_fields():
            if hasattr(rel, 'related_model') and hasattr(rel, 'remote_field'):
                if rel.remote_field and hasattr(rel.remote_field, 'name'):
                    try:
                        related_manager = getattr(self, rel.get_accessor_name())

                        # Find soft-deleted related objects
                        if hasattr(related_manager, 'filter'):
                            deleted_related = related_manager.filter(is_deleted=True)

                            for related_obj in deleted_related:
                                if hasattr(related_obj, 'restore_instance'):
                                    success, message = related_obj.restore_instance(cascade=False)
                                    if success:
                                        restored_count += 1

                    except (AttributeError, Exception):
                        # Skip relationships that can't be processed
                        continue

        # Handle ManyToMany relationships
        for field in self._meta.many_to_many:
            try:
                related_manager = getattr(self, field.name)
                if hasattr(related_manager, 'filter'):
                    deleted_related = related_manager.filter(is_deleted=True)

                    for related_obj in deleted_related:
                        if hasattr(related_obj, 'restore_instance'):
                            success, message = related_obj.restore_instance(cascade=False)
                            if success:
                                restored_count += 1

            except (AttributeError, Exception):
                continue

        return restored_count

    @classmethod
    def bulk_restore(cls, queryset=None, cascade=True):
        """Bulk restore multiple instances."""

        if queryset is None:
            queryset = cls.objects.filter(is_deleted=True)
        else:
            queryset = queryset.filter(is_deleted=True)

        if not queryset.exists():
            return 0, "No deleted objects found to restore"

        restored_objects = []
        total_restored = 0

        for obj in queryset:
            try:
                success, message = obj.restore_instance(cascade=cascade)
                if success:
                    restored_objects.append(obj)
                    total_restored += 1
            except Exception as e:
                print(f"Error restoring {obj}: {e}")
                continue

        return total_restored, f"Successfully restored {total_restored} {cls.__name__} objects"

    def get_restoration_history(self):
        """Get the restoration history of this object."""
        history = {
            'is_currently_deleted': self.is_deleted,
            'is_restored': self.is_restored,
            'last_restoration': self.restored_at,
            'last_deletion': self.last_deletion_at,
            'deletion_restoration_cycle': None
        }

        if self.last_deletion_at and self.restored_at:
            if self.restored_at > self.last_deletion_at:
                history['deletion_restoration_cycle'] = {
                    'deleted_at': self.last_deletion_at,
                    'restored_at': self.restored_at,
                    'cycle_duration': self.restored_at - self.last_deletion_at
                }

        return history

    # Soft delete field
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)
    # Restoration tracking fields
    is_restored = models.BooleanField(default=False)
    restored_at = models.DateTimeField(null=True, blank=True)
    last_deletion_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Content Experiment Result'
        verbose_name_plural = 'Content Experiment Results'

    def __str__(self):
        return f"Results for {self.experiment.name}"

    @property
    def is_significant(self):
        """Check if results are statistically significant (p-value < 0.05)."""
        return self.p_value is not None and self.p_value < 0.05


# NOTE: Post.shares_count reflects ONLY DirectShare (private) interactions.
#       Post.repost_count reflects ONLY Repost (public feed) interactions.
#       These counters are independent and not summed automatically.

# Compatibility aliases for older imports/tests
# Keep these at EOF so classes referenced are already defined.
try:
    Repost = Post
    Share = DirectShare
except NameError:
    # If models are not yet defined during some import paths, ignore.
    Repost = None
    Share = None

