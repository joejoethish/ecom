'use client';

import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string;
  change?: number;
  changeType?: 'increase' | 'decrease';
  icon: LucideIcon;
  color: 'blue' | 'green' | 'purple' | 'yellow' | 'red';
}

const colorClasses = {
  blue: 'text-blue-500 bg-blue-100',
  green: 'text-green-500 bg-green-100',
  purple: 'text-purple-500 bg-purple-100',
  yellow: 'text-yellow-500 bg-yellow-100',
  red: 'text-red-500 bg-red-100',
};

export default function MetricCard({ 
  title, 
  value, 
  change, 
  changeType, 
  icon: Icon, 
  color 
}: MetricCardProps) {
  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={`p-3 rounded-md ${colorClasses[color]}`}>
              <Icon className="h-6 w-6" />
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">
                {title}
              </dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900">
                  {value}
                </div>
                {change !== undefined && (
                  <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                    changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {changeType === &apos;increase&apos; ? (
                      <TrendingUp className="self-center flex-shrink-0 h-4 w-4 mr-1" />
                    ) : (
                      <TrendingDown className="self-center flex-shrink-0 h-4 w-4 mr-1" />
                    )}
                    <span className="sr-only">
                      {changeType === &apos;increase&apos; ? &apos;Increased&apos; : &apos;Decreased&apos;} by
                    </span>
                    {Math.abs(change).toFixed(1)}%
                  </div>
                )}
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}