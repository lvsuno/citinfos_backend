from celery import shared_task
from django.utils import timezone
from django.db.models import Count, F
from django.conf import settings
from datetime import timedelta
from content.models import (
    Post, Comment, PostReaction, CommentReaction, Hashtag, Mention,
    BotDetectionEvent, UserActivityPattern,
    ContentAnalysis, AutoModerationAction, ModerationQueue, DirectShare
)
from accounts.models import UserProfile
from analytics.models import ErrorLog


# =============================================================================
# CONTENT MODERATION AND BOT DETECTION TASKS
# =============================================================================

@shared_task
def process_bot_detection_analysis():
    """Analyze user behavior patterns for bot detection"""
    try:
        from content.utils import update_bot_detection_profile
        from accounts.models import UserProfile

        # Get users who have been active in the last 24 hours
        recent_users = UserProfile.objects.filter(
            last_active__gte=timezone.now() - timedelta(hours=24)
        )

        updated_profiles = 0
        for user in recent_users:
            try:
                # Update bot detection profile
                profile = update_bot_detection_profile(user)
                if profile.overall_bot_score > 0.7:  # Flag threshold
                    # Log high-risk detection
                    BotDetectionEvent.objects.create(
                        user=user,
                        event_type='high_risk_profile',
                        severity=3,
                        confidence_score=profile.overall_bot_score,
                        description=(
                            f'User flagged with bot score: '
                            f'{profile.overall_bot_score:.2f}'
                        )
                    )
                updated_profiles += 1

            except Exception as e:
                ErrorLog.objects.create(
                    level='error',
                    message=(
                        f'Error updating bot profile for user {user.id}: '
                        f'{str(e)}'
                    ),
                    extra_data={
                        'user_id': str(user.id),
                        'task': 'process_bot_detection_analysis'
                    }
                )

        return f"Analyzed {updated_profiles} user profiles for bot detection"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error in bot detection analysis: {str(e)}',
            extra_data={'task': 'process_bot_detection_analysis'}
        )
        return f"Error in bot detection analysis: {str(e)}"


@shared_task
def cleanup_bot_detection_data():
    """Clean up old bot detection data."""
    try:
        # Remove old activity patterns (older than 90 days)
        old_patterns = UserActivityPattern.objects.filter(
            date__lt=timezone.now().date() - timedelta(days=90)
        )
        patterns_deleted = old_patterns.count()
        old_patterns.delete()

        # Archive old bot detection events (older than 180 days)
        old_events = BotDetectionEvent.objects.filter(
            detected_at__lt=timezone.now() - timedelta(days=180)
        )
        events_deleted = old_events.count()
        old_events.delete()

        return (
            f"Cleaned up {patterns_deleted} activity patterns and "
            f"{events_deleted} bot events"
        )

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error cleaning up bot detection data: {str(e)}',
            extra_data={'task': 'cleanup_bot_detection_data'}
        )
        return f"Error cleaning up bot detection data: {str(e)}"


@shared_task
def process_moderation_queue():
    """Process pending items in moderation queue."""
    try:
        from content.utils import check_moderation_rules

        # Get pending moderation items
        pending_items = ModerationQueue.objects.filter(
            status='pending',
            assigned_to__isnull=True  # Not assigned to a moderator
        ).order_by('priority', 'created_at')[:50]  # Process 50 at a time

        processed_count = 0
        for item in pending_items:
            try:
                # Re-analyze content with updated rules
                if item.content_object:
                    content_text = (
                        item.content_object.content
                        if hasattr(item.content_object, 'content')
                        else str(item.content_object)
                    )
                    analysis_result = check_moderation_rules(content_text)

                    # Update item with new analysis
                    item.analysis_result = analysis_result
                    item.last_reviewed = timezone.now()

                    # Auto-approve if confidence is low
                    if isinstance(analysis_result, dict):
                        confidence = analysis_result.get('max_confidence', 1.0)
                        if confidence < 0.3:
                            item.status = 'approved'
                            item.resolution = 'auto_approved_low_confidence'

                    item.save()
                    processed_count += 1

            except Exception as e:
                ErrorLog.objects.create(
                    level='error',
                    message=(
                        f'Error processing moderation item {item.id}: '
                        f'{str(e)}'
                    ),
                    extra_data={
                        'item_id': str(item.id),
                        'task': 'process_moderation_queue'
                    }
                )

        return f"Processed {processed_count} moderation queue items"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error processing moderation queue: {str(e)}',
            extra_data={'task': 'process_moderation_queue'}
        )
        return f"Error processing moderation queue: {str(e)}"


