'use client';

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Users, 
  Target, 
  AlertTriangle,
  Calendar,
  Activity,
  BarChart3,
  PieChart,
  Clock,
  CheckCircle
} from 'lucide-react';

interface DashboardStats {
  counts: {
    total_promotions: number;
    active_promotions: number;
    pending_approval: number;
    expiring_soon: number;
  };
  performance: {
    this_month: {
      total_uses: number;
      total_discount: number;
      total_revenue: number;
      avg_conversion_rate: number;
    };
    last_month: {
      total_uses: number;
      total_discount: number;
      total_revenue: number;
      avg_conversion_rate: number;
    };
  };
  top_promotions: Array<{
    id: string;
    name: string;
    promotion_type_display: string;
    conversion_rate: number;
    roi: number;
    usage_count: number;
    budget_spent: number;
  }>;
}

const PromotionDashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30d');

  useEffect(() => {
    fetchDashboardStats();
  }, [timeRange]);

  const fetchDashboardStats = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/promotions/promotions/dashboard_stats/');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculatePercentageChange = (current: number, previous: number): number => {
    if (previous === 0) return current > 0 ? 100 : 0;
    return ((current - previous) / previous) * 100;
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatNumber = (num: number): string => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Failed to load dashboard data</p>
      </div>
    );
  }

  const thisMonth = stats.performance.this_month;
  const lastMonth = stats.performance.last_month;

  const usageChange = calculatePercentageChange(thisMonth.total_uses || 0, lastMonth.total_uses || 0);
  const revenueChange = calculatePercentageChange(thisMonth.total_revenue || 0, lastMonth.total_revenue || 0);
  const discountChange = calculatePercentageChange(thisMonth.total_discount || 0, lastMonth.total_discount || 0);
  const conversionChange = calculatePercentageChange(thisMonth.avg_conversion_rate || 0, lastMonth.avg_conversion_rate || 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Promotion Dashboard</h1>
          <p className="text-gray-600">Monitor your promotional campaigns performance</p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Promotions */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Promotions</p>
              <p className="text-2xl font-bold text-gray-900">{stats.counts.total_promotions}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <Target className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <span className="text-green-600 font-medium">{stats.counts.active_promotions} active</span>
            <span className="text-gray-500 ml-2">• {stats.counts.pending_approval} pending</span>
          </div>
        </div>

        {/* Usage This Month */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Usage This Month</p>
              <p className="text-2xl font-bold text-gray-900">{formatNumber(thisMonth.total_uses || 0)}</p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <Activity className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            {usageChange >= 0 ? (
              <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
            )}
            <span className={`font-medium ${usageChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {Math.abs(usageChange).toFixed(1)}%
            </span>
            <span className="text-gray-500 ml-1">vs last month</span>
          </div>
        </div>

        {/* Revenue Generated */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Revenue Generated</p>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(thisMonth.total_revenue || 0)}</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <DollarSign className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            {revenueChange >= 0 ? (
              <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
            )}
            <span className={`font-medium ${revenueChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {Math.abs(revenueChange).toFixed(1)}%
            </span>
            <span className="text-gray-500 ml-1">vs last month</span>
          </div>
        </div>

        {/* Avg Conversion Rate */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Conversion Rate</p>
              <p className="text-2xl font-bold text-gray-900">{(thisMonth.avg_conversion_rate || 0).toFixed(2)}%</p>
            </div>
            <div className="p-3 bg-orange-100 rounded-full">
              <BarChart3 className="w-6 h-6 text-orange-600" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            {conversionChange >= 0 ? (
              <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
            )}
            <span className={`font-medium ${conversionChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {Math.abs(conversionChange).toFixed(1)}%
            </span>
            <span className="text-gray-500 ml-1">vs last month</span>
          </div>
        </div>
      </div>

      {/* Alerts and Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Alerts */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="w-5 h-5 text-orange-500 mr-2" />
            Alerts
          </h3>
          <div className="space-y-3">
            {stats.counts.expiring_soon > 0 && (
              <div className="flex items-center p-3 bg-orange-50 rounded-lg">
                <Clock className="w-4 h-4 text-orange-500 mr-2" />
                <div>
                  <p className="text-sm font-medium text-orange-800">
                    {stats.counts.expiring_soon} promotions expiring soon
                  </p>
                  <p className="text-xs text-orange-600">Review and extend if needed</p>
                </div>
              </div>
            )}
            
            {stats.counts.pending_approval > 0 && (
              <div className="flex items-center p-3 bg-blue-50 rounded-lg">
                <Clock className="w-4 h-4 text-blue-500 mr-2" />
                <div>
                  <p className="text-sm font-medium text-blue-800">
                    {stats.counts.pending_approval} promotions pending approval
                  </p>
                  <p className="text-xs text-blue-600">Review and approve campaigns</p>
                </div>
              </div>
            )}

            {stats.counts.expiring_soon === 0 && stats.counts.pending_approval === 0 && (
              <div className="flex items-center p-3 bg-green-50 rounded-lg">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                <div>
                  <p className="text-sm font-medium text-green-800">All good!</p>
                  <p className="text-xs text-green-600">No urgent actions required</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Performance Summary */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <BarChart3 className="w-5 h-5 text-blue-500 mr-2" />
            This Month vs Last Month
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Total Usage</span>
              <div className="flex items-center">
                <span className="text-sm font-medium">{formatNumber(thisMonth.total_uses || 0)}</span>
                <span className={`ml-2 text-xs ${usageChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ({usageChange >= 0 ? '+' : ''}{usageChange.toFixed(1)}%)
                </span>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Revenue</span>
              <div className="flex items-center">
                <span className="text-sm font-medium">{formatCurrency(thisMonth.total_revenue || 0)}</span>
                <span className={`ml-2 text-xs ${revenueChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ({revenueChange >= 0 ? '+' : ''}{revenueChange.toFixed(1)}%)
                </span>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Discount Given</span>
              <div className="flex items-center">
                <span className="text-sm font-medium">{formatCurrency(thisMonth.total_discount || 0)}</span>
                <span className={`ml-2 text-xs ${discountChange >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                  ({discountChange >= 0 ? '+' : ''}{discountChange.toFixed(1)}%)
                </span>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Conversion Rate</span>
              <div className="flex items-center">
                <span className="text-sm font-medium">{(thisMonth.avg_conversion_rate || 0).toFixed(2)}%</span>
                <span className={`ml-2 text-xs ${conversionChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ({conversionChange >= 0 ? '+' : ''}{conversionChange.toFixed(1)}%)
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button className="w-full text-left p-3 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors">
              <div className="flex items-center">
                <Target className="w-4 h-4 text-blue-500 mr-2" />
                <span className="text-sm font-medium text-blue-800">Create New Promotion</span>
              </div>
            </button>
            
            <button className="w-full text-left p-3 bg-green-50 hover:bg-green-100 rounded-lg transition-colors">
              <div className="flex items-center">
                <BarChart3 className="w-4 h-4 text-green-500 mr-2" />
                <span className="text-sm font-medium text-green-800">View Analytics Report</span>
              </div>
            </button>
            
            <button className="w-full text-left p-3 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors">
              <div className="flex items-center">
                <Users className="w-4 h-4 text-purple-500 mr-2" />
                <span className="text-sm font-medium text-purple-800">Manage Customer Segments</span>
              </div>
            </button>
            
            <button className="w-full text-left p-3 bg-orange-50 hover:bg-orange-100 rounded-lg transition-colors">
              <div className="flex items-center">
                <Calendar className="w-4 h-4 text-orange-500 mr-2" />
                <span className="text-sm font-medium text-orange-800">Schedule Campaigns</span>
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Top Performing Promotions */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Top Performing Promotions</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Promotion
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Usage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Conversion Rate
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ROI
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Budget Spent
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {stats.top_promotions.map((promotion) => (
                <tr key={promotion.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{promotion.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {promotion.promotion_type_display}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatNumber(promotion.usage_count)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {promotion.conversion_rate.toFixed(2)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={promotion.roi >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {promotion.roi.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(promotion.budget_spent)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PromotionDashboard;