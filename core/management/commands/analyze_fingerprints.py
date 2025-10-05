"""
Django management command to capture real browser fingerprint
"""
from django.core.management.base import BaseCommand
from core.device_fingerprint import OptimizedDeviceFingerprint
from core.session_manager import session_manager
from accounts.models import UserSession
import json


class Command(BaseCommand):
    help = 'Capture and analyze real browser fingerprint from middleware logs'

    def handle(self, *args, **options):
        self.stdout.write("🔍 ANALYZING REAL BROWSER FINGERPRINTS")
        self.stdout.write("=" * 60)

        # Check all active sessions and their fingerprints
        self.stdout.write("📋 EXISTING ACTIVE SESSIONS:")
        self.stdout.write("-" * 40)

        active_sessions = UserSession.objects.filter(is_active=True)
        self.stdout.write(f"Found {active_sessions.count()} active sessions")

        for session in active_sessions:
            user_name = session.user.user.username if session.user else 'None'
            self.stdout.write(f"\n🔑 Session: {session.session_id[:16]}...")
            self.stdout.write(f"   User: {user_name}")
            self.stdout.write(f"   Device FP: {session.device_fingerprint}")
            self.stdout.write(f"   Started: {session.started_at}")
            self.stdout.write(f"   User Agent: {session.user_agent[:100]}...")
            self.stdout.write(f"   IP: {session.ip_address}")

        # Check Redis sessions
        self.stdout.write(f"\n📡 REDIS SESSIONS:")
        self.stdout.write("-" * 40)

        if session_manager.use_redis:
            try:
                session_keys = session_manager.redis_client.keys('session:*')
                self.stdout.write(f"Found {len(session_keys)} session keys in Redis")

                for key in session_keys:
                    try:
                        session_data_str = session_manager.redis_client.get(key)
                        if session_data_str:
                            # Try different decodings
                            try:
                                session_data = json.loads(session_data_str.decode('utf-8'))
                                redis_good = True
                            except UnicodeDecodeError:
                                try:
                                    session_data = json.loads(session_data_str)
                                    redis_good = True
                                except:
                                    redis_good = False
                                    self.stdout.write(f"❌ Could not decode Redis session {key.decode()}")
                                    continue

                            if redis_good:
                                self.stdout.write(f"\n📦 Redis Session: {key.decode()[-16:]}...")
                                self.stdout.write(f"   User ID: {session_data.get('user_id')}")
                                self.stdout.write(f"   Device FP: {session_data.get('device_fingerprint', 'N/A')}")
                                self.stdout.write(f"   Fast FP: {session_data.get('fast_fingerprint', 'N/A')}")
                                self.stdout.write(f"   Active: {session_data.get('is_active')}")
                                self.stdout.write(f"   User Agent: {session_data.get('user_agent', 'N/A')[:100]}...")

                    except Exception as e:
                        self.stdout.write(f"❌ Error reading Redis session {key}: {e}")

            except Exception as e:
                self.stdout.write(f"❌ Redis connection error: {e}")

        # Instructions
        self.stdout.write(f"\n💡 NEXT STEPS TO FIX YOUR ISSUE:")
        self.stdout.write("-" * 50)
        self.stdout.write("1. 🔐 Log in again to create a fresh session")
        self.stdout.write("2. 🖥️ Make a request from your browser")
        self.stdout.write("3. 📊 Check middleware logs for fingerprint generation")
        self.stdout.write("4. 🔍 Compare fingerprints between login and recovery")

        self.stdout.write(f"\n🛠️ TO ENABLE DEBUG LOGGING:")
        self.stdout.write("-" * 35)
        self.stdout.write("Add this to your settings.py:")
        self.stdout.write("LOGGING = {")
        self.stdout.write("    'loggers': {")
        self.stdout.write("        'core.middleware.optimized_auth_middleware': {")
        self.stdout.write("            'level': 'DEBUG',")
        self.stdout.write("        },")
        self.stdout.write("    }")
        self.stdout.write("}")

        # Clear corrupted Redis sessions
        if session_manager.use_redis:
            self.stdout.write(f"\n🧹 CLEANING CORRUPTED REDIS SESSIONS:")
            self.stdout.write("-" * 45)
            try:
                session_keys = session_manager.redis_client.keys('session:*')
                cleaned = 0
                for key in session_keys:
                    try:
                        session_data_str = session_manager.redis_client.get(key)
                        if session_data_str:
                            try:
                                json.loads(session_data_str.decode('utf-8'))
                            except:
                                try:
                                    json.loads(session_data_str)
                                except:
                                    # Corrupted session, delete it
                                    session_manager.redis_client.delete(key)
                                    cleaned += 1
                                    self.stdout.write(f"🗑️ Cleaned corrupted session: {key.decode()}")
                    except Exception as e:
                        self.stdout.write(f"Error processing {key}: {e}")

                self.stdout.write(f"✅ Cleaned {cleaned} corrupted sessions")

            except Exception as e:
                self.stdout.write(f"❌ Error cleaning Redis: {e}")