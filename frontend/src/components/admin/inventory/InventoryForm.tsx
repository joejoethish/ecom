'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Label } from '@/components/ui/Label';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { ErrorDisplay } from '@/components/ui/ErrorBoundary';
import { X, Search, AlertTriangle } from 'lucide-react';
import { 
  inventoryManagementApi, 
  type InventoryItem, 
  type CreateInventoryRequest, 
  type UpdateInventoryRequest,
  type Warehouse 
} from '@/services/inventoryManagementApi';
import { validateRequired, validateForm } from '@/utils/validation';
import { handleApiResponse, formatValidationErrors, debounce } from '@/utils/errorHandling';

interface InventoryFormProps {
  inventory?: InventoryItem | null;
  onClose: () => void;
  onSave: () => void;
}

interface ProductVariant {
  id: string;
  sku: string;
  product: {
    id: string;
    name: string;
  };
  attributes: Record<string, any>;
}

interface FormData {
  product_variant: string;
  warehouse: string;
  stock_quantity: string;
  reorder_level: string;
}

interface FormErrors {
  product_variant?: string;
  warehouse?: string;
  stock_quantity?: string;
  reorder_level?: string;
  general?: string;
}

export default function InventoryForm({ inventory, onClose, onSave }: InventoryFormProps) {
  const [formData, setFormData] = useState<FormData>({
    product_variant: inventory?.product_variant.id || '',
    warehouse: inventory?.warehouse.id || '',
    stock_quantity: inventory?.stock_quantity.toString() || '',
    reorder_level: inventory?.reorder_level.toString() || '',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [warehousesLoading, setWarehousesLoading] = useState(true);
  const [warehousesError, setWarehousesError] = useState<string | null>(null);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [productVariants, setProductVariants] = useState<ProductVariant[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [showProductSearch, setShowProductSearch] = useState(false);

  const isEditing = !!inventory;

  useEffect(() => {
    fetchWarehouses();
    if (inventory) {
      // If editing, set the current product variant in the search results
      setProductVariants([{
        id: inventory.product_variant.id,
        sku: inventory.product_variant.sku,
        product: inventory.product_variant.product,
        attributes: inventory.product_variant.attributes,
      }]);
    }
  }, [inventory]);

  const fetchWarehouses = async () => {
    try {
      setWarehousesLoading(true);
      setWarehousesError(null);
      
      const response = await inventoryManagementApi.getWarehouses();
      const result = handleApiResponse(response, {
        showErrorToast: false
      });

      if (result.success && result.data) {
        setWarehouses(result.data);
      } else if (result.error) {
        setWarehousesError(result.error.message);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load warehouses';
      setWarehousesError(errorMessage);
    } finally {
      setWarehousesLoading(false);
    }
  };

  const searchProductVariants = async (query: string) => {
    if (!query.trim()) {
      setProductVariants([]);
      setSearchError(null);
      return;
    }

    try {
      setSearchLoading(true);
      setSearchError(null);
      
      const response = await inventoryManagementApi.searchProductVariants(query);
      const result = handleApiResponse(response, {
        showErrorToast: false
      });

      if (result.success && result.data) {
        setProductVariants(result.data);
      } else if (result.error) {
        setSearchError(result.error.message);
        setProductVariants([]);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Search failed';
      setSearchError(errorMessage);
      setProductVariants([]);
    } finally {
      setSearchLoading(false);
    }
  };

  // Debounced search function
  const debouncedSearch = debounce((query: string) => {
    searchProductVariants(query);
  }, 300);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    debouncedSearch(query);
  };

  const handleProductVariantSelect = (variant: ProductVariant) => {
    setFormData({ ...formData, product_variant: variant.id });
    setSearchQuery(`${variant.product.name} - ${variant.sku}`);
    setShowProductSearch(false);
    // Clear product variant error if it exists
    if (errors.product_variant) {
      setErrors({ ...errors, product_variant: undefined });
    }
  };

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData({ ...formData, [field]: value });
    // Clear field error when user starts typing
    if (errors[field]) {
      setErrors({ ...errors, [field]: undefined });
    }
  };

  const validateFormData = (): FormErrors => {
    const validationRules = {
      product_variant: (value: string) => validateRequired(value, 'Product variant'),
      warehouse: (value: string) => validateRequired(value, 'Warehouse'),
      stock_quantity: (value: string) => {
        const required = validateRequired(value, 'Stock quantity');
        if (required) return required;
        
        const num = parseInt(value);
        if (isNaN(num) || num < 0) {
          return 'Stock quantity must be a non-negative number';
        }
        return null;
      },
      reorder_level: (value: string) => {
        const required = validateRequired(value, 'Reorder level');
        if (required) return required;
        
        const num = parseInt(value);
        if (isNaN(num) || num < 0) {
          return 'Reorder level must be a non-negative number';
        }
        return null;
      },
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
      
      if (isEditing && inventory) {
        const updateData: UpdateInventoryRequest = {
          stock_quantity: parseInt(formData.stock_quantity),
          reorder_level: parseInt(formData.reorder_level),
          warehouse: formData.warehouse,
        };
        
        response = await inventoryManagementApi.updateInventory(inventory.id, updateData);
      } else {
        const createData: CreateInventoryRequest = {
          product_variant: formData.product_variant,
          warehouse: formData.warehouse,
          stock_quantity: parseInt(formData.stock_quantity),
          reorder_level: parseInt(formData.reorder_level),
        };
        
        response = await inventoryManagementApi.createInventory(createData);
      }

      const result = handleApiResponse(response, {
        successMessage: `Inventory ${isEditing ? 'updated' : 'created'} successfully`,
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
            general: result.error.message || `Failed to ${isEditing ? 'update' : 'create'} inventory. Please try again.` 
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

  const selectedProductVariant = productVariants.find(v => v.id === formData.product_variant);

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="inventory-form-title"
    >
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="flex items-center justify-between p-4 sm:p-6 border-b">
          <h2 id="inventory-form-title" className="text-lg sm:text-xl font-semibold">
            {isEditing ? 'Edit Inventory' : 'Add Inventory'}
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

          {/* Product Variant Selection */}
          <div className="space-y-2">
            <Label htmlFor="product-search">Product Variant *</Label>
            <div className="relative">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4 pointer-events-none" aria-hidden="true" />
                <Input
                  id="product-search"
                  placeholder={isEditing ? "Product variant (cannot be changed)" : "Search for product variants..."}
                  value={isEditing ? `${inventory?.product_variant.product.name} - ${inventory?.product_variant.sku}` : searchQuery}
                  onChange={handleSearchChange}
                  onFocus={() => !isEditing && setShowProductSearch(true)}
                  className="pl-10 min-h-[44px]"
                  disabled={isEditing}
                  error={errors.product_variant}
                  aria-describedby={errors.product_variant ? "product-variant-error" : undefined}
                  aria-expanded={showProductSearch}
                  aria-haspopup="listbox"
                  role="combobox"
                />
              </div>
              
              {showProductSearch && !isEditing && (
                <div 
                  className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto"
                  role="listbox"
                  aria-label="Product variant options"
                >
                  {searchLoading ? (
                    <div className="p-4 text-center" role="status" aria-live="polite">
                      <LoadingSpinner />
                      <span className="sr-only">Loading product variants...</span>
                    </div>
                  ) : searchError ? (
                    <div className="p-4 text-center" role="alert">
                      <div className="flex items-center justify-center text-red-600 mb-2">
                        <AlertTriangle className="h-4 w-4 mr-2" aria-hidden="true" />
                        <span className="text-sm">{searchError}</span>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => searchProductVariants(searchQuery)}
                        className="text-xs min-h-[36px]"
                      >
                        Try Again
                      </Button>
                    </div>
                  ) : productVariants.length > 0 ? (
                    productVariants.map((variant, index) => (
                      <button
                        key={variant.id}
                        type="button"
                        className="w-full text-left p-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 focus:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset min-h-[44px]"
                        onClick={() => handleProductVariantSelect(variant)}
                        role="option"
                        aria-selected={formData.product_variant === variant.id}
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handleProductVariantSelect(variant);
                          }
                        }}
                      >
                        <div className="font-medium">{variant.product.name}</div>
                        <div className="text-sm text-gray-500">SKU: {variant.sku}</div>
                        {Object.keys(variant.attributes).length > 0 && (
                          <div className="text-xs text-blue-600 mt-1">
                            {Object.entries(variant.attributes).map(([key, value]) => (
                              <span key={key} className="mr-2">{key}: {String(value)}</span>
                            ))}
                          </div>
                        )}
                      </button>
                    ))
                  ) : searchQuery.trim() ? (
                    <div className="p-4 text-center text-gray-500" role="status">
                      No product variants found
                    </div>
                  ) : (
                    <div className="p-4 text-center text-gray-500" role="status">
                      Start typing to search for product variants
                    </div>
                  )}
                </div>
              )}
            </div>
            
            {selectedProductVariant && (
              <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-md" role="status" aria-live="polite">
                <div className="font-medium text-blue-900">{selectedProductVariant.product.name}</div>
                <div className="text-sm text-blue-700">SKU: {selectedProductVariant.sku}</div>
                {Object.keys(selectedProductVariant.attributes).length > 0 && (
                  <div className="text-xs text-blue-600 mt-1">
                    {Object.entries(selectedProductVariant.attributes).map(([key, value]) => (
                      <span key={key} className="mr-2">{key}: {String(value)}</span>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {errors.product_variant && (
              <p id="product-variant-error" className="text-sm text-red-600" role="alert">
                {errors.product_variant}
              </p>
            )}
          </div>

          {/* Warehouse Selection */}
          <div className="space-y-2">
            <Label htmlFor="warehouse">Warehouse *</Label>
            {warehousesError ? (
              <ErrorDisplay 
                error={warehousesError} 
                onRetry={fetchWarehouses}
                className="mb-2"
              />
            ) : (
              <Select
                id="warehouse"
                value={formData.warehouse}
                onChange={(value) => handleInputChange('warehouse', value)}
                disabled={warehousesLoading}
                className="min-h-[44px]"
                aria-describedby={errors.warehouse ? "warehouse-error" : undefined}
                aria-invalid={!!errors.warehouse}
              >
                <option value="">
                  {warehousesLoading ? 'Loading warehouses...' : 'Select a warehouse'}
                </option>
                {warehouses.map((warehouse) => (
                  <option key={warehouse.id} value={warehouse.id}>
                    {warehouse.name} ({warehouse.code}) - {warehouse.city}
                  </option>
                ))}
              </Select>
            )}
            {errors.warehouse && (
              <p id="warehouse-error" className="text-sm text-red-600" role="alert">
                {errors.warehouse}
              </p>
            )}
          </div>

          {/* Stock Quantity */}
          <div className="space-y-2">
            <Label htmlFor="stock-quantity">Stock Quantity *</Label>
            <Input
              id="stock-quantity"
              type="number"
              min="0"
              placeholder="Enter stock quantity"
              value={formData.stock_quantity}
              onChange={(e) => handleInputChange('stock_quantity', e.target.value)}
              error={errors.stock_quantity}
              helperText="Current available quantity in the warehouse"
              className="min-h-[44px]"
              aria-describedby={errors.stock_quantity ? "stock-quantity-error" : "stock-quantity-help"}
              aria-invalid={!!errors.stock_quantity}
            />
          </div>

          {/* Reorder Level */}
          <div className="space-y-2">
            <Label htmlFor="reorder-level">Reorder Level *</Label>
            <Input
              id="reorder-level"
              type="number"
              min="0"
              placeholder="Enter reorder level"
              value={formData.reorder_level}
              onChange={(e) => handleInputChange('reorder_level', e.target.value)}
              error={errors.reorder_level}
              helperText="Minimum stock level before reorder alert is triggered"
              className="min-h-[44px]"
              aria-describedby={errors.reorder_level ? "reorder-level-error" : "reorder-level-help"}
              aria-invalid={!!errors.reorder_level}
            />
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
              {isEditing ? 'Update Inventory' : 'Create Inventory'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}