"""
Django management command to reverse-engineer what headers created a stored fingerprint
"""
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from core.device_fingerprint import OptimizedDeviceFingerprint
import hashlib


class Command(BaseCommand):
    help = 'Try to reverse-engineer what headers created a specific fingerprint'

    def add_arguments(self, parser):
        parser.add_argument('--target-fingerprint', type=str, required=True,
                          help='The fingerprint to reverse-engineer')

    def handle(self, *args, **options):
        target_fingerprint = options['target_fingerprint']
        self.stdout.write(f"🔍 REVERSE ENGINEERING FINGERPRINT: {target_fingerprint}")
        self.stdout.write("=" * 80)

        # Try common variations of Firefox headers
        firefox_variations = [
            # Current Firefox
            {
                'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:143.0) Gecko/20100101 Firefox/143.0',
                'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'HTTP_ACCEPT_LANGUAGE': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
                'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br, zstd',
            },
            # Older Firefox versions
            {
                'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:142.0) Gecko/20100101 Firefox/142.0',
                'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'HTTP_ACCEPT_LANGUAGE': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
                'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br, zstd',
            },
            {
                'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0',
                'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'HTTP_ACCEPT_LANGUAGE': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
                'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br, zstd',
            },
            # Different language preferences
            {
                'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:143.0) Gecko/20100101 Firefox/143.0',
                'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.9,fr;q=0.8',
                'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br, zstd',
            },
            {
                'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:143.0) Gecko/20100101 Firefox/143.0',
                'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.5',
                'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br, zstd',
            },
            # Different Accept-Encoding (without zstd)
            {
                'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:143.0) Gecko/20100101 Firefox/143.0',
                'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'HTTP_ACCEPT_LANGUAGE': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
                'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br',
            },
            # Chrome-like (maybe you used Chrome when logging in?)
            {
                'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.9',
                'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br',
            },
            {
                'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'HTTP_ACCEPT_LANGUAGE': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
                'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br',
            },
        ]

        factory = RequestFactory()

        for i, headers in enumerate(firefox_variations):
            request = factory.get('/')
            request.META.update(headers)
            request.META['REMOTE_ADDR'] = '127.0.0.1'

            # Generate fingerprint
            fingerprint = OptimizedDeviceFingerprint.get_fast_fingerprint(request)

            self.stdout.write(f"\n🔍 Test #{i+1}:")
            self.stdout.write(f"  User-Agent: {headers.get('HTTP_USER_AGENT', 'N/A')[:60]}...")
            self.stdout.write(f"  Accept-Lang: {headers.get('HTTP_ACCEPT_LANGUAGE', 'N/A')}")
            self.stdout.write(f"  Accept-Enc: {headers.get('HTTP_ACCEPT_ENCODING', 'N/A')}")
            self.stdout.write(f"  Generated FP: {fingerprint}")

            if fingerprint == target_fingerprint:
                self.stdout.write("  ✅ MATCH FOUND!")
                self.stdout.write(f"  🎯 These headers generated the target fingerprint:")
                for key, value in headers.items():
                    self.stdout.write(f"     {key}: {value}")

                # Show the components
                ua = headers.get('HTTP_USER_AGENT', '')
                accept = headers.get('HTTP_ACCEPT', '')
                accept_lang = headers.get('HTTP_ACCEPT_LANGUAGE', '')
                accept_encoding = headers.get('HTTP_ACCEPT_ENCODING', '')

                browser_family = OptimizedDeviceFingerprint._fast_browser_detection(ua)
                os_family = OptimizedDeviceFingerprint._fast_os_detection(ua)

                components = [ua, accept, accept_lang, accept_encoding, browser_family, os_family]
                fingerprint_str = '|'.join(str(comp) for comp in components)

                self.stdout.write(f"\n  📋 Fingerprint components:")
                for j, comp in enumerate(components):
                    self.stdout.write(f"     {j+1}. {comp}")
                self.stdout.write(f"\n  🔗 Combined: {fingerprint_str[:100]}...")
                return
            else:
                self.stdout.write(f"  ❌ No match")

        self.stdout.write(f"\n❌ No match found among {len(firefox_variations)} variations")
        self.stdout.write("💡 The fingerprint was likely created with different headers")
        self.stdout.write("💡 Try updating your login to create a new session with current headers")