"""
Middleware to check for suspended users on every request.
"""
import logging
from django.http import JsonResponse
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import TokenError
from accounts.models import UserProfile

logger = logging.getLogger(__name__)

class SuspensionCheckMiddleware:
    """
    Middleware to check if authenticated users are suspended.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated and suspended before processing request
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user, is_deleted=False)
                if profile.is_suspended:
                    # User is suspended, return suspension notice
                    return JsonResponse({
                        'error': 'Account suspended',
                        'status': 'suspended',
                        'message': 'Votre compte a été suspendu. Un email de notification a été envoyé à votre adresse.',
                        'code': 'ACCOUNT_SUSPENDED',
                        'suspended_at': profile.suspended_at.isoformat() if profile.suspended_at else None,
                        'suspension_reason': profile.suspension_reason or 'Raison non spécifiée',
                        'email': request.user.email
                    }, status=403)
            except UserProfile.DoesNotExist:
                # Profile doesn't exist, let the request continue
                pass
            except Exception as e:
                logger.error(f"Error checking suspension status: {e}")
                # Don't block the request if there's an error
                pass

        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Check suspension status before the view is called.
        This is more reliable than __call__ for API requests.
        """
        # Skip admin endpoints and auth endpoints
        if request.path.startswith('/api/admin/') or request.path.startswith('/api/auth/'):
            return None
            
        # Only check authenticated users
        if hasattr(request, 'user') and request.user.is_authenticated and not isinstance(request.user, AnonymousUser):
            try:
                profile = UserProfile.objects.get(user=request.user, is_deleted=False)
                if profile.is_suspended:
                    return JsonResponse({
                        'error': 'Account suspended',
                        'status': 'suspended',
                        'message': 'Votre compte a été suspendu. Un email de notification a été envoyé à votre adresse.',
                        'code': 'ACCOUNT_SUSPENDED',
                        'suspended_at': profile.suspended_at.isoformat() if profile.suspended_at else None,
                        'suspension_reason': profile.suspension_reason or 'Raison non spécifiée',
                        'email': request.user.email
                    }, status=403)
            except UserProfile.DoesNotExist:
                pass
            except Exception as e:
                logger.error(f"Error checking suspension in process_view: {e}")
        
        return None