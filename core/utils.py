"""
Core utilities used across multiple apps.
"""

import hashlib
from user_agents import parse
from typing import Any, Dict
from geoip2.database import Reader
import os
from django.conf import settings


def get_client_ip(request):
    """
    Get the real client IP address from request.

    Handles Docker, reverse proxy, and load balancer scenarios by checking
    multiple headers in priority order to avoid getting internal Docker IPs.

    Priority order:
    1. CF-Connecting-IP (Cloudflare)
    2. X-Real-IP (nginx)
    3. X-Forwarded-For (most proxies) - takes first IP
    4. X-Forwarded (alternative)
    5. X-Cluster-Client-IP (cluster environments)
    6. REMOTE_ADDR (direct connection)
    7. Real public IP (fallback for development/proxy scenarios)
    """
    # Priority list of headers to check for real client IP
    headers = [
        'HTTP_CF_CONNECTING_IP',     # Cloudflare
        'HTTP_X_REAL_IP',            # nginx real_ip_header
        'HTTP_X_FORWARDED_FOR',      # Standard forwarded header
        'HTTP_X_FORWARDED',          # Alternative forwarded header
        'HTTP_X_CLUSTER_CLIENT_IP',  # Cluster environments
        'REMOTE_ADDR'                # Direct connection (fallback)
    ]

    # Known proxy/CDN IP ranges that should trigger real IP lookup
    proxy_ip_ranges = [
        '172.67.',    # Cloudflare
        '104.16.',    # Cloudflare
        '104.17.',    # Cloudflare
        '104.18.',    # Cloudflare
        '104.19.',    # Cloudflare
        '104.20.',    # Cloudflare
        '104.21.',    # Cloudflare
        '104.22.',    # Cloudflare
        '104.23.',    # Cloudflare
        '104.24.',    # Cloudflare
        '104.25.',    # Cloudflare
        '104.26.',    # Cloudflare
        '104.27.',    # Cloudflare
        '104.28.',    # Cloudflare
        '172.64.',    # Cloudflare
        '172.65.',    # Cloudflare
        '172.66.',    # Cloudflare
        '172.68.',    # Cloudflare
        '172.69.',    # Cloudflare
        '172.70.',    # Cloudflare
        '172.71.',    # Cloudflare
    ]

    detected_ip = None

    for header in headers:
        ip = request.META.get(header)
        if ip:
            # Handle comma-separated IPs (X-Forwarded-For can have multiple IPs)
            if ',' in ip:
                ip = ip.split(',')[0].strip()

            # Clean up the IP address
            ip = ip.strip()

            # Skip internal/private IP addresses if we have more headers to check
            if header != 'REMOTE_ADDR' and _is_private_ip(ip):
                continue

            detected_ip = ip
            break

    # If we detected a proxy IP or no IP at all, try to get real public IP in DEBUG mode
    if getattr(request, '_real_ip_debug', True) and getattr(settings, 'DEBUG', False):
        is_proxy_ip = detected_ip and any(detected_ip.startswith(prefix) for prefix in proxy_ip_ranges)

        if not detected_ip or _is_private_ip(detected_ip) or is_proxy_ip:
            public_ip = _get_public_ip()
            if public_ip and not _is_private_ip(public_ip):
                return public_ip

    return detected_ip


def _is_private_ip(ip):
    """
    Check if an IP address is in a private/internal range that should be
    skipped when looking for real client IP.

    We only consider actual RFC 1918 private networks, loopback, and
    link-local addresses as "private". Documentation/testing ranges
    are treated as valid public IPs since they can be geolocated.
    """
    if not ip:
        return True

    try:
        import ipaddress
        ip_obj = ipaddress.ip_address(ip)

        # Only check for actual private/internal ranges that should be skipped
        # We explicitly avoid using is_private as it's too broad
        return (
            ip_obj.is_loopback or     # 127.x.x.x
            ip_obj.is_link_local or   # 169.254.x.x
            ip_obj.is_multicast or    # 224.x.x.x and above
            # RFC 1918 private ranges (check manually to be specific)
            (ip_obj >= ipaddress.ip_address('10.0.0.0') and
             ip_obj <= ipaddress.ip_address('10.255.255.255')) or
            (ip_obj >= ipaddress.ip_address('172.16.0.0') and
             ip_obj <= ipaddress.ip_address('172.31.255.255')) or
            (ip_obj >= ipaddress.ip_address('192.168.0.0') and
             ip_obj <= ipaddress.ip_address('192.168.255.255'))
        )
    except (ImportError, ValueError, AttributeError):
        # Fallback to simple string-based checks if ipaddress module fails
        # or if IP format is invalid
        private_ranges = [
            '127.',      # Loopback
            '10.',       # Private Class A (10.0.0.0/8)
            '172.16.',   # Private Class B start (172.16.0.0/12)
            '172.17.',   # Docker default
            '172.18.',   # Docker custom
            '172.19.',   # Docker custom
            '172.20.',   # Docker custom
            '172.21.',   # Docker custom
            '172.22.',   # Docker custom
            '172.23.',   # Docker custom
            '172.24.',   # Docker custom
            '172.25.',   # Docker custom
            '172.26.',   # Docker custom
            '172.27.',   # Docker custom
            '172.28.',   # Docker custom
            '172.29.',   # Docker custom
            '172.30.',   # Docker custom
            '172.31.',   # Private Class B end
            '192.168.',  # Private Class C (192.168.0.0/16)
            '169.254.',  # Link-local (169.254.0.0/16)
        ]

        for prefix in private_ranges:
            if ip.startswith(prefix):
                return True

        return False


