/**
 * Utility for managing the current active division across the entire app
 * This provides a single source of truth for which division the user is currently viewing
 */

const CURRENT_DIVISION_KEY = 'currentActiveDivision';

/**
 * Get the current active division from localStorage
 * @returns {Object|null} The division object or null if not set
 */
export const getCurrentDivision = () => {
    try {
        const data = localStorage.getItem(CURRENT_DIVISION_KEY);
        if (data) {
            const division = JSON.parse(data);            return division;
        }
    } catch (error) {        localStorage.removeItem(CURRENT_DIVISION_KEY);
    }
    return null;
};

/**
 * Set the current active division in localStorage
 * This should be called whenever the user navigates to a new division
 * @param {Object} division - The division object with id, name, slug, country, etc.
 */
export const setCurrentDivision = (division) => {
    try {
        const divisionData = {
            id: division.id,
            name: division.name,
            slug: division.slug,
            country: division.country?.iso3 || division.country,
            parent: division.parent ? {
                id: division.parent.id,
                name: division.parent.name
            } : null,
            admin_level: division.admin_level,
            boundary_type: division.boundary_type,
            level_1_id: division.level_1_id || division.parent?.id,
            timestamp: Date.now()
        };

        localStorage.setItem(CURRENT_DIVISION_KEY, JSON.stringify(divisionData));        return divisionData;
    } catch (error) {        return null;
    }
};

/**
 * Clear the current active division from localStorage
 */
export const clearCurrentDivision = () => {
    localStorage.removeItem(CURRENT_DIVISION_KEY);};

/**
 * Get the slug for the current division to use in URLs
 * @returns {string|null} The slug or null
 */
export const getCurrentDivisionSlug = () => {
    const division = getCurrentDivision();
    return division?.slug || null;
};

/**
 * Check if a division is the current active one
 * @param {string} divisionId - The division ID to check
 * @returns {boolean}
 */
export const isCurrentDivision = (divisionId) => {
    const current = getCurrentDivision();
    return current?.id === divisionId;
};

/**
 * Clean up old localStorage keys from previous implementations
 */
export const cleanupOldDivisionKeys = () => {
    const oldKeys = [
        'selectedMunicipality',
        'selectedMunicipalityId',
        'lastVisitedDivision'
    ];

    // Also clean up all pageDivision_* keys since we don't need per-page storage
    const allKeys = Object.keys(localStorage);
    const pageDivisionKeys = allKeys.filter(key => key.startsWith('pageDivision_'));

    [...oldKeys, ...pageDivisionKeys].forEach(key => {
        if (localStorage.getItem(key)) {
            localStorage.removeItem(key);        }
    });
};
