/**
 * Admin API service for analytics and dashboard data
 */
import { apiClient } from '@/utils/api';

const ANALYTICS_BASE_URL = '/api/analytics';
const CONTENT_BASE_URL = '/api/content';

// Types for analytics data
export interface DashboardMetrics {
  sales: {
    total_orders: number;
    total_revenue: number;
    average_order_value: number;
    revenue_growth: number;
  };
  customers: {
    new_customers: number;
    total_customers: number;
    returning_customers: number;
  };
  inventory: {
    total_products: number;
    low_stock_products: number;
    out_of_stock_products: number;
    total_inventory_value: number;
  };
  orders_by_status: Record<string, number>;
  period: {
    from: string;
    to: string;
  };
}

export interface SalesReport {
  summary: {
    total_orders: number;
    total_revenue: number;
    total_discount: number;
    total_tax: number;
    total_shipping: number;
    average_order_value: number;
  };
  daily_breakdown: Array<{
    day: string;
    orders: number;
    revenue: number;
  }>;
  top_products: Array<{
    product__name: string;
    product__id: number;
    quantity_sold: number;
    revenue: number;
  }>;
  payment_methods: Array<{
    payment_method: string;
    count: number;
    revenue: number;
  }>;
  filters_applied: Record<string, unknown>;
  period: {
    from: string;
    to: string;
  };
}

export interface TopSellingProduct {
  product__id: number;
  product__name: string;
  product__sku: string;
  product__price: number;
  product__category__name: string;
  total_quantity: number;
  total_revenue: number;
  order_count: number;
}

export interface CustomerAnalyticsSummary {
  lifecycle_distribution: Array<{
    lifecycle_stage: string;
    count: number;
  }>;
  top_customers: Array<{
    customer_id: number;
    email: string;
    lifetime_value: number;
    total_orders: number;
    lifecycle_stage: string;
  }>;
  segments: Array<{
    customer_segment: string;
    count: number;
    avg_lifetime_value: number;
  }>;
}

export interface StockMaintenanceReport {
  low_stock: Array<{
    product_id: number;
    product_name: string;
    sku: string;
    current_quantity: number;
    minimum_level: number;
    reorder_point: number;
  }>;
  out_of_stock: Array<{
    product_id: number;
    product_name: string;
    sku: string;
    last_restocked: string | null;
  }>;
  overstock: Array<{
    product_id: number;
    product_name: string;
    sku: string;
    current_quantity: number;
    maximum_level: number;
    excess_quantity: number;
  }>;
  dead_stock: Array<{
    product_id: number;
    product_name: string;
    sku: string;
    current_quantity: number;
    inventory_value: number;
  }>;
  summary: {
    low_stock_count: number;
    out_of_stock_count: number;
    overstock_count: number;
    dead_stock_count: number;
  };
}

export interface SystemHealthSummary {
  period_summary: {
    avg_response_time: number;
    max_response_time: number;
    avg_error_rate: number;
    max_error_rate: number;
    avg_active_users: number;
    max_active_users: number;
  };
  current_metrics: {
    response_time: number;
    error_rate: number;
    active_users: number;
    memory_usage: number;
    cpu_usage: number;
  };
  health_status: &apos;healthy&apos; | &apos;warning&apos; | &apos;critical&apos;;
}

export interface ContentAnalytics {
  banners: {
    total_banners: number;
    active_banners: number;
    total_views: number;
    total_clicks: number;
    avg_ctr: number;
  };
  carousels: {
    total_carousels: number;
    active_carousels: number;
    total_views: number;
    total_clicks: number;
    avg_ctr: number;
  };
  total_content_views: number;
  total_content_clicks: number;
}

