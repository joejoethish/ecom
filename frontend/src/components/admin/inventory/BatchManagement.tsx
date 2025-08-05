'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/card';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  Package, 
  AlertTriangle, 
  Calendar,
  Clock,
  TrendingUp,
  Eye
} from 'lucide-react';
import { 
  inventoryManagementApi, 
  type ProductBatch, 
  type BatchFilters,
  type CreateBatchRequest,
  type UpdateBatchRequest
} from '@/services/inventoryManagementApi';
import BatchForm from './BatchForm';

export default function BatchManagement() {
  const [batches, setBatches] = useState<ProductBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBatch, setSelectedBatch] = useState<ProductBatch | null>(null);
  const [showBatchForm, setShowBatchForm] = useState(false);
  const [showFifoView, setShowFifoView] = useState(false);
  const [filters, setFilters] = useState<BatchFilters>({
    warehouse: '',
    product_variant: '',
    status: undefined,
    expiring_soon: false,
    page: 1,
    page_size: 20,
    ordering: '-created_at'
  });

  const [warehouses, setWarehouses] = useState<Array<{ id: string; name: string; code: string }>>([]);
  const [stats, setStats] = useState({
    total_batches: 0,
    active_batches: 0,
    expiring_soon: 0,
    expired_batches: 0
  });

  useEffect(() => {
    fetchBatches();
    fetchWarehouses();
    fetchBatchStats();
  }, [filters]);

  const fetchBatches = async () => {
    try {
      setLoading(true);
      const response = await inventoryManagementApi.getBatches(filters);
      if (response.success && response.data) {
        setBatches(response.data.results);
      }
    } catch (error) {
      console.error('Failed to fetch batches:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchWarehouses = async () => {
    try {
      const response = await inventoryManagementApi.getWarehouses();
      if (response.success && response.data) {
        setWarehouses(response.data.map((w: any) => ({ 
          id: w.id, 
          name: w.name, 
          code: w.code 
        })));
      }
    } catch (error) {
      console.error('Failed to fetch warehouses:', error);
    }
  };

  const fetchBatchStats = async () => {
    try {
      // Calculate stats from current batches
      const activeBatches = batches.filter(b => b.status === 'active').length;
      const expiredBatches = batches.filter(b => b.status === 'expired').length;
      const expiringSoon = batches.filter(b => {
        const expirationDate = new Date(b.expiration_date);
        const thirtyDaysFromNow = new Date();
        thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);
        return expirationDate <= thirtyDaysFromNow && b.status === 'active';
      }).length;

      setStats({
        total_batches: batches.length,
        active_batches: activeBatches,
        expiring_soon: expiringSoon,
        expired_batches: expiredBatches
      });
    } catch (error) {
      console.error('Failed to calculate batch stats:', error);
    }
  };

  useEffect(() => {
    fetchBatchStats();
  }, [batches]);

  const handleCreateBatch = () => {
    setSelectedBatch(null);
    setShowBatchForm(true);
  };

  const handleEditBatch = (batch: ProductBatch) => {
    setSelectedBatch(batch);
    setShowBatchForm(true);
  };

  const handleBatchSave = () => {
    fetchBatches();
    setShowBatchForm(false);
  };

  const handleDeleteBatch = async (batchId: string) => {
    if (confirm('Are you sure you want to delete this batch?')) {
      try {
        await inventoryManagementApi.deleteBatch(batchId);
        fetchBatches();
      } catch (error) {
        console.error('Failed to delete batch:', error);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'expired': return 'bg-red-100 text-red-800';
      case 'recalled': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getExpirationStatus = (expirationDate: string, status: string) => {
    if (status === 'expired') return { color: 'text-red-600', label: 'Expired' };
    
    const expDate = new Date(expirationDate);
    const now = new Date();
    const daysUntilExpiration = Math.ceil((expDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    
    if (daysUntilExpiration < 0) return { color: 'text-red-600', label: 'Expired' };
    if (daysUntilExpiration <= 7) return { color: 'text-red-500', label: `${daysUntilExpiration} days` };
    if (daysUntilExpiration <= 30) return { color: 'text-yellow-600', label: `${daysUntilExpiration} days` };
    return { color: 'text-green-600', label: `${daysUntilExpiration} days` };
  };

  const getFifoOrder = () => {
    // Group batches by product variant and sort by expiration date (FIFO)
    const groupedBatches = batches.reduce((acc, batch) => {
      const key = `${batch.product_variant.id}-${batch.warehouse.id}`;
      if (!acc[key]) {
        acc[key] = [];
      }
      acc[key].push(batch);
      return acc;
    }, {} as Record<string, ProductBatch[]>);

    // Sort each group by expiration date
    Object.keys(groupedBatches).forEach(key => {
      groupedBatches[key].sort((a, b) => 
        new Date(a.expiration_date).getTime() - new Date(b.expiration_date).getTime()
      );
    });

    return groupedBatches;
  };

  const renderFifoView = () => {
    const fifoGroups = getFifoOrder();
    
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">FIFO Allocation Order</h3>
          <Button 
            variant="outline" 
            onClick={() => setShowFifoView(false)}
          >
            Back to List
          </Button>
        </div>
        
        {Object.entries(fifoGroups).map(([key, groupBatches]) => {
          const firstBatch = groupBatches[0];
          return (
            <Card key={key} className="p-4">
              <div className="mb-4">
                <h4 className="font-medium text-gray-900">
                  {firstBatch.product_variant.product.name}
                </h4>
                <p className="text-sm text-gray-500">
                  SKU: {firstBatch.product_variant.sku} • {firstBatch.warehouse.name}
                </p>
              </div>
              
              <div className="space-y-2">
                {groupBatches.map((batch, index) => {
                  const expirationStatus = getExpirationStatus(batch.expiration_date, batch.status);
                  return (
                    <div 
                      key={batch.id}
                      className={`flex items-center justify-between p-3 rounded-lg border ${
                        index === 0 ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'
                      }`}
                    >
                      <div className="flex items-center space-x-4">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                          index === 0 ? 'bg-blue-600 text-white' : 'bg-gray-400 text-white'
                        }`}>
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-medium">Batch #{batch.batch_number}</p>
                          <p className="text-sm text-gray-500">
                            Qty: {batch.remaining_quantity}/{batch.quantity}
                          </p>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <p className={`text-sm font-medium ${expirationStatus.color}`}>
                          Expires: {expirationStatus.label}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(batch.expiration_date).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          );
        })}
      </div>
    );
  };

  if (showFifoView) {
    return renderFifoView();
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <Package className="h-5 w-5 text-blue-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Total Batches</p>
              <p className="text-2xl font-bold">{stats.total_batches}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-green-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Active Batches</p>
              <p className="text-2xl font-bold">{stats.active_batches}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <Clock className="h-5 w-5 text-yellow-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Expiring Soon</p>
              <p className="text-2xl font-bold">{stats.expiring_soon}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Expired</p>
              <p className="text-2xl font-bold">{stats.expired_batches}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters and Actions */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-col sm:flex-row gap-4 flex-1">
          <Select
            value={filters.warehouse || ''}
            onChange={(e) => 
              setFilters({ ...filters, warehouse: e.target.value })
            }
          >
            <option value="">All Warehouses</option>
            {warehouses.map((warehouse) => (
              <option key={warehouse.id} value={warehouse.id}>
                {warehouse.name} ({warehouse.code})
              </option>
            ))}
          </Select>
          <Select
            value={filters.status || ''}
            onChange={(e) => 
              setFilters({ ...filters, status: e.target.value as 'active' | 'expired' | 'recalled' | undefined })
            }
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="expired">Expired</option>
            <option value="recalled">Recalled</option>
          </Select>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={filters.expiring_soon || false}
              onChange={(e) => 
                setFilters({ ...filters, expiring_soon: e.target.checked })
              }
              className="rounded border-gray-300"
            />
            <span className="text-sm">Expiring Soon</span>
          </label>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => setShowFifoView(true)}
            className="flex items-center gap-2"
          >
            <Eye className="h-4 w-4" />
            FIFO View
          </Button>
          <Button onClick={handleCreateBatch} className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Add Batch
          </Button>
        </div>
      </div>

      {/* Batches Table */}
      <Card>
        <div className="overflow-x-auto">
          {loading ? (
            <div className="flex justify-center items-center p-8">
              <LoadingSpinner />
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Batch Details
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Product
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Warehouse
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantities
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Expiration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {batches.map((batch) => {
                  const expirationStatus = getExpirationStatus(batch.expiration_date, batch.status);
                  return (
                    <tr key={batch.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            Batch #{batch.batch_number}
                          </div>
                          <div className="text-sm text-gray-500">
                            Supplier: {batch.supplier}
                          </div>
                          <div className="text-sm text-gray-500">
                            Cost: ${batch.cost_per_unit.toFixed(2)}/unit
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {batch.product_variant.product.name}
                          </div>
                          <div className="text-sm text-gray-500">
                            SKU: {batch.product_variant.sku}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{batch.warehouse.name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          <div>Total: <span className="font-medium">{batch.quantity}</span></div>
                          <div>Remaining: <span className="font-medium text-green-600">{batch.remaining_quantity}</span></div>
                          <div>Used: <span className="font-medium text-blue-600">{batch.quantity - batch.remaining_quantity}</span></div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className={`text-sm font-medium ${expirationStatus.color}`}>
                            {expirationStatus.label}
                          </div>
                          <div className="text-sm text-gray-500">
                            {new Date(batch.expiration_date).toLocaleDateString()}
                          </div>
                          <div className="text-xs text-gray-400">
                            Mfg: {new Date(batch.manufacturing_date).toLocaleDateString()}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge className={getStatusColor(batch.status)}>
                          {batch.status}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEditBatch(batch)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteBatch(batch.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </Card>

      {/* Batch Form Modal */}
      {showBatchForm && (
        <BatchForm
          batch={selectedBatch}
          onClose={() => setShowBatchForm(false)}
          onSave={handleBatchSave}
        />
      )}
    </div>
  );
}