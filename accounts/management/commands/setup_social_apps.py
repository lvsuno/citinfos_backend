"""
Management command to create social applications for OAuth providers.
This command creates SocialApp instances for Google, Facebook, GitHub, and Twitter.
"""
from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Create social applications for OAuth providers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--google-client-id',
            type=str,
            help='Google OAuth Client ID'
        )
        parser.add_argument(
            '--google-client-secret',
            type=str,
            help='Google OAuth Client Secret'
        )
        parser.add_argument(
            '--facebook-app-id',
            type=str,
            help='Facebook App ID'
        )
        parser.add_argument(
            '--facebook-app-secret',
            type=str,
            help='Facebook App Secret'
        )
        parser.add_argument(
            '--github-client-id',
            type=str,
            help='GitHub OAuth Client ID'
        )
        parser.add_argument(
            '--github-client-secret',
            type=str,
            help='GitHub OAuth Client Secret'
        )
        parser.add_argument(
            '--twitter-client-id',
            type=str,
            help='Twitter OAuth Client ID'
        )
        parser.add_argument(
            '--twitter-client-secret',
            type=str,
            help='Twitter OAuth Client Secret'
        )

    def handle(self, *args, **options):
        # Get the current site
        site = Site.objects.get_current()

        # Social app configurations
        social_apps = [
            {
                'provider': 'google',
                'name': 'Google',
                'client_id': options.get('google_client_id'),
                'secret': options.get('google_client_secret'),
            },
            {
                'provider': 'facebook',
                'name': 'Facebook',
                'client_id': options.get('facebook_app_id'),
                'secret': options.get('facebook_app_secret'),
            },
            {
                'provider': 'github',
                'name': 'GitHub',
                'client_id': options.get('github_client_id'),
                'secret': options.get('github_client_secret'),
            },
            {
                'provider': 'twitter',
                'name': 'Twitter',
                'client_id': options.get('twitter_client_id'),
                'secret': options.get('twitter_client_secret'),
            },
        ]

        created_count = 0
        updated_count = 0

        for app_config in social_apps:
            provider = app_config['provider']
            client_id = app_config['client_id']
            secret = app_config['secret']

            # Skip if credentials not provided
            if not client_id or not secret:
                self.stdout.write(
                    self.style.WARNING(
                        f'Skipping {provider} - credentials not provided'
                    )
                )
                continue

            # Create or update the social app
            app, created = SocialApp.objects.get_or_create(
                provider=provider,
                defaults={
                    'name': app_config['name'],
                    'client_id': client_id,
                    'secret': secret,
                }
            )

            if created:
                app.sites.add(site)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created {provider} social app'
                    )
                )
            else:
                # Update existing app
                app.client_id = client_id
                app.secret = secret
                app.save()
                if site not in app.sites.all():
                    app.sites.add(site)
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated {provider} social app'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed social apps: '
                f'{created_count} created, {updated_count} updated'
            )
        )

        # Display usage instructions
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Next steps:'))
        self.stdout.write('1. Configure OAuth applications on each platform:')
        self.stdout.write('   - Google: https://console.developers.google.com/')
        self.stdout.write('   - Facebook: https://developers.facebook.com/')
        self.stdout.write('   - GitHub: https://github.com/settings/developers')
        self.stdout.write('   - Twitter: https://developer.twitter.com/')
        self.stdout.write('')
        self.stdout.write('2. Set redirect URIs in each OAuth app:')
        self.stdout.write('   - Development: http://localhost:3000/auth/callback')
        self.stdout.write('   - Production: https://yourdomain.com/auth/callback')
        self.stdout.write('')
        self.stdout.write('3. Set environment variables:')
        self.stdout.write('   - Add credentials to your .env file')
        self.stdout.write('   - See .env.social.example for reference')