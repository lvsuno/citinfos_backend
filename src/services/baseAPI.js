/**
 * Base API Service that uses JWT authentication
 *
 * This service provides a central API instance that all other services can use
 * to make authenticated requests using the JWT authentication system.
 */

import apiService from './apiService';

class BaseAPIService {
  constructor() {
    this.api = apiService.api; // Access the axios instance directly
  }

  // Common request methods
  async get(endpoint, config = {}) {
    const response = await this.api.get(endpoint, config);
    return response.data;
  }

  async post(endpoint, data = {}, config = {}) {
    const response = await this.api.post(endpoint, data, config);
    return response.data;
  }

  async put(endpoint, data = {}, config = {}) {
    const response = await this.api.put(endpoint, data, config);
    return response.data;
  }

  async patch(endpoint, data = {}, config = {}) {
    const response = await this.api.patch(endpoint, data, config);
    return response.data;
  }

  async delete(endpoint, config = {}) {
    const response = await this.api.delete(endpoint, config);
    return response.data;
  }

  // Helper for building query parameters
  buildQueryString(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        searchParams.append(key, value);
      }
    });
    return searchParams.toString();
  }

  // Helper for building endpoint with query params
  buildEndpoint(path, params = {}) {
    const queryString = this.buildQueryString(params);
    return queryString ? `${path}?${queryString}` : path;
  }
}

export const baseAPI = new BaseAPIService();
export default BaseAPIService;
