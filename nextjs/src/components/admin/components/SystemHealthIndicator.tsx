'use client';

import { useState, useEffect } from 'react';
import { Activity, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { adminApi, SystemHealthSummary } from '@/services/adminApi';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function SystemHealthIndicator() {
  const [healthData, setHealthData] = useState<SystemHealthSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealthData = async () => {
      try {
        setLoading(true);
        const data = await adminApi.getSystemHealth(24);
        setHealthData(data);
      } catch (error) {
        console.error('Failed to fetch system health:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHealthData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchHealthData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (!healthData) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Unable to load system health data
      </div>
    );
  }

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-6 w-6 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-6 w-6 text-yellow-500" />;
      case 'critical':
        return <XCircle className="h-6 w-6 text-red-500" />;
      default:
        return <Activity className="h-6 w-6 text-gray-500" />;
    }
  };

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'critical':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const metrics = [
    {
      label: 'Response Time',
      current: `${healthData.current_metrics.response_time.toFixed(0)}ms`,
      average: `${healthData.period_summary.avg_response_time?.toFixed(0) || 0}ms`,
      status: healthData.current_metrics.response_time > 1000 ? 'warning' : 'healthy'
    },
    {
      label: 'Error Rate',
      current: `${healthData.current_metrics.error_rate.toFixed(1)}%`,
      average: `${healthData.period_summary.avg_error_rate?.toFixed(1) || 0}%`,
      status: healthData.current_metrics.error_rate > 5 ? 'critical' : 
               healthData.current_metrics.error_rate > 2 ? 'warning' : 'healthy'
    },
    {
      label: 'Active Users',
      current: healthData.current_metrics.active_users.toString(),
      average: Math.round(healthData.period_summary.avg_active_users || 0).toString(),
      status: 'healthy'
    },
    {
      label: 'Memory Usage',
      current: `${healthData.current_metrics.memory_usage.toFixed(1)}%`,
      average: 'N/A',
      status: healthData.current_metrics.memory_usage > 80 ? 'critical' : 
               healthData.current_metrics.memory_usage > 60 ? 'warning' : 'healthy'
    },
    {
      label: 'CPU Usage',
      current: `${healthData.current_metrics.cpu_usage.toFixed(1)}%`,
      average: 'N/A',
      status: healthData.current_metrics.cpu_usage > 80 ? 'critical' : 
               healthData.current_metrics.cpu_usage > 60 ? 'warning' : 'healthy'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Overall Health Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {getHealthIcon(healthData.health_status)}
          <div>
            <h4 className="text-lg font-medium text-gray-900">System Status</h4>
            <p className={`text-sm font-medium px-2 py-1 rounded-full inline-block ${getHealthColor(healthData.health_status)}`}>
              {healthData.health_status.charAt(0).toUpperCase() + healthData.health_status.slice(1)}
            </p>
          </div>
        </div>
        <div className="text-right text-sm text-gray-500">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {metrics.map((metric) => (
          <div key={metric.label} className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">{metric.label}</span>
              {getHealthIcon(metric.status)}
            </div>
            <div className="space-y-1">
              <div className="text-lg font-semibold text-gray-900">
                {metric.current}
              </div>
              <div className="text-xs text-gray-500">
                24h avg: {metric.average}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Performance Indicators */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">
            {healthData.period_summary.max_active_users || 0}
          </div>
          <div className="text-sm text-gray-500">Peak Users (24h)</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {((1 - (healthData.period_summary.avg_error_rate || 0) / 100) * 100).toFixed(2)}%
          </div>
          <div className="text-sm text-gray-500">Uptime (24h)</div>
        </div>
      </div>
    </div>
  );
}