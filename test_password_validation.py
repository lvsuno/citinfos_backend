#!/usr/bin/env python
"""
Test script to verify password validation is enforced.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

print("=" * 70)
print("Testing Password Validation")
print("=" * 70)

# Create a test user
test_user = User(username='testuser', email='test@example.com')

# Test 1: Weak password (too short)
print("\n1. Testing weak password (too short): 'weak'")
try:
    validate_password('weak', user=test_user)
    print("   ❌ FAIL: Weak password was accepted!")
except ValidationError as e:
    print(f"   ✅ PASS: Password rejected - {e.messages[0]}")

# Test 2: Weak password (no uppercase)
print("\n2. Testing weak password (no uppercase): 'weakpass123'")
try:
    validate_password('weakpass123', user=test_user)
    print("   ❌ FAIL: Password without uppercase was accepted!")
except ValidationError as e:
    print(f"   ✅ PASS: Password rejected - {e.messages[0]}")

# Test 3: Weak password (no special char)
print("\n3. Testing weak password (no special char): 'WeakPass123'")
try:
    validate_password('WeakPass123', user=test_user)
    print("   ❌ FAIL: Password without special char was accepted!")
except ValidationError as e:
    print(f"   ✅ PASS: Password rejected - {e.messages[0]}")

# Test 4: Strong password (should pass)
print("\n4. Testing strong password: 'TestPass123!'")
try:
    validate_password('TestPass123!', user=test_user)
    print("   ✅ PASS: Strong password accepted!")
except ValidationError as e:
    print(f"   ❌ FAIL: Strong password rejected - {e.messages}")

# Test 5: Common password
print("\n5. Testing common password: 'Password123!'")
try:
    validate_password('Password123!', user=test_user)
    print("   ⚠️  WARNING: Common password might be accepted")
except ValidationError as e:
    print(f"   ✅ PASS: Common password rejected - {e.messages[0]}")

# Test 6: Password similar to username
print("\n6. Testing password similar to username: 'Testuser123!'")
try:
    validate_password('Testuser123!', user=test_user)
    print("   ⚠️  WARNING: Password similar to username might be accepted")
except ValidationError as e:
    print(f"   ✅ PASS: Similar password rejected - {e.messages[0]}")

print("\n" + "=" * 70)
print("Password Validation Tests Complete!")
print("=" * 70)
