"""
Utilities for content management and recommendations.
"""

import re
import html
import unicodedata
import hashlib
import random
import statistics
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q, F
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType


def calculate_post_recommendation_score(user, post):
    """Composite score: engagement * freshness + relevance.
    Shares/reposts combined only for scoring.
    """
    likes = getattr(post, 'likes_count', 0)
    comments = getattr(post, 'comments_count', 0)
    direct_shares = getattr(post, 'shares_count', 0)
    reposts = getattr(post, 'repost_count', 0)
    dislikes = getattr(post, 'dislikes_count', 0)
    base_engagement = (
        likes * 1 +
        comments * 3 +
        (direct_shares + reposts) * 4 -
        dislikes * 2
    )
    created_at = getattr(post, 'created_at', timezone.now())
    seconds_old = (timezone.now() - created_at).total_seconds()
    hours_old = max(seconds_old / 3600.0, 0.0)
    decay = 0.5 ** (hours_old / 72.0)  # ~72h half-life
    relevance = 0.0
    if user and getattr(post, 'author_id', None) == getattr(user, 'id', None):
        relevance -= 0.5
    try:
        from content.models import PostHashtag
        recent_hashtags = PostHashtag.objects.filter(
            post__author=user,
            post__created_at__gte=timezone.now() - timedelta(days=7)
        ).values_list('hashtag__name', flat=True)
        post_hashtags = set(
            PostHashtag.objects.filter(post=post).values_list(
                'hashtag__name', flat=True
            )
        )
        overlap = len(post_hashtags.intersection(set(recent_hashtags)))
        if overlap:
            relevance += min(overlap / 5.0, 1.0)
    except Exception:
        pass
    score = (base_engagement * decay) / 50.0 + relevance
    return max(0.0, round(score, 4))


def get_recommendation_reasons(user, post):
    """Return brief explanations for a recommendation."""
    reasons = []
    try:
        from content.models import PostHashtag
        recent_hashtags = PostHashtag.objects.filter(
            post__author=user,
            post__created_at__gte=timezone.now() - timedelta(days=14)
        ).values_list('hashtag__name', flat=True)
        post_hashtags = PostHashtag.objects.filter(post=post).values_list(
            'hashtag__name', flat=True
        )
        overlap = set(post_hashtags).intersection(set(recent_hashtags))
        if overlap:
            sample = list(overlap)[:3]
            reasons.append(
                "Shares hashtags you engage with: #" + ", #".join(sample)
            )
        if getattr(post, 'likes_count', 0) > 10:
            reasons.append('Many users liked this')
        if (
            getattr(post, 'shares_count', 0) +
            getattr(post, 'repost_count', 0)
        ) > 5:
            reasons.append('Widely shared recently')
        if not reasons:
            reasons.append('Content variety')
    except Exception:
        reasons.append('Recommended content')
    return reasons


def calculate_engagement_score(user, days=30):
    """Weighted user engagement metric for period."""
    from .models import Post, Comment, PostReaction, DirectShare
    since = timezone.now() - timedelta(days=days)
    posts = Post.objects.filter(author=user, created_at__gte=since).count()
    comments = Comment.objects.filter(
        author=user, created_at__gte=since
    ).count()
    # Count positive and negative reactions
    positive_reactions = PostReaction.objects.filter(
        user=user,
        created_at__gte=since,
        reaction_type__in=PostReaction.POSITIVE_REACTIONS
    ).count()
    negative_reactions = PostReaction.objects.filter(
        user=user,
        created_at__gte=since,
        reaction_type__in=PostReaction.NEGATIVE_REACTIONS
    ).count()
    direct_shares = DirectShare.objects.filter(
        sender=user, created_at__gte=since
    ).count()
    reposts = Post.objects.filter(author=user, post_type='repost', created_at__gte=since).count()
    score = (
        posts * 5 + comments * 3 + positive_reactions * 1 +
        (direct_shares + reposts) * 4 - negative_reactions * 1
    )
    normalized = score / max(days * 10.0, 1.0)
    return {
        'raw': score,
        'normalized': round(normalized, 4),
        'period_days': days
    }


def get_trending_hashtags(limit=20):
    """Top hashtags by usage in last 24 hours."""
    from .models import PostHashtag
    since = timezone.now() - timedelta(hours=24)
    qs = (
        PostHashtag.objects.filter(post__created_at__gte=since)
        .values('hashtag__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:limit]
    )
    return [
        {'hashtag': h['hashtag__name'], 'count': h['count']} for h in qs
    ]


def extract_hashtags_from_content(content):
    """Return list of hashtag strings (without #)."""
    if not content:
        return []
    raw = set(re.findall(r'(?i)#([a-z0-9_]{2,50})', content.lower()))
    return sorted(raw)


def process_hashtags_in_post(post):
    """Persist hashtags for a post; returns list of tag names."""
    from .models import Hashtag, PostHashtag
    if not getattr(post, 'content', ''):
        return []
    tags = extract_hashtags_from_content(post.content)
    created = []
    for name in tags:
        hashtag, _ = Hashtag.objects.get_or_create(name=name)
        PostHashtag.objects.get_or_create(post=post, hashtag=hashtag)
        created.append(name)
    return created


def extract_mentions_from_content(content, mentioning_user):
    """Return UserProfile objects mentioned via @username."""
    if not content:
        return []
    import re
    usernames = set(
        re.findall(r'(?i)@([a-z0-9_]{2,30})', content.lower())
    )
    from accounts.models import UserProfile
    mentioned_profiles = list(
        UserProfile.objects.filter(user__username__in=usernames)
    )
    return mentioned_profiles


def process_mentions_in_post(post):
    """Process mentions in a post and create mention records."""
    if not post.content:
        return []
    mentions = extract_mentions_from_content(post.content, post.author)
    from .models import Mention
    stored = []
    for profile in mentions:
        m, _ = Mention.objects.get_or_create(
            post=post,
            mentioned_user=profile,
            mentioning_user=post.author
        )
        stored.append(profile)
    return stored


def process_mentions_in_comment(comment):
    """Process mentions in a comment and create mention records."""
    if not comment.content:
        return []
    mentions = extract_mentions_from_content(comment.content, comment.author)
    from .models import Mention
    stored = []
    for profile in mentions:
        m, _ = Mention.objects.get_or_create(
            comment=comment,
            mentioned_user=profile,
            mentioning_user=comment.author
        )
        stored.append(profile)
    return stored


def create_mention_mappings_from_content(content):
    """
    Create mention mappings (username -> user_profile_id) from content text.
    This is used for feed API repost comments and other text that needs mention mappings.
    """
    if not content:
        return {}

    import re
    from accounts.models import UserProfile

    # Extract usernames from content
    usernames = set(re.findall(r'(?i)@([a-z0-9_]{2,30})', content.lower()))

    # Create mapping
    mentions = {}
    mentioned_profiles = UserProfile.objects.filter(
        user__username__in=usernames
    ).select_related('user')

    for profile in mentioned_profiles:
        mentions[profile.user.username] = str(profile.id)

    return mentions


def calculate_post_popularity_score(post, hours=24):
    """Popularity score (direct shares + reposts combined only for score)."""
    # Engagement fields sourced directly; no need to query within window yet
    recent_likes = getattr(post, 'likes_count', 0)
    recent_comments = getattr(post, 'comments_count', 0)
    recent_direct_shares = getattr(post, 'shares_count', 0)
    recent_reposts = getattr(post, 'repost_count', 0)
    recent_dislikes = getattr(post, 'dislikes_count', 0)
    popularity_score = (
        recent_likes * 1 +
        recent_comments * 3 +
        (recent_direct_shares + recent_reposts) * 5 -
        recent_dislikes * 1
    )
    return popularity_score


def get_popular_posts(limit=20, hours=24):
    """Get popular posts based on recent engagement."""
    from content.models import Post

    cache_key = f'popular_posts_{limit}_{hours}'
    popular_posts = cache.get(cache_key)

    if popular_posts is None:
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)

        # Get posts with recent activity and calculate scores
        posts_with_scores = []
        recent_posts = Post.objects.filter(
            created_at__gte=start_time - timedelta(days=7)
        ).exclude(is_deleted=True)

        for post in recent_posts:
            score = calculate_post_popularity_score(post, hours)
            if score > 0:
                posts_with_scores.append((post, score))

        # Sort by score and get top posts
        posts_with_scores.sort(key=lambda x: x[1], reverse=True)
        popular_posts = [post for post, score in posts_with_scores[:limit]]

        # Cache for 30 minutes
        cache.set(cache_key, popular_posts, 1800)

    return popular_posts


