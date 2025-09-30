"""Management command to test the comprehensive search system."""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from search.global_search import GlobalSearchEngine
import json


class Command(BaseCommand):
    help = 'Test the comprehensive search system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--query',
            type=str,
            default='test',
            help='Search query to test'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username to test search as (optional)'
        )
        parser.add_argument(
            '--types',
            type=str,
            help='Comma-separated content types to search'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Limit results per type'
        )

    def handle(self, *args, **options):
        query = options['query']
        username = options.get('user')
        types_str = options.get('types')
        limit = options['limit']

        # Get user
        if username:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(
                    self.style.SUCCESS(f'Testing search as user: {username}')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User {username} not found')
                )
                return
        else:
            # Use anonymous user
            from django.contrib.auth.models import AnonymousUser
            user = AnonymousUser()
            self.stdout.write(
                self.style.WARNING('Testing search as anonymous user')
            )

        # Parse content types
        content_types = None
        if types_str:
            content_types = [t.strip() for t in types_str.split(',')]

        self.stdout.write(
            self.style.SUCCESS(f'Testing search: "{query}"')
        )
        if content_types:
            self.stdout.write(f'Content types: {", ".join(content_types)}')

        # Create search engine and perform search
        try:
            search_engine = GlobalSearchEngine(user)
            results = search_engine.search(
                query=query,
                content_types=content_types,
                limit=limit
            )

            # Display results
            self.stdout.write('\n' + '='*50)
            self.stdout.write(f'SEARCH RESULTS FOR: "{query}"')
            self.stdout.write('='*50)

            self.stdout.write(f'Total results: {results["total_count"]}')
            self.stdout.write(f'Search time: {results["timestamp"]}')

            for content_type, items in results['results'].items():
                if content_type.endswith('_count'):
                    continue

                count = results['results'].get(f'{content_type}_count', 0)
                self.stdout.write(f'\n{content_type.upper()} ({count} results):')
                self.stdout.write('-' * 30)

                if not items:
                    self.stdout.write('  No results found')
                else:
                    for i, item in enumerate(items[:3], 1):  # Show first 3
                        title = item.get('title', item.get('name', 'Untitled'))
                        item_type = item.get('type', content_type)
                        self.stdout.write(f'  {i}. [{item_type}] {title[:50]}...')
                        if 'author' in item:
                            author = item['author'].get('username', 'Unknown')
                            self.stdout.write(f'     Author: {author}')
                        if 'relevance_score' in item:
                            score = item['relevance_score']
                            self.stdout.write(f'     Relevance: {score}')
                        self.stdout.write(f'     URL: {item.get("url", "N/A")}')
                        self.stdout.write('')

            # Show detailed JSON for debugging (optional)
            if options.get('verbosity', 1) >= 2:
                self.stdout.write('\n' + '='*50)
                self.stdout.write('DETAILED JSON RESULTS:')
                self.stdout.write('='*50)
                self.stdout.write(json.dumps(results, indent=2, default=str))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Search failed: {str(e)}')
            )
            if options.get('verbosity', 1) >= 2:
                import traceback
                self.stdout.write(traceback.format_exc())

    def get_verbosity(self, options):
        """Get verbosity level from options."""
        return options.get('verbosity', 1)
