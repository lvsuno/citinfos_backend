/**
 * Configuration for administrative divisions by country/region
 * This allows the application to adapt URLs and terminology based on the geographical context
 */

export const ADMIN_DIVISIONS = {
  // Canada/Quebec - Uses "municipality" system (DATA AVAILABLE)
  'CA': {
    country: 'Canada',
    region: 'Quebec',
    hasData: true, // We have Quebec municipalities data
    dataSource: 'backend-api', // Data comes from Django backend
    adminDivision: {
      type: 'municipality',
      plural: 'municipalities',
      singular: 'municipality',
      urlPath: 'municipality',
      labels: {
        fr: {
          singular: 'municipalité',
          plural: 'municipalités',
          preposition: 'de la',
          mapTitle: 'Carte des municipalités'
        },
        en: {
          singular: 'municipality',
          plural: 'municipalities',
          preposition: 'of',
          mapTitle: 'Municipality Map'
        }
      }
    }
  },

  // Benin - Uses "commune" system (DATA AVAILABLE)
  'BJ': {
    country: 'Benin',
    region: null,
    hasData: true, // We have Benin communes data
    dataSource: 'backend-api', // Data comes from Django backend
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
        en: {
          singular: 'commune',
          plural: 'communes',
          preposition: 'of',
          mapTitle: 'Commune Map'
        }
      }
    }
  }

  // Future countries will be added here as data becomes available
  // Each new country will automatically generate its own routes
};

/**
 * Get the current country code - can be determined by:
 * - User location/IP
 * - Municipality data source
 * - Manual configuration
 * - Default fallback
 */
export const getCurrentCountryCode = () => {
  // For now, we'll default to Canada since we're using Quebec municipalities
  // In the future, this could be determined by:
  // 1. User's IP geolocation
  // 2. Municipality data source
  // 3. User preference settings
  // 4. Environment variables

  const savedCountry = localStorage.getItem('selectedCountry');
  if (savedCountry && ADMIN_DIVISIONS[savedCountry]) {
    return savedCountry;
  }

  return 'CA'; // Default to Canada
};

/**
 * Get administrative division configuration for current context
 */
export const getCurrentAdminDivision = () => {
  const countryCode = getCurrentCountryCode();
  return ADMIN_DIVISIONS[countryCode] || ADMIN_DIVISIONS['CA'];
};

/**
 * Get the URL path for administrative divisions (municipality, commune, etc.)
 */
export const getAdminDivisionUrlPath = () => {
  const adminDivision = getCurrentAdminDivision();
  return adminDivision.adminDivision.urlPath;
};

/**
 * Get localized labels for administrative divisions
 */
export const getAdminDivisionLabels = (language = 'fr') => {
  const adminDivision = getCurrentAdminDivision();
  return adminDivision.adminDivision.labels[language] || adminDivision.adminDivision.labels['fr'];
};

/**
 * Set the current country context
 */
export const setCurrentCountry = (countryCode) => {
  if (ADMIN_DIVISIONS[countryCode]) {
    localStorage.setItem('selectedCountry', countryCode);
    return true;
  }
  return false;
};

/**
 * Get all available countries/regions with data
 */
export const getAvailableCountries = () => {
  return Object.entries(ADMIN_DIVISIONS)
    .filter(([code, config]) => config.hasData) // Only countries with actual data
    .map(([code, config]) => ({
      code,
      name: config.country,
      region: config.region,
      adminType: config.adminDivision.type,
      urlPath: config.adminDivision.urlPath,
      dataSource: config.dataSource
    }));
};

/**
 * Get all unique URL paths from countries with data
 * This is used for dynamic route generation
 */
export const getAvailableUrlPaths = () => {
  const countries = getAvailableCountries();
  const urlPaths = [...new Set(countries.map(country => country.urlPath))];
  return urlPaths;
};

/**
 * Check if a URL path is valid (supported by available data)
 */
export const isValidUrlPath = (urlPath) => {
  const availablePaths = getAvailableUrlPaths();
  return availablePaths.includes(urlPath);
};

/**
 * Get country configuration by URL path
 */
export const getCountryByUrlPath = (urlPath) => {
  return Object.entries(ADMIN_DIVISIONS)
    .find(([code, config]) => config.hasData && config.adminDivision.urlPath === urlPath)?.[1] || null;
};

/**
 * Get country ISO3 code by URL path
 * Maps URL paths like 'municipality' -> 'CAN', 'commune' -> 'BEN'
 */
export const getCountryISO3ByUrlPath = (urlPath) => {
  // Map ISO2 codes to ISO3
  const iso2ToISO3 = {
    'CA': 'CAN',
    'BJ': 'BEN',
    'US': 'USA',
    'FR': 'FRA'
  };

  const entry = Object.entries(ADMIN_DIVISIONS)
    .find(([code, config]) => config.hasData && config.adminDivision.urlPath === urlPath);

  if (entry) {
    const [iso2Code] = entry;
    return iso2ToISO3[iso2Code] || iso2Code;
  }

  return null;
};

/**
 * Get URL path by ISO3 country code
 * Maps ISO3 codes like 'CAN' -> 'municipality', 'BEN' -> 'commune'
 */
export const getUrlPathByISO3 = (iso3Code) => {
  // Map ISO3 codes to ISO2
  const iso3ToISO2 = {
    'CAN': 'CA',
    'BEN': 'BJ',
    'USA': 'US',
    'FRA': 'FR'
  };

  const iso2Code = iso3ToISO2[iso3Code];
  if (!iso2Code) {    return 'municipality'; // Default fallback
  }

  const config = ADMIN_DIVISIONS[iso2Code];
  if (config && config.hasData) {
    return config.adminDivision.urlPath;
  }

  return 'municipality'; // Default fallback
};