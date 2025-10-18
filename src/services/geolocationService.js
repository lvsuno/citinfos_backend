/**
 * Geolocation Service for IP-based location detection and administrative division search
 */

import apiService from './apiService';

class GeolocationService {
  /**
   * Get user's location data from IP address
   * @param {string} ipAddress - Optional IP address, if not provided backend will detect from request
   * @returns {Promise<Object>} Location data with country info and closest divisions
   */
  async getUserLocationData(ipAddress = null) {
    try {
      const response = await apiService.post('/auth/location-data/', {
        ip_address: ipAddress
      });

      const data = response.data;
      if (data.success) {
        return {
          success: true,
          country: data.country,
          userLocation: data.user_location,
          closestDivisions: data.closest_divisions,
          divisionSearchInfo: data.division_search_info
        };
      } else {
        // Handle fallback case (couldn't detect location)
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
   * Search administrative divisions
   * @param {string} countryCode - ISO3 country code (e.g., 'CAN', 'BEN')
   * @param {string} query - Search query (minimum 2 characters)
   * @param {number} limit - Maximum results to return (default 10, max 50)
   * @returns {Promise<Object>} Search results
   */
  async searchDivisions(countryCode, query, limit = 10) {
    try {
      const params = {
        country: countryCode,
        q: query,
        limit: Math.min(limit, 50)
      };
      const response = await apiService.get('/auth/search-divisions/', { params });
      const data = response.data;

      return {
        success: true,
        results: data.results || [],
        total: data.total || 0,
        query: data.query,
        country: data.country,
        divisionType: data.division_type
      };
    } catch (error) {      return {
        success: false,
        error: 'Failed to search divisions',
        results: []
      };
    }
  }

  /**
   * Get the closest neighboring divisions for a given division
   * @param {string} divisionId - UUID of the division
   * @param {number} limit - Number of neighbors to return (default 4, max 10)
   * @returns {Promise<Object>} Neighbors data
   */
  async getDivisionNeighbors(divisionId, limit = 4) {
    try {
      const response = await apiService.get(`/auth/division-neighbors/${divisionId}/`, {
        params: { limit: Math.min(limit, 10) }
      });

      const data = response.data;

      if (data.success) {        return {
          success: true,
          division: data.division,
          neighbors: data.neighbors
        };
      } else {
        return {
          success: false,
          error: data.error || 'Failed to fetch neighbors',
          neighbors: []
        };
      }
    } catch (error) {      return {
        success: false,
        error: 'Failed to get division neighbors',
        neighbors: []
      };
    }
  }

  /**
   * Format division name for display
   * @param {Object} division - Division object from API
   * @returns {string} Formatted display name
   */
  formatDivisionName(division) {
    if (division.parent_name && division.parent_name !== division.name) {
      return `${division.name}, ${division.parent_name}`;
    }
    return division.name;
  }

  /**
   * Get division type display name based on country
   * @param {string} countryCode - ISO3 country code
   * @param {string} divisionType - Division type from API
   * @returns {string} Localized division type name
   */
  getDivisionTypeDisplay(countryCode, divisionType) {
    const divisionTypes = {
      'CAN': {
        'municipalités': 'municipalités',
        'municipalities': 'municipalités'
      },
      'BEN': {
        'communes': 'communes'
      },
      'FRA': {
        'communes': 'communes'
      }
    };

    return divisionTypes[countryCode]?.[divisionType] || divisionType;
  }

  /**
   * Format distance for display
   * @param {number} distanceKm - Distance in kilometers
   * @returns {string} Formatted distance string
   */
  formatDistance(distanceKm) {
    if (distanceKm === null || distanceKm === undefined) {
      return '';
    }

    if (distanceKm < 1) {
      return `${Math.round(distanceKm * 1000)}m`;
    } else if (distanceKm < 10) {
      return `${distanceKm.toFixed(1)}km`;
    } else {
      return `${Math.round(distanceKm)}km`;
    }
  }

  /**
   * Get all available countries
   * Uses localStorage cache with 24-hour expiration
   * @returns {Promise<Object>} Countries data with admin levels
   */
  async getCountries() {
    try {
      // Check localStorage cache first
      const cacheKey = 'cached_countries_v1';
      const cached = localStorage.getItem(cacheKey);

      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          const cacheAge = Date.now() - (parsed.timestamp || 0);

          // Use cache if less than 24 hours old (86400000 ms)
          if (cacheAge < 86400000) {            return {
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
      const response = await apiService.get('/auth/countries/');
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
          countries: data.countries,
          count: data.count,
          fromCache: false
        };
      } else {
        return {
          success: false,
          error: data.error || 'Failed to fetch countries',
          countries: []
        };
      }
    } catch (error) {      return {
        success: false,
        error: 'Failed to get countries',
        countries: []
      };
    }
  }

  /**
   * Get divisions by country and admin level
   * @param {string} countryId - UUID of the country
   * @param {number} adminLevel - Administrative level (0, 1, 2, 3, 4)
   * @param {string} parentId - Optional parent division UUID to filter by
   * @param {number} limit - Maximum results (default 100)
   * @param {string} closestTo - Optional division UUID to find closest divisions to
   * @returns {Promise<Object>} Divisions data
   */
  async getDivisionsByLevel(countryId, adminLevel, parentId = null, limit = 100, closestTo = null) {
    try {
      const params = {
        country_id: countryId,
        admin_level: adminLevel,
        limit
      };

      if (parentId) {
        params.parent_id = parentId;
      }

      if (closestTo) {
        params.closest_to = closestTo;
      }
      const response = await apiService.get('/auth/divisions/', { params });
      const data = response.data;

      if (data.success) {        return {
          success: true,
          divisions: data.divisions,
          count: data.count
        };
      } else {
        return {
          success: false,
          error: data.error || 'Failed to fetch divisions',
          divisions: []
        };
      }
    } catch (error) {      return {
        success: false,
        error: 'Failed to get divisions',
        divisions: []
      };
    }
  }

  /**
   * Get division details by URL slug
   * This is the primary method for loading division data from URLs
   *
   * @param {string} slug - URL slug (e.g., 'sherbrooke', 'saint-denis-de-brompton', 'ze')
   * @param {string} countryISO3 - ISO3 country code (e.g., 'CAN', 'BEN')
   * @param {string} boundaryType - Optional boundary type filter
   * @returns {Promise<Object>} Division data with ID, name, admin_level, etc.
   */
  async getDivisionBySlug(slug, countryISO3, boundaryType = null) {
    try {
      const params = {
        slug,
        country_iso3: countryISO3
      };

      if (boundaryType) {
        params.boundary_type = boundaryType;
      }
      const response = await apiService.get('/auth/divisions/by-slug/', { params });
      const data = response.data;

      if (data.success && data.division) {
        // community_id is now included in the division data from backend
        return {
          success: true,
          division: data.division
        };
      } else {
        return {
          success: false,
          error: data.error || 'Division not found',
          division: null
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to get division',
        division: null
      };
    }
  }

  /**
   * Check if location detection is supported
   * @returns {boolean} True if geolocation features are available
   */
  isSupported() {
    return typeof fetch !== 'undefined';
  }

  /**
   * Clear cached countries data
   * Call this after importing new countries or when cache needs refresh
   * @returns {void}
   */
  clearCountriesCache() {
    const cacheKey = 'cached_countries_v1';
    localStorage.removeItem(cacheKey);  }

  /**
   * Clear all cached division data
   * Removes all pageDivision_ cache entries from localStorage
   * Useful for clearing stale data or during logout
   * @returns {number} Number of cache entries cleared
   */
  clearDivisionCache() {
    let cleared = 0;
    const keysToRemove = [];

    // Find all pageDivision_ keys
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('pageDivision_')) {
        keysToRemove.push(key);
      }
    }

    // Remove them
    keysToRemove.forEach(key => {
      localStorage.removeItem(key);
      cleared++;
    });

    if (cleared > 0) {    }

    return cleared;
  }

  /**
   * Clear specific division cache entry
   * @param {string} countryISO3 - ISO3 country code
   * @param {string} slug - Division slug
   * @returns {boolean} True if cache entry was found and removed
   */
  clearSpecificDivisionCache(countryISO3, slug) {
    const cacheKey = `pageDivision_${countryISO3}_${slug}`;
    const existed = localStorage.getItem(cacheKey) !== null;

    if (existed) {
      localStorage.removeItem(cacheKey);    }

    return existed;
  }

  /**
   * Get cache statistics
   * @returns {Object} Information about cached divisions
   */
  getCacheStats() {
    const stats = {
      divisionCaches: 0,
      totalSize: 0,
      entries: []
    };

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('pageDivision_')) {
        const value = localStorage.getItem(key);
        const size = new Blob([value]).size;

        stats.divisionCaches++;
        stats.totalSize += size;

        try {
          const data = JSON.parse(value);
          stats.entries.push({
            key,
            name: data.name,
            size,
            country: data.country?.iso3
          });
        } catch (e) {
          stats.entries.push({
            key,
            size,
            error: 'Invalid JSON'
          });
        }
      }
    }

    return stats;
  }
}

// Create and export singleton instance
const geolocationService = new GeolocationService();
export default geolocationService;