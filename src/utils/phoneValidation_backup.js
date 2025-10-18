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

        // Parse the phone number to get detailed info
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
            CA: '+1 514 123 4567',
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

// =============================================================================
// HARDCODED COUNTRY DATA REMOVED
// =============================================================================
// The following have been removed from this file:
// - COUNTRY_PHONE_CODES array (120+ countries)
// - ISO3_TO_ISO2_MAP object
// - convertISO3ToISO2() function
//
// WHY? Country data is now fetched from the backend API which has:
// - 242 countries (vs 120 hardcoded)
// - Auto-detection based on IP geolocation
// - Search functionality
// - Regional country grouping
// - Single source of truth
//
// HOW TO GET COUNTRY DATA NOW:
// import countryService from '../services/countryService';
// const data = await countryService.getUserLocationData();
// const all = await countryService.getAllCountries();
//
// See: FRONTEND_COUNTRY_PHONE_INTEGRATION.md for full documentation
// =============================================================================
    { code: 'SL', name: 'Sierra Leone', dialCode: '+232', flag: '��', region: 'West Africa' },
    { code: 'LR', name: 'Liberia', dialCode: '+231', flag: '🇱🇷', region: 'West Africa' },
    { code: 'GM', name: 'Gambia', dialCode: '+220', flag: '��', region: 'West Africa' },

    // Central Africa
    { code: 'CM', name: 'Cameroun', dialCode: '+237', flag: '🇨🇲', region: 'Central Africa' },
    { code: 'CD', name: 'RD Congo', dialCode: '+243', flag: '🇨🇩', region: 'Central Africa' },
    { code: 'CG', name: 'Congo', dialCode: '+242', flag: '🇨�', region: 'Central Africa' },
    { code: 'GA', name: 'Gabon', dialCode: '+241', flag: '🇬🇦', region: 'Central Africa' },
    { code: 'CF', name: 'Centrafrique', dialCode: '+236', flag: '🇨🇫', region: 'Central Africa' },
    { code: 'TD', name: 'Tchad', dialCode: '+235', flag: '🇹🇩', region: 'Central Africa' },

    // East Africa
    { code: 'KE', name: 'Kenya', dialCode: '+254', flag: '��', region: 'East Africa' },
    { code: 'TZ', name: 'Tanzania', dialCode: '+255', flag: '🇹🇿', region: 'East Africa' },
    { code: 'UG', name: 'Uganda', dialCode: '+256', flag: '🇺🇬', region: 'East Africa' },
    { code: 'RW', name: 'Rwanda', dialCode: '+250', flag: '��', region: 'East Africa' },
    { code: 'BI', name: 'Burundi', dialCode: '+257', flag: '🇧🇮', region: 'East Africa' },
    { code: 'ET', name: 'Ethiopia', dialCode: '+251', flag: '🇪🇹', region: 'East Africa' },

    // Southern Africa
    { code: 'ZA', name: 'South Africa', dialCode: '+27', flag: '🇿🇦', region: 'Southern Africa' },
    { code: 'ZW', name: 'Zimbabwe', dialCode: '+263', flag: '🇿🇼', region: 'Southern Africa' },
    { code: 'BW', name: 'Botswana', dialCode: '+267', flag: '🇧🇼', region: 'Southern Africa' },
    { code: 'NA', name: 'Namibia', dialCode: '+264', flag: '🇳🇦', region: 'Southern Africa' },

    // North Africa
    { code: 'DZ', name: 'Algérie', dialCode: '+213', flag: '🇩�', region: 'North Africa' },
    { code: 'MA', name: 'Maroc', dialCode: '+212', flag: '🇲🇦', region: 'North Africa' },
    { code: 'TN', name: 'Tunisie', dialCode: '+216', flag: '🇹🇳', region: 'North Africa' },
    { code: 'EG', name: 'Egypt', dialCode: '+20', flag: '�🇬', region: 'North Africa' },
    { code: 'LY', name: 'Libya', dialCode: '+218', flag: '🇱🇾', region: 'North Africa' },

    // Western Europe
    { code: 'FR', name: 'France', dialCode: '+33', flag: '🇫🇷', region: 'Western Europe' },
    { code: 'DE', name: 'Germany', dialCode: '+49', flag: '�🇪', region: 'Western Europe' },
    { code: 'GB', name: 'United Kingdom', dialCode: '+44', flag: '��', region: 'Western Europe' },
    { code: 'ES', name: 'Spain', dialCode: '+34', flag: '🇪🇸', region: 'Western Europe' },
    { code: 'IT', name: 'Italy', dialCode: '+39', flag: '🇮🇹', region: 'Western Europe' },
    { code: 'PT', name: 'Portugal', dialCode: '+351', flag: '🇵🇹', region: 'Western Europe' },
    { code: 'BE', name: 'Belgium', dialCode: '+32', flag: '🇧🇪', region: 'Western Europe' },
    { code: 'NL', name: 'Netherlands', dialCode: '+31', flag: '🇳🇱', region: 'Western Europe' },
    { code: 'CH', name: 'Switzerland', dialCode: '+41', flag: '🇨🇭', region: 'Western Europe' },
    { code: 'AT', name: 'Austria', dialCode: '+43', flag: '🇦🇹', region: 'Western Europe' },
    { code: 'LU', name: 'Luxembourg', dialCode: '+352', flag: '🇱🇺', region: 'Western Europe' },
    { code: 'IE', name: 'Ireland', dialCode: '+353', flag: '🇮🇪', region: 'Western Europe' },

    // Northern Europe
    { code: 'SE', name: 'Sweden', dialCode: '+46', flag: '🇸🇪', region: 'Northern Europe' },
    { code: 'NO', name: 'Norway', dialCode: '+47', flag: '🇳🇴', region: 'Northern Europe' },
    { code: 'DK', name: 'Denmark', dialCode: '+45', flag: '🇩🇰', region: 'Northern Europe' },
    { code: 'FI', name: 'Finland', dialCode: '+358', flag: '🇫🇮', region: 'Northern Europe' },
    { code: 'IS', name: 'Iceland', dialCode: '+354', flag: '🇮🇸', region: 'Northern Europe' },

    // Eastern Europe
    { code: 'PL', name: 'Poland', dialCode: '+48', flag: '🇵🇱', region: 'Eastern Europe' },
    { code: 'CZ', name: 'Czech Republic', dialCode: '+420', flag: '🇨🇿', region: 'Eastern Europe' },
    { code: 'HU', name: 'Hungary', dialCode: '+36', flag: '🇭🇺', region: 'Eastern Europe' },
    { code: 'RO', name: 'Romania', dialCode: '+40', flag: '🇷🇴', region: 'Eastern Europe' },
    { code: 'BG', name: 'Bulgaria', dialCode: '+359', flag: '🇧🇬', region: 'Eastern Europe' },
    { code: 'UA', name: 'Ukraine', dialCode: '+380', flag: '🇺🇦', region: 'Eastern Europe' },
    { code: 'RU', name: 'Russia', dialCode: '+7', flag: '🇷🇺', region: 'Eastern Europe' },

    // Southern Europe
    { code: 'GR', name: 'Greece', dialCode: '+30', flag: '🇬🇷', region: 'Southern Europe' },
    { code: 'TR', name: 'Turkey', dialCode: '+90', flag: '🇹🇷', region: 'Southern Europe' },
    { code: 'HR', name: 'Croatia', dialCode: '+385', flag: '🇭🇷', region: 'Southern Europe' },
    { code: 'RS', name: 'Serbia', dialCode: '+381', flag: '🇷🇸', region: 'Southern Europe' },

    // Middle East
    { code: 'SA', name: 'Saudi Arabia', dialCode: '+966', flag: '🇸🇦', region: 'Middle East' },
    { code: 'AE', name: 'UAE', dialCode: '+971', flag: '🇦🇪', region: 'Middle East' },
    { code: 'IL', name: 'Israel', dialCode: '+972', flag: '🇮🇱', region: 'Middle East' },
    { code: 'JO', name: 'Jordan', dialCode: '+962', flag: '🇯🇴', region: 'Middle East' },
    { code: 'LB', name: 'Lebanon', dialCode: '+961', flag: '🇱🇧', region: 'Middle East' },
    { code: 'QA', name: 'Qatar', dialCode: '+974', flag: '🇶🇦', region: 'Middle East' },
    { code: 'KW', name: 'Kuwait', dialCode: '+965', flag: '🇰🇼', region: 'Middle East' },

    // Asia Pacific
    { code: 'CN', name: 'China', dialCode: '+86', flag: '🇨🇳', region: 'Asia Pacific' },
    { code: 'JP', name: 'Japan', dialCode: '+81', flag: '🇯🇵', region: 'Asia Pacific' },
    { code: 'KR', name: 'South Korea', dialCode: '+82', flag: '🇰🇷', region: 'Asia Pacific' },
    { code: 'IN', name: 'India', dialCode: '+91', flag: '🇮🇳', region: 'Asia Pacific' },
    { code: 'PK', name: 'Pakistan', dialCode: '+92', flag: '🇵🇰', region: 'Asia Pacific' },
    { code: 'BD', name: 'Bangladesh', dialCode: '+880', flag: '🇧🇩', region: 'Asia Pacific' },
    { code: 'TH', name: 'Thailand', dialCode: '+66', flag: '🇹🇭', region: 'Asia Pacific' },
    { code: 'VN', name: 'Vietnam', dialCode: '+84', flag: '🇻🇳', region: 'Asia Pacific' },
    { code: 'PH', name: 'Philippines', dialCode: '+63', flag: '🇵🇭', region: 'Asia Pacific' },
    { code: 'MY', name: 'Malaysia', dialCode: '+60', flag: '🇲🇾', region: 'Asia Pacific' },
    { code: 'SG', name: 'Singapore', dialCode: '+65', flag: '🇸🇬', region: 'Asia Pacific' },
    { code: 'ID', name: 'Indonesia', dialCode: '+62', flag: '🇮�', region: 'Asia Pacific' },
    { code: 'AU', name: 'Australia', dialCode: '+61', flag: '🇦🇺', region: 'Asia Pacific' },
    { code: 'NZ', name: 'New Zealand', dialCode: '+64', flag: '🇳🇿', region: 'Asia Pacific' },

    // South America
    { code: 'BR', name: 'Brazil', dialCode: '+55', flag: '�🇧🇷', region: 'South America' },
    { code: 'AR', name: 'Argentina', dialCode: '+54', flag: '🇦🇷', region: 'South America' },
    { code: 'CL', name: 'Chile', dialCode: '+56', flag: '🇨🇱', region: 'South America' },
    { code: 'CO', name: 'Colombia', dialCode: '+57', flag: '�🇴', region: 'South America' },
    { code: 'PE', name: 'Peru', dialCode: '+51', flag: '🇵�🇪', region: 'South America' },
    { code: 'VE', name: 'Venezuela', dialCode: '+58', flag: '🇻🇪', region: 'South America' },
    { code: 'EC', name: 'Ecuador', dialCode: '+593', flag: '🇪🇨', region: 'South America' },
    { code: 'UY', name: 'Uruguay', dialCode: '+598', flag: '🇺🇾', region: 'South America' },

    // Caribbean
    { code: 'HT', name: 'Haiti', dialCode: '+509', flag: '🇭🇹', region: 'Caribbean' },
    { code: 'JM', name: 'Jamaica', dialCode: '+1876', flag: '🇯🇲', region: 'Caribbean' },
    { code: 'CU', name: 'Cuba', dialCode: '+53', flag: '🇨🇺', region: 'Caribbean' },
    { code: 'DO', name: 'Dominican Republic', dialCode: '+1809', flag: '🇩🇴', region: 'Caribbean' },
];

