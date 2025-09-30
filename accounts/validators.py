"""
Custom password validators to match client-side requirements.
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class StrongPasswordValidator:
    """
    Validates that the password meets strong password requirements:
    - At least 8 characters
    - Include uppercase and lowercase letters
    - Include numbers
    - Include special characters (!@#$%^&*)
    """

    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                _("Password must be at least 8 characters long."),
                code='password_too_short',
            )

        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code='password_no_upper',
            )

        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code='password_no_lower',
            )

        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _("Password must contain at least one number."),
                code='password_no_number',
            )

        if not re.search(r'[!@#$%^&*]', password):
            raise ValidationError(
                _(
                    "Password must contain at least one special character "
                    "(!@#$%^&*)."
                ),
                code='password_no_special',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 8 characters, including "
            "uppercase and lowercase letters, numbers, and special "
            "characters (!@#$%^&*)."
        )


class PasswordStrengthValidator:
    """
    Validates password strength levels matching client-side logic:
    - Weak: less than 6 characters
    - Medium: 8+ characters but not strong
    - Strong: 8+ characters with uppercase, number, and special character
    """

    def validate(self, password, user=None):
        if len(password) < 6:
            raise ValidationError(
                _("Password is too weak. Must be at least 6 characters."),
                code='password_too_weak',
            )

        # Allow medium strength passwords (8+ characters)
        # but warn about strong requirements
        if len(password) >= 8:
            # Strong password pattern: uppercase, number,
            # special character, 8+ chars
            strong_pattern = r'^(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*]).{8,}$'
            if not re.match(strong_pattern, password):
                # This is medium strength - we'll allow it
                # but could add warnings
                pass

    def get_help_text(self):
        return _(
            "For best security, use a strong password with at least "
            "8 characters, including uppercase letters, numbers, and "
            "special characters (!@#$%^&*)."
        )
