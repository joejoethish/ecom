'use client';

import { useState, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '@/hooks/redux';
import { 
  fetchCustomerAddresses, 
  createCustomerAddress, 
  updateCustomerAddress, 
  deleteCustomerAddress 
} from '@/store/slices/customerSlice';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Address } from '@/types';
import { ADDRESS_TYPES } from '@/constants';
import toast from 'react-hot-toast';

interface AddressFormData {
  type: 'HOME' | 'WORK' | 'OTHER' | 'shipping';
  first_name: string;
  last_name: string;
  company?: string;
  address_line_1: string;
  address_line_2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  phone?: string;
  is_default: boolean;
}

const initialFormData: AddressFormData = {
  type: 'HOME',
  first_name: '',
  last_name: '',
  company: '',
  address_line_1: '',
  address_line_2: '',
  city: '',
  state: '',
  postal_code: '',
  country: 'US',
  phone: '',
  is_default: false,
};

export function AddressManagement() {
  const dispatch = useAppDispatch();
  const { addresses, loading } = useAppSelector((state) => state.customer);
  
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingAddress, setEditingAddress] = useState<Address | null>(null);
  const [formData, setFormData] = useState<AddressFormData>(initialFormData);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    dispatch(fetchCustomerAddresses());
  }, [dispatch]);

  useEffect(() => {
    if (editingAddress) {
      setFormData({
        type: editingAddress.type,
        first_name: editingAddress.first_name,
        last_name: editingAddress.last_name,
        company: editingAddress.company || '',
        address_line_1: editingAddress.address_line_1,
        address_line_2: editingAddress.address_line_2 || '',
        city: editingAddress.city,
        state: editingAddress.state,
        postal_code: editingAddress.postal_code,
        country: editingAddress.country,
        phone: editingAddress.phone || '',
        is_default: editingAddress.is_default,
      });
    } else {
      setFormData(initialFormData);
    }
  }, [editingAddress]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.first_name.trim()) newErrors.first_name = 'First name is required';
    if (!formData.last_name.trim()) newErrors.last_name = 'Last name is required';
    if (!formData.address_line_1.trim()) newErrors.address_line_1 = 'Address is required';
    if (!formData.city.trim()) newErrors.city = 'City is required';
    if (!formData.state.trim()) newErrors.state = 'State is required';
    if (!formData.postal_code.trim()) newErrors.postal_code = 'Postal code is required';
    if (!formData.country.trim()) newErrors.country = 'Country is required';

    // Phone validation (optional)
    if (formData.phone && !/^[\+]?[1-9][\d]{0,15}$/.test(formData.phone)) {
      newErrors.phone = 'Please enter a valid phone number';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      if (editingAddress) {
        await dispatch(updateCustomerAddress({
          id: editingAddress.id,
          addressData: formData,
        })).unwrap();
        toast.success('Address updated successfully!');
      } else {
        await dispatch(createCustomerAddress(formData)).unwrap();
        toast.success('Address added successfully!');
      }
      
      handleCloseForm();
    } catch (error: any) {
      toast.error(error || 'Failed to save address');
    }
  };

  const handleEdit = (address: Address) => {
    setEditingAddress(address);
    setIsFormOpen(true);
  };

  const handleDelete = async (address: Address) => {
    if (window.confirm('Are you sure you want to delete this address?')) {
      try {
        await dispatch(deleteCustomerAddress(address.id)).unwrap();
        toast.success('Address deleted successfully!');
      } catch (error: any) {
        toast.error(error || 'Failed to delete address');
      }
    }
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setEditingAddress(null);
    setFormData(initialFormData);
    setErrors({});
  };

  const handleRefresh = async () => {
    try {
      await dispatch(fetchCustomerAddresses()).unwrap();
      toast.success('Addresses refreshed');
    } catch (error: any) {
      toast.error('Failed to refresh addresses');
    }
  };

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            My Addresses
            {addresses.length > 0 && (
              <span className="ml-2 text-sm text-gray-500">
                ({addresses.length} {addresses.length === 1 ? 'address' : 'addresses'})
              </span>
            )}
          </h2>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              loading={loading}
            >
              Refresh
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsFormOpen(true)}
            >
              Add Address
            </Button>
          </div>
        </div>
      </div>

      <div className="px-6 py-4">
        {addresses.length === 0 ? (
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No addresses found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Add your first address to get started with faster checkout.
            </p>
            <div className="mt-6">
              <Button
                variant="primary"
                onClick={() => setIsFormOpen(true)}
              >
                Add Address
              </Button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {addresses.map((address) => (
              <div
                key={address.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        address.type === 'HOME' ? 'bg-blue-100 text-blue-800' :
                        address.type === 'WORK' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {address.type}
                      </span>
                      {address.is_default && (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                          Default
                        </span>
                      )}
                    </div>
                    
                    <div className="text-sm text-gray-900">
                      <p className="font-medium">
                        {address.first_name} {address.last_name}
                      </p>
                      {address.company && (
                        <p className="text-gray-600">{address.company}</p>
                      )}
                      <p>{address.address_line_1}</p>
                      {address.address_line_2 && <p>{address.address_line_2}</p>}
                      <p>
                        {address.city}, {address.state} {address.postal_code}
                      </p>
                      <p>{address.country}</p>
                      {address.phone && (
                        <p className="text-gray-600">Phone: {address.phone}</p>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="flex justify-end space-x-2 mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(address)}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(address)}
                    className="text-red-600 hover:text-red-700"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Address Form Modal */}
      {isFormOpen && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  {editingAddress ? 'Edit Address' : 'Add New Address'}
                </h3>
                <button
                  onClick={handleCloseForm}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Address Type
                    </label>
                    <select
                      name="type"
                      value={formData.type}
                      onChange={handleChange}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                      <option value="HOME">Home</option>
                      <option value="WORK">Work</option>
                      <option value="OTHER">Other</option>
                    </select>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      id="is_default"
                      name="is_default"
                      type="checkbox"
                      checked={formData.is_default}
                      onChange={handleChange}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="is_default" className="ml-2 block text-sm text-gray-900">
                      Set as default address
                    </label>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="First Name"
                    name="first_name"
                    type="text"
                    value={formData.first_name}
                    onChange={handleChange}
                    error={errors.first_name}
                    required
                  />
                  <Input
                    label="Last Name"
                    name="last_name"
                    type="text"
                    value={formData.last_name}
                    onChange={handleChange}
                    error={errors.last_name}
                    required
                  />
                </div>

                <Input
                  label="Company (Optional)"
                  name="company"
                  type="text"
                  value={formData.company}
                  onChange={handleChange}
                />

                <Input
                  label="Address Line 1"
                  name="address_line_1"
                  type="text"
                  value={formData.address_line_1}
                  onChange={handleChange}
                  error={errors.address_line_1}
                  required
                />

                <Input
                  label="Address Line 2 (Optional)"
                  name="address_line_2"
                  type="text"
                  value={formData.address_line_2}
                  onChange={handleChange}
                />

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Input
                    label="City"
                    name="city"
                    type="text"
                    value={formData.city}
                    onChange={handleChange}
                    error={errors.city}
                    required
                  />
                  <Input
                    label="State"
                    name="state"
                    type="text"
                    value={formData.state}
                    onChange={handleChange}
                    error={errors.state}
                    required
                  />
                  <Input
                    label="Postal Code"
                    name="postal_code"
                    type="text"
                    value={formData.postal_code}
                    onChange={handleChange}
                    error={errors.postal_code}
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Country"
                    name="country"
                    type="text"
                    value={formData.country}
                    onChange={handleChange}
                    error={errors.country}
                    required
                  />
                  <Input
                    label="Phone (Optional)"
                    name="phone"
                    type="tel"
                    value={formData.phone}
                    onChange={handleChange}
                    error={errors.phone}
                    placeholder="+1234567890"
                  />
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCloseForm}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    loading={loading}
                  >
                    {editingAddress ? 'Update Address' : 'Add Address'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}