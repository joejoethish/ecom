'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
// import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { DatePickerWithRange } from '@/components/ui/date-range-picker';
import {
    TrendingUp,
    TrendingDown,
    DollarSign,
    ShoppingCart,
    // Users,
    Target,
    AlertTriangle,
    BarChart3,
    // PieChart,
    LineChart,
    // Calendar,
    Download,
    RefreshCw
} from 'lucide-react';
// import { format } from 'date-fns';
// import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart as RechartsPieChart, Cell } from 'recharts';
// import { format, subDays } from 'date-fns';

interface SalesDashboardData {
    total_revenue: number;
    total_orders: number;
    average_order_value: number;
    conversion_rate: number;
    revenue_growth: number;
    order_growth: number;
    top_products: Array<{
        product_name: string;
        total_revenue: number;
        total_units: number;
    }>;
    recent_anomalies: Array<{
        id: number;
        metric_type: string;
        severity: string;
        deviation_percentage: number;
        date: string;
    }>;
    active_goals: Array<{
        id: number;
        name: string;
        progress_percentage: number;
        target_value: number;
        current_value: number;
    }>;
}

interface RevenueAnalysisData {
    period: string;
    revenue: number;
    orders: number;
    customers: number;
    average_order_value: number;
    gross_margin: number;
    net_profit: number;
    profit_margin_percentage: number;
}

interface ForecastData {
    forecast_date: string;
    predicted_revenue: number;
    predicted_orders: number;
    confidence_interval_lower: number;
    confidence_interval_upper: number;
    model_accuracy: number;
}

