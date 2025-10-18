/**
 * Phone Number Validation Utilities
 * Uses libphonenumber-js for international phone number validation
 */

import { parsePhoneNumber, isValidPhoneNumber, getCountries } from 'libphonenumber-js';

/**
 * Validate a phone number for a specific country
 * @param {string} phoneNumber - The phone number to validate
 * @param {string} countryCode - ISO 3166-1 alpha-2 country code (e.g., 'CA', 'US', 'FR')
 * @returns {Object} Validation result with details
 */
export const validatePhoneNumber = (phoneNumber, countryCode = null) => {
    if (!phoneNumber || typeof phoneNumber !== 'string') {
        return {
            valid: false,
            error: 'Le numéro de téléphone est requis',
            formatted: null,
            national: null,
            international: null,
            countryCode: null,
        };
    }

    try {
        // Check if it's a valid number (with or without country code)
        const isValid = countryCode
            ? isValidPhoneNumber(phoneNumber, countryCode)
            : isValidPhoneNumber(phoneNumber);

        if (!isValid) {
            return {
                valid: false,
                error: 'Format de numéro de téléphone invalide',
                formatted: null,
                national: null,
                international: null,
                countryCode: countryCode,
            };
        }

        // Parse with original country code to preserve user's selection
        const parsed = countryCode
            ? parsePhoneNumber(phoneNumber, countryCode)
            : parsePhoneNumber(phoneNumber);

        if (!parsed) {
            return {
                valid: false,
                error: 'Impossible d\'analyser le numéro de téléphone',
                formatted: null,
                national: null,
                international: null,
                countryCode: countryCode,
            };
        }

        // Return detailed information
        return {
            valid: true,
            error: null,
            formatted: parsed.formatInternational(), // +1 514 123 4567
            national: parsed.formatNational(),       // (514) 123-4567
            international: parsed.number,            // +15141234567
            countryCode: parsed.country,             // CA
            nationalNumber: parsed.nationalNumber,   // 5141234567
            isValid: parsed.isValid(),
            isPossible: parsed.isPossible(),
            type: parsed.getType(),                  // MOBILE, FIXED_LINE, etc.
        };
    } catch (error) {
        return {
            valid: false,
            error: error.message || 'Erreur lors de la validation du numéro',
            formatted: null,
            national: null,
            international: null,
            countryCode: countryCode,
        };
    }
};

/**
 * Format a phone number for display
 * @param {string} phoneNumber - The phone number to format
 * @param {string} countryCode - ISO 3166-1 alpha-2 country code
 * @param {string} format - Format type: 'international', 'national', or 'e164'
 * @returns {string} Formatted phone number or original input if invalid
 */
export const formatPhoneNumber = (phoneNumber, countryCode = null, format = 'international') => {
    try {
        const parsed = countryCode
            ? parsePhoneNumber(phoneNumber, countryCode)
            : parsePhoneNumber(phoneNumber);

        if (!parsed) return phoneNumber;

        switch (format) {
            case 'international':
                return parsed.formatInternational(); // +1 514 123 4567
            case 'national':
                return parsed.formatNational();      // (514) 123-4567
            case 'e164':
                return parsed.format('E.164');       // +15141234567
            case 'uri':
                return parsed.getURI();              // tel:+15141234567
            default:
                return parsed.formatInternational();
        }
    } catch (error) {
        return phoneNumber; // Return original if parsing fails
    }
};

/**
 * Get example phone number for a country
 * @param {string} countryCode - ISO 3166-1 alpha-2 country code
 * @param {string} type - Type of number: 'MOBILE', 'FIXED_LINE', etc.
 * @returns {string} Example phone number
 */
export const getExampleNumber = (countryCode, type = 'MOBILE') => {
    try {
        const { getExampleNumber: getExample } = require('libphonenumber-js/examples.mobile.json');
        const exampleNumber = getExample(countryCode, type);
        return exampleNumber ? exampleNumber.formatInternational() : '';
    } catch (error) {
        // Fallback examples for common countries
        const examples = {
            CA: '+1 514 555 0199',
            US: '+1 202 555 0123',
            FR: '+33 6 12 34 56 78',
            GB: '+44 7911 123456',
            DE: '+49 151 12345678',
            BJ: '+229 97 12 34 56',
        };
        return examples[countryCode] || '';
    }
};

/**
 * Get list of all supported countries
 * @returns {Array} Array of country codes
 */
export const getSupportedCountries = () => {
    return getCountries();
};

/**
 * Get country code from phone number
 * @param {string} phoneNumber - The phone number
 * @returns {string|null} Country code or null
 */
export const getCountryFromNumber = (phoneNumber) => {
    try {
        const parsed = parsePhoneNumber(phoneNumber);
        return parsed ? parsed.country : null;
    } catch (error) {
        return null;
    }
};

/**
 * Check if a phone number is mobile
 * @param {string} phoneNumber - The phone number
 * @param {string} countryCode - ISO 3166-1 alpha-2 country code
 * @returns {boolean} True if mobile number
 */
export const isMobileNumber = (phoneNumber, countryCode = null) => {
    try {
        const parsed = countryCode
            ? parsePhoneNumber(phoneNumber, countryCode)
            : parsePhoneNumber(phoneNumber);

        if (!parsed) return false;

        const type = parsed.getType();
        return type === 'MOBILE' || type === 'FIXED_LINE_OR_MOBILE';
    } catch (error) {
        return false;
    }
};

/**
 * Real-time phone input formatter
 * Formats as the user types
 * @param {string} value - Current input value
 * @param {string} countryCode - ISO 3166-1 alpha-2 country code
 * @returns {string} Formatted value for display
 */
export const formatAsYouType = (value, countryCode = null) => {
    try {
        const { AsYouType } = require('libphonenumber-js');
        const formatter = new AsYouType(countryCode);
        return formatter.input(value);
    } catch (error) {
        return value;
    }
};

// =============================================================================
// HARDCODED COUNTRY DATA REMOVED
// =============================================================================
// The following have been removed from this file:
// - COUNTRY_PHONE_CODES array (120+ countries)
// - ISO3_TO_ISO2_MAP object
// - convertISO3ToISO2() function
//
// WHY? Country data is now fetched from the backend API which provides:
// - 242 countries (vs 120 hardcoded here)
// - Auto-detection based on IP geolocation
// - Search functionality across all countries
// - Regional country grouping
// - Single source of truth for country data
// - Easier maintenance and updates
//
// HOW TO GET COUNTRY DATA NOW:
// ```javascript
// import countryService from '../services/countryService';
//
// // Get user's detected country + regional countries
// const data = await countryService.getUserLocationData();
// // { iso2: 'CA', name: 'Canada', phone_code: '+1', ... }
//
// // Search for countries
// const results = await countryService.searchCountries('france');
//
// // Get all countries
// const all = await countryService.getAllCountries();
// ```
//
// SEE DOCUMENTATION:
// - FRONTEND_COUNTRY_PHONE_INTEGRATION.md - Full implementation guide
// - src/services/countryService.js - Frontend API client
// - src/components/EnhancedCountryPhoneInput.js - Example usage
// - accounts/views.py - Backend API endpoints
// =============================================================================

/**
 * Export all validation functions
 * NOTE: COUNTRY_PHONE_CODES and ISO3_TO_ISO2_MAP exports have been removed!
 * Country data is now fetched from backend API via countryService.js
 */
export default {
    validatePhoneNumber,
    formatPhoneNumber,
    getExampleNumber,
    getSupportedCountries,
    getCountryFromNumber,
    isMobileNumber,
    formatAsYouType,
};