def clean_content(content):
    """Clean and sanitize content text with advanced filtering."""
    if not content:
        return ""
    # Normalize unicode
    content = unicodedata.normalize("NFKC", content)

    # Remove HTML tags
    content = re.sub(r'<[^>]+>', '', content)

    # Escape dangerous characters
    content = html.escape(content)

    # Remove script and iframe tags (even if malformed)
    content = re.sub(
        r'<script.*?>.*?</script>',
        '',
        content,
        flags=re.DOTALL | re.IGNORECASE
    )
    content = re.sub(
        r'<iframe.*?>.*?</iframe>',
        '',
        content,
        flags=re.DOTALL | re.IGNORECASE
    )

    # Remove URLs
    # content = re.sub(r'https?://\S+|www\.\S+', '', content)

    # Remove emojis
    # content = re.sub(r'[\U00010000-\U0010ffff]', '', content)

    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content).strip()

    return content


def get_post_context_info(post):
    """Get context information about a post (community, hashtags, mentions)."""
    from content.models import PostHashtag, Mention
    context = {
        'is_community_post': getattr(post, 'is_community_post', False),
        'community_name': getattr(post, 'context_name', ''),
        'hashtags': [],
        'mentions': [],
    }
    hashtag_associations = (
        PostHashtag.objects.filter(post=post)
        .select_related('hashtag')
    )
    context['hashtags'] = [
        assoc.hashtag.name for assoc in hashtag_associations
    ]
    mentions = (
        Mention.objects.filter(post=post)
        .select_related('mentioned_user__user')
    )
    context['mentions'] = [
        m.mentioned_user.user.username for m in mentions
    ]
    return context


def process_post_content(post):
    """Complete post processing: hashtags and mentions."""
    results = {
        'hashtags': [],
        'mentions': [],
    }

    if post.content:
        # Process hashtags
        results['hashtags'] = process_hashtags_in_post(post)

        # Process mentions
        results['mentions'] = process_mentions_in_post(post)

    return results


def process_comment_content(comment):
    """Complete comment processing: mentions."""
    results = {
        'mentions': [],
    }

    if comment.content:
        # Process mentions
        results['mentions'] = process_mentions_in_comment(comment)

    return results


def generate_recommendation_id(user_id, content_type, object_id):
    """Generate unique recommendation ID."""
    data = f"{user_id}:{content_type}:{object_id}"
    return hashlib.md5(data.encode()).hexdigest()


# Automatic Moderation and Analysis Functions
# TODO: Implement these functions with actual ML models or services
def analyze_content_sentiment(content_text, model_name="default"):
    """Analyze sentiment of content using ML model."""
    # Removed unused ContentAnalysis import (placeholder)

    if not content_text or not content_text.strip():
        return None

    # This is a placeholder for actual ML sentiment analysis
    # You would integrate with services like:
    # - Google Cloud Natural Language API
    # - AWS Comprehend
    # - Azure Text Analytics
    # - OpenAI API
    # - Local models like VADER, TextBlob, or Transformers

    # Placeholder implementation
    sentiments = ['positive', 'negative', 'neutral', 'mixed']
    sentiment = random.choice(sentiments)
    confidence = random.uniform(0.6, 0.95)

    # In real implementation, you would call your ML service here
    # Example with a hypothetical ML service:
    # result = ml_service.analyze_sentiment(content_text)
    # sentiment = result.sentiment
    # confidence = result.confidence

    return {
        'sentiment': sentiment,
        'confidence': confidence,
        'model_name': model_name
    }

# TODO: Implement toxicity analysis with actual ML models or services
def analyze_content_toxicity(content_text, model_name="toxicity-detector-v1"):
    """Analyze content for toxicity, hate speech, spam, etc."""
    # Removed unused ContentAnalysis import (placeholder)

    if not content_text or not content_text.strip():
        return None

    # Placeholder for actual ML toxicity analysis
    # You would integrate with services like:
    # - Perspective API (Google)
    # - Moderator API
    # - Custom trained models
    # - Hugging Face Transformers models

    # Placeholder implementation

    # Simulate ML analysis results
    toxicity_score = random.uniform(0.0, 1.0)
    spam_score = random.uniform(0.0, 0.8)
    hate_speech_score = random.uniform(0.0, 0.7)
    violence_score = random.uniform(0.0, 0.6)
    adult_content_score = random.uniform(0.0, 0.5)

    return {
        'toxicity_score': toxicity_score,
        'spam_score': spam_score,
        'hate_speech_score': hate_speech_score,
        'violence_score': violence_score,
        'adult_content_score': adult_content_score,
        'model_name': model_name
    }

# TODO: Implement language detection with actual ML models or services
def detect_language(content_text):
    """Detect the language of content."""
    if not content_text or not content_text.strip():
        return None

    # Placeholder for language detection
    # You would use libraries like:
    # - langdetect
    # - Google Translate API
    # - Azure Text Analytics
    # - FastText language detection

    # Placeholder implementation
    languages = ['en', 'fr', 'es', 'de', 'it', 'pt']
    detected_language = random.choice(languages)
    confidence = random.uniform(0.7, 0.99)

    return {
        'language': detected_language,
        'confidence': confidence
    }


def create_content_analysis(content_object, analysis_types=None):
    """Create comprehensive analysis for content."""
    from content.models import ContentAnalysis
    from django.contrib.contenttypes.models import ContentType

    if analysis_types is None:
        analysis_types = ['sentiment', 'toxicity', 'language']

    content_text = getattr(content_object, 'content', '')
    if not content_text:
        return []

    content_type = ContentType.objects.get_for_model(content_object)
    created_analyses = []

    for analysis_type in analysis_types:
        # Check if analysis already exists
        existing_analysis = ContentAnalysis.objects.filter(
            content_type=content_type,
            object_id=content_object.id,
            analysis_type=analysis_type
        ).first()

        if existing_analysis:
            continue

        analysis_data = {
            'content_type': content_type,
            'object_id': content_object.id,
            'analysis_type': analysis_type,
        }

        if analysis_type == 'sentiment':
            sentiment_result = analyze_content_sentiment(content_text)
            if sentiment_result:
                analysis_data.update({
                    'sentiment': sentiment_result['sentiment'],
                    'sentiment_confidence': sentiment_result['confidence'],
                    'model_name': sentiment_result['model_name']
                })

        elif analysis_type == 'toxicity':
            toxicity_result = analyze_content_toxicity(content_text)
            if toxicity_result:
                analysis_data.update({
                    'toxicity_score': toxicity_result['toxicity_score'],
                    'spam_score': toxicity_result['spam_score'],
                    'hate_speech_score': toxicity_result['hate_speech_score'],
                    'violence_score': toxicity_result['violence_score'],
                    'adult_content_score': (
                        toxicity_result['adult_content_score']
                    ),
                    'model_name': toxicity_result['model_name']
                })

        elif analysis_type == 'language':
            language_result = detect_language(content_text)
            if language_result:
                analysis_data.update({
                    'detected_language': language_result['language'],
                    'language_confidence': language_result['confidence']
                })

        # Create the analysis record
        analysis = ContentAnalysis.objects.create(**analysis_data)
        created_analyses.append(analysis)

    return created_analyses


def check_moderation_rules(content_object):
    """Check content against all applicable moderation rules."""
    from content.models import ContentModerationRule

    # Get applicable rules
    rules = ContentModerationRule.objects.filter(is_active=True)

    # Filter by content type
    if hasattr(content_object, '__class__'):
        model_name = content_object.__class__.__name__.lower()
        if model_name == 'post':
            rules = rules.filter(applies_to_posts=True)
        elif model_name == 'comment':
            rules = rules.filter(applies_to_comments=True)

    # Filter by community if applicable
    if hasattr(content_object, 'community') and content_object.community:
        rules = rules.filter(
            Q(community=content_object.community) | Q(community=None)
        )

    triggered_actions = []

    for rule in rules:
        action = evaluate_moderation_rule(content_object, rule)
        if action:
            triggered_actions.append(action)

    return triggered_actions


