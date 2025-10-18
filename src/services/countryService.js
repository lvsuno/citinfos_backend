/**
 * Country Service for phone data, country selection, and regional filtering
 * Used primarily for signup page country/phone selection
 */

import apiService from './apiService';

class CountryService {
  /**
   * Get user's location data with detected country and regional countries
   * @param {string} ipAddress - Optional IP address, backend will detect if not provided
   * @returns {Promise<Object>} Location data with country phone data and regional countries
   */
  async getUserLocationData(ipAddress = null) {
    try {
      const response = await apiService.post('/auth/location-data/', {
        ip_address: ipAddress
      });

      const data = response.data;

      if (data.success) {
        // Important: Return the exact structure the component expects
        return {
          success: true,
          country: data.country, // Includes phone_code, flag_emoji, region, iso2, iso3, name
          userLocation: data.user_location,
          closestDivisions: data.closest_divisions,
          regional_countries: data.regional_countries || [], // Keep underscore to match backend
          countrySearchInfo: data.country_search_info
        };
      } else {
        return {
          success: false,
          error: data.error,
          fallback: data.fallback,
          message: data.message
        };
      }
    } catch (error) {      return {
        success: false,
        error: 'Failed to get location data',
        message: 'Unable to detect your location. Please select manually.'
      };
    }
  }

  /**
   * Search countries by name, ISO2, or ISO3 code
   * @param {string} query - Search query (minimum 2 characters recommended)
   * @returns {Promise<Object>} Countries matching search query
   */
  async searchCountries(query) {
    try {
      const response = await apiService.get('/auth/countries/phone-data/', {
        params: { search: query }
      });

      const data = response.data;

      if (data.success) {        return {
          success: true,
          countries: data.countries || [],
          count: data.count || 0,
          search: data.search
        };
      } else {
        return {
          success: false,
          error: data.error || 'Search failed',
          countries: []
        };
      }
    } catch (error) {      return {
        success: false,
        error: 'Failed to search countries',
        countries: []
      };
    }
  }

  /**
   * Get all countries in a specific region
   * @param {string} region - Region name (e.g., 'West Africa', 'North America')
   * @returns {Promise<Object>} Countries in the specified region
   */
  async getCountriesByRegion(region) {
    try {
      const response = await apiService.get('/auth/countries/phone-data/', {
        params: { region }
      });

      const data = response.data;

      if (data.success) {        return {
          success: true,
          countries: data.countries || [],
          count: data.count || 0,
          region: data.region
        };
      } else {
        return {
          success: false,
          error: data.error || 'Failed to get countries by region',
          countries: []
        };
      }
    } catch (error) {      return {
        success: false,
        error: 'Failed to get countries by region',
        countries: []
      };
    }
  }

  /**
   * Get a specific country by ISO3 code
   * @param {string} iso3 - ISO3 country code (e.g., 'CAN', 'BEN', 'FRA')
   * @returns {Promise<Object>} Country data or null if not found
   */
  async getCountry(iso3) {
    try {
      const response = await apiService.get('/auth/countries/phone-data/', {
        params: { iso3 }
      });

      const data = response.data;

      if (data.success && data.countries && data.countries.length > 0) {        return {
          success: true,
          country: data.countries[0]
        };
      } else {
        return {
          success: false,
          error: 'Country not found',
          country: null
        };
      }
    } catch (error) {      return {
        success: false,
        error: 'Failed to get country',
        country: null
      };
    }
  }

  /**
   * Get all available regions with country counts
   * @returns {Promise<Object>} List of regions with counts and sample countries
   */
  async getRegions() {
    try {
      // Check localStorage cache first
      const cacheKey = 'cached_regions_v1';
      const cached = localStorage.getItem(cacheKey);

      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          const cacheAge = Date.now() - (parsed.timestamp || 0);

          // Use cache if less than 24 hours old (86400000 ms)
          if (cacheAge < 86400000) {            return {
              success: true,
              regions: parsed.regions,
              count: parsed.count,
              fromCache: true
            };
          }
        } catch (e) {          localStorage.removeItem(cacheKey);
        }
      }

      // Cache miss or expired - fetch from API
      const response = await apiService.get('/auth/countries/regions/');
      const data = response.data;

