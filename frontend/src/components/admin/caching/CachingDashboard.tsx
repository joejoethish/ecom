import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import {
  Activity,
  Database,
  Zap,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Clock,
  HardDrive,
  Wifi,
  Settings
} from 'lucide-react';

interface CacheStats {
  cache_name: string;
  cache_type: string;
  is_active: boolean;
  hit_ratio: number;
  avg_response_time_ms: number;
  memory_usage_percent: number;
  error_count: number;
}

interface CacheMetrics {
  id: string;
  cache_name: string;
  timestamp: string;
  hit_ratio: number;
  avg_response_time_ms: number;
  memory_usage_percent: number;
  hit_count: number;
  miss_count: number;
  performance_grade: string;
}

interface CacheAlert {
  id: string;
  cache_name: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  is_resolved: boolean;
  created_at: string;
  severity_color: string;
}

const CachingDashboard: React.FC = () => {
  const [cacheStats, setCacheStats] = useState<CacheStats[]>([]);
  const [metrics, setMetrics] = useState<CacheMetrics[]>([]);
  const [alerts, setAlerts] = useState<CacheAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');

  useEffect(() => {
    fetchDashboardData();
  }, [selectedTimeRange]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch cache configurations and their stats
      const configsResponse = await fetch('/api/admin/caching/configurations/');
      const configs = await configsResponse.json();
      
      // Fetch stats for each cache
      const statsPromises = configs.map(async (config: any) => {
        const statsResponse = await fetch(`/api/admin/caching/configurations/${config.id}/stats/`);
        return await statsResponse.json();
      });
      
      const stats = await Promise.all(statsPromises);
      setCacheStats(stats);
      
      // Fetch recent metrics
      const metricsResponse = await fetch(`/api/admin/caching/metrics/?days=${getTimeRangeDays(selectedTimeRange)}`);
      const metricsData = await metricsResponse.json();
      setMetrics(metricsData.results || []);
      
      // Fetch active alerts
      const alertsResponse = await fetch('/api/admin/caching/alerts/?is_resolved=false');
      const alertsData = await alertsResponse.json();
      setAlerts(alertsData.results || []);
      
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTimeRangeDays = (range: string): number => {
    switch (range) {
      case '1h': return 1;
      case '24h': return 1;
      case '7d': return 7;
      case '30d': return 30;
      default: return 1;
    }
  };

  const getOverallHealthScore = (): number => {
    if (cacheStats.length === 0) return 0;
    
    const totalScore = cacheStats.reduce((sum, cache) => {
      let score = 100;
      
      // Hit ratio impact (40%)
      score -= (1 - cache.hit_ratio) * 40;
      
      // Response time impact (30%)
      if (cache.avg_response_time_ms > 100) {
        score -= Math.min(30, (cache.avg_response_time_ms - 100) / 10);
      }
      
      // Memory usage impact (20%)
      if (cache.memory_usage_percent > 80) {
        score -= (cache.memory_usage_percent - 80) / 5;
      }
      
      // Error count impact (10%)
      if (cache.error_count > 0) {
        score -= Math.min(10, cache.error_count);
      }
      
      return sum + Math.max(0, score);
    }, 0);
    
    return Math.round(totalScore / cacheStats.length);
  };

  const getHealthScoreColor = (score: number): string => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getHealthScoreLabel = (score: number): string => {
    if (score >= 90) return 'Excellent';
    if (score >= 75) return 'Good';
    if (score >= 60) return 'Fair';
    if (score >= 40) return 'Poor';
    return 'Critical';
  };

  const getSeverityBadgeVariant = (severity: string) => {
    switch (severity) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'outline';
    }
  };

  const formatMetricsForChart = (metrics: CacheMetrics[]) => {
    return metrics.map(metric => ({
      timestamp: new Date(metric.timestamp).toLocaleTimeString(),
      hit_ratio: metric.hit_ratio * 100,
      response_time: metric.avg_response_time_ms,
      memory_usage: metric.memory_usage_percent,
      operations: metric.hit_count + metric.miss_count
    }));
  };

  const getCacheTypeDistribution = () => {
    const distribution = cacheStats.reduce((acc, cache) => {
      acc[cache.cache_type] = (acc[cache.cache_type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    return Object.entries(distribution).map(([type, count]) => ({
      name: type,
      value: count
    }));
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const overallHealth = getOverallHealthScore();
  const chartData = formatMetricsForChart(metrics);
  const cacheTypeData = getCacheTypeDistribution();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Cache Management</h1>
          <p className="text-gray-600">Monitor and optimize cache performance</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchDashboardData}>
            <Activity className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button>
            <Settings className="h-4 w-4 mr-2" />
            Configure
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Health</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getHealthScoreColor(overallHealth)}`}>
              {overallHealth}%
            </div>
            <p className="text-xs text-muted-foreground">
              {getHealthScoreLabel(overallHealth)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Caches</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {cacheStats.filter(c => c.is_active).length}
            </div>
            <p className="text-xs text-muted-foreground">
              of {cacheStats.length} total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Hit Ratio</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {cacheStats.length > 0 
                ? `${Math.round(cacheStats.reduce((sum, c) => sum + c.hit_ratio, 0) / cacheStats.length * 100)}%`
                : '0%'
              }
            </div>
            <p className="text-xs text-muted-foreground">
              Cache efficiency
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {alerts.length}
            </div>
            <p className="text-xs text-muted-foreground">
              Require attention
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="caches">Cache Status</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Hit Ratio Trend</CardTitle>
                <CardDescription>Cache hit ratio over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Line 
                      type="monotone" 
                      dataKey="hit_ratio" 
                      stroke="#8884d8" 
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Response Time</CardTitle>
                <CardDescription>Average response time in milliseconds</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Area 
                      type="monotone" 
                      dataKey="response_time" 
                      stroke="#82ca9d" 
                      fill="#82ca9d"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Memory Usage</CardTitle>
                <CardDescription>Cache memory utilization</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="memory_usage" fill="#ffc658" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cache Types</CardTitle>
                <CardDescription>Distribution of cache types</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={cacheTypeData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {cacheTypeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="caches" className="space-y-4">
          <div className="grid gap-4">
            {cacheStats.map((cache, index) => (
              <Card key={index}>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle className="flex items-center gap-2">
                      <Database className="h-5 w-5" />
                      {cache.cache_name}
                    </CardTitle>
                    <div className="flex gap-2">
                      <Badge variant={cache.is_active ? "default" : "secondary"}>
                        {cache.is_active ? "Active" : "Inactive"}
                      </Badge>
                      <Badge variant="outline">{cache.cache_type}</Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="flex items-center gap-2">
                      <Zap className="h-4 w-4 text-blue-500" />
                      <div>
                        <p className="text-sm text-gray-600">Hit Ratio</p>
                        <p className="font-semibold">{(cache.hit_ratio * 100).toFixed(1)}%</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-green-500" />
                      <div>
                        <p className="text-sm text-gray-600">Response Time</p>
                        <p className="font-semibold">{cache.avg_response_time_ms.toFixed(1)}ms</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <HardDrive className="h-4 w-4 text-orange-500" />
                      <div>
                        <p className="text-sm text-gray-600">Memory Usage</p>
                        <p className="font-semibold">{cache.memory_usage_percent.toFixed(1)}%</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                      <div>
                        <p className="text-sm text-gray-600">Errors</p>
                        <p className="font-semibold">{cache.error_count}</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <div className="space-y-4">
            {alerts.length === 0 ? (
              <Card>
                <CardContent className="flex items-center justify-center py-8">
                  <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-green-600">All Clear!</h3>
                    <p className="text-gray-600">No active alerts at this time.</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              alerts.map((alert) => (
                <Card key={alert.id} className="border-l-4" style={{ borderLeftColor: alert.severity_color }}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          <AlertTriangle className="h-5 w-5" style={{ color: alert.severity_color }} />
                          {alert.cache_name}
                        </CardTitle>
                        <CardDescription>{alert.alert_type.replace('_', ' ')}</CardDescription>
                      </div>
                      <Badge variant={getSeverityBadgeVariant(alert.severity)}>
                        {alert.severity}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm mb-4">{alert.message}</p>
                    <div className="flex justify-between items-center text-xs text-gray-500">
                      <span>Created: {new Date(alert.created_at).toLocaleString()}</span>
                      <Button size="sm" variant="outline">
                        Resolve
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Operations Volume</CardTitle>
                <CardDescription>Cache operations over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Area 
                      type="monotone" 
                      dataKey="operations" 
                      stroke="#8884d8" 
                      fill="#8884d8"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Grades</CardTitle>
                <CardDescription>Cache performance distribution</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {['A', 'B', 'C', 'D', 'F'].map(grade => {
                    const count = metrics.filter(m => m.performance_grade === grade).length;
                    const percentage = metrics.length > 0 ? (count / metrics.length) * 100 : 0;
                    
                    return (
                      <div key={grade} className="flex items-center gap-4">
                        <div className="w-8 text-center font-bold">{grade}</div>
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <div className="w-12 text-sm text-gray-600">{count}</div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CachingDashboard;