def evaluate_moderation_rule(content_object, rule):
    """Evaluate a specific moderation rule against content."""
    from content.models import AutoModerationAction, ContentAnalysis
    from django.contrib.contenttypes.models import ContentType

    content_text = getattr(content_object, 'content', '')
    if not content_text:
        return None

    rule_triggered = False
    confidence_score = 0.0
    reason = ""

    if rule.rule_type == 'keyword':
        # Check for banned keywords
        keywords = rule.configuration.get('keywords', [])
        for keyword in keywords:
            if keyword.lower() in content_text.lower():
                rule_triggered = True
                confidence_score = 1.0
                reason = f"Contains banned keyword: {keyword}"
                break

    elif rule.rule_type == 'ml_toxicity':
        # Check toxicity analysis
        try:
            analysis = ContentAnalysis.objects.get(
                content_type=ContentType.objects.get_for_model(content_object),
                object_id=content_object.id,
                analysis_type='toxicity'
            )
            threshold = rule.configuration.get('toxicity_threshold', 0.7)
            if (
                analysis.toxicity_score and
                analysis.toxicity_score >= threshold
            ):
                rule_triggered = True
                confidence_score = analysis.toxicity_score
                reason = f"High toxicity score: {analysis.toxicity_score:.2f}"
        except ContentAnalysis.DoesNotExist:
            pass

    elif rule.rule_type == 'ml_spam':
        # Check spam analysis
        try:
            analysis = ContentAnalysis.objects.get(
                content_type=ContentType.objects.get_for_model(content_object),
                object_id=content_object.id,
                analysis_type='toxicity'
            )
            threshold = rule.configuration.get('spam_threshold', 0.8)
            if (
                analysis.spam_score and
                analysis.spam_score >= threshold
            ):
                rule_triggered = True
                confidence_score = analysis.spam_score
                reason = f"High spam score: {analysis.spam_score:.2f}"
        except ContentAnalysis.DoesNotExist:
            pass

    elif rule.rule_type == 'sentiment':
        # Check sentiment analysis
        try:
            analysis = ContentAnalysis.objects.get(
                content_type=ContentType.objects.get_for_model(content_object),
                object_id=content_object.id,
                analysis_type='sentiment'
            )
            blocked_sentiments = rule.configuration.get(
                'blocked_sentiments', []
            )
            if analysis.sentiment in blocked_sentiments:
                rule_triggered = True
                confidence_score = analysis.sentiment_confidence or 0.8
                reason = f"Blocked sentiment: {analysis.sentiment}"
        except ContentAnalysis.DoesNotExist:
            pass

    if rule_triggered:
        # Create auto moderation action
        action = AutoModerationAction.objects.create(
            content_type=ContentType.objects.get_for_model(content_object),
            object_id=content_object.id,
            target_user=getattr(content_object, 'author', None),
            action_type=rule.action,
            reason=reason,
            triggered_by_rule=rule,
            confidence_score=confidence_score,
            severity_level=rule.severity_level
        )
        return action

    return None


def process_content_for_moderation(content_object):
    """Complete moderation processing for new content."""
    from content.models import ModerationQueue

    # Step 1: Create content analysis
    analyses = create_content_analysis(content_object)

    # Step 2: Check moderation rules
    triggered_actions = check_moderation_rules(content_object)

    # Step 3: Handle high-risk content
    for action in triggered_actions:
        if action.severity_level >= 3 or action.confidence_score >= 0.8:
            # Add to moderation queue for human review
            priority = min(action.severity_level, 5)
            ModerationQueue.objects.create(
                content_type=action.content_type,
                object_id=action.object_id,
                priority=priority,
                reason=f"Auto-moderation triggered: {action.reason}",
                auto_moderation_action=action
            )

    return {
        'analyses': analyses,
        'actions': triggered_actions,
        'requires_review': (
            len([a for a in triggered_actions if a.severity_level >= 3]) > 0
        )
    }


def get_content_safety_score(content_object):
    """Get overall safety score for content based on all analyses."""
    from content.models import ContentAnalysis
    from django.contrib.contenttypes.models import ContentType

    content_type = ContentType.objects.get_for_model(content_object)

    analyses = ContentAnalysis.objects.filter(
        content_type=content_type,
        object_id=content_object.id
    )

    if not analyses.exists():
        return 0.5  # Neutral score if no analysis available

    risk_scores = []

    for analysis in analyses:
        if analysis.overall_risk_score > 0:
            risk_scores.append(analysis.overall_risk_score)

    if not risk_scores:
        return 0.1  # Low risk if no concerning scores

    # Safety score is inverse of risk (higher risk = lower safety)
    avg_risk = sum(risk_scores) / len(risk_scores)
    safety_score = 1.0 - avg_risk

    return max(0.0, min(1.0, safety_score))


# Bot Detection Functions

def analyze_user_posting_patterns(user):
    """Analyze user's posting patterns to detect bot-like behavior."""
    from content.models import Post, Comment

    # Get recent posts and comments (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    posts = Post.objects.filter(
        author=user,
        created_at__gte=start_date
    ).order_by('created_at')

    comments = Comment.objects.filter(
        author=user,
        created_at__gte=start_date
    ).order_by('created_at')

    # Combine and sort all activities
    activities = []
    for post in posts:
        activities.append(('post', post.created_at))
    for comment in comments:
        activities.append(('comment', comment.created_at))

    activities.sort(key=lambda x: x[1])

    if len(activities) < 3:
        return {
            'timing_score': 0.0,
            'avg_interval': None,
            'regularity_score': 0.0,
            'rapid_incidents': 0,
        }

    # Calculate intervals between activities
    intervals = []
    for i in range(1, len(activities)):
        interval = (activities[i][1] - activities[i-1][1]).total_seconds()
        intervals.append(interval)

    avg_interval = statistics.mean(intervals)

    # Detect suspiciously regular intervals (bot-like)
    if len(intervals) > 5:
        std_deviation = statistics.stdev(intervals)
        coefficient_of_variation = (
            std_deviation / avg_interval if avg_interval > 0 else 0
        )
        # Low variation = more regular = more bot-like
        regularity_score = max(0.0, 1.0 - coefficient_of_variation)
    else:
        regularity_score = 0.0

    # Detect rapid posting incidents (posts within 10 seconds)
    rapid_incidents = 0
    for interval in intervals:
        if interval < 10:  # Less than 10 seconds
            rapid_incidents += 1

    # Calculate timing score
    timing_score = 0.0

    # High regularity is suspicious
    if regularity_score > 0.8:
        timing_score += 0.4

    # Rapid posting is suspicious
    rapid_ratio = rapid_incidents / len(intervals) if intervals else 0
    timing_score += rapid_ratio * 0.5

    # Very short average intervals are suspicious
    if avg_interval < 60:  # Less than 1 minute average
        timing_score += 0.3

    return {
        'timing_score': min(timing_score, 1.0),
        'avg_interval': avg_interval,
        'regularity_score': regularity_score,
        'rapid_incidents': rapid_incidents,
    }


def analyze_content_patterns(user):
    """Analyze user's content patterns for bot-like behavior."""
    from content.models import Post, Comment
    from difflib import SequenceMatcher

    # Get recent content (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    posts = Post.objects.filter(
        author=user,
        created_at__gte=start_date
    ).values_list('content', flat=True)

    comments = Comment.objects.filter(
        author=user,
        created_at__gte=start_date
    ).values_list('content', flat=True)

    all_content = list(posts) + list(comments)
    all_content = [
        c for c in all_content if c and c.strip()
    ]

    if len(all_content) < 3:
        return {
            'content_score': 0.0,
            'duplicate_ratio': 0.0,
            'link_spam_score': 0.0,
        }

    # Check for duplicate/similar content
    duplicate_count = 0
    link_count = 0
    total_comparisons = 0

    for i, content1 in enumerate(all_content):
        # Count links
        if 'http' in content1.lower() or 'www.' in content1.lower():
            link_count += 1

        # Compare with other content for similarity
        for j, content2 in enumerate(all_content[i+1:], i+1):
            similarity = SequenceMatcher(
                None,
                content1.lower(),
                content2.lower()
            ).ratio()
            if similarity > 0.8:  # 80% similar
                duplicate_count += 1
            total_comparisons += 1

    duplicate_ratio = (
        duplicate_count / total_comparisons if total_comparisons > 0 else 0.0
    )
    link_spam_score = (
        min(link_count / len(all_content), 1.0) if all_content else 0.0
    )

    # Calculate content score
    content_score = 0.0

    # High duplicate content is suspicious
    if duplicate_ratio > 0.3:
        content_score += 0.5

    # Excessive links are suspicious
    if link_spam_score > 0.5:
        content_score += 0.4

    # Very short or very repetitive content
    avg_length = (
        sum(len(content) for content in all_content) / len(all_content)
    )
    if avg_length < 20:  # Very short content
        content_score += 0.2

    return {
        'content_score': min(content_score, 1.0),
        'duplicate_ratio': duplicate_ratio,
        'link_spam_score': link_spam_score,
    }


def analyze_user_behavior(user):
    """Analyze general user behavior patterns."""
    from accounts.models import Follow

    # Get user's social metrics
    following_count = Follow.objects.filter(follower=user).count()
    followers_count = Follow.objects.filter(followed=user).count()

    # Calculate ratios
    follow_ratio = following_count / max(followers_count, 1)

    # Check profile completeness
    profile_score = 0.0
    if hasattr(user, 'user') and user.user:
        if user.user.first_name:
            profile_score += 0.2
        if user.user.last_name:
            profile_score += 0.2
        if user.user.email:
            profile_score += 0.2

    if hasattr(user, 'bio') and user.bio:
        profile_score += 0.2
    if hasattr(user, 'avatar') and user.avatar:
        profile_score += 0.2

    # Calculate behavior score
    behavior_score = 0.0

    # High follow ratio is suspicious (following many, few followers)
    if follow_ratio > 10:
        behavior_score += 0.4
    elif follow_ratio > 5:
        behavior_score += 0.2

    # Incomplete profile is suspicious
    if profile_score < 0.4:
        behavior_score += 0.3

    # Very new account with high activity
    account_age = (timezone.now() - user.user.date_joined).days
    if account_age < 7:  # Less than a week old
        behavior_score += 0.2

    return {
        'behavior_score': min(behavior_score, 1.0),
        'follow_ratio': follow_ratio,
        'profile_completeness': profile_score,
        'account_age_days': account_age,
    }


