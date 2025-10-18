/**
 * Authentication Debugger Utility
 *
 * This utility helps debug authentication state issues during development.
 * Add this to your browser console or call from React components.
 */

export const authDebugger = {
    // Check current authentication state
    checkAuthState() {
        const tokens = {
            access: localStorage.getItem('access_token'),
            refresh: localStorage.getItem('refresh_token')
        };

        const savedUser = localStorage.getItem('currentUser');
        let parsedUser = null;

        try {
            parsedUser = savedUser ? JSON.parse(savedUser) : null;
        } catch (error) {        }

        const report = {
            hasAccessToken: !!tokens.access,
            hasRefreshToken: !!tokens.refresh,
            accessTokenLength: tokens.access?.length || 0,
            hasSavedUser: !!savedUser,
            savedUserData: parsedUser,
            timestamp: new Date().toISOString()
        };

        console.group('🔍 Authentication State Report');
        console.table(report);

        if (tokens.access) {        }

        if (parsedUser) {        }

        console.groupEnd();
        return report;
    },

    // Clear all authentication data
    clearAuthData() {        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('currentUser');
        localStorage.removeItem('pendingVerification');    },

    // Simulate authentication recovery
    async testAuthRecovery() {
        // Import apiService dynamically to avoid circular dependencies
        const { default: apiService } = await import('../services/apiService');

        if (!apiService.isAuthenticated()) {            return;
        }

        try {
            const userData = await apiService.getCurrentUser();            localStorage.setItem('currentUser', JSON.stringify(userData));
            return userData;
        } catch (error) {            return null;
        }
    },

    // Monitor localStorage changes
    startMonitoring() {
        const originalSetItem = localStorage.setItem;
        const originalRemoveItem = localStorage.removeItem;
        const originalClear = localStorage.clear;

        localStorage.setItem = function(key, value) {
            if (['access_token', 'refresh_token', 'currentUser'].includes(key)) {            }
            return originalSetItem.apply(this, arguments);
        };

        localStorage.removeItem = function(key) {
            if (['access_token', 'refresh_token', 'currentUser'].includes(key)) {            }
            return originalRemoveItem.apply(this, arguments);
        };

        localStorage.clear = function() {            return originalClear.apply(this, arguments);
        };

        // Store original functions to restore later
        window._originalLocalStorage = {
            setItem: originalSetItem,
            removeItem: originalRemoveItem,
            clear: originalClear
        };    },

    // Stop monitoring localStorage changes
    stopMonitoring() {
        if (window._originalLocalStorage) {
            localStorage.setItem = window._originalLocalStorage.setItem;
            localStorage.removeItem = window._originalLocalStorage.removeItem;
            localStorage.clear = window._originalLocalStorage.clear;
            delete window._originalLocalStorage;        }
    },

    // Log current browser storage usage
    getStorageInfo() {
        const storage = {};
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            const value = localStorage.getItem(key);
            storage[key] = {
                type: typeof value,
                length: value?.length || 0,
                preview: typeof value === 'string' ? value.substring(0, 100) : value
            };
        }

        console.group('💾 Current localStorage Contents');
        console.table(storage);
        console.groupEnd();

        return storage;
    }
};

// Make it available globally in development
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
    window.authDebugger = authDebugger;}

export default authDebugger;