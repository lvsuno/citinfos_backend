import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  PlusIcon,
  HomeIcon,
  MapPinIcon,
  WrenchScrewdriverIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import HomeDetailsModal from '../components/HomeDetailsModal';
import HomeFormModal from '../components/HomeFormModal';

// Restored simple mock data matching original visual version
const mockHomes = [
  {
    id: '1',
    name: 'Main House',
    address: '123 Main St, Anytown, ST 12345',
    description: 'Primary residence with modern amenities',
    purchase_date: '2020-06-15',
    purchase_price: 450000,
    property_type: 'house',
    square_footage: 2400,
    bedrooms: 4,
    bathrooms: 3,
    created_at: '2020-06-15T10:00:00Z',
    equipment_count: 15,
    total_equipment_value: 25000
  },
  {
    id: '2',
    name: 'Vacation Home',
    address: '456 Beach Ave, Coastal City, ST 67890',
    description: 'Beachfront vacation property',
    purchase_date: '2022-03-20',
    purchase_price: 320000,
    property_type: 'house',
    square_footage: 1800,
    bedrooms: 3,
    bathrooms: 2,
    created_at: '2022-03-20T14:30:00Z',
    equipment_count: 8,
    total_equipment_value: 12000
  }
];

// Original hover card visual
const HomeCard = ({ home, onEdit, onViewDetails, onDelete }) => {
  const [isHovered, setIsHovered] = useState(false);
  const getImageUrl = (h) => {
    if (h.image_url) return h.image_url;
    const m = {
      house: 'https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=400&h=300&fit=crop&crop=center',
      apartment: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=400&h=300&fit=crop&crop=center',
      condo: 'https://images.unsplash.com/photo-1560448204-e1a3ecba47d2?w=400&h=300&fit=crop&crop=center',
      commercial: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=400&h=300&fit=crop&crop=center',
      other: 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400&h=300&fit=crop&crop=center'
    };
    return m[h.property_type] || m.house;
  };
  return (
    <div
      className="bg-white rounded-lg shadow hover:shadow-lg transition-all duration-300 overflow-hidden cursor-pointer"
      onMouseEnter={()=>setIsHovered(true)}
      onMouseLeave={()=>setIsHovered(false)}
    >
      {!isHovered ? (
        <div className="relative h-80">
          <img src={getImageUrl(home)} alt={home.name} className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
          <div className="absolute bottom-0 left-0 right-0 p-4 text-white">
            <h3 className="text-xl font-bold">{home.name}</h3>
            <p className="text-sm opacity-90 capitalize">{home.property_type}</p>
          </div>
        </div>
      ) : (
        <div className="h-80 p-3 relative flex flex-col">
          <div className="flex justify-center space-x-2 mb-3">
            <button onClick={(e)=>{e.stopPropagation(); onViewDetails(home);}} className="p-2 bg-green-500 hover:bg-green-600 text-white rounded-full shadow-lg transition-all duration-200 transform hover:scale-105" title="View Full Details"><EyeIcon className="h-4 w-4" /></button>
            <button onClick={(e)=>{e.stopPropagation(); onEdit(home);}} className="p-2 bg-blue-500 hover:bg-blue-600 text-white rounded-full shadow-lg transition-colors" title="Edit Home"><PencilIcon className="h-4 w-4" /></button>
            <button onClick={(e)=>{e.stopPropagation(); onDelete(home);}} className="p-2 bg-red-500 hover:bg-red-600 text-white rounded-full shadow-lg transition-colors" title="Delete Home"><TrashIcon className="h-4 w-4" /></button>
          </div>
          <div className="flex-1 space-y-2 overflow-y-auto">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-2 rounded-lg shadow-lg">
              <h3 className="text-lg font-bold mb-1">{home.name}</h3>
              <p className="text-blue-100 text-sm capitalize">{home.property_type}</p>
            </div>
            <div className="bg-white p-2 rounded-lg shadow-md border-l-4 border-indigo-400">
              <div className="flex items-start">
                <MapPinIcon className="h-4 w-4 mr-2 mt-0.5 text-indigo-500 flex-shrink-0" />
                <div>
                  <p className="text-gray-500 text-xs">Address</p>
                  <p className="font-semibold text-gray-900 text-sm">{home.address}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-2 rounded-lg shadow-md border-l-4 border-orange-400">
              <div className="flex items-center">
                <WrenchScrewdriverIcon className="h-5 w-5 mr-2 text-orange-500" />
                <div>
                  <p className="text-gray-500 text-xs">Equipment Count</p>
                  <p className="font-semibold text-gray-900">{home.equipment_count} items</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const Homes = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedHome, setSelectedHome] = useState(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [viewingHome, setViewingHome] = useState(null);
  const { data: homes = mockHomes } = useQuery('homes', () => Promise.resolve(mockHomes));

  const handleAddHome = () => { setSelectedHome(null); setIsModalOpen(true); };
  const handleEditHome = (home) => { setSelectedHome(home); setIsModalOpen(true); };
  const handleViewDetails = (home) => { setViewingHome(home); setIsDetailsModalOpen(true); };
  const handleDeleteHome = (home) => {
    if (window.confirm(`Delete home "${home.name}"?`)) {
      // simple delete (mock)
    }
  };
  const handleSaveHome = (formData) => {
    // stub save (mock)
    setIsModalOpen(false);
    setSelectedHome(null);
  };

  const totalHomes = homes.length;
  const totalEquipment = homes.reduce((sum, h) => sum + h.equipment_count, 0);
  const totalValue = homes.reduce((sum, h) => sum + (h.total_equipment_value||0), 0);
  const totalPropertyValue = homes.reduce((sum, h) => sum + (h.purchase_price||0), 0);
  const formatCurrency = (amt) => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',minimumFractionDigits:0}).format(amt);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Home Management</h1>
          <p className="text-gray-600">Manage your properties and their equipment</p>
        </div>
        <button onClick={handleAddHome} className="inline-flex items-center px-4 py-2 rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
          <PlusIcon className="h-4 w-4 mr-2" /> Add Home
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6 flex items-center">
          <HomeIcon className="h-8 w-8 text-blue-600" />
          <div className="ml-4"><p className="text-sm font-medium text-gray-600">Total Homes</p><p className="text-2xl font-semibold text-gray-900">{totalHomes}</p></div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 flex items-center">
          <WrenchScrewdriverIcon className="h-8 w-8 text-green-600" />
          <div className="ml-4"><p className="text-sm font-medium text-gray-600">Total Equipment</p><p className="text-2xl font-semibold text-gray-900">{totalEquipment}</p></div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 flex items-center">
          <div className="h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center"><span className="text-purple-600 font-bold">$</span></div>
          <div className="ml-4"><p className="text-sm font-medium text-gray-600">Equipment Value</p><p className="text-2xl font-semibold text-gray-900">{formatCurrency(totalValue)}</p></div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 flex items-center">
          <div className="h-8 w-8 bg-orange-100 rounded-full flex items-center justify-center"><span className="text-orange-600 font-bold">$</span></div>
          <div className="ml-4"><p className="text-sm font-medium text-gray-600">Property Value</p><p className="text-2xl font-semibold text-gray-900">{formatCurrency(totalPropertyValue)}</p></div>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {homes.map(home => (
          <HomeCard
            key={home.id}
            home={home}
            onEdit={handleEditHome}
            onViewDetails={handleViewDetails}
            onDelete={handleDeleteHome}
          />
        ))}
      </div>
      {homes.length === 0 && (
        <div className="text-center py-12">
          <HomeIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No homes found</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by adding your first home.</p>
          <div className="mt-6"><button onClick={handleAddHome} className="inline-flex items-center px-4 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"><PlusIcon className="h-4 w-4 mr-2" /> Add Home</button></div>
        </div>
      )}
      {isDetailsModalOpen && viewingHome && (
        <HomeDetailsModal home={viewingHome} isOpen={isDetailsModalOpen} onClose={() => { setIsDetailsModalOpen(false); setViewingHome(null); }} />
      )}
      {isModalOpen && (
        <HomeFormModal
          home={selectedHome}
          isOpen={isModalOpen}
          onClose={() => { setIsModalOpen(false); setSelectedHome(null); }}
          onSave={handleSaveHome}
        />
      )}
    </div>
  );
};

export default Homes;
