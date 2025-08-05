'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Card } from '@/components/ui/card';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { ErrorBoundary, ErrorDisplay, EmptyState } from '@/components/ui/ErrorBoundary';
import { SkeletonWarehouseCard } from '@/components/ui/SkeletonLoader';
import { Plus, Edit, Trash2, Warehouse, MapPin, Phone, Mail, User, X, RefreshCw } from 'lucide-react';
import { 
  inventoryManagementApi, 
  type Warehouse as WarehouseType,
  type CreateWarehouseRequest,
  type UpdateWarehouseRequest
} from '@/services/inventoryManagementApi';
import { validateRequired, validateForm } from '@/utils/validation';
import { handleApiResponse, showErrorToast, showSuccessToast, formatValidationErrors } from '@/utils/errorHandling';

interface WarehouseFormProps {
  warehouse?: WarehouseType | null;
  onClose: () => void;
  onSave: () => void;
}

interface FormData {
  name: string;
  code: string;
  address: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  phone: string;
  email: string;
  manager: string;
  is_active: boolean;
}

interface FormErrors {
  name?: string;
  code?: string;
  address?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  phone?: string;
  email?: string;
  manager?: string;
  general?: string;
}

function WarehouseForm({ warehouse, onClose, onSave }: WarehouseFormProps) {
  const [formData, setFormData] = useState<FormData>({
    name: warehouse?.name || '',
    code: warehouse?.code || '',
    address: warehouse?.address || '',
    city: warehouse?.city || '',
    state: warehouse?.state || '',
    postal_code: warehouse?.postal_code || '',
    country: warehouse?.country || '',
    phone: warehouse?.phone || '',
    email: warehouse?.email || '',
    manager: warehouse?.manager || '',
    is_active: warehouse?.is_active ?? true,
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [existingWarehouses, setExistingWarehouses] = useState<WarehouseType[]>([]);

  const isEditing = !!warehouse;

  useEffect(() => {
    fetchExistingWarehouses();
  }, []);

  const fetchExistingWarehouses = async () => {
    try {
      const response = await inventoryManagementApi.getWarehouses();
      if (response.success && response.data) {
        setExistingWarehouses(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch existing warehouses:', error);
    }
  };

  const handleInputChange = (field: keyof FormData, value: string | boolean) => {
    setFormData({ ...formData, [field]: value });
    // Clear field error when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors({ ...errors, [field]: undefined });
    }
  };

  const validateEmail = (email: string): string | null => {
    if (!email.trim()) return null; // Email is optional
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return 'Please enter a valid email address';
    }
    return null;
  };

  const validatePhone = (phone: string): string | null => {
    if (!phone.trim()) return null; // Phone is optional
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
    if (!phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''))) {
      return 'Please enter a valid phone number';
    }
    return null;
  };

  const validateWarehouseCode = (code: string): string | null => {
    const required = validateRequired(code, 'Warehouse code');
    if (required) return required;

    // Check for uniqueness
    const isDuplicate = existingWarehouses.some(w => 
      w.code.toLowerCase() === code.toLowerCase() && 
      (!isEditing || w.id !== warehouse?.id)
    );
    
    if (isDuplicate) {
      return 'Warehouse code already exists. Please choose a different code.';
    }

    // Check format (alphanumeric, underscores, hyphens)
    if (!/^[A-Za-z0-9_-]+$/.test(code)) {
      return 'Warehouse code can only contain letters, numbers, underscores, and hyphens';
    }

    return null;
  };

  const validateFormData = (): FormErrors => {
    const validationRules = {
      name: (value: string) => validateRequired(value, 'Warehouse name'),
      code: (value: string) => validateWarehouseCode(value),
      address: (value: string) => validateRequired(value, 'Address'),
      city: (value: string) => validateRequired(value, 'City'),
      state: (value: string) => validateRequired(value, 'State'),
      postal_code: (value: string) => validateRequired(value, 'Postal code'),
      country: (value: string) => validateRequired(value, 'Country'),
      phone: (value: string) => validatePhone(value),
      email: (value: string) => validateEmail(value),
      manager: (value: string) => validateRequired(value, 'Manager name'),
    };

    return validateForm(formData, validationRules);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationErrors = validateFormData();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      let response;
      
      if (isEditing && warehouse) {
        const updateData: UpdateWarehouseRequest = {
          name: formData.name,
          code: formData.code,
          address: formData.address,
          city: formData.city,
          state: formData.state,
          postal_code: formData.postal_code,
          country: formData.country,
          phone: formData.phone,
          email: formData.email,
          manager: formData.manager,
          is_active: formData.is_active,
        };
        
        response = await inventoryManagementApi.updateWarehouse(warehouse.id, updateData);
      } else {
        const createData: CreateWarehouseRequest = {
          name: formData.name,
          code: formData.code,
          address: formData.address,
          city: formData.city,
          state: formData.state,
          postal_code: formData.postal_code,
          country: formData.country,
          phone: formData.phone,
          email: formData.email,
          manager: formData.manager,
          is_active: formData.is_active,
        };
        
        response = await inventoryManagementApi.createWarehouse(createData);
      }

      const result = handleApiResponse(response, {
        successMessage: `Warehouse ${isEditing ? 'updated' : 'created'} successfully`,
        showSuccessToast: true
      });

      if (result.success) {
        onSave();
        onClose();
      } else if (result.error) {
        // Handle validation errors
        if (result.error.type === 'validation') {
          const formErrors = formatValidationErrors(result.error);
          setErrors(formErrors);
        } else {
          setErrors({ 
            general: result.error.message || `Failed to ${isEditing ? 'update' : 'create'} warehouse. Please try again.` 
          });
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="warehouse-form-title"
    >
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="flex items-center justify-between p-4 sm:p-6 border-b">
          <h2 id="warehouse-form-title" className="text-lg sm:text-xl font-semibold">
            {isEditing ? 'Edit Warehouse' : 'Add Warehouse'}
          </h2>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onClose}
            className="min-h-[44px] min-w-[44px] p-2"
            aria-label="Close form"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 sm:p-6 space-y-4 sm:space-y-6">
          {errors.general && (
            <div 
              className="bg-red-50 border border-red-200 rounded-md p-4"
              role="alert"
              aria-live="polite"
            >
              <p className="text-sm text-red-600">{errors.general}</p>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Basic Information</h3>
              
              <div className="space-y-2">
                <Label htmlFor="name">Warehouse Name *</Label>
                <Input
                  id="name"
                  placeholder="Enter warehouse name"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  error={errors.name}
                  className="min-h-[44px]"
                  aria-describedby={errors.name ? "name-error" : undefined}
                  aria-invalid={!!errors.name}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="code">Warehouse Code *</Label>
                <Input
                  id="code"
                  placeholder="Enter unique warehouse code (e.g., WH001)"
                  value={formData.code}
                  onChange={(e) => handleInputChange('code', e.target.value.toUpperCase())}
                  error={errors.code}
                  helperText="Unique identifier for the warehouse (letters, numbers, underscores, hyphens only)"
                  className="min-h-[44px]"
                  aria-describedby={errors.code ? "code-error" : "code-help"}
                  aria-invalid={!!errors.code}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="manager">Manager Name *</Label>
                <Input
                  id="manager"
                  placeholder="Enter manager name"
                  value={formData.manager}
                  onChange={(e) => handleInputChange('manager', e.target.value)}
                  error={errors.manager}
                  className="min-h-[44px]"
                  aria-describedby={errors.manager ? "manager-error" : undefined}
                  aria-invalid={!!errors.manager}
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => handleInputChange('is_active', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 min-h-[20px] min-w-[20px]"
                />
                <Label htmlFor="is_active">Active warehouse</Label>
              </div>
            </div>

            {/* Contact Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Contact Information</h3>
              
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  placeholder="Enter phone number"
                  value={formData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  error={errors.phone}
                  className="min-h-[44px]"
                  aria-describedby={errors.phone ? "phone-error" : undefined}
                  aria-invalid={!!errors.phone}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter email address"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  error={errors.email}
                  className="min-h-[44px]"
                  aria-describedby={errors.email ? "email-error" : undefined}
                  aria-invalid={!!errors.email}
                />
              </div>
            </div>
          </div>

          {/* Address Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Address Information</h3>
            
            <div className="space-y-2">
              <Label htmlFor="address">Street Address *</Label>
              <Input
                id="address"
                placeholder="Enter street address"
                value={formData.address}
                onChange={(e) => handleInputChange('address', e.target.value)}
                error={errors.address}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="city">City *</Label>
                <Input
                  id="city"
                  placeholder="Enter city"
                  value={formData.city}
                  onChange={(e) => handleInputChange('city', e.target.value)}
                  error={errors.city}
                  className="min-h-[44px]"
                  aria-describedby={errors.city ? "city-error" : undefined}
                  aria-invalid={!!errors.city}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="state">State/Province *</Label>
                <Input
                  id="state"
                  placeholder="Enter state or province"
                  value={formData.state}
                  onChange={(e) => handleInputChange('state', e.target.value)}
                  error={errors.state}
                  className="min-h-[44px]"
                  aria-describedby={errors.state ? "state-error" : undefined}
                  aria-invalid={!!errors.state}
                />
              </div>

              <div className="space-y-2 sm:col-span-2 lg:col-span-1">
                <Label htmlFor="postal_code">Postal Code *</Label>
                <Input
                  id="postal_code"
                  placeholder="Enter postal code"
                  value={formData.postal_code}
                  onChange={(e) => handleInputChange('postal_code', e.target.value)}
                  error={errors.postal_code}
                  className="min-h-[44px]"
                  aria-describedby={errors.postal_code ? "postal-code-error" : undefined}
                  aria-invalid={!!errors.postal_code}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="country">Country *</Label>
              <Input
                id="country"
                placeholder="Enter country"
                value={formData.country}
                onChange={(e) => handleInputChange('country', e.target.value)}
                error={errors.country}
              />
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex flex-col sm:flex-row justify-end space-y-3 sm:space-y-0 sm:space-x-3 pt-6 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading}
              className="min-h-[44px] order-2 sm:order-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="flex items-center justify-center gap-2 min-h-[44px] order-1 sm:order-2"
            >
              {loading && <LoadingSpinner />}
              {isEditing ? 'Update Warehouse' : 'Create Warehouse'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function WarehouseManagement() {
  const [warehouses, setWarehouses] = useState<WarehouseType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [selectedWarehouse, setSelectedWarehouse] = useState<WarehouseType | null>(null);
  const [showWarehouseForm, setShowWarehouseForm] = useState(false);

  useEffect(() => {
    fetchWarehouses();
  }, []);

  const fetchWarehouses = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await inventoryManagementApi.getWarehouses();
      const result = handleApiResponse(response, {
        showErrorToast: false
      });

      if (result.success && result.data) {
        setWarehouses(result.data);
      } else if (result.error) {
        setError(result.error.message);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load warehouses';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWarehouse = () => {
    setSelectedWarehouse(null);
    setShowWarehouseForm(true);
  };

  const handleEditWarehouse = (warehouse: WarehouseType) => {
    setSelectedWarehouse(warehouse);
    setShowWarehouseForm(true);
  };

  const handleWarehouseSave = () => {
    fetchWarehouses();
    showSuccessToast('Warehouse saved successfully');
  };

  const checkWarehouseDependencies = async (warehouseId: string): Promise<boolean> => {
    try {
      // Check if warehouse has any inventory items
      const response = await inventoryManagementApi.getInventory({ warehouse: warehouseId, page_size: 1 });
      if (response.success && response.data && response.data.pagination.count > 0) {
        return true; // Has dependencies
      }
      return false; // No dependencies
    } catch (error) {
      console.error('Failed to check warehouse dependencies:', error);
      return true; // Assume has dependencies on error for safety
    }
  };

  const handleDeleteWarehouse = async (warehouse: WarehouseType) => {
    // Check for dependencies first
    const hasDependencies = await checkWarehouseDependencies(warehouse.id);
    
    if (hasDependencies) {
      showErrorToast(
        { type: 'validation', message: 'Cannot delete warehouse with inventory items', field_errors: {} },
        `Cannot delete warehouse "${warehouse.name}" because it has inventory items associated with it. Please move or remove all inventory items from this warehouse before deleting it.`
      );
      return;
    }

    if (!confirm(`Are you sure you want to delete warehouse "${warehouse.name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setDeleteLoading(warehouse.id);
      
      const response = await inventoryManagementApi.deleteWarehouse(warehouse.id);
      const result = handleApiResponse(response, {
        successMessage: `Warehouse "${warehouse.name}" deleted successfully`,
        showSuccessToast: true
      });

      if (result.success) {
        fetchWarehouses();
      }
    } catch (error) {
      showErrorToast(
        { type: 'unknown', message: 'Failed to delete warehouse' },
        'Failed to delete warehouse. Please try again.'
      );
    } finally {
      setDeleteLoading(null);
    }
  };

  return (
    <ErrorBoundary>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row gap-4 sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Warehouse Management</h2>
            <p className="text-sm sm:text-base text-gray-600">Manage warehouse locations and their details</p>
          </div>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
            <Button
              variant="outline"
              onClick={fetchWarehouses}
              disabled={loading}
              className="flex items-center justify-center gap-2 min-h-[44px]"
              aria-label="Refresh warehouse list"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" />
              <span className="hidden sm:inline">Refresh</span>
            </Button>
            <Button 
              onClick={handleCreateWarehouse} 
              className="flex items-center justify-center gap-2 min-h-[44px]"
              aria-label="Add new warehouse"
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">Add Warehouse</span>
              <span className="sm:hidden">Add</span>
            </Button>
          </div>
        </div>

        {/* Warehouses Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {Array.from({ length: 6 }).map((_, index) => (
              <SkeletonWarehouseCard key={index} />
            ))}
          </div>
        ) : error ? (
          <ErrorDisplay 
            error={error} 
            onRetry={fetchWarehouses}
          />
        ) : warehouses.length === 0 ? (
          <EmptyState
            icon={Warehouse}
            title="No warehouses found"
            description="Get started by creating your first warehouse"
            action={
              <Button onClick={handleCreateWarehouse} className="flex items-center gap-2">
                <Plus className="h-4 w-4" />
                Add Warehouse
              </Button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6" role="list" aria-label="Warehouses">
            {warehouses.map((warehouse) => (
              <Card 
                key={warehouse.id} 
                className="p-4 sm:p-6 hover:shadow-md transition-shadow"
                role="listitem"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3 min-w-0 flex-1">
                    <div className="p-2 bg-blue-100 rounded-lg flex-shrink-0">
                      <Warehouse className="h-5 w-5 sm:h-6 sm:w-6 text-blue-600" aria-hidden="true" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-base sm:text-lg font-semibold text-gray-900 truncate">
                        {warehouse.name}
                      </h3>
                      <p className="text-xs sm:text-sm text-gray-500">Code: {warehouse.code}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1 flex-shrink-0">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditWarehouse(warehouse)}
                      disabled={deleteLoading === warehouse.id}
                      className="min-h-[44px] min-w-[44px] p-2"
                      aria-label={`Edit ${warehouse.name}`}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteWarehouse(warehouse)}
                      className="text-red-600 hover:text-red-900 min-h-[44px] min-w-[44px] p-2"
                      disabled={deleteLoading === warehouse.id}
                      aria-label={`Delete ${warehouse.name}`}
                    >
                      {deleteLoading === warehouse.id ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

              <div className="space-y-3">
                <div className="flex items-start space-x-2">
                  <MapPin className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" aria-hidden="true" />
                  <div className="text-xs sm:text-sm text-gray-600 min-w-0">
                    <div className="break-words">{warehouse.address}</div>
                    <div>{warehouse.city}, {warehouse.state} {warehouse.postal_code}</div>
                    <div>{warehouse.country}</div>
                  </div>
                </div>

                {warehouse.phone && (
                  <div className="flex items-center space-x-2">
                    <Phone className="h-4 w-4 text-gray-400 flex-shrink-0" aria-hidden="true" />
                    <span className="text-xs sm:text-sm text-gray-600 truncate">{warehouse.phone}</span>
                  </div>
                )}

                {warehouse.email && (
                  <div className="flex items-center space-x-2">
                    <Mail className="h-4 w-4 text-gray-400 flex-shrink-0" aria-hidden="true" />
                    <span className="text-xs sm:text-sm text-gray-600 truncate">{warehouse.email}</span>
                  </div>
                )}

                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4 text-gray-400 flex-shrink-0" aria-hidden="true" />
                  <span className="text-xs sm:text-sm text-gray-600 truncate">Manager: {warehouse.manager}</span>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pt-2 border-t gap-2">
                  <span 
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      warehouse.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}
                    aria-label={`Warehouse status: ${warehouse.is_active ? 'Active' : 'Inactive'}`}
                  >
                    {warehouse.is_active ? 'Active' : 'Inactive'}
                  </span>
                  <span className="text-xs text-gray-500">
                    Created {new Date(warehouse.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Warehouse Form Modal */}
      {showWarehouseForm && (
        <WarehouseForm
          warehouse={selectedWarehouse}
          onClose={() => setShowWarehouseForm(false)}
          onSave={handleWarehouseSave}
        />
      )}
      </div>
    </ErrorBoundary>
  );
}