@shared_task
def update_moderation_analytics():
    """Update content moderation analytics."""
    try:
        from collections import defaultdict

        # Get moderation actions from last 24 hours
        recent_actions = AutoModerationAction.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        )

        analytics_data = {
            'total_actions': recent_actions.count(),
            'actions_by_type': defaultdict(int),
            'rules_triggered': defaultdict(int),
            'confidence_distribution': {
                'high': 0,  # > 0.8
                'medium': 0,  # 0.5-0.8
                'low': 0  # < 0.5
            }
        }

        for action in recent_actions:
            analytics_data['actions_by_type'][action.action] += 1
            analytics_data['rules_triggered'][action.rule.name] += 1

            # Confidence distribution
            if action.confidence_score > 0.8:
                analytics_data['confidence_distribution']['high'] += 1
            elif action.confidence_score > 0.5:
                analytics_data['confidence_distribution']['medium'] += 1
            else:
                analytics_data['confidence_distribution']['low'] += 1

        # Convert defaultdict to regular dict
        analytics_data['actions_by_type'] = dict(
            analytics_data['actions_by_type']
        )
        analytics_data['rules_triggered'] = dict(
            analytics_data['rules_triggered']
        )

        # Log analytics (you might want to store this in a dedicated model)
        ErrorLog.objects.create(
            level='info',
            message='Daily moderation analytics generated',
            extra_data=analytics_data
        )

        return (
            f"Generated moderation analytics: "
            f"{analytics_data['total_actions']} actions processed"
        )

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating moderation analytics: {str(e)}',
            extra_data={'task': 'update_moderation_analytics'}
        )
        return f"Error updating moderation analytics: {str(e)}"


# =============================================================================
# CONTENT ENGAGEMENT AND ANALYTICS TASKS
# =============================================================================

@shared_task
def update_content_counters():
    """Update reaction, comment, share counts for posts."""
    try:
        posts = Post.objects.filter(
            updated_at__gte=timezone.now() - timedelta(hours=1)
        )  # Only update recently active posts

        updated_count = 0
        for post in posts:
            try:
                # Count positive reactions (likes)
                likes_count = PostReaction.objects.filter(
                    post=post,
                    is_deleted=False,
                    reaction_type__in=PostReaction.POSITIVE_REACTIONS
                ).count()

                # Count negative reactions (dislikes)
                dislikes_count = PostReaction.objects.filter(
                    post=post,
                    is_deleted=False,
                    reaction_type__in=PostReaction.NEGATIVE_REACTIONS
                ).count()

                comments_count = Comment.objects.filter(
                    post=post, is_deleted=False
                ).count()
                # Independent counters
                direct_shares_count = DirectShare.objects.filter(
                    post=post
                ).count()
                reposts_count = Post.objects.filter(
                    parent_post=post,
                    post_type='repost'
                ).count()

                if (post.likes_count != likes_count or
                        post.dislikes_count != dislikes_count or
                        post.comments_count != comments_count or
                        post.shares_count != direct_shares_count or
                        getattr(post, 'repost_count', 0) != reposts_count):

                    post.likes_count = likes_count
                    post.dislikes_count = dislikes_count
                    post.comments_count = comments_count
                    post.shares_count = direct_shares_count
                    if hasattr(post, 'repost_count'):
                        post.repost_count = reposts_count
                    post.save(update_fields=[
                        'likes_count', 'dislikes_count', 'comments_count', 'shares_count', 'repost_count'
                    ])
                    updated_count += 1

            except Exception as e:
                ErrorLog.objects.create(
                    level='error',
                    message=(
                        f'Error updating counters for post {post.id}: '
                        f'{str(e)}'
                    ),
                    extra_data={
                        'post_id': str(post.id),
                        'task': 'update_content_counters'
                    }
                )

        return f"Updated counters for {updated_count} posts"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating content counters: {str(e)}',
            extra_data={'task': 'update_content_counters'}
        )
        return f"Error updating content counters: {str(e)}"


@shared_task
def update_trending_hashtags():
    """Update trending hashtags based on recent activity."""
    try:
        # Calculate trending hashtags for the last 24 hours
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=24)

        # Get hashtags with activity in the last 24 hours
        from content.models import PostHashtag
        trending_hashtags = PostHashtag.objects.filter(
            created_at__gte=start_time,
            created_at__lt=end_time
        ).annotate(
            recent_mentions=Count('id')
        ).filter(recent_mentions__gt=0)

        # Update hashtag trending score for each hashtag
        for hashtag in trending_hashtags:
            # Simple engagement calculation
            engagement_score = hashtag.recent_mentions

            # Update hashtag trending score (if field exists)
            if hasattr(hashtag, 'trending_score'):
                hashtag.trending_score = engagement_score
                hashtag.save(update_fields=['trending_score'])

        # Mark top hashtags as trending
        Hashtag.objects.update(is_trending=False)
        top_trending = trending_hashtags.order_by('-recent_mentions')[:20]
        top_trending_ids = [h.id for h in top_trending]
        Hashtag.objects.filter(
            id__in=top_trending_ids
        ).update(is_trending=True)

        return f"Updated {trending_hashtags.count()} trending hashtags"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating trending hashtags: {str(e)}',
            extra_data={'task': 'update_trending_hashtags'}
        )
        return f"Error updating trending hashtags: {str(e)}"


