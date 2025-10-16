#!/usr/bin/env python

"""Test script to check admin endpoints"""

import os
import sys
import django

# Setup Django environment
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
    django.setup()

    from django.urls import reverse
    from django.test import Client
    from django.contrib.auth.models import User
    from accounts.models import UserProfile
    
    # Test URLs resolution
    try:
        print("=== Testing URL Resolution ===")
        from django.urls import resolve
        
        # Test if admin URLs are accessible
        print("Testing /api/admin/users/ resolution...")
        resolved = resolve('/api/admin/users/')
        print(f"✅ Resolved to: {resolved.func} (namespace: {resolved.namespace})")
        
    except Exception as e:
        print(f"❌ URL resolution failed: {e}")
    
    # Test ViewSet import
    try:
        print("\n=== Testing ViewSet Import ===")
        from accounts.admin_views import AdminUserListViewSet
        print("✅ AdminUserListViewSet imported successfully")
        
        # Check if queryset works
        viewset = AdminUserListViewSet()
        queryset = viewset.get_queryset()
        print(f"✅ Queryset works, found {queryset.count()} user profiles")
        
    except Exception as e:
        print(f"❌ ViewSet import/usage failed: {e}")
    
    # Test admin user
    try:
        print("\n=== Testing Admin User ===")
        admin_user = User.objects.get(username='admin')
        print(f"✅ Admin user found: {admin_user.username}")
        
        if hasattr(admin_user, 'profile'):
            print(f"✅ Admin profile found, role: {admin_user.profile.role}")
        else:
            print("❌ No profile found for admin user")
            
    except User.DoesNotExist:
        print("❌ Admin user not found")
    except Exception as e:
        print(f"❌ Error checking admin user: {e}")
    
    print("\n=== Test completed ===")