def update_bot_detection_profile(user):
    """Update or create bot detection profile for user."""
    from content.models import BotDetectionProfile

    # Get or create profile
    profile, created = BotDetectionProfile.objects.get_or_create(
        user=user,
        defaults={
            'overall_bot_score': 0.0,
            'last_analysis': timezone.now(),
        }
    )

    # Analyze different aspects
    timing_analysis = analyze_user_posting_patterns(user)
    content_analysis = analyze_content_patterns(user)
    behavior_analysis = analyze_user_behavior(user)

    # Update profile with new scores
    profile.timing_score = timing_analysis['timing_score']
    profile.content_score = content_analysis['content_score']
    profile.behavior_score = behavior_analysis['behavior_score']

    # Calculate overall bot score (weighted average)
    profile.overall_bot_score = (
        profile.timing_score * 0.4 +
        profile.content_score * 0.3 +
        profile.behavior_score * 0.3
    )

    # Update specific metrics
    profile.avg_posting_interval = timing_analysis['avg_interval']
    profile.posting_regularity_score = timing_analysis['regularity_score']
    profile.rapid_posting_incidents = timing_analysis['rapid_incidents']
    profile.duplicate_content_ratio = content_analysis['duplicate_ratio']
    profile.link_spam_score = content_analysis['link_spam_score']
    profile.follows_to_followers_ratio = behavior_analysis['follow_ratio']
    profile.profile_completeness_score = (
        behavior_analysis['profile_completeness']
    )

    # Update metadata
    profile.last_analysis = timezone.now()
    profile.analysis_count += 1

    # Auto-flag if high bot score
    if profile.overall_bot_score >= 0.7 and not profile.is_verified_human:
        profile.is_flagged_as_bot = True

    # Auto-block if very high bot score
    if profile.overall_bot_score >= 0.9 and not profile.is_verified_human:
        profile.auto_blocked = True

    profile.save()

    return profile


def create_bot_detection_event(
    user,
    event_type,
    severity,
    description,
    confidence_score,
    related_post=None,
    related_comment=None,
    metadata=None,
):
    """Create a bot detection event."""
    from content.models import BotDetectionEvent

    event = BotDetectionEvent.objects.create(
        user=user,
        event_type=event_type,
        severity=severity,
        description=description,
        confidence_score=confidence_score,
        related_post=related_post,
        related_comment=related_comment,
        metadata=metadata or {}
    )

    return event


def check_rapid_posting(user, content_object):
    """Check if user is posting too rapidly."""
    from content.models import Post, Comment

    # Check last 5 minutes of activity
    recent_time = timezone.now() - timedelta(minutes=5)

    recent_posts = Post.objects.filter(
        author=user,
        created_at__gte=recent_time
    ).count()

    recent_comments = Comment.objects.filter(
        author=user,
        created_at__gte=recent_time
    ).count()

    total_recent = recent_posts + recent_comments

    # Threshold: more than 10 posts/comments in 5 minutes
    if total_recent > 10:
        create_bot_detection_event(
            user=user,
            event_type='rapid_posting',
            severity=3,
            description=(
                f"Posted {total_recent} times in 5 minutes"
            ),
            confidence_score=0.9,
            related_post=(
                content_object if isinstance(content_object, Post) else None
            ),
            related_comment=(
                content_object if isinstance(content_object, Comment) else None
            ),
            metadata={'recent_count': total_recent, 'time_window': 5}
        )
        return True

    return False


def check_duplicate_content(user, content_object):
    """Check if user is posting duplicate content.

    Excludes legitimate reposts from duplicate detection since reposts
    are expected to be similar to their parent posts.
    """
    from content.models import Post, Comment
    from difflib import SequenceMatcher

    content_text = getattr(content_object, 'content', '')
    if not content_text or len(content_text.strip()) < 10:
        return False

    # Skip duplicate check for legitimate reposts
    if isinstance(content_object, Post) and content_object.is_repost:
        return False

    # Check last 24 hours for similar content
    recent_time = timezone.now() - timedelta(hours=24)

    if isinstance(content_object, Post):
        # Exclude legitimate reposts from comparison since they're
        # supposed to be similar to their parent posts
        recent_content = Post.objects.filter(
            author=user,
            created_at__gte=recent_time,
            parent_post__isnull=True  # Only compare with original posts
        ).exclude(id=content_object.id).values_list('content', flat=True)
    else:
        recent_content = Comment.objects.filter(
            author=user,
            created_at__gte=recent_time
        ).exclude(id=content_object.id).values_list('content', flat=True)

    # Check for high similarity
    for existing_content in recent_content:
        if existing_content:
            similarity = SequenceMatcher(
                None,
                content_text.lower().strip(),
                existing_content.lower().strip()
            ).ratio()

            if similarity > 0.9:  # 90% similar
                create_bot_detection_event(
                    user=user,
                    event_type='duplicate_content',
                    severity=2,
                    description=(
                        f"Posted content {similarity:.1%} similar to recent post"
                    ),
                    confidence_score=similarity,
                    related_post=(
                        content_object if isinstance(content_object, Post)
                        else None
                    ),
                    related_comment=(
                        content_object if isinstance(content_object, Comment)
                        else None
                    ),
                    metadata={'similarity_score': similarity}
                )
                return True

    return False


def is_user_blocked_as_bot(user):
    """Check if user is blocked as a bot."""
    from content.models import BotDetectionProfile

    try:
        profile = BotDetectionProfile.objects.get(user=user)
        return profile.auto_blocked
    except BotDetectionProfile.DoesNotExist:
        return False


def process_content_for_bot_detection(content_object):
    """Process content for bot detection."""
    user = getattr(content_object, 'author', None)
    if not user:
        return {'bot_detected': False, 'events': []}

    events = []

    # Check if user is already blocked
    if is_user_blocked_as_bot(user):
        return {'bot_detected': True, 'events': [], 'blocked': True}

    # Check rapid posting
    if check_rapid_posting(user, content_object):
        events.append('rapid_posting')

    # Check duplicate content
    if check_duplicate_content(user, content_object):
        events.append('duplicate_content')

    # Update bot detection profile every 10th post/comment
    if random.randint(1, 10) == 1:  # 10% chance to update profile
        update_bot_detection_profile(user)

    return {
        'bot_detected': len(events) > 0,
        'events': events,
        'blocked': False
    }


# =============================================================================
# CONTENT RECOMMENDATION SYSTEM FUNCTIONS
# =============================================================================

