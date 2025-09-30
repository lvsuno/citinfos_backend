"""
Management command to set up default content moderation rules.
"""

from django.core.management.base import BaseCommand
from content.models import ContentModerationRule


class Command(BaseCommand):
    help = 'Set up default content moderation rules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing rules before creating new ones',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Deleting existing moderation rules...')
            ContentModerationRule.objects.all().delete()

        self.stdout.write('Creating default moderation rules...')

        # Basic profanity filter
        ContentModerationRule.objects.get_or_create(
            name='Basic Profanity Filter',
            defaults={
                'rule_type': 'keyword',
                'description': 'Flags content containing common profanity',
                'configuration': {
                    'keywords': [
                        'damn', 'hell', 'shit', 'fuck', 'bitch', 'ass',
                        'bastard', 'crap', 'piss', 'slut', 'whore'
                    ]
                },
                'action': 'flag',
                'severity_level': 2,
                'is_active': True,
                'applies_to_posts': True,
                'applies_to_comments': True,
            }
        )

        # Hate speech keywords
        ContentModerationRule.objects.get_or_create(
            name='Hate Speech Keywords',
            defaults={
                'rule_type': 'keyword',
                'description': 'Flags content with hate speech terms',
                'configuration': {
                    'keywords': [
                        'nazi', 'hitler', 'genocide', 'terrorist', 'extremist',
                        'racial slurs placeholder'  # Add actual terms as needed
                    ]
                },
                'action': 'hide',
                'severity_level': 5,
                'is_active': True,
                'applies_to_posts': True,
                'applies_to_comments': True,
            }
        )

        # Spam keywords
        ContentModerationRule.objects.get_or_create(
            name='Spam Keywords',
            defaults={
                'rule_type': 'keyword',
                'description': 'Flags potential spam content',
                'configuration': {
                    'keywords': [
                        'buy now', 'click here', 'free money', 'make money fast',
                        'winner', 'congratulations you won', 'limited time offer',
                        'act now', 'urgent', 'exclusive deal'
                    ]
                },
                'action': 'flag',
                'severity_level': 3,
                'is_active': True,
                'applies_to_posts': True,
                'applies_to_comments': True,
            }
        )

        # High toxicity ML rule
        ContentModerationRule.objects.get_or_create(
            name='High Toxicity Detection',
            defaults={
                'rule_type': 'ml_toxicity',
                'description': 'Uses ML to detect highly toxic content',
                'configuration': {
                    'toxicity_threshold': 0.8
                },
                'action': 'hide',
                'severity_level': 4,
                'is_active': True,
                'applies_to_posts': True,
                'applies_to_comments': True,
            }
        )

        # Moderate toxicity ML rule
        ContentModerationRule.objects.get_or_create(
            name='Moderate Toxicity Detection',
            defaults={
                'rule_type': 'ml_toxicity',
                'description': 'Flags moderately toxic content for review',
                'configuration': {
                    'toxicity_threshold': 0.6
                },
                'action': 'flag',
                'severity_level': 3,
                'is_active': True,
                'applies_to_posts': True,
                'applies_to_comments': True,
            }
        )

        # Spam detection ML rule
        ContentModerationRule.objects.get_or_create(
            name='Spam Detection',
            defaults={
                'rule_type': 'ml_spam',
                'description': 'Uses ML to detect spam content',
                'configuration': {
                    'spam_threshold': 0.7
                },
                'action': 'flag',
                'severity_level': 3,
                'is_active': True,
                'applies_to_posts': True,
                'applies_to_comments': True,
            }
        )

        # Negative sentiment rule (for sensitive communities)
        ContentModerationRule.objects.get_or_create(
            name='Negative Sentiment Filter',
            defaults={
                'rule_type': 'sentiment',
                'description': 'Flags very negative content in sensitive contexts',
                'configuration': {
                    'blocked_sentiments': ['negative'],
                    'confidence_threshold': 0.9
                },
                'action': 'flag',
                'severity_level': 2,
                'is_active': False,  # Disabled by default
                'applies_to_posts': True,
                'applies_to_comments': True,
            }
        )

        # Self-harm keywords
        ContentModerationRule.objects.get_or_create(
            name='Self-Harm Detection',
            defaults={
                'rule_type': 'keyword',
                'description': 'Detects content related to self-harm',
                'configuration': {
                    'keywords': [
                        'kill myself', 'end it all', 'suicide', 'self harm',
                        'cutting', 'want to die', 'life not worth living'
                    ]
                },
                'action': 'escalate',
                'severity_level': 5,
                'is_active': True,
                'applies_to_posts': True,
                'applies_to_comments': True,
            }
        )

        # Violence keywords
        ContentModerationRule.objects.get_or_create(
            name='Violence Detection',
            defaults={
                'rule_type': 'keyword',
                'description': 'Detects content with violent threats',
                'configuration': {
                    'keywords': [
                        'kill you', 'murder', 'bomb', 'terrorist attack',
                        'shoot up', 'violence', 'hurt you', 'beat you up'
                    ]
                },
                'action': 'hide',
                'severity_level': 5,
                'is_active': True,
                'applies_to_posts': True,
                'applies_to_comments': True,
            }
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {ContentModerationRule.objects.count()} moderation rules'
            )
        )

        # Display summary
        self.stdout.write('\nModeration Rules Summary:')
        for rule in ContentModerationRule.objects.all().order_by('severity_level', 'name'):
            status = 'ACTIVE' if rule.is_active else 'INACTIVE'
            self.stdout.write(
                f'  - {rule.name} (Severity: {rule.severity_level}, Action: {rule.action}) [{status}]'
            )
