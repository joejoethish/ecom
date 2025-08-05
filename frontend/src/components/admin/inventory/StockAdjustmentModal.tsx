'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/Badge';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { ErrorDisplay } from '@/components/ui/ErrorBoundary';
import { X, Plus, Minus, Package, AlertTriangle } from 'lucide-react';
import { inventoryManagementApi, type InventoryItem } from '@/services/inventoryManagementApi';
import { handleApiResponse, showErrorToast, showSuccessToast } from '@/utils/errorHandling';

interface StockAdjustmentModalProps {
  inventory: InventoryItem | InventoryItem[];
  onClose: () => void;
  onSuccess: () => void;
}

interface AdjustmentItem {
  inventory: InventoryItem;
  adjustment: number;
  reason: string;
  newQuantity: number;
}

const ADJUSTMENT_REASONS = [
  'Inventory Count Correction',
  'Damaged Goods',
  'Expired Products',
  'Theft/Loss',
  'Supplier Return',
  'Quality Control',
  'System Error Correction',
  'Other'
];

export default function StockAdjustmentModal({ inventory, onClose, onSuccess }: StockAdjustmentModalProps) {
  const [adjustments, setAdjustments] = useState<AdjustmentItem[]>(() => {
    const items = Array.isArray(inventory) ? inventory : [inventory];
    return items.map(item => ({
      inventory: item,
      adjustment: 0,
      reason: '',
      newQuantity: item.stock_quantity
    }));
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [customReason, setCustomReason] = useState('');

  const isBulkAdjustment = Array.isArray(inventory);

  const updateAdjustment = (index: number, field: keyof AdjustmentItem, value: any) => {
    setAdjustments(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      
      // Recalculate new quantity when adjustment changes
      if (field === 'adjustment') {
        updated[index].newQuantity = updated[index].inventory.stock_quantity + value;
      }
      
      return updated;
    });
  };

  const handleQuickAdjustment = (index: number, amount: number) => {
    const currentAdjustment = adjustments[index].adjustment;
    const newAdjustment = currentAdjustment + amount;
    updateAdjustment(index, 'adjustment', newAdjustment);
  };

  const validateAdjustments = (): string | null => {
    for (const adjustment of adjustments) {
      if (adjustment.adjustment === 0) {
        continue; // Skip items with no adjustment
      }
      
      if (!adjustment.reason.trim()) {
        return 'Please provide a reason for all adjustments';
      }
      
      if (adjustment.newQuantity < 0) {
        return `New quantity cannot be negative for ${adjustment.inventory.product_variant.product.name}`;
      }
      
      // Check if adjustment would make available quantity negative
      const newAvailable = adjustment.inventory.available_quantity + adjustment.adjustment;
      if (newAvailable < 0) {
        return `Adjustment would result in negative available quantity for ${adjustment.inventory.product_variant.product.name}`;
      }
    }
    
    return null;
  };

  const handleSubmit = async () => {
    const validationError = validateAdjustments();
    if (validationError) {
      setError(validationError);
      return;
    }

    // Filter out items with no adjustment
    const validAdjustments = adjustments.filter(adj => adj.adjustment !== 0);
    
    if (validAdjustments.length === 0) {
      setError('Please make at least one adjustment');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (isBulkAdjustment && validAdjustments.length > 1) {
        // Use bulk adjustment API
        const bulkData = validAdjustments.map(adj => ({
          inventory_id: adj.inventory.id,
          adjustment: adj.adjustment,
          reason: adj.reason === 'Other' ? customReason : adj.reason
        }));
        
        const response = await inventoryManagementApi.bulkAdjustStock(bulkData);
        const result = handleApiResponse(response, {
          successMessage: `Successfully adjusted ${validAdjustments.length} items`,
          showSuccessToast: true
        });

        if (!result.success && result.error) {
          setError(result.error.message);
          return;
        }
      } else {
        // Use individual adjustment API for single items or single valid adjustment
        for (const adjustment of validAdjustments) {
          const response = await inventoryManagementApi.adjustStock(
            adjustment.inventory.id,
            {
              adjustment: adjustment.adjustment,
              reason: adjustment.reason === 'Other' ? customReason : adjustment.reason
            }
          );
          
          const result = handleApiResponse(response, {
            showErrorToast: false,
            showSuccessToast: false
          });

          if (!result.success && result.error) {
            setError(result.error.message);
            return;
          }
        }
        
        showSuccessToast(`Successfully adjusted ${validAdjustments.length} item${validAdjustments.length > 1 ? 's' : ''}`);
      }

      onSuccess();
      onClose();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(errorMessage);
      showErrorToast(
        { type: 'unknown', message: errorMessage },
        'Failed to adjust stock. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const getStockStatusColor = (status: string) => {
    switch (status) {
      case 'in_stock': return 'bg-green-100 text-green-800';
      case 'low_stock': return 'bg-yellow-100 text-yellow-800';
      case 'out_of_stock': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getNewStockStatus = (newQuantity: number, reorderLevel: number): string => {
    if (newQuantity === 0) return 'out_of_stock';
    if (newQuantity <= reorderLevel) return 'low_stock';
    return 'in_stock';
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="adjustment-modal-title"
    >
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 sm:p-6 border-b">
          <h2 id="adjustment-modal-title" className="text-lg sm:text-xl font-semibold">
            {isBulkAdjustment ? 'Bulk Stock Adjustment' : 'Stock Adjustment'}
          </h2>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onClose}
            className="min-h-[44px] min-w-[44px] p-2"
            aria-label="Close adjustment modal"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="p-4 sm:p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {error && (
            <div 
              className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md"
              role="alert"
              aria-live="polite"
            >
              <div className="flex items-center">
                <AlertTriangle className="h-4 w-4 text-red-600 mr-2 flex-shrink-0" aria-hidden="true" />
                <span className="text-red-700 text-sm">{error}</span>
              </div>
            </div>
          )}

          <div className="space-y-4 sm:space-y-6">
            {adjustments.map((adjustment, index) => (
              <Card key={adjustment.inventory.id} className="p-3 sm:p-4">
                <div className="space-y-4">
                  {/* Product Info */}
                  <div className="flex items-center space-x-3">
                    {adjustment.inventory.product_variant.product.images.length > 0 && (
                      <img
                        className="h-10 w-10 sm:h-12 sm:w-12 rounded-lg object-cover flex-shrink-0"
                        src={adjustment.inventory.product_variant.product.images.find((img: any) => img.is_primary)?.image || adjustment.inventory.product_variant.product.images[0]?.image}
                        alt={adjustment.inventory.product_variant.product.name}
                      />
                    )}
                    <div className="min-w-0 flex-1">
                      <h3 className="font-medium text-gray-900 text-sm sm:text-base truncate">
                        {adjustment.inventory.product_variant.product.name}
                      </h3>
                      <p className="text-xs sm:text-sm text-gray-500">
                        SKU: {adjustment.inventory.product_variant.sku}
                      </p>
                      <p className="text-xs sm:text-sm text-gray-500">
                        {adjustment.inventory.warehouse.name} ({adjustment.inventory.warehouse.code})
                      </p>
                    </div>
                  </div>

                  {/* Current Stock Info */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                    <div>
                      <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Current Stock
                      </label>
                      <p className="text-base sm:text-lg font-semibold">{adjustment.inventory.stock_quantity}</p>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Reserved
                      </label>
                      <p className="text-base sm:text-lg font-semibold">{adjustment.inventory.reserved_quantity}</p>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Available
                      </label>
                      <p className="text-base sm:text-lg font-semibold text-green-600">{adjustment.inventory.available_quantity}</p>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </label>
                      <Badge className={getStockStatusColor(adjustment.inventory.stock_status)}>
                        {adjustment.inventory.stock_status.replace('_', ' ')}
                      </Badge>
                    </div>
                  </div>

                  {/* Adjustment Controls */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Adjustment Amount
                      </label>
                      <div className="flex items-center space-x-1 sm:space-x-2">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleQuickAdjustment(index, -10)}
                          disabled={loading}
                          className="min-h-[44px] px-2 sm:px-3 text-xs sm:text-sm"
                          aria-label="Decrease by 10"
                        >
                          -10
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleQuickAdjustment(index, -1)}
                          disabled={loading}
                          className="min-h-[44px] min-w-[44px] p-2"
                          aria-label="Decrease by 1"
                        >
                          <Minus className="h-4 w-4" />
                        </Button>
                        <Input
                          type="number"
                          value={adjustment.adjustment}
                          onChange={(e) => updateAdjustment(index, 'adjustment', parseInt(e.target.value) || 0)}
                          className="w-16 sm:w-24 text-center min-h-[44px]"
                          disabled={loading}
                          aria-label="Adjustment amount"
                        />
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleQuickAdjustment(index, 1)}
                          disabled={loading}
                          className="min-h-[44px] min-w-[44px] p-2"
                          aria-label="Increase by 1"
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleQuickAdjustment(index, 10)}
                          disabled={loading}
                          className="min-h-[44px] px-2 sm:px-3 text-xs sm:text-sm"
                          aria-label="Increase by 10"
                        >
                          +10
                        </Button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Reason for Adjustment
                      </label>
                      <Select
                        value={adjustment.reason}
                        onChange={(e) => updateAdjustment(index, 'reason', e.target.value)}
                        disabled={loading}
                        className="min-h-[44px]"
                        aria-label="Select reason for adjustment"
                      >
                        <option value="">Select a reason</option>
                        {ADJUSTMENT_REASONS.map(reason => (
                          <option key={reason} value={reason}>{reason}</option>
                        ))}
                      </Select>
                    </div>
                  </div>

                  {/* New Stock Preview */}
                  {adjustment.adjustment !== 0 && (
                    <div className="p-3 bg-blue-50 rounded-md" role="status" aria-live="polite">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                        <div>
                          <p className="text-sm font-medium text-blue-900">
                            New Stock Quantity: {adjustment.newQuantity}
                          </p>
                          <p className="text-sm text-blue-700">
                            New Available: {adjustment.inventory.available_quantity + adjustment.adjustment}
                          </p>
                        </div>
                        <Badge className={getStockStatusColor(getNewStockStatus(adjustment.newQuantity, adjustment.inventory.reorder_level))}>
                          {getNewStockStatus(adjustment.newQuantity, adjustment.inventory.reorder_level).replace('_', ' ')}
                        </Badge>
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            ))}

            {/* Custom Reason Input */}
            {adjustments.some(adj => adj.reason === 'Other') && (
              <div>
                <label htmlFor="custom-reason" className="block text-sm font-medium text-gray-700 mb-2">
                  Custom Reason
                </label>
                <Input
                  id="custom-reason"
                  value={customReason}
                  onChange={(e) => setCustomReason(e.target.value)}
                  placeholder="Please specify the reason for adjustment"
                  disabled={loading}
                  className="min-h-[44px]"
                  aria-label="Enter custom reason for adjustment"
                />
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-end space-y-3 sm:space-y-0 sm:space-x-3 p-4 sm:p-6 border-t bg-gray-50">
          <Button 
            variant="outline" 
            onClick={onClose} 
            disabled={loading}
            className="min-h-[44px] order-2 sm:order-1"
          >
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit} 
            disabled={loading}
            className="min-h-[44px] order-1 sm:order-2"
          >
            {loading ? (
              <>
                <LoadingSpinner className="mr-2" />
                Processing...
              </>
            ) : (
              <>
                <Package className="h-4 w-4 mr-2" aria-hidden="true" />
                Apply Adjustments
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}