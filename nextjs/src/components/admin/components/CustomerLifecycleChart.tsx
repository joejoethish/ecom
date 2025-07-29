'use client';

import { useState, useEffect } from 'react';
import { adminApi, CustomerAnalyticsSummary } from '@/services/adminApi';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

const lifecycleColors: Record<string, string> = {
  new: '#3b82f6',
  active: '#10b981',
  at_risk: '#f59e0b',
  dormant: '#6b7280',
  churned: '#ef4444',
  vip: '#8b5cf6',
};

const lifecycleLabels: Record<string, string> = {
  new: 'New',
  active: 'Active',
  at_risk: 'At Risk',
  dormant: 'Dormant',
  churned: 'Churned',
  vip: 'VIP',
};

export default function CustomerLifecycleChart() {
  const [data, setData] = useState<CustomerAnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCustomerData = async () => {
      try {
        setLoading(true);
        const customerData = await adminApi.getCustomerAnalyticsSummary();
        setData(customerData);
      } catch (error) {
        console.error('Failed to fetch customer analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCustomerData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (!data || !data.lifecycle_distribution.length) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No customer lifecycle data available
      </div>
    );
  }

  const total = data.lifecycle_distribution.reduce((sum, item) => sum + item.count, 0);
  const maxCount = Math.max(...data.lifecycle_distribution.map(item => item.count));

  return (
    <div className="space-y-6">
      {/* Bar Chart */}
      <div className="space-y-3">
        {data.lifecycle_distribution.map((item) => {
          const percentage = total > 0 ? (item.count / total) * 100 : 0;
          const barWidth = maxCount > 0 ? (item.count / maxCount) * 100 : 0;
          
          return (
            <div key={item.lifecycle_stage} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="font-medium text-gray-700">
                  {lifecycleLabels[item.lifecycle_stage] || item.lifecycle_stage}
                </span>
                <span className="text-gray-500">
                  {item.count} ({percentage.toFixed(1)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="h-3 rounded-full transition-all duration-300"
                  style={{
                    width: `${barWidth}%`,
                    backgroundColor: lifecycleColors[item.lifecycle_stage] || '#6b7280'
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{total}</div>
          <div className="text-sm text-gray-500">Total Customers</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {data.lifecycle_distribution.find(item => item.lifecycle_stage === 'active')?.count || 0}
          </div>
          <div className="text-sm text-gray-500">Active Customers</div>
        </div>
      </div>

      {/* Top Customers */}
      {data.top_customers.length > 0 && (
        <div className="pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Top Customers by Lifetime Value</h4>
          <div className="space-y-2">
            {data.top_customers.slice(0, 5).map((customer, index) => (
              <div key={customer.customer_id} className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  <span className="text-gray-400">#{index + 1}</span>
                  <span className="font-medium text-gray-900">{customer.email}</span>
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    customer.lifecycle_stage === 'vip' ? 'bg-purple-100 text-purple-800' :
                    customer.lifecycle_stage === 'active' ? 'bg-green-100 text-green-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {lifecycleLabels[customer.lifecycle_stage] || customer.lifecycle_stage}
                  </span>
                </div>
                <div className="text-right">
                  <div className="font-medium text-gray-900">
                    ${customer.lifetime_value.toLocaleString()}
                  </div>
                  <div className="text-gray-500">
                    {customer.total_orders} orders
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}