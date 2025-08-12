'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, ScatterChart, Scatter
} from 'recharts';
import { 
  TrendingUp, TrendingDown, Users, DollarSign, ShoppingCart, 
  AlertTriangle, Eye, Settings, Download, Share2, RefreshCw,
  Brain, Target, Zap, Globe, BarChart3, PieChart as PieChartIcon
} from 'lucide-react';

interface BIDashboardProps {
  dashboardId?: string;
  dashboardType?: 'executive' | 'sales' | 'financial' | 'operational' | 'customer' | 'product' | 'custom';
}

interface DashboardData {
  id: string;
  name: string;
  description: string;
  dashboard_type: string;
  layout_config: any;
  filters_config: any;
  widgets: WidgetData[];
}

interface WidgetData {
  id: string;
  name: string;
  widget_type: string;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
  visualization_config: any;
  data: any;
  last_updated: string;
  error?: string;
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

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export default function BIDashboard({ dashboardId, dashboardType = 'executive' }: BIDashboardProps) {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [realtimeMetrics, setRealtimeMetrics] = useState<RealtimeMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDateRange, setSelectedDateRange] = useState('30d');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(300000); // 5 minutes

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      
      let url = '/api/analytics/bi/dashboards/';
      if (dashboardId) {
        url += `${dashboardId}/dashboard_data/?date_range=${selectedDateRange}`;
      } else {
        // Create executive dashboard if none exists
        const response = await fetch('/api/analytics/bi/dashboards/create_executive_dashboard/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({ name: 'Executive Dashboard' })
        });
        
        if (!response.ok) throw new Error('Failed to create dashboard');
        
        const newDashboard = await response.json();
        url = `/api/analytics/bi/dashboards/${newDashboard.id}/dashboard_data/?date_range=${selectedDateRange}`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch dashboard data');
      