@shared_task
def process_mentions():
    """Process recent mentions with user settings integration."""
    try:
        from notifications.utils import NotificationService

        # Get recent mentions from the last hour
        recent_mentions = Mention.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).select_related(
            'mentioned_user', 'mentioning_user', 'post', 'comment'
        )

        push_notifications_sent = 0
        email_notifications_sent = 0

        for mention in recent_mentions:
            try:
                mentioned_user = mention.mentioned_user
                user_settings = getattr(mentioned_user, 'settings', None)

                # Skip if user has disabled all notifications
                if (not user_settings or
                        user_settings.notification_frequency == 'never'):
                    continue

                # Determine content type and create appropriate message
                if mention.post:
                    content_title = f"Mentioned in post by {mention.mentioning_user.username}"
                    content_message = f"@{mention.mentioning_user.username} mentioned you in a post"
                    related_object = mention.post
                elif mention.comment:
                    content_title = f"Mentioned in comment by {mention.mentioning_user.username}"
                    content_message = f"@{mention.mentioning_user.username} mentioned you in a comment"
                    related_object = mention.comment
                else:
                    continue

                # Create push notification if enabled
                if user_settings.push_notifications:
                    push_notification = NotificationService.create_notification(
                        recipient=mentioned_user,
                        title=content_title,
                        message=content_message,
                        notification_type='mention',
                        related_object=related_object,
                        app_context='content',
                        extra_data={
                            'mention_id': str(mention.id),
                            'mentioner_id': str(mention.mentioning_user.id),
                            'mentioner_username': mention.mentioning_user.username,
                            'content_type': 'post' if mention.post else 'comment'
                        }
                    )

                    if push_notification:
                        push_notifications_sent += 1

                # Send email notification based on frequency
                should_email = (
                    user_settings.email_notifications and
                    user_settings.notification_frequency in
                    ['real_time', 'hourly', 'daily']
                )

                if should_email:
                    email_sent = NotificationService.send_email_notification(
                        recipient=mentioned_user,
                        subject=f'📢 {content_title}',
                        template='content/email/mention_notification.html',
                        context={
                            'recipient': mentioned_user,
                            'mentioner': mention.mentioning_user,
                            'mention': mention,
                            'content': related_object,
                            'content_type': 'post' if mention.post else 'comment'
                        }
                    )

                    if email_sent:
                        email_notifications_sent += 1

            except Exception as e:
                ErrorLog.objects.create(
                    level='warning',
                    message=f'Error creating mention notification: {str(e)}',
                    extra_data={
                        'mention_id': str(mention.id),
                        'task': 'process_mentions'
                    }
                )

        return (f"Processed {recent_mentions.count()} mentions, "
                f"sent {push_notifications_sent} push notifications "
                f"and {email_notifications_sent} emails")

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error processing mentions: {str(e)}',
            extra_data={'task': 'process_mentions'}
        )
        return f"Error processing mentions: {str(e)}"


@shared_task
def generate_content_recommendations():
    """Generate personalized content recommendations for all active users."""
    try:
        from accounts.models import UserProfile
        from content.utils import generate_user_recommendations

        # Get users active in the last 7 days
        active_users = UserProfile.objects.filter(
            last_active__gte=timezone.now() - timedelta(days=7)
        )

        recommendations_generated = 0
        for user in active_users:
            try:
                # Skip users flagged as bots
                bot_profile = getattr(user, 'bot_profile', None)
                if bot_profile and bot_profile.is_flagged_as_bot:
                    continue

                # Generate personalized recommendations
                # Update follower counts before generating recommendations
                if hasattr(user, 'update_follower_counts'):
                    user.update_follower_counts()
                recommendations = generate_user_recommendations(user)
                recommendations_generated += len(recommendations)

            except Exception as e:
                ErrorLog.objects.create(
                    level='error',
                    message=(
                        f'Error generating recommendations for user '
                        f'{user.id}: {str(e)}'
                    ),
                    extra_data={
                        'user_id': str(user.id),
                        'task': 'generate_content_recommendations'
                    }
                )

        return (
            f"Generated recommendations for {active_users.count()} users "
            f"({recommendations_generated} total recommendations)"
        )

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error generating recommendations: {str(e)}',
            extra_data={'task': 'generate_content_recommendations'}
        )
        return f"Error generating recommendations: {str(e)}"


