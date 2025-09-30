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
