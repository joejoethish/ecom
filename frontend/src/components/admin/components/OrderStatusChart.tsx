'use client';

interface OrderStatusChartProps {
  data: Record<string, number>;
}

const statusColors: Record<string, string> = {
  pending: '#f59e0b',
  confirmed: '#3b82f6',
  shipped: '#8b5cf6',
  delivered: '#10b981',
  cancelled: '#ef4444',
  returned: '#f97316',
};

const statusLabels: Record<string, string> = {
  pending: 'Pending',
  confirmed: 'Confirmed',
  shipped: 'Shipped',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
  returned: 'Returned',
};

export default function OrderStatusChart({ data }: OrderStatusChartProps) {
  const total = Object.values(data).reduce((sum, value) => sum + value, 0);
  
  if (total === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No order data available
      </div>
    );
  }

  // Create a simple donut chart using CSS
  let cumulativePercentage = 0;
  const segments = Object.entries(data).map(([status, count]) => {
    const percentage = (count / total) * 100;
    const segment = {
      status,
      count,
      percentage,
      color: statusColors[status] || '#6b7280',
      label: statusLabels[status] || status,
      startAngle: cumulativePercentage * 3.6, // Convert to degrees
    };
    cumulativePercentage += percentage;
    return segment;
  });

  return (
    <div className="flex items-center space-x-8">
      {/* Simple pie chart representation */}
      <div className="relative w-48 h-48">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke="#f3f4f6"
            strokeWidth="8"
          />
          {segments.map((segment, index) => {
            const circumference = 2 * Math.PI * 40;
            const strokeDasharray = `${(segment.percentage / 100) * circumference} ${circumference}`;
            const strokeDashoffset = -((segments.slice(0, index).reduce((sum, s) => sum + s.percentage, 0) / 100) * circumference);
            
            return (
              <circle
                key={segment.status}
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke={segment.color}
                strokeWidth="8"
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                className="transition-all duration-300"
              />
            );
          })}
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{total}</div>
            <div className="text-sm text-gray-500">Total Orders</div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="space-y-2">
        {segments.map((segment) => (
          <div key={segment.status} className="flex items-center space-x-3">
            <div
              className="w-4 h-4 rounded-full"
              style={{ backgroundColor: segment.color }}
            />
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-900">
                {segment.label}
              </div>
              <div className="text-xs text-gray-500">
                {segment.count} ({segment.percentage.toFixed(1)}%)
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}