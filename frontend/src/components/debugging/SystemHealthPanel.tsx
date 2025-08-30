/**
 * System Health Panel Component
 * 
 * Displays real-time system health metrics for frontend, backend, and database layers.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface SystemMetrics {
  frontend: {
    status: 'healthy' | 'warning' | 'error';
    responseTime: number;
    errorRate: number;
    activeUsers: number;
    memoryUsage: number;
  };
  backend: {
    status: 'healthy' | 'warning' | 'error';
    responseTime: number;
    errorRate: number;
    activeConnections: number;
    cpuUsage: number;
  };
  database: {
    status: 'healthy' | 'warning' | 'error';
    queryTime: number;
    connectionPool: number;
    slowQueries: number;
    diskUsage: number;
  };
  timestamp: string;
}

interface HealthMetric {
  name: string;
  value: number;
  unit: string;
  status: 'healthy' | 'warning' | 'error';
  threshold: { warning: number; error: number };
}

export function SystemHealthPanel() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [historicalData, setHistoricalData] = useState<SystemMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState(5000); // 5 seconds

  useEffect(() => {
    fetchSystemMetrics();
    const interval = setInterval(fetchSystemMetrics, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const fetchSystemMetrics = async () => {
    try {
      const response = await fetch('/api/v1/debugging/system-health/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setMetrics(data);
      
      // Update historical data (keep last 20 points)
      setHistoricalData(prev => {
        const newData = [...prev, data].slice(-20);
        return newData;
      });

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: 'healthy' | 'warning' | 'error') => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: 'healthy' | 'warning' | 'error') => {
    switch (status) {
      case 'healthy':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'warning':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const renderMetricCard = (title: string, metrics: HealthMetric[], status: 'healthy' | 'warning' | 'error') => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <div className={`flex items-center px-2 py-1 rounded-full text-sm font-medium ${getStatusColor(status)}`}>
          {getStatusIcon(status)}
          <span className="ml-1 capitalize">{status}</span>
        </div>
      </div>

      <div className="space-y-4">
        {metrics.map((metric, index) => (
          <div key={index} className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-gray-900">{metric.name}</div>
              <div className="text-xs text-gray-500">
                Warning: {metric.threshold.warning}{metric.unit} | Error: {metric.threshold.error}{metric.unit}
              </div>
            </div>
            <div className="text-right">
              <div className={`text-lg font-bold ${getStatusColor(metric.status).split(' ')[0]}`}>
                {metric.value.toFixed(1)}{metric.unit}
              </div>
              <div className="w-20 bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    metric.status === 'healthy' ? 'bg-green-500' :
                    metric.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min((metric.value / metric.threshold.error) * 100, 100)}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderResponseTimeChart = () => {
    if (historicalData.length === 0) return null;

    const chartData = {
      labels: historicalData.map((_, index) => `${index + 1}`),
      datasets: [
        {
          label: 'Frontend (ms)',
          data: historicalData.map(d => d.frontend.responseTime),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
        },
        {
          label: 'Backend (ms)',
          data: historicalData.map(d => d.backend.responseTime),
          borderColor: 'rgb(16, 185, 129)',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4,
        },
        {
          label: 'Database (ms)',
          data: historicalData.map(d => d.database.queryTime),
          borderColor: 'rgb(245, 158, 11)',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          tension: 0.4,
        },
      ],
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: 'Response Time Trends',
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Response Time (ms)',
          },
        },
      },
    };

    return (
      <div className="bg-white rounded-lg shadow p-6">
        <Line data={chartData} options={options} />
      </div>
    );
  };

  const renderSystemOverview = () => {
    if (!metrics) return null;

    const overallStatus = [metrics.frontend.status, metrics.backend.status, metrics.database.status]
      .includes('error') ? 'error' :
      [metrics.frontend.status, metrics.backend.status, metrics.database.status]
        .includes('warning') ? 'warning' : 'healthy';

    const statusCounts = {
      healthy: [metrics.frontend.status, metrics.backend.status, metrics.database.status]
        .filter(s => s === 'healthy').length,
      warning: [metrics.frontend.status, metrics.backend.status, metrics.database.status]
        .filter(s => s === 'warning').length,
      error: [metrics.frontend.status, metrics.backend.status, metrics.database.status]
        .filter(s => s === 'error').length,
    };

    const chartData = {
      labels: ['Healthy', 'Warning', 'Error'],
      datasets: [
        {
          data: [statusCounts.healthy, statusCounts.warning, statusCounts.error],
          backgroundColor: ['#10B981', '#F59E0B', '#EF4444'],
          borderWidth: 0,
        },
      ],
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'bottom' as const,
        },
        title: {
          display: true,
          text: 'System Status Overview',
        },
      },
    };

    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Overall System Status</h3>
          <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(overallStatus)}`}>
            {getStatusIcon(overallStatus)}
            <span className="ml-2 capitalize">{overallStatus}</span>
          </div>
        </div>
        <div className="w-64 mx-auto">
          <Doughnut data={chartData} options={options} />
        </div>
      </div>
    );
  };

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex">
          <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading system metrics</h3>
            <div className="mt-2 text-sm text-red-700">{error}</div>
            <button
              onClick={fetchSystemMetrics}
              className="mt-2 text-sm bg-red-100 text-red-800 px-3 py-1 rounded hover:bg-red-200"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  const frontendMetrics: HealthMetric[] = [
    {
      name: 'Response Time',
      value: metrics.frontend.responseTime,
      unit: 'ms',
      status: metrics.frontend.responseTime > 1000 ? 'error' : metrics.frontend.responseTime > 500 ? 'warning' : 'healthy',
      threshold: { warning: 500, error: 1000 },
    },
    {
      name: 'Error Rate',
      value: metrics.frontend.errorRate,
      unit: '%',
      status: metrics.frontend.errorRate > 5 ? 'error' : metrics.frontend.errorRate > 2 ? 'warning' : 'healthy',
      threshold: { warning: 2, error: 5 },
    },
    {
      name: 'Memory Usage',
      value: metrics.frontend.memoryUsage,
      unit: 'MB',
      status: metrics.frontend.memoryUsage > 512 ? 'error' : metrics.frontend.memoryUsage > 256 ? 'warning' : 'healthy',
      threshold: { warning: 256, error: 512 },
    },
  ];

  const backendMetrics: HealthMetric[] = [
    {
      name: 'Response Time',
      value: metrics.backend.responseTime,
      unit: 'ms',
      status: metrics.backend.responseTime > 2000 ? 'error' : metrics.backend.responseTime > 1000 ? 'warning' : 'healthy',
      threshold: { warning: 1000, error: 2000 },
    },
    {
      name: 'Error Rate',
      value: metrics.backend.errorRate,
      unit: '%',
      status: metrics.backend.errorRate > 5 ? 'error' : metrics.backend.errorRate > 2 ? 'warning' : 'healthy',
      threshold: { warning: 2, error: 5 },
    },
    {
      name: 'CPU Usage',
      value: metrics.backend.cpuUsage,
      unit: '%',
      status: metrics.backend.cpuUsage > 80 ? 'error' : metrics.backend.cpuUsage > 60 ? 'warning' : 'healthy',
      threshold: { warning: 60, error: 80 },
    },
  ];

  const databaseMetrics: HealthMetric[] = [
    {
      name: 'Query Time',
      value: metrics.database.queryTime,
      unit: 'ms',
      status: metrics.database.queryTime > 1000 ? 'error' : metrics.database.queryTime > 500 ? 'warning' : 'healthy',
      threshold: { warning: 500, error: 1000 },
    },
    {
      name: 'Connection Pool',
      value: metrics.database.connectionPool,
      unit: '%',
      status: metrics.database.connectionPool > 90 ? 'error' : metrics.database.connectionPool > 70 ? 'warning' : 'healthy',
      threshold: { warning: 70, error: 90 },
    },
    {
      name: 'Disk Usage',
      value: metrics.database.diskUsage,
      unit: '%',
      status: metrics.database.diskUsage > 85 ? 'error' : metrics.database.diskUsage > 70 ? 'warning' : 'healthy',
      threshold: { warning: 70, error: 85 },
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">System Health Monitor</h2>
        <div className="flex items-center space-x-4">
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value={1000}>1s refresh</option>
            <option value={5000}>5s refresh</option>
            <option value={10000}>10s refresh</option>
            <option value={30000}>30s refresh</option>
          </select>
          <button
            onClick={fetchSystemMetrics}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
          >
            Refresh Now
          </button>
        </div>
      </div>

      {/* System Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          {renderSystemOverview()}
        </div>
        <div className="lg:col-span-3">
          {renderResponseTimeChart()}
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {renderMetricCard('Frontend', frontendMetrics, metrics.frontend.status)}
        {renderMetricCard('Backend', backendMetrics, metrics.backend.status)}
        {renderMetricCard('Database', databaseMetrics, metrics.database.status)}
      </div>

      {/* Additional Info */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <div className="font-medium text-gray-700">Active Users</div>
            <div className="text-2xl font-bold text-blue-600">{metrics.frontend.activeUsers}</div>
          </div>
          <div>
            <div className="font-medium text-gray-700">Active Connections</div>
            <div className="text-2xl font-bold text-green-600">{metrics.backend.activeConnections}</div>
          </div>
          <div>
            <div className="font-medium text-gray-700">Slow Queries</div>
            <div className="text-2xl font-bold text-yellow-600">{metrics.database.slowQueries}</div>
          </div>
        </div>
        <div className="mt-4 text-xs text-gray-500">
          Last updated: {new Date(metrics.timestamp).toLocaleString()}
        </div>
      </div>
    </div>
  );
}