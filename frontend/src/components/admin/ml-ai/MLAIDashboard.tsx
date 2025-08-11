import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Brain, 
  TrendingUp, 
  Users, 
  Shield, 
  Star, 
  DollarSign,
  AlertTriangle,
  BarChart3,
  Lightbulb,
  Activity
} from 'lucide-react';

interface MLModel {
  id: string;
  name: string;
  type: string;
  status: string;
  accuracy?: number;
  last_trained?: string;
  predictions_count: number;
}

interface AIInsight {
  type: string;
  title: string;
  description: string;
  priority: string;
  recommendations: string[];
  confidence: number;
}

interface MLStats {
  total_models: number;
  active_models: number;
  total_predictions: number;
  avg_accuracy: number;
}

const MLAIDashboard: React.FC = () => {
  const [models, setModels] = useState<MLModel[]>([]);
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [stats, setStats] = useState<MLStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch ML models
      const modelsResponse = await fetch('/api/admin/ml-ai/models/performance_summary/');
      const modelsData = await modelsResponse.json();
      setModels(modelsData);
      
      // Fetch AI insights
      const insightsResponse = await fetch('/api/admin/ml-ai/insights/generate/');
      const insightsData = await insightsResponse.json();
      setInsights(insightsData);
      
      // Calculate stats
      const totalModels = modelsData.length;
      const activeModels = modelsData.filter((m: MLModel) => m.status === 'active').length;
      const totalPredictions = modelsData.reduce((sum: number, m: MLModel) => sum + m.predictions_count, 0);
      const avgAccuracy = modelsData.reduce((sum: number, m: MLModel) => sum + (m.accuracy || 0), 0) / totalModels;
      
      setStats({
        total_models: totalModels,
        active_models: activeModels,
        total_predictions: totalPredictions,
        avg_accuracy: avgAccuracy
      });
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getModelIcon = (type: string) => {
    switch (type) {
      case 'demand_forecasting': return <TrendingUp className="h-4 w-4" />;
      case 'customer_segmentation': return <Users className="h-4 w-4" />;
      case 'fraud_detection': return <Shield className="h-4 w-4" />;
      case 'recommendation': return <Star className="h-4 w-4" />;
      case 'pricing_optimization': return <DollarSign className="h-4 w-4" />;
      case 'churn_prediction': return <AlertTriangle className="h-4 w-4" />;
      case 'sentiment_analysis': return <BarChart3 className="h-4 w-4" />;
      case 'anomaly_detection': return <Activity className="h-4 w-4" />;
      default: return <Brain className="h-4 w-4" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'default';
    }
  };

  const formatModelType = (type: string) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">ML & AI Dashboard</h1>
          <p className="text-gray-600">Machine Learning models and AI-powered insights</p>
        </div>
        <Button onClick={fetchDashboardData} disabled={loading}>
          <Brain className="h-4 w-4 mr-2" />
          Refresh Data
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Models</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total_models}</p>
                </div>
                <Brain className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Models</p>
                  <p className="text-2xl font-bold text-green-600">{stats.active_models}</p>
                </div>
                <Activity className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Predictions</p>
                  <p className="text-2xl font-bold text-purple-600">{stats.total_predictions.toLocaleString()}</p>
                </div>
                <BarChart3 className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Accuracy</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {(stats.avg_accuracy * 100).toFixed(1)}%
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-orange-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="models">ML Models</TabsTrigger>
          <TabsTrigger value="insights">AI Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Models */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Brain className="h-5 w-5 mr-2" />
                  Recent Models
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {models.slice(0, 5).map((model) => (
                    <div key={model.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        {getModelIcon(model.type)}
                        <div>
                          <p className="font-medium text-gray-900">{model.name}</p>
                          <p className="text-sm text-gray-600">{formatModelType(model.type)}</p>
                        </div>
                      </div>
                      <Badge variant={model.status === 'active' ? 'default' : 'secondary'}>
                        {model.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Top Insights */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Lightbulb className="h-5 w-5 mr-2" />
                  Top AI Insights
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {insights.slice(0, 5).map((insight, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-medium text-gray-900">{insight.title}</h4>
                        <Badge variant={getPriorityColor(insight.priority)}>
                          {insight.priority}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{insight.description}</p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500">
                          Confidence: {(insight.confidence * 100).toFixed(0)}%
                        </span>
                        <span className="text-xs text-gray-500">
                          {insight.recommendations.length} recommendations
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="models" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>ML Models Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Model</th>
                      <th className="text-left p-2">Type</th>
                      <th className="text-left p-2">Status</th>
                      <th className="text-left p-2">Accuracy</th>
                      <th className="text-left p-2">Predictions</th>
                      <th className="text-left p-2">Last Trained</th>
                    </tr>
                  </thead>
                  <tbody>
                    {models.map((model) => (
                      <tr key={model.id} className="border-b hover:bg-gray-50">
                        <td className="p-2">
                          <div className="flex items-center space-x-2">
                            {getModelIcon(model.type)}
                            <span className="font-medium">{model.name}</span>
                          </div>
                        </td>
                        <td className="p-2">{formatModelType(model.type)}</td>
                        <td className="p-2">
                          <Badge variant={model.status === 'active' ? 'default' : 'secondary'}>
                            {model.status}
                          </Badge>
                        </td>
                        <td className="p-2">
                          {model.accuracy ? `${(model.accuracy * 100).toFixed(1)}%` : 'N/A'}
                        </td>
                        <td className="p-2">{model.predictions_count.toLocaleString()}</td>
                        <td className="p-2">
                          {model.last_trained ? 
                            new Date(model.last_trained).toLocaleDateString() : 
                            'Never'
                          }
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="insights" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {insights.map((insight, index) => (
              <Card key={index}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-lg">{insight.title}</CardTitle>
                    <Badge variant={getPriorityColor(insight.priority)}>
                      {insight.priority}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-4">{insight.description}</p>
                  
                  <div className="mb-4">
                    <h4 className="font-medium text-gray-900 mb-2">Recommendations:</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {insight.recommendations.map((rec, recIndex) => (
                        <li key={recIndex} className="text-sm text-gray-600">{rec}</li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>Type: {insight.type.replace('_', ' ')}</span>
                    <span>Confidence: {(insight.confidence * 100).toFixed(0)}%</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MLAIDashboard;