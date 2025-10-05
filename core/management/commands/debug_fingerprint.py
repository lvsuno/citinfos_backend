"""
Django management command to debug fingerprint session recovery
"""
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from core.device_fingerprint import OptimizedDeviceFingerprint
from core.session_manager import session_manager
from accounts.models import UserSession
import json


class Command(BaseCommand):
    help = 'Debug fingerprint generation and session recovery'

    def handle(self, *args, **options):
        self.stdout.write("🔍 DEBUGGING FINGERPRINT SESSION RECOVERY")
        self.stdout.write("=" * 60)

        # Create a mock request similar to your browser
        factory = RequestFactory()
        request = factory.get('/')

        # Set typical browser headers (like your browser would send)
        request.META.update({
            'HTTP_USER_AGENT': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                               'AppleWebKit/537.36 (KHTML, like Gecko) '
                               'Chrome/119.0.0.0 Safari/537.36'),
            'HTTP_ACCEPT': ('text/html,application/xhtml+xml,application/xml;'
                           'q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'),
            'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.9',
            'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br',
            'REMOTE_ADDR': '127.0.0.1'
        })

        # Generate fast fingerprint
        fast_fingerprint = OptimizedDeviceFingerprint.get_fast_fingerprint(request)
        self.stdout.write(f"🔑 Generated Fast Fingerprint: {fast_fingerprint}")
        self.stdout.write(f"🔑 Fingerprint Length: {len(fast_fingerprint)}")

        # Check what components are being used
        self.stdout.write("\n📋 FINGERPRINT COMPONENTS:")
        self.stdout.write("-" * 30)
        ua = request.META.get('HTTP_USER_AGENT', '')
        accept = request.META.get('HTTP_ACCEPT', '')
        accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')

        browser_family = OptimizedDeviceFingerprint._fast_browser_detection(ua)
        os_family = OptimizedDeviceFingerprint._fast_os_detection(ua)

        components = [ua, accept, accept_lang, accept_encoding, browser_family, os_family]

        for i, component in enumerate(components):
            self.stdout.write(f"{i+1}. {component}")

        # Show how the fingerprint is generated
        fingerprint_str = '|'.join(str(comp) for comp in components)
        self.stdout.write(f"\n🔗 Combined String: {fingerprint_str[:100]}...")

        # Look for existing sessions
        self.stdout.write("\n🔍 SEARCHING FOR EXISTING SESSIONS:")
        self.stdout.write("-" * 50)

        # Check Redis first
        self.stdout.write("📡 Checking Redis...")
        if session_manager.use_redis:
            try:
                session_keys = session_manager.redis_client.keys('session:*')
                self.stdout.write(f"Found {len(session_keys)} session keys in Redis")

                matches = []
                for key in session_keys[:10]:  # Check first 10 sessions
                    try:
                        session_data_str = session_manager.redis_client.get(key)
                        if session_data_str:
                            session_data = json.loads(session_data_str)
                            stored_fp = session_data.get('device_fingerprint', '')
                            stored_fast_fp = session_data.get('fast_fingerprint', '')

                            self.stdout.write(f"  Session {key.decode()[-8:]}...")
                            self.stdout.write(f"    Stored FP: {stored_fp[:32]}...")
                            self.stdout.write(f"    Fast FP:   {stored_fast_fp[:32]}...")
                            match = (stored_fp == fast_fingerprint or
                                   stored_fast_fp == fast_fingerprint)
                            self.stdout.write(f"    Match: {match}")
                            self.stdout.write(f"    Active: {session_data.get('is_active', False)}")

                            if match:
                                matches.append(session_data)
                    except Exception as e:
                        self.stdout.write(f"    Error reading session: {e}")

                if matches:
                    self.stdout.write(f"✅ Found {len(matches)} matching sessions in Redis!")
                    for match in matches:
                        self.stdout.write(f"   User ID: {match.get('user_id')}")
                        self.stdout.write(f"   Active: {match.get('is_active')}")
                else:
                    self.stdout.write("❌ No matching sessions found in Redis")

            except Exception as e:
                self.stdout.write(f"❌ Redis error: {e}")

        # Check database
        self.stdout.write("\n💾 Checking Database...")
        db_sessions = UserSession.objects.filter(
            device_fingerprint=fast_fingerprint,
            is_active=True
        )
        self.stdout.write(f"Found {db_sessions.count()} matching active sessions in DB")

        for session in db_sessions[:5]:  # Show first 5
            self.stdout.write(f"  Session ID: {session.session_id[:16]}...")
            user_name = session.user.user.username if session.user else 'None'
            self.stdout.write(f"  User: {user_name}")
            self.stdout.write(f"  Started: {session.started_at}")
            self.stdout.write(f"  Expires: {session.expires_at}")
            self.stdout.write(f"  Active: {session.is_active}")

        # Test the actual lookup function
        self.stdout.write("\n🎯 TESTING SESSION LOOKUP FUNCTION:")
        self.stdout.write("-" * 40)
        found_session = session_manager.find_any_active_session_by_fingerprint(
            fast_fingerprint
        )

        if found_session:
            self.stdout.write("✅ Session found by lookup function!")
            session_id = found_session.get('session_id', 'Unknown')
            self.stdout.write(f"   Session ID: {session_id}")
            user_profile = found_session.get('user_profile')
            if user_profile:
                self.stdout.write(f"   User: {user_profile.user.username}")
        else:
            self.stdout.write("❌ No session found by lookup function")

        # Show all sessions for debugging
        self.stdout.write(f"\n📋 ALL ACTIVE SESSIONS (for reference):")
        self.stdout.write("-" * 40)
        all_sessions = UserSession.objects.filter(is_active=True)[:10]
        for session in all_sessions:
            user_name = session.user.user.username if session.user else 'None'
            self.stdout.write(f"  {session.session_id[:16]}... | {user_name} | "
                            f"FP: {session.device_fingerprint[:16]}...")

        self.stdout.write(f"\n🔍 RECOMMENDATIONS:")
        self.stdout.write("-" * 30)
        if not matches and db_sessions.count() == 0:
            self.stdout.write("1. No sessions exist - you need to log in first")
            self.stdout.write("2. Check if your login actually created a session")
            self.stdout.write("3. Verify Redis is running and accessible")
        else:
            self.stdout.write("1. Sessions exist! Check middleware logs")
            self.stdout.write("2. Enable debug logging in OptimizedAuthenticationMiddleware")
            self.stdout.write("3. Verify fingerprint consistency between login and recovery")