import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Pencil, Trash2, MapPin, Cog, Eye } from 'lucide-react';

const statusBadge = (status) => {
  switch (status) {
    case 'operational': return 'bg-green-100 text-green-800';
    case 'maintenance': return 'bg-yellow-100 text-yellow-800';
    case 'broken': return 'bg-red-100 text-red-800';
    case 'retired': return 'bg-gray-100 text-gray-800';
    default: return 'bg-blue-100 text-blue-800';
  }
};

const imageUrl = (equipment) => {
  const specific = {
    'electronic': 'photo-1550745165-9bc0b252726f',
    'home_appliance': 'photo-1556909114-f6e7ad7d3136',
    'hvac': 'photo-1581091226825-a6a2a5aee158',
    'plumbing': 'photo-1581091008917-2b40d1a19cfc',
    'electrical': 'photo-1621905251189-08b45d6a269e',
    'security': 'photo-1558618666-fcd25c85cd64',
    'garden': 'photo-1416879595882-3373a0480b5b',
    'automotive': 'photo-1492144534655-ae79c964c9d7'
  };
  const photoId = specific[equipment.equipment_type] || specific['electronic'];
  return `https://images.unsplash.com/${photoId}?w=800&h=600&auto=format&fit=crop&q=90`;
};

const EquipmentPageCard = ({ equipment, onEdit, onDelete, onViewDetails }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [imageError, setImageError] = useState(false);
  const fallback = 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&h=600&auto=format&fit=crop&q=90';

  const safeImage = imageError ? fallback : imageUrl(equipment);

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 relative" onMouseEnter={() => setIsHovered(true)} onMouseLeave={() => setIsHovered(false)}>
      {!isHovered && (
        <div className="absolute top-2 left-2 z-10">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusBadge(equipment.status)}`}>{equipment.status.charAt(0).toUpperCase() + equipment.status.slice(1)}</span>
        </div>
      )}
      <div className="relative h-64 overflow-hidden">
        {!isHovered ? (
          <div className="w-full h-full">
            <img src={safeImage} alt={`${equipment.brand?.name} ${equipment.model?.name}`} className="w-full h-full object-cover" onError={() => setImageError(true)} />
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-4">
              <h3 className="text-xl font-bold text-white mb-1">{equipment.name}</h3>
              <p className="text-gray-200 text-sm">{equipment.brand?.name} {equipment.model?.name}</p>
              <p className="text-gray-300 text-xs">{equipment.home?.name} - {equipment.room}</p>
            </div>
          </div>
        ) : (
          <div className="w-full h-full p-3 bg-gradient-to-br from-white via-gray-50 to-blue-50 relative flex">
            <div className="flex-1 space-y-2 pr-2 overflow-y-auto">
              <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-2 rounded-lg shadow-lg">
                <h3 className="text-lg font-bold mb-1">{equipment.name}</h3>
                <p className="text-blue-100 text-sm">{equipment.brand?.name} {equipment.model?.name}</p>
              </div>
              <div className="grid grid-cols-1 gap-2">
                <div className="bg-white p-2 rounded-lg shadow-md border-l-4 border-blue-400">
                  <div className="flex items-center text-sm">
                    <Cog className="h-4 w-4 mr-2 text-blue-500" />
                    <div><p className="text-gray-500 text-xs">Type</p><p className="font-semibold text-gray-900 capitalize">{equipment.equipment_type?.replace('_', ' ')}</p></div>
                  </div>
                </div>
                <div className="bg-white p-2 rounded-lg shadow-md border-l-4 border-green-400">
                  <div className="flex items-center text-sm">
                    <div className="w-4 h-4 mr-2 flex items-center justify-center"><span className="w-3 h-3 rounded-full bg-green-500" /></div>
                    <div><p className="text-gray-500 text-xs">Status</p><p className="font-semibold text-gray-900 capitalize">{equipment.status}</p></div>
                  </div>
                </div>
                <div className="bg-white p-2 rounded-lg shadow-md border-l-4 border-indigo-400">
                  <div className="flex items-center text-sm">
                    <MapPin className="h-4 w-4 mr-2 text-indigo-500" />
                    <div><p className="text-gray-500 text-xs">Location</p><p className="font-semibold text-gray-900">{equipment.home?.name} - {equipment.room}</p></div>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex flex-col justify-center space-y-2 ml-2">
              <button onClick={() => onViewDetails(equipment)} className="p-2 bg-green-500 hover:bg-green-600 text-white rounded-full shadow-lg transition-all duration-200 transform hover:scale-105" title="View Full Details"><Eye className="h-4 w-4" /></button>
              <button onClick={() => onEdit(equipment)} className="p-2 bg-blue-500 hover:bg-blue-600 text-white rounded-full shadow-lg transition-all duration-200 transform hover:scale-105" title="Edit Equipment"><Pencil className="h-4 w-4" /></button>
              <button onClick={() => { if (window.confirm('Delete this equipment?')) onDelete(equipment.id); }} className="p-2 bg-red-500 hover:bg-red-600 text-white rounded-full shadow-lg transition-all duration-200 transform hover:scale-105" title="Delete Equipment"><Trash2 className="h-4 w-4" /></button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

EquipmentPageCard.propTypes = {
  equipment: PropTypes.object.isRequired,
  onEdit: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onViewDetails: PropTypes.func.isRequired,
};

export default EquipmentPageCard;
