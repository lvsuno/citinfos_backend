# Social Network Authentication - Django AllAuth Integration

## Overview
This implementation provides social network login/registration functionality using Django AllAuth, a robust and well-maintained authentication library. This replaces the previous custom OAuth implementation with a much simpler, more secure, and maintainable solution.

## Key Benefits of Django AllAuth

- **Proven Security**: Battle-tested OAuth implementation
- **Minimal Code**: No complex SDK management or token handling
- **Multiple Providers**: Easy support for 50+ social platforms
- **Automatic Updates**: Provider API changes are handled by AllAuth
- **Admin Interface**: Easy configuration through Django admin

## Architecture

### Backend (Django AllAuth)
- Django AllAuth handles all OAuth flows automatically
- Custom API views integrate AllAuth with existing JWT system
- Social apps are configured through Django admin or management commands
- All OAuth security is handled by AllAuth (CSRF, state verification, etc.)

### Frontend (Simplified)
- Simple redirect-based OAuth flows for all providers
- No complex SDK loading or popup management
- Single API endpoint handles all social providers
- Automatic provider detection from backend

## Components

### Backend Components

#### 1. Django AllAuth Configuration (`settings.py`)
- AllAuth apps added to `INSTALLED_APPS`
- Social providers configured: Google, Facebook, GitHub, Twitter
- Provider-specific settings for scopes and OAuth parameters

#### 2. Custom API Views (`accounts/social_auth_views.py`)
- `social_login()`: Universal endpoint for all providers
- `social_login_url()`: Get OAuth URLs for redirect flows
- `social_apps()`: List available/configured providers
- JWT token generation integrated with AllAuth authentication

#### 3. Management Command (`accounts/management/commands/setup_social_apps.py`)
- Easy setup of social applications from command line
- Creates SocialApp instances with OAuth credentials

### Frontend Components

#### 1. Simplified Social Auth Service (`src/services/socialAuth.js`)
- Single `socialLogin()` method for all providers
- Simplified redirect-based OAuth flows
- Automatic provider availability detection
- OAuth callback handling

#### 2. Streamlined Social Login Buttons (`src/components/SocialLoginButtons.jsx`)
- Loads available providers from backend
- Simple redirect flows (no SDK complexity)
- Consistent UI for all providers
- Loading states and error handling

#### 3. OAuth Callback Handler (`src/pages/OAuthCallback.jsx`)
- Handles OAuth redirects for all providers
- Automatic provider detection from URL parameters
- JWT token storage and user data refresh

## Setup Instructions

### 1. OAuth Application Setup

You'll need to create OAuth applications on each platform:

#### Google Cloud Console
- Go to: https://console.developers.google.com/
- Create project and enable Google+ API
- Create OAuth 2.0 credentials
- Add redirect URI: `http://localhost:5173/auth/callback` (dev)
- Add redirect URI: `https://yourdomain.com/auth/callback` (prod)

#### Facebook Developers
- Go to: https://developers.facebook.com/
- Create new app and add Facebook Login product
- Add redirect URIs in Facebook Login settings

#### GitHub Settings
- Go to: https://github.com/settings/developers
- Create new OAuth App
- Set Authorization callback URL

#### Twitter Developer Portal
- Go to: https://developer.twitter.com/
- Create new app and set callback URL

### 2. Environment Configuration

Copy `.env.social.example` to `.env.social` and fill in your OAuth credentials:

```bash
# Frontend variables (non-secret)
VITE_GOOGLE_CLIENT_ID=your_google_client_id
VITE_FACEBOOK_APP_ID=your_facebook_app_id
VITE_GITHUB_CLIENT_ID=your_github_client_id
VITE_TWITTER_CLIENT_ID=your_twitter_client_id

# Backend variables (secret)
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
FACEBOOK_APP_SECRET=your_facebook_app_secret
GITHUB_CLIENT_SECRET=your_github_client_secret
TWITTER_CLIENT_SECRET=your_twitter_client_secret
```

### 3. Django Social Apps Setup

Run the management command to create social applications:

```bash
docker compose exec backend python manage.py setup_social_apps \
  --google-client-id="$GOOGLE_OAUTH_CLIENT_ID" \
  --google-client-secret="$GOOGLE_OAUTH_CLIENT_SECRET" \
  --facebook-app-id="$FACEBOOK_APP_ID" \
  --facebook-app-secret="$FACEBOOK_APP_SECRET" \
  --github-client-id="$GITHUB_CLIENT_ID" \
  --github-client-secret="$GITHUB_CLIENT_SECRET"
```

Alternatively, configure through Django Admin:
- Go to `/admin/socialaccount/socialapp/`
- Add social applications manually

## API Endpoints

### Social Authentication
- `POST /api/auth/social/` - Universal social login endpoint
- `GET /api/auth/social/url/<provider>/` - Get OAuth authorization URL
- `GET /api/auth/social/apps/` - List available providers

### Request/Response Format

#### Social Login Request
```json
{
  "provider": "google|facebook|github|twitter",
  "access_token": "provider_access_token",  // For Google/Facebook
  "code": "oauth_authorization_code",       // For GitHub/Twitter
  "redirect_uri": "callback_url"            // For redirect flows
}
```

#### Success Response
```json
{
  "success": true,
  "user": {
    "id": 123,
    "username": "user123",
    "email": "user@example.com",
    "display_name": "User Name"
  },
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token"
}
```

## User Experience Flow

### Login Process
1. User clicks social login button
2. Frontend redirects to provider OAuth URL
3. User authenticates with social provider
4. Provider redirects to `/auth/callback` with authorization code
5. Frontend exchanges code for JWT tokens via AllAuth API
6. User is logged in and redirected to intended page

### Registration Process
- Same flow as login
- AllAuth automatically creates user account from social profile
- No email verification required for social accounts
- User profile populated with social data

## Security Features

- **CSRF Protection**: AllAuth handles state parameters automatically
- **Token Verification**: All social tokens verified server-side
- **Scope Limitation**: OAuth scopes limited to profile and email
- **JWT Integration**: Seamless integration with existing JWT auth system
- **No Client Secrets**: Frontend never sees OAuth client secrets

## Migration from Custom OAuth

### Removed Complexity
- ❌ Manual SDK loading (Google, Facebook)
- ❌ Complex popup management
- ❌ Custom token verification logic
- ❌ Provider-specific OAuth implementations
- ❌ Manual CSRF protection

### Added Benefits
- ✅ Single unified OAuth flow
- ✅ Automatic security updates
- ✅ Provider API compatibility
- ✅ Django admin integration
- ✅ Simplified debugging

## Troubleshooting

### Common Issues

1. **Provider not available**: Check if SocialApp is created in Django admin
2. **Redirect URI mismatch**: Ensure OAuth app redirect URIs match exactly
3. **Invalid client credentials**: Verify environment variables are correct
4. **CORS errors**: Check CORS_ALLOWED_ORIGINS includes your frontend domain

### Debug Mode
Enable Django AllAuth debug logging in settings:
```python
LOGGING = {
    'loggers': {
        'allauth': {
            'level': 'DEBUG',
        },
    },
}
```

## Future Enhancements

- **Additional Providers**: LinkedIn, Discord, Apple, etc.
- **Account Linking**: Connect multiple social accounts to one user
- **Profile Sync**: Automatic avatar/profile updates from social accounts
- **Admin Analytics**: Social login usage statistics