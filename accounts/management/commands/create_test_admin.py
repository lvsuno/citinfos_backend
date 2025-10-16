from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from accounts.models import UserProfile, AdminProfile
from core.models import AdministrativeDivision
from datetime import date
import uuid


class Command(BaseCommand):
    help = "Create an admin user for testing the admin dashboard"

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Admin username', default='admin')
        parser.add_argument('--email', type=str, help='Admin email', default='admin@citinfos.local')
        parser.add_argument('--password', type=str, help='Admin password', default='admin123')
        parser.add_argument('--first_name', type=str, help='Admin first name', default='Admin')
        parser.add_argument('--last_name', type=str, help='Admin last name', default='User')
        parser.add_argument('--phone', type=str, help='Admin phone number', default='+1234567890')

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
                    user.is_staff = True
                    user.is_superuser = True
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
                    user.is_staff = True
                    user.is_superuser = True
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
                        date_of_birth=date(1990, 1, 1),  # Default date
                        bio='Administrateur système',
                        administrative_division=admin_division,
                        is_verified=True,
                        role='admin'
                    )

                # Update profile to admin role
                profile.role = 'admin'
                profile.is_verified = True
                profile.save()

                # Get or create AdminProfile
                admin_profile, created = AdminProfile.objects.get_or_create(
                    profile=profile,
                    defaults={
                        'admin_level': 'super_admin',
                        'department': 'IT',
                        'permissions': ['all'],
                        'access_level': 10,
                        'can_access_sensitive_data': True,
                        'can_modify_system_settings': True,
                        'can_manage_users': True,
                        'can_manage_content': True,
                        'can_view_analytics': True,
                        'can_export_data': True,
                        'is_active': True
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Admin user "{username}" created successfully!')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Admin user "{username}" updated successfully!')
                    )

                self.stdout.write('')
                self.stdout.write('Admin credentials:')
                self.stdout.write(f'Username: {username}')
                self.stdout.write(f'Email: {email}')
                self.stdout.write(f'Password: {password}')
                self.stdout.write('')
                self.stdout.write('You can now login and access the admin dashboard at /admin/dashboard')

        except IntegrityError as e:
            self.stderr.write(
                self.style.ERROR(f'Database error while creating admin user: {e}')
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error while creating admin user: {e}')
            )