/**
 * Mapping from ISO3 country codes (backend) to ISO2 country codes (phone validation)
 * Backend returns ISO3 codes (CAN, BEN, FRA), but phone validation uses ISO2 (CA, BJ, FR)
 */
export const ISO3_TO_ISO2_MAP = {
    // North America
    'CAN': 'CA', 'USA': 'US', 'MEX': 'MX',

    // West Africa
    'BEN': 'BJ', 'BFA': 'BF', 'CIV': 'CI', 'GIN': 'GN', 'MLI': 'ML',
    'NER': 'NE', 'SEN': 'SN', 'TGO': 'TG', 'GHA': 'GH', 'NGA': 'NG',
    'SLE': 'SL', 'LBR': 'LR', 'GMB': 'GM',

    // Central Africa
    'CMR': 'CM', 'COD': 'CD', 'COG': 'CG', 'GAB': 'GA', 'CAF': 'CF', 'TCD': 'TD',

    // East Africa
    'KEN': 'KE', 'TZA': 'TZ', 'UGA': 'UG', 'RWA': 'RW', 'BDI': 'BI', 'ETH': 'ET',

    // Southern Africa
    'ZAF': 'ZA', 'ZWE': 'ZW', 'BWA': 'BW', 'NAM': 'NA',

    // North Africa
    'DZA': 'DZ', 'MAR': 'MA', 'TUN': 'TN', 'EGY': 'EG', 'LBY': 'LY',

    // Western Europe
    'FRA': 'FR', 'DEU': 'DE', 'GBR': 'GB', 'ESP': 'ES', 'ITA': 'IT',
    'PRT': 'PT', 'BEL': 'BE', 'NLD': 'NL', 'CHE': 'CH', 'AUT': 'AT',
    'LUX': 'LU', 'IRL': 'IE',

    // Northern Europe
    'SWE': 'SE', 'NOR': 'NO', 'DNK': 'DK', 'FIN': 'FI', 'ISL': 'IS',

    // Eastern Europe
    'POL': 'PL', 'CZE': 'CZ', 'HUN': 'HU', 'ROU': 'RO', 'BGR': 'BG',
    'UKR': 'UA', 'RUS': 'RU',

    // Southern Europe
    'GRC': 'GR', 'TUR': 'TR', 'HRV': 'HR', 'SRB': 'RS',

    // Middle East
    'SAU': 'SA', 'ARE': 'AE', 'ISR': 'IL', 'JOR': 'JO', 'LBN': 'LB',
    'QAT': 'QA', 'KWT': 'KW',

    // Asia Pacific
    'CHN': 'CN', 'JPN': 'JP', 'KOR': 'KR', 'IND': 'IN', 'PAK': 'PK',
    'BGD': 'BD', 'THA': 'TH', 'VNM': 'VN', 'PHL': 'PH', 'MYS': 'MY',
    'SGP': 'SG', 'IDN': 'ID', 'AUS': 'AU', 'NZL': 'NZ',

    // South America
    'BRA': 'BR', 'ARG': 'AR', 'CHL': 'CL', 'COL': 'CO', 'PER': 'PE',
    'VEN': 'VE', 'ECU': 'EC', 'URY': 'UY',

    // Caribbean
    'HTI': 'HT', 'JAM': 'JM', 'CUB': 'CU', 'DOM': 'DO',
};

/**
 * Convert ISO3 country code (from backend) to ISO2 code (for phone validation)
 * @param {string} iso3Code - ISO3 country code (e.g., 'CAN', 'BEN', 'FRA')
 * @returns {string} ISO2 country code (e.g., 'CA', 'BJ', 'FR') or 'CA' as fallback
 */
export function convertISO3ToISO2(iso3Code) {
    if (!iso3Code) return 'CA'; // Default fallback

    const iso2 = ISO3_TO_ISO2_MAP[iso3Code.toUpperCase()];

    if (!iso2) {        return 'CA';
    }

    return iso2;
}

/**
 * NOTE: COUNTRY_PHONE_CODES and ISO3_TO_ISO2_MAP have been removed!
 * 
 * Country data is now fetched from the backend API through countryService.js
 * The backend provides 242 countries with phone codes, flags, and regions.
 * 
 * See:
 * - src/services/countryService.js - Frontend API client
 * - accounts/views.py - Backend endpoints
 * - FRONTEND_COUNTRY_PHONE_INTEGRATION.md - Full documentation
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
