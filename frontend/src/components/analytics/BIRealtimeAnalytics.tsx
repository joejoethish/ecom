'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';
import { 
  Zap, Activity, Users, DollarSign, ShoppingCart, Eye, 
  Globe, TrendingUp, TrendingDown, RefreshCw, Play, Pause,
  AlertTriangle, CheckCircle, Clock, Wifi, WifiOff
} from 'lucide-react';

interface BIRealtimeAnalyticsProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface RealtimeMetrics {
  timestamp: string;
  active_users: number;
  current_revenue: number;
  orders_today: number;
  conversion_rate: number;
  cart_abandonment_rate: number;
  page_views: number;
  bounce_rate: number;
  average_session_duration: number;
  top_products_realtime: Array<{name: string; views: number}>;
  geographic_activity: Array<{country: string; active_users: number}>;
}

interface StreamingStatus {
  active_streams: number;
  events_processed_today: number;
  processing_rate: number;
  error_rate: number;
  last_processed: string;
  stream_health: Array<{
    stream: string;
    status: 'healthy' | 'warning' | 'error';
    rate: number;
  }>;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export default function BIRealtimeAnalytics({ 
  autoRefresh = true, 
  refreshInterval = 5000 
}: BIRealtimeAnalyticsProps) {
  const [realtimeMetrics, setRealtimeMetrics] = useState<RealtimeMetrics | null>(null);
  const [streamingStatus, setStreamingStatus] = useState<StreamingStatus | null>(null);
  const [historicalData, setHistoricalData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(autoRefresh);

  const fetchRealtimeMetrics = useCallback(async () => {
    try {
      const response = await fetch('/api/analytics/bi/realtime/realtime_metrics/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch realtime metrics');
      
      const data = await response.json();
      setRealtimeMetrics(data);
      setIsConnected(true);
      setError(null);

      // Add to historical data for trending
      setHistoricalData(prev => {
        const newData = [...prev, {
          timestamp: new Date().toLocaleTimeString(),
          active_users: data.active_users,
          revenue: data.current_revenue,
          orders: data.orders_today,
          conversion_rate: data.conversion_rate
        }];
        // Keep only last 20 data points
        return newData.slice(-20);
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch realtime metrics');
      setIsConnected(false);
    }
  }, []);

  const fetchStreamingStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/analytics/bi/realtime/streaming_status/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch streaming status');
      
      const data = await response.json();
      setStreamingStatus(data);
    } catch (err) {
      console.error('Failed to fetch streaming status:', err);
    }
  }, []);

  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      await Promise.all([fetchRealtimeMetrics(), fetchStreamingStatus()]);
      setLoading(false);
    };