def get_device_info(request) -> Dict[str, Any]:
    """Extract device information from user agent"""
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')

    if parse:
        user_agent = parse(user_agent_string)
        return {
            'browser': {
                'family': user_agent.browser.family,
                'version': user_agent.browser.version_string,
            },
            'os': {
                'family': user_agent.os.family,
                'version': user_agent.os.version_string,
            },
            'device': {
                'family': user_agent.device.family,
                'brand': user_agent.device.brand,
                'model': user_agent.device.model,
            },
            'is_mobile': user_agent.is_mobile,
            'is_tablet': user_agent.is_tablet,
            'is_pc': user_agent.is_pc,
            'is_bot': user_agent.is_bot,
            'is_touch_capable': user_agent.is_touch_capable,
        }
    else:
        # Fallback: Basic user agent parsing without external library
        user_agent_lower = user_agent_string.lower()

        # Basic mobile detection
        is_mobile = any(mobile in user_agent_lower for mobile in [
            'mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone'
        ])

        # Basic tablet detection
        is_tablet = any(tablet in user_agent_lower for tablet in [
            'ipad', 'tablet', 'kindle'
        ])

        # Basic browser detection
        browser_family = 'Unknown'
        if 'chrome' in user_agent_lower:
            browser_family = 'Chrome'
        elif 'firefox' in user_agent_lower:
            browser_family = 'Firefox'
        elif 'safari' in user_agent_lower:
            browser_family = 'Safari'
        elif 'edge' in user_agent_lower:
            browser_family = 'Edge'

        # Basic OS detection
        os_family = 'Unknown'
        if 'windows' in user_agent_lower:
            os_family = 'Windows'
        elif 'mac' in user_agent_lower:
            os_family = 'macOS'
        elif 'linux' in user_agent_lower:
            os_family = 'Linux'
        elif 'android' in user_agent_lower:
            os_family = 'Android'
        elif 'ios' in user_agent_lower or 'iphone' in user_agent_lower:
            os_family = 'iOS'

        return {
            'browser': {
                'family': browser_family,
                'version': 'Unknown',
            },
            'os': {
                'family': os_family,
                'version': 'Unknown',
            },
            'device': {
                'family': 'Unknown',
                'brand': 'Unknown',
                'model': 'Unknown',
            },
            'is_mobile': is_mobile,
            'is_tablet': is_tablet,
            'is_pc': not is_mobile and not is_tablet,
            'is_bot': False,
        }


def get_location_from_ip(ip: str) -> dict:
    """
    Infer location from IP address using MaxMind GeoLite2 City database.
    Returns a dict with country, city, latitude, longitude, etc. or empty dict if not found.
    Requires the GeoLite2-City.mmdb file (see MaxMind license).

    Note: IP validation and proxy detection should be handled by get_client_ip() before calling this function.
    """
    # If we don't have a valid IP, return empty
    if not ip:
        return {}

    db_path = getattr(settings, 'GEOIP2_DB_PATH', None) or os.environ.get('GEOIP2_DB_PATH')
    if not db_path:
        # Default to a common location in the project
        db_path = os.path.join(settings.BASE_DIR, 'GeoLite2-City.mmdb')
    if not os.path.exists(db_path):
        return {}
    try:
        reader = Reader(db_path)
        response = reader.city(ip)
        location = {
            'country': response.country.name,
            'country_iso_code': response.country.iso_code,
            'city': response.city.name,
            'region': response.subdivisions.most_specific.name,
            'latitude': response.location.latitude,
            'longitude': response.location.longitude,
            'timezone': response.location.time_zone,
            'accuracy_radius': response.location.accuracy_radius
        }
        reader.close()
        return {k: v for k, v in location.items() if v}
    except Exception:
        return {}


def _get_public_ip():
    """
    Get the user's real public IP address using external services.
    This is only used in development mode when Docker gives us internal IPs.

    Returns the public IP address or None if unable to determine.
    """
    try:
        import requests
    except ImportError:
        # requests not available, return None
        return None

    # List of reliable IP detection services
    services = [
        'https://api.ipify.org?format=text',
        'https://ipv4.icanhazip.com',
        'https://api.my-ip.io/ip.txt',
        'https://checkip.amazonaws.com',
    ]

    for service in services:
        try:
            response = requests.get(service, timeout=3)
            if response.status_code == 200:
                ip = response.text.strip()
                # Validate it's a proper IP address
                if ip and not _is_private_ip(ip):
                    return ip
        except Exception:
            continue

    return None


def generate_recommendation_id(user_id, content_type, object_id):
    """Generate unique recommendation ID."""
    data = f"{user_id}:{content_type}:{object_id}"
    return hashlib.md5(data.encode()).hexdigest()
