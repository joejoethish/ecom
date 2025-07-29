'use client';

import { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  ShoppingCart, 
  Package, 
  DollarSign,
  AlertTriangle,
  Activity,
  Calendar,
  Download
} from 'lucide-react';
import { adminApi, DashboardMetrics } from '@/services/adminApi';
import MetricCard from './components/MetricCard';
import SalesChart from './components/SalesChart';
import OrderStatusChart from './components/OrderStatusChart';
import TopProductsTable from './components/TopProductsTable';
import CustomerLifecycleChart from './components/CustomerLifecycleChart';
import SystemHealthIndicator from './components/SystemHealthIndicator';
import DateRangePicker from './components/DateRangePicker';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import toast from 'react-hot-toast';

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({
    from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    to: new Date().toISOString().split('T')[0]
  });

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const data = await adminApi.getDashboardMetrics(
        dateRange.from,
        dateRange.to
      );
      setMetrics(data);
    } catch (error) {
      console.error('Failed to fetch dashboard metrics:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [dateRange]);

  const handleDateRangeChange = (from: string, to: string) => {
    setDateRange({ from, to });
  };

  const handleExportReport = async () => {
    try {
      const exportData = await adminApi.exportReport({
        report_type: 'sales',
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Failed to load dashboard data</p>
        <button
          onClick={fetchDashboardData}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Overview of your ecommerce platform performance
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

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Revenue"
          value={`$${metrics.sales.total_revenue.toLocaleString()}`}
          change={metrics.sales.revenue_growth}
          changeType={metrics.sales.revenue_growth >= 0 ? 'increase' : 'decrease'}
          icon={DollarSign}
          color="green"
        />
        <MetricCard
          title="Total Orders"
          value={metrics.sales.total_orders.toLocaleString()}
          icon={ShoppingCart}
          color="blue"
        />
        <MetricCard
          title="New Customers"
          value={metrics.customers.new_customers.toLocaleString()}
          icon={Users}
          color="purple"
        />
        <MetricCard
          title="Low Stock Items"
          value={metrics.inventory.low_stock_products.toLocaleString()}
          icon={AlertTriangle}
          color="yellow"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Sales Trend</h3>
          <SalesChart dateRange={dateRange} />
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Order Status Distribution</h3>
          <OrderStatusChart data={metrics.orders_by_status} />
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Customer Lifecycle</h3>
          <CustomerLifecycleChart />
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">System Health</h3>
          <SystemHealthIndicator />
        </div>
      </div>

      {/* Top Products Table */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Top Selling Products</h3>
        </div>
        <TopProductsTable dateRange={dateRange} />
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Users className="h-8 w-8 text-blue-500" />
            </div>
            <div className="ml-4">
              <h4 className="text-sm font-medium text-gray-500">Total Customers</h4>
              <p className="text-2xl font-semibold text-gray-900">
                {metrics.customers.total_customers.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Package className="h-8 w-8 text-green-500" />
            </div>
            <div className="ml-4">
              <h4 className="text-sm font-medium text-gray-500">Total Products</h4>
              <p className="text-2xl font-semibold text-gray-900">
                {metrics.inventory.total_products.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <DollarSign className="h-8 w-8 text-purple-500" />
            </div>
            <div className="ml-4">
              <h4 className="text-sm font-medium text-gray-500">Inventory Value</h4>
              <p className="text-2xl font-semibold text-gray-900">
                ${metrics.inventory.total_inventory_value.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}