@shared_task
def update_content_similarity_scores():
    """Update similarity scores between posts for better recommendations"""
    try:
        from content.utils import calculate_content_similarity

        # Get recent posts (last 7 days) to update similarity scores
        recent_posts = Post.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7),
            is_deleted=False,
            is_hidden=False
        )

        updated_pairs = 0
        for post in recent_posts:
            try:
                # Calculate similarity with other posts
                similar_posts = calculate_content_similarity(post)
                updated_pairs += len(similar_posts)

            except Exception as e:
                ErrorLog.objects.create(
                    level='warning',
                    message=f'Error calculating similarity for post {post.id}: {str(e)}',
                    extra_data={'post_id': post.id}
                )

        return f"Updated similarity scores for {updated_pairs} post pairs"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating similarity scores: {str(e)}',
            extra_data={'task': 'update_content_similarity_scores'}
        )
        return f"Error updating similarity scores: {str(e)}"


@shared_task
def generate_trending_content_recommendations():
    """Generate recommendations based on trending content"""
    try:
        from content.utils import get_trending_posts, create_trending_recommendations

        # Get trending posts from different time periods
        trending_24h = get_trending_posts(hours=24, limit=20)
        trending_week = get_trending_posts(days=7, limit=30)

        # Get users who haven't seen trending content
        active_users = UserProfile.objects.filter(
            last_active__gte=timezone.now() - timedelta(days=3)
        )

        recommendations_created = 0
        for user in active_users:
            try:
                # Create trending recommendations for user
                user_recommendations = create_trending_recommendations(
                    user, trending_24h, trending_week
                )
                recommendations_created += len(user_recommendations)

            except Exception as e:
                ErrorLog.objects.create(
                    level='warning',
                    message=f'Error creating trending recommendations for user {user.id}: {str(e)}',
                    extra_data={'user_id': user.id}
                )

        return f"Created {recommendations_created} trending content recommendations"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error generating trending recommendations: {str(e)}',
            extra_data={'task': 'generate_trending_content_recommendations'}
        )
        return f"Error generating trending recommendations: {str(e)}"


@shared_task
def update_user_content_preferences():
    """Update user content preferences based on engagement patterns"""
    try:
        from content.utils import analyze_user_content_preferences

        # Get users with recent activity
        active_users = UserProfile.objects.filter(
            last_active__gte=timezone.now() - timedelta(days=14)
        )

        updated_preferences = 0
        from content.models import UserContentPreferences
        for user in active_users:
            try:
                # Analyze user's content engagement patterns
                preferences = analyze_user_content_preferences(user)

                if preferences:
                    # Map analyze_user_content_preferences output to model fields
                    UserContentPreferences.objects.update_or_create(
                        user=user,
                        defaults={
                            'preferred_hashtags': preferences.get('top_hashtags', {}),
                            'preferred_content_types': preferences.get('top_content_types', {}),
                            'preferred_communities': preferences.get('top_communities', {}),
                            'interaction_patterns': preferences.get('interaction_patterns', {}),
                            'active_hours': list(preferences.get('preferred_hours', {}).keys()),
                            'preferred_content_length': int(preferences.get('avg_content_length', 0)),
                            'total_interactions': preferences.get('total_interactions', 0),
                            'analysis_period_days': preferences.get('analysis_period_days', 7),
                        }
                    )
                    updated_preferences += 1

            except Exception as e:
                ErrorLog.objects.create(
                    level='warning',
                    message=f'Error updating preferences for user {user.id}: {str(e)}',
                    extra_data={'user_id': str(user.id)}
                )

        return f"Updated content preferences for {updated_preferences} users"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating user preferences: {str(e)}',
            extra_data={'task': 'update_user_content_preferences'}
        )
        return f"Error updating user preferences: {str(e)}"


@shared_task
def generate_collaborative_filtering_recommendations():
    """Generate recommendations using collaborative filtering"""
    try:
        from content.utils import generate_collaborative_recommendations, get_user_interaction_frequency
        # Users active in last 30 days
        recent_users = UserProfile.objects.filter(
            last_active__gte=timezone.now() - timedelta(days=30)
        )
        eligible_users = []
        for user in recent_users:
            freq = get_user_interaction_frequency(user, days=30)
            if freq.get('total', 0) >= 10:  # At least 10 interactions
                eligible_users.append(user)
        recommendations_generated = 0
        for user in eligible_users:
            try:
                collab_recs = generate_collaborative_recommendations(user)
                recommendations_generated += len(collab_recs)
            except Exception as e:
                ErrorLog.objects.create(
                    level='warning',
                    message=(
                        f'Error generating collaborative recs for user '
                        f'{user.id}: {str(e)}'
                    ),
                    extra_data={'user_id': str(user.id)}
                )
        return (
            f"Generated {recommendations_generated} collaborative "
            f"filtering recommendations"
        )
    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error generating collaborative recommendations: {str(e)}',
            extra_data={'task': 'generate_collaborative_filtering_recommendations'}
        )
        return f"Error generating collaborative recommendations: {str(e)}"


