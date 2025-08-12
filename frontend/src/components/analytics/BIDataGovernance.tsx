'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';
import {
    Shield, Database, CheckCircle, AlertTriangle, TrendingUp,
    Users, FileText, Search, Filter, RefreshCw, Eye, Settings,
    GitBranch, Activity, Lock, Unlock, Star, Clock
} from 'lucide-react';

interface BIDataGovernanceProps {
    dataSourceId?: string;
}

interface DataQualityAssessment {
    data_source_id: string;
    data_source_name: string;
    overall_score: number;
    quality_metrics: {
        completeness: number;
        accuracy: number;
        consistency: number;
        timeliness: number;
        validity: number;
        uniqueness: number;
    };
    issues: string[];
    recommendations: string[];
    assessed_at: string;
}

interface DataLineage {
    source_id: string;
    source_name: string;
    upstream_sources: Array<{
        name: string;
        type: string;
        last_updated: string;
    }>;
    transformations: Array<{
        step: number;
        operation: string;
        description: string;
    }>;
    downstream_consumers: Array<{
        name: string;
        type: string;
    }>;
    impact_analysis: {
        affected_dashboards: number;
        affected_reports: number;
        affected_models: number;
    };
}

interface GovernanceDashboard {
    data_sources_count: number;
    data_quality_average: number;
    compliance_score: number;
    active_policies: number;
    recent_quality_issues: Array<{
        source: string;
        issue: string;
        severity: string;
    }>;
    data_stewards: number;
    cataloged_assets: number;
    last_audit: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export default function BIDataGovernance({ dataSourceId }: BIDataGovernanceProps) {
    const [governanceDashboard, setGovernanceDashboard] = useState<GovernanceDashboard | null>(null);
    const [dataQuality, setDataQuality] = useState<DataQualityAssessment | null>(null);
    const [dataLineage, setDataLineage] = useState<DataLineage | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedTab, setSelectedTab] = useState('overview');
    const [assessingQuality, setAssessingQuality] = useState(false);
    const [creatingLineage, setCreatingLineage] = useState(false);

    const fetchGovernanceDashboard = useCallback(async () => {
        try {
            const response = await fetch('/api/analytics/bi/governance/governance_dashboard/', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) throw new Error('Failed to fetch governance dashboard');

            const data = await response.json();
            setGovernanceDashboard(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch governance dashboard');
        }
    }, []);

    const assessDataQuality = async (sourceId: string) => {
        try {
            setAssessingQuality(true);

            const response = await fetch('/api/analytics/bi/governance/assess_data_quality/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ data_source_id: sourceId })
            });

            if (!response.ok) throw new Error('Failed to assess data quality');

            const assessment = await response.json();
            setDataQuality(assessment);
            setSelectedTab('quality');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to assess data quality');
        } finally {
            setAssessingQuality(false);
        }
    };

