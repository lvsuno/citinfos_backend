/**
 * Social Authentication Service - Django AllAuth Integration
 * Simplified service that works with Django AllAuth backend
 */

import axios from 'axios';

// Use the environment variable directly - it already includes /api
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class SocialAuthService {
  /**
   * Universal social login method for all providers
   * Works with Django AllAuth backend
   */
  async socialLogin(provider, credentials) {
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/social/`, {
        provider: provider,
        ...credentials
      });
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.error || `${provider} login failed`;
      throw new Error(errorMessage);
    }
  }

  /**
   * Google OAuth Login (using access token from Google SDK)
   */
  async googleLogin(accessToken) {
    return this.socialLogin('google', {
      access_token: accessToken
    });
  }

  /**
   * Facebook OAuth Login (using access token from Facebook SDK)
   */
  async facebookLogin(accessToken) {
    return this.socialLogin('facebook', {
      access_token: accessToken
    });
  }

  /**
   * GitHub OAuth Login (using authorization code)
   */
  async githubLogin(code, redirectUri) {
    return this.socialLogin('github', {
      code: code,
      redirect_uri: redirectUri || window.location.origin + '/auth/callback'
    });
  }

  /**
   * Twitter OAuth Login (using OAuth tokens)
   */
  async twitterLogin(oauthToken, oauthVerifier) {
    return this.socialLogin('twitter', {
      oauth_token: oauthToken,
      oauth_verifier: oauthVerifier
    });
  }

  /**
   * Get OAuth authorization URL from backend
   * This uses Django AllAuth's URL generation
   */
  async getOAuthURL(provider, redirectUri = window.location.origin + '/auth/callback') {
    try {
      const response = await axios.get(`${API_BASE_URL}/auth/social/url/${provider}/`, {
        params: { redirect_uri: redirectUri }
      });
      return response.data.auth_url;
    } catch (error) {
      // Fallback to client-side URL generation for providers that support it
      return this.getClientOAuthURL(provider, redirectUri);
    }
  }

  /**
   * Client-side OAuth URL generation (fallback)
   */
  getClientOAuthURL(provider, redirectUri = window.location.origin + '/auth/callback') {
    const clientIds = {
      github: import.meta.env.VITE_GITHUB_CLIENT_ID,
      google: import.meta.env.VITE_GOOGLE_CLIENT_ID,
      facebook: import.meta.env.VITE_FACEBOOK_APP_ID,
      twitter: import.meta.env.VITE_TWITTER_CLIENT_ID
    };

    switch (provider) {
      case 'github':
        return `https://github.com/login/oauth/authorize?client_id=${clientIds.github}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=user:email&state=github`;
      case 'google':
        return `https://accounts.google.com/oauth/authorize?client_id=${clientIds.google}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=email profile&response_type=code&state=google`;
      default:
        throw new Error(`OAuth URL not supported for provider: ${provider}`);
    }
  }

  /**
   * Get available social providers from backend
   */
  async getAvailableProviders() {
    try {
      const response = await axios.get(`${API_BASE_URL}/auth/social/apps/`);
      return response.data.available_providers || [];
    } catch (error) {
      console.warn('Could not fetch available providers, using defaults');
      return ['google', 'facebook', 'github', 'twitter'];
    }
  }

  /**
   * Handle OAuth callback (for redirect-based flows)
   */
  async handleOAuthCallback(provider, urlParams) {
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const error = urlParams.get('error');

    if (error) {
      throw new Error(`OAuth error: ${error}`);
    }

    if (!code) {
      throw new Error('No authorization code received');
    }

    // Verify state parameter matches provider (basic CSRF protection)
    if (state && state !== provider) {
      throw new Error('Invalid state parameter');
    }

    // Exchange code for tokens
    if (provider === 'github') {
      return this.githubLogin(code);
    } else if (provider === 'google') {
      return this.socialLogin('google', { code: code });
    } else {
      throw new Error(`Callback handling not implemented for ${provider}`);
    }
  }
}

export default new SocialAuthService();