def generate_user_recommendations(user, limit=20):
    """Generate personalized content recommendations for a user."""
    # Removed unused local imports (Post, ContentRecommendation, ContentType)

    # Skip bot users
    if is_user_blocked_as_bot(user):
        return []

    # Get content-based recommendations
    content_based_recs = get_content_based_recommendations(user, limit//2)

    # Get collaborative filtering recommendations
    collaborative_recs = get_collaborative_filtering_recommendations(
        user, limit // 2
    )

    # Get trending content recommendations
    trending_recs = get_trending_content_recommendations(
        user, limit//4
    )

    # Combine and score all recommendations
    all_recommendations = []

    # Add content-based recommendations with high weight
    for post, score in content_based_recs:
        all_recommendations.append({
            'post': post,
            'score': score * 0.4,
            'reason': 'Based on your interests',
            'type': 'content_based'
        })

    # Add collaborative recommendations with medium weight
    for post, score in collaborative_recs:
        all_recommendations.append({
            'post': post,
            'score': score * 0.3,
            'reason': 'Users like what you also liked',
            'type': 'collaborative'
        })

    # Add trending recommendations with lower weight
    for post, score in trending_recs:
        all_recommendations.append({
            'post': post,
            'score': score * 0.2,
            'reason': 'Trending now',
            'type': 'trending'
        })

    # Remove duplicates and posts user has already seen
    seen_post_ids = set()
    filtered_recommendations = []

    for rec in all_recommendations:
        post_id = rec['post'].id
        if (
            post_id not in seen_post_ids and
            not has_user_seen_post(user, rec['post'])
        ):
            seen_post_ids.add(post_id)
            filtered_recommendations.append(rec)

    # Sort by combined score
    filtered_recommendations.sort(key=lambda x: x['score'], reverse=True)

    # Store recommendations in database
    final_recommendations = []
    for i, rec in enumerate(filtered_recommendations[:limit]):
        recommendation = store_recommendation(
            user=user,
            content_object=rec['post'],
            score=rec['score'],
            reason=rec['reason'],
            recommendation_type=rec['type'],
            rank=i + 1
        )
        final_recommendations.append(recommendation)

    return final_recommendations


def get_user_content_interactions(user, days=30):
    """Get user's content interaction history."""
    from content.models import PostReaction, Comment, DirectShare, Post
    from django.contrib.contenttypes.models import ContentType

    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    interactions = {
        'liked_posts': [],
        'commented_posts': [],
        'shared_posts': [],
        'viewed_posts': [],
        'disliked_posts': []
    }

    # Get liked posts (positive reactions)
    liked_posts = PostReaction.objects.filter(
        user=user,
        reaction_type__in=PostReaction.POSITIVE_REACTIONS,
        created_at__gte=start_date
    ).values_list('post_id', flat=True)
    interactions['liked_posts'] = list(liked_posts)

    # Get commented posts
    commented_posts = Comment.objects.filter(
        author=user,
        is_deleted=False,
        created_at__gte=start_date
    ).values_list('post_id', flat=True)
    interactions['commented_posts'] = list(commented_posts)

    # Get shared posts (track direct shares and reposts separately for callers)
    direct_shared_posts = DirectShare.objects.filter(
        sender=user,
        created_at__gte=start_date
    ).values_list('post_id', flat=True)
    reposted_posts = Post.objects.filter(
        author=user,
        post_type='repost',
        created_at__gte=start_date
    ).values_list('parent_post_id', flat=True)
    shared_posts = set(list(direct_shared_posts) + list(reposted_posts))
    interactions['shared_posts'] = list(shared_posts)
    interactions['direct_shared_posts'] = list(direct_shared_posts)
    interactions['reposted_posts'] = list(reposted_posts)

    # Get disliked posts (negative reactions)
    disliked_posts = PostReaction.objects.filter(
        user=user,
        reaction_type__in=PostReaction.NEGATIVE_REACTIONS,
        created_at__gte=start_date
    ).values_list('post_id', flat=True)
    interactions['disliked_posts'] = list(disliked_posts)

    # Get all interacted post IDs
    all_interacted = set(
        interactions['liked_posts'] +
        interactions['commented_posts'] +
        interactions['shared_posts'] +
        interactions['disliked_posts']
    )
    interactions['all_interacted'] = list(all_interacted)

    return interactions


def get_content_based_recommendations(user, limit=10):
    """Get recommendations based on content similarity to user's
    preferences."""
    from content.models import Post, PostHashtag  # Removed unused Hashtag

    # Get user's preferred hashtags based on interaction history
    user_interactions = get_user_content_interactions(user)
    interacted_post_ids = user_interactions['all_interacted']

    if not interacted_post_ids:
        # New user - return popular posts
        return get_popular_posts_with_scores(limit)

    # Get hashtags from posts user interacted with
    preferred_hashtags = PostHashtag.objects.filter(
        post_id__in=interacted_post_ids
    ).values_list('hashtag__name', flat=True).distinct()

    # Find posts with similar hashtags, exclude disliked posts
    recommended_posts = Post.objects.filter(
        content_hashtags__hashtag__name__in=preferred_hashtags,
        is_deleted=False,
        is_hidden=False,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).exclude(id__in=interacted_post_ids).exclude(
        author=user
    ).exclude(
        id__in=user_interactions['disliked_posts']
    ).annotate(
        hashtag_matches=Count(
            'content_hashtags__hashtag__name', distinct=True
        ),
        combined_shares=F('shares_count') + F('repost_count')
    ).order_by(
        '-hashtag_matches', '-likes_count', '-comments_count',
        '-combined_shares', 'dislikes_count'
    )[:limit]

    # Calculate scores
    recommendations = []
    for post in recommended_posts:
        hashtag_score = post.hashtag_matches / max(len(preferred_hashtags), 1)
        # Use post fields for engagement
        engagement_score = min((
            getattr(post, 'likes_count', 0) +
            getattr(post, 'comments_count', 0) * 2 +
            (getattr(post, 'shares_count', 0) +
             getattr(post, 'repost_count', 0)) * 3 -
            getattr(post, 'dislikes_count', 0) * 2
        ) / 100.0, 1.0)
        final_score = (hashtag_score * 0.6) + (engagement_score * 0.4)
        recommendations.append((post, final_score))

    return recommendations


def get_collaborative_filtering_recommendations(user, limit=10):
    """Get recommendations using collaborative filtering."""
    from content.models import PostReaction, Post
    from django.db.models import Count

    # Get users with similar interests (users who liked similar posts)
    user_interactions = get_user_content_interactions(user)
    user_liked_posts = user_interactions['liked_posts']

    if not user_liked_posts:
        return []

    # Find users who also liked the same posts (positive reactions)
    similar_users = PostReaction.objects.filter(
        post_id__in=user_liked_posts,
        reaction_type__in=PostReaction.POSITIVE_REACTIONS
    ).exclude(
        user=user
    ).values('user').annotate(
        common_likes=Count('post_id')
    ).filter(
        common_likes__gte=2  # At least 2 posts in common
    ).order_by('-common_likes')[:20]  # Top 20 similar users

    similar_user_ids = [u['user'] for u in similar_users]

    # Get posts liked by similar users that current user hasn't seen
    liked_post_ids = PostReaction.objects.filter(
        user__in=similar_user_ids,
        reaction_type__in=PostReaction.POSITIVE_REACTIONS
    ).values_list('post_id', flat=True)

    # Exclude posts disliked by the user
    user_interactions = get_user_content_interactions(user)
    recommended_posts = Post.objects.filter(
        id__in=liked_post_ids,
        is_deleted=False,
        is_hidden=False,
        created_at__gte=timezone.now() - timedelta(days=60)
    ).exclude(id__in=user_liked_posts).exclude(
        author=user
    ).exclude(
        id__in=user_interactions['disliked_posts']
    ).annotate(
        combined_shares=F('shares_count') + F('repost_count')
    ).order_by(
        '-likes_count', '-comments_count', '-combined_shares', 'dislikes_count'
    )[:limit]

    # Calculate collaborative scores
    recommendations = []

    for post in recommended_posts:
        # Use post fields for engagement
        engagement_score = min((
            getattr(post, 'likes_count', 0) +
            getattr(post, 'comments_count', 0) * 2 +
            (getattr(post, 'shares_count', 0) +
             getattr(post, 'repost_count', 0)) * 3 -
            getattr(post, 'dislikes_count', 0) * 2
        ) / 50.0, 1.0)
        final_score = engagement_score
        recommendations.append((post, final_score))

    return recommendations


def get_trending_content_recommendations(user, limit=5):
    """Get trending content recommendations."""
    from content.models import Post

    # Get posts trending in last 24 hours
    trending_posts = Post.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=24),
        is_deleted=False,
        is_hidden=False
    ).exclude(
        author=user
    ).exclude(
        id__in=get_user_content_interactions(user)['disliked_posts']
    )[:limit]

    # Calculate trending scores manually to avoid annotation conflict
    recommendations = []
    for post in trending_posts:
        score = (
            post.likes_count * 1 +
            post.comments_count * 3 +
            (post.shares_count + post.repost_count) * 5 -
            post.dislikes_count * 2
        )
        recommendations.append((post, score))

    # Sort by score descending and filter out non-positive scores
    recommendations = [r for r in recommendations if r[1] > 0]
    recommendations.sort(key=lambda x: x[1], reverse=True)
    recommendations = recommendations[:limit]

    # Normalize scores
    max_trend_score = max([score for _, score in recommendations], default=1)
    normalized = []
    for post, score in recommendations:
        normalized.append(
            (
                post,
                score / max_trend_score if max_trend_score else 0
            )
        )
    return normalized


def get_popular_posts_with_scores(limit=10):
    """Get popular posts with calculated scores."""
    popular_posts = get_popular_posts(limit)

    recommendations = []
    for i, post in enumerate(popular_posts):
        # Score based on position in popular list
        score = 1.0 - (i / limit)
        recommendations.append((post, score))

    return recommendations


def has_user_seen_post(user, post):
    """Check if user has already seen/interacted with a post."""
    from content.models import (
        PostReaction, Comment, DirectShare, Post, ContentRecommendation
    )
    from django.contrib.contenttypes.models import ContentType

    post_ct = ContentType.objects.get_for_model(post)
    # Any reaction (positive or negative)
    if PostReaction.objects.filter(user=user, post=post).exists():
        return True
    # Comment
    if Comment.objects.filter(author=user, post=post).exists():
        return True
    # Direct share (sender)
    if DirectShare.objects.filter(sender=user, post=post).exists():
        return True
    # Repost
    if Post.objects.filter(author=user, parent_post=post, post_type='repost').exists():
        return True
    # Recent recommendation
    return ContentRecommendation.objects.filter(
        user=user,
        content_type=post_ct,
        object_id=post.id,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).exists()


