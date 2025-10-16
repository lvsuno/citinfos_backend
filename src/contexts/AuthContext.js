import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiService from '../services/apiService';
import { trackLogout } from '../utils/navigationTracker';
import geolocationService from '../services/geolocationService';

// Auth debugger disabled - uncomment if needed for debugging
// if (process.env.NODE_ENV === 'development') {
//     import('../utils/authDebugger').then(({ authDebugger }) => {
//         if (typeof window !== 'undefined') {
//             window.authDebugger = authDebugger;
//         }
//     });
// }

const AuthContext = createContext();

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [anonymousLocation, setAnonymousLocation] = useState(null);

    useEffect(() => {
        // Initialize authentication state
        const initializeAuth = async () => {
            setLoading(true);

            try {
                // First check if we have tokens
                const hasTokens = apiService.isAuthenticated();

                if (hasTokens) {
                    // We have tokens - try to validate them with API
                    try {
                        const userData = await apiService.getCurrentUser();
                        setUser(userData);
                        // Update localStorage with fresh user data
                        localStorage.setItem('currentUser', JSON.stringify(userData));
                    } catch (apiError) {
                        // API call failed, try localStorage fallback
                        const savedUser = localStorage.getItem('currentUser');
                        if (savedUser) {
                            try {
                                const parsedUser = JSON.parse(savedUser);
                                setUser(parsedUser);

                                // Try to validate the saved user in the background
                                setTimeout(async () => {
                                    try {
                                        const freshUserData = await apiService.getCurrentUser();
                                        if (freshUserData) {
                                            setUser(freshUserData);
                                            localStorage.setItem('currentUser', JSON.stringify(freshUserData));
                                        }
                                    } catch (bgError) {
                                        // Silent fail - keep cached user
                                    }
                                }, 1000);
                            } catch (parseError) {
                                console.error('Error parsing saved user:', parseError);
                                localStorage.removeItem('currentUser');
                                apiService.clearTokens();
                                setUser(null);
                            }
                        } else {
                            // No saved user and API failed - clear everything
                            apiService.clearTokens();
                            setUser(null);
                        }
                    }
                } else {
                    // No tokens - check if there's a saved user (shouldn't happen but handle it)
                    const savedUser = localStorage.getItem('currentUser');
                    if (savedUser) {
                        localStorage.removeItem('currentUser');
                    }

                    // FALLBACK: Try to retrieve session from server via fingerprint
                    // This handles development mode reloads and edge cases
                    try {
                        const userData = await apiService.getCurrentUser();
                        if (userData) {
                            setUser(userData);
                            localStorage.setItem('currentUser', JSON.stringify(userData));
                        } else {
                            setUser(null);
                        }
                    } catch (recoveryError) {
                        // No active session - stay in read-only mode
                        setUser(null);
                    }
                }
            } catch (error) {
                console.error('Auth initialization error:', error);
                // Clear everything on unexpected error
                apiService.clearTokens();
                setUser(null);
            } finally {
                setLoading(false);
            }
        };

        initializeAuth();

        // Listen for session expired events
        const handleSessionExpired = () => {
            setUser(null);
            apiService.clearTokens();
        };

        // Listen for session expired events
        window.addEventListener('sessionExpired', handleSessionExpired);

        // Focus and storage handlers disabled - were causing infinite re-renders
        // The authentication state is already managed by the main initialization above
        // and by the login/logout/register functions

        // window.addEventListener('focus', handleWindowFocus);
        // window.addEventListener('storage', handleStorageChange);

        return () => {
            window.removeEventListener('sessionExpired', handleSessionExpired);
            // window.removeEventListener('focus', handleWindowFocus);
            // window.removeEventListener('storage', handleStorageChange);
        };
    }, []);

    // Detect location for anonymous users
    useEffect(() => {
        const detectAnonymousLocation = async () => {
            // Only detect if user is not authenticated
            if (!user) {
                // Check if we have cached location
                const cachedLocation = localStorage.getItem('anonymousLocation');
                if (cachedLocation) {
                    try {
                        const parsed = JSON.parse(cachedLocation);
                        // Use cached if less than 24 hours old
                        const cacheAge = Date.now() - (parsed.timestamp || 0);
                        if (cacheAge < 24 * 60 * 60 * 1000) {
                            setAnonymousLocation(parsed);
                            return;
                        }
                    } catch (e) {
                        console.error('Error parsing cached location:', e);
                    }
                }

                // Detect location via IP
                try {
                    const locationData = await geolocationService.getUserLocationData();
                    if (locationData.success) {
                        const anonymousData = {
                            country: locationData.country,
                            location: locationData.userLocation,
                            closestDivisions: locationData.closestDivisions,
                            timestamp: Date.now()
                        };
                        setAnonymousLocation(anonymousData);
                        localStorage.setItem('anonymousLocation', JSON.stringify(anonymousData));
                    }
                } catch (error) {
                    console.error('Error detecting anonymous location:', error);
                }
            } else {
                // Clear anonymous location when user logs in
                setAnonymousLocation(null);
                localStorage.removeItem('anonymousLocation');
            }
        };

        detectAnonymousLocation();
    }, [user]);

    const login = async (usernameOrEmail, password, rememberMe = false) => {
        try {
            setLoading(true);
            console.log('🔑 Starting login process...');

            // First attempt login to get user info
            const result = await apiService.login(usernameOrEmail, password, rememberMe);

            if (result.success && result.user) {
                console.log('✅ Login successful for:', result.user.username || result.user.email);

                // Check if user is admin and remember me is not already set
                const isAdmin = result.user.profile?.role === 'admin';
                if (isAdmin && !rememberMe) {
                    console.log('🔧 Admin detected - enabling persistent session');
                    // For admins, automatically enable remember me for persistent sessions
                    try {
                        const adminResult = await apiService.login(usernameOrEmail, password, true);
                        if (adminResult.success) {
                            setUser(adminResult.user);
                            localStorage.setItem('currentUser', JSON.stringify(adminResult.user));
                            console.log('✅ Admin persistent session established');
                            return adminResult;
                        }
                    } catch (adminLoginError) {
                        console.warn('Admin persistent login failed, using normal login:', adminLoginError);
                        // Fall back to normal login result
                    }
                }

                // Always set the user (session is created on backend)
                setUser(result.user);

                // Store user in localStorage for persistence
                localStorage.setItem('currentUser', JSON.stringify(result.user));
                console.log('💾 User data stored in localStorage');

                // Check if verification is required
                if (result.verification_required) {
                    // Store verification details for the modal
                    localStorage.setItem('pendingVerification', JSON.stringify({
                        email: result.user.email,
                        verification_status: result.verification_status,
                        verification_code: result.verification_code,
                        verification_expiry: result.verification_expiry
                    }));

                    return {
                        success: true,
                        user: result.user,
                        verification_required: true,
                        verification_message: result.verification_message,
                        message: result.message
                    };
                }

                // No verification needed - normal success
                return {
                    success: true,
                    user: result.user,
                    message: result.message
                };
            }

            return { success: false, error: result.error || 'Connexion échouée' };
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: error.message || 'Erreur lors de la connexion' };
        } finally {
            setLoading(false);
        }
    };

    const signUp = async (userData) => {
        try {
            setLoading(true);

            // Transform form data to match backend expectations
            const registrationData = {
                username: userData.username,
                first_name: userData.firstName,
                last_name: userData.lastName,
                email: userData.email,
                phone_number: userData.phoneNumber,
                password: userData.password,
                password_confirm: userData.confirmPassword,
                date_of_birth: userData.birthDate,
                division_id: userData.divisionId || '',
                municipality: userData.municipality, // Keep for backward compatibility
                accept_terms: userData.acceptTerms
            };

            const result = await apiService.register(registrationData);

            if (result.success) {
                // Store email for verification process
                localStorage.setItem('pendingEmail', userData.email);

                // Don't set user as logged in - they need to verify email first
                return {
                    success: true,
                    message: result.message,
                    requiresVerification: true,
                    email: userData.email  // Toujours utiliser l'email du formulaire
                };
            }

            return { success: false, error: 'Inscription échouée' };
        } catch (error) {
            console.error('Registration error:', error);
            throw new Error(error.message || 'Erreur lors de l\'inscription');
        } finally {
            setLoading(false);
        }
    };

    const logout = async () => {
        try {
            setLoading(true);
            console.log('🚪 Starting logout process...');

            // Track logout time for smart redirect
            trackLogout();

            await apiService.logout();
            console.log('✅ Backend logout completed');
        } catch (error) {
            console.error('❌ Logout error:', error);
        } finally {
            // Clear user state and localStorage
            console.log('🧹 Clearing user state and localStorage');
            setUser(null);
            localStorage.removeItem('currentUser');
            setLoading(false);
        }
    };

    const verifyEmail = async (email, code) => {
        try {
            setLoading(true);
            const result = await apiService.verifyEmail(email, code);

            if (result.success && result.user) {
                setUser(result.user);
                localStorage.removeItem('pendingEmail');
                return { success: true, user: result.user, message: result.message };
            }

            return { success: false, error: 'Vérification échouée' };
        } catch (error) {
            console.error('Email verification error:', error);
            return { success: false, error: error.message || 'Erreur lors de la vérification' };
        } finally {
            setLoading(false);
        }
    };

    const resendVerificationCode = async (email) => {
        try {
            const result = await apiService.resendVerificationCode(email);
            return { success: true, message: result.message };
        } catch (error) {
            console.error('Resend verification error:', error);
            return { success: false, error: error.message || 'Erreur lors du renvoi du code' };
        }
    };

    const updateUser = (updatedUserData) => {
        setUser(updatedUserData);
        localStorage.setItem('currentUser', JSON.stringify(updatedUserData));
    };

    const refreshUserData = async () => {
        if (apiService.isAuthenticated()) {
            try {
                const userData = await apiService.getCurrentUser();
                setUser(userData);
                return userData;
            } catch (error) {
                console.error('Failed to refresh user data:', error);
                // If refresh fails due to auth issues, logout
                if (error.response?.status === 401) {
                    await logout();
                }
            }
        }
    };

    const checkPermission = (permission) => {
        // Basic permission checking - can be extended based on user roles
        if (!user) return false;

        // Admin can do anything
        const userRole = user.role || (user.profile && user.profile.role);
        if (userRole === 'admin') return true;

        // Add more permission logic as needed
        return user.permissions && user.permissions.includes(permission);
    };

    const isRole = (role) => {
        if (!user) return false;
        const userRole = user.role || (user.profile && user.profile.role);
        return userRole === role;
    };

    const getHomeUrl = () => {
        if (!user) return '/';

        // Redirect based on user role or municipality
        const userRole = user.role || (user.profile && user.profile.role);
        if (userRole === 'admin') return '/admin/dashboard';
        if (user.municipality) return `/municipality/${user.municipality}`;
        return '/dashboard';
    };

    const value = {
        user,
        login,
        signUp,
        logout,
        verifyEmail,
        resendVerificationCode,
        updateUser,
        refreshUserData,
        loading,
        isAuthenticated: !!user,
        checkPermission,
        isRole,
        getHomeUrl,
        // Anonymous user location data
        anonymousLocation,
        // Expose API service for other components
        apiService
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};