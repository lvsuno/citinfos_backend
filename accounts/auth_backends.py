"""
Authentication backend that checks verification expiry on login.
"""

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.models import UserProfile
from accounts.tasks import generate_verification_code_for_user
from django.contrib.auth import authenticate
from django.contrib.auth.backends import ModelBackend


def check_verification_expiry_on_login(user):
    """
    Utility function to check verification expiry.
    Can be called from any login view.
    """
    try:
        # Try to get the UserProfile, handle if it doesn't exist
        try:
            profile = user.profile
        except AttributeError:
            # User doesn't have a profile, needs verification
            return {
                'error': 'No profile found',
                'code': 'NO_PROFILE',
                'verification_required': True,
                'status': 'no_profile',
                'message': 'User profile not found',
                'action': 'create_profile',
                'user_id': profile.id,
                'verification_sent': False
            }


        # Check verification expiry
        if profile.last_verified_at:
            days_since = (timezone.now() - profile.last_verified_at).days
            if days_since > 7:
                # Mark as unverified and generate code
                profile.is_verified = False
                profile.save(update_fields=['is_verified'])
                generate_verification_code_for_user.delay(str(profile.id))

                return {
                    'error': 'Error: Verification expired',
                    'code': 'VERIFICATION_EXPIRED',
                    'verification_required': True,
                    'status': 'expired',
                    'message': 'User profile verification has expired',
                    'action': 'verify_account',
                    'user_id': profile.id,
                    'verification_sent': True
                }
        else:
            # If last_verified_at is null but user is marked as verified,
            # this is inconsistent data - require verification
            if profile.is_verified:
                profile.is_verified = False
                profile.save(update_fields=['is_verified'])
                generate_verification_code_for_user.delay(str(profile.id))

                return {
                    'status': 'missing_verification_timestamp',
                    'message': 'Verification timestamp missing, please verify your account',
                    'error': 'Error: Inconsistent data',
                    'code': 'INCONSISTENT_DATA',
                    'verification_required': True,
                    'action': 'verify_account',
                    'user_id': profile.id,
                    'verification_sent': True
                }
            else:
                generate_verification_code_for_user.delay(str(profile.id))
                return {
                    'status': 'not_verified',
                    'error': 'Error: User not verified',
                    'code': 'USER_NOT_VERIFIED',
                    'verification_required': True,
                    'message': 'User profile verification is required',
                    'action': 'verify_account',
                    'user_id': profile.id,
                    'verification_sent': True
                }

        return {
            'error': 'N/A',
            'code': 'VERIFICATION_ALREADY_VALID',
            'verification_required': False,
            'status': 'valid',
            'message': 'User profile verification is valid',
            'action': 'none',
            'user_id': profile.id,
            'verification_sent': False}

    except UserProfile.DoesNotExist:
        return {
                'error': 'No profile found',
                'code': 'NO_PROFILE',
                'verification_required': True,
                'status': 'no_profile',
                'message': 'User profile not found',
                'action': 'create_profile',
                'user_id': profile.id,
                'verification_sent': False
            }
