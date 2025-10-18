/**
 * Utility to get the default division URL for redirection
 * Users should ALWAYS be redirected to a division page, never to a generic dashboard
 */

import { getCurrentDivision } from './divisionStorage';
import { getAdminDivisionUrlPath } from '../config/adminDivisions';
import geolocationService from '../services/geolocationService';

/**
 * Get the default division URL to redirect to
 * Priority:
 * 1. Current division from localStorage
 * 2. User's profile location
 * 3. Anonymous location from IP
 * 4. Default division (Sherbrooke, Canada)
 *
 * @param {object} user - The authenticated user object (optional)
 * @param {object} anonymousLocation - Location detected from IP (optional)
 * @returns {Promise<string>} - URL to redirect to (e.g., /municipality/sherbrooke/accueil)
 */
export const getDefaultDivisionUrl = async (user = null, anonymousLocation = null) => {
    // PRIORITY 1: Check if there's a current division in localStorage
    const currentDivision = getCurrentDivision();
    if (currentDivision?.slug && currentDivision?.country) {
        // Map country ISO3 to URL path
        const iso3ToUrlPath = {
            'CAN': 'municipality',
            'BEN': 'commune',
            'USA': 'city',
            'FRA': 'commune'
        };

        const urlPath = iso3ToUrlPath[currentDivision.country] || getAdminDivisionUrlPath();
        return `/${urlPath}/${currentDivision.slug}/accueil`;
    }

    // PRIORITY 2: Use user's location if authenticated
    if (user?.location?.city && user?.location?.division_id) {
        // Fetch division data to get slug
        try {
            const result = await geolocationService.getDivisionById(user.location.division_id);
            if (result.success && result.division) {
                const slug = result.division.slug || slugify(result.division.name);
                const country = result.division.country?.iso3 || user.location.country;

                const iso3ToUrlPath = {
                    'CAN': 'municipality',
                    'BEN': 'commune',
                    'USA': 'city',
                    'FRA': 'commune'
                };

                const urlPath = iso3ToUrlPath[country] || getAdminDivisionUrlPath();
                return `/${urlPath}/${slug}/accueil`;
            }
        } catch (error) {        }
    }

    // PRIORITY 3: Use anonymous location from IP
    if (anonymousLocation?.location?.division_name && anonymousLocation?.location?.administrative_division_id) {
        try {
            const result = await geolocationService.getDivisionById(anonymousLocation.location.administrative_division_id);
            if (result.success && result.division) {
                const slug = result.division.slug || slugify(result.division.name);
                const country = result.division.country?.iso3 || anonymousLocation.country?.iso3;

                const iso3ToUrlPath = {
                    'CAN': 'municipality',
                    'BEN': 'commune',
                    'USA': 'city',
                    'FRA': 'commune'
                };

                const urlPath = iso3ToUrlPath[country] || getAdminDivisionUrlPath();
                return `/${urlPath}/${slug}/accueil`;
            }
        } catch (error) {        }
    }

    // PRIORITY 4: Default to Sherbrooke, Canada    return '/municipality/sherbrooke/accueil';
};

/**
 * Helper function to create URL-friendly slug from division name
 */
const slugify = (name) => {
    return name
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '') // Remove accents
        .replace(/[^a-z0-9]/g, '-') // Replace special chars with hyphens
        .replace(/-+/g, '-') // Replace multiple hyphens with single
        .replace(/^-|-$/g, ''); // Remove leading/trailing hyphens
};
