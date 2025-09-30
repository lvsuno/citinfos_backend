import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  PlusIcon,
  WrenchScrewdriverIcon,
  TagIcon,
  CalendarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  HomeIcon,
  CogIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  ClockIcon,
  ChartBarIcon,
  ChatBubbleLeftIcon,
  ExclamationCircleIcon,
  BuildingOfficeIcon,
  CurrencyDollarIcon,
  PhotoIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

// Mock API service that demonstrates the full backend integration
const mockEquipmentAPI = {
  // Main equipment operations
  async getEquipment(filters = {}) {
    // Simulate API call with comprehensive equipment data
    return {
      results: [
        {
          // Core Equipment fields
          id: '123e4567-e89b-12d3-a456-426614174000',
          name: 'Samsung Smart TV',

          // Relationship fields (from your models)
          home: {
            id: 'home-123',
            name: 'Main House',
            address: '123 Main Street'
          },

          // Equipment Model relationship
          equipment_model: {
            id: 'model-456',
            type: 'Television',
            make: 'Samsung',
            model: 'QN85A',
            usagepatterns: 'Daily entertainment use',
            locations: 'Living room, bedroom',
            failure_frequency: 'Low - every 5-7 years',
            brand: {
              id: 'brand-789',
              name: 'Samsung',
              description: 'South Korean electronics manufacturer',
              country_of_origin: 'South Korea',
              reputation: {
                electronics: 'Excellent',
                appliances: 'Good'
              }
            },
            manualfile: '/media/manuals/samsung-qn85a-manual.pdf',
            image: '/media/equipment_images/samsung-tv.jpg'
          },

          // Current backend fields
          owner: {
            id: 'user-111',
            username: 'john_doe',
            first_name: 'John',
            last_name: 'Doe'
          },
          other_details: 'Mounted on wall, includes sound bar',
          image: '/media/equipment_images/living-room-tv.jpg',
          current_health: 'good',
          visibility: 'private',
          approved: true,
          purchase_date: '2023-01-15',
          purchase_price: '1299.99',
          maintenance_notes: 'Clean screen monthly, check connections quarterly',
          created_at: '2023-01-16T10:30:00Z',

          // Missing fields that frontend expects (marked with *)
          status: 'operational', // * Maps from current_health
          equipment_type: 'electronic', // * Derived from specialized model type
          room: 'Living Room', // * Missing in backend
          serial_number: 'SN123456789', // * Missing in backend
          warranty_expires: '2025-01-15', // * Should come from Warranty model
          notes: 'Great picture quality, family loves it', // * Missing general notes field

          // Rich specifications (missing JSON field in backend)
          specifications: {
            screen_size: '55 inches',
            resolution: '4K UHD',
            smart_features: true,
            refresh_rate: '120Hz',
            power_consumption: '120W',
            ports: 'HDMI x4, USB x2, Optical',
            operating_system: 'Tizen',
            connectivity: 'WiFi, Bluetooth, Ethernet'
          },

          // Related data from your models
          warranties: [
            {
              id: 'warranty-1',
              name: 'Manufacturer Warranty',
              start_date: '2023-01-15',
              end_date: '2025-01-15',
              description: '2-year comprehensive warranty',
              is_active: true,
              file: '/media/warranties/samsung-warranty.pdf'
            }
          ],

          bills: [
            {
              id: 'bill-1',
              name: 'Samsung TV Purchase',
              amount: '1299.99',
              issue_date: '2023-01-15',
              template: {
                id: 'template-1',
                name: 'Electronics Purchase Template'
              },
              file: '/media/bills/samsung-tv-receipt.pdf'
            }
          ],

          failures: [
            {
              id: 'failure-1',
              failuredate: '2023-06-15',
              failurecause: 'Remote control stopped working',
              created_at: '2023-06-15T14:20:00Z'
            }
          ],

          equipment_history: [
            {
              id: 'history-1',
              event_name: 'Initial Setup',
              event_date: '2023-01-16',
              description: 'TV mounted and configured',
              location: 'Living Room'
            },
            {
              id: 'history-2',
              event_name: 'Software Update',
              event_date: '2023-03-20',
              description: 'Updated to latest Tizen version',
              location: 'Living Room'
            }
          ],

          comments: [
            {
              id: 'comment-1',
              text: 'Picture quality is amazing!',
              user: {
                username: 'jane_doe',
                first_name: 'Jane'
              },
              created_at: '2023-02-01T16:45:00Z'
            }
          ],

          // Specialized Equipment fields (Electronic model)
          specialized_data: {
            device_type: 'Television',
            screen_size: '55 inches',
            resolution: '4K UHD',
            power_usage: '120W',
            ports: 'HDMI x4, USB x2, Optical',
            smart_features: true,
            refresh_rate: '120Hz',
            audio_output: 'Dolby Atmos',
            operating_system: 'Tizen',
            connectivity: 'WiFi, Bluetooth, HDMI',
            power_consumption: '120W',
            storage_capacity: '32GB'
          }
        },

        // Second equipment example - HVAC system
        {
          id: '456e7890-e89b-12d3-a456-426614174001',
          name: 'Central Air Conditioning',
          home: {
            id: 'home-123',
            name: 'Main House',
            address: '123 Main Street'
          },
          equipment_model: {
            id: 'model-hvac-1',
            type: 'Central AC',
            make: 'Carrier',
            model: 'Infinity Series',
            brand: {
              id: 'brand-carrier',
              name: 'Carrier',
              description: 'Leading HVAC manufacturer',
              country_of_origin: 'United States'
            }
          },
          owner: {
            id: 'user-111',
            username: 'john_doe'
          },
          current_health: 'warning',
          status: 'maintenance',
          equipment_type: 'hvac',
          room: 'Utility Room',
          serial_number: 'CAR-AC-789456',
          purchase_date: '2022-05-20',
          purchase_price: '4500.00',
          warranty_expires: '2032-05-20',
          notes: 'Requires annual maintenance, filter changes every 3 months',

          specifications: {
            cooling_capacity: '3 tons',
            heating_capacity: '60000 BTU',
            energy_efficiency: '16 SEER',
            refrigerant_type: 'R410A',
            noise_level: '42 dB'
          },

          specialized_data: {
            hvac_type: 'Central',
            btu_capacity: '36000 BTU/hr',
            power_usage: '3500W',
            cooling_capacity: '36000 BTU',
            heating_capacity: '60000 BTU',
            energy_efficiency_ratio: 16.0,
            noise_level: '42 dB',
            refrigerant_type: 'R410A',
            airflow_rate: '1200 CFM',
            operating_range: '-10°C to 45°C',
            filter_type: 'MERV 13'
          },

          warranties: [
            {
              id: 'warranty-hvac-1',
              name: '10-Year Manufacturer Warranty',
              start_date: '2022-05-20',
              end_date: '2032-05-20',
              is_active: true
            }
          ],

          failures: [
            {
              id: 'failure-hvac-1',
              failuredate: '2024-07-15',
              failurecause: 'Refrigerant leak detected',
              created_at: '2024-07-15T09:30:00Z'
            }
          ]
        }
      ]
    };
  },

  async getEquipmentStats() {
    return {
      total_count: 25,
      status_counts: {
        operational: 18,
        maintenance: 4,
        broken: 2,
        retired: 1
      },
      type_counts: {
        electronic: 8,
        home_appliance: 6,
        hvac: 4,
        vehicle: 3,
        smart_device: 2,
        power_tool: 1,
        medical_equipment: 1
      },
      recent_additions: 3,
      health_distribution: {
        good: 18,
        warning: 5,
        critical: 2
      },
      warranty_expiring_soon: 3,
      maintenance_due: 4
    };
  },

  async getBrands() {
    return [
      {
        id: 'brand-samsung',
        name: 'Samsung',
        description: 'South Korean electronics manufacturer',
        country_of_origin: 'South Korea',
        logo: '/media/brands/samsung-logo.png',
        reputation: {
          electronics: 'Excellent',
          appliances: 'Good'
        }
      },
      {
        id: 'brand-carrier',
        name: 'Carrier',
        description: 'Leading HVAC manufacturer',
        country_of_origin: 'United States'
      }
    ];
  },

  async getHomes() {
    return [
      {
        id: 'home-123',
        name: 'Main House',
        address: '123 Main Street',
        equipment_count: 15
      },
      {
        id: 'home-456',
        name: 'Vacation Home',
        address: '456 Beach Road',
        equipment_count: 8
      }
    ];
  }
};

