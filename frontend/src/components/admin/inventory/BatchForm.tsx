'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Label } from '@/components/ui/Label';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { X, Search, Calendar, AlertTriangle } from 'lucide-react';
import {
    inventoryManagementApi,
    type ProductBatch,
    type CreateBatchRequest,
    type UpdateBatchRequest,
    type Warehouse
} from '@/services/inventoryManagementApi';
import { validateRequired, validateForm } from '@/utils/validation';

interface BatchFormProps {
    batch?: ProductBatch | null;
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
    batch_number: string;
    product_variant: string;
    warehouse: string;
    quantity: string;
    expiration_date: string;
    manufacturing_date: string;
    supplier: string;
    cost_per_unit: string;
}

interface FormErrors {
    batch_number?: string;
    product_variant?: string;
    warehouse?: string;
    quantity?: string;
    expiration_date?: string;
    manufacturing_date?: string;
    supplier?: string;
    cost_per_unit?: string;
    general?: string;
}

export default function BatchForm({ batch, onClose, onSave }: BatchFormProps) {
    const [formData, setFormData] = useState<FormData>({
        batch_number: batch?.batch_number || '',
        product_variant: batch?.product_variant.id || '',
        warehouse: batch?.warehouse.id || '',
        quantity: batch?.quantity.toString() || '',
        expiration_date: batch?.expiration_date ? batch.expiration_date.split('T')[0] : '',
        manufacturing_date: batch?.manufacturing_date ? batch.manufacturing_date.split('T')[0] : '',
        supplier: batch?.supplier || '',
        cost_per_unit: batch?.cost_per_unit.toString() || '',
    });

    const [errors, setErrors] = useState<FormErrors>({});
    const [loading, setLoading] = useState(false);
    const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
    const [productVariants, setProductVariants] = useState<ProductVariant[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchLoading, setSearchLoading] = useState(false);
    const [showProductSearch, setShowProductSearch] = useState(false);

    const isEditing = !!batch;

    useEffect(() => {
        fetchWarehouses();
        if (batch) {
            // If editing, set the current product variant in the search results
            setProductVariants([{
                id: batch.product_variant.id,
                sku: batch.product_variant.sku,
                product: {
                    id: batch.product_variant.id, // Use variant id as fallback
                    name: batch.product_variant.product.name,
                },
                attributes: {},
            }]);
            setSearchQuery(`${batch.product_variant.product.name} - ${batch.product_variant.sku}`);
        }
    }, [batch]);

    const fetchWarehouses = async () => {
        try {
            const response = await inventoryManagementApi.getWarehouses();
            if (response.success && response.data) {
                setWarehouses(response.data);
            }
        } catch (error) {
            console.error('Failed to fetch warehouses:', error);
            setErrors({ general: 'Failed to load warehouses. Please try again.' });
        }
    };

    const searchProductVariants = async (query: string) => {
        if (!query.trim()) {
            setProductVariants([]);
            return;
        }

        try {
            setSearchLoading(true);
            const response = await inventoryManagementApi.searchProductVariants(query);
            if (response.success && response.data) {
                setProductVariants(response.data);
            }
        } catch (error) {
            console.error('Failed to search product variants:', error);
        } finally {
            setSearchLoading(false);
        }
    };

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const query = e.target.value;
        setSearchQuery(query);

        // Debounce search
        const timeoutId = setTimeout(() => {
            searchProductVariants(query);
        }, 300);

        return () => clearTimeout(timeoutId);
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
            batch_number: (value: string) => validateRequired(value, 'Batch number'),
            product_variant: (value: string) => validateRequired(value, 'Product variant'),
            warehouse: (value: string) => validateRequired(value, 'Warehouse'),
            quantity: (value: string) => {
                const required = validateRequired(value, 'Quantity');
                if (required) return required;

                const num = parseInt(value);
                if (isNaN(num) || num <= 0) {
                    return 'Quantity must be a positive number';
                }
                return null;
            },
            expiration_date: (value: string) => {
                const required = validateRequired(value, 'Expiration date');
                if (required) return required;

                const expirationDate = new Date(value);
                const manufacturingDate = new Date(formData.manufacturing_date);
                const today = new Date();

                if (expirationDate <= today) {
                    return 'Expiration date must be in the future';
                }

                if (formData.manufacturing_date && expirationDate <= manufacturingDate) {
                    return 'Expiration date must be after manufacturing date';
                }

                return null;
            },
            manufacturing_date: (value: string) => {
                const required = validateRequired(value, 'Manufacturing date');
                if (required) return required;

                const manufacturingDate = new Date(value);
                const today = new Date();

                if (manufacturingDate > today) {
                    return 'Manufacturing date cannot be in the future';
                }

                return null;
            },
            supplier: (value: string) => validateRequired(value, 'Supplier'),
            cost_per_unit: (value: string) => {
                const required = validateRequired(value, 'Cost per unit');
                if (required) return required;

                const num = parseFloat(value);
                if (isNaN(num) || num < 0) {
                    return 'Cost per unit must be a non-negative number';
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
            if (isEditing && batch) {
                const updateData: UpdateBatchRequest = {
                    batch_number: formData.batch_number,
                    quantity: parseInt(formData.quantity),
                    expiration_date: formData.expiration_date,
                    manufacturing_date: formData.manufacturing_date,
                    supplier: formData.supplier,
                    cost_per_unit: parseFloat(formData.cost_per_unit),
                };

                const response = await inventoryManagementApi.updateBatch(batch.id, updateData);
                if (!response.success) {
                    throw new Error(response.error?.message || 'Failed to update batch');
                }
            } else {
                const createData: CreateBatchRequest = {
                    batch_number: formData.batch_number,
                    product_variant: formData.product_variant,
                    warehouse: formData.warehouse,
                    quantity: parseInt(formData.quantity),
                    expiration_date: formData.expiration_date,
                    manufacturing_date: formData.manufacturing_date,
                    supplier: formData.supplier,
                    cost_per_unit: parseFloat(formData.cost_per_unit),
                };

                const response = await inventoryManagementApi.createBatch(createData);
                if (!response.success) {
                    throw new Error(response.error?.message || 'Failed to create batch');
                }
            }

            onSave();
            onClose();
        } catch (error: any) {
            console.error('Failed to save batch:', error);
            setErrors({
                general: error.message || `Failed to ${isEditing ? 'update' : 'create'} batch. Please try again.`
            });
        } finally {
            setLoading(false);
        }
    };

    const selectedProductVariant = productVariants.find(v => v.id === formData.product_variant);

    // Check if batch is expiring soon (within 30 days)
    const isExpiringSoon = formData.expiration_date &&
        new Date(formData.expiration_date) <= new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                <div className="flex items-center justify-between p-6 border-b">
                    <h2 className="text-xl font-semibold">
                        {isEditing ? 'Edit Product Batch' : 'Add Product Batch'}
                    </h2>
                    <Button variant="ghost" size="sm" onClick={onClose}>
                        <X className="h-4 w-4" />
                    </Button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    {errors.general && (
                        <div className="bg-red-50 border border-red-200 rounded-md p-4">
                            <p className="text-sm text-red-600">{errors.general}</p>
                        </div>
                    )}

                    {/* Batch Number */}
                    <div className="space-y-2">
                        <Label htmlFor="batch-number">Batch Number *</Label>
                        <Input
                            id="batch-number"
                            placeholder="Enter unique batch number"
                            value={formData.batch_number}
                            onChange={(e) => handleInputChange('batch_number', e.target.value)}
                            error={errors.batch_number}
                            helperText="Unique identifier for this batch"
                        />
                    </div>

                    {/* Product Variant Selection */}
                    <div className="space-y-2">
                        <Label htmlFor="product-search">Product Variant *</Label>
                        <div className="relative">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                                <Input
                                    id="product-search"
                                    placeholder={isEditing ? "Product variant (cannot be changed)" : "Search for product variants..."}
                                    value={searchQuery}
                                    onChange={handleSearchChange}
                                    onFocus={() => !isEditing && setShowProductSearch(true)}
                                    className="pl-10"
                                    disabled={isEditing}
                                    error={errors.product_variant}
                                />
                            </div>

                            {showProductSearch && !isEditing && (
                                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                                    {searchLoading ? (
                                        <div className="p-4 text-center">
                                            <LoadingSpinner />
                                        </div>
                                    ) : productVariants.length > 0 ? (
                                        productVariants.map((variant) => (
                                            <button
                                                key={variant.id}
                                                type="button"
                                                className="w-full text-left p-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                                                onClick={() => handleProductVariantSelect(variant)}
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
                                        <div className="p-4 text-center text-gray-500">
                                            No product variants found
                                        </div>
                                    ) : (
                                        <div className="p-4 text-center text-gray-500">
                                            Start typing to search for product variants
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {selectedProductVariant && (
                            <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
                                <div className="font-medium text-blue-900">{selectedProductVariant.product.name}</div>
                                <div className="text-sm text-blue-700">SKU: {selectedProductVariant.sku}</div>
                            </div>
                        )}
                    </div>

                    {/* Warehouse Selection */}
                    <div className="space-y-2">
                        <Label htmlFor="warehouse">Warehouse *</Label>
                        <Select
                            id="warehouse"
                            value={formData.warehouse}
                            onChange={(value) => handleInputChange('warehouse', value)}
                            disabled={isEditing}
                        >
                            <option value="">Select a warehouse</option>
                            {warehouses.map((warehouse) => (
                                <option key={warehouse.id} value={warehouse.id}>
                                    {warehouse.name} ({warehouse.code}) - {warehouse.city}
                                </option>
                            ))}
                        </Select>
                        {errors.warehouse && (
                            <p className="text-sm text-red-600">{errors.warehouse}</p>
                        )}
                        {isEditing && (
                            <p className="text-xs text-gray-500">Warehouse cannot be changed after batch creation</p>
                        )}
                    </div>

                    {/* Quantity */}
                    <div className="space-y-2">
                        <Label htmlFor="quantity">Quantity *</Label>
                        <Input
                            id="quantity"
                            type="number"
                            min="1"
                            placeholder="Enter batch quantity"
                            value={formData.quantity}
                            onChange={(e) => handleInputChange('quantity', e.target.value)}
                            error={errors.quantity}
                            helperText="Total quantity in this batch"
                        />
                    </div>

                    {/* Manufacturing Date */}
                    <div className="space-y-2">
                        <Label htmlFor="manufacturing-date">Manufacturing Date *</Label>
                        <div className="relative">
                            <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                            <Input
                                id="manufacturing-date"
                                type="date"
                                value={formData.manufacturing_date}
                                onChange={(e) => handleInputChange('manufacturing_date', e.target.value)}
                                className="pl-10"
                                error={errors.manufacturing_date}
                                max={new Date().toISOString().split('T')[0]}
                            />
                        </div>
                    </div>

                    {/* Expiration Date */}
                    <div className="space-y-2">
                        <Label htmlFor="expiration-date">Expiration Date *</Label>
                        <div className="relative">
                            <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                            <Input
                                id="expiration-date"
                                type="date"
                                value={formData.expiration_date}
                                onChange={(e) => handleInputChange('expiration_date', e.target.value)}
                                className="pl-10"
                                error={errors.expiration_date}
                                min={formData.manufacturing_date || new Date().toISOString().split('T')[0]}
                            />
                        </div>
                        {isExpiringSoon && (
                            <div className="flex items-center gap-2 p-2 bg-yellow-50 border border-yellow-200 rounded-md">
                                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                                <p className="text-sm text-yellow-700">
                                    This batch expires within 30 days
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Supplier */}
                    <div className="space-y-2">
                        <Label htmlFor="supplier">Supplier *</Label>
                        <Input
                            id="supplier"
                            placeholder="Enter supplier name"
                            value={formData.supplier}
                            onChange={(e) => handleInputChange('supplier', e.target.value)}
                            error={errors.supplier}
                            helperText="Name of the supplier for this batch"
                        />
                    </div>

                    {/* Cost per Unit */}
                    <div className="space-y-2">
                        <Label htmlFor="cost-per-unit">Cost per Unit *</Label>
                        <Input
                            id="cost-per-unit"
                            type="number"
                            min="0"
                            step="0.01"
                            placeholder="0.00"
                            value={formData.cost_per_unit}
                            onChange={(e) => handleInputChange('cost_per_unit', e.target.value)}
                            error={errors.cost_per_unit}
                            helperText="Cost per unit for this batch"
                        />
                    </div>

                    {/* Form Actions */}
                    <div className="flex justify-end space-x-3 pt-6 border-t">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={onClose}
                            disabled={loading}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            disabled={loading}
                            className="flex items-center gap-2"
                        >
                            {loading && <LoadingSpinner />}
                            {isEditing ? 'Update Batch' : 'Create Batch'}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}