export interface ReportExport {
  id: number;
  report_type: string;
  export_format: string;
  file_path: string;
  file_size: number;
  file_size_human: string;
  date_from: string | null;
  date_to: string | null;
  filters: Record<string, unknown>;
  exported_by: number;
  exported_by_email: string;
  export_status: &apos;pending&apos; | &apos;processing&apos; | &apos;completed&apos; | &apos;failed&apos;;
  download_count: number;
  expires_at: string | null;
  is_expired: boolean;
  created_at: string;
  updated_at: string;
}

  // Dashboard metrics
  async getDashboardMetrics(dateFrom?: string, dateTo?: string): Promise<DashboardMetrics> {
    const params = new URLSearchParams();
    if (dateFrom) params.append(&apos;date_from&apos;, dateFrom);
    if (dateTo) params.append(&apos;date_to&apos;, dateTo);
    
    const response = await apiClient.get<DashboardMetrics>(
      `${ANALYTICS_BASE_URL}/dashboard_metrics/?${params.toString()}`
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || &apos;Failed to fetch dashboard metrics&apos;);
    }
    return response.data;
  },

  // Sales analytics
  async getSalesReport(filters?: {
    date_from?: string;
    date_to?: string;
    category?: number;
    product?: number;
    order_status?: string;
    payment_method?: string;
  }): Promise<SalesReport> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }
    
    const response = await apiClient.get<SalesReport>(
      `${ANALYTICS_BASE_URL}/sales_report/?${params.toString()}`
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || &apos;Failed to fetch sales report&apos;);
    }
    return response.data;
  },

  async getTopSellingProducts(
    dateFrom?: string,
    dateTo?: string,
    limit: number = 10
  ): Promise<TopSellingProduct[]> {
    const params = new URLSearchParams();
    if (dateFrom) params.append(&apos;date_from&apos;, dateFrom);
    if (dateTo) params.append(&apos;date_to&apos;, dateTo);
    params.append(&apos;limit&apos;, limit.toString());
    
    const response = await apiClient.get<TopSellingProduct[]>(
      `${ANALYTICS_BASE_URL}/top_selling_products/?${params.toString()}`
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || &apos;Failed to fetch top selling products&apos;);
    }
    return response.data;
  },

  // Customer analytics
  async getCustomerAnalyticsSummary(): Promise<CustomerAnalyticsSummary> {
    const response = await apiClient.get<CustomerAnalyticsSummary>(
      `${ANALYTICS_BASE_URL}/customer_analytics_summary/`
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || &apos;Failed to fetch customer analytics summary&apos;);
    }
    return response.data;
  },

  // Inventory analytics
  async getStockMaintenanceReport(): Promise<StockMaintenanceReport> {
    const response = await apiClient.get<StockMaintenanceReport>(
      `${ANALYTICS_BASE_URL}/stock_maintenance_report/`
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || &apos;Failed to fetch stock maintenance report&apos;);
    }
    return response.data;
  },

  // System health
  async getSystemHealth(hours: number = 24): Promise<SystemHealthSummary> {
    const response = await apiClient.get<SystemHealthSummary>(
      `${ANALYTICS_BASE_URL}/system_health/?hours=${hours}`
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || &apos;Failed to fetch system health&apos;);
    }
    return response.data;
  },

  // Content analytics
  async getContentAnalytics(dateFrom?: string, dateTo?: string): Promise<ContentAnalytics> {
    const params = new URLSearchParams();
    if (dateFrom) params.append(&apos;date_from&apos;, dateFrom);
    if (dateTo) params.append(&apos;date_to&apos;, dateTo);
    
    const response = await apiClient.get<ContentAnalytics>(
      `${CONTENT_BASE_URL}/content_management/performance_summary/?${params.toString()}`
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || &apos;Failed to fetch content analytics&apos;);
    }
    return response.data;
  },

  // Report exports
  async exportReport(data: {
    report_type: &apos;sales&apos; | &apos;inventory&apos; | &apos;customer&apos; | &apos;product&apos; | &apos;profit_loss&apos;;
    export_format: &apos;pdf&apos; | &apos;excel&apos; | &apos;csv&apos;;
    date_from?: string;
    date_to?: string;
    filters?: Record<string, unknown>;
  }): Promise<ReportExport> {
    const response = await apiClient.post<ReportExport>(
      `${ANALYTICS_BASE_URL}/export_report/`,
      data
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || &apos;Failed to export report&apos;);
    }
    return response.data;
  },

  async getExportHistory(): Promise<ReportExport[]> {
    const response = await apiClient.get<ReportExport[]>(
      `${ANALYTICS_BASE_URL}/export_history/`
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || &apos;Failed to fetch export history&apos;);
    }
    return response.data;
  },

  async downloadExport(exportId: number): Promise<void> {
    const response = await apiClient.get<Blob>(
      `${ANALYTICS_BASE_URL}/download_export/?export_id=${exportId}`,
      { responseType: &apos;blob&apos; as any }
    );
    
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || &apos;Failed to download export&apos;);
    }
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement(&apos;a&apos;);
    link.href = url;
    link.setAttribute(&apos;download&apos;, `report_${exportId}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  // Daily reports generation
  async generateDailyReports(date?: string): Promise<{
    message: string;
    sales_report_id: number;
    inventory_report_id: number;
  }> {
    const response = await apiClient.post<{
      message: string;
      sales_report_id: number;
      inventory_report_id: number;
    }>(
      `${ANALYTICS_BASE_URL}/generate_daily_reports/`,
      date ? { date } : {}
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to generate daily reports');
    }
    return response.data;
  },
};