// Enhanced Equipment Card Component
const EnhancedEquipmentCard = ({ equipment, onEdit, onDelete, onViewDetails }) => {
  const [showDetails, setShowDetails] = useState(false);

  const getStatusBadge = (status, health) => {
    const statusConfig = {
      operational: { color: 'bg-green-100 text-green-800', icon: CheckCircleIcon },
      maintenance: { color: 'bg-yellow-100 text-yellow-800', icon: ClockIcon },
      broken: { color: 'bg-red-100 text-red-800', icon: ExclamationCircleIcon },
      retired: { color: 'bg-gray-100 text-gray-800', icon: TagIcon }
    };

    const config = statusConfig[status] || statusConfig.operational;
    const Icon = config.icon;

    return (
      <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-all duration-300">
      {/* Equipment Image */}
      <div className="relative h-48">
        {equipment.image ? (
          <img
            src={equipment.image}
            alt={equipment.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full bg-gray-200 flex items-center justify-center">
            <PhotoIcon className="w-16 h-16 text-gray-400" />
          </div>
        )}

        {/* Status Badge */}
        <div className="absolute top-2 left-2">
          {getStatusBadge(equipment.status, equipment.current_health)}
        </div>

        {/* Quick Actions */}
        <div className="absolute top-2 right-2 flex space-x-1">
          <button
            onClick={() => onViewDetails(equipment)}
            className="p-1 bg-white bg-opacity-90 rounded-full hover:bg-opacity-100"
            title="View Details"
          >
            <InformationCircleIcon className="w-4 h-4 text-blue-600" />
          </button>
        </div>
      </div>

      {/* Equipment Info */}
      <div className="p-4">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {equipment.name}
          </h3>
          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
            {equipment.equipment_type}
          </span>
        </div>

        {/* Brand and Model */}
        <div className="text-sm text-gray-600 mb-2">
          <span className="font-medium">{equipment.equipment_model?.brand?.name}</span>
          {equipment.equipment_model?.model && (
            <span> • {equipment.equipment_model.model}</span>
          )}
        </div>

        {/* Location */}
        <div className="flex items-center text-sm text-gray-500 mb-3">
          <HomeIcon className="w-4 h-4 mr-1" />
          <span>{equipment.home?.name}</span>
          {equipment.room && <span> • {equipment.room}</span>}
        </div>

        {/* Key Specifications */}
        {equipment.specifications && (
          <div className="mb-3">
            <div className="grid grid-cols-2 gap-1 text-xs">
              {Object.entries(equipment.specifications).slice(0, 4).map(([key, value]) => (
                <div key={key} className="truncate">
                  <span className="text-gray-500">{key.replace('_', ' ')}:</span>
                  <span className="ml-1 font-medium">
                    {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Stats */}
        <div className="flex justify-between items-center text-xs text-gray-500 mb-3">
          <div className="flex items-center">
            <CalendarIcon className="w-3 h-3 mr-1" />
            <span>{new Date(equipment.purchase_date).getFullYear()}</span>
          </div>

          {equipment.warranties && equipment.warranties.length > 0 && (
            <div className="flex items-center">
              <ShieldCheckIcon className="w-3 h-3 mr-1" />
              <span>{equipment.warranties.filter(w => w.is_active).length} warranties</span>
            </div>
          )}

          {equipment.failures && equipment.failures.length > 0 && (
            <div className="flex items-center text-orange-600">
              <ExclamationTriangleIcon className="w-3 h-3 mr-1" />
              <span>{equipment.failures.length} issues</span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex space-x-2">
          <button
            onClick={() => onEdit(equipment)}
            className="flex-1 px-3 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100"
          >
            Edit
          </button>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex-1 px-3 py-1 text-xs bg-gray-50 text-gray-700 rounded hover:bg-gray-100"
          >
            {showDetails ? 'Less' : 'More'}
          </button>
        </div>

        {/* Expanded Details */}
        {showDetails && (
          <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
            {/* Serial Number */}
            {equipment.serial_number && (
              <div className="text-xs">
                <span className="text-gray-500">Serial:</span>
                <span className="ml-1 font-mono">{equipment.serial_number}</span>
              </div>
            )}

            {/* Recent History */}
            {equipment.equipment_history && equipment.equipment_history.length > 0 && (
              <div className="text-xs">
                <span className="text-gray-500">Last event:</span>
                <span className="ml-1">{equipment.equipment_history[0].event_name}</span>
              </div>
            )}

            {/* Comments Count */}
            {equipment.comments && equipment.comments.length > 0 && (
              <div className="flex items-center text-xs text-gray-500">
                <ChatBubbleLeftIcon className="w-3 h-3 mr-1" />
                <span>{equipment.comments.length} comments</span>
              </div>
            )}

            {/* Quick Delete */}
            <button
              onClick={() => onDelete(equipment.id)}
              className="w-full px-3 py-1 text-xs bg-red-50 text-red-700 rounded hover:bg-red-100"
            >
              Delete Equipment
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced Stats Dashboard
const StatsDashboard = ({ stats }) => {
  const statusStats = [
    {
      key: 'operational',
      label: 'Operational',
      value: stats.status_counts?.operational || 0,
      icon: CheckCircleIcon,
      color: 'text-green-600 bg-green-100'
    },
    {
      key: 'maintenance',
      label: 'Maintenance',
      value: stats.status_counts?.maintenance || 0,
      icon: ClockIcon,
      color: 'text-yellow-600 bg-yellow-100'
    },
    {
      key: 'broken',
      label: 'Broken',
      value: stats.status_counts?.broken || 0,
      icon: ExclamationCircleIcon,
      color: 'text-red-600 bg-red-100'
    },
    {
      key: 'retired',
      label: 'Retired',
      value: stats.status_counts?.retired || 0,
      icon: TagIcon,
      color: 'text-gray-600 bg-gray-100'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4 mb-6">
      {/* Total Equipment */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center">
          <WrenchScrewdriverIcon className="h-8 w-8 text-blue-600" />
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-600">Total Equipment</p>
            <p className="text-2xl font-semibold text-gray-900">{stats.total_count || 0}</p>
          </div>
        </div>
      </div>

      {/* Status Stats */}
      {statusStats.map(({ key, label, value, icon: Icon, color }) => (
        <div key={key} className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Icon className={`h-8 w-8 ${color.split(' ')[0]}`} />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">{label}</p>
              <p className="text-2xl font-semibold text-gray-900">{value}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Main Enhanced Equipment Component
const Equipment2 = () => {
  const [selectedHome, setSelectedHome] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [brandFilter, setBrandFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEquipment, setSelectedEquipment] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  // Mock queries
  const { data: equipment = [], isLoading: equipmentLoading } = useQuery(
    ['equipment', selectedHome, statusFilter, typeFilter, brandFilter, searchTerm],
    () => mockEquipmentAPI.getEquipment({
      home: selectedHome !== 'all' ? selectedHome : undefined,
      status: statusFilter !== 'all' ? statusFilter : undefined,
      equipment_type: typeFilter !== 'all' ? typeFilter : undefined,
      brand: brandFilter !== 'all' ? brandFilter : undefined,
      search: searchTerm
    }),
    {
      refetchInterval: 30000,
      select: data => data.results || data
    }
  );

  const { data: stats } = useQuery(
    ['equipment-stats'],
    () => mockEquipmentAPI.getEquipmentStats()
  );

  const { data: homes = [] } = useQuery(
    ['homes'],
    () => mockEquipmentAPI.getHomes()
  );

  const { data: brands = [] } = useQuery(
    ['brands'],
    () => mockEquipmentAPI.getBrands()
  );

  // Equipment types based on your backend models
  const equipmentTypes = [
    { value: 'all', label: 'All Types' },
    { value: 'home_appliance', label: 'Home Appliances' },
    { value: 'electronic', label: 'Electronics' },
    { value: 'hvac', label: 'HVAC Systems' },
    { value: 'vehicle', label: 'Vehicles' },
    { value: 'smart_device', label: 'Smart Devices' },
    { value: 'power_tool', label: 'Power Tools' },
    { value: 'medical_equipment', label: 'Medical Equipment' }
  ];

  // Filter equipment based on current filters
  const filteredEquipment = equipment.filter(item => {
    const matchesHome = selectedHome === 'all' || item.home?.id === selectedHome;
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
    const matchesType = typeFilter === 'all' || item.equipment_type === typeFilter;
    const matchesBrand = brandFilter === 'all' || item.equipment_model?.brand?.id === brandFilter;
    const matchesSearch = !searchTerm ||
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.equipment_model?.brand?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.equipment_model?.model.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesHome && matchesStatus && matchesType && matchesBrand && matchesSearch;
  });

  const handleViewDetails = (equipment) => {
    setSelectedEquipment(equipment);
    setShowDetailsModal(true);
  };

  const handleEdit = (equipment) => {
    console.log('Edit equipment:', equipment);
    // TODO: Open edit modal
  };

  const handleDelete = (equipmentId) => {
    if (window.confirm('Are you sure you want to delete this equipment?')) {
      console.log('Delete equipment:', equipmentId);
      // TODO: Implement delete
    }
  };

  const clearFilters = () => {
    setSelectedHome('all');
    setStatusFilter('all');
    setTypeFilter('all');
    setBrandFilter('all');
    setSearchTerm('');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Enhanced Equipment Management</h1>
          <p className="text-gray-600">Complete integration with all backend models</p>
        </div>
        <button className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
          <PlusIcon className="h-4 w-4 mr-2" />
          Add Equipment
        </button>
      </div>

      {/* Enhanced Stats Dashboard */}
      <StatsDashboard stats={stats || {}} />

      {/* Additional Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center">
            <ShieldCheckIcon className="h-6 w-6 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm text-gray-500">Warranties Expiring Soon</p>
              <p className="text-lg font-semibold">{stats?.warranty_expiring_soon || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center">
            <ClockIcon className="h-6 w-6 text-orange-500" />
            <div className="ml-3">
              <p className="text-sm text-gray-500">Maintenance Due</p>
              <p className="text-lg font-semibold">{stats?.maintenance_due || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center">
            <BuildingOfficeIcon className="h-6 w-6 text-green-500" />
            <div className="ml-3">
              <p className="text-sm text-gray-500">Homes</p>
              <p className="text-lg font-semibold">{homes.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center">
            <TagIcon className="h-6 w-6 text-purple-500" />
            <div className="ml-3">
              <p className="text-sm text-gray-500">Brands</p>
              <p className="text-lg font-semibold">{brands.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
            <input
              type="text"
              placeholder="Search equipment, brand, model..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          {/* Home Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Home</label>
            <select
              value={selectedHome}
              onChange={(e) => setSelectedHome(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="all">All Homes</option>
              {homes.map(home => (
                <option key={home.id} value={home.id}>
                  {home.name} ({home.equipment_count})
                </option>
              ))}
            </select>
          </div>

          {/* Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              {equipmentTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Brand Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Brand</label>
            <select
              value={brandFilter}
              onChange={(e) => setBrandFilter(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="all">All Brands</option>
              {brands.map(brand => (
                <option key={brand.id} value={brand.id}>
                  {brand.name}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="operational">Operational</option>
              <option value="maintenance">Maintenance</option>
              <option value="broken">Broken</option>
              <option value="retired">Retired</option>
            </select>
          </div>

          {/* Clear Filters */}
          <div className="flex items-end">
            <button
              onClick={clearFilters}
              className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Results Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          Showing <span className="font-semibold">{filteredEquipment.length}</span> of{' '}
          <span className="font-semibold">{equipment.length}</span> equipment items
          {(selectedHome !== 'all' || statusFilter !== 'all' || typeFilter !== 'all' || brandFilter !== 'all' || searchTerm) && (
            <span> (filtered)</span>
          )}
        </p>
      </div>

      {/* Equipment Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {equipmentLoading ? (
          // Loading skeleton
          Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow animate-pulse">
              <div className="h-48 bg-gray-200" />
              <div className="p-4 space-y-3">
                <div className="h-4 bg-gray-200 rounded w-3/4" />
                <div className="h-4 bg-gray-200 rounded w-1/2" />
                <div className="h-4 bg-gray-200 rounded w-2/3" />
              </div>
            </div>
          ))
        ) : filteredEquipment.length > 0 ? (
          filteredEquipment.map(equipment => (
            <EnhancedEquipmentCard
              key={equipment.id}
              equipment={equipment}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onViewDetails={handleViewDetails}
            />
          ))
        ) : (
          <div className="col-span-full text-center py-12">
            <WrenchScrewdriverIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No equipment found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {(selectedHome !== 'all' || statusFilter !== 'all' || typeFilter !== 'all' || brandFilter !== 'all' || searchTerm)
                ? 'Try adjusting your filters or add new equipment.'
                : 'Get started by adding your first piece of equipment.'
              }
            </p>
          </div>
        )}
      </div>

      {/* Enhanced Details Modal */}
      {showDetailsModal && selectedEquipment && (
        <EnhancedDetailsModal
          equipment={selectedEquipment}
          isOpen={showDetailsModal}
          onClose={() => setShowDetailsModal(false)}
        />
      )}
    </div>
  );
};

// Enhanced Details Modal Component
const EnhancedDetailsModal = ({ equipment, isOpen, onClose }) => {
  if (!isOpen || !equipment) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-white hover:text-gray-300"
          >
            ✕
          </button>
          <div>
            <h2 className="text-2xl font-bold mb-2">{equipment.name}</h2>
            <p className="text-blue-100 text-lg">
              {equipment.equipment_model?.brand?.name} {equipment.equipment_model?.model}
            </p>
            <div className="flex items-center space-x-4 mt-2">
              <span className="bg-white bg-opacity-20 px-2 py-1 rounded text-sm">
                {equipment.equipment_type}
              </span>
              <span className="bg-white bg-opacity-20 px-2 py-1 rounded text-sm">
                {equipment.status}
              </span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Left Column - Basic Info */}
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-3">Basic Information</h3>
                <div className="space-y-2 text-sm">
                  <div><span className="text-gray-500">Serial:</span> <span className="font-mono">{equipment.serial_number}</span></div>
                  <div><span className="text-gray-500">Location:</span> {equipment.home?.name} - {equipment.room}</div>
                  <div><span className="text-gray-500">Owner:</span> {equipment.owner?.first_name} {equipment.owner?.last_name}</div>
                  <div><span className="text-gray-500">Purchase Date:</span> {new Date(equipment.purchase_date).toLocaleDateString()}</div>
                  <div><span className="text-gray-500">Purchase Price:</span> ${equipment.purchase_price}</div>
                </div>
              </div>

              {/* Warranties */}
              {equipment.warranties && equipment.warranties.length > 0 && (
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                    <ShieldCheckIcon className="w-5 h-5 mr-2 text-green-600" />
                    Warranties
                  </h3>
                  {equipment.warranties.map(warranty => (
                    <div key={warranty.id} className="text-sm mb-2 last:mb-0">
                      <div className="font-medium">{warranty.name}</div>
                      <div className="text-gray-600">
                        {new Date(warranty.start_date).toLocaleDateString()} - {new Date(warranty.end_date).toLocaleDateString()}
                      </div>
                      <div className={`text-xs ${warranty.is_active ? 'text-green-600' : 'text-red-600'}`}>
                        {warranty.is_active ? 'Active' : 'Expired'}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Bills */}
              {equipment.bills && equipment.bills.length > 0 && (
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                    <CurrencyDollarIcon className="w-5 h-5 mr-2 text-blue-600" />
                    Bills & Receipts
                  </h3>
                  {equipment.bills.map(bill => (
                    <div key={bill.id} className="text-sm mb-2 last:mb-0">
                      <div className="font-medium">{bill.name}</div>
                      <div className="text-gray-600">${bill.amount} - {new Date(bill.issue_date).toLocaleDateString()}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Middle Column - Specifications */}
            <div className="space-y-4">
              {/* Technical Specifications */}
              {equipment.specifications && Object.keys(equipment.specifications).length > 0 && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                    <CogIcon className="w-5 h-5 mr-2 text-gray-600" />
                    Specifications
                  </h3>
                  <div className="space-y-2 text-sm">
                    {Object.entries(equipment.specifications).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-gray-500 capitalize">{key.replace('_', ' ')}:</span>
                        <span className="font-medium">
                          {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Specialized Data */}
              {equipment.specialized_data && Object.keys(equipment.specialized_data).length > 0 && (
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-3">
                    {equipment.equipment_type.charAt(0).toUpperCase() + equipment.equipment_type.slice(1)} Specific
                  </h3>
                  <div className="space-y-2 text-sm">
                    {Object.entries(equipment.specialized_data).slice(0, 8).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-gray-500 capitalize">{key.replace('_', ' ')}:</span>
                        <span className="font-medium">
                          {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Notes */}
              {equipment.notes && (
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-3">Notes</h3>
                  <p className="text-sm text-gray-700 italic">"{equipment.notes}"</p>
                </div>
              )}
            </div>

            {/* Right Column - History & Activity */}
            <div className="space-y-4">
              {/* Equipment History */}
              {equipment.equipment_history && equipment.equipment_history.length > 0 && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                    <ClockIcon className="w-5 h-5 mr-2 text-gray-600" />
                    History
                  </h3>
                  <div className="space-y-3 max-h-40 overflow-y-auto">
                    {equipment.equipment_history.map(event => (
                      <div key={event.id} className="text-sm border-l-2 border-gray-300 pl-3">
                        <div className="font-medium">{event.event_name}</div>
                        <div className="text-gray-600">{new Date(event.event_date).toLocaleDateString()}</div>
                        {event.description && (
                          <div className="text-gray-500 text-xs">{event.description}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Failures */}
              {equipment.failures && equipment.failures.length > 0 && (
                <div className="bg-red-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                    <ExclamationTriangleIcon className="w-5 h-5 mr-2 text-red-600" />
                    Issues & Failures
                  </h3>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {equipment.failures.map(failure => (
                      <div key={failure.id} className="text-sm">
                        <div className="text-red-700 font-medium">{new Date(failure.failuredate).toLocaleDateString()}</div>
                        <div className="text-gray-700">{failure.failurecause}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Comments */}
              {equipment.comments && equipment.comments.length > 0 && (
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                    <ChatBubbleLeftIcon className="w-5 h-5 mr-2 text-blue-600" />
                    Comments
                  </h3>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {equipment.comments.map(comment => (
                      <div key={comment.id} className="text-sm">
                        <div className="font-medium">{comment.user.first_name}</div>
                        <div className="text-gray-700">{comment.text}</div>
                        <div className="text-gray-500 text-xs">{new Date(comment.created_at).toLocaleDateString()}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Equipment2;
