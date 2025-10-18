/**
 * Navigation Tracker - Tracks user's page visits for smart login redirect
 *
 * Tracks:
 * - Last visited division URL
 * - Timestamp of last visit
 * - Time since logout
 *
 * Used to determine where to redirect user after login:
 * - Recent session (< 30 min) → Return to last visited page
 * - Old session (> 30 min) → Go to user's home division
 */

const STORAGE_KEYS = {
    LAST_VISITED_URL: 'lastVisitedUrl',
    LAST_VISITED_TIME: 'lastVisitedTime',
    LOGOUT_TIME: 'logoutTime',
    LAST_VISITED_DIVISION: 'lastVisitedDivision'
};

const SESSION_TIMEOUT_MINUTES = 30;

/**
 * Track current page visit
 * @param {string} url - Current URL path (e.g., '/municipality/sherbrooke/accueil')
 * @param {object} divisionData - Division data {id, name, slug, country}
 */
export const trackPageVisit = (url, divisionData = null) => {
    const currentTime = Date.now();

    localStorage.setItem(STORAGE_KEYS.LAST_VISITED_URL, url);
    localStorage.setItem(STORAGE_KEYS.LAST_VISITED_TIME, currentTime.toString());

    if (divisionData) {
        localStorage.setItem(
            STORAGE_KEYS.LAST_VISITED_DIVISION,
            JSON.stringify(divisionData)
        );
    }};

/**
 * Track logout event
 */
export const trackLogout = () => {
    const logoutTime = Date.now();
    localStorage.setItem(STORAGE_KEYS.LOGOUT_TIME, logoutTime.toString());};

/**
 * Get smart redirect URL after login
 * @param {string} userHomeDivisionUrl - User's home division URL
 * @returns {object} {url: string, reason: string}
 */
export const getSmartRedirectUrl = (userHomeDivisionUrl) => {
    const lastVisitedUrl = localStorage.getItem(STORAGE_KEYS.LAST_VISITED_URL);
    const lastVisitedTime = localStorage.getItem(STORAGE_KEYS.LAST_VISITED_TIME);
    const logoutTime = localStorage.getItem(STORAGE_KEYS.LOGOUT_TIME);

    // If no previous visit data, go home
    if (!lastVisitedUrl || !lastVisitedTime) {
        return {
            url: userHomeDivisionUrl,
            reason: 'No previous visit data - going to home division'
        };
    }

    const currentTime = Date.now();
    const lastVisitTimestamp = parseInt(lastVisitedTime);
    const logoutTimestamp = logoutTime ? parseInt(logoutTime) : lastVisitTimestamp;

    // Calculate time since logout (or last visit if no logout tracked)
    const timeSinceLogout = (currentTime - logoutTimestamp) / 1000 / 60; // minutes
    // Recent session (< 30 minutes) - continue where they left off
    if (timeSinceLogout < SESSION_TIMEOUT_MINUTES) {
        return {
            url: lastVisitedUrl,
            reason: `Recent session (${timeSinceLogout.toFixed(1)} min ago) - continuing`
        };
    }

    // Old session (> 30 minutes) - go to home division
    return {
        url: userHomeDivisionUrl,
        reason: `Old session (${timeSinceLogout.toFixed(1)} min ago) - going home`
    };
};

/**
 * Get last visited division data
 * @returns {object|null} Division data or null
 */
export const getLastVisitedDivision = () => {
    const divisionData = localStorage.getItem(STORAGE_KEYS.LAST_VISITED_DIVISION);
    if (divisionData) {
        try {
            return JSON.parse(divisionData);
        } catch (e) {
            return null;
        }
    }
    return null;
};

/**
 * Clear navigation tracking data (on logout or manual clear)
 */
export const clearNavigationTracking = () => {
    // Don't clear lastVisitedUrl and lastVisitedTime - we need them for smart redirect
    // Only clear if you want to force fresh start
};

/**
 * Clear all navigation tracking data (force reset)
 */
export const clearAllNavigationTracking = () => {
    Object.values(STORAGE_KEYS).forEach(key => {
        localStorage.removeItem(key);
    });
};

/**
 * Check if user should be redirected based on current URL
 * @param {string} currentUrl - Current URL path
 * @returns {boolean} True if should redirect
 */
export const shouldRedirectFromUrl = (currentUrl) => {
    // Redirect if on login/register/root pages
    const redirectPages = ['/', '/login', '/register', '/signup'];
    return redirectPages.includes(currentUrl) || currentUrl === '';
};
