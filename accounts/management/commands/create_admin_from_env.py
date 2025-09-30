from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from typing import Any
import os


class Command(BaseCommand):
    help = (
        "Create a Django superuser from environment variables "
        "if CREATE_SUPERUSER_ON_BUILD is set."
    )

    def handle(self, *args: str, **options: Any) -> None:
        create_flag = os.environ.get("CREATE_SUPERUSER_ON_BUILD", "").lower()
        if create_flag not in ("1", "true", "yes"):
            self.stdout.write(
                "CREATE_SUPERUSER_ON_BUILD not set true "
                "— skipping admin creation."
            )
            return

        username = (
            os.environ.get("DJANGO_SUPERUSER_USERNAME")
            or os.environ.get("ADMIN_USERNAME")
        )
        email = (
            os.environ.get("DJANGO_SUPERUSER_EMAIL")
            or os.environ.get("ADMIN_EMAIL")
        )
        password = (
            os.environ.get("DJANGO_SUPERUSER_PASSWORD")
            or os.environ.get("ADMIN_PASSWORD")
        )
        force_reset = (
            os.environ.get("DJANGO_SUPERUSER_FORCE_RESET", "").lower()
            in ("1", "true", "yes")
        )

        if not username or not password:
            self.stdout.write(
                "Missing DJANGO_SUPERUSER_USERNAME or "
                "DJANGO_SUPERUSER_PASSWORD environment variables."
            )
            return

        User = get_user_model()
        user = User.objects.filter(username=username).first()
        try:
            if user:
                if not user.is_superuser:
                    user.is_staff = True
                    user.is_superuser = True
                    user.email = email or user.email
                    if force_reset:
                        user.set_password(password)
                    user.save()
                    self.stdout.write(
                        f'Updated existing user "{username}" to '
                        'superuser.'
                    )
                else:
                    if force_reset and password:
                        user.set_password(password)
                        user.save()
                        self.stdout.write(
                            f'Existing superuser "{username}" '
                            'password updated.'
                        )
                    else:
                        self.stdout.write(
                            f'Superuser "{username}" already exists - '
                            'no changes made.'
                        )
                return

            # create new superuser
            User.objects.create_superuser(
                username=username,
                email=email or "",
                password=password,
            )
            self.stdout.write(
                f'Created superuser "{username}" successfully.'
            )
        except IntegrityError as e:
            self.stderr.write(
                f"Database error while creating superuser: {e}"
            )
        except ValueError as e:
            self.stderr.write(f"Value error while creating superuser: {e}")
