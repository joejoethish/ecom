/**
 * Inventory Management API service
 */
import { apiClient } from '@/utils/api';
import { ApiResponse, PaginatedResponse } from '@/types';

// Core inventory interfaces
export interface InventoryItem {
  id: string;
  product_variant: {
    id: string;
    sku: string;
    product: {
      id: string;
      name: string;
      images: Array<{
        id: string;
        image: string;
        is_primary: boolean;
      }>;
    };
    attributes: Record<string, unknown>;
  };
  warehouse: {
    id: string;
    name: string;
    code: string;
    city: string;
  };
  stock_quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  reorder_level: number;
  last_stock_update: string;
  stock_status: &apos;in_stock&apos; | &apos;low_stock&apos; | &apos;out_of_stock&apos;;
  created_at: string;
  updated_at: string;
}

export interface Warehouse {
  id: string;
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
  created_at: string;
  updated_at: string;
}

export interface ProductBatch {
  id: string;
  batch_number: string;
  product_variant: {
    id: string;
    sku: string;
    product: {
      name: string;
    };
  };
  warehouse: {
    id: string;
    name: string;
  };
  quantity: number;
  remaining_quantity: number;
  expiration_date: string;
  manufacturing_date: string;
  supplier: string;
  cost_per_unit: number;
  status: &apos;active&apos; | &apos;expired&apos; | &apos;recalled&apos;;
  created_at: string;
  updated_at: string;
}

export interface InventoryTransaction {
  id: string;
  inventory_item: {
    id: string;
    product_variant: {
      sku: string;
      product: {
        name: string;
      };
    };
    warehouse: {
      name: string;
    };
  };
  transaction_type: &apos;adjustment&apos; | &apos;sale&apos; | &apos;purchase&apos; | &apos;transfer&apos; | &apos;return&apos;;
  quantity_change: number;
  previous_quantity: number;
  new_quantity: number;
  reason: string;
  reference_id?: string;
  user: {
    id: string;
    username: string;
  };
  created_at: string;
}

export interface StockAlert {
  id: string;
  inventory_item: {
    id: string;
    product_variant: {
      sku: string;
      product: {
        name: string;
      };
    };
    warehouse: {
      name: string;
    };
  };
  alert_type: &apos;low_stock&apos; | &apos;out_of_stock&apos; | &apos;expiring_batch&apos;;
  priority: &apos;low&apos; | &apos;medium&apos; | &apos;high&apos; | &apos;critical&apos;;
  message: string;
  is_acknowledged: boolean;
  acknowledged_by?: {
    id: string;
    username: string;
  };
  acknowledged_at?: string;
  created_at: string;
}

// Statistics interfaces
export interface InventoryStats {
  total_products: number;
  total_warehouses: number;
  total_stock_value: number;
  low_stock_items: number;
  out_of_stock_items: number;
  total_transactions_today: number;
  pending_alerts: number;
  expiring_batches_count: number;
}