    initializeData();
  }, [fetchRealtimeMetrics, fetchStreamingStatus]);

  useEffect(() => {
    if (autoRefreshEnabled) {
      const interval = setInterval(() => {
        fetchRealtimeMetrics();
        fetchStreamingStatus();
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [autoRefreshEnabled, refreshInterval, fetchRealtimeMetrics, fetchStreamingStatus]);

  const renderConnectionStatus = () => {
    return (
      <div className="flex items-center space-x-2">
        {isConnected ? (
          <>
            <Wifi className="w-4 h-4 text-green-500" />
            <span className="text-sm text-green-600">Connected</span>
          </>
        ) : (
          <>
            <WifiOff className="w-4 h-4 text-red-500" />
            <span className="text-sm text-red-600">Disconnected</span>
          </>
        )}
        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
      </div>
    );
  };

  const renderRealtimeMetrics = () => {
    if (!realtimeMetrics) return null;

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Users</p>
                <p className="text-2xl font-bold">{realtimeMetrics.active_users}</p>
                <p className="text-xs text-gray-500">Right now</p>
              </div>
              <Users className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Revenue Today</p>
                <p className="text-2xl font-bold">${realtimeMetrics.current_revenue.toLocaleString()}</p>
                <p className="text-xs text-gray-500">Live tracking</p>
              </div>
              <DollarSign className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Orders Today</p>
                <p className="text-2xl font-bold">{realtimeMetrics.orders_today}</p>
                <p className="text-xs text-gray-500">Real-time count</p>
              </div>
              <ShoppingCart className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Conversion Rate</p>
                <p className="text-2xl font-bold">{realtimeMetrics.conversion_rate}%</p>
                <p className="text-xs text-gray-500">Current session</p>
              </div>
              <TrendingUp className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderTrendingCharts = () => {
    if (historicalData.length < 2) return null;

    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Active Users Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="active_users" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Revenue Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, 'Revenue']} />
                  <Area 
                    type="monotone" 
                    dataKey="revenue" 
                    stroke="#10b981" 
                    fill="#10b981" 
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderTopProducts = () => {
    if (!realtimeMetrics?.top_products_realtime) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle>Top Products (Real-time Views)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={realtimeMetrics.top_products_realtime}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="views" fill="#8884d8">
                  {realtimeMetrics.top_products_realtime.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderGeographicActivity = () => {
    if (!realtimeMetrics?.geographic_activity) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle>Geographic Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {realtimeMetrics.geographic_activity.map((location, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Globe className="w-5 h-5 text-blue-500" />
                  <span className="font-medium">{location.country}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">{location.active_users} users</span>
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderStreamingStatus = () => {
    if (!streamingStatus) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle>Streaming Data Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-600">Active Streams</p>
              <p className="text-2xl font-bold text-blue-800">{streamingStatus.active_streams}</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <p className="text-sm text-green-600">Events Today</p>
              <p className="text-2xl font-bold text-green-800">
                {streamingStatus.events_processed_today.toLocaleString()}
              </p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <p className="text-sm text-purple-600">Processing Rate</p>
              <p className="text-2xl font-bold text-purple-800">
                {streamingStatus.processing_rate}/sec
              </p>
            </div>
            <div className="p-3 bg-orange-50 rounded-lg">
              <p className="text-sm text-orange-600">Error Rate</p>
              <p className="text-2xl font-bold text-orange-800">
                {streamingStatus.error_rate}%
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="font-semibold">Stream Health</h4>
            {streamingStatus.stream_health.map((stream, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Activity className="w-5 h-5 text-blue-500" />
                  <span className="font-medium">{stream.stream.replace('_', ' ')}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-600">{stream.rate}/sec</span>
                  <Badge className={`${
                    stream.status === 'healthy' ? 'bg-green-100 text-green-800' :
                    stream.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {stream.status === 'healthy' && <CheckCircle className="w-3 h-3 mr-1" />}
                    {stream.status === 'warning' && <AlertTriangle className="w-3 h-3 mr-1" />}
                    {stream.status === 'error' && <AlertTriangle className="w-3 h-3 mr-1" />}
                    {stream.status.toUpperCase()}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin mr-2" />
        <span>Loading real-time analytics...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Real-time Analytics</h1>
          <p className="text-gray-600">Live business metrics and streaming data processing</p>
        </div>
        <div className="flex items-center space-x-4">
          {renderConnectionStatus()}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefreshEnabled(!autoRefreshEnabled)}
          >
            {autoRefreshEnabled ? (
              <Pause className="w-4 h-4 mr-1" />
            ) : (
              <Play className="w-4 h-4 mr-1" />
            )}
            {autoRefreshEnabled ? 'Pause' : 'Resume'}
          </Button>
          <Button variant="outline" size="sm" onClick={fetchRealtimeMetrics}>
            <RefreshCw className="w-4 h-4 mr-1" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}

      {/* Real-time Metrics */}
      {renderRealtimeMetrics()}

      {/* Trending Charts */}
      {renderTrendingCharts()}

      {/* Additional Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {renderTopProducts()}
        {renderGeographicActivity()}
      </div>

      {/* Streaming Status */}
      {renderStreamingStatus()}

      {/* Additional Metrics */}
      {realtimeMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Page Views</p>
                  <p className="text-2xl font-bold">{realtimeMetrics.page_views.toLocaleString()}</p>
                </div>
                <Eye className="w-8 h-8 text-indigo-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Bounce Rate</p>
                  <p className="text-2xl font-bold">{realtimeMetrics.bounce_rate}%</p>
                </div>
                <TrendingDown className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Avg Session</p>
                  <p className="text-2xl font-bold">{Math.round(realtimeMetrics.average_session_duration)}s</p>
                </div>
                <Clock className="w-8 h-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Cart Abandonment</p>
                  <p className="text-2xl font-bold">{realtimeMetrics.cart_abandonment_rate}%</p>
                </div>
                <ShoppingCart className="w-8 h-8 text-gray-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Last Updated */}
      <div className="text-center text-sm text-gray-500">
        Last updated: {realtimeMetrics ? new Date(realtimeMetrics.timestamp).toLocaleString() : 'Never'}
        {autoRefreshEnabled && (
          <span className="ml-2">• Auto-refresh every {refreshInterval / 1000}s</span>
        )}
      </div>
    </div>
  );
}