@shared_task
def cleanup_old_recommendations():
    """Clean up old and expired recommendation data"""
    try:
        # Clean up recommendations older than 7 days
        try:
            from content.models import ContentRecommendation
            old_recommendations = ContentRecommendation.objects.filter(
                created_at__lt=timezone.now() - timedelta(days=7)
            )
            deleted_count = old_recommendations.count()
            old_recommendations.delete()
        except ImportError:
            # ContentRecommendation model doesn't exist yet
            deleted_count = 0

        # Clean up similarity scores older than 30 days
        try:
            from content.models import ContentSimilarity
            old_similarity = ContentSimilarity.objects.filter(
                calculated_at__lt=timezone.now() - timedelta(days=30)
            )
            similarity_deleted = old_similarity.count()
            old_similarity.delete()
        except ImportError:
            # ContentSimilarity model doesn't exist yet
            similarity_deleted = 0

        return f"Cleaned up {deleted_count} old recommendations and {similarity_deleted} similarity records"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error cleaning up recommendations: {str(e)}',
            extra_data={'task': 'cleanup_old_recommendations'}
        )
        return f"Error cleaning up recommendations: {str(e)}"


@shared_task
def update_recommendation_performance_metrics():
    """Update metrics to track recommendation system performance"""
    try:
        from content.utils import calculate_recommendation_metrics

        # Calculate click-through rates, engagement rates, etc.
        metrics = calculate_recommendation_metrics()

        # Log performance metrics
        ErrorLog.objects.create(
            level='info',
            message='Recommendation performance metrics updated',
            extra_data={
                'task': 'update_recommendation_performance_metrics',
                'metrics': metrics
            }
        )

        return f"Updated recommendation performance metrics: {metrics}"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating recommendation metrics: {str(e)}',
            extra_data={'task': 'update_recommendation_performance_metrics'}
        )
        return f"Error updating recommendation metrics: {str(e)}"


@shared_task
def cleanup_old_content():
    """
    Clean up old content data to maintain performance.
    Respects the soft deletion system - only removes truly orphaned records.
    """
    try:
        cleanup_stats = {
            'old_post_reactions': 0,
            'old_comment_reactions': 0,
            'old_analysis': 0,
            'orphaned_post_reactions': 0,
            'orphaned_comment_reactions': 0
        }

        # Since we have cascading soft deletion, we should only clean up:
        # 1. Records older than 30 days that are already soft deleted
        # 2. Truly orphaned records where content no longer exists

        # Remove old post reaction records that are soft deleted (30+ days)
        old_soft_deleted_post_reactions = PostReaction.objects.filter(
            is_deleted=True,
            deleted_at__lt=timezone.now() - timedelta(days=30)
        )
        cleanup_stats['old_post_reactions'] = (
            old_soft_deleted_post_reactions.count()
        )
        old_soft_deleted_post_reactions.delete()

        # Remove old comment reaction records that are soft deleted (30+ days)
        old_soft_deleted_comment_reactions = CommentReaction.objects.filter(
            is_deleted=True,
            deleted_at__lt=timezone.now() - timedelta(days=30)
        )
        cleanup_stats['old_comment_reactions'] = (
            old_soft_deleted_comment_reactions.count()
        )
        old_soft_deleted_comment_reactions.delete()

        # Check for orphaned post reactions (where post was hard deleted)
        orphaned_post_reactions_count = 0
        for reaction in PostReaction.objects.filter(is_deleted=False):
            try:
                if reaction.post is None:
                    # Post was hard deleted - clean up the reaction
                    reaction.delete()
                    orphaned_post_reactions_count += 1
            except Exception:
                # Post doesn't exist or is inaccessible
                reaction.delete()
                orphaned_post_reactions_count += 1

        cleanup_stats['orphaned_post_reactions'] = (
            orphaned_post_reactions_count
        )

        # Check for orphaned comment reactions
        orphaned_comment_reactions_count = 0
        for reaction in CommentReaction.objects.filter(is_deleted=False):
            try:
                if reaction.comment is None:
                    # Comment was hard deleted - clean up the reaction
                    reaction.delete()
                    orphaned_comment_reactions_count += 1
            except Exception:
                # Comment doesn't exist or is inaccessible
                reaction.delete()
                orphaned_comment_reactions_count += 1

        cleanup_stats['orphaned_comment_reactions'] = (
            orphaned_comment_reactions_count
        )

        # Remove old content analysis records (keep 6 months, regardless of soft deletion)
        old_analysis = ContentAnalysis.objects.filter(
            analysis_date__lt=timezone.now() - timedelta(days=180)
        )
        cleanup_stats['old_analysis'] = old_analysis.count()
        old_analysis.delete()

        return f"Content cleanup complete: {cleanup_stats}"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error during content cleanup: {str(e)}',
            extra_data={'task': 'cleanup_old_content'}
        )
        return f"Error during content cleanup: {str(e)}"


