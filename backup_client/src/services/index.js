/**
 * API Services Index
 *
 * Central export file for all API services that use JWT authentication.
 * This makes it easier to import services throughout the application.
 */

// Authentication
export { jwtAuthService, useJWTAuth, JWTAuthProvider } from './jwtAuthService';
export { default as BaseAPIService, baseAPI } from './baseAPI';

// Core API services
export { default as authService } from './authService';
export { default as searchService } from './searchService';

// Social and content APIs
export { default as socialAPI } from './social-api';
export { default as communityContextAPI } from './community-context-api';
export { default as chatAPI } from './chat-api';

// Legacy axios config (for compatibility)
export { default as api } from './axiosConfig';
