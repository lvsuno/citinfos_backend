/**
 * Utility functions for managing dynamic country data and routes
 *
 * This file provides utilities for adding new countries and their administrative divisions
 * without needing to manually update routing configuration.
 */

import { ADMIN_DIVISIONS, setCurrentCountry } from './adminDivisions';

/**
 * Add a new country configuration
 * @param {string} countryCode - ISO country code (e.g., 'FR', 'DE', 'SN')
 * @param {object} config - Country configuration object
 * @returns {boolean} - Success status
 */
export const addCountryConfig = (countryCode, config) => {
  if (!countryCode || !config) {    return false;
  }

  if (!config.adminDivision?.urlPath) {    return false;
  }

  // Validate required structure
  const requiredFields = ['country', 'hasData', 'adminDivision'];
  const missingFields = requiredFields.filter(field => !config[field]);

  if (missingFields.length > 0) {    return false;
  }

  // Add to configuration
  ADMIN_DIVISIONS[countryCode] = config;
  return true;
};

/**
 * Example configurations for easy copy-paste when adding new countries
 */
export const EXAMPLE_CONFIGURATIONS = {
  // Senegal - Uses "commune" system
  'SN': {
    country: 'Senegal',
    region: null,
    hasData: true,
    dataSource: 'backend-api',
    adminDivision: {
      type: 'commune',
      plural: 'communes',
      singular: 'commune',
      urlPath: 'commune',
      labels: {
        fr: {
          singular: 'commune',
          plural: 'communes',
          preposition: 'de la',
          mapTitle: 'Carte des communes'
        },
        wo: { // Wolof
          singular: 'kommin',
          plural: 'kommin yi',
          preposition: 'ci',
          mapTitle: 'Karte kommin yi'
        }
      }
    }
  },

  // Burkina Faso - Uses "commune" system
  'BF': {
    country: 'Burkina Faso',
    region: null,
    hasData: true,
    dataSource: 'backend-api',
    adminDivision: {
      type: 'commune',
      plural: 'communes',
      singular: 'commune',
      urlPath: 'commune',
      labels: {
        fr: {
          singular: 'commune',
          plural: 'communes',
          preposition: 'de la',
          mapTitle: 'Carte des communes'
        }
      }
    }
  },

  // Germany - Uses "gemeinde" system
  'DE': {
    country: 'Germany',
    region: null,
    hasData: true,
    dataSource: 'backend-api',
    adminDivision: {
      type: 'gemeinde',
      plural: 'gemeinden',
      singular: 'gemeinde',
      urlPath: 'gemeinde',
      labels: {
        de: {
          singular: 'Gemeinde',
          plural: 'Gemeinden',
          preposition: 'der',
          mapTitle: 'Karte der Gemeinden'
        },
        en: {
          singular: 'municipality',
          plural: 'municipalities',
          preposition: 'of',
          mapTitle: 'Municipality Map'
        }
      }
    }
  }
};

/**
 * Quick setup function for common administrative division types
 */
export const addCountryWithCommonType = (countryCode, countryName, type = 'commune', hasDataInBackend = true) => {
  const commonTypes = {
    'commune': {
      type: 'commune',
      plural: 'communes',
      singular: 'commune',
      urlPath: 'commune'
    },
    'municipality': {
      type: 'municipality',
      plural: 'municipalities',
      singular: 'municipality',
      urlPath: 'municipality'
    },
    'city': {
      type: 'city',
      plural: 'cities',
      singular: 'city',
      urlPath: 'city'
    }
  };

  if (!commonTypes[type]) {    return false;
  }

  const config = {
    country: countryName,
    region: null,
    hasData: hasDataInBackend,
    dataSource: 'backend-api', // All data now comes from Django backend
    adminDivision: {
      ...commonTypes[type],
      labels: {
        fr: {
          singular: type === 'commune' ? 'commune' : type === 'city' ? 'ville' : 'municipalité',
          plural: type === 'commune' ? 'communes' : type === 'city' ? 'villes' : 'municipalités',
          preposition: 'de la',
          mapTitle: `Carte des ${type === 'commune' ? 'communes' : type === 'city' ? 'villes' : 'municipalités'}`
        }
      }
    }
  };

  return addCountryConfig(countryCode, config);
};

/**
 * Log current routing information - useful for debugging
 */
export const logCurrentRoutes = () => {
  const { getAvailableUrlPaths, getAvailableCountries } = require('./adminDivisions');  getAvailableCountries().forEach(country => {  });  getAvailableUrlPaths().forEach(path => {  });
};

/**
 * Instructions for adding new countries
 */
export const SETUP_INSTRUCTIONS = `
📋 How to Add a New Country:

1. Add administrative division data to Django backend
2. Use one of these methods:

METHOD A - Quick setup for common types:
import { addCountryWithCommonType } from './config/countryUtils';
addCountryWithCommonType('SN', 'Senegal', 'commune', true); // true = has backend data

METHOD B - Custom configuration:
import { addCountryConfig, EXAMPLE_CONFIGURATIONS } from './config/countryUtils';
addCountryConfig('SN', EXAMPLE_CONFIGURATIONS.SN);

METHOD C - Manual configuration:
Add directly to ADMIN_DIVISIONS in adminDivisions.js

3. Routes are automatically generated! No need to touch App.js
4. Test with: /{urlPath}/{slug}/accueil

🚀 That's it! The system will automatically:
- Generate new routes for backend data
- Update URL generation
- Adapt UI labels
- Support navigation

📊 All data comes from Django backend API now!
`;

export default {
  addCountryConfig,
  addCountryWithCommonType,
  EXAMPLE_CONFIGURATIONS,
  logCurrentRoutes,
  SETUP_INSTRUCTIONS
};