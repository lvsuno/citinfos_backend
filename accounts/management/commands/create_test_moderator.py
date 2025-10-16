from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from accounts.models import UserProfile, ModeratorProfile
from core.models import AdministrativeDivision
from datetime import date
import uuid


class Command(BaseCommand):
    help = "Create a moderator user for testing the moderation dashboard"

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Moderator username', default='moderator')
        parser.add_argument('--email', type=str, help='Moderator email', default='moderator@citinfos.local')
        parser.add_argument('--password', type=str, help='Moderator password', default='moderator123')
        parser.add_argument('--first_name', type=str, help='Moderator first name', default='Moderator')
        parser.add_argument('--last_name', type=str, help='Moderator last name', default='User')
        parser.add_argument('--phone', type=str, help='Moderator phone number', default='+1234567891')

    def handle(self, *args, **options):
        User = get_user_model()
        
        username = options['username']
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        phone = options['phone']

        try:
            with transaction.atomic():
                # Check if user already exists
                if User.objects.filter(username=username).exists():
                    self.stdout.write(
                        self.style.WARNING(f'User "{username}" already exists. Updating...')
                    )
                    user = User.objects.get(username=username)
                    user.email = email
                    user.first_name = first_name
                    user.last_name = last_name
                    user.set_password(password)
                    user.is_staff = False  # Moderators are not Django staff
                    user.is_superuser = False
                    user.save()
                else:
                    # Create Django user
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name
                    )
                    user.is_staff = False  # Moderators are not Django staff
                    user.is_superuser = False
                    user.save()

                # Get or create UserProfile
                try:
                    profile = user.profile
                    self.stdout.write(f'UserProfile for "{username}" already exists. Updating...')
                except UserProfile.DoesNotExist:
                    # Find a default administrative division (Sherbrooke if available)
                    admin_division = None
                    try:
                        admin_division = AdministrativeDivision.objects.filter(
                            name__icontains='sherbrooke'
                        ).first()
                        if not admin_division:
                            # Fallback to any division
                            admin_division = AdministrativeDivision.objects.first()
                    except:
                        pass

                    profile = UserProfile.objects.create(
                        user=user,
                        phone_number=phone,
                        date_of_birth=date(1992, 5, 15),  # Different default date
                        bio='Modérateur de contenu',
                        administrative_division=admin_division,
                        is_verified=True,
                        role='moderator'
                    )

                # Update profile to moderator role
                profile.role = 'moderator'
                profile.is_verified = True
                profile.save()

                # Get or create ModeratorProfile
                moderator_profile, created = ModeratorProfile.objects.get_or_create(
                    profile=profile,
                    defaults={
                        'moderator_level': 'senior',
                        'specialization': 'general',
                        'assigned_communities': [],
                        'assigned_categories': ['general', 'content', 'spam'],
                        'languages': ['fr', 'en'],
                        'can_remove_posts': True,
                        'can_remove_comments': True,
                        'can_ban_users': False,  # Senior but not lead
                        'can_suspend_users': True,
                        'can_feature_content': False,
                        'can_manage_reports': True,
                        'can_escalate_issues': True,
                        'can_send_warnings': True,
                        'timezone': 'America/Montreal',
                        'is_available': True,
                        'is_active': True,
                        'training_completed': ['basic_moderation', 'community_guidelines', 'content_policy'],
                        'certifications': ['content_moderation_101'],
                        'training_score': 92.5
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Moderator user "{username}" created successfully!')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Moderator user "{username}" updated successfully!')
                    )

                self.stdout.write('')
                self.stdout.write('Moderator credentials:')
                self.stdout.write(f'Username: {username}')
                self.stdout.write(f'Email: {email}')
                self.stdout.write(f'Password: {password}')
                self.stdout.write('')
                self.stdout.write('Moderator details:')
                self.stdout.write(f'Level: {moderator_profile.get_moderator_level_display()}')
                self.stdout.write(f'Specialization: {moderator_profile.get_specialization_display()}')
                self.stdout.write(f'Languages: {", ".join(moderator_profile.languages)}')
                self.stdout.write('')
                self.stdout.write('You can now login and access the moderation dashboard at /moderator/dashboard')

        except IntegrityError as e:
            self.stderr.write(
                self.style.ERROR(f'Database error while creating moderator user: {e}')
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error while creating moderator user: {e}')
            )