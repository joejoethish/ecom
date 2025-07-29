'use client';

import { useState, useEffect, useCallback } from 'react';
import { 
  TrendingUp, 
  Users, 
  ShoppingCart, 
  Package,
  Download
} from 'lucide-react';
import { adminApi, SalesReport, CustomerAnalyticsSummary, StockMaintenanceReport } from '@/services/adminApi';
import DateRangePicker from '@/components/admin/components/DateRangePicker';
import SalesChart from '@/components/admin/components/SalesChart';
import CustomerLifecycleChart from '@/components/admin/components/CustomerLifecycleChart';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import toast from 'react-hot-toast';

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<'sales' | 'customers' | 'inventory'>('sales');
  const [salesData, setSalesData] = useState<SalesReport | null>(null);
  const [inventoryData, setInventoryData] = useState<StockMaintenanceReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({
    from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    to: new Date().toISOString().split('T')[0]
  });

  const fetchAnalyticsData = useCallback(async () => {
    try {
      setLoading(true);
      
      if (activeTab === 'sales') {
        const data = await adminApi.getSalesReport({
          date_from: dateRange.from,
          date_to: dateRange.to
        });
        setSalesData(data);
      } else if (activeTab === 'customers') {
        const data = await adminApi.getCustomerAnalyticsSummary();
        // Customer data is handled by CustomerLifecycleChart component
      } else if (activeTab === 'inventory') {
        const data = await adminApi.getStockMaintenanceReport();
        setInventoryData(data);
      }
    } catch (error) {
      console.error('Failed to fetch analytics data:', error);
      toast.error('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  }, [activeTab, dateRange]);

  useEffect(() => {
    fetchAnalyticsData();
  }, [activeTab, dateRange]);

  const handleDateRangeChange = (from: string, to: string) => {
    setDateRange({ from, to });
  };

  const handleExportReport = async () => {
    try {
      let reportType: 'sales' | 'customer' | 'inventory' = 'sales';
      if (activeTab === 'customers') reportType = 'customer';
      if (activeTab === 'inventory') reportType = 'inventory';

      await adminApi.exportReport({
        report_type: reportType,
        export_format: 'csv',
        date_from: dateRange.from,
        date_to: dateRange.to
      });
      toast.success('Report export started. You will be notified when ready.');
    } catch (error) {
      console.error('Failed to export report:', error);
      toast.error('Failed to export report');
    }
  };

  const tabs = [
    { id: 'sales', name: 'Sales Analytics', icon: TrendingUp },
    { id: 'customers', name: 'Customer Analytics', icon: Users },
    { id: 'inventory', name: 'Inventory Analytics', icon: Package },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Advanced Analytics</h1>
          <p className="mt-1 text-sm text-gray-500">
            Detailed insights and performance metrics
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex items-center space-x-3">
          <DateRangePicker
            from={dateRange.from}
            to={dateRange.to}
            onChange={handleDateRangeChange}
          />
          <button
            onClick={handleExportReport}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                  isActive
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="h-5 w-5 mr-2" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <div className="space-y-6">
          {activeTab === 'sales' && salesData && (
            <div className="space-y-6">
              {/* Sales Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <ShoppingCart className="h-8 w-8 text-blue-500" />
                    </div>
                    <div className="ml-4">
                      <h4 className="text-sm font-medium text-gray-500">Total Orders</h4>
                      <p className="text-2xl font-semibold text-gray-900">
                        {salesData.summary.total_orders.toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <TrendingUp className="h-8 w-8 text-green-500" />
                    </div>
                    <div className="ml-4">
                      <h4 className="text-sm font-medium text-gray-500">Total Revenue</h4>
                      <p className="text-2xl font-semibold text-gray-900">
                        ${salesData.summary.total_revenue.toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <TrendingUp className="h-8 w-8 text-purple-500" />
                    </div>
                    <div className="ml-4">
                      <h4 className="text-sm font-medium text-gray-500">Avg Order Value</h4>
                      <p className="text-2xl font-semibold text-gray-900">
                        ${salesData.summary.average_order_value.toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <TrendingUp className="h-8 w-8 text-yellow-500" />
                    </div>
                    <div className="ml-4">
                      <h4 className="text-sm font-medium text-gray-500">Total Discounts</h4>
                      <p className="text-2xl font-semibold text-gray-900">
                        ${salesData.summary.total_discount.toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Sales Chart */}
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Sales Trend</h3>
                <SalesChart dateRange={dateRange} />
              </div>

              {/* Payment Methods */}
              {salesData.payment_methods.length > 0 && (
                <div className="bg-white p-6 rounded-lg shadow">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Payment Methods</h3>
                  <div className="space-y-3">
                    {salesData.payment_methods.map((method, index) => {
                      const percentage = (method.revenue / salesData.summary.total_revenue) * 100;
                      return (
                        <div key={`${method.payment_method}-${index}`} className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div className="text-sm font-medium text-gray-900">
                              {method.payment_method || 'Unknown'}
                            </div>
                            <div className="text-sm text-gray-500">
                              {method.count} orders
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-medium text-gray-900">
                              ${method.revenue.toLocaleString()}
                            </div>
                            <div className="text-xs text-gray-500">
                              {percentage.toFixed(1)}%
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'customers' && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Customer Lifecycle Analysis</h3>
              <CustomerLifecycleChart />
            </div>
          )}

          {activeTab === 'inventory' && inventoryData && (
            <div className="space-y-6">
              {/* Inventory Summary */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">
                      {inventoryData.summary.low_stock_count}
                    </div>
                    <div className="text-sm text-gray-500">Low Stock Items</div>
                  </div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">
                      {inventoryData.summary.out_of_stock_count}
                    </div>
                    <div className="text-sm text-gray-500">Out of Stock</div>
                  </div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {inventoryData.summary.overstock_count}
                    </div>
                    <div className="text-sm text-gray-500">Overstock Items</div>
                  </div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-600">
                      {inventoryData.summary.dead_stock_count}
                    </div>
                    <div className="text-sm text-gray-500">Dead Stock Items</div>
                  </div>
                </div>
              </div>

              {/* Low Stock Items */}
              {inventoryData.low_stock.length > 0 && (
                <div className="bg-white shadow rounded-lg">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-medium text-gray-900">Low Stock Items</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Product
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            SKU
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Current Stock
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Minimum Level
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Reorder Point
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {inventoryData.low_stock.slice(0, 10).map((item) => (
                          <tr key={item.product_id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {item.product_name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {item.sku}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-600 font-medium">
                              {item.current_quantity}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {item.minimum_level}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {item.reorder_point}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
