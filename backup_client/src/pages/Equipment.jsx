import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { PlusIcon, WrenchScrewdriverIcon, TagIcon, CalendarIcon, ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import EquipmentPageCard from '../components/EquipmentPageCard';
import EquipmentModal from '../components/EquipmentModal';
import EquipmentDetailsModal from '../components/EquipmentDetailsModal';
import { equipmentAPI } from '../services/equipmentAPI';

const Equipment = () => {
  const [selectedHome, setSelectedHome] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [selectedEquipment, setSelectedEquipment] = useState(null);
  const [equipmentForDetails, setEquipmentForDetails] = useState(null);
  const queryClient = useQueryClient();

  const { data: equipment = [], isLoading: equipmentLoading } = useQuery(
    ['equipment', selectedHome, statusFilter, typeFilter],
    () => equipmentAPI.getEquipment({
      home: selectedHome !== 'all' ? selectedHome : undefined,
      status: statusFilter !== 'all' ? statusFilter : undefined,
      equipmentType: typeFilter !== 'all' ? typeFilter : undefined
    }),
    { refetchInterval: 30000 }
  );

  const { data: equipmentStats } = useQuery(
    ['equipment-stats'],
    () => equipmentAPI.getEquipmentStats()
  );

  const createMutation = useMutation(
    (equipmentData) => equipmentAPI.createEquipment(equipmentData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['equipment']);
        queryClient.invalidateQueries(['equipment-stats']);
        setIsModalOpen(false);
      },
      onError: (error) => {
        console.error('Error creating equipment:', error);
      }
    }
  );

  const updateMutation = useMutation(
    ({ id, data }) => equipmentAPI.updateEquipment(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['equipment']);
        queryClient.invalidateQueries(['equipment-stats']);
        setIsModalOpen(false);
      },
      onError: (error) => {
        console.error('Error updating equipment:', error);
      }
    }
  );

  const deleteMutation = useMutation(
    (equipmentId) => equipmentAPI.deleteEquipment(equipmentId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['equipment']);
        queryClient.invalidateQueries(['equipment-stats']);
      },
      onError: (error) => {
        console.error('Error deleting equipment:', error);
      }
    }
  );

  const filteredEquipment = equipment.filter(item => {
    if (selectedHome !== 'all' && item.home?.id !== selectedHome) return false;
    if (statusFilter !== 'all' && item.status !== statusFilter) return false;
    if (typeFilter !== 'all' && item.equipment_type !== typeFilter) return false;
    return true;
  });

  const defaultStats = {
    total: equipment.length,
    operational: equipment.filter(e => e.status === 'operational').length,
    maintenance: equipment.filter(e => e.status === 'maintenance').length,
    broken: equipment.filter(e => e.status === 'broken').length,
    retired: equipment.filter(e => e.status === 'retired').length
  };

  const statusColors = { operational: 'text-green-600 bg-green-100', maintenance: 'text-yellow-600 bg-yellow-100', broken: 'text-red-600 bg-red-100', retired: 'text-gray-600 bg-gray-100' };
  const statusIcons = { operational: CheckCircleIcon, maintenance: CalendarIcon, broken: ExclamationTriangleIcon, retired: TagIcon };

  const equipmentTypes = [ { value: 'all', label: 'All Types' }, { value: 'home_appliance', label: 'Home Appliances' }, { value: 'electronic', label: 'Electronics' }, { value: 'hvac', label: 'HVAC' }, { value: 'vehicle', label: 'Vehicles' }, { value: 'smart_device', label: 'Smart Devices' }, { value: 'power_tool', label: 'Power Tools' }, { value: 'medical_equipment', label: 'Medical Equipment' } ];

  const handleAddEquipment = () => { setSelectedEquipment(null); setIsModalOpen(true); };
  const handleEditEquipment = (equipment) => { setSelectedEquipment(equipment); setIsModalOpen(true); };
  const handleDeleteEquipment = async (id) => {
    if (window.confirm('Are you sure you want to delete this equipment?')) {
      try {
        await deleteMutation.mutateAsync(id);
      } catch (error) {
        console.error('Failed to delete equipment:', error);
      }
    }
  };
  const handleViewDetails = (equipment) => { setEquipmentForDetails(equipment); setIsDetailsModalOpen(true); };

  const handleSubmitEquipment = async (data, id) => {
    try {
      if (id) {
        await updateMutation.mutateAsync({ id, data });
      } else {
        await createMutation.mutateAsync(data);
      }
    } catch (error) {
      console.error('Failed to save equipment:', error);
    }
  };

  const currentStats = equipmentStats || defaultStats;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div><h1 className="text-2xl font-bold text-gray-900">Equipment Management</h1><p className="text-gray-600">Manage your home and business equipment</p></div>
        <button onClick={handleAddEquipment} className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"><PlusIcon className="h-4 w-4 mr-2" /> Add Equipment</button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow p-6"><div className="flex items-center"><WrenchScrewdriverIcon className="h-8 w-8 text-blue-600" /><div className="ml-4"><p className="text-sm font-medium text-gray-600">Total Equipment</p><p className="text-2xl font-semibold text-gray-900">{currentStats.total}</p></div></div></div>
        {Object.entries(currentStats).slice(1).map(([status, count]) => { const Icon = statusIcons[status]; return (<div key={status} className="bg-white rounded-lg shadow p-6"><div className="flex items-center"><Icon className={`h-8 w-8 ${statusColors[status].split(' ')[0]}`} /><div className="ml-4"><p className="text-sm font-medium text-gray-600 capitalize">{status}</p><p className="text-2xl font-semibold text-gray-900">{count}</p></div></div></div>); })}
      </div>
      <div className="bg-white rounded-lg shadow p-6"><div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div><label className="block text-sm font-medium text-gray-700 mb-2">Home</label><select value={selectedHome} onChange={(e) => setSelectedHome(e.target.value)} className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"><option value="all">All Homes</option></select></div>
        <div><label className="block text-sm font-medium text-gray-700 mb-2">Type</label><select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">{equipmentTypes.map(type => <option key={type.value} value={type.value}>{type.label}</option>)}</select></div>
        <div><label className="block text-sm font-medium text-gray-700 mb-2">Status</label><select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"><option value="all">All Status</option><option value="operational">Operational</option><option value="maintenance">Maintenance</option><option value="broken">Broken</option><option value="retired">Retired</option></select></div>
        <div className="flex items-end"><button onClick={() => { setSelectedHome('all'); setStatusFilter('all'); setTypeFilter('all'); }} className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">Clear Filters</button></div>
      </div></div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {equipmentLoading ? Array.from({ length: 6 }).map((_, i) => (<div key={i} className="bg-white rounded-lg shadow animate-pulse"><div className="h-64 bg-gray-200" /><div className="p-6 space-y-3"><div className="h-4 bg-gray-200 rounded w-3/4" /><div className="h-4 bg-gray-200 rounded w-1/2" /><div className="h-4 bg-gray-200 rounded w-2/3" /></div></div>)) : filteredEquipment.length>0 ? filteredEquipment.map(eq => (<EquipmentPageCard key={eq.id} equipment={eq} onEdit={handleEditEquipment} onDelete={handleDeleteEquipment} onViewDetails={handleViewDetails} />)) : (<div className="col-span-full text-center py-12"><WrenchScrewdriverIcon className="mx-auto h-12 w-12 text-gray-400" /><h3 className="mt-2 text-sm font-medium text-gray-900">No equipment found</h3><p className="mt-1 text-sm text-gray-500">{selectedHome!=='all'||statusFilter!=='all'||typeFilter!=='all' ? 'Try adjusting your filters or add new equipment.' : 'Get started by adding your first piece of equipment.'}</p><div className="mt-6"><button onClick={handleAddEquipment} className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"><PlusIcon className="h-4 w-4 mr-2" /> Add Equipment</button></div></div>)}
      </div>
      <EquipmentModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} equipment={selectedEquipment} onSubmit={handleSubmitEquipment} />
      <EquipmentDetailsModal isOpen={isDetailsModalOpen} onClose={() => setIsDetailsModalOpen(false)} equipment={equipmentForDetails} />
    </div>
  );
};

export default Equipment;