      if (data.success) {
        // Store in localStorage with timestamp
        const cacheData = {
          regions: data.regions,
          count: data.count,
          timestamp: Date.now()
        };

        localStorage.setItem(cacheKey, JSON.stringify(cacheData));
        return {
          success: true,
          regions: data.regions || [],
          count: data.count || 0,
          fromCache: false
        };
      } else {
        return {
          success: false,
          error: data.error || 'Failed to get regions',
          regions: []
        };
      }
    } catch (error) {      return {
        success: false,
        error: 'Failed to get regions',
        regions: []
      };
    }
  }

  /**
   * Get all countries with phone data
   * @returns {Promise<Object>} All countries
   */
  async getAllCountries() {
    try {
      // Check localStorage cache first
      const cacheKey = 'cached_countries_phone_v1';
      const cached = localStorage.getItem(cacheKey);

      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          const cacheAge = Date.now() - (parsed.timestamp || 0);

          // Use cache if less than 1 hour old (3600000 ms)
          if (cacheAge < 3600000) {            return {
              success: true,
              countries: parsed.countries,
              count: parsed.count,
              fromCache: true
            };
          }
        } catch (e) {          localStorage.removeItem(cacheKey);
        }
      }

      // Cache miss or expired - fetch from API
      const response = await apiService.get('/auth/countries/phone-data/');
      const data = response.data;

      if (data.success) {
        // Store in localStorage with timestamp
        const cacheData = {
          countries: data.countries,
          count: data.count,
          timestamp: Date.now()
        };

        localStorage.setItem(cacheKey, JSON.stringify(cacheData));
        return {
          success: true,
          countries: data.countries || [],
          count: data.count || 0,
          fromCache: false
        };
      } else {
        return {
          success: false,
          error: data.error || 'Failed to get countries',
          countries: []
        };
      }
    } catch (error) {      return {
        success: false,
        error: 'Failed to get all countries',
        countries: []
      };
    }
  }

  /**
   * Format phone number for display with country code
   * @param {Object} country - Country object with phone_code
   * @param {string} phoneNumber - Phone number without country code
   * @returns {string} Formatted phone number (e.g., "+1 514-555-1234")
   */
  formatPhoneNumber(country, phoneNumber) {
    if (!country || !country.phone_code || !phoneNumber) {
      return phoneNumber || '';
    }

    const cleanNumber = phoneNumber.replace(/\D/g, '');
    return `${country.phone_code} ${cleanNumber}`;
  }

  /**
   * Get full international phone number
   * @param {Object} country - Country object with phone_code
   * @param {string} phoneNumber - Phone number without country code
   * @returns {string} Full international format (e.g., "+15145551234")
   */
  getInternationalNumber(country, phoneNumber) {
    if (!country || !country.phone_code || !phoneNumber) {
      return '';
    }

    const cleanNumber = phoneNumber.replace(/\D/g, '');
    return `${country.phone_code}${cleanNumber}`;
  }

  /**
   * Format country display with flag and name
   * @param {Object} country - Country object
   * @returns {string} Formatted display (e.g., "🇨🇦 Canada (+1)")
   */
  formatCountryDisplay(country) {
    if (!country) return '';

    const parts = [];

    if (country.flag_emoji) {
      parts.push(country.flag_emoji);
    }

    if (country.name) {
      parts.push(country.name);
    }

    if (country.phone_code) {
      parts.push(`(${country.phone_code})`);
    }

    return parts.join(' ');
  }

  /**
   * Format country display for dropdown (compact)
   * @param {Object} country - Country object
   * @returns {string} Compact display (e.g., "🇨🇦 +1")
   */
  formatCountryCompact(country) {
    if (!country) return '';

    const parts = [];

    if (country.flag_emoji) {
      parts.push(country.flag_emoji);
    }

    if (country.phone_code) {
      parts.push(country.phone_code);
    }

    return parts.join(' ');
  }

  /**
   * Validate phone number length for a specific country
   * Note: This is a basic validation. For comprehensive validation,
   * use backend validation or a library like libphonenumber-js
   * @param {Object} country - Country object
   * @param {string} phoneNumber - Phone number to validate
   * @returns {Object} Validation result
   */
  validatePhoneNumber(country, phoneNumber) {
    if (!phoneNumber || phoneNumber.length === 0) {
      return {
        valid: false,
        error: 'Phone number is required'
      };
    }

    const cleanNumber = phoneNumber.replace(/\D/g, '');

    if (cleanNumber.length < 4) {
      return {
        valid: false,
        error: 'Phone number is too short'
      };
    }

    if (cleanNumber.length > 15) {
      return {
        valid: false,
        error: 'Phone number is too long'
      };
    }

    // Basic validation passed
    return {
      valid: true,
      fullNumber: this.getInternationalNumber(country, phoneNumber)
    };
  }

  /**
   * Clear all country-related caches
   * Call this when country data is updated or user logs out
   * @returns {void}
   */
  clearCache() {
    localStorage.removeItem('cached_regions_v1');
    localStorage.removeItem('cached_countries_phone_v1');  }

  /**
   * Check if country service is available
   * @returns {boolean} True if service is available
   */
  isAvailable() {
    return typeof fetch !== 'undefined' && typeof localStorage !== 'undefined';
  }
}

// Create and export singleton instance
const countryService = new CountryService();
export default countryService;
