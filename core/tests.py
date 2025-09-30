from .utils import get_client_ip, get_device_info
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from rest_framework.request import Request


class UtilsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_client_ip(self):
        """Test client IP extraction."""
        # Test with X-Forwarded-For
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.1,10.0.0.1'
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')

        # Test with REMOTE_ADDR
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        ip = get_client_ip(request)
        self.assertEqual(ip, '127.0.0.1')

    def test_get_device_info_fallback(self):
        """Test device info extraction with fallback parsing."""
        request = self.factory.get('/')
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'

        device_info = get_device_info(request)

        self.assertIn('browser', device_info)
        self.assertIn('os', device_info)
        self.assertIn('device', device_info)
        self.assertIn('is_mobile', device_info)