@shared_task
def send_content_notification_emails():
    """Send notifications for content events with user settings integration."""
    try:
        from notifications.utils import NotificationService

        # Get recent content activity that needs notifications
        recent_post_reactions = PostReaction.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).select_related('user', 'post')

        recent_comment_reactions = CommentReaction.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).select_related('user', 'comment')

        recent_comments = Comment.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=1),
            is_deleted=False
        ).select_related('author', 'post')

        push_notifications_sent = 0
        email_notifications_sent = 0

        # Create notifications for post reactions
        for reaction in recent_post_reactions:
            try:
                if reaction.post and reaction.post.author != reaction.user:
                    content_author = reaction.post.author
                    user_settings = getattr(content_author, 'settings', None)

                    # Skip if user has disabled notifications
                    if (not user_settings or
                            user_settings.notification_frequency == 'never'):
                        continue

                    # Determine sentiment for message
                    emoji = reaction.get_reaction_type_display()
                    title = f"New reaction on your post"
                    message = (
                        f"{reaction.user.username} reacted {emoji} "
                        f"to your post"
                    )

                    # Create push notification if enabled
                    if user_settings.push_notifications:
                        push_notification = (
                            NotificationService.create_notification(
                                recipient=content_author,
                                title=title,
                                message=message,
                                notification_type='reaction',
                                related_object=reaction.post,
                                app_context='content',
                                extra_data={
                                    'reaction_id': str(reaction.id),
                                    'reactor_id': str(reaction.user.id),
                                    'reactor_username': reaction.user.username,
                                    'reaction_type': reaction.reaction_type,
                                    'content_type': 'post'
                                }
                            )
                        )

                        if push_notification:
                            push_notifications_sent += 1

                    # Send email based on frequency preferences
                    should_email = (
                        user_settings.email_notifications and
                        user_settings.notification_frequency in
                        ['real_time', 'hourly']
                    )

                    if should_email:
                        email_sent = (
                            NotificationService.send_email_notification(
                                recipient=content_author,
                                subject=f'{emoji} {title}',
                                template='content/email/reaction_notification.html',
                                context={
                                    'recipient': content_author,
                                    'reactor': reaction.user,
                                    'content': reaction.post,
                                    'reaction_emoji': emoji,
                                    'content_type': 'post'
                                }
                            )
                        )

                        if email_sent:
                            email_notifications_sent += 1

            except Exception as e:
                ErrorLog.objects.create(
                    level='warning',
                    message=f'Error creating reaction notification: {str(e)}',
                    extra_data={
                        'reaction_id': str(reaction.id),
                        'task': 'send_content_notification_emails'
                    }
                )

        # Create notifications for comment reactions
        for reaction in recent_comment_reactions:
            try:
                if (reaction.comment and
                        reaction.comment.author != reaction.user):
                    content_author = reaction.comment.author
                    user_settings = getattr(content_author, 'settings', None)

                    # Skip if user has disabled notifications
                    if (not user_settings or
                            user_settings.notification_frequency == 'never'):
                        continue

                    # Determine sentiment for message
                    emoji = reaction.get_reaction_type_display()
                    title = f"New reaction on your comment"
                    message = (
                        f"{reaction.user.username} reacted {emoji} "
                        f"to your comment"
                    )

                    # Create push notification if enabled
                    if user_settings.push_notifications:
                        push_notification = (
                            NotificationService.create_notification(
                                recipient=content_author,
                                title=title,
                                message=message,
                                notification_type='reaction',
                                related_object=reaction.comment,
                                app_context='content',
                                extra_data={
                                    'reaction_id': str(reaction.id),
                                    'reactor_id': str(reaction.user.id),
                                    'reactor_username': reaction.user.username,
                                    'reaction_type': reaction.reaction_type,
                                    'content_type': 'comment'
                                }
                            )
                        )

                        if push_notification:
                            push_notifications_sent += 1

                    # Send email based on frequency preferences
                    should_email = (
                        user_settings.email_notifications and
                        user_settings.notification_frequency in
                        ['real_time', 'hourly']
                    )

                    if should_email:
                        email_sent = (
                            NotificationService.send_email_notification(
                                recipient=content_author,
                                subject=f'{emoji} {title}',
                                template='content/email/reaction_notification.html',
                                context={
                                    'recipient': content_author,
                                    'reactor': reaction.user,
                                    'content': reaction.comment,
                                    'reaction_emoji': emoji,
                                    'content_type': 'comment'
                                }
                            )
                        )

                        if email_sent:
                            email_notifications_sent += 1

            except Exception as e:
                ErrorLog.objects.create(
                    level='warning',
                    message=f'Error creating reaction notification: {str(e)}',
                    extra_data={
                        'reaction_id': str(reaction.id),
                        'task': 'send_content_notification_emails'
                    }
                )


        # Create notifications for comments
        for comment in recent_comments:
            try:
                if comment.post and comment.post.author != comment.author:
                    post_author = comment.post.author
                    user_settings = getattr(post_author, 'settings', None)

                    # Skip if user has disabled notifications
                    if (not user_settings or
                            user_settings.notification_frequency == 'never'):
                        continue

                    title = "New comment on your post"
                    message = f"{comment.author.username} commented on your post"

                    # Create push notification if enabled
                    if user_settings.push_notifications:
                        push_notification = NotificationService.create_notification(
                            recipient=post_author,
                            title=title,
                            message=message,
                            notification_type='comment',
                            related_object=comment.post,
                            app_context='content',
                            extra_data={
                                'comment_id': str(comment.id),
                                'commenter_id': str(comment.author.id),
                                'commenter_username': comment.author.username,
                                'post_id': str(comment.post.id)
                            }
                        )

                        if push_notification:
                            push_notifications_sent += 1

                    # Send email based on frequency preferences
                    should_email = (
                        user_settings.email_notifications and
                        user_settings.notification_frequency in
                        ['real_time', 'hourly', 'daily']
                    )

                    if should_email:
                        email_sent = NotificationService.send_email_notification(
                            recipient=post_author,
                            subject=f'💬 {title}',
                            template='content/email/comment_notification.html',
                            context={
                                'recipient': post_author,
                                'commenter': comment.author,
                                'comment': comment,
                                'post': comment.post
                            }
                        )

                        if email_sent:
                            email_notifications_sent += 1

            except Exception as e:
                ErrorLog.objects.create(
                    level='warning',
                    message=f'Error creating comment notification: {str(e)}',
                    extra_data={
                        'comment_id': str(comment.id),
                        'task': 'send_content_notification_emails'
                    }
                )

        return (f"Content notifications sent: {push_notifications_sent} push "
                f"notifications and {email_notifications_sent} emails")

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error creating content notifications: {str(e)}',
            extra_data={'task': 'send_content_notification_emails'}
        )
        return f"Error creating content notifications: {str(e)}"


