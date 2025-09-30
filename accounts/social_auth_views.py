"""
Django AllAuth integration with JWT authentication system.
Provides API endpoints for social authentication that work with the existing JWT system.
"""
from django.contrib.auth import login
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.socialaccount.models import SocialApp, SocialAccount
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.twitter.views import TwitterOAuthAdapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.oauth.client import OAuthClient
from allauth.socialaccount import app_settings
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialLogin
from allauth.account.utils import complete_signup
import json


def generate_jwt_tokens(user):
    """Generate JWT tokens for authenticated user."""
    refresh = RefreshToken.for_user(user)
    return {
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def social_login(request):
    """
    Handle social login for all providers.

    Expected payload:
    {
        "provider": "google|facebook|github|twitter",
        "access_token": "provider_access_token",  # For Google/Facebook
        "code": "oauth_code",  # For GitHub/Twitter
        "redirect_uri": "frontend_redirect_uri"  # For GitHub/Twitter
    }
    """
    try:
        data = request.data
        provider = data.get('provider')

        if not provider:
            return Response(
                {'error': 'Provider is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Route to appropriate provider handler
        if provider == 'google':
            return handle_google_login(request, data)
        elif provider == 'facebook':
            return handle_facebook_login(request, data)
        elif provider == 'github':
            return handle_github_login(request, data)
        elif provider == 'twitter':
            return handle_twitter_login(request, data)
        else:
            return Response(
                {'error': f'Unsupported provider: {provider}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        return Response(
            {'error': f'Authentication failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def handle_google_login(request, data):
    """Handle Google OAuth login."""
    access_token = data.get('access_token')
    if not access_token:
        return Response(
            {'error': 'Google access token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get Google app
        app = SocialApp.objects.get(provider='google')

        # Create OAuth2 client
        client = OAuth2Client(
            client_id=app.client_id,
            client_secret=app.secret,
        )

        # Create adapter and complete login
        adapter = GoogleOAuth2Adapter(request)
        token = adapter.parse_token({'access_token': access_token})
        token.app = app

        # Get user info and complete social login
        login_result = adapter.complete_login(request, app, token, response={'access_token': access_token})

        return complete_social_auth(request, login_result)

    except SocialApp.DoesNotExist:
        return Response(
            {'error': 'Google app not configured'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Google authentication failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


def handle_facebook_login(request, data):
    """Handle Facebook OAuth login."""
    access_token = data.get('access_token')
    if not access_token:
        return Response(
            {'error': 'Facebook access token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get Facebook app
        app = SocialApp.objects.get(provider='facebook')

        # Create adapter and complete login
        adapter = FacebookOAuth2Adapter(request)
        token = adapter.parse_token({'access_token': access_token})
        token.app = app

        # Get user info and complete social login
        login_result = adapter.complete_login(request, app, token, response={'access_token': access_token})

        return complete_social_auth(request, login_result)

    except SocialApp.DoesNotExist:
        return Response(
            {'error': 'Facebook app not configured'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Facebook authentication failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


def handle_github_login(request, data):
    """Handle GitHub OAuth login."""
    code = data.get('code')
    redirect_uri = data.get('redirect_uri')

    if not code:
        return Response(
            {'error': 'GitHub authorization code is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get GitHub app
        app = SocialApp.objects.get(provider='github')

        # Create OAuth2 client
        client = OAuth2Client(
            client_id=app.client_id,
            client_secret=app.secret,
        )

        # Create adapter and complete login
        adapter = GitHubOAuth2Adapter(request)

        # Exchange code for access token
        access_token = adapter.get_access_token_data(code, redirect_uri)
        token = adapter.parse_token(access_token)
        token.app = app

        # Get user info and complete social login
        login_result = adapter.complete_login(request, app, token, response=access_token)

        return complete_social_auth(request, login_result)

    except SocialApp.DoesNotExist:
        return Response(
            {'error': 'GitHub app not configured'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'GitHub authentication failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


def handle_twitter_login(request, data):
    """Handle Twitter OAuth login."""
    # Note: Twitter uses OAuth 1.0a, which is more complex
    # For now, we'll implement a basic version
    oauth_token = data.get('oauth_token')
    oauth_verifier = data.get('oauth_verifier')

    if not oauth_token or not oauth_verifier:
        return Response(
            {'error': 'Twitter OAuth token and verifier are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get Twitter app
        app = SocialApp.objects.get(provider='twitter')

        # Create adapter
        adapter = TwitterOAuthAdapter(request)

        # Complete the OAuth flow (simplified)
        # In a real implementation, you'd need to handle the full OAuth 1.0a flow
        return Response(
            {'error': 'Twitter authentication not fully implemented yet'},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )

    except SocialApp.DoesNotExist:
        return Response(
            {'error': 'Twitter app not configured'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Twitter authentication failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


def complete_social_auth(request, social_login):
    """Complete social authentication and return JWT tokens."""
    try:
        # Complete the social login process
        ret = complete_social_login(request, social_login)

        if ret:
            # If there was a redirect or error, handle it
            if hasattr(ret, 'status_code'):
                return Response(
                    {'error': 'Social login failed'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Get the user from the social login
        user = social_login.user

        if not user.is_active:
            return Response(
                {'error': 'User account is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate JWT tokens
        tokens = generate_jwt_tokens(user)

        # Get user profile info
        try:
            from .models import UserProfile
            profile = UserProfile.objects.get(user=user)
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'display_name': profile.display_name,
                'avatar_url': profile.avatar.url if profile.avatar else None,
            }
        except UserProfile.DoesNotExist:
            # Create a basic user profile if it doesn't exist
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }

        return Response({
            'success': True,
            'user': user_data,
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Failed to complete social authentication: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def social_login_url(request, provider):
    """
    Get the OAuth login URL for a specific provider.
    Used for redirect-based flows (GitHub, Twitter).
    """
    try:
        # Get the redirect URI from query params
        redirect_uri = request.GET.get('redirect_uri', 'http://localhost:3000/auth/callback')

        if provider == 'github':
            try:
                app = SocialApp.objects.get(provider='github')
                auth_url = (
                    f"https://github.com/login/oauth/authorize"
                    f"?client_id={app.client_id}"
                    f"&redirect_uri={redirect_uri}"
                    f"&scope=user:email"
                    f"&state=github"
                )
                return Response({'auth_url': auth_url})
            except SocialApp.DoesNotExist:
                return Response(
                    {'error': 'GitHub app not configured'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        elif provider == 'twitter':
            return Response(
                {'error': 'Twitter OAuth URL generation not implemented'},
                status=status.HTTP_501_NOT_IMPLEMENTED
            )

        else:
            return Response(
                {'error': f'OAuth URL not supported for provider: {provider}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        return Response(
            {'error': f'Failed to generate OAuth URL: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def social_apps(request):
    """Get configured social applications."""
    try:
        apps = SocialApp.objects.filter(
            provider__in=['google', 'facebook', 'github', 'twitter']
        ).values('provider', 'name', 'client_id')

        # Return apps data (client_id is safe to expose to frontend)
        return Response({
            'apps': list(apps),
            'available_providers': [app['provider'] for app in apps]
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Failed to get social apps: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )