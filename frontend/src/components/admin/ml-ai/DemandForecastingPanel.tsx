import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, Calendar, Package, AlertCircle } from 'lucide-react';

interface ForecastData {
  date: string;
  predicted_demand: number;
  confidence_lower: number;
  confidence_upper: number;
}

interface TrainingRequest {
  product_id: string;
}

interface PredictionRequest {
  product_id: string;
  forecast_days: number;
}

const DemandForecastingPanel: React.FC = () => {
  const [forecasts, setForecasts] = useState<ForecastData[]>([]);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [productId, setProductId] = useState('');
  const [forecastDays, setForecastDays] = useState(30);
  const [error, setError] = useState<string | null>(null);

  const trainModel = async () => {
    if (!productId.trim()) {
      setError('Please enter a product ID');
      return;
    }

    try {
      setTraining(true);
      setError(null);

      const response = await fetch('/api/admin/ml-ai/demand-forecasting/train/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ product_id: productId }),
      });

      if (!response.ok) {
        throw new Error('Failed to train model');
      }

      const data = await response.json();
      alert(`Model training completed: ${data.message}`);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Training failed');
    } finally {
      setTraining(false);
    }
  };

  const generateForecast = async () => {
    if (!productId.trim()) {
      setError('Please enter a product ID');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/admin/ml-ai/demand-forecasting/predict/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_id: productId,
          forecast_days: forecastDays,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate forecast');
      }

      const data = await response.json();
      setForecasts(data);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Forecast generation failed');
    } finally {
      setLoading(false);
    }
  };

  const chartData = forecasts.map(forecast => ({
    date: new Date(forecast.date).toLocaleDateString(),
    predicted: forecast.predicted_demand,
    lower: forecast.confidence_lower,
    upper: forecast.confidence_upper,
  }));

  const totalPredictedDemand = forecasts.reduce((sum, f) => sum + f.predicted_demand, 0);
  const avgDailyDemand = forecasts.length > 0 ? totalPredictedDemand / forecasts.length : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Demand Forecasting</h2>
          <p className="text-gray-600">AI-powered demand prediction for inventory planning</p>
        </div>
        <TrendingUp className="h-8 w-8 text-blue-600" />
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Forecast Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="productId">Product ID</Label>
              <Input
                id="productId"
                value={productId}
                onChange={(e) => setProductId(e.target.value)}
                placeholder="Enter product ID"
              />
            </div>
            <div>
              <Label htmlFor="forecastDays">Forecast Days</Label>
              <Select value={forecastDays.toString()} onChange={(value: string) => setForecastDays(parseInt(value))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7">7 days</SelectItem>
                  <SelectItem value="14">14 days</SelectItem>
                  <SelectItem value="30">30 days</SelectItem>
                  <SelectItem value="60">60 days</SelectItem>
                  <SelectItem value="90">90 days</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end space-x-2">
              <Button onClick={trainModel} disabled={training} variant="outline">
                {training ? 'Training...' : 'Train Model'}
              </Button>
              <Button onClick={generateForecast} disabled={loading}>
                {loading ? 'Generating...' : 'Generate Forecast'}
              </Button>
            </div>
          </div>

          {error && (
            <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-lg">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Forecast Summary */}
      {forecasts.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Predicted Demand</p>
                  <p className="text-2xl font-bold text-blue-600">{totalPredictedDemand.toLocaleString()}</p>
                </div>
                <Package className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Average Daily Demand</p>
                  <p className="text-2xl font-bold text-green-600">{Math.round(avgDailyDemand).toLocaleString()}</p>
                </div>
                <Calendar className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Forecast Period</p>
                  <p className="text-2xl font-bold text-purple-600">{forecastDays} days</p>
                </div>
                <TrendingUp className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Forecast Chart */}
      {forecasts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Demand Forecast Chart</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="predicted" 
                    stroke="#2563eb" 
                    strokeWidth={2}
                    name="Predicted Demand"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="lower" 
                    stroke="#dc2626" 
                    strokeDasharray="5 5"
                    name="Lower Bound"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="upper" 
                    stroke="#16a34a" 
                    strokeDasharray="5 5"
                    name="Upper Bound"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Forecast Table */}
      {forecasts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Detailed Forecast Data</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Date</th>
                    <th className="text-left p-2">Predicted Demand</th>
                    <th className="text-left p-2">Confidence Range</th>
                    <th className="text-left p-2">Variance</th>
                  </tr>
                </thead>
                <tbody>
                  {forecasts.map((forecast, index) => {
                    const variance = forecast.confidence_upper - forecast.confidence_lower;
                    return (
                      <tr key={index} className="border-b hover:bg-gray-50">
                        <td className="p-2">{new Date(forecast.date).toLocaleDateString()}</td>
                        <td className="p-2 font-medium">{forecast.predicted_demand.toLocaleString()}</td>
                        <td className="p-2">
                          {forecast.confidence_lower.toLocaleString()} - {forecast.confidence_upper.toLocaleString()}
                        </td>
                        <td className="p-2">
                          <span className={`px-2 py-1 rounded text-xs ${
                            variance > 50 ? 'bg-red-100 text-red-800' :
                            variance > 25 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            ±{variance.toLocaleString()}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DemandForecastingPanel;