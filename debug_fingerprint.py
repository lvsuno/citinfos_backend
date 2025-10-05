"""
Debug script to test device fingerprinting and session recovery
Run this to understand why your session isn't being found
"""

# Add this to your Django shell or create a management command

def debug_fingerprint_session_recovery():
    """
    Debug fingerprint generation and session lookup
    """
    from django.test import RequestFactory
    from core.device_fingerprint import OptimizedDeviceFingerprint
    from core.session_manager import session_manager
    from accounts.models import UserSession
    import json

    print("🔍 DEBUGGING FINGERPRINT SESSION RECOVERY")
    print("=" * 60)

    # Create a mock request similar to your browser
    factory = RequestFactory()
    request = factory.get('/')

    # Set typical browser headers
    request.META.update({
        'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.9',
        'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br',
        'REMOTE_ADDR': '127.0.0.1'  # Local IP for testing
    })

    # Generate fast fingerprint
    fast_fingerprint = OptimizedDeviceFingerprint.get_fast_fingerprint(request)
    print(f"🔑 Generated Fast Fingerprint: {fast_fingerprint}")
    print(f"🔑 Fingerprint Length: {len(fast_fingerprint)}")

    # Check what components are being used
    print("\n📋 FINGERPRINT COMPONENTS:")
    print("-" * 30)
    ua = request.META.get('HTTP_USER_AGENT', '')
    accept = request.META.get('HTTP_ACCEPT', '')
    accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')

    browser_family = OptimizedDeviceFingerprint._fast_browser_detection(ua)
    os_family = OptimizedDeviceFingerprint._fast_os_detection(ua)

    components = [ua, accept, accept_lang, accept_encoding, browser_family, os_family]

    for i, component in enumerate(components):
        print(f"{i+1}. {component}")

    # Show how the fingerprint is generated
    fingerprint_str = '|'.join(str(comp) for comp in components)
    print(f"\n🔗 Combined String: {fingerprint_str[:100]}...")

    # Look for sessions with this fingerprint
    print(f"\n🔍 SEARCHING FOR SESSIONS WITH FINGERPRINT:")
    print("-" * 50)

    # Check Redis first
    print("📡 Checking Redis...")
    if session_manager.use_redis:
        try:
            session_keys = session_manager.redis_client.keys('session:*')
            print(f"Found {len(session_keys)} session keys in Redis")

            matches = []
            for key in session_keys[:10]:  # Check first 10 sessions
                try:
                    session_data_str = session_manager.redis_client.get(key)
                    if session_data_str:
                        session_data = json.loads(session_data_str)
                        stored_fp = session_data.get('device_fingerprint', '')
                        stored_fast_fp = session_data.get('fast_fingerprint', '')

                        print(f"  Session {key.decode()[-8:]}...")
                        print(f"    Stored FP: {stored_fp[:32]}...")
                        print(f"    Fast FP:   {stored_fast_fp[:32]}...")
                        print(f"    Match: {stored_fp == fast_fingerprint or stored_fast_fp == fast_fingerprint}")
                        print(f"    Active: {session_data.get('is_active', False)}")

                        if stored_fp == fast_fingerprint or stored_fast_fp == fast_fingerprint:
                            matches.append(session_data)
                        print()
                except Exception as e:
                    print(f"    Error reading session: {e}")

            if matches:
                print(f"✅ Found {len(matches)} matching sessions in Redis!")
                for match in matches:
                    print(f"   User ID: {match.get('user_id')}")
                    print(f"   Active: {match.get('is_active')}")
            else:
                print("❌ No matching sessions found in Redis")

        except Exception as e:
            print(f"❌ Redis error: {e}")

    # Check database
    print(f"\n💾 Checking Database...")
    db_sessions = UserSession.objects.filter(
        device_fingerprint=fast_fingerprint,
        is_active=True
    )
    print(f"Found {db_sessions.count()} matching active sessions in DB")

    for session in db_sessions[:5]:  # Show first 5
        print(f"  Session ID: {session.session_id[:16]}...")
        print(f"  User: {session.user.user.username if session.user else 'None'}")
        print(f"  Started: {session.started_at}")
        print(f"  Expires: {session.expires_at}")
        print(f"  Active: {session.is_active}")
        print()

    # Test the actual lookup function
    print(f"\n🎯 TESTING SESSION LOOKUP FUNCTION:")
    print("-" * 40)
    found_session = session_manager.find_any_active_session_by_fingerprint(fast_fingerprint)

    if found_session:
        print("✅ Session found by lookup function!")
        print(f"   Session ID: {found_session.get('session_id', 'Unknown')}")
        print(f"   User: {found_session.get('user_profile', 'Unknown')}")
    else:
        print("❌ No session found by lookup function")

    print(f"\n🔍 RECOMMENDATION:")
    print("-" * 30)
    if not matches and db_sessions.count() == 0:
        print("1. No sessions exist - you need to log in first")
        print("2. Check if your login actually created a session")
        print("3. Verify Redis is running and accessible")
    elif matches or db_sessions.count() > 0:
        print("1. Sessions exist but lookup function failed")
        print("2. Check session_manager implementation")
        print("3. Verify Redis connection in session_manager")
    else:
        print("1. Fingerprint mismatch - headers may be different")
        print("2. Check browser headers between login and current request")
        print("3. Verify fingerprint generation is consistent")

if __name__ == '__main__':
    debug_fingerprint_session_recovery()