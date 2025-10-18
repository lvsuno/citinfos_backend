#!/usr/bin/env python
"""
Test script to check if verification headers are being set correctly.
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from accounts.middleware import UpdateLastActiveMiddleware

User = get_user_model()

def test_verification_headers():
    """Test that verification headers are added to responses."""

    print("\n" + "="*60)
    print("TESTING VERIFICATION HEADERS")
    print("="*60 + "\n")

    # Get user
    try:
        user = User.objects.get(username='elvist')
    except User.DoesNotExist:
        print("❌ User 'elvist' not found")
        return False

    # Create request factory
    factory = RequestFactory()

    # Create a GET request
    request = factory.get('/api/test/')
    request.user = user

    # Create middleware instance
    middleware = UpdateLastActiveMiddleware(lambda req: type('Response', (), {
        'status_code': 200,
        '__setitem__': lambda self, k, v: print(f"   Setting header: {k} = {v}"),
        '__getitem__': lambda self, k: None,
    })())

    # Process request
    print("📝 Processing request in middleware...")
    response = middleware.process_request(request)

    if response:
        print(f"\n⚠️  Middleware returned a response (blocking request)")
        print(f"   Status: {response.status_code}")
        print(f"   Content: {response.content.decode()}")
    else:
        print("\n✅ Request allowed to proceed")
        print(f"   _verification_expired flag: {getattr(request, '_verification_expired', False)}")

        # Create a mock response
        class MockResponse:
            def __init__(self):
                self.headers = {}
                self.status_code = 200

            def __setitem__(self, key, value):
                self.headers[key] = value
                print(f"   Setting header: {key} = {value}")

            def __getitem__(self, key):
                return self.headers.get(key)

        mock_response = MockResponse()

        # Process response
        print("\n📝 Processing response in middleware...")
        final_response = middleware.process_response(request, mock_response)

        print(f"\n✅ Response headers:")
        for key, value in final_response.headers.items():
            print(f"   {key}: {value}")

    print("\n" + "="*60 + "\n")

    return True


if __name__ == "__main__":
    success = test_verification_headers()
    sys.exit(0 if success else 1)