// Filter interfaces
export interface InventoryFilters {
  warehouse?: string;
  stock_status?: &apos;in_stock&apos; | &apos;low_stock&apos; | &apos;out_of_stock&apos;;
  product?: string;
  category?: string;
  search?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface BatchFilters {
  warehouse?: string;
  product_variant?: string;
  status?: &apos;active&apos; | &apos;expired&apos; | &apos;recalled&apos;;
  expiring_soon?: boolean;
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface TransactionFilters {
  date_from?: string;
  date_to?: string;
  product?: string;
  warehouse?: string;
  transaction_type?: &apos;adjustment&apos; | &apos;sale&apos; | &apos;purchase&apos; | &apos;transfer&apos; | &apos;return&apos;;
  user?: string;
  inventory_item?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface AlertFilters {
  alert_type?: &apos;low_stock&apos; | &apos;out_of_stock&apos; | &apos;expiring_batch&apos;;
  priority?: &apos;low&apos; | &apos;medium&apos; | &apos;high&apos; | &apos;critical&apos;;
  is_acknowledged?: boolean;
  warehouse?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}

// Request interfaces
export interface CreateInventoryRequest {
  product_variant: string;
  warehouse: string;
  stock_quantity: number;
  reorder_level: number;
}

export interface UpdateInventoryRequest {
  stock_quantity?: number;
  reorder_level?: number;
  warehouse?: string;
}

export interface CreateWarehouseRequest {
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
  is_active?: boolean;
}

export interface UpdateWarehouseRequest {
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
  is_active?: boolean;
}

export interface CreateBatchRequest {
  batch_number: string;
  product_variant: string;
  warehouse: string;
  quantity: number;
  expiration_date: string;
  manufacturing_date: string;
  supplier: string;
  cost_per_unit: number;
}

export interface UpdateBatchRequest {
  batch_number?: string;
  quantity?: number;
  expiration_date?: string;
  manufacturing_date?: string;
  supplier?: string;
  cost_per_unit?: number;
  status?: &apos;active&apos; | &apos;expired&apos; | &apos;recalled&apos;;
}

export interface StockAdjustmentRequest {
  adjustment: number;
  reason: string;
}

// API service
export const inventoryManagementApi = {
  // Inventory operations
  getInventory: async (filters?: InventoryFilters): Promise<ApiResponse<PaginatedResponse<InventoryItem>>> => {
    const params = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }
    
    const url = `/api/inventory/${params.toString() ? `?${params.toString()}` : &apos;&apos;}`;
    return apiClient.get(url);
  },

  getInventoryById: async (id: string): Promise<ApiResponse<InventoryItem>> => {
    return apiClient.get(`/api/inventory/${id}/`);
  },

  createInventory: async (data: CreateInventoryRequest): Promise<ApiResponse<InventoryItem>> => {
    return apiClient.post(&apos;/api/inventory/&apos;, data);
  },

  updateInventory: async (id: string, data: UpdateInventoryRequest): Promise<ApiResponse<InventoryItem>> => {
    return apiClient.patch(`/api/inventory/${id}/`, data);
  },

  deleteInventory: async (id: string): Promise<ApiResponse<void>> => {
    return apiClient.delete(`/api/inventory/${id}/`);
  },

  adjustStock: async (id: string, data: StockAdjustmentRequest): Promise<ApiResponse<InventoryItem>> => {
    return apiClient.post(`/api/inventory/${id}/adjust_stock/`, data);
  },

  // Statistics
  getInventoryStats: async (): Promise<ApiResponse<InventoryStats>> => {
    return apiClient.get(&apos;/api/inventory/stats/&apos;);
  },

  // Warehouses
  getWarehouses: async (): Promise<ApiResponse<Warehouse[]>> => {
    return apiClient.get(&apos;/api/warehouses/&apos;);
  },

  getWarehouseById: async (id: string): Promise<ApiResponse<Warehouse>> => {
    return apiClient.get(`/api/warehouses/${id}/`);
  },

  createWarehouse: async (data: CreateWarehouseRequest): Promise<ApiResponse<Warehouse>> => {
    return apiClient.post(&apos;/api/warehouses/&apos;, data);
  },

  updateWarehouse: async (id: string, data: UpdateWarehouseRequest): Promise<ApiResponse<Warehouse>> => {
    return apiClient.patch(`/api/warehouses/${id}/`, data);
  },

  deleteWarehouse: async (id: string): Promise<ApiResponse<void>> => {
    return apiClient.delete(`/api/warehouses/${id}/`);
  },

  // Batches
  getBatches: async (filters?: BatchFilters): Promise<ApiResponse<PaginatedResponse<ProductBatch>>> => {
    const params = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }
    
    const url = `/api/inventory/batches/${params.toString() ? `?${params.toString()}` : &apos;&apos;}`;
    return apiClient.get(url);
  },

  getBatchById: async (id: string): Promise<ApiResponse<ProductBatch>> => {
    return apiClient.get(`/api/inventory/batches/${id}/`);
  },

  createBatch: async (data: CreateBatchRequest): Promise<ApiResponse<ProductBatch>> => {
    return apiClient.post(&apos;/api/inventory/batches/&apos;, data);
  },

  updateBatch: async (id: string, data: UpdateBatchRequest): Promise<ApiResponse<ProductBatch>> => {
    return apiClient.patch(`/api/inventory/batches/${id}/`, data);
  },

  deleteBatch: async (id: string): Promise<ApiResponse<void>> => {
    return apiClient.delete(`/api/inventory/batches/${id}/`);
  },

  // Transactions
  getTransactions: async (filters?: TransactionFilters): Promise<ApiResponse<PaginatedResponse<InventoryTransaction>>> => {
    const params = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }
    
    const url = `/api/inventory/transactions/${params.toString() ? `?${params.toString()}` : &apos;&apos;}`;
    return apiClient.get(url);
  },

  getTransactionById: async (id: string): Promise<ApiResponse<InventoryTransaction>> => {
    return apiClient.get(`/api/inventory/transactions/${id}/`);
  },

  exportTransactions: async (filters?: TransactionFilters): Promise<Blob> => {
    const params = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }
    
    params.append(&apos;export&apos;, &apos;csv&apos;);
    
    const response = await apiClient.get(
      `/api/inventory/transactions/export/${params.toString() ? `?${params.toString()}` : &apos;&apos;}`,
      { responseType: &apos;blob&apos; as any }
    );
    
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || &apos;Failed to export transactions&apos;);
    }
    
    return response.data;
  },

  // Alerts
  getAlerts: async (filters?: AlertFilters): Promise<ApiResponse<PaginatedResponse<StockAlert>>> => {
    const params = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }
    
    const url = `/api/inventory/alerts/${params.toString() ? `?${params.toString()}` : &apos;&apos;}`;
    return apiClient.get(url);
  },

  getAlertById: async (id: string): Promise<ApiResponse<StockAlert>> => {
    return apiClient.get(`/api/inventory/alerts/${id}/`);
  },

  acknowledgeAlert: async (id: string): Promise<ApiResponse<StockAlert>> => {
    return apiClient.post(`/api/inventory/alerts/${id}/acknowledge/`);
  },

  dismissAlert: async (id: string): Promise<ApiResponse<void>> => {
    return apiClient.delete(`/api/inventory/alerts/${id}/`);
  },

  // Bulk operations
  bulkAdjustStock: async (adjustments: Array<{
    inventory_id: string;
    adjustment: number;
    reason: string;
  }>): Promise<ApiResponse<InventoryItem[]>> => {
    return apiClient.post(&apos;/api/inventory/bulk_adjust/&apos;, { adjustments });
  },

  // Product variant search for forms
  searchProductVariants: async (query: string): Promise<ApiResponse<Array<{
    id: string;
    sku: string;
    product: {
      id: string;
      name: string;
    };
    attributes: Record<string, unknown>;
  }>>> => {
    return apiClient.get(`/api/product-variants/search/?q=${encodeURIComponent(query)}`);
  },
};

export default inventoryManagementApi;