import React, { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import {
  XMarkIcon,
  HomeIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  WrenchScrewdriverIcon,
  ChartBarIcon,
  BuildingOfficeIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { createPortal } from 'react-dom';

const HomeDetailsModal = ({ home, isOpen, onClose, onEdit, onUpdate, startInEdit = false }) => {
  if (!isOpen || !home) return null; // early return
  const [editing, setEditing] = useState(startInEdit);
  const [form, setForm] = useState({});

  useEffect(() => {
    if (editing) {
      setForm({
        name: home.name || '',
        property_type: home.property_type || 'house',
        address: home.address || '',
        description: home.description || '',
        purchase_date: home.purchase_date ? home.purchase_date.substring(0, 10) : '',
        purchase_price: home.purchase_price ?? '',
        square_footage: home.square_footage ?? '',
        bedrooms: home.bedrooms ?? '',
        bathrooms: home.bathrooms ?? ''
      });
    }
  }, [editing, home]);

  const dialogRef = useRef(null);

  useEffect(() => {
    const handleKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  const formatCurrency = (amount) => new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0
  }).format(amount);

  const formatDate = (dateString) => new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric'
  });

  const getPropertyTypeIcon = (type) => {
    switch (type) {
      case 'house':
        return <HomeIcon className="h-6 w-6" />;
      case 'apartment':
      case 'condo':
        return <BuildingOfficeIcon className="h-6 w-6" />;
      case 'commercial':
        return <ChartBarIcon className="h-6 w-6" />;
      default:
        return <HomeIcon className="h-6 w-6" />;
    }
  };

  const getPropertyTypeColor = (type) => {
    switch (type) {
      case 'house':
        return 'from-green-600 to-emerald-600';
      case 'apartment':
        return 'from-blue-600 to-indigo-600';
      case 'condo':
        return 'from-purple-600 to-violet-600';
      case 'commercial':
        return 'from-orange-600 to-red-600';
      default:
        return 'from-gray-600 to-slate-600';
    }
  };

  const getImageUrl = (home) => {
    if (home.image_url) return home.image_url;
    const propertyImages = {
      house: 'https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=600&h=400&fit=crop&crop=center',
      apartment: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=600&h=400&fit=crop&crop=center',
      condo: 'https://images.unsplash.com/photo-1560448204-e1a3ecba47d2?w=600&h=400&fit=crop&crop=center',
      commercial: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600&h=400&fit=crop&crop=center',
      other: 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=600&h=400&fit=crop&crop=center'
    };
    return propertyImages[home.property_type] || propertyImages.house;
  };

  const handleField = (e) => { const { name, value } = e.target; setForm(f => ({ ...f, [name]: value })); };
  const handleSave = () => {
    const updated = {
      ...home,
      ...form,
      purchase_price: form.purchase_price === '' ? undefined : Number(form.purchase_price),
      square_footage: form.square_footage === '' ? undefined : Number(form.square_footage),
      bedrooms: form.bedrooms === '' ? undefined : Number(form.bedrooms),
      bathrooms: form.bathrooms === '' ? undefined : Number(form.bathrooms)
    };
    if (onUpdate) onUpdate(updated);
    setEditing(false);
  };

  const content = (
    <div className="fixed inset-0 z-[100]" role="dialog" aria-modal="true" aria-label={`Details for ${home.name}`}> {/* elevated z-index */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div ref={dialogRef} className="relative h-full flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className={`bg-gradient-to-r ${getPropertyTypeColor(home.property_type)} text-white p-6 relative`}>
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 hover:bg-white/20 rounded-full transition-colors"
              aria-label="Close"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
            <div className="flex items-start space-x-4">
              <div className="p-3 bg-white/20 rounded-lg">
                {getPropertyTypeIcon(home.property_type)}
              </div>
              <div className="flex-1">
                {editing ? (
                  <div className="space-y-2">
                    <input name="name" value={form.name} onChange={handleField} className="w-full bg-white/20 focus:bg-white/30 text-white placeholder-white/60 font-bold text-2xl rounded px-2 py-1 outline-none" placeholder="Name" />
                    <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                      <select name="property_type" value={form.property_type} onChange={handleField} className="bg-white/20 text-white rounded px-2 py-1 focus:bg-white/30 outline-none capitalize">
                        <option value="house">house</option>
                        <option value="apartment">apartment</option>
                        <option value="condo">condo</option>
                        <option value="commercial">commercial</option>
                        <option value="other">other</option>
                      </select>
                      <input name="address" value={form.address} onChange={handleField} className="flex-1 bg-white/20 focus:bg-white/30 text-white rounded px-2 py-1 outline-none" placeholder="Address" />
                    </div>
                  </div>
                ) : (
                  <>
                    <h2 className="text-3xl font-bold mb-2">{home.name}</h2>
                    <p className="text-white/90 text-lg capitalize mb-1">{home.property_type}</p>
                    <div className="flex items-center text-white/80">
                      <MapPinIcon className="h-5 w-5 mr-2" />
                      <span>{home.address}</span>
                    </div>
                  </>
                )}
              </div>
            </div>
            <div className="absolute left-6 top-6 flex gap-2">
              {!editing && (
                <button onClick={() => setEditing(true)} className="px-3 py-1 text-sm bg-white/20 hover:bg-white/30 rounded-md font-medium">Edit</button>
              )}
              {editing && (
                <>
                  <button onClick={handleSave} className="px-3 py-1 text-sm bg-green-500 hover:bg-green-600 text-white rounded-md font-medium">Save</button>
                  <button onClick={() => setEditing(false)} className="px-3 py-1 text-sm bg-white/20 hover:bg-white/30 rounded-md font-medium">Cancel</button>
                </>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column */}
              <div className="space-y-6">
                <div className="bg-gray-50 rounded-xl overflow-hidden">
                  <img src={getImageUrl(home)} alt={home.name} className="w-full h-64 object-cover" />
                </div>
                {editing ? (
                  <div className="bg-gray-50 rounded-xl p-4 space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                      <textarea name="description" value={form.description} onChange={handleField} rows={4} className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Purchase Date</label>
                        <input type="date" name="purchase_date" value={form.purchase_date} onChange={handleField} className="w-full border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Purchase Price</label>
                        <input type="number" name="purchase_price" value={form.purchase_price} onChange={handleField} className="w-full border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" />
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    {home.description && (
                      <div className="bg-gray-50 rounded-xl p-4">
                        <div className="flex items-center mb-3">
                          <DocumentTextIcon className="h-5 w-5 mr-2 text-gray-600" />
                          <h3 className="text-lg font-semibold text-gray-900">Description</h3>
                        </div>
                        <p className="text-gray-700 leading-relaxed">{home.description}</p>
                      </div>
                    )}
                    <div className="bg-blue-50 rounded-xl p-4 border-l-4 border-blue-400">
                      <div className="flex items-center mb-3">
                        <CurrencyDollarIcon className="h-5 w-5 mr-2 text-blue-600" />
                        <h3 className="text-lg font-semibold text-blue-900">Purchase Information</h3>
                      </div>
                      <div className="grid grid-cols-1 gap-3">
                        {home.purchase_date && (
                          <div className="flex items-center justify-between">
                            <span className="text-blue-700 font-medium flex items-center">
                              <CalendarIcon className="h-4 w-4 mr-2" />Purchase Date:
                            </span>
                            <span className="text-blue-900 font-semibold">{formatDate(home.purchase_date)}</span>
                          </div>
                        )}
                        {home.purchase_price && (
                          <div className="flex items-center justify-between">
                            <span className="text-blue-700 font-medium">Purchase Price:</span>
                            <span className="text-blue-900 font-bold text-lg">{formatCurrency(home.purchase_price)}</span>
                          </div>
                        )}
                        <div className="flex items-center justify-between">
                          <span className="text-blue-700 font-medium">Added to System:</span>
                          <span className="text-blue-900 font-semibold">{formatDate(home.created_at)}</span>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
              {/* Right Column */}
              <div className="space-y-6">
                <div className="bg-gray-50 rounded-xl p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Property Specifications</h3>
                  {editing ? (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-600">Square Footage</label>
                        <input type="number" name="square_footage" value={form.square_footage} onChange={handleField} className="mt-1 w-full border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600">Bedrooms</label>
                        <input type="number" name="bedrooms" value={form.bedrooms} onChange={handleField} className="mt-1 w-full border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600">Bathrooms</label>
                        <input type="number" name="bathrooms" value={form.bathrooms} onChange={handleField} className="mt-1 w-full border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600">Property Type</label>
                        <select name="property_type" value={form.property_type} onChange={handleField} className="mt-1 w-full border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 capitalize">
                          <option value="house">house</option>
                          <option value="apartment">apartment</option>
                          <option value="condo">condo</option>
                          <option value="commercial">commercial</option>
                          <option value="other">other</option>
                        </select>
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-4">
                      {home.square_footage && (
                        <div className="bg-white p-3 rounded-lg shadow-sm border-l-4 border-purple-400">
                          <p className="text-gray-500 text-sm">Square Footage</p>
                          <p className="font-bold text-purple-600 text-xl">{home.square_footage.toLocaleString()} sq ft</p>
                        </div>
                      )}
                      {home.bedrooms && (
                        <div className="bg-white p-3 rounded-lg shadow-sm border-l-4 border-blue-400">
                          <p className="text-gray-500 text-sm">Bedrooms</p>
                          <p className="font-bold text-blue-600 text-xl">{home.bedrooms}</p>
                        </div>
                      )}
                      {home.bathrooms && (
                        <div className="bg-white p-3 rounded-lg shadow-sm border-l-4 border-green-400">
                          <p className="text-gray-500 text-sm">Bathrooms</p>
                          <p className="font-bold text-green-600 text-xl">{home.bathrooms}</p>
                        </div>
                      )}
                      <div className="bg-white p-3 rounded-lg shadow-sm border-l-4 border-orange-400">
                        <p className="text-gray-500 text-sm">Property Type</p>
                        <p className="font-bold text-orange-600 text-lg capitalize">{home.property_type}</p>
                      </div>
                    </div>
                  )}
                </div>
                {!editing && (
                  <div className="bg-orange-50 rounded-xl p-4 border-l-4 border-orange-400">
                    <div className="flex items-center mb-3">
                      <WrenchScrewdriverIcon className="h-5 w-5 mr-2 text-orange-600" />
                      <h3 className="text-lg font-semibold text-orange-900">Equipment Overview</h3>
                    </div>
                    <div className="grid grid-cols-1 gap-3">
                      <div className="flex items-center justify-between bg-white p-3 rounded-lg">
                        <span className="text-orange-700 font-medium">Equipment Count:</span>
                        <span className="text-orange-900 font-bold text-xl">{home.equipment_count}</span>
                      </div>
                      <div className="flex items-center justify-between bg-white p-3 rounded-lg">
                        <span className="text-orange-700 font-medium">Total Equipment Value:</span>
                        <span className="text-orange-900 font-bold text-xl">{formatCurrency(home.total_equipment_value)}</span>
                      </div>
                    </div>
                  </div>
                )}
                {!editing && (
                  <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-4 border border-green-200">
                    <h3 className="text-lg font-semibold text-green-900 mb-4">Property Value Summary</h3>
                    <div className="space-y-3">
                      {home.purchase_price && (
                        <div className="flex items-center justify-between">
                          <span className="text-green-700 font-medium">Property Value:</span>
                          <span className="text-green-900 font-bold text-lg">{formatCurrency(home.purchase_price)}</span>
                        </div>
                      )}
                      <div className="flex items-center justify-between">
                        <span className="text-green-700 font-medium">Equipment Value:</span>
                        <span className="text-green-900 font-bold text-lg">{formatCurrency(home.total_equipment_value)}</span>
                      </div>
                      <div className="border-t border-green-200 pt-3">
                        <div className="flex items-center justify-between">
                          <span className="text-green-800 font-bold">Total Investment:</span>
                          <span className="text-green-900 font-bold text-xl">{formatCurrency((home.purchase_price || 0) + home.total_equipment_value)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Footer */}
          {!editing && (
            <div className="bg-gray-50 px-6 py-4 border-t">
              <div className="flex justify-end space-x-3">
                <button onClick={onClose} className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Close</button>
                {onEdit && <button className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors" onClick={() => setEditing(true)}>Edit Property</button>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(content, document.body);
};

HomeDetailsModal.propTypes = {
  home: PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    address: PropTypes.string.isRequired,
    description: PropTypes.string,
    purchase_date: PropTypes.string,
    purchase_price: PropTypes.number,
    property_type: PropTypes.string.isRequired,
    square_footage: PropTypes.number,
    bedrooms: PropTypes.number,
    bathrooms: PropTypes.number,
    created_at: PropTypes.string.isRequired,
    equipment_count: PropTypes.number.isRequired,
    total_equipment_value: PropTypes.number.isRequired,
    image_url: PropTypes.string
  }),
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onEdit: PropTypes.func,
  onUpdate: PropTypes.func,
  startInEdit: PropTypes.bool
};

export default HomeDetailsModal;
