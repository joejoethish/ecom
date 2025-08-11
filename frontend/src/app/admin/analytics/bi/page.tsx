'use client';

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  BarChart3, Brain, TrendingUp, Database, Eye, 
  Zap, Globe, Settings, Users, Target
} from 'lucide-react';

// Import BI components
import BIDashboard from '@/components/analytics/BIDashboard';
import BIInsights from '@/components/analytics/BIInsights';
import BIMLModels from '@/components/analytics/BIMLModels';
import BISelfServiceAnalytics from '@/components/analytics/BISelfServiceAnalytics';
import BIDataGovernance from '@/components/analytics/BIDataGovernance';
import BIRealtimeAnalytics from '@/components/analytics/BIRealtimeAnalytics';

export default function BIAnalyticsPage() {
  const [selectedTab, setSelectedTab] = useState('dashboard');

  const biFeatures = [
    {
      title: 'Executive Dashboards',
      description: 'Comprehensive dashboards with key business metrics and real-time insights',
      icon: BarChart3,
      color: 'text-blue-500',
      features: ['Real-time metrics', 'Interactive widgets', 'Custom layouts', 'Mobile responsive']
    },
    {
      title: 'Automated Insights',
      description: 'AI-powered insights with anomaly detection and trend analysis',
      icon: Brain,
      color: 'text-purple-500',
      features: ['Anomaly detection', 'Trend analysis', 'Pattern recognition', 'Smart alerts']
    },
    {
      title: 'Predictive Analytics',
      description: 'Machine learning models for forecasting and predictive analysis',
      icon: TrendingUp,
      color: 'text-green-500',
      features: ['Sales forecasting', 'Demand planning', 'Churn prediction', 'Price optimization']
    },
    {
      title: 'Self-Service Analytics',
      description: 'Drag-and-drop interface for creating custom reports and visualizations',
      icon: Eye,
      color: 'text-orange-500',
      features: ['Query builder', 'Custom visualizations', 'Data exploration', 'Collaboration tools']
    },
    {
      title: 'Real-time Processing',
      description: 'Stream processing for real-time analytics and instant insights',
      icon: Zap,
      color: 'text-yellow-500',
      features: ['Live data streams', 'Real-time alerts', 'Event processing', 'Instant updates']
    },
    {
      title: 'Data Governance',
      description: 'Comprehensive data governance with quality management and lineage',
      icon: Database,
      color: 'text-indigo-500',
      features: ['Data quality', 'Lineage tracking', 'Metadata management', 'Compliance monitoring']
    }
  ];

  const renderOverview = () => {
    return (
      <div className="space-y-6">
        {/* Hero Section */}
        <div className="text-center py-12 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
          <Brain className="w-16 h-16 text-blue-500 mx-auto mb-4" />
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Advanced Business Intelligence Platform
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Comprehensive BI solution with executive dashboards, automated insights, 
            predictive analytics, and self-service data exploration capabilities.
          </p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Active Dashboards</p>
                  <p className="text-3xl font-bold">12</p>
                </div>
                <BarChart3 className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">ML Models</p>
                  <p className="text-3xl font-bold">8</p>
                </div>
                <Brain className="w-8 h-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Data Sources</p>
                  <p className="text-3xl font-bold">15</p>
                </div>
                <Database className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Active Users</p>
                  <p className="text-3xl font-bold">156</p>
                </div>
                <Users className="w-8 h-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {biFeatures.map((feature, index) => {
            const IconComponent = feature.icon;
            return (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center space-x-3">
                    <IconComponent className={`w-8 h-8 ${feature.color}`} />
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-4">{feature.description}</p>
                  <div className="space-y-2">
                    {feature.features.map((item, i) => (
                      <div key={i} className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-sm text-gray-700">{item}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div 
                className="p-4 border rounded-lg cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => setSelectedTab('dashboard')}
              >
                <BarChart3 className="w-8 h-8 text-blue-500 mb-2" />
                <h3 className="font-semibold">View Dashboard</h3>
                <p className="text-sm text-gray-600">Access executive dashboard</p>
              </div>
              
              <div 
                className="p-4 border rounded-lg cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => setSelectedTab('insights')}
              >
                <Brain className="w-8 h-8 text-purple-500 mb-2" />
                <h3 className="font-semibold">Generate Insights</h3>
                <p className="text-sm text-gray-600">AI-powered analysis</p>
              </div>
              
              <div 
                className="p-4 border rounded-lg cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => setSelectedTab('ml-models')}
              >
                <TrendingUp className="w-8 h-8 text-green-500 mb-2" />
                <h3 className="font-semibold">Create Model</h3>
                <p className="text-sm text-gray-600">Build ML models</p>
              </div>
              
              <div 
                className="p-4 border rounded-lg cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => setSelectedTab('self-service')}
              >
                <Eye className="w-8 h-8 text-orange-500 mb-2" />
                <h3 className="font-semibold">Explore Data</h3>
                <p className="text-sm text-gray-600">Self-service analytics</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* System Status */}
        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <div>
                  <p className="font-medium">Data Pipeline</p>
                  <p className="text-sm text-gray-600">All systems operational</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <div>
                  <p className="font-medium">ML Models</p>
                  <p className="text-sm text-gray-600">8 models deployed</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                <div>
                  <p className="font-medium">Data Quality</p>
                  <p className="text-sm text-gray-600">92% quality score</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="overview" className="flex items-center space-x-2">
            <Globe className="w-4 h-4" />
            <span>Overview</span>
          </TabsTrigger>
          <TabsTrigger value="dashboard" className="flex items-center space-x-2">
            <BarChart3 className="w-4 h-4" />
            <span>Dashboard</span>
          </TabsTrigger>
          <TabsTrigger value="insights" className="flex items-center space-x-2">
            <Brain className="w-4 h-4" />
            <span>Insights</span>
          </TabsTrigger>
          <TabsTrigger value="ml-models" className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4" />
            <span>ML Models</span>
          </TabsTrigger>
          <TabsTrigger value="self-service" className="flex items-center space-x-2">
            <Eye className="w-4 h-4" />
            <span>Self-Service</span>
          </TabsTrigger>
          <TabsTrigger value="governance" className="flex items-center space-x-2">
            <Database className="w-4 h-4" />
            <span>Governance</span>
          </TabsTrigger>
          <TabsTrigger value="realtime" className="flex items-center space-x-2">
            <Zap className="w-4 h-4" />
            <span>Real-time</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          {renderOverview()}
        </TabsContent>

        <TabsContent value="dashboard" className="mt-6">
          <BIDashboard dashboardType="executive" />
        </TabsContent>

        <TabsContent value="insights" className="mt-6">
          <BIInsights />
        </TabsContent>

        <TabsContent value="ml-models" className="mt-6">
          <BIMLModels />
        </TabsContent>

        <TabsContent value="self-service" className="mt-6">
          <BISelfServiceAnalytics />
        </TabsContent>

        <TabsContent value="governance" className="mt-6">
          <BIDataGovernance />
        </TabsContent>

        <TabsContent value="realtime" className="mt-6">
          <BIRealtimeAnalytics />
        </TabsContent>
      </Tabs>
    </div>
  );
}