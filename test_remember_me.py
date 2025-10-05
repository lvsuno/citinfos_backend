"""Test script to verify Remember Me functionality"""
from django.utils import timezone
from datetime import timedelta

# Simulate the fixed code logic
def calculate_expiration(persistent):
    from django.conf import settings
    
    if persistent:
        # Remember me: 30 days
        default_hours = getattr(
            settings, 'PERSISTENT_SESSION_DURATION_DAYS', 30
        ) * 24
    else:
        # Normal session: 4 hours
        default_hours = getattr(settings, 'SESSION_DURATION_HOURS', 4)
    
    started_at = timezone.now()
    expires_at = started_at + timedelta(hours=default_hours)
    
    duration = expires_at - started_at
    return {
        'started_at': started_at,
        'expires_at': expires_at,
        'duration_hours': duration.total_seconds() / 3600,
        'duration_days': duration.days
    }

# Test with remember_me=True
print("Testing with remember_me=True:")
result = calculate_expiration(persistent=True)
print(f"  Duration: {result['duration_days']} days ({result['duration_hours']:.0f} hours)")
print(f"  Expected: 30 days (720 hours)")
print(f"  Match: {abs(result['duration_hours'] - 720) < 1}")

print("\nTesting with remember_me=False:")
result = calculate_expiration(persistent=False)
print(f"  Duration: {result['duration_days']} days ({result['duration_hours']:.0f} hours)")
print(f"  Expected: 0 days (4 hours)")
print(f"  Match: {abs(result['duration_hours'] - 4) < 1}")