      const data = await response.json();
      setDashboardData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [dashboardId, selectedDateRange]);

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
    } catch (err) {
      console.error('Failed to fetch realtime metrics:', err);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
    fetchRealtimeMetrics();
  }, [fetchDashboardData, fetchRealtimeMetrics]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchDashboardData();
        fetchRealtimeMetrics();
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, fetchDashboardData, fetchRealtimeMetrics]);

  const renderWidget = (widget: WidgetData) => {
    if (widget.error) {
      return (
        <Card className="h-full">
          <CardHeader>
            <CardTitle className="text-red-600">{widget.name}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center h-32 text-red-500">
              <AlertTriangle className="w-8 h-8 mr-2" />
              <span>Error loading widget: {widget.error}</span>
            </div>
          </CardContent>
        </Card>
      );
    }

    switch (widget.widget_type) {
      case 'metric':
        return renderMetricWidget(widget);
      case 'chart':
        return renderChartWidget(widget);
      case 'table':
        return renderTableWidget(widget);
      case 'gauge':
        return renderGaugeWidget(widget);
      case 'map':
        return renderMapWidget(widget);
      default:
        return renderDefaultWidget(widget);
    }
  };

  const renderMetricWidget = (widget: WidgetData) => {
    const { data } = widget;
    const trend = data?.revenue_trend || data?.trend;
    
    return (
      <Card className="h-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">{widget.name}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold">
                {typeof data?.current_revenue === 'number' 
                  ? `$${data.current_revenue.toLocaleString()}`
                  : data?.value || 'N/A'
                }
              </div>
              {trend && (
                <div className={`flex items-center text-sm ${
                  trend.direction === 'up' ? 'text-green-600' : 
                  trend.direction === 'down' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {trend.direction === 'up' ? <TrendingUp className="w-4 h-4 mr-1" /> : 
                   trend.direction === 'down' ? <TrendingDown className="w-4 h-4 mr-1" /> : null}
                  {trend.percentage}%
                </div>
              )}
            </div>
            <div className="text-right">
              <DollarSign className="w-8 h-8 text-blue-500" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderChartWidget = (widget: WidgetData) => {
    const { data, visualization_config } = widget;
    const chartType = visualization_config?.chart_type || 'line';
    
    if (!data?.trend_data && !data?.products && !data?.regional_data) {
      return renderDefaultWidget(widget);
    }

    const chartData = data.trend_data || data.products || data.regional_data || [];

    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="text-sm font-medium">{widget.name}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              {chartType === 'line' && (
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="new_customers" stroke="#8884d8" />
                </LineChart>
              )}
              {chartType === 'bar' && (
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="product_name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="revenue" fill="#8884d8" />
                </BarChart>
              )}
              {chartType === 'area' && (
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="revenue" stroke="#8884d8" fill="#8884d8" />
                </AreaChart>
              )}
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderTableWidget = (widget: WidgetData) => {
    const { data } = widget;
    const products = data?.products || [];

    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="text-sm font-medium">{widget.name}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto max-h-64">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Product</th>
                  <th className="text-right p-2">Revenue</th>
                  <th className="text-right p-2">Units</th>
                  <th className="text-right p-2">Margin</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product: any, index: number) => (
                  <tr key={index} className="border-b">
                    <td className="p-2">{product.product_name}</td>
                    <td className="text-right p-2">${product.revenue?.toLocaleString()}</td>
                    <td className="text-right p-2">{product.units_sold}</td>
                    <td className="text-right p-2">{product.profit_margin}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderGaugeWidget = (widget: WidgetData) => {
    const { data } = widget;
    const value = data?.gross_margin_percent || data?.value || 0;
    const maxValue = 100;
    const percentage = (value / maxValue) * 100;

    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="text-sm font-medium">{widget.name}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="relative w-24 h-24">
              <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  stroke="#e5e7eb"
                  strokeWidth="8"
                  fill="none"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  stroke="#3b82f6"
                  strokeWidth="8"
                  fill="none"
                  strokeDasharray={`${percentage * 2.51} 251`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-lg font-bold">{value.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderMapWidget = (widget: WidgetData) => {
    const { data } = widget;
    const regionalData = data?.regional_data || [];

    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="text-sm font-medium">{widget.name}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {regionalData.map((region: any, index: number) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span className="font-medium">{region.region}</span>
                <div className="text-right">
                  <div className="font-bold">${region.revenue?.toLocaleString()}</div>
                  <div className="text-sm text-gray-600">{region.orders} orders</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderDefaultWidget = (widget: WidgetData) => {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="text-sm font-medium">{widget.name}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32 text-gray-500">
            <BarChart3 className="w-8 h-8 mr-2" />
            <span>Widget type: {widget.widget_type}</span>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderRealtimeMetrics = () => {
    if (!realtimeMetrics) return null;

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Users</p>
                <p className="text-2xl font-bold">{realtimeMetrics.active_users}</p>
              </div>
              <Users className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Today's Revenue</p>
                <p className="text-2xl font-bold">${realtimeMetrics.current_revenue.toLocaleString()}</p>
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
              </div>
              <Target className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin mr-2" />
        <span>Loading dashboard...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-red-500">
        <AlertTriangle className="w-8 h-8 mr-2" />
        <span>Error: {error}</span>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <span>No dashboard data available</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{dashboardData.name}</h1>
          <p className="text-gray-600">{dashboardData.description}</p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={selectedDateRange}
            onChange={(e) => setSelectedDateRange(e.target.value)}
            className="px-3 py-2 border rounded-md"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="1y">Last year</option>
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <Zap className={`w-4 h-4 mr-1 ${autoRefresh ? 'text-green-500' : 'text-gray-500'}`} />
            Auto Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={fetchDashboardData}>
            <RefreshCw className="w-4 h-4 mr-1" />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-1" />
            Export
          </Button>
          <Button variant="outline" size="sm">
            <Share2 className="w-4 h-4 mr-1" />
            Share
          </Button>
        </div>
      </div>

      {/* Real-time Metrics */}
      {renderRealtimeMetrics()}

      {/* Dashboard Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {dashboardData.widgets.map((widget) => (
          <div
            key={widget.id}
            className={`col-span-${widget.width} row-span-${widget.height}`}
            style={{
              gridColumn: `span ${widget.width}`,
              gridRow: `span ${widget.height}`
            }}
          >
            {renderWidget(widget)}
          </div>
        ))}
      </div>

      {/* Dashboard Status */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div>
          Last updated: {new Date().toLocaleString()}
        </div>
        <div className="flex items-center space-x-4">
          <Badge variant="outline">
            {dashboardData.widgets.length} widgets
          </Badge>
          <Badge variant="outline">
            {dashboardData.dashboard_type}
          </Badge>
          {autoRefresh && (
            <Badge variant="outline" className="text-green-600">
              Auto-refresh enabled
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
}