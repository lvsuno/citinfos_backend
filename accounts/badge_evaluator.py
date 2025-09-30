"""
Enhanced badge evaluation and storing system for the Database.
Uses thresholds from environment variables for coherent automatic badge management.
"""

import os
import logging
from datetime import timedelta
from typing import Dict, List, Optional, Tuple, Any
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q
from accounts.models import UserProfile, BadgeDefinition, UserBadge, UserEvent

logger = logging.getLogger(__name__)


class BadgeThresholds:
    """Centralized badge threshold management from environment variables."""

    def __init__(self):
        self.thresholds = self._load_from_env()

    def _load_from_env(self) -> Dict[str, int]:
        """Load all badge thresholds from environment variables."""
        return {
            # Early Adopter
            'EARLY_ADOPTER_MAX_INDEX': int(os.environ.get('EARLY_ADOPTER_MAX_INDEX', 1000)),

            # Post Achievement Badges
            'POSTS_BRONZE': int(os.environ.get('BADGE_POSTS_BRONZE', 10)),
            'POSTS_SILVER': int(os.environ.get('BADGE_POSTS_SILVER', 50)),
            'POSTS_GOLD': int(os.environ.get('BADGE_POSTS_GOLD', 200)),

            # Poll Creation Badges
            'POLLS_CREATED_BRONZE': int(os.environ.get('BADGE_POLLS_CREATED_BRONZE', 5)),
            'POLLS_CREATED_SILVER': int(os.environ.get('BADGE_POLLS_CREATED_SILVER', 25)),
            'POLLS_CREATED_GOLD': int(os.environ.get('BADGE_POLLS_CREATED_GOLD', 100)),

            # Poll Voting Badges
            'POLL_VOTES_BRONZE': int(os.environ.get('BADGE_POLL_VOTES_BRONZE', 20)),
            'POLL_VOTES_SILVER': int(os.environ.get('BADGE_POLL_VOTES_SILVER', 100)),
            'POLL_VOTES_GOLD': int(os.environ.get('BADGE_POLL_VOTES_GOLD', 500)),

            # Like Giving Badges
            'LIKES_GIVEN_BRONZE': int(os.environ.get('BADGE_LIKES_GIVEN_BRONZE', 50)),
            'LIKES_GIVEN_SILVER': int(os.environ.get('BADGE_LIKES_GIVEN_SILVER', 250)),
            'LIKES_GIVEN_GOLD': int(os.environ.get('BADGE_LIKES_GIVEN_GOLD', 1000)),

            # Comment Badges
            'COMMENTS_MADE_BRONZE': int(os.environ.get('BADGE_COMMENTS_MADE_BRONZE', 20)),
            'COMMENTS_MADE_SILVER': int(os.environ.get('BADGE_COMMENTS_MADE_SILVER', 100)),
            'COMMENTS_MADE_GOLD': int(os.environ.get('BADGE_COMMENTS_MADE_GOLD', 400)),

            # Repost Badges
            'REPOSTS_BRONZE': int(os.environ.get('BADGE_REPOSTS_BRONZE', 5)),
            'REPOSTS_SILVER': int(os.environ.get('BADGE_REPOSTS_SILVER', 25)),
            'REPOSTS_GOLD': int(os.environ.get('BADGE_REPOSTS_GOLD', 100)),

            # Share Badges (Sent)
            'SHARES_SENT_BRONZE': int(os.environ.get('BADGE_SHARES_SENT_BRONZE', 5)),
            'SHARES_SENT_SILVER': int(os.environ.get('BADGE_SHARES_SENT_SILVER', 30)),
            'SHARES_SENT_GOLD': int(os.environ.get('BADGE_SHARES_SENT_GOLD', 120)),

            # Share Badges (Received)
            'SHARES_RECEIVED_BRONZE': int(os.environ.get('BADGE_SHARES_RECEIVED_BRONZE', 5)),
            'SHARES_RECEIVED_SILVER': int(os.environ.get('BADGE_SHARES_RECEIVED_SILVER', 30)),
            'SHARES_RECEIVED_GOLD': int(os.environ.get('BADGE_SHARES_RECEIVED_GOLD', 120)),
            # Best Comments Badges
            'BEST_COMMENTS_BRONZE': int(os.environ.get('BADGE_BEST_COMMENTS_BRONZE', 1)),
            'BEST_COMMENTS_SILVER': int(os.environ.get('BADGE_BEST_COMMENTS_SILVER', 5)),
            'BEST_COMMENTS_GOLD': int(os.environ.get('BADGE_BEST_COMMENTS_GOLD', 20)),

            # Community Engagement Badges
            'COMMUNITIES_JOINED_BRONZE': int(os.environ.get('BADGE_COMMUNITIES_JOINED_BRONZE', 3)),
            'COMMUNITIES_JOINED_SILVER': int(os.environ.get('BADGE_COMMUNITIES_JOINED_SILVER', 10)),
            'COMMUNITIES_JOINED_GOLD': int(os.environ.get('BADGE_COMMUNITIES_JOINED_GOLD', 25)),

            # Follower Badges
            'FOLLOWER_COUNT_BRONZE': int(os.environ.get('BADGE_FOLLOWER_COUNT_BRONZE', 50)),
            'FOLLOWER_COUNT_SILVER': int(os.environ.get('BADGE_FOLLOWER_COUNT_SILVER', 250)),
            'FOLLOWER_COUNT_GOLD': int(os.environ.get('BADGE_FOLLOWER_COUNT_GOLD', 1000)),

            # Following Badges
            'FOLLOWING_COUNT_BRONZE': int(os.environ.get('BADGE_FOLLOWING_COUNT_BRONZE', 25)),
            'FOLLOWING_COUNT_SILVER': int(os.environ.get('BADGE_FOLLOWING_COUNT_SILVER', 100)),
            'FOLLOWING_COUNT_GOLD': int(os.environ.get('BADGE_FOLLOWING_COUNT_GOLD', 300)),

            # Engagement Score Badges
            'ENGAGEMENT_SCORE_BRONZE': float(os.environ.get('BADGE_ENGAGEMENT_SCORE_BRONZE', 0.25)),
            'ENGAGEMENT_SCORE_SILVER': float(os.environ.get('BADGE_ENGAGEMENT_SCORE_SILVER', 0.50)),
            'ENGAGEMENT_SCORE_GOLD': float(os.environ.get('BADGE_ENGAGEMENT_SCORE_GOLD', 0.75)),

            # Content Quality Score Badges
            'CONTENT_QUALITY_SCORE_BRONZE': float(os.environ.get('BADGE_CONTENT_QUALITY_SCORE_BRONZE', 0.20)),
            'CONTENT_QUALITY_SCORE_SILVER': float(os.environ.get('BADGE_CONTENT_QUALITY_SCORE_SILVER', 0.45)),
            'CONTENT_QUALITY_SCORE_GOLD': float(os.environ.get('BADGE_CONTENT_QUALITY_SCORE_GOLD', 0.70)),

            # Interaction Frequency Badges
            'INTERACTION_FREQUENCY_BRONZE': float(os.environ.get('BADGE_INTERACTION_FREQUENCY_BRONZE', 0.20)),
            'INTERACTION_FREQUENCY_SILVER': float(os.environ.get('BADGE_INTERACTION_FREQUENCY_SILVER', 0.50)),
            'INTERACTION_FREQUENCY_GOLD': float(os.environ.get('BADGE_INTERACTION_FREQUENCY_GOLD', 0.80)),
        }

    def get(self, key: str, default: Any = 0) -> Any:
        """Get threshold value with fallback."""
        return self.thresholds.get(key, default)