# =============================================================================
# A/B TESTING TASKS FOR CONTENT RECOMMENDATION EXPERIMENTATION
# =============================================================================

@shared_task
def analyze_content_experiment_results(experiment_id):
    """
    Analyze results for a completed content A/B testing experiment.
    """
    from content.models import ContentExperiment, ContentExperimentResult
    from content.utils import get_content_experiment_stats

    try:
        experiment = ContentExperiment.objects.get(id=experiment_id)

        # Get or create result record
        result, created = ContentExperimentResult.objects.get_or_create(
            experiment=experiment
        )

        # Generate comprehensive stats
        stats = get_content_experiment_stats(experiment_id)

        if stats:
            # Update result with stats
            result.control_sample_size = stats['sample_sizes']['control']
            result.test_sample_size = stats['sample_sizes']['test']

            control_metrics = stats['metrics']['control']
            test_metrics = stats['metrics']['test']

            # Update performance metrics
            result.control_avg_response_time = control_metrics.get(
                'avg_response_time'
            )
            result.test_avg_response_time = test_metrics.get(
                'avg_response_time'
            )
            result.control_avg_accuracy = control_metrics.get('avg_accuracy')
            result.test_avg_accuracy = test_metrics.get('avg_accuracy')
            result.control_engagement_rate = control_metrics.get(
                'engagement_rate'
            )
            result.test_engagement_rate = test_metrics.get('engagement_rate')
            result.control_click_through_rate = control_metrics.get(
                'click_through_rate'
            )
            result.test_click_through_rate = test_metrics.get(
                'click_through_rate'
            )

            # Statistical significance
            significance = stats.get('statistical_significance', {})
            result.p_value = significance.get('p_value')

            # Determine winner based on engagement and CTR
            if significance.get('is_significant', False):
                control_score = (
                    (control_metrics.get('engagement_rate', 0) * 0.6) +
                    (control_metrics.get('click_through_rate', 0) * 0.4)
                )
                test_score = (
                    (test_metrics.get('engagement_rate', 0) * 0.6) +
                    (test_metrics.get('click_through_rate', 0) * 0.4)
                )

                if test_score > control_score:
                    result.winner = 'test'
                    if control_score > 0:
                        improvement = ((test_score - control_score) /
                                     control_score) * 100
                        result.improvement_percentage = improvement
                elif control_score > test_score:
                    result.winner = 'control'
                    if test_score > 0:
                        improvement = ((control_score - test_score) /
                                     test_score) * 100
                        result.improvement_percentage = improvement
                else:
                    result.winner = 'inconclusive'
            else:
                result.winner = 'inconclusive'

            # Generate summary
            result.summary = generate_content_experiment_summary(stats, result)
            result.detailed_analysis = stats
            result.save()

            return f"Analyzed content experiment {experiment.name}: {result.winner} wins"
        else:
            return f"Failed to generate stats for experiment {experiment.name}"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error analyzing content experiment {experiment_id}: {str(e)}',
            extra_data={
                'experiment_id': str(experiment_id),
                'task': 'analyze_content_experiment_results'
            }
        )
        return f"Error analyzing content experiment: {str(e)}"


