# core/device_fingerprint.py
"""
Optimized Device Fingerprinting System

Combines fast server-side fingerprinting with client-side enhancement
for optimal performance and security.
"""

import hashlib
import json
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.http import HttpRequest

from core.utils import get_device_info


class OptimizedDeviceFingerprint:
    """
    High-performance device fingerprinting with hybrid approach:
    1. Fast server-side fingerprint for immediate response (10-20ms)
    2. Enhanced client-side data collection (background)
    3. Merged fingerprint for maximum accuracy
    """

    CACHE_TTL = 3600  # 1 hour cache for fingerprint components

    @classmethod
    def get_fast_fingerprint(cls, request: HttpRequest) -> str:
        """
        Generate fast server-side fingerprint for immediate use.
        Uses only HTTP headers and basic request data (10-20ms).

        Note: IP address excluded to allow session recovery across locations.

        Args:
            request: Django HTTP request object

        Returns:
            SHA256 hash string for fast fingerprint
        """
        # Fast fingerprint using only HTTP headers
        # (excluding IP for location independence)
        ua = request.META.get('HTTP_USER_AGENT', '')
        accept = request.META.get('HTTP_ACCEPT', '')
        accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')

        # Basic server-side device detection (fast)
        browser_family = cls._fast_browser_detection(ua)
        os_family = cls._fast_os_detection(ua)

        # Build fast fingerprint components (IP removed for location-independence)
        fast_components = [
            ua, accept, accept_lang, accept_encoding,
            browser_family, os_family
        ]

        # Generate SHA256 hash
        fingerprint_str = '|'.join(str(comp) for comp in fast_components)
        return hashlib.sha256(fingerprint_str.encode('utf-8')).hexdigest()

    @classmethod
    def get_enhanced_fingerprint(cls, client_data: Optional[Dict[str, Any]] = None,
                               server_data: Optional[Dict[str, Any]] = None
                               ) -> str:
        """
        Generate enhanced fingerprint with full server + client data.
        Used for background processing and high-security scenarios.

        Args:
            request: Django HTTP request object
            client_data: Client-side fingerprint data
            merged_device_info: Server-side device information

        Returns:
            SHA256 hash string for enhanced fingerprint
        """
        # Start with fast fingerprint components
        # fast_fingerprint = cls.get_fast_fingerprint(request)

        # Add enhanced server-side data
        enhanced_components = []

        if server_data:
            server_components = cls._extract_server_components(server_data)
            enhanced_components.extend(server_components)

        # Add client-side fingerprint data
        if client_data:
            client_components = cls._extract_client_components(client_data)
            enhanced_components.extend(client_components)

        # Generate enhanced SHA256 hash
        enhanced_str = '|'.join(str(comp) for comp in enhanced_components)
        return hashlib.sha256(enhanced_str.encode('utf-8')).hexdigest()

    @classmethod
    def _fast_browser_detection(cls, user_agent: str) -> str:
        """Fast browser family detection from user agent"""
        ua_lower = user_agent.lower()
        if 'chrome' in ua_lower and 'chromium' not in ua_lower:
            return 'Chrome'
        elif 'firefox' in ua_lower:
            return 'Firefox'
        elif 'safari' in ua_lower and 'chrome' not in ua_lower:
            return 'Safari'
        elif 'edge' in ua_lower:
            return 'Edge'
        elif 'opera' in ua_lower:
            return 'Opera'
        else:
            return 'Unknown'

    @classmethod
    def _fast_os_detection(cls, user_agent: str) -> str:
        """Fast OS family detection from user agent"""
        ua_lower = user_agent.lower()
        if 'windows' in ua_lower:
            return 'Windows'
        elif 'mac os x' in ua_lower or 'macos' in ua_lower:
            return 'macOS'
        elif 'linux' in ua_lower:
            return 'Linux'
        elif 'android' in ua_lower:
            return 'Android'
        elif 'ios' in ua_lower or 'iphone' in ua_lower or 'ipad' in ua_lower:
            return 'iOS'
        else:
            return 'Unknown'

    @classmethod
    def _extract_server_components(cls, device_info: Dict[str, Any]) -> list:
        """Extract fingerprint components from server-side device info"""
        components = []

        # Basic server-side request data (excluding IP for location-independence)
        components.extend([
            device_info.get('accept', ''),
            device_info.get('accept_lang', ''),
            device_info.get('accept_encoding', ''),
            device_info.get('accept_charset', ''),
        ])

        # Security and tracking headers
        components.extend([
            device_info.get('dnt', ''),  # Do Not Track
            device_info.get('connection', ''),
            device_info.get('cache_control', ''),
            device_info.get('pragma', ''),
        ])

        # Security fetch headers (modern browsers)
        components.extend([
            device_info.get('sec_fetch_dest', ''),
            device_info.get('sec_fetch_mode', ''),
            device_info.get('sec_fetch_site', ''),
            device_info.get('sec_fetch_user', ''),
            device_info.get('upgrade_insecure', ''),
        ])

        # Browser info (from user agent parsing)
        browser_info = device_info.get('browser', {})
        if isinstance(browser_info, dict):
            components.extend([
                browser_info.get('family', ''),
                browser_info.get('version', ''),
            ])

        # OS info (from user agent parsing)
        os_info = device_info.get('os', {})
        if isinstance(os_info, dict):
            components.extend([
                os_info.get('family', ''),
                os_info.get('version', ''),
            ])

        # Device info (from user agent parsing)
        device_data = device_info.get('device', {})
        if isinstance(device_data, dict):
            components.extend([
                device_data.get('family', ''),
                device_data.get('brand', ''),
                device_data.get('model', ''),
            ])

        # Device capabilities
        components.extend([
            str(device_info.get('is_mobile', '')),
            str(device_info.get('is_tablet', '')),
            str(device_info.get('is_bot', '')),
            str(device_info.get('is_touch_capable', '')),
            str(device_info.get('is_pc', '')),
        ])

        return components

    @classmethod
    def _extract_client_components(cls, client_data: Dict[str, Any]) -> list:
        """Extract fingerprint components from client-side data"""
        components = []

        # Hardware and display
        components.extend([
            client_data.get('screen_resolution', ''),
            str(client_data.get('color_depth', '')),
            str(client_data.get('hardware_concurrency', '')),
            client_data.get('device_memory', ''),
        ])

        # System info
        components.extend([
            client_data.get('timezone', ''),
            client_data.get('platform', ''),
            client_data.get('language', ''),
        ])

        # Languages (array support)
        languages = client_data.get('languages', [])
        if isinstance(languages, list):
            components.append('|'.join(sorted(languages)))
        else:
            components.append(str(languages))

        # Browser capabilities and storage
        components.extend([
            client_data.get('touch_support', ''),
            client_data.get('cookie_enabled', ''),
            client_data.get('local_storage', ''),
            client_data.get('session_storage', ''),
            client_data.get('indexed_db', ''),
        ])

        # WebGL and graphics
        components.extend([
            client_data.get('webgl_support', ''),
            client_data.get('webgl_vendor', ''),
            client_data.get('webgl_renderer', ''),
            client_data.get('canvas_fingerprint', ''),
        ])

        # Audio fingerprinting
        components.extend([
            client_data.get('audio_fingerprint', ''),
        ])

        # Client-provided fingerprint
        components.extend([
            client_data.get('client_fingerprint', ''),
        ])

        # Fonts (multiple font sources)
        fonts = client_data.get('fonts', [])
        if isinstance(fonts, list):
            components.append('|'.join(sorted(fonts)))
        else:
            components.append(str(fonts))

        available_fonts = client_data.get('available_fonts', [])
        if isinstance(available_fonts, list):
            components.append('|'.join(sorted(available_fonts)))
        else:
            components.append(str(available_fonts))

        # Plugins
        plugins = client_data.get('plugins', [])
        if isinstance(plugins, list):
            components.append('|'.join(sorted(plugins)))
        else:
            components.append(str(plugins))

        components.extend([
            client_data.get('plugins_hash', ''),
        ])

        # Storage and network
        components.extend([
            client_data.get('storage_quota', ''),
            client_data.get('connection_type', ''),
        ])

        # Network info (if it's a dict, serialize it consistently)
        network_info = client_data.get('network_info')
        if isinstance(network_info, dict):
            # Sort keys for consistent serialization
            network_str = '|'.join(
                f"{k}:{v}" for k, v in sorted(network_info.items())
            )
            components.append(network_str)
        else:
            components.append(str(network_info) if network_info else '')

        return components

    @classmethod
    def cache_client_fingerprint(cls, session_id: str,
                                 client_data: Dict[str, Any]):
        """
        Cache client-side fingerprint data for later merging.

        Args:
            session_id: Session identifier
            client_data: Client-side fingerprint data
        """
        cache_key = f"client_fingerprint:{session_id}"
        try:
            cache.set(cache_key, client_data, cls.CACHE_TTL)
        except (ConnectionError, TimeoutError) as e:
            # Don't fail if caching fails
            print(f"Client fingerprint caching failed: {e}")

    @classmethod
    def get_cached_client_fingerprint(cls, session_id: str) -> Optional[
        Dict[str, Any]
    ]:
        """
        Retrieve cached client-side fingerprint data.

        Args:
            session_id: Session identifier

        Returns:
            Client fingerprint data or None
        """
        cache_key = f"client_fingerprint:{session_id}"
        try:
            return cache.get(cache_key)
        except (ConnectionError, TimeoutError):
            return None


# Convenience functions for backward compatibility
def get_fast_device_fingerprint(request: HttpRequest) -> str:
    """
    OPTIMIZED: Fast device fingerprinting for immediate responses.
    Replacement for expensive get_device_fingerprint() calls.
    """
    return OptimizedDeviceFingerprint.get_fast_fingerprint(request)


def get_enhanced_device_fingerprint(
    request: HttpRequest,
    client_data: Optional[Dict[str, Any]] = None,
    server_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Enhanced device fingerprinting with full data.
    Used for background processing and high-security scenarios.
    """
    return OptimizedDeviceFingerprint.get_enhanced_fingerprint(
        client_data, server_data
    )