def get_user_interaction_frequency(user, days=7):
    """Return per-type interaction counts and frequencies."""
    from .models import (
        Post, Comment, PostReaction, DirectShare
    )
    since = timezone.now() - timedelta(days=days)
    post_count = Post.objects.filter(
        author=user, created_at__gte=since
    ).count()
    comment_count = Comment.objects.filter(
        author=user, created_at__gte=since
    ).count()
    # Count positive reactions (likes)
    positive_reaction_count = PostReaction.objects.filter(
        user=user,
        created_at__gte=since,
        reaction_type__in=PostReaction.POSITIVE_REACTIONS
    ).count()
    # Count negative reactions (dislikes)
    negative_reaction_count = PostReaction.objects.filter(
        user=user,
        created_at__gte=since,
        reaction_type__in=PostReaction.NEGATIVE_REACTIONS
    ).count()
    direct_share_count = DirectShare.objects.filter(
        sender=user, created_at__gte=since
    ).count()
    repost_count = Post.objects.filter(
        author=user, post_type='repost', created_at__gte=since
    ).count()
    total = (
        post_count + comment_count + positive_reaction_count +
        negative_reaction_count + direct_share_count + repost_count
    )
    days = max(days, 1)
    return {
        'posts': post_count,
        'comments': comment_count,
        'likes': positive_reaction_count,  # For compatibility
        'dislikes': negative_reaction_count,  # For compatibility
        'direct_shares': direct_share_count,
        'reposts': repost_count,
        'combined_shares_for_scoring': (
            direct_share_count + repost_count
        ),
        'total': total,
        'frequency_per_day': total / days,
        'per_day_breakdown': {
            'posts': post_count / days,
            'comments': comment_count / days,
            'likes': positive_reaction_count / days,
            'dislikes': negative_reaction_count / days,
            'direct_shares': direct_share_count / days,
            'reposts': repost_count / days
        }
    }


def generate_collaborative_recommendations(user, limit=15):
    """Generate recommendations using advanced collaborative filtering."""
    from content.models import PostReaction, Post

    # Get user's liked posts (positive reactions)
    user_liked_posts = PostReaction.objects.filter(
        user=user,
        reaction_type__in=PostReaction.POSITIVE_REACTIONS
    ).values_list('post_id', flat=True)

    if len(user_liked_posts) < 3:
        # Not enough data for collaborative filtering
        return []

    # Find users with similar tastes using Jaccard similarity
    similar_users_data = []

    # Get all users who liked at least one post that current user liked
    potential_similar_users = PostReaction.objects.filter(
        post_id__in=user_liked_posts,
        reaction_type__in=PostReaction.POSITIVE_REACTIONS
    ).exclude(user=user).values_list('user', flat=True).distinct()

    user_liked_set = set(user_liked_posts)

    for similar_user_id in potential_similar_users:
        similar_user_likes = set(
            PostReaction.objects.filter(
                user_id=similar_user_id,
                reaction_type__in=PostReaction.POSITIVE_REACTIONS
            ).values_list('post_id', flat=True)
        )
        intersection = user_liked_set.intersection(similar_user_likes)
        union = user_liked_set.union(similar_user_likes)
        if union:
            jaccard = len(intersection) / len(union)
            if jaccard > 0.1 and len(intersection) >= 2:
                similar_users_data.append({
                    'user_id': similar_user_id,
                    'similarity': jaccard,
                    'common_likes': len(intersection),
                    'liked_posts': similar_user_likes
                })
    similar_users_data.sort(
        key=lambda x: x['similarity'], reverse=True
    )
    top_similar_users = similar_users_data[:20]
    # Get user's disliked posts (negative reactions)
    user_disliked_posts = set(
        PostReaction.objects.filter(
            user=user,
            reaction_type__in=PostReaction.NEGATIVE_REACTIONS,
            is_deleted=False
        ).values_list('post_id', flat=True)
    )
    recommendation_candidates = {}
    for similar_user in top_similar_users:
        new_posts = (
            similar_user['liked_posts'] - user_liked_set - user_disliked_posts
        )
        for pid in new_posts:
            bucket = recommendation_candidates.setdefault(
                pid,
                {
                    'score': 0.0,
                    'similar_users': 0,
                    'total_similarity': 0.0
                }
            )
            bucket['score'] += similar_user['similarity']
            bucket['similar_users'] += 1
            bucket['total_similarity'] += similar_user['similarity']
    final_recommendations = []
    for post_id, data in recommendation_candidates.items():
        if data['similar_users'] >= 2:
            try:
                post = Post.objects.get(
                    id=post_id,
                    is_deleted=False,
                    is_hidden=False,
                    created_at__gte=timezone.now() - timedelta(days=90)
                )
            except Post.DoesNotExist:
                continue
            dislikes = getattr(post, 'dislikes_count', 0)
            likes = getattr(post, 'likes_count', 0)
            penalty = min(dislikes / max(likes + 1, 1), 1.0)
            avg_sim = data['total_similarity'] / data['similar_users']
            crowd = min(data['similar_users'] / 5.0, 1.0)
            final_score = (
                avg_sim * 0.7 + crowd * 0.3 - penalty * 0.5
            )
            final_recommendations.append((post, final_score))
    final_recommendations.sort(key=lambda x: x[1], reverse=True)
    return final_recommendations[:limit]


def calculate_recommendation_metrics():
    """Calculate metrics to track recommendation system performance."""
    from content.models import ContentRecommendation
    from django.db.models import Avg

    # Get recommendations from last 7 days
    recent_recommendations = ContentRecommendation.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    )

    # Calculate click-through rate
    total_recommendations = recent_recommendations.count()
    clicked = recent_recommendations.filter(is_clicked=True).count()
    viewed = recent_recommendations.filter(is_viewed=True).count()
    click_through_rate = (
        clicked / total_recommendations if total_recommendations else 0
    )
    view_rate = (
        viewed / total_recommendations if total_recommendations else 0
    )
    avg_score = (
        recent_recommendations.aggregate(avg=Avg('score'))['avg'] or 0
    )
    type_distribution = {
        row['recommendation_type']: row['count']
        for row in recent_recommendations.values(
            'recommendation_type'
        ).annotate(count=Count('id'))
    }
    users_with_recs = recent_recommendations.values('user').distinct().count()
    return {
        'total_recommendations': total_recommendations,
        'click_through_rate': click_through_rate,
        'view_rate': view_rate,
        'average_score': avg_score,
        'users_served': users_with_recs,
        'type_distribution': type_distribution,
        'period': '7_days',
        'calculated_at': timezone.now().isoformat()
    }


def mark_recommendation_viewed(user, content_object):
    """Mark a recommendation as viewed when user sees the content."""
    from content.models import ContentRecommendation  # local import
    from django.contrib.contenttypes.models import ContentType

    content_type = ContentType.objects.get_for_model(content_object)

    ContentRecommendation.objects.filter(
        user=user,
        content_type=content_type,
        object_id=content_object.id,
        is_viewed=False
    ).update(is_viewed=True, viewed_at=timezone.now())


def mark_recommendation_clicked(user, content_object):
    """Mark recommendation as clicked when user engages."""
    from content.models import ContentRecommendation  # local import
    from django.contrib.contenttypes.models import ContentType

    content_type = ContentType.objects.get_for_model(content_object)

    ContentRecommendation.objects.filter(
        user=user,
        content_type=content_type,
        object_id=content_object.id,
        is_clicked=False
    ).update(is_clicked=True, clicked_at=timezone.now())


def get_user_recommendations(user, limit=20, recommendation_types=None):
    """Get stored recommendations for a user."""
    from content.models import ContentRecommendation, Post
    from django.contrib.contenttypes.models import ContentType

    recommendations_query = ContentRecommendation.objects.filter(
        user=user,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).select_related('content_type')

    if recommendation_types:
        recommendations_query = recommendations_query.filter(
            recommendation_type__in=recommendation_types
        )

    recommendations = recommendations_query.order_by(
        '-score', '-created_at'
    )[:limit]

    # Convert to post objects with metadata
    results = []
    for rec in recommendations:
        try:
            if rec.content_type.model == 'post':
                post = Post.objects.get(id=rec.object_id)
                results.append({
                    'post': post,
                    'score': rec.score,
                    'reason': rec.reason,
                    'type': rec.recommendation_type,
                    'rank': rec.rank,
                    'created_at': rec.created_at,
                    'is_viewed': rec.is_viewed,
                    'is_clicked': rec.is_clicked
                })
        except Post.DoesNotExist:
            # Clean up broken recommendation
            rec.delete()
            continue

    return results


def refresh_user_recommendations(user):
    """Refresh recommendations for a user by generating new ones."""
    from content.models import ContentRecommendation

    # Delete old recommendations (older than 7 days)
    ContentRecommendation.objects.filter(
        user=user,
        created_at__lt=timezone.now() - timedelta(days=7)
    ).delete()

    # Generate new recommendations
    new_recommendations = generate_user_recommendations(user, limit=30)

    return new_recommendations


def get_like_status(user_profile, post):
    """Get like status for a user and post (positive reactions)."""
    from content.models import PostReaction

    return PostReaction.objects.filter(
        user=user_profile,
        post=post,
        reaction_type__in=PostReaction.POSITIVE_REACTIONS
    ).exists()


def create_like(user_profile, post):
    """Create a like (default positive reaction) for a user and post."""
    from content.models import PostReaction

    reaction, created = PostReaction.objects.get_or_create(
        user=user_profile,
        post=post,
        defaults={'reaction_type': 'like'}
    )

    if created:
        # Update the post likes count
        post.likes_count += 1
        post.save(update_fields=['likes_count'])

    return reaction, created