@shared_task
def auto_stop_content_experiments():
    """
    Automatically stop content experiments that have reached their end date.
    """
    from content.models import ContentExperiment

    try:
        # Find active experiments past their end date
        expired_experiments = ContentExperiment.objects.filter(
            status='active',
            end_date__lt=timezone.now()
        )

        stopped_count = 0
        for experiment in expired_experiments:
            experiment.status = 'completed'
            experiment.save()

            # Trigger analysis
            analyze_content_experiment_results.delay(experiment.id)
            stopped_count += 1

        return f"Auto-stopped {stopped_count} expired content experiments"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error auto-stopping content experiments: {str(e)}',
            extra_data={'task': 'auto_stop_content_experiments'}
        )
        return f"Error auto-stopping content experiments: {str(e)}"


@shared_task
def cleanup_content_experiment_metrics():
    """
    Clean up old content experiment metrics to prevent database bloat.
    """
    from content.models import ContentExperimentMetric

    try:
        # Delete metrics older than 90 days
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count = ContentExperimentMetric.objects.filter(
            recorded_at__lt=cutoff_date
        ).count()

        ContentExperimentMetric.objects.filter(
            recorded_at__lt=cutoff_date
        ).delete()

        return f"Cleaned up {deleted_count} old content experiment metrics"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error cleaning up content experiment metrics: {str(e)}',
            extra_data={'task': 'cleanup_content_experiment_metrics'}
        )
        return f"Error cleaning up content experiment metrics: {str(e)}"


def generate_content_experiment_summary(stats, result):
    """
    Generate a human-readable summary of content experiment results.
    """
    try:
        experiment = result.experiment
        control_metrics = stats['metrics']['control']
        test_metrics = stats['metrics']['test']

        summary_parts = [
            f"Content A/B Test: {experiment.control_algorithm} vs {experiment.test_algorithm}",
            f"Sample sizes: Control={result.control_sample_size}, Test={result.test_sample_size}",
        ]

        if result.winner == 'test':
            summary_parts.append(
                f"Winner: {experiment.test_algorithm} "
                f"({result.improvement_percentage:.1f}% improvement)"
            )
        elif result.winner == 'control':
            summary_parts.append(
                f"Winner: {experiment.control_algorithm} "
                f"({result.improvement_percentage:.1f}% better)"
            )
        else:
            summary_parts.append("Result: No significant difference detected")

        # Add key metrics
        control_ctr = control_metrics.get('click_through_rate', 0)
        test_ctr = test_metrics.get('click_through_rate', 0)
        if control_ctr and test_ctr:
            summary_parts.append(
                f"CTR: Control={control_ctr:.3f}, Test={test_ctr:.3f}"
            )

        control_engagement = control_metrics.get('engagement_rate', 0)
        test_engagement = test_metrics.get('engagement_rate', 0)
        if control_engagement and test_engagement:
            summary_parts.append(
                f"Engagement: Control={control_engagement:.3f}, "
                f"Test={test_engagement:.3f}"
            )

        if result.p_value:
            summary_parts.append(f"p-value: {result.p_value:.4f}")

        return ". ".join(summary_parts)

    except Exception as e:
        return f"Error generating summary: {str(e)}"
