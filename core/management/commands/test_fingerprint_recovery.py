"""
Django management command to test fingerprint session recovery with real data
"""
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from core.device_fingerprint import OptimizedDeviceFingerprint
from core.session_manager import session_manager
from accounts.models import UserSession
import json


class Command(BaseCommand):
    help = 'Test fingerprint generation and recovery with real session data'

    def add_arguments(self, parser):
        parser.add_argument('--clean', action='store_true', help='Clean corrupted Redis sessions')

    def handle(self, *args, **options):
        if options['clean']:
            self.clean_redis_sessions()
            return

        self.stdout.write("🔍 TESTING FINGERPRINT SESSION RECOVERY")
        self.stdout.write("=" * 60)

        # Show current sessions with their fingerprints
        self.show_existing_sessions()

        # Test fingerprint generation with various headers
        self.test_fingerprint_variations()

        # Instructions for manual testing
        self.stdout.write(f"\n💡 MANUAL TESTING INSTRUCTIONS:")
        self.stdout.write("-" * 40)
        self.stdout.write("1. Login to your app in browser")
        self.stdout.write("2. Check browser developer tools -> Network tab")
        self.stdout.write("3. Look at request headers for any API call")
        self.stdout.write("4. Note the exact User-Agent, Accept, Accept-Language, Accept-Encoding")
        self.stdout.write("5. Run: docker compose exec backend python manage.py test_real_headers")

    def clean_redis_sessions(self):
        """Clean corrupted Redis sessions"""
        self.stdout.write("🧹 CLEANING CORRUPTED REDIS SESSIONS...")

        if not session_manager.use_redis:
            self.stdout.write("❌ Redis not available")
            return

        try:
            session_keys = session_manager.redis_client.keys('session:*')
            cleaned = 0

            for key in session_keys:
                try:
                    session_data_str = session_manager.redis_client.get(key)
                    if session_data_str:
                        # Test if we can decode the session
                        try:
                            if isinstance(session_data_str, bytes):
                                json.loads(session_data_str.decode('utf-8'))
                            else:
                                json.loads(session_data_str)
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            # Corrupted session, delete it
                            session_manager.redis_client.delete(key)
                            cleaned += 1
                            self.stdout.write(f"🗑️ Cleaned: {key.decode()}")
                except Exception as e:
                    self.stdout.write(f"Error processing {key}: {e}")

            self.stdout.write(f"✅ Cleaned {cleaned} corrupted sessions")

        except Exception as e:
            self.stdout.write(f"❌ Error accessing Redis: {e}")

    def show_existing_sessions(self):
        """Show existing sessions and their fingerprints"""
        self.stdout.write("📋 EXISTING SESSIONS:")
        self.stdout.write("-" * 30)

        # Database sessions
        db_sessions = UserSession.objects.filter(is_active=True)
        self.stdout.write(f"Database: {db_sessions.count()} active sessions")

        for session in db_sessions:
            user_name = session.user.user.username if session.user else 'None'
            self.stdout.write(f"  👤 {user_name}")
            self.stdout.write(f"     Session ID: {session.session_id[:16]}...")
            self.stdout.write(f"     Device FP:  {session.device_fingerprint[:32]}...")
            self.stdout.write(f"     Fast FP:    {getattr(session, 'fast_fingerprint', 'N/A')}")
            self.stdout.write("")

        # Redis sessions
        if session_manager.use_redis:
            try:
                session_keys = session_manager.redis_client.keys('session:*')
                self.stdout.write(f"Redis: {len(session_keys)} sessions")

                valid_sessions = 0
                for key in session_keys:
                    try:
                        session_data_str = session_manager.redis_client.get(key)
                        if session_data_str:
                            try:
                                if isinstance(session_data_str, bytes):
                                    session_data = json.loads(session_data_str.decode('utf-8'))
                                else:
                                    session_data = json.loads(session_data_str)

                                valid_sessions += 1
                                if session_data.get('is_active'):
                                    user_name = session_data.get('user_username', 'Unknown')
                                    self.stdout.write(f"  📡 {user_name} (Redis)")
                                    self.stdout.write(f"     Session ID: {session_data.get('session_id', 'N/A')[:16]}...")
                                    self.stdout.write(f"     Device FP:  {session_data.get('device_fingerprint', 'N/A')[:32]}...")
                                    self.stdout.write(f"     Fast FP:    {session_data.get('fast_fingerprint', 'N/A')[:32]}...")
                                    self.stdout.write("")

                            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                                self.stdout.write(f"  ❌ Corrupted session: {key.decode()[-16:]}... ({e})")

                    except Exception as e:
                        self.stdout.write(f"  ❌ Error reading session: {e}")

                self.stdout.write(f"Valid Redis sessions: {valid_sessions}")

            except Exception as e:
                self.stdout.write(f"❌ Redis error: {e}")

    def test_fingerprint_variations(self):
        """Test fingerprint generation with different header combinations"""
        self.stdout.write(f"\n🧪 TESTING FINGERPRINT VARIATIONS:")
        self.stdout.write("-" * 45)

        factory = RequestFactory()

        # Test cases with different headers
        test_cases = [
            {
                'name': 'Chrome macOS (typical)',
                'headers': {
                    'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.9',
                    'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br',
                }
            },
            {
                'name': 'Chrome macOS (different version)',
                'headers': {
                    'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.9',
                    'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br',
                }
            },
            {
                'name': 'API Request (JSON)',
                'headers': {
                    'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    'HTTP_ACCEPT': 'application/json, text/plain, */*',
                    'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.9',
                    'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br',
                }
            }
        ]

        for test_case in test_cases:
            request = factory.get('/')
            request.META.update(test_case['headers'])

            fingerprint = OptimizedDeviceFingerprint.get_fast_fingerprint(request)

            self.stdout.write(f"\n📱 {test_case['name']}:")
            self.stdout.write(f"   Fingerprint: {fingerprint}")

            # Check if this matches any existing session
            found_session = session_manager.find_any_active_session_by_fingerprint(fingerprint)
            if found_session:
                user_profile = found_session.get('user_profile')
                user_name = user_profile.user.username if user_profile else 'Unknown'
                self.stdout.write(f"   ✅ MATCH! Found session for {user_name}")
            else:
                self.stdout.write("   ❌ No matching session")