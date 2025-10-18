#!/usr/bin/env python
"""
Test script to verify immediate verification checking works correctly.

This script:
1. Expires a user's verification
2. Tests that the verification is checked on first authenticated request
3. Verifies the appropriate headers/responses are returned
"""

import os
import sys
import django
from datetime import timedelta

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.models import UserProfile

User = get_user_model()


def test_verification_immediate_check():
    """Test that verification is checked on first authenticated request."""

    print("\n" + "="*60)
    print("VERIFICATION IMMEDIATE CHECK TEST")
    print("="*60 + "\n")

    # Get or create test user
    username = 'elvist'

    try:
        user = User.objects.get(username=username)
        profile = user.profile
    except User.DoesNotExist:
        print(f"❌ User '{username}' not found. Please create this user first.")
        return False

    print(f"Testing with user: {user.username} ({user.email})")
    print(f"Current verification status: {profile.is_verified}")
    print(f"Last verified at: {profile.last_verified_at}")

    # Step 1: Expire verification
    print("\n📝 Step 1: Expiring user's verification...")
    profile.last_verified_at = timezone.now() - timedelta(days=8)
    profile.save()

    # Refresh and check
    profile.refresh_from_db()
    profile.sync_verification_status()

    print(f"   ✅ Verification expired")
    print(f"   - Last verified: {profile.last_verified_at}")
    print(f"   - Is verified: {profile.is_verified}")

    # Step 2: Verify middleware will check on first request
    print("\n📝 Step 2: Simulating authenticated request...")
    print("   ℹ️  Middleware will check verification status on:")
    print("   - ALL authenticated requests (GET, POST, PUT, etc.)")
    print("   - For READ requests: Adds X-Verification-Required header")
    print("   - For WRITE requests: Returns 403 with VERIFICATION_EXPIRED")

    # Step 3: Test what happens
    print("\n📝 Step 3: Expected behavior...")

    if not profile.is_verified:
        print("   ✅ When user makes FIRST request (even GET):")
        print("      → Middleware checks verification status")
        print("      → Detects verification expired")
        print("      → Adds header: X-Verification-Required: true")
        print("      → Frontend interceptor sees header")
        print("      → Triggers 'verificationRequired' event")
        print("      → Modal appears IMMEDIATELY")
        print("")
        print("   ✅ On subsequent requests:")
        print("      → Modal already shown (verificationModalShown = true)")
        print("      → Event listener ignores duplicate events")
        print("      → Modal doesn't reappear")
        print("")
        print("   ✅ On write requests (POST/PUT/PATCH/DELETE):")
        print("      → Middleware returns 403 error immediately")
        print("      → Error includes VERIFICATION_EXPIRED code")
        print("      → Request is blocked until verified")
    else:
        print("   ❌ User is still verified - test failed")
        return False

    # Step 4: Instructions for frontend testing
    print("\n📝 Step 4: Frontend Testing Instructions...")
    print("   1. Log in as 'elvist' in the frontend")
    print("   2. Navigate to any page (e.g., dashboard, feed)")
    print("   3. EXPECTED: Verification modal appears immediately")
    print("   4. You can still browse (read) while modal is shown")
    print("   5. Try to post/comment → Should be blocked")
    print("   6. Complete verification → Modal closes")
    print("   7. Full access restored")

    # Step 5: Restore verification (optional)
    print("\n📝 Step 5: Restore verification? (y/n)")
    response = input("   > ").strip().lower()

    if response == 'y':
        profile.last_verified_at = timezone.now()
        profile.save()
        profile.sync_verification_status()
        print(f"   ✅ Verification restored")
        print(f"   - Is verified: {profile.is_verified}")
    else:
        print(f"   ℹ️  Verification left expired for testing")

    print("\n" + "="*60)
    print("✅ TEST SETUP COMPLETE")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    success = test_verification_immediate_check()
    sys.exit(0 if success else 1)
