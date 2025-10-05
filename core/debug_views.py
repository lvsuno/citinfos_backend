"""
Debug utilities view for testing and debugging.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from core.utils import get_client_ip, get_location_from_ip
import json


@csrf_exempt
@require_http_methods(["GET"])
def debug_ip_location(request):
    """
    Debug endpoint to test IP geolocation functionality.
    Returns the user's IP and its resolved location.
    """
    try:
        # Get client IP
        client_ip = get_client_ip(request)

        # Get location from IP
        location_data = get_location_from_ip(client_ip)

        # Prepare debug response
        # Expose the headers checked by get_client_ip to help debugging
        header_keys = [
            'X_FORWARDED_FOR', 'HTTP_X_FORWARDED_FOR', 'HTTP_CLIENT_IP',
            'HTTP_X_REAL_IP', 'HTTP_X_FORWARDED', 'HTTP_X_CLUSTER_CLIENT_IP',
            'HTTP_FORWARDED_FOR', 'HTTP_FORWARDED', 'HTTP_CF_CONNECTING_IP',
            'X-CLIENT-IP', 'X-REAL-IP', 'X-CLUSTER-CLIENT-IP', 'X_FORWARDED',
            'FORWARDED_FOR', 'CF-CONNECTING-IP', 'TRUE-CLIENT-IP',
            'FASTLY-CLIENT-IP', 'FORWARDED', 'CLIENT-IP', 'REMOTE_ADDR'
        ]

        headers = {k: request.META.get(k) for k in header_keys}

        debug_info = {
            'client_ip': client_ip,
            'location_data': location_data,
            'headers': headers,
            'success': True,
            'timestamp': str(request.headers.get('Date', 'N/A')),
        }

        return JsonResponse(debug_info)

    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False,
            'client_ip': None,
            'location_data': {},
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def debug_custom_ip_location(request):
    """
    Debug endpoint to test IP geolocation for a custom IP address.
    Requires IP address in POST body.
    """
    try:
        data = json.loads(request.body)
        custom_ip = data.get('ip')

        if not custom_ip:
            return JsonResponse({
                'error': 'IP address is required',
                'success': False,
            }, status=400)

        # Get location from custom IP
        location_data = get_location_from_ip(custom_ip)

        debug_info = {
            'provided_ip': custom_ip,
            'location_data': location_data,
            'success': True,
        }

        return JsonResponse(debug_info)

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body',
            'success': False,
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False,
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def debug_client_fingerprint(request):
    """
    Debug endpoint to capture client headers and generate fingerprint.
    Call this from your browser to see what fingerprint is generated.
    """
    from core.device_fingerprint import OptimizedDeviceFingerprint
    from core.session_manager import session_manager
    import logging

    logger = logging.getLogger(__name__)

    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = '*'
        return response

    # Capture all relevant headers
    headers_info = {}
    fingerprint_headers = [
        'HTTP_USER_AGENT',
        'HTTP_ACCEPT',
        'HTTP_ACCEPT_LANGUAGE',
        'HTTP_ACCEPT_ENCODING',
        'HTTP_ACCEPT_CHARSET',
        'HTTP_DNT',
        'HTTP_CONNECTION',
        'HTTP_CACHE_CONTROL',
        'HTTP_PRAGMA',
        'HTTP_SEC_FETCH_DEST',
        'HTTP_SEC_FETCH_MODE',
        'HTTP_SEC_FETCH_SITE',
        'HTTP_SEC_FETCH_USER',
        'HTTP_UPGRADE_INSECURE_REQUESTS',
        'REMOTE_ADDR',
    ]

    for header in fingerprint_headers:
        if header in request.META:
            headers_info[header] = request.META[header]

    # Generate fast fingerprint with current request
    fast_fingerprint = OptimizedDeviceFingerprint.get_fast_fingerprint(request)

    # Get browser and OS detection
    ua = request.META.get('HTTP_USER_AGENT', '')
    browser_family = OptimizedDeviceFingerprint._fast_browser_detection(ua)
    os_family = OptimizedDeviceFingerprint._fast_os_detection(ua)

    # Test session lookup
    found_session = session_manager.find_any_active_session_by_fingerprint(fast_fingerprint)
    session_found = found_session is not None

    if found_session:
        user_profile = found_session.get('user_profile')
        session_user = user_profile.user.username if user_profile else 'Unknown'
    else:
        session_user = None

    # Log for server-side debugging
    logger.info("🔍 CLIENT FINGERPRINT DEBUG:")
    logger.info(f"  Generated Fingerprint: {fast_fingerprint}")
    logger.info(f"  Browser: {browser_family}")
    logger.info(f"  OS: {os_family}")
    logger.info(f"  Session Found: {session_found}")
    logger.info(f"  Headers:")
    for key, value in headers_info.items():
        logger.info(f"    {key}: {value}")

    response_data = {
        'fingerprint': fast_fingerprint,
        'browser_family': browser_family,
        'os_family': os_family,
        'headers': headers_info,
        'session_found': session_found,
        'session_user': session_user,
        'request_method': request.method,
        'request_path': request.path,
        'timestamp': request.META.get('HTTP_DATE', 'Unknown')
    }

    response = JsonResponse(response_data)
    response['Access-Control-Allow-Origin'] = '*'
    return response
