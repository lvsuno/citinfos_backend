/**
 * Equipment API Service
 * Handles all equipment-related API operations
 * Updated to use actual backend endpoints
 */

import BaseAPIService from './baseAPI';

class EquipmentAPI extends BaseAPIService {
  constructor() {
    super();
  }

  // Get all equipment with optional filters
  async getEquipment(filters = {}) {
    const endpoint = this.buildEndpoint('/equipment/', {
      search: filters.search,
      status: filters.status,
      equipment_type: filters.equipmentType,
      location: filters.location,
      owner: filters.owner,
      home: filters.home,
      ordering: filters.ordering || '-created_at',
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    });
    const response = await this.get(endpoint);
    return response.results || response;
  }

  // Get equipment by ID
  async getEquipmentById(equipmentId) {
    return this.get(`/equipment/${equipmentId}/`);
  }

  // Create new equipment
  async createEquipment(equipmentData) {
    // Handle file upload if images are present
    if (equipmentData.images && equipmentData.images.length > 0) {
      const formData = new FormData();

      // Add equipment data
      Object.keys(equipmentData).forEach(key => {
        if (key !== 'images') {
          formData.append(key, equipmentData[key]);
        }
      });

      // Add images
      equipmentData.images.forEach((image, index) => {
        formData.append(`image_${index}`, image);
      });

      const response = await this.api.post('/equipment/', formData);
      return response.data;
    } else {
      return this.post('/equipment/', equipmentData);
    }
  }

  // Update equipment
  async updateEquipment(equipmentId, equipmentData) {
    // Handle file upload if images are present
    if (equipmentData.images && equipmentData.images.length > 0) {
      const formData = new FormData();

      Object.keys(equipmentData).forEach(key => {
        if (key !== 'images') {
          formData.append(key, equipmentData[key]);
        }
      });

      equipmentData.images.forEach((image, index) => {
        formData.append(`image_${index}`, image);
      });

      const response = await this.api.patch(`/equipment/${equipmentId}/`, formData);
      return response.data;
    } else {
      return this.patch(`/equipment/${equipmentId}/`, equipmentData);
    }
  }

  // Delete equipment
  async deleteEquipment(equipmentId) {
    return this.delete(`/equipment/${equipmentId}/`);
  }

  // Get equipment statistics (aggregate from API data)
  async getEquipmentStats(filters = {}) {
    try {
      // Since there's no dedicated stats endpoint, we'll aggregate from equipment data
      const equipment = await this.getEquipment({ limit: 1000, ...filters });
      const equipmentList = equipment.results || equipment;

      const stats = {
        total_count: equipmentList.length,
        status_counts: {},
        type_counts: {},
        recent_additions: 0
      };

      const oneWeekAgo = new Date();
      oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

      equipmentList.forEach(item => {
        // Count by status
        stats.status_counts[item.status] = (stats.status_counts[item.status] || 0) + 1;

        // Count by type
        if (item.equipment_type) {
          stats.type_counts[item.equipment_type] = (stats.type_counts[item.equipment_type] || 0) + 1;
        }

        // Count recent additions
        if (new Date(item.created_at) > oneWeekAgo) {
          stats.recent_additions++;
        }
      });

      return stats;
    } catch (error) {
      console.error('Error getting equipment stats:', error);
      throw error;
    }
  }

  // Get equipment by status
  async getEquipmentByStatus(status) {
    const response = await this.get(`/equipment/?status=${status}`);
    return response.results || response;
  }

  // Get equipment types (from equipment-types endpoint)
  async getEquipmentTypes() {
    const response = await this.get('/equipment-types/');
    return response.results || response;
  }

  // Update equipment status
  async updateEquipmentStatus(equipmentId, status, notes = '') {
    return this.patch(`/equipment/${equipmentId}/`, {
      status: status,
      status_notes: notes,
      last_maintenance: status === 'maintenance' ? new Date().toISOString() : undefined,
    });
  }

  // Add maintenance record
  async addMaintenanceRecord(equipmentId, maintenanceData) {
    return this.post('/maintenance-records/', {
      equipment: equipmentId,
      maintenance_type: maintenanceData.type,
      description: maintenanceData.description,
      performed_by: maintenanceData.performedBy,
      performed_at: maintenanceData.performedAt || new Date().toISOString(),
      cost: maintenanceData.cost,
      next_maintenance_due: maintenanceData.nextMaintenanceDue,
    });
  }

  // Get maintenance history
  async getMaintenanceHistory(equipmentId) {
    const response = await this.get(`/maintenance-records/?equipment=${equipmentId}`);
    return response.results || response;
  }

  // Get equipment warranty info (from warranty-records)
  async getWarrantyInfo(equipmentId) {
    const response = await this.get(`/warranty-records/?equipment=${equipmentId}`);
    return response.results || response;
  }

  // Update warranty info
  async updateWarrantyInfo(equipmentId, warrantyData) {
    // Create or update warranty record
    const existingWarranty = await this.getWarrantyInfo(equipmentId);
    if (existingWarranty && existingWarranty.length > 0) {
      return this.patch(`/warranty-records/${existingWarranty[0].id}/`, warrantyData);
    } else {
      return this.post('/warranty-records/', {
        equipment: equipmentId,
        ...warrantyData
      });
    }
  }

  // Get equipment locations
  async getEquipmentLocations() {
    const response = await this.get('/equipment-locations/');
    return response.results || response;
  }

  // Get equipment by location
  async getEquipmentByLocation(locationId) {
    const response = await this.get(`/equipment/?location=${locationId}`);
    return response.results || response;
  }

  // Get home/building equipment
  async getHomeEquipment(homeId) {
    const response = await this.get(`/equipment/?home=${homeId}`);
    return response.results || response;
  }

  // Search equipment
  async searchEquipment(searchTerm, filters = {}) {
    return this.getEquipment({
      ...filters,
      search: searchTerm
    });
  }

  // Get recent equipment
  async getRecentEquipment(limit = 10) {
    return this.getEquipment({
      ordering: '-created_at',
      limit
    });
  }

  // Get equipment needing maintenance
  async getEquipmentNeedingMaintenance() {
    return this.getEquipmentByStatus('maintenance');
  }

  // Get archived equipment
  async getArchivedEquipment(filters = {}) {
    return this.getEquipment({
      ...filters,
      status: 'archived'
    });
  }

  // Archive equipment
  async archiveEquipment(equipmentId) {
    return this.updateEquipmentStatus(equipmentId, 'archived', 'Equipment archived');
  }

  // Restore equipment from archive
  async restoreEquipment(equipmentId) {
    return this.updateEquipmentStatus(equipmentId, 'active', 'Equipment restored from archive');
  }
}

export const equipmentAPI = new EquipmentAPI();
export default equipmentAPI;