class BadgeEvaluationEngine:
    """Main badge evaluation engine that handles all badge logic."""

    def __init__(self):
        self.thresholds = BadgeThresholds()
        self._initialize_badge_definitions()

    def _initialize_badge_definitions(self):
        """Initialize or update badge definitions in the database."""
        badge_configs = self._get_badge_configurations()

        with transaction.atomic():
            for badge_config in badge_configs:
                badge, created = BadgeDefinition.objects.get_or_create(
                    code=badge_config['code'],
                    defaults={
                        'full_name': badge_config['full_name'],
                        'description': badge_config['description'],
                        'icon': badge_config['icon'],
                        'criteria': badge_config['criteria'],
                        'points': badge_config['points'],
                        'is_active': True,
                    }
                )

                if not created:
                    # Update existing badge with new criteria/thresholds
                    badge.full_name = badge_config['full_name']
                    badge.description = badge_config['description']
                    badge.criteria = badge_config['criteria']
                    badge.points = badge_config['points']
                    badge.save()

                logger.info(f"{'Created' if created else 'Updated'} badge: {badge.code}")

    def _get_badge_configurations(self) -> List[Dict]:
        """Get all badge configurations with current thresholds."""
        t = self.thresholds

        return [
            # Early Adopter Badge
            {
                'code': 'early_adopter',
                'full_name': 'Early Adopter',
                'description': f'Join the platform within the first {t.get("EARLY_ADOPTER_MAX_INDEX")} users',
                'icon': 'fas fa-rocket',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'registration_index',
                    'operator': '<=',
                    'value': t.get('EARLY_ADOPTER_MAX_INDEX')
                },
                'points': 100
            },

            # Post Achievement Badges
            {
                'code': 'posts_bronze',
                'full_name': 'Content Creator (Bronze)',
                'description': f'Create {t.get("POSTS_BRONZE")} posts',
                'icon': 'fas fa-edit',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'posts_count',
                    'operator': '>=',
                    'value': t.get('POSTS_BRONZE')
                },
                'points': 25
            },
            {
                'code': 'posts_silver',
                'full_name': 'Content Creator (Silver)',
                'description': f'Create {t.get("POSTS_SILVER")} posts',
                'icon': 'fas fa-edit',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'posts_count',
                    'operator': '>=',
                    'value': t.get('POSTS_SILVER')
                },
                'points': 50
            },
            {
                'code': 'posts_gold',
                'full_name': 'Content Creator (Gold)',
                'description': f'Create {t.get("POSTS_GOLD")}  posts',
                'icon': 'fas fa-edit',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'posts_count',
                    'operator': '>=',
                    'value': t.get('POSTS_GOLD')
                },
                'points': 100
            },

            # Poll Creation Badges
            {
                'code': 'polls_bronze',
                'full_name': 'Poll Creator (Bronze)',
                'description': f'Create {t.get("POLLS_CREATED_BRONZE")} polls',
                'icon': 'fas fa-poll',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'polls_created_count',
                    'operator': '>=',
                    'value': t.get('POLLS_CREATED_BRONZE')
                },
                'points': 15
            },
            {
                'code': 'polls_silver',
                'full_name': 'Poll Creator (Silver)',
                'description': f'Create {t.get("POLLS_CREATED_SILVER")} polls',
                'icon': 'fas fa-poll',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'polls_created_count',
                    'operator': '>=',
                    'value': t.get('POLLS_CREATED_SILVER')
                },
                'points': 40
            },
            {
                'code': 'polls_gold',
                'full_name': 'Poll Creator (Gold)',
                'description': f'Create {t.get("POLLS_CREATED_GOLD")} polls',
                'icon': 'fas fa-poll',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'polls_created_count',
                    'operator': '>=',
                    'value': t.get('POLLS_CREATED_GOLD')
                },
                'points': 80
            },

            # Poll Voting Badges
            {
                'code': 'poll_voter_bronze',
                'full_name': 'Active Voter (Bronze)',
                'description': f'Vote in {t.get("POLL_VOTES_BRONZE")} polls',
                'icon': 'fas fa-vote-yea',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'poll_votes_count',
                    'operator': '>=',
                    'value': t.get('POLL_VOTES_BRONZE')
                },
                'points': 20
            },
            {
                'code': 'poll_voter_silver',
                'full_name': 'Active Voter (Silver)',
                'description': f'Vote in {t.get("POLL_VOTES_SILVER")} polls',
                'icon': 'fas fa-vote-yea',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'poll_votes_count',
                    'operator': '>=',
                    'value': t.get('POLL_VOTES_SILVER')
                },
                'points': 50
            },
            {
                'code': 'poll_voter_gold',
                'full_name': 'Active Voter (Gold)',
                'description': f'Vote in {t.get("POLL_VOTES_GOLD")} polls',
                'icon': 'fas fa-vote-yea',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'poll_votes_count',
                    'operator': '>=',
                    'value': t.get('POLL_VOTES_GOLD')
                },
                'points': 100
            },

            # Like Giving Badges
            {
                'code': 'likes_giver_bronze',
                'full_name': 'Like Enthusiast (Bronze)',
                'description': f'Give {t.get("LIKES_GIVEN_BRONZE")} likes to others',
                'icon': 'fas fa-heart',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'likes_given_count',
                    'operator': '>=',
                    'value': t.get('LIKES_GIVEN_BRONZE')
                },
                'points': 15
            },
            {
                'code': 'likes_giver_silver',
                'full_name': 'Like Enthusiast (Silver)',
                'description': f'Give {t.get("LIKES_GIVEN_SILVER")} likes to others',
                'icon': 'fas fa-heart',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'likes_given_count',
                    'operator': '>=',
                    'value': t.get('LIKES_GIVEN_SILVER')
                },
                'points': 35
            },
            {
                'code': 'likes_giver_gold',
                'full_name': 'Like Enthusiast (Gold)',
                'description': f'Give {t.get("LIKES_GIVEN_GOLD")} likes to others',
                'icon': 'fas fa-heart',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'likes_given_count',
                    'operator': '>=',
                    'value': t.get('LIKES_GIVEN_GOLD')
                },
                'points': 75
            },

            # Comment Badges
            {
                'code': 'commenter_bronze',
                'full_name': 'Community Helper (Bronze)',
                'description': f'Make {t.get("COMMENTS_MADE_BRONZE")} helpful comments',
                'icon': 'fas fa-comment',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'comments_made_count',
                    'operator': '>=',
                    'value': t.get('COMMENTS_MADE_BRONZE')
                },
                'points': 20
            },
            {
                'code': 'commenter_silver',
                'full_name': 'Community Helper (Silver)',
                'description': f'Make {t.get("COMMENTS_MADE_SILVER")} helpful comments',
                'icon': 'fas fa-comment',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'comments_made_count',
                    'operator': '>=',
                    'value': t.get('COMMENTS_MADE_SILVER')
                },
                'points': 50
            },
            {
                'code': 'commenter_gold',
                'full_name': 'Community Helper (Gold)',
                'description': f'Make {t.get("COMMENTS_MADE_GOLD")} helpful comments',
                'icon': 'fas fa-comment',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'comments_made_count',
                    'operator': '>=',
                    'value': t.get('COMMENTS_MADE_GOLD')
                },
                'points': 100
            },

            # Follower Achievement Badges
            {
                'code': 'popular_bronze',
                'full_name': 'Popular (Bronze)',
                'description': f'Gain {t.get("FOLLOWER_COUNT_BRONZE")} followers',
                'icon': 'fas fa-users',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'follower_count',
                    'operator': '>=',
                    'value': t.get('FOLLOWER_COUNT_BRONZE')
                },
                'points': 30
            },
            {
                'code': 'popular_silver',
                'full_name': 'Popular (Silver)',
                'description': f'Gain {t.get("FOLLOWER_COUNT_SILVER")} followers',
                'icon': 'fas fa-users',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'follower_count',
                    'operator': '>=',
                    'value': t.get('FOLLOWER_COUNT_SILVER')
                },
                'points': 75
            },
            {
                'code': 'popular_gold',
                'full_name': 'Popular (Gold)',
                'description': f'Gain {t.get("FOLLOWER_COUNT_GOLD")} followers',
                'icon': 'fas fa-users',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'follower_count',
                    'operator': '>=',
                    'value': t.get('FOLLOWER_COUNT_GOLD')
                },
                'points': 150
            },

            # Social Butterfly Badges (Following)
            {
                'code': 'social_bronze',
                'full_name': 'Social Butterfly (Bronze)',
                'description': f'Follow {t.get("FOLLOWING_COUNT_BRONZE")} users',
                'icon': 'fas fa-user-friends',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'following_count',
                    'operator': '>=',
                    'value': t.get('FOLLOWING_COUNT_BRONZE')
                },
                'points': 20
            },
            {
                'code': 'social_silver',
                'full_name': 'Social Butterfly (Silver)',
                'description': f'Follow {t.get("FOLLOWING_COUNT_SILVER")} users',
                'icon': 'fas fa-user-friends',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'following_count',
                    'operator': '>=',
                    'value': t.get('FOLLOWING_COUNT_SILVER')
                },
                'points': 40
            },
            {
                'code': 'social_gold',
                'full_name': 'Social Butterfly (Gold)',
                'description': f'Follow {t.get("FOLLOWING_COUNT_GOLD")} users',
                'icon': 'fas fa-user-friends',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'following_count',
                    'operator': '>=',
                    'value': t.get('FOLLOWING_COUNT_GOLD')
                },
                'points': 80
            },

            # Quality Comment Badges
            {
                'code': 'quality_commenter_bronze',
                'full_name': 'Quality Contributor (Bronze)',
                'description': f'Have {t.get("BEST_COMMENTS_BRONZE")} comment(s) marked as best',
                'icon': 'fas fa-star',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'best_comments_count',
                    'operator': '>=',
                    'value': t.get('BEST_COMMENTS_BRONZE')
                },
                'points': 50
            },
            {
                'code': 'quality_commenter_silver',
                'full_name': 'Quality Contributor (Silver)',
                'description': f'Have {t.get("BEST_COMMENTS_SILVER")} comments marked as best',
                'icon': 'fas fa-star',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'best_comments_count',
                    'operator': '>=',
                    'value': t.get('BEST_COMMENTS_SILVER')
                },
                'points': 100
            },
            {
                'code': 'quality_commenter_gold',
                'full_name': 'Quality Contributor (Gold)',
                'description': f'Have {t.get("BEST_COMMENTS_GOLD")} comments marked as best',
                'icon': 'fas fa-star',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'best_comments_count',
                    'operator': '>=',
                    'value': t.get('BEST_COMMENTS_GOLD')
                },
                'points': 200
            },

            # High Engagement Score Badge
            {
                'code': 'high_engagement_bronze',
                'full_name': 'Engaging User (Bronze)',
                'description': f'Achieve {t.get("ENGAGEMENT_SCORE_BRONZE"):.2f} engagement score',
                'icon': 'fas fa-chart-line',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'engagement_score',
                    'operator': '>=',
                    'value': t.get('ENGAGEMENT_SCORE_BRONZE')
                },
                'points': 40
            },
            {
                'code': 'high_engagement_silver',
                'full_name': 'Engaging User (Silver)',
                'description': f'Achieve {t.get("ENGAGEMENT_SCORE_SILVER"):.2f} engagement score',
                'icon': 'fas fa-chart-line',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'engagement_score',
                    'operator': '>=',
                    'value': t.get('ENGAGEMENT_SCORE_SILVER')
                },
                'points': 80
            },
            {
                'code': 'high_engagement_gold',
                'full_name': 'Engaging User (Gold)',
                'description': f'Achieve {t.get("ENGAGEMENT_SCORE_GOLD"):.2f} engagement score',
                'icon': 'fas fa-chart-line',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'engagement_score',
                    'operator': '>=',
                    'value': t.get('ENGAGEMENT_SCORE_GOLD')
                },
                'points': 160
            },

            # Repost Badges
            {
                'code': 'reposter_bronze',
                'full_name': 'Content Sharer (Bronze)',
                'description': f'Make {t.get("REPOSTS_BRONZE")} reposts',
                'icon': 'fas fa-retweet',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'reposts_count',
                    'operator': '>=',
                    'value': t.get('REPOSTS_BRONZE')
                },
                'points': 15
            },
            {
                'code': 'reposter_silver',
                'full_name': 'Content Sharer (Silver)',
                'description': f'Make {t.get("REPOSTS_SILVER")} reposts',
                'icon': 'fas fa-retweet',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'reposts_count',
                    'operator': '>=',
                    'value': t.get('REPOSTS_SILVER')
                },
                'points': 35
            },
            {
                'code': 'reposter_gold',
                'full_name': 'Content Sharer (Gold)',
                'description': f'Make {t.get("REPOSTS_GOLD")} reposts',
                'icon': 'fas fa-retweet',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'reposts_count',
                    'operator': '>=',
                    'value': t.get('REPOSTS_GOLD')
                },
                'points': 75
            },

            # Share Sent Badges
            {
                'code': 'share_sender_bronze',
                'full_name': 'Share Sender (Bronze)',
                'description': f'Send {t.get("SHARES_SENT_BRONZE")} private shares',
                'icon': 'fas fa-paper-plane',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'shares_sent_count',
                    'operator': '>=',
                    'value': t.get('SHARES_SENT_BRONZE')
                },
                'points': 10
            },
            {
                'code': 'share_sender_silver',
                'full_name': 'Share Sender (Silver)',
                'description': f'Send {t.get("SHARES_SENT_SILVER")} private shares',
                'icon': 'fas fa-paper-plane',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'shares_sent_count',
                    'operator': '>=',
                    'value': t.get('SHARES_SENT_SILVER')
                },
                'points': 25
            },
            {
                'code': 'share_sender_gold',
                'full_name': 'Share Sender (Gold)',
                'description': f'Send {t.get("SHARES_SENT_GOLD")} private shares',
                'icon': 'fas fa-paper-plane',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'shares_sent_count',
                    'operator': '>=',
                    'value': t.get('SHARES_SENT_GOLD')
                },
                'points': 60
            },

            # Share Received Badges
            {
                'code': 'share_magnet_bronze',
                'full_name': 'Share Magnet (Bronze)',
                'description': f'Receive {t.get("SHARES_RECEIVED_BRONZE")} private shares',
                'icon': 'fas fa-magnet',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'shares_received_count',
                    'operator': '>=',
                    'value': t.get('SHARES_RECEIVED_BRONZE')
                },
                'points': 15
            },
            {
                'code': 'share_magnet_silver',
                'full_name': 'Share Magnet (Silver)',
                'description': f'Receive {t.get("SHARES_RECEIVED_SILVER")} private shares',
                'icon': 'fas fa-magnet',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'shares_received_count',
                    'operator': '>=',
                    'value': t.get('SHARES_RECEIVED_SILVER')
                },
                'points': 30
            },
            {
                'code': 'share_magnet_gold',
                'full_name': 'Share Magnet (Gold)',
                'description': f'Receive {t.get("SHARES_RECEIVED_GOLD")} private shares',
                'icon': 'fas fa-magnet',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'shares_received_count',
                    'operator': '>=',
                    'value': t.get('SHARES_RECEIVED_GOLD')
                },
                'points': 75
            },

            # Community Engagement Badges
            {
                'code': 'community_member_bronze',
                'full_name': 'Community Member (Bronze)',
                'description': f'Join {t.get("COMMUNITIES_JOINED_BRONZE")} communities',
                'icon': 'fas fa-users-cog',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'communities_joined_count',
                    'operator': '>=',
                    'value': t.get('COMMUNITIES_JOINED_BRONZE')
                },
                'points': 20
            },
            {
                'code': 'community_member_silver',
                'full_name': 'Community Member (Silver)',
                'description': f'Join {t.get("COMMUNITIES_JOINED_SILVER")} communities',
                'icon': 'fas fa-users-cog',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'communities_joined_count',
                    'operator': '>=',
                    'value': t.get('COMMUNITIES_JOINED_SILVER')
                },
                'points': 40
            },
            {
                'code': 'community_member_gold',
                'full_name': 'Community Member (Gold)',
                'description': f'Join {t.get("COMMUNITIES_JOINED_GOLD")} communities',
                'icon': 'fas fa-users-cog',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'communities_joined_count',
                    'operator': '>=',
                    'value': t.get('COMMUNITIES_JOINED_GOLD')
                },
                'points': 80
            },

            # Content Quality Score Badges
            {
                'code': 'quality_content_bronze',
                'full_name': 'Quality Creator (Bronze)',
                'description': f'Achieve {t.get("CONTENT_QUALITY_SCORE_BRONZE"):.2f} content quality score',
                'icon': 'fas fa-award',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'content_quality_score',
                    'operator': '>=',
                    'value': t.get('CONTENT_QUALITY_SCORE_BRONZE')
                },
                'points': 35
            },
            {
                'code': 'quality_content_silver',
                'full_name': 'Quality Creator (Silver)',
                'description': f'Achieve {t.get("CONTENT_QUALITY_SCORE_SILVER"):.2f} content quality score',
                'icon': 'fas fa-award',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'content_quality_score',
                    'operator': '>=',
                    'value': t.get('CONTENT_QUALITY_SCORE_SILVER')
                },
                'points': 70
            },
            {
                'code': 'quality_content_gold',
                'full_name': 'Quality Creator (Gold)',
                'description': f'Achieve {t.get("CONTENT_QUALITY_SCORE_GOLD"):.2f} content quality score',
                'icon': 'fas fa-award',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'content_quality_score',
                    'operator': '>=',
                    'value': t.get('CONTENT_QUALITY_SCORE_GOLD')
                },
                'points': 140
            },

            # Interaction Frequency Badges
            {
                'code': 'active_user_bronze',
                'full_name': 'Active User (Bronze)',
                'description': f'Achieve {t.get("INTERACTION_FREQUENCY_BRONZE"):.2f} interaction frequency',
                'icon': 'fas fa-bolt',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'interaction_frequency',
                    'operator': '>=',
                    'value': t.get('INTERACTION_FREQUENCY_BRONZE')
                },
                'points': 30
            },
            {
                'code': 'active_user_silver',
                'full_name': 'Active User (Silver)',
                'description': f'Achieve {t.get("INTERACTION_FREQUENCY_SILVER"):.2f} interaction frequency',
                'icon': 'fas fa-bolt',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'interaction_frequency',
                    'operator': '>=',
                    'value': t.get('INTERACTION_FREQUENCY_SILVER')
                },
                'points': 60
            },
            {
                'code': 'active_user_gold',
                'full_name': 'Active User (Gold)',
                'description': f'Achieve {t.get("INTERACTION_FREQUENCY_GOLD"):.2f} interaction frequency',
                'icon': 'fas fa-bolt',
                'criteria': {
                    'type': 'stat_threshold',
                    'stat': 'interaction_frequency',
                    'operator': '>=',
                    'value': t.get('INTERACTION_FREQUENCY_GOLD')
                },
                'points': 120
            },
        ]

    def evaluate_user_badges(self, user_profile: UserProfile) -> Tuple[int, List[str]]:
        """
        Evaluate all badges for a single user profile.

        Returns:
            Tuple of (newly_awarded_count, list_of_new_badge_codes)
        """
        newly_awarded = []

        try:
            with transaction.atomic():
                # Get all active badges that user doesn't have yet
                existing_badges = set(
                    UserBadge.objects.filter(
                        profile=user_profile,
                        is_deleted=False
                    ).values_list('badge__code', flat=True)
                )

                active_badges = BadgeDefinition.objects.filter(
                    is_active=True,
                    is_deleted=False
                ).exclude(code__in=existing_badges)

                for badge in active_badges:
                    if self._evaluate_badge_criteria(user_profile, badge):
                        # Award the badge
                        user_badge = UserBadge.objects.create(
                            profile=user_profile,
                            badge=badge,
                            first_trigger_event='system_evaluation',
                            metadata={
                                'evaluated_at': timezone.now().isoformat(),
                                'auto_awarded': True
                            }
                        )

                        newly_awarded.append(badge.code)

                        # Log the badge award
                        UserEvent.objects.create(
                            user=user_profile,
                            event_type='badge_earned',
                            description=f'Earned badge: {badge.full_name}',
                            severity='info',
                            metadata={
                                'badge_id': str(badge.id),
                                'badge_code': badge.code,
                                'badge_full_name': badge.full_name,
                                'points_earned': badge.points
                            }
                        )

                        logger.info(f"Awarded badge '{badge.code}' to user {user_profile.user.username}")

        except Exception as e:
            logger.error(f"Error evaluating badges for user {user_profile.id}: {str(e)}")
            return 0, []

        return len(newly_awarded), newly_awarded

    def _evaluate_badge_criteria(self, user_profile: UserProfile, badge: BadgeDefinition) -> bool:
        """Evaluate if user meets badge criteria."""
        try:
            criteria = badge.criteria
            if not criteria:
                return False

            return self._evaluate_criteria_recursive(user_profile, criteria)

        except Exception as e:
            logger.error(f"Error evaluating criteria for badge {badge.code}: {str(e)}")
            return False

    def _evaluate_criteria_recursive(self, user_profile: UserProfile, criteria: Dict) -> bool:
        """Recursively evaluate badge criteria (supports AND/OR logic)."""
        criteria_type = criteria.get('type')

        if criteria_type == 'and':
            conditions = criteria.get('conditions', [])
            return all(self._evaluate_criteria_recursive(user_profile, cond) for cond in conditions)

        elif criteria_type == 'or':
            conditions = criteria.get('conditions', [])
            return any(self._evaluate_criteria_recursive(user_profile, cond) for cond in conditions)

        elif criteria_type == 'stat_threshold':
            return self._evaluate_stat_threshold(user_profile, criteria)

        elif criteria_type == 'account_age_days':
            return self._evaluate_account_age(user_profile, criteria)

        return False

    def _evaluate_stat_threshold(self, user_profile: UserProfile, criteria: Dict) -> bool:
        """Evaluate stat threshold criteria."""
        stat = criteria.get('stat')
        operator = criteria.get('operator', '>=')
        value = criteria.get('value')

        if not hasattr(user_profile, stat):
            logger.warning(f"UserProfile has no attribute '{stat}'")
            return False

        current_value = getattr(user_profile, stat)

        if operator == '>=':
            return current_value >= value
        elif operator == '>':
            return current_value > value
        elif operator == '<=':
            return current_value <= value
        elif operator == '<':
            return current_value < value
        elif operator == '==':
            return current_value == value
        elif operator == '!=':
            return current_value != value

        return False

    def _evaluate_account_age(self, user_profile: UserProfile, criteria: Dict) -> bool:
        """Evaluate account age criteria."""
        required_days = criteria.get('value', 0)
        operator = criteria.get('operator', '>=')

        account_age_days = (timezone.now() - user_profile.created_at).days

        if operator == '>=':
            return account_age_days >= required_days
        elif operator == '>':
            return account_age_days > required_days
        elif operator == '<=':
            return account_age_days <= required_days
        elif operator == '<':
            return account_age_days < required_days
        elif operator == '==':
            return account_age_days == required_days

        return False

    def evaluate_all_users(self, batch_size: int = 100) -> Dict[str, int]:
        """
        Evaluate badges for all users in batches.

        Returns:
            Dictionary with evaluation statistics
        """
        stats = {
            'users_processed': 0,
            'total_badges_awarded': 0,
            'errors': 0
        }

        users_queryset = UserProfile.objects.filter(is_deleted=False).order_by('id')
        total_users = users_queryset.count()

        logger.info(f"Starting badge evaluation for {total_users} users...")

        for offset in range(0, total_users, batch_size):
            batch = users_queryset[offset:offset + batch_size]

            for user_profile in batch:
                try:
                    newly_awarded_count, _ = self.evaluate_user_badges(user_profile)
                    stats['total_badges_awarded'] += newly_awarded_count
                    stats['users_processed'] += 1

                except Exception as e:
                    logger.error(f"Error processing user {user_profile.id}: {str(e)}")
                    stats['errors'] += 1

            # Log progress
            logger.info(f"Processed {min(offset + batch_size, total_users)}/{total_users} users")

        logger.info(f"Badge evaluation complete. Stats: {stats}")
        return stats

    def get_badge_progress(self, user_profile: UserProfile, badge_code: str) -> Optional[Dict]:
        """Get progress toward a specific badge."""
        try:
            badge = BadgeDefinition.objects.get(code=badge_code, is_active=True, is_deleted=False)

            # Check if user already has this badge
            has_badge = UserBadge.objects.filter(
                profile=user_profile,
                badge=badge,
                is_deleted=False
            ).exists()

            if has_badge:
                return {
                    'badge_code': badge_code,
                    'badge_full_name': badge.full_name,
                    'earned': True,
                    'progress': 100
                }

            # Calculate progress based on criteria
            criteria = badge.criteria
            if criteria.get('type') == 'stat_threshold':
                stat = criteria.get('stat')
                required_value = criteria.get('value')
                current_value = getattr(user_profile, stat, 0)

                progress = min((current_value / required_value) * 100, 100) if required_value > 0 else 0

                return {
                    'badge_code': badge_code,
                    'badge_full_name': badge.full_name,
                    'description': badge.description,
                    'earned': False,
                    'progress': round(progress, 2),
                    'current_value': current_value,
                    'required_value': required_value,
                    'remaining': max(required_value - current_value, 0)
                }

        except BadgeDefinition.DoesNotExist:
            logger.warning(f"Badge with code '{badge_code}' not found")
            return None
        except Exception as e:
            logger.error(f"Error calculating badge progress: {str(e)}")
            return None

        return None


# Global instance
badge_evaluator = BadgeEvaluationEngine()
