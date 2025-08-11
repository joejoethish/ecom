'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar
} from 'recharts';
import { 
  Brain, TrendingUp, Play, Pause, Settings, Download, 
  AlertTriangle, CheckCircle, Clock, RefreshCw, Target,
  BarChart3, Zap, Database, Cpu, Activity, DollarSign
} from 'lucide-react';

interface BIMLModelsProps {
  dataSourceId?: string;
}

interface MLModel {
  id: string;
  name: string;
  description: string;
  model_type: 'forecasting' | 'classification' | 'clustering' | 'anomaly_detection' | 'recommendation' | 'churn_prediction' | 'price_optimization' | 'demand_planning';
  algorithm: string;
  training_data_source_name: string;
  feature_config: any;
  hyperparameters: any;
  performance_metrics: any;
  version: string;
  is_deployed: boolean;
  last_trained?: string;
  last_prediction?: string;
  training_schedule: string;
  created_by_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  model_status: 'not_trained' | 'trained' | 'deployed';
}

interface Prediction {
  date: string;
  predicted_value: number;
  lower_bound: number;
  upper_bound: number;
  confidence: number;
}

interface PredictionResult {
  model_id: string;
  model_name: string;
  predictions: Prediction[];
  prediction_periods: number;
  generated_at: string;
}

const MODEL_TYPE_ICONS = {
  forecasting: TrendingUp,
  classification: Target,
  clustering: BarChart3,
  anomaly_detection: AlertTriangle,
  recommendation: Brain,
  churn_prediction: Activity,
  price_optimization: DollarSign,
  demand_planning: Database
};

const MODEL_STATUS_COLORS = {
  not_trained: 'bg-gray-100 text-gray-800',
  trained: 'bg-blue-100 text-blue-800',
  deployed: 'bg-green-100 text-green-800'
};

