/**
 * Country Preference Utility
 *
 * Manages user's preferred country for browsing divisions.
 * Syncs between left menu and map page via localStorage.
 *
 * Priority:
 * 1. User's manual selection (stored in localStorage)
 * 2. User's profile country
 * 3. Default to Canada
 */

const STORAGE_KEY = 'currentBrowsingCountry';

/**
 * Get user's preferred browsing country
 * @param {object} user - User object from AuthContext
 * @returns {string} Country ISO3 code (e.g., 'CAN', 'BEN', 'FRA')
 */
export const getPreferredCountry = (user = null) => {
    // Priority 1: Check localStorage for manual selection
    const savedCountry = localStorage.getItem(STORAGE_KEY);
    if (savedCountry) {        return savedCountry;
    }

    // Priority 2: Get from user profile location
    if (user) {
        const userLocation = user?.profile?.location || '';

        // Parse country from location string
        if (userLocation.includes('Canada')) return 'CAN';
        if (userLocation.includes('Benin') || userLocation.includes('Bénin')) return 'BEN';
        if (userLocation.includes('France')) return 'FRA';

        // Check user.location object if available
        if (user?.location?.country) {
            const countryISO = user.location.country;
            if (countryISO === 'CA' || countryISO === 'CAN') return 'CAN';
            if (countryISO === 'BJ' || countryISO === 'BEN') return 'BEN';
            if (countryISO === 'FR' || countryISO === 'FRA') return 'FRA';
        }
    }

    // Priority 3: Default to Canada    return 'CAN';
};

/**
 * Set user's preferred browsing country
 * @param {string} countryCode - Country ISO3 code
 */
export const setPreferredCountry = (countryCode) => {
    if (!countryCode) {        return;
    }

    localStorage.setItem(STORAGE_KEY, countryCode);
    // Dispatch custom event so other components can react
    window.dispatchEvent(new CustomEvent('countryPreferenceChanged', {
        detail: { countryCode }
    }));
};

/**
 * Clear saved country preference (revert to user profile country)
 */
export const clearPreferredCountry = () => {
    localStorage.removeItem(STORAGE_KEY);
    window.dispatchEvent(new CustomEvent('countryPreferenceChanged', {
        detail: { countryCode: null }
    }));
};

/**
 * Check if user is browsing a different country than their profile
 * @param {object} user - User object
 * @returns {boolean}
 */
export const isBrowsingDifferentCountry = (user) => {
    if (!user) return false;

    const preferredCountry = getPreferredCountry(user);
    const profileCountry = getPreferredCountry({ ...user, profile: null }); // Get default without preference

    return preferredCountry !== profileCountry;
};

/**
 * Get human-readable country name from ISO3 code
 * @param {string} iso3 - Country ISO3 code
 * @returns {string} Country name
 */
export const getCountryName = (iso3) => {
    const countryNames = {
        'CAN': 'Canada',
        'BEN': 'Bénin',
        'FRA': 'France',
        'USA': 'États-Unis',
        'GBR': 'Royaume-Uni',
        'DEU': 'Allemagne',
        'ITA': 'Italie',
        'ESP': 'Espagne'
    };

    return countryNames[iso3] || iso3;
};

/**
 * Hook to listen for country preference changes
 * Use in components that need to react to country changes
 * @param {Function} callback - Called when country changes
 */
export const useCountryPreferenceListener = (callback) => {
    if (typeof window === 'undefined') return;

    const handleChange = (event) => {
        callback(event.detail.countryCode);
    };

    window.addEventListener('countryPreferenceChanged', handleChange);

    return () => {
        window.removeEventListener('countryPreferenceChanged', handleChange);
    };
};

export default {
    getPreferredCountry,
    setPreferredCountry,
    clearPreferredCountry,
    isBrowsingDifferentCountry,
    getCountryName,
    useCountryPreferenceListener
};
