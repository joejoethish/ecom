'use client';

import { useState, useEffect } from 'react';
import { adminApi, SalesReport } from '@/services/adminApi';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

interface SalesChartProps {
  dateRange: {
    from: string;
    to: string;
  };
}

export default function SalesChart({ dateRange }: SalesChartProps) {
  const [salesData, setSalesData] = useState<SalesReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSalesData = async () => {
      try {
        setLoading(true);
        const data = await adminApi.getSalesReport({
          date_from: dateRange.from,
          date_to: dateRange.to
        });
        setSalesData(data);
      } catch (error) {
        console.error('Failed to fetch sales data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSalesData();
  }, [dateRange]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (!salesData || !salesData.daily_breakdown.length) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No sales data available for the selected period
      </div>
    );
  }

  // Simple bar chart implementation using CSS
  const maxRevenue = Math.max(...salesData.daily_breakdown.map(d => d.revenue));
  
  return (
    <div className="space-y-4">
      {/* Chart */}
      <div className="h-64 flex items-end space-x-2 overflow-x-auto">
        {salesData.daily_breakdown.map((day, index) => {
          const height = (day.revenue / maxRevenue) * 100;
          return (
            <div key={index} className="flex flex-col items-center min-w-0 flex-1">
              <div className="w-full flex flex-col items-center">
                <div
                  className="w-8 bg-blue-500 rounded-t transition-all duration-300 hover:bg-blue-600"
                  style={{ height: `${height}%` }}
                  title={`${day.day}: $${day.revenue.toLocaleString()}`}
                />
                <div className="text-xs text-gray-500 mt-2 transform -rotate-45 origin-left">
                  {new Date(day.day).toLocaleDateString('en-US', { 
                    month: 'short', 
                    day: 'numeric' 
                  })}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex justify-between text-sm text-gray-600">
        <span>Revenue: ${salesData.summary.total_revenue.toLocaleString()}</span>
        <span>Orders: {salesData.summary.total_orders.toLocaleString()}</span>
        <span>Avg: ${salesData.summary.average_order_value.toFixed(2)}</span>
      </div>
    </div>
  );
}