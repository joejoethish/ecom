/**
 * Tests for inventory management API service
 */
import { inventoryManagementApi } from '../inventoryManagementApi';
import { apiClient } from '@/utils/api';

// Mock the API client
jest.mock('@/utils/api', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
}));

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('inventoryManagementApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('API service structure', () => {
    it('should have all required inventory methods', () => {
      expect(inventoryManagementApi.getInventory).toBeDefined();
      expect(inventoryManagementApi.getInventoryById).toBeDefined();
      expect(inventoryManagementApi.createInventory).toBeDefined();
      expect(inventoryManagementApi.updateInventory).toBeDefined();
      expect(inventoryManagementApi.deleteInventory).toBeDefined();
      expect(inventoryManagementApi.adjustStock).toBeDefined();
    });

    it('should have statistics methods', () => {
      expect(inventoryManagementApi.getInventoryStats).toBeDefined();
    });

    it('should have warehouse management methods', () => {
      expect(inventoryManagementApi.getWarehouses).toBeDefined();
      expect(inventoryManagementApi.getWarehouseById).toBeDefined();
      expect(inventoryManagementApi.createWarehouse).toBeDefined();
      expect(inventoryManagementApi.updateWarehouse).toBeDefined();
      expect(inventoryManagementApi.deleteWarehouse).toBeDefined();
    });

    it('should have batch management methods', () => {
      expect(inventoryManagementApi.getBatches).toBeDefined();
      expect(inventoryManagementApi.getBatchById).toBeDefined();
      expect(inventoryManagementApi.createBatch).toBeDefined();
      expect(inventoryManagementApi.updateBatch).toBeDefined();
      expect(inventoryManagementApi.deleteBatch).toBeDefined();
    });

    it('should have transaction methods', () => {
      expect(inventoryManagementApi.getTransactions).toBeDefined();
      expect(inventoryManagementApi.getTransactionById).toBeDefined();
      expect(inventoryManagementApi.exportTransactions).toBeDefined();
    });

    it('should have alert methods', () => {
      expect(inventoryManagementApi.getAlerts).toBeDefined();
      expect(inventoryManagementApi.getAlertById).toBeDefined();
      expect(inventoryManagementApi.acknowledgeAlert).toBeDefined();
      expect(inventoryManagementApi.dismissAlert).toBeDefined();
    });

    it('should have bulk operations', () => {
      expect(inventoryManagementApi.bulkAdjustStock).toBeDefined();
    });

    it('should have search functionality', () => {
      expect(inventoryManagementApi.searchProductVariants).toBeDefined();
    });
  });

  describe('method signatures', () => {
    it('should have correct method signatures for inventory operations', () => {
      expect(typeof inventoryManagementApi.getInventory).toBe('function');
      expect(typeof inventoryManagementApi.createInventory).toBe('function');
      expect(typeof inventoryManagementApi.updateInventory).toBe('function');
      expect(typeof inventoryManagementApi.deleteInventory).toBe('function');
      expect(typeof inventoryManagementApi.adjustStock).toBe('function');
    });

    it('should have correct method signatures for warehouse operations', () => {
      expect(typeof inventoryManagementApi.getWarehouses).toBe('function');
      expect(typeof inventoryManagementApi.createWarehouse).toBe('function');
      expect(typeof inventoryManagementApi.updateWarehouse).toBe('function');
      expect(typeof inventoryManagementApi.deleteWarehouse).toBe('function');
    });
  });

  describe('inventory operations', () => {
    const mockInventoryItem = {
      id: '1',
      product_variant: {
        id: '1',
        sku: 'TEST-001',
        product: { id: '1', name: 'Test Product', images: [] },
        attributes: {},
      },
      warehouse: { id: '1', name: 'Test Warehouse', code: 'TW001', city: 'Test City' },
      stock_quantity: 100,
      reserved_quantity: 10,
      available_quantity: 90,
      reorder_level: 20,
      last_stock_update: '2024-01-01T00:00:00Z',
      stock_status: 'in_stock' as const,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    it('should fetch inventory with filters', async () => {
      const mockResponse = {
        results: [mockInventoryItem],
        count: 1,
        next: null,
        previous: null,
      };
      mockApiClient.get.mockResolvedValue({ success: true, data: mockResponse });

      const filters = { search: 'test', warehouse: '1', stock_status: 'in_stock' as const };
      const result = await inventoryManagementApi.getInventory(filters);

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/inventory/', { params: filters });
      expect(result).toEqual({ success: true, data: mockResponse });
    });

    it('should fetch inventory by ID', async () => {
      mockApiClient.get.mockResolvedValue({ success: true, data: mockInventoryItem });

      const result = await inventoryManagementApi.getInventoryById('1');

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/inventory/1/');
      expect(result).toEqual({ success: true, data: mockInventoryItem });
    });

    it('should create inventory', async () => {
      const createData = {
        product_variant: '1',
        warehouse: '1',
        stock_quantity: 100,
        reorder_level: 20,
      };
      mockApiClient.post.mockResolvedValue({ success: true, data: mockInventoryItem });

      const result = await inventoryManagementApi.createInventory(createData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/inventory/', createData);
      expect(result).toEqual({ success: true, data: mockInventoryItem });
    });

    it('should update inventory', async () => {
      const updateData = { stock_quantity: 150, reorder_level: 25 };
      mockApiClient.patch.mockResolvedValue({ success: true, data: { ...mockInventoryItem, ...updateData } });

      const result = await inventoryManagementApi.updateInventory('1', updateData);

      expect(mockApiClient.patch).toHaveBeenCalledWith('/api/inventory/1/', updateData);
      expect(result).toEqual({ success: true, data: { ...mockInventoryItem, ...updateData } });
    });

    it('should delete inventory', async () => {
      mockApiClient.delete.mockResolvedValue({ success: true, data: null });

      const result = await inventoryManagementApi.deleteInventory('1');

      expect(mockApiClient.delete).toHaveBeenCalledWith('/api/inventory/1/');
      expect(result).toEqual({ success: true, data: null });
    });

    it('should adjust stock', async () => {
      const adjustmentData = { adjustment: 10, reason: 'Inventory count correction' };
      mockApiClient.post.mockResolvedValue({ success: true, data: mockInventoryItem });

      const result = await inventoryManagementApi.adjustStock('1', adjustmentData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/inventory/1/adjust-stock/', adjustmentData);
      expect(result).toEqual({ success: true, data: mockInventoryItem });
    });

    it('should handle API errors', async () => {
      const errorResponse = { response: { data: { message: 'Not found' }, status: 404 } };
      mockApiClient.get.mockRejectedValue(errorResponse);

      const result = await inventoryManagementApi.getInventoryById('999');

      expect(result).toEqual({
        success: false,
        error: { message: 'Not found', status: 404 },
      });
    });
  });

  describe('warehouse operations', () => {
    const mockWarehouse = {
      id: '1',
      name: 'Test Warehouse',
      code: 'TW001',
      address: '123 Test St',
      city: 'Test City',
      state: 'TS',
      postal_code: '12345',
      country: 'Test Country',
      phone: '+1234567890',
      email: 'test@warehouse.com',
      manager: 'Test Manager',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    it('should fetch warehouses', async () => {
      mockApiClient.get.mockResolvedValue({ success: true, data: [mockWarehouse] });

      const result = await inventoryManagementApi.getWarehouses();

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/warehouses/');
      expect(result).toEqual({ success: true, data: [mockWarehouse] });
    });

    it('should create warehouse', async () => {
      const createData = {
        name: 'New Warehouse',
        code: 'NW001',
        address: '456 New St',
        city: 'New City',
        state: 'NC',
        postal_code: '67890',
        country: 'New Country',
        phone: '+0987654321',
        email: 'new@warehouse.com',
        manager: 'New Manager',
        is_active: true,
      };
      mockApiClient.post.mockResolvedValue({ success: true, data: { ...mockWarehouse, ...createData } });

      const result = await inventoryManagementApi.createWarehouse(createData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/warehouses/', createData);
      expect(result).toEqual({ success: true, data: { ...mockWarehouse, ...createData } });
    });

    it('should update warehouse', async () => {
      const updateData = { name: 'Updated Warehouse', manager: 'Updated Manager' };
      mockApiClient.patch.mockResolvedValue({ success: true, data: { ...mockWarehouse, ...updateData } });

      const result = await inventoryManagementApi.updateWarehouse('1', updateData);

      expect(mockApiClient.patch).toHaveBeenCalledWith('/api/warehouses/1/', updateData);
      expect(result).toEqual({ success: true, data: { ...mockWarehouse, ...updateData } });
    });

    it('should delete warehouse', async () => {
      mockApiClient.delete.mockResolvedValue({ success: true, data: null });

      const result = await inventoryManagementApi.deleteWarehouse('1');

      expect(mockApiClient.delete).toHaveBeenCalledWith('/api/warehouses/1/');
      expect(result).toEqual({ success: true, data: null });
    });
  });

  describe('batch operations', () => {
    const mockBatch = {
      id: '1',
      batch_number: 'BATCH-001',
      product_variant: {
        id: '1',
        sku: 'TEST-001',
        product: { name: 'Test Product' },
      },
      warehouse: { id: '1', name: 'Test Warehouse' },
      quantity: 100,
      remaining_quantity: 80,
      expiration_date: '2024-12-31T00:00:00Z',
      manufacturing_date: '2024-01-01T00:00:00Z',
      supplier: 'Test Supplier',
      cost_per_unit: 10.50,
      status: 'active' as const,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    it('should fetch batches with filters', async () => {
      const mockResponse = { results: [mockBatch], count: 1 };
      mockApiClient.get.mockResolvedValue({ success: true, data: mockResponse });

      const filters = { warehouse: '1', status: 'active' as const };
      const result = await inventoryManagementApi.getBatches(filters);

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/batches/', { params: filters });
      expect(result).toEqual({ success: true, data: mockResponse });
    });

    it('should create batch', async () => {
      const createData = {
        batch_number: 'BATCH-002',
        product_variant: '1',
        warehouse: '1',
        quantity: 50,
        expiration_date: '2024-06-30',
        manufacturing_date: '2024-01-15',
        supplier: 'New Supplier',
        cost_per_unit: 8.75,
      };
      mockApiClient.post.mockResolvedValue({ success: true, data: { ...mockBatch, ...createData } });

      const result = await inventoryManagementApi.createBatch(createData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/batches/', createData);
      expect(result).toEqual({ success: true, data: { ...mockBatch, ...createData } });
    });

    it('should update batch', async () => {
      const updateData = { quantity: 120, supplier: 'Updated Supplier' };
      mockApiClient.patch.mockResolvedValue({ success: true, data: { ...mockBatch, ...updateData } });

      const result = await inventoryManagementApi.updateBatch('1', updateData);

      expect(mockApiClient.patch).toHaveBeenCalledWith('/api/batches/1/', updateData);
      expect(result).toEqual({ success: true, data: { ...mockBatch, ...updateData } });
    });

    it('should delete batch', async () => {
      mockApiClient.delete.mockResolvedValue({ success: true, data: null });

      const result = await inventoryManagementApi.deleteBatch('1');

      expect(mockApiClient.delete).toHaveBeenCalledWith('/api/batches/1/');
      expect(result).toEqual({ success: true, data: null });
    });
  });

  describe('transaction operations', () => {
    const mockTransaction = {
      id: '1',
      inventory_item: {
        id: '1',
        product_variant: {
          sku: 'TEST-001',
          product: { name: 'Test Product' },
        },
        warehouse: { name: 'Test Warehouse' },
      },
      transaction_type: 'adjustment' as const,
      quantity_change: 10,
      previous_quantity: 100,
      new_quantity: 110,
      reason: 'Inventory count correction',
      user: { id: '1', username: 'testuser' },
      created_at: '2024-01-01T00:00:00Z',
    };

    it('should fetch transactions with filters', async () => {
      const mockResponse = { results: [mockTransaction], count: 1 };
      mockApiClient.get.mockResolvedValue({ success: true, data: mockResponse });

      const filters = { transaction_type: 'adjustment' as const, date_from: '2024-01-01' };
      const result = await inventoryManagementApi.getTransactions(filters);

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/inventory-transactions/', { params: filters });
      expect(result).toEqual({ success: true, data: mockResponse });
    });

    it('should export transactions', async () => {
      const mockBlob = new Blob(['csv data'], { type: 'text/csv' });
      mockApiClient.get.mockResolvedValue({ success: true, data: mockBlob });

      const result = await inventoryManagementApi.exportTransactions({ date_from: '2024-01-01' });

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/inventory-transactions/export/', {
        params: { date_from: '2024-01-01' },
        responseType: 'blob',
      });
      expect(result).toBe(mockBlob);
    });
  });

  describe('alert operations', () => {
    const mockAlert = {
      id: '1',
      inventory_item: {
        id: '1',
        product_variant: {
          sku: 'TEST-001',
          product: { name: 'Test Product' },
        },
        warehouse: { name: 'Test Warehouse' },
      },
      alert_type: 'low_stock' as const,
      priority: 'high' as const,
      message: 'Stock level is below reorder point',
      is_acknowledged: false,
      acknowledged_by: null,
      acknowledged_at: null,
      created_at: '2024-01-01T00:00:00Z',
    };

    it('should fetch alerts with filters', async () => {
      const mockResponse = {
        results: [mockAlert],
        pagination: { count: 1, current_page: 1, total_pages: 1 },
      };
      mockApiClient.get.mockResolvedValue({ success: true, data: mockResponse });

      const filters = { alert_type: 'low_stock' as const, priority: 'high' as const };
      const result = await inventoryManagementApi.getAlerts(filters);

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/stock-alerts/', { params: filters });
      expect(result).toEqual({ success: true, data: mockResponse });
    });

    it('should acknowledge alert', async () => {
      const acknowledgedAlert = { ...mockAlert, is_acknowledged: true };
      mockApiClient.post.mockResolvedValue({ success: true, data: acknowledgedAlert });

      const result = await inventoryManagementApi.acknowledgeAlert('1');

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/stock-alerts/1/acknowledge/');
      expect(result).toEqual({ success: true, data: acknowledgedAlert });
    });

    it('should dismiss alert', async () => {
      mockApiClient.delete.mockResolvedValue({ success: true, data: null });

      const result = await inventoryManagementApi.dismissAlert('1');

      expect(mockApiClient.delete).toHaveBeenCalledWith('/api/stock-alerts/1/');
      expect(result).toEqual({ success: true, data: null });
    });
  });

  describe('bulk operations', () => {
    it('should perform bulk stock adjustment', async () => {
      const adjustments = [
        { inventory_id: '1', adjustment: 10, reason: 'Count correction' },
        { inventory_id: '2', adjustment: -5, reason: 'Damaged goods' },
      ];
      const mockResponse = { success: true, updated_items: 2 };
      mockApiClient.post.mockResolvedValue({ success: true, data: mockResponse });

      const result = await inventoryManagementApi.bulkAdjustStock(adjustments);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/inventory/bulk-adjust/', {
        adjustments,
      });
      expect(result).toEqual({ success: true, data: mockResponse });
    });
  });

  describe('search operations', () => {
    it('should search product variants', async () => {
      const mockVariants = [
        {
          id: '1',
          sku: 'TEST-001',
          product: { id: '1', name: 'Test Product' },
          attributes: { color: 'red' },
        },
      ];
      mockApiClient.get.mockResolvedValue({ success: true, data: mockVariants });

      const result = await inventoryManagementApi.searchProductVariants('test');

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/product-variants/search/', {
        params: { q: 'test' },
      });
      expect(result).toEqual({ success: true, data: mockVariants });
    });
  });

  describe('statistics operations', () => {
    it('should fetch inventory statistics', async () => {
      const mockStats = {
        total_products: 150,
        total_warehouses: 3,
        low_stock_items: 12,
        out_of_stock_items: 5,
        total_stock_value: 50000,
        total_transactions_today: 25,
      };
      mockApiClient.get.mockResolvedValue({ data: mockStats });

      const result = await inventoryManagementApi.getInventoryStats();

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/inventory/stats/');
      expect(result).toEqual({ success: true, data: mockStats });
    });
  });

  describe('error handling', () => {
    it('should handle network errors', async () => {
      const networkError = new Error('Network Error');
      mockApiClient.get.mockRejectedValue(networkError);

      const result = await inventoryManagementApi.getInventory({});

      expect(result).toEqual({
        success: false,
        error: { message: 'Network Error' },
      });
    });

    it('should handle HTTP errors with response data', async () => {
      const httpError = {
        response: {
          data: { message: 'Validation failed', errors: { name: 'Required' } },
          status: 400,
        },
      };
      mockApiClient.post.mockRejectedValue(httpError);

      const result = await inventoryManagementApi.createInventory({
        product_variant: '1',
        warehouse: '1',
        stock_quantity: 100,
        reorder_level: 20,
      });

      expect(result).toEqual({
        success: false,
        error: {
          message: 'Validation failed',
          errors: { name: 'Required' },
          status: 400,
        },
      });
    });

    it('should handle HTTP errors without response data', async () => {
      const httpError = { response: { status: 500 } };
      mockApiClient.get.mockRejectedValue(httpError);

      const result = await inventoryManagementApi.getInventoryStats();

      expect(result).toEqual({
        success: false,
        error: { message: 'An error occurred', status: 500 },
      });
    });
  });
});