import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/progress';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter, ReferenceLine } from 'recharts';
import { Brain, TrendingUp, AlertTriangle, Target, Zap, Activity } from 'lucide-react';

interface PredictionData {
  timestamp: string;
  predicted_value: number;
  hour_ahead: number;
}

interface AnomalyData {
  timestamp: string;
  predicted_value: number;
  z_score: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

interface ModelAccuracy {
  mse: number;
  mae: number;
  mape: number;
  r2_score: number;
}

interface TrendAnalysis {
  historical_trend: {
    slope: number;
    direction: 'increasing' | 'decreasing' | 'stable';
  };
  predicted_trend: {
    slope: number;
    direction: 'increasing' | 'decreasing' | 'stable';
  };
  trend_change: boolean;
}

interface PredictiveAnalyticsData {
  metric_type: string;
  historical_data: Array<{
    timestamp: string;
    value: number;
    hour: number;
    day_of_week: number;
  }>;
  predictions: PredictionData[];
  anomalies: AnomalyData[];
  model_accuracy: ModelAccuracy;
  confidence_interval: {
    '95_percent': { lower: number; upper: number };
    '99_percent': { lower: number; upper: number };
    mean: number;
    std_dev: number;
  };
  trend_analysis: TrendAnalysis;
}

const PredictiveAnalytics: React.FC = () => {
  const [activeTab, setActiveTab] = useState('predictions');
  const [selectedMetric, setSelectedMetric] = useState('response_time');
  const [analyticsData, setAnalyticsData] = useState<PredictiveAnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [anomalyDetectionData, setAnomalyDetectionData] = useState<any>(null);

  const metricOptions = [
    { value: 'response_time', label: 'Response Time' },
    { value: 'cpu_usage', label: 'CPU Usage' },
    { value: 'memory_usage', label: 'Memory Usage' },
    { value: 'disk_usage', label: 'Disk Usage' },
    { value: 'error_rate', label: 'Error Rate' },
    { value: 'throughput', label: 'Throughput' }
  ];

  useEffect(() => {
    fetchPredictiveAnalytics();
  }, [selectedMetric]);

  const fetchPredictiveAnalytics = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/admin/performance/predictive-analytics/?metric_type=${selectedMetric}`);
      const data = await response.json();
      setAnalyticsData(data);
    } catch (error) {
      console.error('Failed to fetch predictive analytics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAnomalyDetection = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/admin/performance/anomaly-detection/?metric_type=${selectedMetric}`);
      const data = await response.json();
      setAnomalyDetectionData(data);
    } catch (error) {
      console.error('Failed to fetch anomaly detection:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'outline';
    }
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'increasing': return <TrendingUp className="h-4 w-4 text-red-500" />;
      case 'decreasing': return <TrendingUp className="h-4 w-4 text-green-500 rotate-180" />;
      case 'stable': return <Activity className="h-4 w-4 text-blue-500" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  const renderPredictionsTab = () => {
    if (!analyticsData) return <div>No data available</div>;

    const combinedData = [
      ...analyticsData.historical_data.map(d => ({
        timestamp: new Date(d.timestamp).getTime(),
        historical: d.value,
        type: 'historical'
      })),
      ...analyticsData.predictions.map(p => ({
        timestamp: new Date(p.timestamp).getTime(),
        predicted: p.predicted_value,
        type: 'predicted'
      }))
    ].sort((a, b) => a.timestamp - b.timestamp);

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Model Accuracy</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(analyticsData.model_accuracy.r2_score * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground">R² Score</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">MAPE</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {analyticsData.model_accuracy.mape.toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground">Mean Absolute Percentage Error</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Predicted Anomalies</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {analyticsData.anomalies.length}
              </div>
              <div className="text-sm text-muted-foreground">Next 24 hours</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Trend Direction</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                {getTrendIcon(analyticsData.trend_analysis.predicted_trend.direction)}
                <span className="text-lg font-semibold capitalize">
                  {analyticsData.trend_analysis.predicted_trend.direction}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Performance Predictions</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={combinedData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="timestamp" 
                  type="number"
                  scale="time"
                  domain={['dataMin', 'dataMax']}
                  tickFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => new Date(value).toLocaleString()}
                  formatter={(value, name) => [
                    typeof value === 'number' ? value.toFixed(2) : value,
                    name === 'historical' ? 'Historical' : 'Predicted'
                  ]}
                />
                <Line 
                  type="monotone" 
                  dataKey="historical" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                  dot={false}
                  connectNulls={false}
                />
                <Line 
                  type="monotone" 
                  dataKey="predicted" 
                  stroke="#82ca9d" 
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  connectNulls={false}
                />
                <ReferenceLine 
                  x={Date.now()} 
                  stroke="#ff7300" 
                  strokeDasharray="2 2"
                  label="Now"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {analyticsData.anomalies.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-orange-500" />
                Predicted Anomalies
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {analyticsData.anomalies.map((anomaly, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <div className="font-medium">
                        {new Date(anomaly.timestamp).toLocaleString()}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Predicted value: {anomaly.predicted_value.toFixed(2)}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={getSeverityColor(anomaly.severity)}>
                        {anomaly.severity}
                      </Badge>
                      <div className="text-sm">
                        Z-Score: {anomaly.z_score.toFixed(2)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderAnomalyDetectionTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Real-time Anomaly Detection</h3>
        <Button onClick={fetchAnomalyDetection} disabled={isLoading}>
          <Brain className="h-4 w-4 mr-2" />
          Run Detection
        </Button>
      </div>

      {anomalyDetectionData && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Total Samples</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {anomalyDetectionData.total_samples}
                </div>
                <div className="text-sm text-muted-foreground">Last 24 hours</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Anomalies Detected</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {anomalyDetectionData.anomaly_count}
                </div>
                <div className="text-sm text-muted-foreground">
                  {(anomalyDetectionData.anomaly_rate * 100).toFixed(1)}% rate
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Detection Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${
                    anomalyDetectionData.anomaly_rate > 0.1 ? 'bg-red-500' : 
                    anomalyDetectionData.anomaly_rate > 0.05 ? 'bg-yellow-500' : 'bg-green-500'
                  }`} />
                  <span className="font-semibold">
                    {anomalyDetectionData.anomaly_rate > 0.1 ? 'High' : 
                     anomalyDetectionData.anomaly_rate > 0.05 ? 'Medium' : 'Normal'}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          {anomalyDetectionData.anomalies.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Anomalies</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {anomalyDetectionData.anomalies.map((anomaly: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">
                          {new Date(anomaly.timestamp).toLocaleString()}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Value: {anomaly.value.toFixed(2)}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={getSeverityColor(anomaly.severity)}>
                          {anomaly.severity}
                        </Badge>
                        <div className="text-sm">
                          Score: {anomaly.anomaly_score.toFixed(3)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );

  const renderTrendAnalysisTab = () => {
    if (!analyticsData) return <div>No data available</div>;

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Historical Trend
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold capitalize">
                    {analyticsData.trend_analysis.historical_trend.direction}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Slope: {analyticsData.trend_analysis.historical_trend.slope.toFixed(4)}
                  </div>
                </div>
                {getTrendIcon(analyticsData.trend_analysis.historical_trend.direction)}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Predicted Trend
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold capitalize">
                    {analyticsData.trend_analysis.predicted_trend.direction}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Slope: {analyticsData.trend_analysis.predicted_trend.slope.toFixed(4)}
                  </div>
                </div>
                {getTrendIcon(analyticsData.trend_analysis.predicted_trend.direction)}
              </div>
            </CardContent>
          </Card>
        </div>

        {analyticsData.trend_analysis.trend_change && (
          <Card className="border-orange-200 bg-orange-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-orange-800">
                <AlertTriangle className="h-5 w-5" />
                Trend Change Detected
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-orange-700">
                A significant change in trend has been detected between historical and predicted data. 
                This may indicate a shift in system behavior that requires attention.
              </p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Confidence Intervals</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-medium">95% Confidence Interval</h4>
                <div className="text-sm">
                  <div>Lower: {analyticsData.confidence_interval['95_percent'].lower.toFixed(2)}</div>
                  <div>Upper: {analyticsData.confidence_interval['95_percent'].upper.toFixed(2)}</div>
                </div>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium">99% Confidence Interval</h4>
                <div className="text-sm">
                  <div>Lower: {analyticsData.confidence_interval['99_percent'].lower.toFixed(2)}</div>
                  <div>Upper: {analyticsData.confidence_interval['99_percent'].upper.toFixed(2)}</div>
                </div>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Mean:</span> {analyticsData.confidence_interval.mean.toFixed(2)}
                </div>
                <div>
                  <span className="font-medium">Std Dev:</span> {analyticsData.confidence_interval.std_dev.toFixed(2)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Predictive Analytics</h2>
        <div className="flex items-center gap-4">
          <Select value={selectedMetric} onChange={setSelectedMetric}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {metricOptions.map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={fetchPredictiveAnalytics} disabled={isLoading}>
            <Zap className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {isLoading && (
        <Card>
          <CardContent className="py-8">
            <div className="flex items-center justify-center space-x-2">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              <span>Analyzing performance data...</span>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue={activeTab} >
        <TabsList>
          <TabsTrigger value="predictions">Predictions</TabsTrigger>
          <TabsTrigger value="anomalies">Anomaly Detection</TabsTrigger>
          <TabsTrigger value="trends">Trend Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="predictions">
          {renderPredictionsTab()}
        </TabsContent>

        <TabsContent value="anomalies">
          {renderAnomalyDetectionTab()}
        </TabsContent>

        <TabsContent value="trends">
          {renderTrendAnalysisTab()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PredictiveAnalytics;