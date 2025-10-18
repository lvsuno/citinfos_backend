/**
 * Community API Service
 * Handles API requests for community/division data including enabled rubriques
 */

import apiService from './apiService';

class CommunityAPI {
  constructor() {
    // Cache for enabled rubriques per community
    this.rubriqueCache = new Map();
    this.cacheDuration = 5 * 60 * 1000; // 5 minutes
  }

  /**
   * Get enabled rubriques for a specific community/division
   * Uses caching for performance
   * @param {string} communitySlug - Community slug (e.g., 'montreal', 'paris')
   * @returns {Promise<Object>} Community rubriques data with tree structure
   */
  async getEnabledRubriques(communitySlug) {
    // Check cache first
    const cached = this.rubriqueCache.get(communitySlug);
    if (cached && Date.now() - cached.timestamp < this.cacheDuration) {
      console.log(`✅ Rubriques loaded from CACHE for ${communitySlug} (no API call)`);
      return cached.data;
    }

    console.log(`🌐 Fetching rubriques from API for ${communitySlug}...`);
    try {
      const response = await apiService.get(`/communities/${communitySlug}/rubriques/`);
      const data = response.data;

      // Cache the result
      this.rubriqueCache.set(communitySlug, {
        data,
        timestamp: Date.now()
      });

      console.log(`✅ Rubriques fetched and CACHED for ${communitySlug}`);
      return data;
    } catch (error) {
      console.error(`Error fetching rubriques for ${communitySlug}:`, error);

      // Return default rubriques on error (3 required rubriques)
      return {
        community_id: null,
        community_name: communitySlug,
        rubriques: this.getDefaultRubriques(),
        is_default: true
      };
    }
  }

  /**
   * Get all available rubrique templates (global list)
   * @returns {Promise<Array>} List of all rubrique templates
   */
  async getAllRubriqueTemplates() {
    try {
      const response = await apiService.get('/communities/rubrique-templates/');
      return response.data.results || response.data;
    } catch (error) {
      console.error('Error fetching rubrique templates:', error);
      return this.getDefaultRubriques();
    }
  }

  /**
   * Enable a rubrique for a community (admin only)
   * @param {string} communitySlug - Community slug
   * @param {string} rubriqueId - Rubrique template ID
   * @returns {Promise<Object>} Updated rubrique data
   */
  async enableRubrique(communitySlug, rubriqueId) {
    try {
      const response = await apiService.post(
        `/communities/${communitySlug}/rubriques/${rubriqueId}/enable/`
      );

      // Invalidate cache
      this.rubriqueCache.delete(communitySlug);

      return response.data;
    } catch (error) {
      console.error(`Error enabling rubrique ${rubriqueId}:`, error);
      throw error;
    }
  }

  /**
   * Disable a rubrique for a community (admin only)
   * @param {string} communitySlug - Community slug
   * @param {string} rubriqueId - Rubrique template ID
   * @returns {Promise<Object>} Updated rubrique data
   */
  async disableRubrique(communitySlug, rubriqueId) {
    try {
      const response = await apiService.delete(
        `/communities/${communitySlug}/rubriques/${rubriqueId}/disable/`
      );

      // Invalidate cache
      this.rubriqueCache.delete(communitySlug);

      return response.data;
    } catch (error) {
      console.error(`Error disabling rubrique ${rubriqueId}:`, error);
      throw error;
    }
  }

  /**
   * Clear cache for a specific community or all communities
   * @param {string|null} communitySlug - Community slug or null for all
   */
  clearCache(communitySlug = null) {
    if (communitySlug) {
      this.rubriqueCache.delete(communitySlug);
    } else {
      this.rubriqueCache.clear();
    }
  }

  /**
   * Get default rubriques (fallback when API fails)
   * Returns the 3 required rubriques plus common optional ones
   * @returns {Array} Default rubrique configuration
   */
  getDefaultRubriques() {
    return [
      {
        id: 'default-actualites',
        template_type: 'actualites',
        name: 'Actualités',
        icon: '📰',
        color: '#3498db',
        path: 'actualites',
        required: true,
        depth: 0,
        children: []
      },
      {
        id: 'default-evenements',
        template_type: 'evenements',
        name: 'Événements',
        icon: '🎭',
        color: '#9b59b6',
        path: 'evenements',
        required: true,
        depth: 0,
        children: []
      },
      {
        id: 'default-commerces',
        template_type: 'commerces',
        name: 'Commerces',
        icon: '🏪',
        color: '#e74c3c',
        path: 'commerces',
        required: true,
        depth: 0,
        children: []
      },
      {
        id: 'default-transport',
        template_type: 'transport',
        name: 'Transport',
        icon: '🚌',
        color: '#16a085',
        path: 'transport',
        required: false,
        depth: 0,
        children: []
      },
      {
        id: 'default-culture',
        template_type: 'culture',
        name: 'Culture',
        icon: '🎨',
        color: '#f39c12',
        path: 'culture',
        required: false,
        depth: 0,
        children: []
      },
      {
        id: 'default-sport',
        template_type: 'sport',
        name: 'Sport',
        icon: '⚽',
        color: '#27ae60',
        path: 'sport',
        required: false,
        depth: 0,
        children: []
      }
    ];
  }
}

// Create singleton instance
export const communityAPI = new CommunityAPI();
export default communityAPI;
