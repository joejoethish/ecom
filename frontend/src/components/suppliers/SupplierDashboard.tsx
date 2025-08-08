import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
// Note: recharts would need to be installed for charts to work
// For now, we'll comment out the recharts import and use placeholder charts
// import {
//     BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
//     PieChart, Pie, Cell, LineChart, Line
// } from 'recharts';
import {
    Users, TrendingUp, AlertTriangle, CheckCircle,
    DollarSign, Package, Clock, Award
} from 'lucide-react';

interface SupplierAnalytics {
    total_suppliers: number;
    active_suppliers: number;
    pending_suppliers: number;
    high_risk_suppliers: number;
    average_performance_score: number;
    average_quality_score: number;
    average_delivery_score: number;
    total_purchase_orders: number;
    total_purchase_value: number;
    average_order_value: number;
    minority_owned_count: number;
    women_owned_count: number;
    veteran_owned_count: number;
    small_business_count: number;
}

interface PerformanceData {
    supplier_name: string;
    performance_score: number;
    quality_score: number;
    delivery_score: number;
    total_orders: number;
    total_value: number;
}

interface RiskData {
    supplier_name: string;
    risk_level: string;
    financial_stability_score: number;
    compliance_score: number;
    quality_issues: number;
    delivery_delays: number;
}

const SupplierDashboard: React.FC = () => {
    const [analytics, setAnalytics] = useState<SupplierAnalytics | null>(null);
    const [performanceData, setPerformanceData] = useState<PerformanceData[]>([]);
    const [riskData, setRiskData] = useState<RiskData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchAnalytics();
        fetchPerformanceData();
        fetchRiskData();
    }, []);

    const fetchAnalytics = async () => {
        try {
            const response = await fetch('/api/suppliers/suppliers/analytics/');
            const data = await response.json();
            setAnalytics(data);
        } catch (error) {
            console.error('Error fetching analytics:', error);
        }
    };

    const fetchPerformanceData = async () => {
        try {
            const response = await fetch('/api/suppliers/suppliers/performance_report/');
            const data = await response.json();
            setPerformanceData(data.slice(0, 10)); // Top 10 suppliers
        } catch (error) {
            console.error('Error fetching performance data:', error);
        }
    };

    const fetchRiskData = async () => {
        try {
            const response = await fetch('/api/suppliers/suppliers/risk_assessment/');
            const data = await response.json();
            setRiskData(data.filter((item: RiskData) => item.risk_level === 'high'));
        } catch (error) {
            console.error('Error fetching risk data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading || !analytics) {
        return <div className="flex justify-center items-center h-64">Loading...</div>;
    }

    const diversityData = [
        { name: 'Minority Owned', value: analytics.minority_owned_count, color: '#8884d8' },
        { name: 'Women Owned', value: analytics.women_owned_count, color: '#82ca9d' },
        { name: 'Veteran Owned', value: analytics.veteran_owned_count, color: '#ffc658' },
        { name: 'Small Business', value: analytics.small_business_count, color: '#ff7300' },
    ];

    const performanceChartData = performanceData.map(item => ({
        name: item.supplier_name.substring(0, 15) + '...',
        performance: item.performance_score,
        quality: item.quality_score,
        delivery: item.delivery_score,
    }));

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold">Supplier Management Dashboard</h1>
                <div className="flex space-x-2">
                    <Button variant="outline">Export Report</Button>
                    <Button>Add Supplier</Button>
                </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Suppliers</CardTitle>
                        <Users className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{analytics.total_suppliers}</div>
                        <p className="text-xs text-muted-foreground">
                            {analytics.active_suppliers} active
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Purchase Value</CardTitle>
                        <DollarSign className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            ${analytics.total_purchase_value.toLocaleString()}
                        </div>
                        <p className="text-xs text-muted-foreground">
                            {analytics.total_purchase_orders} orders
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg Performance Score</CardTitle>
                        <Award className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {analytics.average_performance_score.toFixed(1)}/5.0
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Quality: {analytics.average_quality_score.toFixed(1)}/5.0
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">High Risk Suppliers</CardTitle>
                        <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-red-600">
                            {analytics.high_risk_suppliers}
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Require immediate attention
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Charts and Analytics */}
            <Tabs defaultValue="performance" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="performance">Performance</TabsTrigger>
                    <TabsTrigger value="diversity">Diversity</TabsTrigger>
                    <TabsTrigger value="risk">Risk Assessment</TabsTrigger>
                </TabsList>

                <TabsContent value="performance" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Top Supplier Performance</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="w-full h-96 bg-gray-100 rounded-lg flex items-center justify-center">
                                <div className="text-center">
                                    <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                                    <p className="text-gray-600">Performance Chart</p>
                                    <p className="text-sm text-gray-500">Install recharts to display interactive charts</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="diversity" className="space-y-4">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Supplier Diversity Breakdown</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="w-full h-72 bg-gray-100 rounded-lg flex items-center justify-center">
                                    <div className="text-center">
                                        <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                                        <p className="text-gray-600">Diversity Chart</p>
                                        <p className="text-sm text-gray-500">Install recharts to display interactive charts</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle>Diversity Metrics</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <span>Minority Owned</span>
                                    <Badge variant="secondary">{analytics.minority_owned_count}</Badge>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span>Women Owned</span>
                                    <Badge variant="secondary">{analytics.women_owned_count}</Badge>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span>Veteran Owned</span>
                                    <Badge variant="secondary">{analytics.veteran_owned_count}</Badge>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span>Small Business</span>
                                    <Badge variant="secondary">{analytics.small_business_count}</Badge>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                <TabsContent value="risk" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>High Risk Suppliers</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {riskData.length === 0 ? (
                                    <div className="text-center py-8 text-muted-foreground">
                                        <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
                                        <p>No high-risk suppliers identified</p>
                                    </div>
                                ) : (
                                    riskData.map((supplier, index) => (
                                        <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                                            <div>
                                                <h4 className="font-semibold">{supplier.supplier_name}</h4>
                                                <div className="flex space-x-4 text-sm text-muted-foreground">
                                                    <span>Financial: {supplier.financial_stability_score}/5</span>
                                                    <span>Compliance: {supplier.compliance_score}/5</span>
                                                    <span>Quality Issues: {supplier.quality_issues}</span>
                                                    <span>Delivery Delays: {supplier.delivery_delays}</span>
                                                </div>
                                            </div>
                                            <Badge variant="destructive">{supplier.risk_level}</Badge>
                                        </div>
                                    ))
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>

            {/* Quick Actions */}
            <Card>
                <CardHeader>
                    <CardTitle>Quick Actions</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <Button variant="outline" className="h-20 flex flex-col items-center justify-center">
                            <Package className="h-6 w-6 mb-2" />
                            Create Purchase Order
                        </Button>
                        <Button variant="outline" className="h-20 flex flex-col items-center justify-center">
                            <Clock className="h-6 w-6 mb-2" />
                            Schedule Audit
                        </Button>
                        <Button variant="outline" className="h-20 flex flex-col items-center justify-center">
                            <TrendingUp className="h-6 w-6 mb-2" />
                            Generate Report
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default SupplierDashboard;