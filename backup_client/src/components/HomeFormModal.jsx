import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { XMarkIcon } from '@heroicons/react/24/outline';

const emptyForm = {
  name: '',
  address: '',
  description: '',
  purchase_date: '',
  purchase_price: '',
  property_type: 'house',
  square_footage: '',
  bedrooms: '',
  bathrooms: ''
};

const HomeFormModal = ({ home, isOpen, onClose, onSave }) => {
  const [form, setForm] = useState(emptyForm);

  useEffect(() => {
    if (home) {
      setForm({
        name: home.name || '',
        address: home.address || '',
        description: home.description || '',
        purchase_date: home.purchase_date ? home.purchase_date.substring(0,10) : '',
        purchase_price: home.purchase_price || '',
        property_type: home.property_type || 'house',
        square_footage: home.square_footage || '',
        bedrooms: home.bedrooms || '',
        bathrooms: home.bathrooms || ''
      });
    } else {
      setForm(emptyForm);
    }
  }, [home]);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(f => ({ ...f, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      ...home,
      ...form,
      purchase_price: form.purchase_price ? Number(form.purchase_price) : undefined,
      square_footage: form.square_footage ? Number(form.square_footage) : undefined,
      bedrooms: form.bedrooms ? Number(form.bedrooms) : undefined,
      bathrooms: form.bathrooms ? Number(form.bathrooms) : undefined
    };
    onSave(payload);
  };

  return (
    <div className="fixed inset-0 z-[110]" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative h-full flex items-center justify-center p-4">
        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <h2 className="text-xl font-semibold text-gray-900">{home ? 'Edit Home' : 'Add Home'}</h2>
            <button type="button" onClick={onClose} className="p-2 hover:bg-gray-100 rounded-md" aria-label="Close"><XMarkIcon className="h-6 w-6" /></button>
          </div>
          <div className="p-6 space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input name="name" value={form.name} onChange={handleChange} required className="mt-1 w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Property Type</label>
                <select name="property_type" value={form.property_type} onChange={handleChange} className="mt-1 w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                  <option value="house">House</option>
                  <option value="apartment">Apartment</option>
                  <option value="condo">Condo</option>
                  <option value="commercial">Commercial</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700">Address</label>
                <input name="address" value={form.address} onChange={handleChange} required className="mt-1 w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Purchase Date</label>
                <input type="date" name="purchase_date" value={form.purchase_date} onChange={handleChange} className="mt-1 w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Purchase Price</label>
                <input type="number" name="purchase_price" value={form.purchase_price} onChange={handleChange} className="mt-1 w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Square Footage</label>
                <input type="number" name="square_footage" value={form.square_footage} onChange={handleChange} className="mt-1 w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Bedrooms</label>
                <input type="number" name="bedrooms" value={form.bedrooms} onChange={handleChange} className="mt-1 w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Bathrooms</label>
                <input type="number" name="bathrooms" value={form.bathrooms} onChange={handleChange} className="mt-1 w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea name="description" value={form.description} onChange={handleChange} rows={3} className="mt-1 w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
              </div>
            </div>
          </div>
          <div className="px-6 py-4 bg-gray-50 border-t flex justify-end space-x-3">
            <button type="button" onClick={onClose} className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
            <button type="submit" className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700">{home ? 'Save Changes' : 'Add Home'}</button>
          </div>
        </form>
      </div>
    </div>
  );
};

HomeFormModal.propTypes = {
  home: PropTypes.object,
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSave: PropTypes.func.isRequired
};

export default HomeFormModal;
