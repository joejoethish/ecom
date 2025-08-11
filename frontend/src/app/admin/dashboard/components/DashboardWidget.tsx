'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  IconButton,
  Card,
  CardContent
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  ShowChart as ChartIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface DashboardWidgetProps {
  widget: {
    id: string;
    name: string;
    title: string;
    widget_type: string;
    chart_type?: string;
    display_config: any;
    chart_config: any;
  };
  onRefresh: () => void;
}

export function DashboardWidget({ widget, onRefresh }: DashboardWidgetProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    fetchWidgetData();
  }, [widget.id]);

  const fetchWidgetData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/admin/dashboard/widgets/${widget.id}/data/`);
      if (!response.ok) {
        throw new Error('Failed to fetch widget data');
      }
      
      const result = await response.json();
      setData(result);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchWidgetData();
    onRefresh();
  };

  const renderMetricWidget = () => {
    if (!data) return null;

    const value = data.total_sales || data.total_customers || data.total_products || 0;
    const growth = data.sales_growth || data.customer_retention || 0;
    const isPositive = growth >= 0;

    return (
      <Box textAlign="center">
        <Typography variant="h3" component="div" color="primary" gutterBottom>
          {typeof value === 'number' ? value.toLocaleString() : value}
        </Typography>
        <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
          {isPositive ? (
            <TrendingUpIcon color="success" fontSize="small" />
          ) : (
            <TrendingDownIcon color="error" fontSize="small" />
          )}
          <Typography
            variant="body2"
            color={isPositive ? 'success.main' : 'error.main'}
          >
            {Math.abs(growth).toFixed(1)}%
          </Typography>
        </Box>
      </Box>
    );
  };

  const renderChartWidget = () => {
    if (!data || !data.labels || !data.data) return null;

    const chartData = data.labels.map((label: string, index: number) => ({
      name: label,
      value: data.data[index]
    }));

    const colors = widget.display_config?.colors || ['#8884d8', '#82ca9d', '#ffc658', '#ff7300'];

    switch (widget.chart_type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke={colors[0]} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Area type="monotone" dataKey="value" stroke={colors[0]} fill={colors[0]} />
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill={colors[0]} />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );

      default:
        return (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke={colors[0]} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        );
    }
  };

  const renderTableWidget = () => {
    if (!data || !Array.isArray(data)) return null;

    return (
      <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {Object.keys(data[0] || {}).map((key) => (
                <th
                  key={key}
                  style={{
                    padding: '8px',
                    borderBottom: '1px solid #ddd',
                    textAlign: 'left',
                    fontWeight: 'bold'
                  }}
                >
                  {key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 10).map((row: any, index: number) => (
              <tr key={index}>
                {Object.values(row).map((value: any, cellIndex: number) => (
                  <td
                    key={cellIndex}
                    style={{
                      padding: '8px',
                      borderBottom: '1px solid #eee'
                    }}
                  >
                    {value}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </Box>
    );
  };

  const renderListWidget = () => {
    if (!data || !Array.isArray(data)) return null;

    return (
      <Box>
        {data.slice(0, 5).map((item: any, index: number) => (
          <Box
            key={index}
            display="flex"
            justifyContent="space-between"
            alignItems="center"
            py={1}
            borderBottom={index < data.length - 1 ? '1px solid #eee' : 'none'}
          >
            <Typography variant="body2">
              {item.name || item.title || item.label || `Item ${index + 1}`}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {item.value || item.count || item.amount || ''}
            </Typography>
          </Box>
        ))}
      </Box>
    );
  };

  const renderWidgetContent = () => {
    if (loading) {
      return (
        <Box display="flex" justifyContent="center" alignItems="center" height={200}>
          <CircularProgress />
        </Box>
      );
    }

    if (error) {
      return (
        <Alert severity="error" sx={{ height: 200, display: 'flex', alignItems: 'center' }}>
          {error}
        </Alert>
      );
    }

    switch (widget.widget_type) {
      case 'metric':
        return renderMetricWidget();
      case 'chart':
        return renderChartWidget();
      case 'table':
        return renderTableWidget();
      case 'list':
        return renderListWidget();
      default:
        return (
          <Box display="flex" justifyContent="center" alignItems="center" height={200}>
            <Typography color="text.secondary">
              Widget type not supported: {widget.widget_type}
            </Typography>
          </Box>
        );
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Widget Header */}
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={2}
        sx={{ minHeight: 40 }}
      >
        <Typography variant="h6" component="h3" noWrap>
          {widget.title}
        </Typography>
        <Box display="flex" alignItems="center" gap={1}>
          {lastUpdated && (
            <Typography variant="caption" color="text.secondary">
              {lastUpdated.toLocaleTimeString()}
            </Typography>
          )}
          <IconButton size="small" onClick={handleRefresh} disabled={loading}>
            <RefreshIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>

      {/* Widget Content */}
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        {renderWidgetContent()}
      </Box>
    </Box>
  );
}