def remove_like(user_profile, post):
    """Remove a like (any positive reaction) for a user and post."""
    from content.models import PostReaction

    try:
        reaction = PostReaction.objects.get(
            user=user_profile,
            post=post,
            reaction_type__in=PostReaction.POSITIVE_REACTIONS
        )
        reaction.delete()

        # Update the post likes count
        if post.likes_count > 0:
            post.likes_count -= 1
            post.save(update_fields=['likes_count'])

        return True
    except PostReaction.DoesNotExist:
        return False


# TODO: Implement actual ML model calls for content analysis
def analyze_content_with_ml(content_text):
    """Analyze content using ML models for toxicity, spam, sentiment."""
    # Mock ML analysis (production would call real ML models)
    analysis_result = {
        'toxicity_score': 0.1,
        'spam_score': 0.05,
        'sentiment_score': 0.7,
        'sentiment_label': 'positive',
        'is_toxic': False,
        'is_spam': False,
        'confidence': 0.85,
        'flags': [],
        'analysis_timestamp': timezone.now().isoformat()
    }

    # Simple keyword-based analysis for testing
    toxic_keywords = ['hate', 'kill', 'die', 'stupid', 'idiot']
    spam_keywords = ['buy now', 'click here', 'free money', 'winner']

    content_lower = content_text.lower()

    for keyword in toxic_keywords:
        if keyword in content_lower:
            analysis_result['toxicity_score'] = min(
                analysis_result['toxicity_score'] + 0.3, 1.0
            )
            analysis_result['flags'].append(
                f"Contains toxic keyword: {keyword}"
            )
    for keyword in spam_keywords:
        if keyword in content_lower:
            analysis_result['spam_score'] = min(
                analysis_result['spam_score'] + 0.4, 1.0
            )
            analysis_result['flags'].append(
                f"Contains spam keyword: {keyword}"
            )

    # Update boolean flags
    analysis_result['is_toxic'] = analysis_result['toxicity_score'] > 0.5
    analysis_result['is_spam'] = analysis_result['spam_score'] > 0.5

    # Adjust sentiment for negative content
    if analysis_result['is_toxic']:
        analysis_result['sentiment_score'] = 0.2
        analysis_result['sentiment_label'] = 'negative'

    return analysis_result


# =============================================================================
# A/B TESTING UTILITIES FOR CONTENT RECOMMENDATION EXPERIMENTATION
# =============================================================================

def assign_user_to_content_experiment(user_id, experiment_id):
    """
    Assign a user to a content A/B testing experiment.
    Returns the group assignment ('control' or 'test').
    """
    from content.models import ContentExperiment, UserContentExperimentAssignment

    try:
        experiment = ContentExperiment.objects.get(
            id=experiment_id,
            status__in=['active', 'running']  # Accept both active and running
        )

        # Check if user is already assigned
        existing_assignment = UserContentExperimentAssignment.objects.filter(
            user_id=user_id,
            experiment=experiment
        ).first()

        if existing_assignment:
            return existing_assignment.group

        # Use deterministic assignment based on user ID for consistency
        hash_input = f"{user_id}_{experiment_id}_{experiment.created_at}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()
        hash_int = int(hash_value[:8], 16)

        # Assign based on traffic split
        is_test = (hash_int % 100) / 100 < experiment.traffic_split
        group = 'test' if is_test else 'control'

        # Create assignment
        UserContentExperimentAssignment.objects.create(
            user_id=user_id,
            experiment=experiment,
            group=group
        )

        return group

    except ContentExperiment.DoesNotExist:
        return 'control'  # Default to control if experiment not found
    except Exception as e:
        print(f"Error in assign_user_to_content_experiment: {e}")
        return 'control'


def get_content_algorithm_for_user(user_id, default_algorithm='hybrid'):
    """
    Get the appropriate content recommendation algorithm for a user based on A/B testing.
    Returns the algorithm name to use.
    """
    from content.models import (
        ContentExperiment,
        UserContentExperimentAssignment
    )

    try:
        # Get active experiments
        active_experiments = ContentExperiment.objects.filter(
            status='active'
        ).filter(
            Q(start_date__lte=timezone.now()) | Q(start_date__isnull=True)
        ).filter(
            Q(end_date__gte=timezone.now()) | Q(end_date__isnull=True)
        ).order_by('-created_at')

        for experiment in active_experiments:
            # Check if user is assigned to this experiment
            assignment = UserContentExperimentAssignment.objects.filter(
                user_id=user_id,
                experiment=experiment
            ).first()

            if assignment:
                if assignment.group == 'control':
                    return experiment.control_algorithm
                else:
                    return experiment.test_algorithm
            else:
                # Auto-assign user to experiment
                group = assign_user_to_content_experiment(
                    user_id, experiment.id
                )
                if group == 'control':
                    return experiment.control_algorithm
                else:
                    return experiment.test_algorithm

        # No active experiments, return default
        return default_algorithm

    except Exception as e:
        print(f"Error in get_content_algorithm_for_user: {e}")
        return default_algorithm


def record_content_experiment_metric(
    user_id,
    metric_type,
    value,
    algorithm_used=None,
    content_object=None,
    metadata=None,
):
    """
    Record a metric for content A/B testing experiments.
    """
    from content.models import (
        UserContentExperimentAssignment,
        ContentExperimentMetric
    )
    from django.contrib.contenttypes.models import ContentType

    if metadata is None:
        metadata = {}

    try:
        # Find active experiments for this user
        assignments = UserContentExperimentAssignment.objects.filter(
            user_id=user_id,
            experiment__status__in=['active', 'running']  # Both statuses
        ).select_related('experiment')

        for assignment in assignments:
            # Determine algorithm used
            if algorithm_used is None:
                if assignment.group == 'control':
                    algorithm_used = assignment.experiment.control_algorithm
                else:
                    algorithm_used = assignment.experiment.test_algorithm

            # Prepare content object fields
            content_type = None
            object_id = None
            if content_object:
                content_type = ContentType.objects.get_for_model(
                    content_object
                )
                object_id = content_object.id

            # Record metric
            ContentExperimentMetric.objects.create(
                experiment=assignment.experiment,
                user_id=user_id,
                metric_type=metric_type,
                value=value,
                algorithm_used=algorithm_used,
                content_type=content_type,
                object_id=object_id,
                metadata=metadata
            )

    except Exception as e:
        print(f"Error recording content experiment metric: {e}")


def get_content_experiment_stats(experiment_id):
    """
    Get statistical summary for a content A/B testing experiment.
    """
    from content.models import (
        ContentExperiment,
        UserContentExperimentAssignment,
        ContentExperimentMetric
    )
    from django.db.models import Avg, Count
    import math

    try:
        experiment = ContentExperiment.objects.get(id=experiment_id)

        # Get assignment counts
        control_count = UserContentExperimentAssignment.objects.filter(
            experiment=experiment,
            group='control'
        ).count()

        test_count = UserContentExperimentAssignment.objects.filter(
            experiment=experiment,
            group='test'
        ).count()

        # Get metrics by group for control group
        control_metrics = ContentExperimentMetric.objects.filter(
            experiment=experiment,
            user__content_experiment_assignments__group='control',
            user__content_experiment_assignments__experiment=experiment
        ).aggregate(
            avg_response_time=Avg(
                'value',
                filter=Q(metric_type='algorithm_response_time')
            ),
            avg_accuracy=Avg(
                'value',
                filter=Q(metric_type='recommendation_accuracy')
            ),
            avg_ctr=Avg(
                'value',
                filter=Q(metric_type='click_through_rate')
            ),
            total_clicks=Count(
                'id', filter=Q(metric_type='recommendation_click')
            ),
            total_views=Count(
                'id', filter=Q(metric_type='recommendation_view')
            ),
            total_engagement=Count(
                'id', filter=Q(metric_type='content_engagement')
            )
        )

        # Get metrics by group for test group
        test_metrics = ContentExperimentMetric.objects.filter(
            experiment=experiment,
            user__content_experiment_assignments__group='test',
            user__content_experiment_assignments__experiment=experiment
        ).aggregate(
            avg_response_time=Avg(
                'value',
                filter=Q(metric_type='algorithm_response_time')
            ),
            avg_accuracy=Avg(
                'value',
                filter=Q(metric_type='recommendation_accuracy')
            ),
            avg_ctr=Avg(
                'value',
                filter=Q(metric_type='click_through_rate')
            ),
            total_clicks=Count(
                'id', filter=Q(metric_type='recommendation_click')
            ),
            total_views=Count(
                'id', filter=Q(metric_type='recommendation_view')
            ),
            total_engagement=Count(
                'id', filter=Q(metric_type='content_engagement')
            )
        )

        # Calculate engagement rates
        control_engagement = (
            (control_metrics['total_clicks'] or 0) +
            (control_metrics['total_engagement'] or 0)
        ) / max(control_count, 1)

        test_engagement = (
            (test_metrics['total_clicks'] or 0) +
            (test_metrics['total_engagement'] or 0)
        ) / max(test_count, 1)

        # Calculate click-through rates
        control_ctr = (
            (control_metrics['total_clicks'] or 0) /
            max(control_metrics['total_views'] or 1, 1)
        )
        test_ctr = (
            (test_metrics['total_clicks'] or 0) /
            max(test_metrics['total_views'] or 1, 1)
        )

        # Simple significance test (basic t-test approximation)
        p_value = None
        if (control_metrics['avg_response_time'] and
            test_metrics['avg_response_time'] and
            control_count > 10 and
            test_count > 10
        ):

            # Basic statistical significance calculation
            control_mean = control_metrics['avg_response_time']
            test_mean = test_metrics['avg_response_time']

            # Simplified p-value calculation (for demonstration)
            difference = abs(control_mean - test_mean)
            pooled_std = math.sqrt(
                ((control_mean * 0.1) ** 2 + (test_mean * 0.1) ** 2) / 2
            )
            if pooled_std > 0:
                t_stat = difference / (
                    pooled_std * math.sqrt(
                        2 / min(control_count, test_count)
                    )
                )
                # Very simplified p-value (this is not statistically rigorous)
                p_value = max(0.001, min(0.999, 1 / (1 + t_stat ** 2)))

        return {
            'experiment': {
                'id': experiment.id,
                'name': experiment.name,
                'status': experiment.status,
                'control_algorithm': experiment.control_algorithm,
                'test_algorithm': experiment.test_algorithm,
                'traffic_split': experiment.traffic_split
            },
            'sample_sizes': {
                'control': control_count,
                'test': test_count
            },
            'metrics': {
                'control': {
                    'avg_response_time': control_metrics['avg_response_time'],
                    'avg_accuracy': control_metrics['avg_accuracy'],
                    'avg_ctr': control_metrics['avg_ctr'],
                    'engagement_rate': control_engagement,
                    'click_through_rate': control_ctr,
                    'total_clicks': control_metrics['total_clicks'],
                    'total_views': control_metrics['total_views'],
                    'total_engagement': control_metrics['total_engagement']
                },
                'test': {
                    'avg_response_time': test_metrics['avg_response_time'],
                    'avg_accuracy': test_metrics['avg_accuracy'],
                    'avg_ctr': test_metrics['avg_ctr'],
                    'engagement_rate': test_engagement,
                    'click_through_rate': test_ctr,
                    'total_clicks': test_metrics['total_clicks'],
                    'total_views': test_metrics['total_views'],
                    'total_engagement': test_metrics['total_engagement']
                }
            },
            'statistical_significance': {
                'p_value': p_value,
                'is_significant': p_value < 0.05 if p_value else False
            }
        }

    except Exception as e:
        print(f"Error getting content experiment stats: {e}")
        return None


