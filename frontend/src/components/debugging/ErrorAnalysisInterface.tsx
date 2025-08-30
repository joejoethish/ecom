/**
 * Error Analysis Interface Component
 * 
 * Provides error grouping, analysis, and resolution suggestions.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface ErrorGroup {
  id: string;
  errorType: string;
  errorMessage: string;
  count: number;
  firstSeen: string;
  lastSeen: string;
  affectedComponents: string[];
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'investigating' | 'resolved' | 'ignored';
  resolutionSuggestions: ResolutionSuggestion[];
  recentOccurrences: ErrorOccurrence[];
}

interface ErrorOccurrence {
  id: string;
  timestamp: string;
  correlationId: string;
  layer: 'frontend' | 'api' | 'database';
  component: string;
  stackTrace?: string;
  metadata: Record<string, any>;
  userAgent?: string;
  userId?: string;
}

interface ResolutionSuggestion {
  type: 'code_fix' | 'configuration' | 'infrastructure' | 'monitoring';
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  estimatedEffort: string;
  steps: string[];
}

interface ErrorAnalytics {
  totalErrors: number;
  errorsByLayer: Record<string, number>;
  errorsByType: Record<string, number>;
  errorTrends: Array<{ date: string; count: number }>;
  topComponents: Array<{ component: string; count: number }>;
}

export function ErrorAnalysisInterface() {
  const [errorGroups, setErrorGroups] = useState<ErrorGroup[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<ErrorGroup | null>(null);
  const [analytics, setAnalytics] = useState<ErrorAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    severity: '',
    status: '',
    layer: '',
    timeRange: '24h',
  });

  useEffect(() => {
    fetchErrorData();
  }, [filters]);

  const fetchErrorData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const [groupsResponse, analyticsResponse] = await Promise.all([
        fetch(`/api/v1/debugging/error-groups/?${params}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }),
        fetch(`/api/v1/debugging/error-analytics/?${params}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }),
      ]);

      if (groupsResponse.ok) {
        const groupsData = await groupsResponse.json();
        setErrorGroups(groupsData.results || groupsData);
      }

      if (analyticsResponse.ok) {
        const analyticsData = await analyticsResponse.json();
        setAnalytics(analyticsData);
      }

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch error data');
    } finally {
      setLoading(false);
    }
  };

  const updateErrorStatus = async (groupId: string, status: string) => {
    try {
      const response = await fetch(`/api/v1/debugging/error-groups/${groupId}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({ status }),
      });

      if (response.ok) {
        setErrorGroups(prev => 
          prev.map(group => 
            group.id === groupId ? { ...group, status: status as any } : group
          )
        );
        
        if (selectedGroup?.id === groupId) {
          setSelectedGroup(prev => prev ? { ...prev, status: status as any } : null);
        }
      }
    } catch (error) {
      console.error('Failed to update error status:', error);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-800 bg-red-100 border-red-200';
      case 'high': return 'text-red-700 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-700 bg-green-50 border-green-200';
      default: return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'text-red-700 bg-red-100';
      case 'investigating': return 'text-yellow-700 bg-yellow-100';
      case 'resolved': return 'text-green-700 bg-green-100';
      case 'ignored': return 'text-gray-700 bg-gray-100';
      default: return 'text-gray-700 bg-gray-100';
    }
  };

  const renderErrorAnalytics = () => {
    if (!analytics) return null;

    const layerChartData = {
      labels: Object.keys(analytics.errorsByLayer),
      datasets: [
        {
          data: Object.values(analytics.errorsByLayer),
          backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
          borderWidth: 0,
        },
      ],
    };

    const trendChartData = {
      labels: analytics.errorTrends.map(t => new Date(t.date).toLocaleDateString()),
      datasets: [
        {
          label: 'Error Count',
          data: analytics.errorTrends.map(t => t.count),
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          borderColor: 'rgb(239, 68, 68)',
          borderWidth: 2,
          tension: 0.4,
        },
      ],
    };

    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Total Errors */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Error Overview</h3>
          <div className="text-center">
            <div className="text-3xl font-bold text-red-600">{analytics.totalErrors}</div>
            <div className="text-sm text-gray-600">Total Errors</div>
          </div>
          <div className="mt-4 space-y-2">
            {analytics.topComponents.slice(0, 3).map((comp, index) => (
              <div key={index} className="flex justify-between text-sm">
                <span className="text-gray-600">{comp.component}</span>
                <span className="font-medium">{comp.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Errors by Layer */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Errors by Layer</h3>
          <div className="h-48">
            <Doughnut 
              data={layerChartData} 
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom',
                  },
                },
              }}
            />
          </div>
        </div>

        {/* Error Trends */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Error Trends</h3>
          <div className="h-48">
            <Bar 
              data={trendChartData} 
              options={{
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                  },
                },
                plugins: {
                  legend: {
                    display: false,
                  },
                },
              }}
            />
          </div>
        </div>
      </div>
    );
  };

  const renderErrorGroupsList = () => (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Error Groups</h3>
          <button
            onClick={fetchErrorData}
            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
          >
            Refresh
          </button>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <select
            value={filters.severity}
            onChange={(e) => setFilters(prev => ({ ...prev, severity: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded text-sm"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded text-sm"
          >
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="ignored">Ignored</option>
          </select>

          <select
            value={filters.layer}
            onChange={(e) => setFilters(prev => ({ ...prev, layer: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded text-sm"
          >
            <option value="">All Layers</option>
            <option value="frontend">Frontend</option>
            <option value="api">API</option>
            <option value="database">Database</option>
          </select>

          <select
            value={filters.timeRange}
            onChange={(e) => setFilters(prev => ({ ...prev, timeRange: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded text-sm"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {errorGroups.map((group) => (
          <div
            key={group.id}
            onClick={() => setSelectedGroup(group)}
            className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
              selectedGroup?.id === group.id ? 'bg-blue-50 border-blue-200' : ''
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <span className={`px-2 py-1 rounded text-xs font-medium border ${getSeverityColor(group.severity)}`}>
                    {group.severity.toUpperCase()}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(group.status)}`}>
                    {group.status}
                  </span>
                </div>
                <div className="font-medium text-gray-900 mb-1">{group.errorType}</div>
                <div className="text-sm text-gray-600 mb-2 line-clamp-2">{group.errorMessage}</div>
                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  <span>Count: {group.count}</span>
                  <span>Components: {group.affectedComponents.join(', ')}</span>
                  <span>Last seen: {new Date(group.lastSeen).toLocaleString()}</span>
                </div>
              </div>
              <div className="ml-4 text-right">
                <div className="text-2xl font-bold text-red-600">{group.count}</div>
                <div className="text-xs text-gray-500">occurrences</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderErrorDetails = () => {
    if (!selectedGroup) {
      return (
        <div className="bg-white rounded-lg shadow p-8 flex items-center justify-center text-gray-500">
          Select an error group to view details
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* Error Group Header */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">{selectedGroup.errorType}</h3>
              <p className="text-gray-600 mb-4">{selectedGroup.errorMessage}</p>
              <div className="flex items-center space-x-4">
                <span className={`px-3 py-1 rounded text-sm font-medium border ${getSeverityColor(selectedGroup.severity)}`}>
                  {selectedGroup.severity.toUpperCase()}
                </span>
                <span className={`px-3 py-1 rounded text-sm font-medium ${getStatusColor(selectedGroup.status)}`}>
                  {selectedGroup.status}
                </span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-red-600">{selectedGroup.count}</div>
              <div className="text-sm text-gray-600">Total Occurrences</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">First Seen:</span>
              <div>{new Date(selectedGroup.firstSeen).toLocaleString()}</div>
            </div>
            <div>
              <span className="font-medium text-gray-700">Last Seen:</span>
              <div>{new Date(selectedGroup.lastSeen).toLocaleString()}</div>
            </div>
            <div>
              <span className="font-medium text-gray-700">Affected Components:</span>
              <div>{selectedGroup.affectedComponents.join(', ')}</div>
            </div>
          </div>

          {/* Status Actions */}
          <div className="mt-4 flex space-x-2">
            {['investigating', 'resolved', 'ignored'].map((status) => (
              <button
                key={status}
                onClick={() => updateErrorStatus(selectedGroup.id, status)}
                className={`px-3 py-1 rounded text-sm font-medium ${
                  selectedGroup.status === status
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Mark as {status}
              </button>
            ))}
          </div>
        </div>

        {/* Resolution Suggestions */}
        {selectedGroup.resolutionSuggestions.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="text-lg font-semibold mb-4">Resolution Suggestions</h4>
            <div className="space-y-4">
              {selectedGroup.resolutionSuggestions.map((suggestion, index) => (
                <div key={index} className="border border-gray-200 rounded p-4">
                  <div className="flex items-start justify-between mb-2">
                    <h5 className="font-medium text-gray-900">{suggestion.title}</h5>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        suggestion.priority === 'high' ? 'bg-red-100 text-red-800' :
                        suggestion.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {suggestion.priority} priority
                      </span>
                      <span className="text-xs text-gray-500">{suggestion.estimatedEffort}</span>
                    </div>
                  </div>
                  <p className="text-gray-600 text-sm mb-3">{suggestion.description}</p>
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-1">Steps:</div>
                    <ol className="list-decimal list-inside text-sm text-gray-600 space-y-1">
                      {suggestion.steps.map((step, stepIndex) => (
                        <li key={stepIndex}>{step}</li>
                      ))}
                    </ol>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Occurrences */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-semibold mb-4">Recent Occurrences</h4>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {selectedGroup.recentOccurrences.map((occurrence) => (
              <div key={occurrence.id} className="border border-gray-200 rounded p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">{occurrence.component}</span>
                    <span className="text-xs text-gray-500">({occurrence.layer})</span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(occurrence.timestamp).toLocaleString()}
                  </div>
                </div>
                <div className="text-xs text-gray-600 mb-2">
                  Correlation ID: {occurrence.correlationId}
                </div>
                {occurrence.stackTrace && (
                  <details className="text-xs">
                    <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                      View Stack Trace
                    </summary>
                    <pre className="mt-2 bg-gray-50 p-2 rounded overflow-x-auto">
                      {occurrence.stackTrace}
                    </pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="text-red-800">{error}</div>
        <button
          onClick={fetchErrorData}
          className="mt-2 text-sm bg-red-100 text-red-800 px-3 py-1 rounded hover:bg-red-200"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Error Analysis</h2>
      </div>

      {/* Analytics Overview */}
      {renderErrorAnalytics()}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Error Groups List */}
        <div>
          {renderErrorGroupsList()}
        </div>

        {/* Error Details */}
        <div>
          {renderErrorDetails()}
        </div>
      </div>
    </div>
  );
}