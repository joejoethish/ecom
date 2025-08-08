'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { ErrorBoundary, ErrorDisplay, EmptyState } from '@/components/ui/ErrorBoundary';
import { SkeletonStats, SkeletonInventoryItem } from '@/components/ui/SkeletonLoader';
import { Plus, Search, Edit, Trash2, Package, Warehouse, AlertTriangle, BarChart3, Settings, History, RefreshCw } from 'lucide-react';
import { inventoryManagementApi, type InventoryItem, type InventoryFilters } from '@/services/inventoryManagementApi';
import { handleApiResponse, showErrorToast, showSuccessToast, debounce, withRetry } from '@/utils/errorHandling';
import { useInventoryAuth, InventoryPermission, InventoryPermissionGate, withInventoryAuth } from '@/utils/inventoryAuth';
import { useInventoryAlertNotifications, InventoryNotificationType } from '@/utils/inventoryNotifications';
import InventoryForm from './InventoryForm';
import WarehouseManagement from './WarehouseManagement';
import TransactionHistory from './TransactionHistory';
import StockAlerts from './StockAlerts';
import StockAdjustmentModal from './StockAdjustmentModal';
import AdjustmentHistory from './AdjustmentHistory';

// Types are now imported from the API service

function InventoryManagementComponent() {
  // Authentication and permissions
  const auth = useInventoryAuth();
  const notifications = useInventoryAlertNotifications();
  
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [warehousesLoading, setWarehousesLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [warehousesError, setWarehousesError] = useState<string | null>(null);
  const [selectedInventory, setSelectedInventory] = useState<InventoryItem | null>(null);
  const [showInventoryForm, setShowInventoryForm] = useState(false);
  const [showStockAdjustment, setShowStockAdjustment] = useState(false);
  const [adjustmentInventory, setAdjustmentInventory] = useState<InventoryItem | InventoryItem[] | null>(null);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [filters, setFilters] = useState<Partial<InventoryFilters>>({
    search: '',
    warehouse: '',
    stock_status: undefined,
    product: '',
    category: ''
  });

  const [stats, setStats] = useState({
    total_items: 0,
    total_warehouses: 0,
    low_stock_items: 0,
    out_of_stock_items: 0,
    total_value: 0,
    reserved_quantity: 0,
    available_quantity: 0,
    recent_transactions: 0
  });

  const [warehouses, setWarehouses] = useState<Array<{ id: string; name: string; code: string }>>([]);

  // Debounced search function
  const debouncedFetchInventory = useCallback(
    debounce(() => {
      fetchInventory();
    }, 300),
    [filters]
  );

  useEffect(() => {
    if (filters.search !== undefined) {
      debouncedFetchInventory();
    } else {
      fetchInventory();
    }
    
    // Only fetch stats and warehouses on initial load
    if (statsLoading) {
      fetchStats();
    }
    if (warehousesLoading) {
      fetchWarehouses();
    }
  }, [filters, debouncedFetchInventory, statsLoading, warehousesLoading]);

  const fetchInventory = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await withRetry(
        () => inventoryManagementApi.getInventory(filters),
        2,
        1000
      );
      
      const result = handleApiResponse(response, {
        showErrorToast: false // We'll handle errors manually
      });

      if (result.success && result.data) {
        setInventory(result.data.results);
      } else if (result.error) {
        setError(result.error.message);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load inventory';
      setError(errorMessage);
      showErrorToast({ type: 'unknown', message: errorMessage }, 'Failed to load inventory');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      setStatsLoading(true);
      setStatsError(null);
      
      const response = await withRetry(
        () => inventoryManagementApi.getInventoryStats(),
        2,
        1000
      );
      
      const result = handleApiResponse(response, {
        showErrorToast: false
      });

      if (result.success && result.data) {
        setStats({
          total_items: result.data.total_products,
          total_warehouses: result.data.total_warehouses,
          low_stock_items: result.data.low_stock_items,
          out_of_stock_items: result.data.out_of_stock_items,
          total_value: result.data.total_stock_value,
          reserved_quantity: 0, // Not available in API response
          available_quantity: 0, // Not available in API response
          recent_transactions: result.data.total_transactions_today
        });
      } else if (result.error) {
        setStatsError(result.error.message);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load statistics';
      setStatsError(errorMessage);
    } finally {
      setStatsLoading(false);
    }
  };

  const fetchWarehouses = async () => {
    try {
      setWarehousesLoading(true);
      setWarehousesError(null);
      
      const response = await withRetry(
        () => inventoryManagementApi.getWarehouses(),
        2,
        1000
      );
      
      const result = handleApiResponse(response, {
        showErrorToast: false
      });

      if (result.success && result.data) {
        setWarehouses(result.data.map((w: any) => ({ id: w.id, name: w.name, code: w.code })));
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

  const handleCreateInventory = () => {
    // Check permission before allowing creation
    if (!auth.canCreateInventory) {
      showErrorToast(
        { type: 'permission', message: 'You do not have permission to create inventory items' },
        'Access denied'
      );
      return;
    }
    
    setSelectedInventory(null);
    setShowInventoryForm(true);
  };

  const handleEditInventory = (item: InventoryItem) => {
    // Check permission before allowing edit
    if (!auth.canEditInventory) {
      showErrorToast(
        { type: 'permission', message: 'You do not have permission to edit inventory items' },
        'Access denied'
      );
      return;
    }
    
    setSelectedInventory(item);
    setShowInventoryForm(true);
  };

  const handleInventorySave = (savedItem?: InventoryItem, isNew?: boolean) => {
    fetchInventory();
    fetchStats();
    
    // Send notification for inventory changes
    if (savedItem) {
      const notificationType = isNew 
        ? InventoryNotificationType.INVENTORY_CREATED 
        : InventoryNotificationType.INVENTORY_UPDATED;
      
      notifications.sendInventoryNotification(notificationType, {
        inventory_id: savedItem.id,
        product_name: savedItem.product_variant.product.name,
        warehouse_name: savedItem.warehouse.name,
        sku: savedItem.product_variant.sku
      });
    }
    
    showSuccessToast('Inventory updated successfully');
  };

  const handleDeleteInventory = async (inventoryId: string) => {
    // Check permission before allowing deletion
    if (!auth.canDeleteInventory) {
      showErrorToast(
        { type: 'permission', message: 'You do not have permission to delete inventory items' },
        'Access denied'
      );
      return;
    }
    
    if (!confirm('Are you sure you want to delete this inventory item? This action cannot be undone.')) {
      return;
    }

    try {
      setDeleteLoading(inventoryId);
      
      // Get item details before deletion for notification
      const itemToDelete = inventory.find(item => item.id === inventoryId);
      
      const response = await inventoryManagementApi.deleteInventory(inventoryId);
      const result = handleApiResponse(response, {
        successMessage: 'Inventory item deleted successfully',
        showSuccessToast: true
      });

      if (result.success) {
        // Send notification for inventory deletion
        if (itemToDelete) {
          notifications.sendInventoryNotification(InventoryNotificationType.INVENTORY_DELETED, {
            inventory_id: inventoryId,
            product_name: itemToDelete.product_variant.product.name,
            warehouse_name: itemToDelete.warehouse.name,
            sku: itemToDelete.product_variant.sku
          });
        }
        
        fetchInventory();
        fetchStats(); // Refresh stats after deletion
      }
    } catch (error) {
      showErrorToast(
        { type: 'unknown', message: 'Failed to delete inventory item' },
        'Failed to delete inventory item. Please try again.'
      );
    } finally {
      setDeleteLoading(null);
    }
  };

  const handleStockAdjustment = (item: InventoryItem) => {
    // Check permission before allowing stock adjustment
    if (!auth.canAdjustStock) {
      showErrorToast(
        { type: 'permission', message: 'You do not have permission to adjust stock levels' },
        'Access denied'
      );
      return;
    }
    
    setAdjustmentInventory(item);
    setShowStockAdjustment(true);
  };

  const handleBulkStockAdjustment = () => {
    // Check permission before allowing bulk stock adjustment
    if (!auth.canAdjustStock) {
      showErrorToast(
        { type: 'permission', message: 'You do not have permission to adjust stock levels' },
        'Access denied'
      );
      return;
    }
    
    const selectedInventoryItems = inventory.filter(item => selectedItems.has(item.id));
    if (selectedInventoryItems.length === 0) {
      alert('Please select items to adjust');
      return;
    }
    setAdjustmentInventory(selectedInventoryItems);
    setShowStockAdjustment(true);
  };

  const handleStockAdjustmentSuccess = (adjustedItems?: InventoryItem[], adjustment?: number, reason?: string) => {
    fetchInventory();
    fetchStats();
    setSelectedItems(new Set());
    
    // Send notifications for stock adjustments
    if (adjustedItems && adjustment !== undefined) {
      adjustedItems.forEach(item => {
        notifications.notifyStockAdjustment(item, adjustment, reason || 'Manual adjustment');
      });
    }
    
    showSuccessToast('Stock adjustment completed successfully');
  };

  const handleSelectItem = (itemId: string) => {
    setSelectedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedItems.size === inventory.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(inventory.map(item => item.id)));
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

  const getStockStatusIcon = (status: string) => {
    switch (status) {
      case 'in_stock': return <Package className="h-4 w-4" />;
      case 'low_stock': return <AlertTriangle className="h-4 w-4" />;
      case 'out_of_stock': return <AlertTriangle className="h-4 w-4" />;
      default: return <Package className="h-4 w-4" />;
    }
  };

  return (
    <ErrorBoundary>
      <div className="space-y-6">
        <Tabs defaultValue="inventory">
        <TabsList className="grid w-full grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-1 p-1">
          <TabsTrigger 
            value="inventory" 
            className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm px-2 sm:px-3 py-2 min-h-[44px]"
            aria-label="Inventory management"
          >
            <Package className="h-3 w-3 sm:h-4 sm:w-4" />
            <span className="hidden xs:inline">Inventory</span>
            <span className="xs:hidden">Inv</span>
          </TabsTrigger>
          <InventoryPermissionGate permissions={[InventoryPermission.MANAGE_WAREHOUSES]}>
            <TabsTrigger 
              value="warehouses" 
              className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm px-2 sm:px-3 py-2 min-h-[44px]"
              aria-label="Warehouse management"
            >
              <Warehouse className="h-3 w-3 sm:h-4 sm:w-4" />
              <span className="hidden xs:inline">Warehouses</span>
              <span className="xs:hidden">WH</span>
            </TabsTrigger>
          </InventoryPermissionGate>
          <InventoryPermissionGate permissions={[InventoryPermission.MANAGE_BATCHES]}>
            <TabsTrigger 
              value="batches" 
              className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm px-2 sm:px-3 py-2 min-h-[44px]"
              aria-label="Batch management"
            >
              <Package className="h-3 w-3 sm:h-4 sm:w-4" />
              <span className="hidden xs:inline">Batches</span>
              <span className="xs:hidden">Batch</span>
            </TabsTrigger>
          </InventoryPermissionGate>
          <InventoryPermissionGate permissions={[InventoryPermission.VIEW_TRANSACTIONS]}>
            <TabsTrigger 
              value="transactions" 
              className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm px-2 sm:px-3 py-2 min-h-[44px]"
              aria-label="Transaction history"
            >
              <BarChart3 className="h-3 w-3 sm:h-4 sm:w-4" />
              <span className="hidden xs:inline">Transactions</span>
              <span className="xs:hidden">Trans</span>
            </TabsTrigger>
          </InventoryPermissionGate>
          <InventoryPermissionGate permissions={[InventoryPermission.ADJUST_STOCK]}>
            <TabsTrigger 
              value="adjustments" 
              className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm px-2 sm:px-3 py-2 min-h-[44px]"
              aria-label="Stock adjustments"
            >
              <History className="h-3 w-3 sm:h-4 sm:w-4" />
              <span className="hidden xs:inline">Adjustments</span>
              <span className="xs:hidden">Adj</span>
            </TabsTrigger>
          </InventoryPermissionGate>
          <InventoryPermissionGate permissions={[InventoryPermission.VIEW_ALERTS]}>
            <TabsTrigger 
              value="alerts" 
              className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm px-2 sm:px-3 py-2 min-h-[44px]"
              aria-label="Stock alerts"
            >
              <AlertTriangle className="h-3 w-3 sm:h-4 sm:w-4" />
              <span className="hidden xs:inline">Alerts</span>
              <span className="xs:hidden">Alert</span>
            </TabsTrigger>
          </InventoryPermissionGate>
        </TabsList>

        <TabsContent value="inventory" className="space-y-6">
          {/* Stats Cards */}
          {statsLoading ? (
            <SkeletonStats count={4} />
          ) : statsError ? (
            <ErrorDisplay 
              error={statsError} 
              onRetry={fetchStats}
              className="mb-6"
            />
          ) : (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
              <Card className="p-3 sm:p-4" role="region" aria-label="Total inventory items">
                <div className="flex items-center space-x-2">
                  <Package className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 flex-shrink-0" aria-hidden="true" />
                  <div className="min-w-0">
                    <p className="text-xs sm:text-sm font-medium text-gray-600 truncate">Total Items</p>
                    <p className="text-lg sm:text-2xl font-bold" aria-label={`${stats.total_items} total items`}>
                      {stats.total_items}
                    </p>
                  </div>
                </div>
              </Card>
              <Card className="p-3 sm:p-4" role="region" aria-label="Total warehouses">
                <div className="flex items-center space-x-2">
                  <Warehouse className="h-4 w-4 sm:h-5 sm:w-5 text-purple-600 flex-shrink-0" aria-hidden="true" />
                  <div className="min-w-0">
                    <p className="text-xs sm:text-sm font-medium text-gray-600 truncate">Warehouses</p>
                    <p className="text-lg sm:text-2xl font-bold" aria-label={`${stats.total_warehouses} warehouses`}>
                      {stats.total_warehouses}
                    </p>
                  </div>
                </div>
              </Card>
              <Card className="p-3 sm:p-4" role="region" aria-label="Low stock items">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 sm:h-5 sm:w-5 text-yellow-600 flex-shrink-0" aria-hidden="true" />
                  <div className="min-w-0">
                    <p className="text-xs sm:text-sm font-medium text-gray-600 truncate">Low Stock</p>
                    <p className="text-lg sm:text-2xl font-bold" aria-label={`${stats.low_stock_items} low stock items`}>
                      {stats.low_stock_items}
                    </p>
                  </div>
                </div>
              </Card>
              <Card className="p-3 sm:p-4" role="region" aria-label="Out of stock items">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 sm:h-5 sm:w-5 text-red-600 flex-shrink-0" aria-hidden="true" />
                  <div className="min-w-0">
                    <p className="text-xs sm:text-sm font-medium text-gray-600 truncate">Out of Stock</p>
                    <p className="text-lg sm:text-2xl font-bold" aria-label={`${stats.out_of_stock_items} out of stock items`}>
                      {stats.out_of_stock_items}
                    </p>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Filters and Actions */}
          <div className="space-y-4">
            {/* Search and Filters */}
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="relative flex-1 min-w-0">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4 pointer-events-none" aria-hidden="true" />
                <Input
                  placeholder="Search inventory..."
                  value={filters.search || ''}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                  className="pl-10 w-full min-h-[44px]"
                  aria-label="Search inventory items"
                />
              </div>
              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                <Select
                  value={filters.warehouse || ''}
                  onChange={(value) => 
                    setFilters({ ...filters, warehouse: value })
                  }
                  disabled={warehousesLoading || !!warehousesError}
                  className="min-w-0 sm:min-w-[160px] min-h-[44px]"
                  aria-label="Filter by warehouse"
                >
                  <option value="">
                    {warehousesLoading ? 'Loading warehouses...' : 
                     warehousesError ? 'Error loading warehouses' : 
                     'All Warehouses'}
                  </option>
                  {warehouses.map((warehouse) => (
                    <option key={warehouse.id} value={warehouse.id}>
                      {warehouse.name} ({warehouse.code})
                    </option>
                  ))}
                </Select>
                <Select
                  value={filters.stock_status || ''}
                  onChange={(value) => 
                    setFilters({ ...filters, stock_status: value as 'in_stock' | 'low_stock' | 'out_of_stock' | undefined })
                  }
                  className="min-w-0 sm:min-w-[140px] min-h-[44px]"
                  aria-label="Filter by stock status"
                >
                  <option value="">All Stock Status</option>
                  <option value="in_stock">In Stock</option>
                  <option value="low_stock">Low Stock</option>
                  <option value="out_of_stock">Out of Stock</option>
                </Select>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    fetchInventory();
                    fetchStats();
                  }}
                  disabled={loading}
                  className="flex items-center gap-2 min-h-[44px] px-4"
                  aria-label="Refresh inventory data"
                >
                  <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" />
                  <span className="hidden sm:inline">Refresh</span>
                </Button>
                {selectedItems.size > 0 && (
                  <Button
                    variant="outline"
                    onClick={handleBulkStockAdjustment}
                    className="flex items-center gap-2 min-h-[44px] px-4"
                    aria-label={`Adjust stock for ${selectedItems.size} selected items`}
                  >
                    <Settings className="h-4 w-4" aria-hidden="true" />
                    <span className="hidden sm:inline">Adjust Selected ({selectedItems.size})</span>
                    <span className="sm:hidden">Adjust ({selectedItems.size})</span>
                  </Button>
                )}
              </div>
              <InventoryPermissionGate permissions={[InventoryPermission.CREATE_INVENTORY]}>
                <Button 
                  onClick={handleCreateInventory} 
                  className="flex items-center gap-2 min-h-[44px] px-4 justify-center sm:justify-start"
                  aria-label="Add new inventory item"
                >
                  <Plus className="h-4 w-4" aria-hidden="true" />
                  <span className="hidden sm:inline">Add Inventory</span>
                  <span className="sm:hidden">Add</span>
                </Button>
              </InventoryPermissionGate>
            </div>
          </div>

          {/* Inventory Table */}
          <Card>
            {/* Mobile Card View */}
            <div className="block lg:hidden">
              {loading ? (
                <div className="space-y-4 p-4">
                  {Array.from({ length: 5 }).map((_, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4 animate-pulse">
                      <div className="flex items-center space-x-3 mb-3">
                        <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
                        <div className="flex-1 space-y-2">
                          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="h-3 bg-gray-200 rounded"></div>
                        <div className="h-3 bg-gray-200 rounded"></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : error ? (
                <ErrorDisplay 
                  error={error} 
                  onRetry={fetchInventory}
                  className="m-6"
                />
              ) : inventory.length === 0 ? (
                <EmptyState
                  icon={Package}
                  title="No inventory items found"
                  description="Get started by adding your first inventory item or adjust your filters."
                  action={
                    <Button onClick={handleCreateInventory} className="flex items-center gap-2">
                      <Plus className="h-4 w-4" />
                      Add Inventory
                    </Button>
                  }
                  className="py-12"
                />
              ) : (
                <div className="space-y-3 p-4" role="list" aria-label="Inventory items">
                  {inventory.map((item) => (
                    <div 
                      key={item.id} 
                      className="bg-white border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                      role="listitem"
                    >
                      <div className="flex items-start space-x-3 mb-3">
                        <input
                          type="checkbox"
                          checked={selectedItems.has(item.id)}
                          onChange={() => handleSelectItem(item.id)}
                          className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500 min-h-[20px] min-w-[20px]"
                          aria-label={`Select ${item.product_variant.product.name}`}
                        />
                        {item.product_variant.product.images.length > 0 && (
                          <div className="flex-shrink-0">
                            <img
                              className="h-12 w-12 rounded-lg object-cover"
                              src={item.product_variant.product.images.find((img: any) => img.is_primary)?.image || item.product_variant.product.images[0]?.image}
                              alt={item.product_variant.product.name}
                              onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.style.display = 'none';
                              }}
                            />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-gray-900 truncate">
                            {item.product_variant.product.name}
                          </h3>
                          <p className="text-xs text-gray-500">SKU: {item.product_variant.sku}</p>
                          <p className="text-xs text-blue-600">
                            {item.warehouse.name} • {item.warehouse.city}
                          </p>
                        </div>
                        <Badge className={getStockStatusColor(item.stock_status)}>
                          <div className="flex items-center space-x-1">
                            {getStockStatusIcon(item.stock_status)}
                            <span className="text-xs">{item.stock_status.replace('_', ' ')}</span>
                          </div>
                        </Badge>
                      </div>

                      <div className="grid grid-cols-2 gap-4 mb-3 text-xs">
                        <div>
                          <span className="text-gray-500">Stock:</span>
                          <span className="font-medium ml-1">{item.stock_quantity}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Available:</span>
                          <span className="font-medium text-green-600 ml-1">{item.available_quantity}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Reserved:</span>
                          <span className="font-medium ml-1">{item.reserved_quantity}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Reorder:</span>
                          <span className="font-medium ml-1">{item.reorder_level}</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                        <span className="text-xs text-gray-500">
                          Updated {new Date(item.last_stock_update).toLocaleDateString()}
                        </span>
                        <div className="flex items-center space-x-1">
                          <InventoryPermissionGate permissions={[InventoryPermission.ADJUST_STOCK]}>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleStockAdjustment(item)}
                              disabled={deleteLoading === item.id}
                              className="min-h-[44px] min-w-[44px] p-2"
                              aria-label={`Adjust stock for ${item.product_variant.product.name}`}
                            >
                              <Settings className="h-4 w-4" />
                            </Button>
                          </InventoryPermissionGate>
                          <InventoryPermissionGate permissions={[InventoryPermission.EDIT_INVENTORY]}>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEditInventory(item)}
                              disabled={deleteLoading === item.id}
                              className="min-h-[44px] min-w-[44px] p-2"
                              aria-label={`Edit ${item.product_variant.product.name}`}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          </InventoryPermissionGate>
                          <InventoryPermissionGate permissions={[InventoryPermission.DELETE_INVENTORY]}>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteInventory(item.id)}
                              className="text-red-600 hover:text-red-900 min-h-[44px] min-w-[44px] p-2"
                              disabled={deleteLoading === item.id}
                              aria-label={`Delete ${item.product_variant.product.name}`}
                            >
                              {deleteLoading === item.id ? (
                                <LoadingSpinner size="sm" />
                              ) : (
                                <Trash2 className="h-4 w-4" />
                              )}
                            </Button>
                          </InventoryPermissionGate>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Desktop Table View */}
            <div className="hidden lg:block overflow-x-auto">
              {loading ? (
                <table className="w-full" role="table" aria-label="Inventory items table">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <div className="w-4 h-4 bg-gray-200 rounded animate-pulse"></div>
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Product
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Warehouse
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Stock Levels
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Reorder Level
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Last Updated
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {Array.from({ length: 5 }).map((_, index) => (
                      <SkeletonInventoryItem key={index} />
                    ))}
                  </tbody>
                </table>
              ) : error ? (
                <ErrorDisplay 
                  error={error} 
                  onRetry={fetchInventory}
                  className="m-6"
                />
              ) : inventory.length === 0 ? (
                <EmptyState
                  icon={Package}
                  title="No inventory items found"
                  description="Get started by adding your first inventory item or adjust your filters."
                  action={
                    <Button onClick={handleCreateInventory} className="flex items-center gap-2">
                      <Plus className="h-4 w-4" />
                      Add Inventory
                    </Button>
                  }
                  className="py-12"
                />
              ) : (
                <table className="w-full" role="table" aria-label="Inventory items table">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <input
                          type="checkbox"
                          checked={selectedItems.size === inventory.length && inventory.length > 0}
                          onChange={handleSelectAll}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 min-h-[20px] min-w-[20px]"
                          aria-label="Select all inventory items"
                        />
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Product
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Warehouse
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Stock Levels
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Reorder Level
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Last Updated
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {inventory.map((item) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="checkbox"
                            checked={selectedItems.has(item.id)}
                            onChange={() => handleSelectItem(item.id)}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 min-h-[20px] min-w-[20px]"
                            aria-label={`Select ${item.product_variant.product.name}`}
                          />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            {item.product_variant.product.images.length > 0 && (
                              <div className="flex-shrink-0 h-10 w-10">
                                <img
                                  className="h-10 w-10 rounded-lg object-cover"
                                  src={item.product_variant.product.images.find((img: any) => img.is_primary)?.image || item.product_variant.product.images[0]?.image}
                                  alt={item.product_variant.product.name}
                                  onError={(e) => {
                                    const target = e.target as HTMLImageElement;
                                    target.style.display = 'none';
                                  }}
                                />
                              </div>
                            )}
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {item.product_variant.product.name}
                              </div>
                              <div className="text-sm text-gray-500">SKU: {item.product_variant.sku}</div>
                              {Object.keys(item.product_variant.attributes).length > 0 && (
                                <div className="text-xs text-blue-600">
                                  {Object.entries(item.product_variant.attributes).map(([key, value]) => (
                                    <span key={key} className="mr-2">{key}: {String(value)}</span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{item.warehouse.name}</div>
                          <div className="text-sm text-gray-500">{item.warehouse.code} • {item.warehouse.city}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            <div>Stock: <span className="font-medium">{item.stock_quantity}</span></div>
                            <div>Reserved: <span className="font-medium">{item.reserved_quantity}</span></div>
                            <div>Available: <span className="font-medium text-green-600">{item.available_quantity}</span></div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge className={getStockStatusColor(item.stock_status)}>
                            <div className="flex items-center space-x-1">
                              {getStockStatusIcon(item.stock_status)}
                              <span>{item.stock_status.replace('_', ' ')}</span>
                            </div>
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {item.reorder_level}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(item.last_stock_update).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center justify-end space-x-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleStockAdjustment(item)}
                              disabled={deleteLoading === item.id}
                              className="min-h-[44px] min-w-[44px]"
                              aria-label={`Adjust stock for ${item.product_variant.product.name}`}
                            >
                              <Settings className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEditInventory(item)}
                              disabled={deleteLoading === item.id}
                              className="min-h-[44px] min-w-[44px]"
                              aria-label={`Edit ${item.product_variant.product.name}`}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteInventory(item.id)}
                              className="text-red-600 hover:text-red-900 min-h-[44px] min-w-[44px]"
                              disabled={deleteLoading === item.id}
                              aria-label={`Delete ${item.product_variant.product.name}`}
                            >
                              {deleteLoading === item.id ? (
                                <LoadingSpinner size="sm" />
                              ) : (
                                <Trash2 className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </Card>
        </TabsContent>

        <InventoryPermissionGate permissions={[InventoryPermission.MANAGE_WAREHOUSES]}>
          <TabsContent value="warehouses">
            <WarehouseManagement />
          </TabsContent>
        </InventoryPermissionGate>

        <InventoryPermissionGate permissions={[InventoryPermission.MANAGE_BATCHES]}>
          <TabsContent value="batches">
            <div className="p-8 text-center text-gray-500">
              <Package className="h-12 w-12 mx-auto mb-4" />
              <p>Batch management component will be implemented in a future task.</p>
            </div>
          </TabsContent>
        </InventoryPermissionGate>

        <InventoryPermissionGate permissions={[InventoryPermission.VIEW_TRANSACTIONS]}>
          <TabsContent value="transactions">
            <TransactionHistory />
          </TabsContent>
        </InventoryPermissionGate>

        <InventoryPermissionGate permissions={[InventoryPermission.ADJUST_STOCK]}>
          <TabsContent value="adjustments">
            <AdjustmentHistory />
          </TabsContent>
        </InventoryPermissionGate>

        <InventoryPermissionGate permissions={[InventoryPermission.VIEW_ALERTS]}>
          <TabsContent value="alerts">
            <StockAlerts />
          </TabsContent>
        </InventoryPermissionGate>
      </Tabs>

      {/* Inventory Form Modal */}
      {showInventoryForm && (
        <InventoryForm
          inventory={selectedInventory}
          onClose={() => setShowInventoryForm(false)}
          onSave={handleInventorySave}
        />
      )}

      {/* Stock Adjustment Modal */}
      {showStockAdjustment && adjustmentInventory && (
        <StockAdjustmentModal
          inventory={adjustmentInventory}
          onClose={() => {
            setShowStockAdjustment(false);
            setAdjustmentInventory(null);
          }}
          onSuccess={handleStockAdjustmentSuccess}
        />
      )}
      </div>
    </ErrorBoundary>
  );
}

// Export the component wrapped with authentication
export default withInventoryAuth(InventoryManagementComponent, [InventoryPermission.VIEW_INVENTORY]);