def generate_user_recommendations_ab(user, algorithm=None, limit=10):
    """
    Enhanced version of generate_user_recommendations with A/B testing support.
    """
    # Get algorithm based on A/B testing assignment
    if algorithm is None:
        algorithm = get_content_algorithm_for_user(user.id)

    # Record the recommendation request
    start_time = timezone.now()

    try:
        # Call original function with selected algorithm
        recommendations = generate_user_recommendations(
            user, algorithm=algorithm, limit=limit
        )

        # Calculate response time
        response_time = (timezone.now() - start_time).total_seconds() * 1000

        # Record metrics
        record_content_experiment_metric(
            user_id=user.id,
            metric_type='algorithm_response_time',
            value=response_time,
            algorithm_used=algorithm,
            metadata={
                'limit': limit,
                'algorithm': algorithm,
                'results_count': len(recommendations)
            }
        )

        record_content_experiment_metric(
            user_id=user.id,
            metric_type='recommendation_view',
            value=len(recommendations),
            algorithm_used=algorithm,
            metadata={'algorithm': algorithm}
        )

        return recommendations

    except Exception as e:
        print(f"Error in generate_user_recommendations_ab: {e}")
        return []


def record_content_interaction(user_id, interaction_type, content_object=None,
                             metadata=None):
    """
    Record user interactions with content for A/B testing analysis.
    """
    metric_mapping = {
        'click': 'recommendation_click',
        'like': 'post_like',
        'comment': 'post_comment',
        'share': 'post_share',
        'view': 'recommendation_view',
        'engagement': 'content_engagement'
    }

    metric_type = metric_mapping.get(interaction_type, 'content_engagement')

    record_content_experiment_metric(
        user_id=user_id,
        metric_type=metric_type,
        value=1,
        content_object=content_object,
        metadata=metadata or {}
    )


# Helper: store recommendation (missing earlier)
def store_recommendation(user, content_object, score, reason,
                         recommendation_type, rank):
    from content.models import ContentRecommendation
    ctype = ContentType.objects.get_for_model(content_object)
    rec, _ = ContentRecommendation.objects.update_or_create(
        user=user,
        content_type=ctype,
        object_id=content_object.id,
        recommendation_type=recommendation_type,
        defaults={
            'score': score,
            'reason': reason,
            'rank': rank
        }
    )
    return rec


def get_trending_posts(hours=None, days=None, limit=20):
    """
    Get trending posts based on engagement within a time period.

    Args:
        hours: Number of hours to look back
        days: Number of days to look back
        limit: Maximum number of posts to return

    Returns:
        QuerySet of trending posts
    """
    from content.models import Post
    from django.db.models import F

    # Calculate the time threshold
    if hours:
        time_threshold = timezone.now() - timedelta(hours=hours)
    elif days:
        time_threshold = timezone.now() - timedelta(days=days)
    else:
        # Default to 24 hours
        time_threshold = timezone.now() - timedelta(hours=24)

    # Get posts with high engagement in the time period
    trending_posts = Post.objects.filter(
        created_at__gte=time_threshold,
        is_deleted=False
    ).annotate(
        total_engagement=(F('likes_count') + F('comments_count') * 2 +
                          F('shares_count') * 3)
    ).order_by('-total_engagement')[:limit]

    return trending_posts


def create_trending_recommendations(user, trending_24h, trending_week):
    """
    Create trending content recommendations for a user.

    Args:
        user: UserProfile instance
        trending_24h: QuerySet of 24h trending posts
        trending_week: QuerySet of weekly trending posts

    Returns:
        List of created recommendations
    """
    recommendations = []

    # Filter out posts the user has already seen/interacted with
    seen_posts = set(user.user.post_likes.values_list('post_id', flat=True))
    seen_posts.update(
        user.user.post_comments.values_list('post_id', flat=True))

    # Create recommendations for trending posts
    all_trending = list(trending_24h) + list(trending_week)

    for rank, post in enumerate(all_trending[:10], 1):  # Limit to top 10
        if post.id not in seen_posts and post.author != user:
            rec = store_recommendation(
                user=user,
                content_object=post,
                score=0.8,  # High score for trending content
                reason=f"Trending post with {post.likes_count} likes",
                recommendation_type='trending',
                rank=rank
            )
            recommendations.append(rec)

    return recommendations


def analyze_user_content_preferences(user):
    """
    Analyze user's content preferences based on engagement patterns.

    Args:
        user: UserProfile instance

    Returns:
        Dictionary with user preferences
    """
    from content.models import PostHashtag, Like, Post
    from django.db.models import Count
    from django.contrib.contenttypes.models import ContentType

    # Get content type for Post model
    post_content_type = ContentType.objects.get_for_model(Post)

    # Get user's liked posts
    liked_post_ids = Like.objects.filter(
        user=user,
        content_type=post_content_type,
        is_deleted=False
    ).values_list('object_id', flat=True)

    # Analyze hashtag preferences from liked posts
    liked_hashtags = PostHashtag.objects.filter(
        post__id__in=liked_post_ids
    ).values('hashtag__name').annotate(
        count=Count('hashtag__name')
    ).order_by('-count')[:10]

    # Get the actual liked posts for analysis
    liked_posts = Post.objects.filter(
        id__in=liked_post_ids,
        is_deleted=False
    )[:50]

    # Calculate preferences
    preferences = {
        'preferred_hashtags': [
            item['hashtag__name'] for item in liked_hashtags],
        'engagement_frequency': len(liked_posts),
        'preferred_content_types': ['text', 'image'],  # Default types
        'activity_score': min(len(liked_posts) / 10.0, 1.0),
    }

    return preferences


def process_repost_comment_mentions(content_text):
    """
    Process mentions in repost comment text and return mapping of usernames to user IDs.

    Args:
        content_text (str): The repost comment content

    Returns:
        dict: Dictionary mapping username to user profile ID
    """
    from accounts.models import UserProfile
    import re

    if not content_text:
        return {}

    # Extract mentions using regex
    mention_pattern = r'@([a-zA-Z0-9_]+)'
    mentioned_usernames = re.findall(mention_pattern, content_text)

    mention_mapping = {}

    for username in mentioned_usernames:
        try:
            # Get the user profile for the mentioned username
            user_profile = UserProfile.objects.get(user__username=username)
            mention_mapping[username] = str(user_profile.id)
        except UserProfile.DoesNotExist:
            # If user doesn't exist, still include in mapping but with None
            mention_mapping[username] = None

    return mention_mapping
