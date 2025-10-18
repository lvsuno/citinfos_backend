"""
Management command to create communities for divisions that don't have one.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import AdministrativeDivision, UserProfile
from communities.models import Community
from django.utils.text import slugify

User = get_user_model()


class Command(BaseCommand):
    help = 'Create communities for divisions that don\'t have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--country',
            type=str,
            help='Filter by country name (e.g., "Canada")',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        country_name = options.get('country')

        # Get divisions
        divisions_qs = AdministrativeDivision.objects.all()

        if country_name:
            # Find divisions by country name (case-insensitive)
            from core.models import Country
            try:
                country = Country.objects.get(name__iexact=country_name)
                divisions_qs = divisions_qs.filter(country=country)
                self.stdout.write(f'Filtering by country: {country.name}')
            except Country.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Country "{country_name}" not found')
                )
                return

        # Get default creator
        creator_user = User.objects.filter(is_superuser=True).first()
        if not creator_user:
            creator_user = User.objects.first()

        if not creator_user:
            self.stdout.write(
                self.style.ERROR('No users found in database. Create a user first.')
            )
            return

        creator_profile = UserProfile.objects.filter(user=creator_user).first()
        if not creator_profile:
            self.stdout.write(
                self.style.ERROR(f'No UserProfile found for user {creator_user.username}')
            )
            return

        self.stdout.write(f'Using creator: {creator_user.username}')

        # Find divisions without communities
        divisions_without_communities = []

        for division in divisions_qs:
            community = Community.objects.filter(
                division=division,
                is_deleted=False
            ).first()

            if not community:
                divisions_without_communities.append(division)

        self.stdout.write(
            f'\nFound {len(divisions_without_communities)} divisions without communities'
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN MODE ==='))
            self.stdout.write('The following communities would be created:\n')
            for division in divisions_without_communities[:20]:  # Show first 20
                slug = slugify(division.name)[:100]
                self.stdout.write(f'  - {division.name:40s} -> slug: {slug}')
            if len(divisions_without_communities) > 20:
                self.stdout.write(f'  ... and {len(divisions_without_communities) - 20} more')
            return

        # Create communities
        created_count = 0
        skipped_count = 0

        for division in divisions_without_communities:
            try:
                # Generate unique slug
                base_slug = slugify(division.name)[:100]
                slug = base_slug
                counter = 1

                while Community.objects.filter(slug=slug).exists():
                    slug = f"{base_slug[:90]}-{counter}"
                    counter += 1

                # Create community
                community = Community.objects.create(
                    name=division.name,
                    slug=slug,
                    division=division,
                    description=f'Communauté de {division.name}',
                    creator=creator_profile,
                    community_type='public'
                )

                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Created: {division.name:40s} -> {slug}'
                    )
                )

            except Exception as e:
                skipped_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Failed: {division.name:40s} -> {str(e)}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n\nSummary: Created {created_count} communities, '
                f'skipped {skipped_count}'
            )
        )