    const createDataLineage = async (sourceId: string) => {
        try {
            setCreatingLineage(true);

            const response = await fetch('/api/analytics/bi/governance/create_data_lineage/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ data_source_id: sourceId })
            });

            if (!response.ok) throw new Error('Failed to create data lineage');

            const lineage = await response.json();
            setDataLineage(lineage);
            setSelectedTab('lineage');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create data lineage');
        } finally {
            setCreatingLineage(false);
        }
    };

    useEffect(() => {
        const initializeData = async () => {
            setLoading(true);
            await fetchGovernanceDashboard();
            setLoading(false);
        };

        initializeData();
    }, [fetchGovernanceDashboard]);

    const renderOverview = () => {
        if (!governanceDashboard) return null;

        const qualityData = [
            { name: 'Excellent', value: 45, color: '#00C49F' },
            { name: 'Good', value: 30, color: '#0088FE' },
            { name: 'Fair', value: 20, color: '#FFBB28' },
            { name: 'Poor', value: 5, color: '#FF8042' }
        ];

        return (
            <div className="space-y-6">
                {/* Key Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Data Sources</p>
                                    <p className="text-3xl font-bold">{governanceDashboard.data_sources_count}</p>
                                </div>
                                <Database className="w-8 h-8 text-blue-500" />
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Data Quality</p>
                                    <p className="text-3xl font-bold">{governanceDashboard.data_quality_average}%</p>
                                </div>
                                <CheckCircle className="w-8 h-8 text-green-500" />
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Compliance Score</p>
                                    <p className="text-3xl font-bold">{governanceDashboard.compliance_score}%</p>
                                </div>
                                <Shield className="w-8 h-8 text-purple-500" />
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Data Stewards</p>
                                    <p className="text-3xl font-bold">{governanceDashboard.data_stewards}</p>
                                </div>
                                <Users className="w-8 h-8 text-orange-500" />
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Data Quality Distribution */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Data Quality Distribution</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={qualityData}
                                            cx="50%"
                                            cy="50%"
                                            labelLine={false}
                                            label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                                            outerRadius={80}
                                            fill="#8884d8"
                                            dataKey="value"
                                        >
                                            {qualityData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Recent Quality Issues</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {governanceDashboard.recent_quality_issues.map((issue, index) => (
                                    <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                                        <AlertTriangle className={`w-5 h-5 mt-0.5 ${issue.severity === 'high' ? 'text-red-500' :
                                                issue.severity === 'medium' ? 'text-yellow-500' : 'text-blue-500'
                                            }`} />
                                        <div className="flex-1">
                                            <p className="font-medium">{issue.source}</p>
                                            <p className="text-sm text-gray-600">{issue.issue}</p>
                                            <Badge
                                                className={`mt-1 ${issue.severity === 'high' ? 'bg-red-100 text-red-800' :
                                                        issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                                            'bg-blue-100 text-blue-800'
                                                    }`}
                                            >
                                                {issue.severity.toUpperCase()}
                                            </Badge>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Governance Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center space-x-3">
                                <FileText className="w-8 h-8 text-blue-500" />
                                <div>
                                    <p className="text-sm text-gray-600">Active Policies</p>
                                    <p className="text-2xl font-bold">{governanceDashboard.active_policies}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center space-x-3">
                                <Database className="w-8 h-8 text-green-500" />
                                <div>
                                    <p className="text-sm text-gray-600">Cataloged Assets</p>
                                    <p className="text-2xl font-bold">{governanceDashboard.cataloged_assets}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center space-x-3">
                                <Clock className="w-8 h-8 text-purple-500" />
                                <div>
                                    <p className="text-sm text-gray-600">Last Audit</p>
                                    <p className="text-sm font-medium">
                                        {new Date(governanceDashboard.last_audit).toLocaleDateString()}
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Quick Actions */}
                <Card>
                    <CardHeader>
                        <CardTitle>Quick Actions</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            <Button
                                onClick={() => assessDataQuality('default-source')}
                                disabled={assessingQuality}
                                className="h-auto p-4 flex flex-col items-center space-y-2"
                            >
                                {assessingQuality ? (
                                    <RefreshCw className="w-6 h-6 animate-spin" />
                                ) : (
                                    <CheckCircle className="w-6 h-6" />
                                )}
                                <span>Assess Quality</span>
                            </Button>

                            <Button
                                variant="outline"
                                onClick={() => createDataLineage('default-source')}
                                disabled={creatingLineage}
                                className="h-auto p-4 flex flex-col items-center space-y-2"
                            >
                                {creatingLineage ? (
                                    <RefreshCw className="w-6 h-6 animate-spin" />
                                ) : (
                                    <GitBranch className="w-6 h-6" />
                                )}
                                <span>Create Lineage</span>
                            </Button>

                            <Button
                                variant="outline"
                                className="h-auto p-4 flex flex-col items-center space-y-2"
                            >
                                <Search className="w-6 h-6" />
                                <span>Data Catalog</span>
                            </Button>

                            <Button
                                variant="outline"
                                className="h-auto p-4 flex flex-col items-center space-y-2"
                            >
                                <Shield className="w-6 h-6" />
                                <span>Compliance Check</span>
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    };

    const renderDataQuality = () => {
        if (!dataQuality) {
            return (
                <div className="text-center py-12">
                    <CheckCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No quality assessment available</h3>
                    <p className="text-gray-500 mb-4">Run a data quality assessment to see detailed metrics.</p>
                    <Button onClick={() => assessDataQuality('default-source')} disabled={assessingQuality}>
                        {assessingQuality ? (
                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                            <CheckCircle className="w-4 h-4 mr-2" />
                        )}
                        Assess Data Quality
                    </Button>
                </div>
            );
        }

        const qualityMetrics = Object.entries(dataQuality.quality_metrics).map(([key, value]) => ({
            name: key.charAt(0).toUpperCase() + key.slice(1),
            score: value,
            color: value >= 95 ? '#00C49F' : value >= 85 ? '#0088FE' : value >= 70 ? '#FFBB28' : '#FF8042'
        }));

        return (
            <div className="space-y-6">
                {/* Overall Score */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                            <span>Data Quality Assessment: {dataQuality.data_source_name}</span>
                            <Badge className={`${dataQuality.overall_score >= 90 ? 'bg-green-100 text-green-800' :
                                    dataQuality.overall_score >= 75 ? 'bg-blue-100 text-blue-800' :
                                        dataQuality.overall_score >= 60 ? 'bg-yellow-100 text-yellow-800' :
                                            'bg-red-100 text-red-800'
                                }`}>
                                {dataQuality.overall_score.toFixed(1)}% Overall Score
                            </Badge>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-sm text-gray-600 mb-4">
                            Assessed on {new Date(dataQuality.assessed_at).toLocaleString()}
                        </p>

                        {/* Quality Metrics Chart */}
                        <div className="h-64 mb-6">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={qualityMetrics}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="name" />
                                    <YAxis domain={[0, 100]} />
                                    <Tooltip formatter={(value) => [`${value}%`, 'Score']} />
                                    <Bar dataKey="score" fill="#8884d8">
                                        {qualityMetrics.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Quality Metrics Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                            {qualityMetrics.map((metric, index) => (
                                <div key={index} className="p-4 bg-gray-50 rounded-lg">
                                    <p className="text-sm text-gray-600">{metric.name}</p>
                                    <p className="text-2xl font-bold" style={{ color: metric.color }}>
                                        {metric.score}%
                                    </p>
                                </div>
                            ))}
                        </div>

                        {/* Issues */}
                        {dataQuality.issues.length > 0 && (
                            <div className="mb-6">
                                <h4 className="font-semibold mb-3">Identified Issues</h4>
                                <div className="space-y-2">
                                    {dataQuality.issues.map((issue, index) => (
                                        <div key={index} className="flex items-center space-x-2 p-2 bg-red-50 rounded">
                                            <AlertTriangle className="w-4 h-4 text-red-500" />
                                            <span className="text-sm text-red-700">{issue}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Recommendations */}
                        {dataQuality.recommendations.length > 0 && (
                            <div>
                                <h4 className="font-semibold mb-3">Recommendations</h4>
                                <div className="space-y-2">
                                    {dataQuality.recommendations.map((recommendation, index) => (
                                        <div key={index} className="flex items-center space-x-2 p-2 bg-blue-50 rounded">
                                            <CheckCircle className="w-4 h-4 text-blue-500" />
                                            <span className="text-sm text-blue-700">{recommendation}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        );
    };

    const renderDataLineage = () => {
        if (!dataLineage) {
            return (
                <div className="text-center py-12">
                    <GitBranch className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No data lineage available</h3>
                    <p className="text-gray-500 mb-4">Create a data lineage map to understand data flow.</p>
                    <Button onClick={() => createDataLineage('default-source')} disabled={creatingLineage}>
                        {creatingLineage ? (
                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                            <GitBranch className="w-4 h-4 mr-2" />
                        )}
                        Create Data Lineage
                    </Button>
                </div>
            );
        }

        return (
            <div className="space-y-6">
                {/* Lineage Overview */}
                <Card>
                    <CardHeader>
                        <CardTitle>Data Lineage: {dataLineage.source_name}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {/* Impact Analysis */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                            <div className="p-4 bg-blue-50 rounded-lg">
                                <p className="text-sm text-blue-600">Affected Dashboards</p>
                                <p className="text-2xl font-bold text-blue-800">
                                    {dataLineage.impact_analysis.affected_dashboards}
                                </p>
                            </div>
                            <div className="p-4 bg-green-50 rounded-lg">
                                <p className="text-sm text-green-600">Affected Reports</p>
                                <p className="text-2xl font-bold text-green-800">
                                    {dataLineage.impact_analysis.affected_reports}
                                </p>
                            </div>
                            <div className="p-4 bg-purple-50 rounded-lg">
                                <p className="text-sm text-purple-600">Affected Models</p>
                                <p className="text-2xl font-bold text-purple-800">
                                    {dataLineage.impact_analysis.affected_models}
                                </p>
                            </div>
                        </div>

                        {/* Upstream Sources */}
                        <div className="mb-6">
                            <h4 className="font-semibold mb-3">Upstream Sources</h4>
                            <div className="space-y-2">
                                {dataLineage.upstream_sources.map((source, index) => (
                                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                        <div className="flex items-center space-x-3">
                                            <Database className="w-5 h-5 text-blue-500" />
                                            <div>
                                                <p className="font-medium">{source.name}</p>
                                                <p className="text-sm text-gray-600">{source.type}</p>
                                            </div>
                                        </div>
                                        <span className="text-sm text-gray-500">
                                            {new Date(source.last_updated).toLocaleDateString()}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Transformations */}
                        <div className="mb-6">
                            <h4 className="font-semibold mb-3">Data Transformations</h4>
                            <div className="space-y-3">
                                {dataLineage.transformations.map((transform, index) => (
                                    <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                                        <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                                            {transform.step}
                                        </div>
                                        <div className="flex-1">
                                            <p className="font-medium">{transform.operation}</p>
                                            <p className="text-sm text-gray-600">{transform.description}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Downstream Consumers */}
                        <div>
                            <h4 className="font-semibold mb-3">Downstream Consumers</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                {dataLineage.downstream_consumers.map((consumer, index) => (
                                    <div key={index} className="p-3 border rounded-lg">
                                        <div className="flex items-center space-x-2">
                                            {consumer.type === 'dashboard' && <Activity className="w-4 h-4 text-blue-500" />}
                                            {consumer.type === 'report' && <FileText className="w-4 h-4 text-green-500" />}
                                            {consumer.type === 'ml_model' && <TrendingUp className="w-4 h-4 text-purple-500" />}
                                            <div>
                                                <p className="font-medium">{consumer.name}</p>
                                                <p className="text-sm text-gray-600">{consumer.type}</p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
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
                <span>Loading data governance...</span>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Data Governance</h1>
                    <p className="text-gray-600">Data quality management and compliance monitoring</p>
                </div>
                <div className="flex items-center space-x-2">
                    <Button variant="outline" onClick={fetchGovernanceDashboard}>
                        <RefreshCw className="w-4 h-4 mr-2" />
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

            {/* Tabs */}
            <Tabs defaultValue={selectedTab}>
                <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="overview">
                        Overview
                    </TabsTrigger>
                    <TabsTrigger value="quality">
                        Data Quality
                    </TabsTrigger>
                    <TabsTrigger value="lineage">
                        Data Lineage
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="mt-6">
                    {renderOverview()}
                </TabsContent>

                <TabsContent value="quality" className="mt-6">
                    {renderDataQuality()}
                </TabsContent>

                <TabsContent value="lineage" className="mt-6">
                    {renderDataLineage()}
                </TabsContent>
            </Tabs>
        </div>
    );
}