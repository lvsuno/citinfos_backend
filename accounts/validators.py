"""
Custom password validators to match client-side requirements.
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

try:
    import phonenumbers
    from phonenumbers import NumberParseException
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False


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


def validate_phone_number(phone_number, country_code=None):
    """
    Validate a phone number using Google's libphonenumber library.

    Args:
        phone_number (str): The phone number to validate
        country_code (str): ISO 3166-1 alpha-2 country code (e.g., 'CA', 'US', 'FR')
                           If not provided, phone must include country code (e.g., +1...)

    Returns:
        dict: Dictionary with validation results
            - valid (bool): Whether the number is valid
            - formatted (str): Formatted phone number (international format)
            - national (str): National format
            - country_code (str): Detected country code
            - error (str): Error message if invalid

    Raises:
        ValidationError: If the phone number is invalid
    """
    if not PHONENUMBERS_AVAILABLE:
        # Fallback to basic regex validation if phonenumbers not installed
        pattern = r'^[+]?[0-9\s\-\(\)]{8,}$'
        if not re.match(pattern, phone_number):
            raise ValidationError(
                _("Invalid phone number format."),
                code='invalid_phone',
            )
        return {
            'valid': True,
            'formatted': phone_number,
            'national': phone_number,
            'country_code': country_code or 'UNKNOWN',
            'error': None
        }

    try:
        # Parse the phone number
        parsed = phonenumbers.parse(phone_number, country_code)

        # Validate the number
        if not phonenumbers.is_valid_number(parsed):
            raise ValidationError(
                _("This phone number is not valid for the selected country."),
                code='invalid_phone',
            )

        # Get formatted versions
        international_format = phonenumbers.format_number(
            parsed,
            phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
        national_format = phonenumbers.format_number(
            parsed,
            phonenumbers.PhoneNumberFormat.NATIONAL
        )
        detected_country = phonenumbers.region_code_for_number(parsed)

        return {
            'valid': True,
            'formatted': international_format,
            'national': national_format,
            'country_code': detected_country,
            'error': None
        }

    except NumberParseException as e:
        error_messages = {
            NumberParseException.INVALID_COUNTRY_CODE: _(
                "Invalid country code."
            ),
            NumberParseException.NOT_A_NUMBER: _(
                "This is not a valid phone number."
            ),
            NumberParseException.TOO_SHORT_NSN: _(
                "Phone number is too short."
            ),
            NumberParseException.TOO_SHORT_AFTER_IDD: _(
                "Phone number is too short after international prefix."
            ),
            NumberParseException.TOO_LONG: _(
                "Phone number is too long."
            ),
        }

        error_msg = error_messages.get(
            e.error_type,
            _("Invalid phone number format.")
        )

        raise ValidationError(error_msg, code='invalid_phone')
    except Exception as e:
        raise ValidationError(
            _("Error validating phone number: {}").format(str(e)),
            code='phone_validation_error',
        )


class PhoneNumberValidator:
    """
    Django model field validator for phone numbers.

    Usage:
        phone = models.CharField(
            max_length=20,
            validators=[PhoneNumberValidator(country_code='CA')]
        )
    """

    def __init__(self, country_code=None):
        self.country_code = country_code

    def __call__(self, value):
        validate_phone_number(value, self.country_code)

    def __eq__(self, other):
        return (
            isinstance(other, PhoneNumberValidator) and
            self.country_code == other.country_code
        )
