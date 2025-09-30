import React from 'react';
import PropTypes from 'prop-types';
import { X, Cog, Hash, Calendar as CalendarLucide, DollarSign, MapPin } from 'lucide-react';

const EquipmentDetailsModal = ({ equipment, isOpen, onClose }) => {
  if (!isOpen || !equipment) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 relative">
          <button onClick={onClose} className="absolute top-4 right-4 text-white hover:text-gray-300 transition-colors">
            <X className="h-6 w-6" />
          </button>
          <div>
            <h2 className="text-2xl font-bold mb-2">{equipment.name}</h2>
            <p className="text-blue-100 text-lg">{equipment.brand?.name} {equipment.model?.name}</p>
            {equipment.model?.model_number && (
              <p className="text-blue-200 text-sm">Model: {equipment.model.model_number}</p>
            )}
          </div>
        </div>
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white p-4 rounded-lg shadow-md border-l-4 border-blue-400">
                <div className="flex items-center">
                  <Cog className="h-6 w-6 mr-3 text-blue-500" />
                  <div>
                    <p className="text-gray-500 text-sm">Equipment Type</p>
                    <p className="font-semibold text-gray-900 text-lg capitalize">{equipment.equipment_type?.replace('_', ' ')}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white p-4 rounded-lg shadow-md border-l-4 border-green-400">
                <div className="flex items-center">
                  <div className="w-6 h-6 mr-3 flex items-center justify-center">
                    <span className="w-4 h-4 rounded-full bg-green-500" />
                  </div>
                  <div>
                    <p className="text-gray-500 text-sm">Status</p>
                    <p className="font-semibold text-gray-900 text-lg capitalize">{equipment.status}</p>
                  </div>
                </div>
              </div>
            </div>

            {equipment.serial_number && (
              <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                <div className="flex items-center">
                  <Hash className="h-6 w-6 mr-3 text-yellow-600" />
                  <div>
                    <p className="text-yellow-600 text-sm font-medium">Serial Number</p>
                    <p className="font-mono font-bold text-gray-900 text-lg">{equipment.serial_number}</p>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-4">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Purchase Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {equipment.purchase_date && (
                  <div className="bg-white p-4 rounded-lg shadow-md border-l-4 border-purple-400">
                    <div className="flex items-center">
                      <CalendarLucide className="h-6 w-6 mr-3 text-purple-500" />
                      <div>
                        <p className="text-gray-500 text-sm">Purchase Date</p>
                        <p className="font-semibold text-gray-900">{new Date(equipment.purchase_date).toLocaleDateString('en-US', { year:'numeric', month:'long', day:'numeric' })}</p>
                      </div>
                    </div>
                  </div>
                )}
                {equipment.purchase_price != null && (
                  <div className="bg-white p-4 rounded-lg shadow-md border-l-4 border-green-400">
                    <div className="flex items-center">
                      <DollarSign className="h-6 w-6 mr-3 text-green-500" />
                      <div>
                        <p className="text-gray-500 text-sm">Purchase Price</p>
                        <p className="font-bold text-green-600 text-xl">${equipment.purchase_price.toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                )}
                {equipment.warranty_expires && (
                  <div className="bg-white p-4 rounded-lg shadow-md border-l-4 border-orange-400">
                    <div className="flex items-center">
                      <CalendarLucide className="h-6 w-6 mr-3 text-orange-500" />
                      <div>
                        <p className="text-gray-500 text-sm">Warranty Expires</p>
                        <p className="font-semibold text-gray-900">{new Date(equipment.warranty_expires).toLocaleDateString('en-US', { year:'numeric', month:'long', day:'numeric' })}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {equipment.home && (
              <div className="bg-white p-4 rounded-lg shadow-md border-l-4 border-indigo-400">
                <div className="flex items-center">
                  <MapPin className="h-6 w-6 mr-3 text-indigo-500" />
                  <div>
                    <p className="text-gray-500 text-sm">Location</p>
                    <p className="font-semibold text-gray-900 text-lg">{equipment.home.name}</p>
                    {equipment.room && <p className="text-gray-600">{equipment.room}</p>}
                  </div>
                </div>
              </div>
            )}

            {equipment.maintenance_schedule && (
              <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                <h3 className="text-lg font-bold text-gray-900 mb-3">Maintenance Schedule</h3>
                <div className="flex items-center">
                  <CalendarLucide className="h-6 w-6 mr-3 text-blue-600" />
                  <div>
                    <p className="text-blue-600 text-sm font-medium">Next Maintenance</p>
                    <p className="font-semibold text-gray-900 text-lg">{new Date(equipment.maintenance_schedule.next_maintenance).toLocaleDateString('en-US', { year:'numeric', month:'long', day:'numeric' })}</p>
                    <p className="text-gray-600">Frequency: Every {equipment.maintenance_schedule.frequency_days} days</p>
                  </div>
                </div>
              </div>
            )}

            {equipment.notes && (
              <div className="bg-gray-50 border border-gray-200 p-4 rounded-lg">
                <h3 className="text-lg font-bold text-gray-900 mb-3">Notes</h3>
                <p className="text-gray-800 leading-relaxed italic text-lg">"{equipment.notes}"</p>
              </div>
            )}

            {equipment.specifications && Object.keys(equipment.specifications).length > 0 && (
              <div className="bg-white p-4 rounded-lg shadow-md border border-gray-200">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                  <Cog className="h-5 w-5 mr-2 text-blue-500" />
                  Technical Specifications
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {Object.entries(equipment.specifications).map(([key, value]) => (
                    <div key={key} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                      <span className="text-sm text-gray-600 capitalize font-medium">{key.replace('_',' ')}:</span>
                      <span className="text-sm text-gray-900 font-semibold">
                        {typeof value === 'boolean' ? (
                          <span className={`px-3 py-1 rounded-full text-xs ${value ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{value ? 'Yes' : 'No'}</span>
                        ) : value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {equipment.created_at && (
              <div className="bg-gray-50 border border-gray-200 p-4 rounded-lg">
                <div className="flex items-center">
                  <CalendarLucide className="h-5 w-5 mr-2 text-gray-500" />
                  <div>
                    <p className="text-gray-500 text-sm">Added to System</p>
                    <p className="font-semibold text-gray-900">{new Date(equipment.created_at).toLocaleDateString('en-US', { year:'numeric', month:'long', day:'numeric', hour:'2-digit', minute:'2-digit' })}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

EquipmentDetailsModal.propTypes = {
  equipment: PropTypes.object,
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default EquipmentDetailsModal;
