import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { X } from 'lucide-react';

const EquipmentModal = ({ isOpen, onClose, equipment, onSubmit }) => {
  const [formData, setFormData] = useState({
    name: '',
    equipment_type: '',
    brand_id: '',
    model_name: '',
    model_number: '',
    home_id: '',
    room: '',
    serial_number: '',
    purchase_date: '',
    purchase_price: '',
    warranty_expires: '',
    status: 'operational',
    notes: ''
  });
  // New state for dynamic custom specification fields
  const [specifications, setSpecifications] = useState([{ key: '', value: '' }]);

  useEffect(() => {
    if (equipment) {
      setFormData({
        name: equipment.name || '',
        equipment_type: equipment.equipment_type || '',
        brand_id: equipment.brand?.id || '',
        model_name: equipment.model?.name || '',
        model_number: equipment.model?.model_number || '',
        home_id: equipment.home?.id || '',
        room: equipment.room || '',
        serial_number: equipment.serial_number || '',
        purchase_date: equipment.purchase_date || '',
        purchase_price: equipment.purchase_price != null ? equipment.purchase_price.toString() : '',
        warranty_expires: equipment.warranty_expires || '',
        status: equipment.status || 'operational',
        notes: equipment.notes || ''
      });
      // Load existing specifications into editable pairs
      const existingSpecs = equipment.specifications ? Object.entries(equipment.specifications) : [];
      if (existingSpecs.length > 0) {
        setSpecifications(existingSpecs.map(([k, v]) => ({ key: k, value: String(v) })));
      } else {
        setSpecifications([{ key: '', value: '' }]);
      }
    } else {
      setFormData(prev => ({ ...prev, name: '', equipment_type: '', brand_id: '', model_name: '', model_number: '', home_id: '', room: '', serial_number: '', purchase_date: '', purchase_price: '', warranty_expires: '', status: 'operational', notes: '' }));
      setSpecifications([{ key: '', value: '' }]);
    }
  }, [equipment, isOpen]);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(f => ({ ...f, [name]: value }));
  };

  const handleSpecChange = (index, field, value) => {
    setSpecifications(specs => specs.map((s, i) => i === index ? { ...s, [field]: value } : s));
  };

  const addSpecRow = () => {
    setSpecifications(specs => [...specs, { key: '', value: '' }]);
  };

  const removeSpecRow = (index) => {
    setSpecifications(specs => specs.filter((_, i) => i !== index));
  };

  const parseValue = (val) => {
    if (val === 'true') return true;
    if (val === 'false') return false;
    if (val !== '' && !isNaN(val)) return Number(val);
    return val;
  };

  const buildSpecificationsObject = () => {
    const obj = {};
    specifications.forEach(({ key, value }) => {
      const trimmedKey = key.trim();
      if (!trimmedKey) return; // skip empty keys
      obj[trimmedKey.replace(/\s+/g, '_').toLowerCase()] = parseValue(value.trim());
    });
    return obj;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const specsObj = buildSpecificationsObject();
    const payload = { ...formData, specifications: specsObj };
    if (onSubmit) onSubmit(payload, equipment?.id);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen p-4 text-center">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={onClose}></div>
        <div className="bg-white rounded-lg shadow-xl transform transition-all w-full max-w-2xl text-left overflow-hidden relative">
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-medium text-gray-900">{equipment ? 'Edit Equipment' : 'Add Equipment'}</h3>
              <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600">
                <X className="h-6 w-6" />
              </button>
            </div>
            {/* Basic Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name*</label>
                <input required name="name" value={formData.name} onChange={handleChange} className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500" placeholder="Living Room TV" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type*</label>
                <input required name="equipment_type" value={formData.equipment_type} onChange={handleChange} className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500" placeholder="electronic" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Brand</label>
                <input name="brand_id" value={formData.brand_id} onChange={handleChange} className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500" placeholder="1" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Model Name</label>
                <input name="model_name" value={formData.model_name} onChange={handleChange} className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500" placeholder="QN85A" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Model Number</label>
                <input name="model_number" value={formData.model_number} onChange={handleChange} className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500" placeholder="QN55QN85AAFXZA" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Home</label>
                <input name="home_id" value={formData.home_id} onChange={handleChange} className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500" placeholder="1" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Room</label>
                <input name="room" value={formData.room} onChange={handleChange} className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500" placeholder="Living Room" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Serial Number</label>
                <input name="serial_number" value={formData.serial_number} onChange={handleChange} className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500" placeholder="SN123456" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Purchase Date</label>
                <input type="date" name="purchase_date" value={formData.purchase_date} onChange={handleChange} className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Purchase Price</label>
                <input type="number" step="0.01" name="purchase_price" value={formData.purchase_price} onChange={handleChange} className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500" placeholder="0.00" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Warranty Expires</label>
                <input type="date" name="warranty_expires" value={formData.warranty_expires} onChange={handleChange} className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select name="status" value={formData.status} onChange={handleChange} className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500">
                  <option value="operational">Operational</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="broken">Broken</option>
                  <option value="retired">Retired</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea name="notes" value={formData.notes} onChange={handleChange} rows={3} className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500" placeholder="Additional notes..." />
              </div>
            </div>
            {/* Dynamic Specifications */}
            <div className="pt-4 border-t">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-md font-semibold text-gray-900">Custom Specifications</h4>
                <button type="button" onClick={addSpecRow} className="px-2 py-1 text-sm rounded-md bg-blue-100 text-blue-700 hover:bg-blue-200">Add Field</button>
              </div>
              <p className="text-xs text-gray-500 mb-2">Add any additional attributes (e.g. Screen Size, Energy Star, Voltage). Keys will be normalized to snake_case.</p>
              <div className="space-y-2">
                {specifications.map((spec, idx) => (
                  <div key={idx} className="flex items-start space-x-2">
                    <div className="flex-1">
                      <input
                        type="text"
                        placeholder="Field Name (e.g. Energy Star)"
                        value={spec.key}
                        onChange={(e) => handleSpecChange(idx, 'key', e.target.value)}
                        className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500 text-sm"
                      />
                    </div>
                    <div className="flex-1">
                      <input
                        type="text"
                        placeholder="Value (e.g. true / 55 inches)"
                        value={spec.value}
                        onChange={(e) => handleSpecChange(idx, 'value', e.target.value)}
                        className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500 text-sm"
                      />
                    </div>
                    {specifications.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeSpecRow(idx)}
                        className="px-2 py-1 text-xs rounded-md bg-red-100 text-red-600 hover:bg-red-200"
                        aria-label="Remove field"
                      >Remove</button>
                    )}
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-gray-50 -m-6 mt-4 p-4 flex justify-end space-x-3 border-t">
              <button type="button" onClick={onClose} className="px-4 py-2 rounded-md border text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">Cancel</button>
              <button type="submit" className="px-4 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">{equipment ? 'Update' : 'Add'}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

EquipmentModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  equipment: PropTypes.object,
  onSubmit: PropTypes.func,
};

export default EquipmentModal;
