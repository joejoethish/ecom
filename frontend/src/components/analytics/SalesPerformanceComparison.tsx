'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Select } from '@/components/ui/Select';
import { DatePickerWithRange } from '@/components/ui/date-range-picker';
import {
    TrendingUp,
    TrendingDown,
    ArrowUpRight,
    ArrowDownRight,
    Calendar,
    BarChart3,
    PieChart,
    RefreshCw,
    Download
} from 'lucide-react';
// import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
// import { format, subDays, subYears } from 'date-fns';

interface PerformanceData {
    period: string;
    revenue: number;
    orders: number;
    customers: number;
    average_order_value: number;
    gross_margin: number;
    net_profit: number;
    profit_margin_percentage: number;
}

interface ComparisonResult {
    current_period: PerformanceData;
    previous_period: PerformanceData;
    growth_metrics: {
        revenue_growth: number;
        orders_growth: number;
        customers_growth: number;
        average_order_value_growth: number;
        gross_margin_growth: number;
        net_profit_growth: number;
    };
}

interface AttributionData {
    channel: string;
    revenue: number;
    orders: number;
    customers: number;
    conversion_rate: number;
    cost_per_acquisition: number;
    return_on_investment: number;
}

export default function SalesPerformanceComparison() {
    const [comparisonData, setComparisonData] = useState<ComparisonResult | null>(null);
    const [attributionData, setAttributionData] = useState<AttributionData[]>([]);
    const [loading, setLoading] = useState(true);
    const [dateRange, setDateRange] = useState({
        from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
        to: new Date()
    });
    const [compareWith, setCompareWith] = useState('previous_period');
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        fetchComparisonData();
    }, [dateRange, compareWith]);

    const fetchComparisonData = async () => {
        setLoading(true);
        try {
            // Fetch performance comparison
            const comparisonParams = new URLSearchParams({
                current_start: dateRange.from.toISOString(),
                current_end: dateRange.to.toISOString(),
                compare_with: compareWith
            });

            const comparisonResponse = await fetch(`/api/analytics/sales-analytics/sales_performance_comparison/?${comparisonParams}`);
            if (comparisonResponse.ok) {
                const comparisonResult = await comparisonResponse.json();
                setComparisonData(comparisonResult);
            }

            // Fetch attribution analysis
            const attributionParams = new URLSearchParams({
                date_from: dateRange.from.toISOString(),
                date_to: dateRange.to.toISOString()
            });

            const attributionResponse = await fetch(`/api/analytics/sales-analytics/sales_attribution_analysis/?${attributionParams}`);
            if (attributionResponse.ok) {
                const attributionResult = await attributionResponse.json();
                setAttributionData(attributionResult);
            }

        } catch (error) {
            console.error('Error fetching comparison data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleRefresh = async () => {
        setRefreshing(true);
        await fetchComparisonData();
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

    const formatPercentage = (value: number) => {
        return `${value.toFixed(2)}%`;
    };

    const getGrowthIcon = (growth: number) => {
        return growth >= 0 ? (
            <ArrowUpRight className="h-4 w-4 text-green-500" />
        ) : (
            <ArrowDownRight className="h-4 w-4 text-red-500" />
        );
    };

    const getGrowthColor = (growth: number) => {
        return growth >= 0 ? 'text-green-600' : 'text-red-600';
    };

    const getGrowthBadge = (growth: number) => {
        if (growth >= 10) return 'default';
        if (growth >= 0) return 'secondary';
        if (growth >= -10) return 'outline';
        return 'destructive';
    };

    if (loading && !comparisonData) {
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
                    <h2 className="text-2xl font-bold tracking-tight">Sales Performance Comparison</h2>
                    <p className="text-muted-foreground">
                        Period-over-period and year-over-year analysis
                    </p>
                </div>
                <div className="flex items-center space-x-4">
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

            {/* Comparison Configuration */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center">
                        <Calendar className="h-5 w-5 mr-2" />
                        Comparison Settings
                    </CardTitle>
                    <CardDescription>
                        Configure date ranges and comparison periods
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Current Period</label>
                            <DatePickerWithRange
                                date={dateRange}
                                onDateChange={setDateRange}
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Compare With</label>
                            <Select value={compareWith} onChange={setCompareWith}>
                                <option value="previous_period">Previous Period</option>
                                <option value="previous_year">Previous Year</option>
                            </Select>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Key Metrics Comparison */}
            {comparisonData && (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Revenue</CardTitle>
                            <BarChart3 className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">
                                {formatCurrency(comparisonData.current_period.revenue)}
                            </div>
                            <div className="flex items-center text-xs">
                                {getGrowthIcon(comparisonData.growth_metrics.revenue_growth)}
                                <span className={`ml-1 font-medium ${getGrowthColor(comparisonData.growth_metrics.revenue_growth)}`}>
                                    {formatPercentage(Math.abs(comparisonData.growth_metrics.revenue_growth))}
                                </span>
                                <span className="ml-1 text-muted-foreground">vs {compareWith.replace('_', ' ')}</span>
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                                Previous: {formatCurrency(comparisonData.previous_period.revenue)}
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Orders</CardTitle>
                            <BarChart3 className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">
                                {formatNumber(comparisonData.current_period.orders)}
                            </div>
                            <div className="flex items-center text-xs">
                                {getGrowthIcon(comparisonData.growth_metrics.orders_growth)}
                                <span className={`ml-1 font-medium ${getGrowthColor(comparisonData.growth_metrics.orders_growth)}`}>
                                    {formatPercentage(Math.abs(comparisonData.growth_metrics.orders_growth))}
                                </span>
                                <span className="ml-1 text-muted-foreground">vs {compareWith.replace('_', ' ')}</span>
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                                Previous: {formatNumber(comparisonData.previous_period.orders)}
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Average Order Value</CardTitle>
                            <BarChart3 className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">
                                {formatCurrency(comparisonData.current_period.average_order_value)}
                            </div>
                            <div className="flex items-center text-xs">
                                {getGrowthIcon(comparisonData.growth_metrics.average_order_value_growth)}
                                <span className={`ml-1 font-medium ${getGrowthColor(comparisonData.growth_metrics.average_order_value_growth)}`}>
                                    {formatPercentage(Math.abs(comparisonData.growth_metrics.average_order_value_growth))}
                                </span>
                                <span className="ml-1 text-muted-foreground">vs {compareWith.replace('_', ' ')}</span>
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                                Previous: {formatCurrency(comparisonData.previous_period.average_order_value)}
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Net Profit</CardTitle>
                            <BarChart3 className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">
                                {formatCurrency(comparisonData.current_period.net_profit)}
                            </div>
                            <div className="flex items-center text-xs">
                                {getGrowthIcon(comparisonData.growth_metrics.net_profit_growth)}
                                <span className={`ml-1 font-medium ${getGrowthColor(comparisonData.growth_metrics.net_profit_growth)}`}>
                                    {formatPercentage(Math.abs(comparisonData.growth_metrics.net_profit_growth))}
                                </span>
                                <span className="ml-1 text-muted-foreground">vs {compareWith.replace('_', ' ')}</span>
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                                Previous: {formatCurrency(comparisonData.previous_period.net_profit)}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Growth Metrics Chart */}
            {comparisonData && (
                <Card>
                    <CardHeader>
                        <CardTitle>Growth Metrics Comparison</CardTitle>
                        <CardDescription>
                            Period-over-period growth across key metrics
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="w-full h-[300px] bg-gray-100 rounded-lg flex items-center justify-center">
                            <div className="text-center">
                                <BarChart3 className="h-12 w-12 mx-auto mb-2 text-gray-400" />
                                <p className="text-gray-500">Growth Metrics Chart</p>
                                <p className="text-sm text-gray-400">Period-over-period growth visualization</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            <div className="grid gap-4 md:grid-cols-2">
                {/* Detailed Comparison Table */}
                {comparisonData && (
                    <Card>
                        <CardHeader>
                            <CardTitle>Detailed Comparison</CardTitle>
                            <CardDescription>
                                Side-by-side metric comparison
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="grid grid-cols-3 gap-4 text-sm font-medium border-b pb-2">
                                    <div>Metric</div>
                                    <div>Current</div>
                                    <div>Previous</div>
                                </div>

                                <div className="grid grid-cols-3 gap-4 text-sm">
                                    <div>Revenue</div>
                                    <div className="font-medium">{formatCurrency(comparisonData.current_period.revenue)}</div>
                                    <div className="text-muted-foreground">{formatCurrency(comparisonData.previous_period.revenue)}</div>
                                </div>

                                <div className="grid grid-cols-3 gap-4 text-sm">
                                    <div>Orders</div>
                                    <div className="font-medium">{formatNumber(comparisonData.current_period.orders)}</div>
                                    <div className="text-muted-foreground">{formatNumber(comparisonData.previous_period.orders)}</div>
                                </div>

                                <div className="grid grid-cols-3 gap-4 text-sm">
                                    <div>Customers</div>
                                    <div className="font-medium">{formatNumber(comparisonData.current_period.customers)}</div>
                                    <div className="text-muted-foreground">{formatNumber(comparisonData.previous_period.customers)}</div>
                                </div>

                                <div className="grid grid-cols-3 gap-4 text-sm">
                                    <div>AOV</div>
                                    <div className="font-medium">{formatCurrency(comparisonData.current_period.average_order_value)}</div>
                                    <div className="text-muted-foreground">{formatCurrency(comparisonData.previous_period.average_order_value)}</div>
                                </div>

                                <div className="grid grid-cols-3 gap-4 text-sm">
                                    <div>Gross Margin</div>
                                    <div className="font-medium">{formatCurrency(comparisonData.current_period.gross_margin)}</div>
                                    <div className="text-muted-foreground">{formatCurrency(comparisonData.previous_period.gross_margin)}</div>
                                </div>

                                <div className="grid grid-cols-3 gap-4 text-sm">
                                    <div>Net Profit</div>
                                    <div className="font-medium">{formatCurrency(comparisonData.current_period.net_profit)}</div>
                                    <div className="text-muted-foreground">{formatCurrency(comparisonData.previous_period.net_profit)}</div>
                                </div>

                                <div className="grid grid-cols-3 gap-4 text-sm">
                                    <div>Profit Margin</div>
                                    <div className="font-medium">{formatPercentage(comparisonData.current_period.profit_margin_percentage)}</div>
                                    <div className="text-muted-foreground">{formatPercentage(comparisonData.previous_period.profit_margin_percentage)}</div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Growth Summary */}
                {comparisonData && (
                    <Card>
                        <CardHeader>
                            <CardTitle>Growth Summary</CardTitle>
                            <CardDescription>
                                Key growth indicators and trends
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {Object.entries(comparisonData.growth_metrics).map(([key, value]) => (
                                    <div key={key} className="flex items-center justify-between">
                                        <span className="text-sm font-medium capitalize">
                                            {key.replace('_growth', '').replace('_', ' ')}
                                        </span>
                                        <div className="flex items-center space-x-2">
                                            <Badge variant={getGrowthBadge(value)}>
                                                {getGrowthIcon(value)}
                                                <span className="ml-1">{formatPercentage(Math.abs(value))}</span>
                                            </Badge>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                                <h4 className="font-medium mb-2">Key Insights</h4>
                                <div className="space-y-2 text-sm text-muted-foreground">
                                    {comparisonData.growth_metrics.revenue_growth > 0 ? (
                                        <div className="flex items-center">
                                            <TrendingUp className="h-4 w-4 text-green-500 mr-2" />
                                            Revenue is growing positively
                                        </div>
                                    ) : (
                                        <div className="flex items-center">
                                            <TrendingDown className="h-4 w-4 text-red-500 mr-2" />
                                            Revenue needs attention
                                        </div>
                                    )}

                                    {comparisonData.growth_metrics.average_order_value_growth > 0 ? (
                                        <div className="flex items-center">
                                            <TrendingUp className="h-4 w-4 text-green-500 mr-2" />
                                            AOV is improving
                                        </div>
                                    ) : (
                                        <div className="flex items-center">
                                            <TrendingDown className="h-4 w-4 text-red-500 mr-2" />
                                            Focus on increasing AOV
                                        </div>
                                    )}

                                    {comparisonData.growth_metrics.customers_growth > 0 ? (
                                        <div className="flex items-center">
                                            <TrendingUp className="h-4 w-4 text-green-500 mr-2" />
                                            Customer acquisition is strong
                                        </div>
                                    ) : (
                                        <div className="flex items-center">
                                            <TrendingDown className="h-4 w-4 text-red-500 mr-2" />
                                            Improve customer acquisition
                                        </div>
                                    )}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>

            {/* Channel Attribution Analysis */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center">
                        <PieChart className="h-5 w-5 mr-2" />
                        Sales Attribution Analysis
                    </CardTitle>
                    <CardDescription>
                        Revenue attribution across marketing channels
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {attributionData.map((channel, index) => (
                            <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                                <div className="flex items-center space-x-3">
                                    <div
                                        className="w-4 h-4 rounded-full"
                                        style={{ backgroundColor: `hsl(${index * 45}, 70%, 50%)` }}
                                    ></div>
                                    <div>
                                        <div className="font-medium">{channel.channel}</div>
                                        <div className="text-sm text-muted-foreground">
                                            {formatNumber(channel.orders)} orders • {formatNumber(channel.customers)} customers
                                        </div>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="font-bold">{formatCurrency(channel.revenue)}</div>
                                    <div className="text-sm text-muted-foreground">
                                        {formatPercentage(channel.conversion_rate)} conversion
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                        ROI: {formatPercentage(channel.return_on_investment)}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}