export default function BIMLModels({ dataSourceId }: BIMLModelsProps) {
  const [models, setModels] = useState<MLModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<MLModel | null>(null);
  const [predictions, setPredictions] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trainingModel, setTrainingModel] = useState<string | null>(null);
  const [generatingPredictions, setGeneratingPredictions] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState('models');

  const fetchModels = useCallback(async () => {
    try {
      setLoading(true);
      
      const response = await fetch('/api/analytics/bi/ml-models/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch ML models');
      
      const data = await response.json();
      setModels(data.results || data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, []);

  const createForecastingModel = async () => {
    try {
      const name = prompt('Enter model name:');
      if (!name) return;

      const response = await fetch('/api/analytics/bi/ml-models/create_forecasting_model/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          name,
          data_source_id: dataSourceId || 'default'
        })
      });

      if (!response.ok) throw new Error('Failed to create model');
      
      await fetchModels();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create model');
    }
  };

  const trainModel = async (modelId: string) => {
    try {
      setTrainingModel(modelId);
      
      const response = await fetch(`/api/analytics/bi/ml-models/${modelId}/train_model/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to train model');
      
      const result = await response.json();
      
      // Update model in local state
      setModels(prev => prev.map(model => 
        model.id === modelId 
          ? { ...model, model_status: 'trained', last_trained: new Date().toISOString() }
          : model
      ));
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to train model');
    } finally {
      setTrainingModel(null);
    }
  };

  const deployModel = async (modelId: string) => {
    try {
      const response = await fetch(`/api/analytics/bi/ml-models/${modelId}/deploy_model/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          deployment_config: {
            environment: 'production',
            auto_retrain: true,
            monitoring_enabled: true
          }
        })
      });

      if (!response.ok) throw new Error('Failed to deploy model');
      
      // Update model in local state
      setModels(prev => prev.map(model => 
        model.id === modelId 
          ? { ...model, is_deployed: true, model_status: 'deployed' }
          : model
      ));
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to deploy model');
    }
  };

  const generatePredictions = async (modelId: string, periods: number = 30) => {
    try {
      setGeneratingPredictions(modelId);
      
      const response = await fetch(`/api/analytics/bi/ml-models/${modelId}/generate_predictions/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          prediction_periods: periods,
          confidence_level: 95.0,
          include_intervals: true
        })
      });

      if (!response.ok) throw new Error('Failed to generate predictions');
      
      const result = await response.json();
      setPredictions(result);
      setSelectedTab('predictions');
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate predictions');
    } finally {
      setGeneratingPredictions(null);
    }
  };

  const getModelPerformance = async (modelId: string) => {
    try {
      const response = await fetch(`/api/analytics/bi/ml-models/${modelId}/model_performance/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to get model performance');
      
      const performance = await response.json();
      
      // Update selected model with performance data
      setSelectedModel(prev => prev ? { ...prev, performance_metrics: performance.performance_metrics } : null);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get model performance');
    }
  };

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const getModelIcon = (type: string) => {
    const IconComponent = MODEL_TYPE_ICONS[type as keyof typeof MODEL_TYPE_ICONS] || Brain;
    return IconComponent;
  };

  const getStatusBadge = (status: string) => {
    const colorClass = MODEL_STATUS_COLORS[status as keyof typeof MODEL_STATUS_COLORS] || 'bg-gray-100 text-gray-800';
    return (
      <Badge className={colorClass}>
        {status.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };

  const renderModelCard = (model: MLModel) => {
    const IconComponent = getModelIcon(model.model_type);

    return (
      <Card key={model.id} className="cursor-pointer hover:shadow-md transition-shadow">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <IconComponent className="w-6 h-6 text-blue-500 mt-1" />
              <div className="flex-1">
                <CardTitle className="text-lg">{model.name}</CardTitle>
                <p className="text-sm text-gray-600 mt-1">{model.description}</p>
                <div className="flex items-center space-x-2 mt-2">
                  {getStatusBadge(model.model_status)}
                  <Badge variant="outline">{model.model_type}</Badge>
                  <Badge variant="outline">{model.algorithm}</Badge>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {model.is_deployed && (
                <Badge className="bg-green-100 text-green-800">
                  <Zap className="w-3 h-3 mr-1" />
                  Live
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm text-gray-600">Data Source</p>
              <p className="font-medium">{model.training_data_source_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Version</p>
              <p className="font-medium">v{model.version}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Last Trained</p>
              <p className="font-medium">
                {model.last_trained 
                  ? new Date(model.last_trained).toLocaleDateString()
                  : 'Never'
                }
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Schedule</p>
              <p className="font-medium">{model.training_schedule}</p>
            </div>
          </div>

          {/* Performance Metrics */}
          {model.performance_metrics && Object.keys(model.performance_metrics).length > 0 && (
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <h4 className="font-semibold mb-2">Performance Metrics</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                {Object.entries(model.performance_metrics).map(([key, value]) => (
                  <div key={key}>
                    <span className="text-gray-600">{key.toUpperCase()}:</span>
                    <span className="ml-1 font-medium">
                      {typeof value === 'number' ? value.toFixed(3) : value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Created by {model.created_by_name}
            </div>
            <div className="flex items-center space-x-2">
              {model.model_status === 'not_trained' && (
                <Button
                  size="sm"
                  onClick={() => trainModel(model.id)}
                  disabled={trainingModel === model.id}
                >
                  {trainingModel === model.id ? (
                    <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4 mr-1" />
                  )}
                  Train
                </Button>
              )}
              {model.model_status === 'trained' && !model.is_deployed && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => deployModel(model.id)}
                >
                  <Zap className="w-4 h-4 mr-1" />
                  Deploy
                </Button>
              )}
              {model.is_deployed && (
                <Button
                  size="sm"
                  onClick={() => generatePredictions(model.id)}
                  disabled={generatingPredictions === model.id}
                >
                  {generatingPredictions === model.id ? (
                    <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
                  ) : (
                    <Target className="w-4 h-4 mr-1" />
                  )}
                  Predict
                </Button>
              )}
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setSelectedModel(model);
                  getModelPerformance(model.id);
                }}
              >
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderPredictionsChart = () => {
    if (!predictions) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle>Predictions: {predictions.model_name}</CardTitle>
          <p className="text-sm text-gray-600">
            Generated {predictions.prediction_periods} predictions on {new Date(predictions.generated_at).toLocaleString()}
          </p>
        </CardHeader>
        <CardContent>
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={predictions.predictions}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip 
                  formatter={(value, name) => [
                    typeof value === 'number' ? value.toLocaleString() : value,
                    name
                  ]}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="upper_bound"
                  stackId="1"
                  stroke="#e5e7eb"
                  fill="#e5e7eb"
                  fillOpacity={0.3}
                />
                <Area
                  type="monotone"
                  dataKey="lower_bound"
                  stackId="1"
                  stroke="#e5e7eb"
                  fill="#ffffff"
                  fillOpacity={1}
                />
                <Line
                  type="monotone"
                  dataKey="predicted_value"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          
          {/* Prediction Summary */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-600">Average Prediction</p>
              <p className="text-lg font-bold text-blue-800">
                {(predictions.predictions.reduce((sum, p) => sum + p.predicted_value, 0) / predictions.predictions.length).toLocaleString()}
              </p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <p className="text-sm text-green-600">Highest Prediction</p>
              <p className="text-lg font-bold text-green-800">
                {Math.max(...predictions.predictions.map(p => p.predicted_value)).toLocaleString()}
              </p>
            </div>
            <div className="p-3 bg-orange-50 rounded-lg">
              <p className="text-sm text-orange-600">Average Confidence</p>
              <p className="text-lg font-bold text-orange-800">
                {(predictions.predictions.reduce((sum, p) => sum + p.confidence, 0) / predictions.predictions.length).toFixed(1)}%
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin mr-2" />
        <span>Loading ML models...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Machine Learning Models</h1>
          <p className="text-gray-600">Predictive analytics and forecasting models</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button onClick={createForecastingModel}>
            <Brain className="w-4 h-4 mr-2" />
            Create Model
          </Button>
          <Button variant="outline" onClick={fetchModels}>
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
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="models">
            Models ({models.length})
          </TabsTrigger>
          <TabsTrigger value="predictions">
            Predictions
          </TabsTrigger>
          <TabsTrigger value="performance">
            Performance
          </TabsTrigger>
        </TabsList>

        <TabsContent value="models" className="mt-6">
          {models.length === 0 ? (
            <div className="text-center py-12">
              <Brain className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No ML models found</h3>
              <p className="text-gray-500 mb-4">
                Create your first machine learning model to start generating predictions.
              </p>
              <Button onClick={createForecastingModel}>
                <Brain className="w-4 h-4 mr-2" />
                Create Forecasting Model
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {models.map(renderModelCard)}
            </div>
          )}
        </TabsContent>

        <TabsContent value="predictions" className="mt-6">
          {predictions ? (
            renderPredictionsChart()
          ) : (
            <div className="text-center py-12">
              <Target className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No predictions generated</h3>
              <p className="text-gray-500">
                Deploy a model and generate predictions to see forecasts here.
              </p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="performance" className="mt-6">
          {selectedModel ? (
            <Card>
              <CardHeader>
                <CardTitle>Model Performance: {selectedModel.name}</CardTitle>
              </CardHeader>
              <CardContent>
                {selectedModel.performance_metrics ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(selectedModel.performance_metrics).map(([key, value]) => (
                      <div key={key} className="p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-600">{key.toUpperCase()}</p>
                        <p className="text-2xl font-bold">
                          {typeof value === 'number' ? value.toFixed(3) : value}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">No performance metrics available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="text-center py-12">
              <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Select a model</h3>
              <p className="text-gray-500">
                Click on a model to view its performance metrics.
              </p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}