// const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export default function SalesAnalyticsDashboard() {
    const [dashboardData, setDashboardData] = useState<SalesDashboardData | null>(null);
    const [revenueAnalysis, setRevenueAnalysis] = useState<any[]>([]);
    const [forecastData, setForecastData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [dateRange, setDateRange] = useState({
        from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
        to: new Date()
    });
    const [refreshing, setRefreshing] = useState(false);

    const fetchDashboardData = useCallback(async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams({
                date_from: dateRange.from.toISOString(),
                date_to: dateRange.to.toISOString()
            });

            // Fetch dashboard data
            const dashboardResponse = await fetch(`/api/analytics/sales-analytics/sales_dashboard/?${params}`);
            if (dashboardResponse.ok) {
                const dashboardResult = await dashboardResponse.json();
                setDashboardData(dashboardResult);
            }

            // Fetch revenue analysis
            const revenueParams = new URLSearchParams({
                date_from: dateRange.from.toISOString(),
                date_to: dateRange.to.toISOString(),
                group_by: 'day'
            });
            const revenueResponse = await fetch(`/api/analytics/sales-analytics/revenue_analysis/?${revenueParams}`);
            if (revenueResponse.ok) {
                const revenueResult = await revenueResponse.json();
                setRevenueAnalysis(revenueResult);
            }

            // Fetch forecast data
            const forecastResponse = await fetch('/api/analytics/sales-analytics/sales_forecast/?type=monthly&periods=6');
            if (forecastResponse.ok) {
                const forecastResult = await forecastResponse.json();
                setForecastData(forecastResult);
            }

        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        } finally {
            setLoading(false);
        }
    }, [dateRange]);

    useEffect(() => {
        fetchDashboardData();
    }, [fetchDashboardData]);

    const handleRefresh = async () => {
        setRefreshing(true);
        await fetchDashboardData();
        setRefreshing(false);
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(value);
    };

    const formatNumber = (value: number) => {
        return new Intl.NumberFormat('en-US').format(value);
    };

    const getGrowthIcon = (growth: number) => {
        return growth >= 0 ? (
            <TrendingUp className="h-4 w-4 text-green-500" />
        ) : (
            <TrendingDown className="h-4 w-4 text-red-500" />
        );
    };

    const getGrowthColor = (growth: number) => {
        return growth >= 0 ? 'text-green-500' : 'text-red-500';
    };

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'high':
                return 'destructive';
            case 'medium':
                return 'default';
            case 'low':
                return 'secondary';
            default:
                return 'outline';
        }
    };

    if (loading && !dashboardData) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Sales Analytics Dashboard</h1>
                    <p className="text-muted-foreground">
                        Comprehensive sales insights and performance tracking
                    </p>
                </div>
                <div className="flex items-center space-x-4">
                    <DatePickerWithRange
                        date={dateRange}
                        onDateChange={setDateRange}
                    />
                    <Button
                        onClick={handleRefresh}
                        disabled={refreshing}
                        variant="outline"
                        size="sm"
                    >
                        <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                    <Button variant="outline" size="sm">
                        <Download className="h-4 w-4 mr-2" />
                        Export
                    </Button>
                </div>
            </div>

            {/* Key Metrics Cards */}
            {dashboardData && (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
                            <DollarSign className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{formatCurrency(dashboardData.total_revenue)}</div>
                            <div className="flex items-center text-xs text-muted-foreground">
                                {getGrowthIcon(dashboardData.revenue_growth)}
                                <span className={`ml-1 ${getGrowthColor(dashboardData.revenue_growth)}`}>
                                    {Math.abs(dashboardData.revenue_growth)}% from last period
                                </span>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total Orders</CardTitle>
                            <ShoppingCart className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{formatNumber(dashboardData.total_orders)}</div>
                            <div className="flex items-center text-xs text-muted-foreground">
                                {getGrowthIcon(dashboardData.order_growth)}
                                <span className={`ml-1 ${getGrowthColor(dashboardData.order_growth)}`}>
                                    {Math.abs(dashboardData.order_growth)}% from last period
                                </span>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Average Order Value</CardTitle>
                            <BarChart3 className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{formatCurrency(dashboardData.average_order_value)}</div>
                            <p className="text-xs text-muted-foreground">
                                Conversion rate: {dashboardData.conversion_rate}%
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Active Goals</CardTitle>
                            <Target className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{dashboardData.active_goals.length}</div>
                            <p className="text-xs text-muted-foreground">
                                {dashboardData.active_goals.filter(g => g.progress_percentage >= 100).length} achieved
                            </p>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Main Content Tabs */}
            <Tabs defaultValue="overview" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="overview">Overview</TabsTrigger>
                    <TabsTrigger value="revenue">Revenue Analysis</TabsTrigger>
                    <TabsTrigger value="forecasting">Forecasting</TabsTrigger>
                    <TabsTrigger value="performance">Performance</TabsTrigger>
                    <TabsTrigger value="goals">Goals & Targets</TabsTrigger>
                    <TabsTrigger value="anomalies">Anomalies</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                        {/* Revenue Trend Chart */}
                        <Card className="col-span-2">
                            <CardHeader>
                                <CardTitle>Revenue Trend</CardTitle>
                                <CardDescription>Daily revenue and order trends</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="w-full h-[300px] bg-gray-100 rounded-lg flex items-center justify-center">
                                    <div className="text-center">
                                        <BarChart3 className="h-12 w-12 mx-auto mb-2 text-gray-400" />
                                        <p className="text-gray-500">Revenue Trend Chart</p>
                                        <p className="text-sm text-gray-400">Chart visualization would appear here</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Top Products */}
                        {dashboardData && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Top Performing Products</CardTitle>
                                    <CardDescription>By revenue in selected period</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-4">
                                        {dashboardData.top_products.slice(0, 5).map((product, index) => (
                                            <div key={index} className="flex items-center justify-between">
                                                <div className="flex items-center space-x-2">
                                                    <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                                                    <span className="text-sm font-medium truncate">
                                                        {product.product_name}
                                                    </span>
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-sm font-bold">
                                                        {formatCurrency(product.total_revenue)}
                                                    </div>
                                                    <div className="text-xs text-muted-foreground">
                                                        {formatNumber(product.total_units)} units
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        {/* Active Goals Progress */}
                        {dashboardData && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Goal Progress</CardTitle>
                                    <CardDescription>Current sales goals status</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-4">
                                        {dashboardData.active_goals.slice(0, 5).map((goal) => (
                                            <div key={goal.id} className="space-y-2">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-sm font-medium">{goal.name}</span>
                                                    <span className="text-sm text-muted-foreground">
                                                        {goal.progress_percentage.toFixed(1)}%
                                                    </span>
                                                </div>
                                                <div className="w-full bg-gray-200 rounded-full h-2">
                                                    <div
                                                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                                        style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
                                                    ></div>
                                                </div>
                                                <div className="flex justify-between text-xs text-muted-foreground">
                                                    <span>{formatCurrency(goal.current_value)}</span>
                                                    <span>{formatCurrency(goal.target_value)}</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="revenue" className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                        {/* Profit Margin Analysis */}
                        <Card className="col-span-2">
                            <CardHeader>
                                <CardTitle>Profit Margin Analysis</CardTitle>
                                <CardDescription>Revenue, costs, and profit margins over time</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="w-full h-[300px] bg-gray-100 rounded-lg flex items-center justify-center">
                                    <div className="text-center">
                                        <LineChart className="h-12 w-12 mx-auto mb-2 text-gray-400" />
                                        <p className="text-gray-500">Profit Margin Analysis Chart</p>
                                        <p className="text-sm text-gray-400">Chart visualization would appear here</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                <TabsContent value="forecasting" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Sales Forecast</CardTitle>
                            <CardDescription>ML-powered sales predictions with confidence intervals</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="w-full h-[400px] bg-gray-100 rounded-lg flex items-center justify-center">
                                <div className="text-center">
                                    <TrendingUp className="h-12 w-12 mx-auto mb-2 text-gray-400" />
                                    <p className="text-gray-500">Sales Forecast Chart</p>
                                    <p className="text-sm text-gray-400">ML-powered forecast visualization would appear here</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="performance" className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle>Performance Metrics</CardTitle>
                                <CardDescription>Key performance indicators</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    <div className="flex justify-between items-center">
                                        <span className="text-sm font-medium">Conversion Rate</span>
                                        <span className="text-sm font-bold">
                                            {dashboardData?.conversion_rate.toFixed(2)}%
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-sm font-medium">Average Order Value</span>
                                        <span className="text-sm font-bold">
                                            {formatCurrency(dashboardData?.average_order_value || 0)}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-sm font-medium">Revenue Growth</span>
                                        <span className={`text-sm font-bold ${getGrowthColor(dashboardData?.revenue_growth || 0)}`}>
                                            {dashboardData?.revenue_growth.toFixed(2)}%
                                        </span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle>Channel Performance</CardTitle>
                                <CardDescription>Revenue by sales channel</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="text-center text-muted-foreground">
                                    Channel analysis data will be displayed here
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                <TabsContent value="goals" className="space-y-4">
                    {dashboardData && (
                        <div className="grid gap-4">
                            {dashboardData.active_goals.map((goal) => (
                                <Card key={goal.id}>
                                    <CardHeader>
                                        <div className="flex items-center justify-between">
                                            <CardTitle className="text-lg">{goal.name}</CardTitle>
                                            <Badge variant={goal.progress_percentage >= 100 ? "default" : "secondary"}>
                                                {goal.progress_percentage >= 100 ? "Achieved" : "In Progress"}
                                            </Badge>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-4">
                                            <div className="flex justify-between text-sm">
                                                <span>Progress: {goal.progress_percentage.toFixed(1)}%</span>
                                                <span>
                                                    {formatCurrency(goal.current_value)} / {formatCurrency(goal.target_value)}
                                                </span>
                                            </div>
                                            <div className="w-full bg-gray-200 rounded-full h-3">
                                                <div
                                                    className={`h-3 rounded-full transition-all duration-300 ${goal.progress_percentage >= 100 ? 'bg-green-600' : 'bg-blue-600'
                                                        }`}
                                                    style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
                                                ></div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}
                </TabsContent>

                <TabsContent value="anomalies" className="space-y-4">
                    {dashboardData && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Recent Anomalies</CardTitle>
                                <CardDescription>Detected sales anomalies and alerts</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {dashboardData.recent_anomalies.length > 0 ? (
                                    <div className="space-y-4">
                                        {dashboardData.recent_anomalies.map((anomaly) => (
                                            <div key={anomaly.id} className="flex items-center justify-between p-4 border rounded-lg">
                                                <div className="flex items-center space-x-3">
                                                    <AlertTriangle className="h-5 w-5 text-orange-500" />
                                                    <div>
                                                        <div className="font-medium">
                                                            {anomaly.metric_type.charAt(0).toUpperCase() + anomaly.metric_type.slice(1)} Anomaly
                                                        </div>
                                                        <div className="text-sm text-muted-foreground">
                                                            {new Date(anomaly.date).toLocaleDateString('en-US', {
                                                                month: 'short',
                                                                day: '2-digit',
                                                                year: 'numeric'
                                                            })}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center space-x-2">
                                                    <Badge variant={getSeverityColor(anomaly.severity)}>
                                                        {anomaly.severity}
                                                    </Badge>
                                                    <span className="text-sm font-medium">
                                                        {anomaly.deviation_percentage.toFixed(1)}% deviation
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center text-muted-foreground py-8">
                                        No anomalies detected in the selected period
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    )}
                </TabsContent>
            </Tabs>
        </div>
    );
}