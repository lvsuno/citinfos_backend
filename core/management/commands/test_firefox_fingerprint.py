"""
Django management command to test Firefox fingerprint matching
"""
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from core.device_fingerprint import OptimizedDeviceFingerprint
from core.session_manager import session_manager


class Command(BaseCommand):
    help = 'Test Firefox fingerprint generation to match existing session'

    def handle(self, *args, **options):
        self.stdout.write("🦊 TESTING FIREFOX FINGERPRINT MATCHING")
        self.stdout.write("=" * 60)

        # Your existing session fingerprint
        existing_fingerprint = "313152fabf2a8dc78caec60b0acbe771"
        self.stdout.write(f"🎯 Target fingerprint: {existing_fingerprint}...")

        factory = RequestFactory()

        # Test various Firefox configurations
        firefox_configs = [
            {
                'name': 'Firefox macOS (latest)',
                'headers': {
                    'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15) Gecko/20100101 Firefox/119.0',
                    'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.5',
                    'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br',
                }
            },
            {
                'name': 'Firefox macOS (older)',
                'headers': {
                    'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15) Gecko/20100101 Firefox/118.0',
                    'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.5',
                    'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br',
                }
            },
            {
                'name': 'Firefox macOS (different accept)',
                'headers': {
                    'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15) Gecko/20100101 Firefox/119.0',
                    'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.5',
                    'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br',
                }
            },
            {
                'name': 'Firefox macOS (API request)',
                'headers': {
                    'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15) Gecko/20100101 Firefox/119.0',
                    'HTTP_ACCEPT': 'application/json, text/plain, */*',
                    'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.5',
                    'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br',
                }
            },
            {
                'name': 'Firefox macOS 10_15_7',
                'headers': {
                    'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Gecko/20100101 Firefox/119.0',
                    'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.5',
                    'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br',
                }
            },
        ]

        for config in firefox_configs:
            request = factory.get('/')
            request.META.update(config['headers'])

            fingerprint = OptimizedDeviceFingerprint.get_fast_fingerprint(request)

            self.stdout.write(f"\n🦊 {config['name']}:")
            self.stdout.write(f"   Generated: {fingerprint}")

            # Check if this matches your session
            if fingerprint.startswith(existing_fingerprint):
                self.stdout.write("   ✅ PARTIAL MATCH!")
            elif fingerprint == existing_fingerprint:
                self.stdout.write("   🎯 EXACT MATCH!")
            else:
                self.stdout.write("   ❌ No match")

            # Test session lookup
            found_session = session_manager.find_any_active_session_by_fingerprint(fingerprint)
            if found_session:
                user_profile = found_session.get('user_profile')
                user_name = user_profile.user.username if user_profile else 'Unknown'
                self.stdout.write(f"   🔍 Found session for: {user_name}")

            # Show fingerprint components for debugging
            self.stdout.write("   Components:")
            ua = config['headers']['HTTP_USER_AGENT']
            accept = config['headers']['HTTP_ACCEPT']
            accept_lang = config['headers']['HTTP_ACCEPT_LANGUAGE']
            accept_encoding = config['headers']['HTTP_ACCEPT_ENCODING']

            browser = OptimizedDeviceFingerprint._fast_browser_detection(ua)
            os_family = OptimizedDeviceFingerprint._fast_os_detection(ua)

            self.stdout.write(f"     Browser: {browser}")
            self.stdout.write(f"     OS: {os_family}")
            self.stdout.write(f"     UA: {ua[:50]}...")
            self.stdout.write(f"     Accept: {accept[:50]}...")

        # Test with the exact session lookup to verify it works
        self.stdout.write(f"\n🔍 TESTING ACTUAL SESSION LOOKUP:")
        self.stdout.write("-" * 45)

        # Get the full fingerprint from your session
        from accounts.models import UserSession
        session = UserSession.objects.filter(user__user__username='elvist', is_active=True).first()
        if session:
            session_fast_fp = getattr(session, 'fast_fingerprint', None)
            if session_fast_fp:
                self.stdout.write(f"Session fast_fingerprint: {session_fast_fp}")

                # Test lookup with actual fingerprint
                found = session_manager.find_any_active_session_by_fingerprint(session_fast_fp)
                if found:
                    self.stdout.write("✅ Session lookup works with stored fast_fingerprint!")
                else:
                    self.stdout.write("❌ Session lookup fails even with stored fast_fingerprint")
            else:
                self.stdout.write("❌ Session has no fast_fingerprint field")
        else:
            self.stdout.write("❌ No active session found for user elvist")

        self.stdout.write(f"\n💡 NEXT STEPS:")
        self.stdout.write("-" * 20)
        self.stdout.write("1. Open Firefox Developer Tools (F12)")
        self.stdout.write("2. Go to Network tab")
        self.stdout.write("3. Make a request to your API")
        self.stdout.write("4. Check the exact request headers")
        self.stdout.write("5. Compare with the fingerprint components above")