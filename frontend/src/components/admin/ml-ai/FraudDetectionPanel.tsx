import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Badge } from '@/components/ui/Badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Shield, AlertTriangle, CheckCircle, XCircle, TrendingUp } from 'lucide-react';

interface FraudResult {
  is_fraud_risk: boolean;
  risk_score: number;
  risk_level: string;
  risk_factors: string[];
  anomaly_score: number;
}

interface FraudStats {
  total_transactions: number;
  high_risk_count: number;
  critical_risk_count: number;
  avg_risk_score: number;
}

interface TransactionData {
  transaction_id: string;
  amount: number;
  hour_of_day: number;
  day_of_week: number;
  num_items: number;
  customer_age_days: number;
  payment_method: number;
  shipping_address_matches: boolean;
}

const FraudDetectionPanel: React.FC = () => {
  const [result, setResult] = useState<FraudResult | null>(null);
  const [stats, setStats] = useState<FraudStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [transactionData, setTransactionData] = useState<TransactionData>({
    transaction_id: '',
    amount: 0,
    hour_of_day: 12,
    day_of_week: 1,
    num_items: 1,
    customer_age_days: 30,
    payment_method: 0,
    shipping_address_matches: true,
  });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/admin/ml-ai/fraud-detection/statistics/');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching fraud statistics:', error);
    }
  };

  const trainModel = async () => {
    try {
      setTraining(true);
      const response = await fetch('/api/admin/ml-ai/fraud-detection/train/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to train model');
      }

      const data = await response.json();
      alert(`Model training completed: ${data.message}`);
    } catch (error) {
      alert('Training failed: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setTraining(false);
    }
  };

  const detectFraud = async () => {
    if (!transactionData.transaction_id.trim()) {
      alert('Please enter a transaction ID');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch('/api/admin/ml-ai/fraud-detection/detect/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(transactionData),
      });

      if (!response.ok) {
        throw new Error('Failed to detect fraud');
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      alert('Fraud detection failed: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'secondary';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'critical':
      case 'high':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'medium':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'low':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      default:
        return <Shield className="h-5 w-5 text-gray-600" />;
    }
  };

  const paymentMethods = ['Credit Card', 'PayPal', 'Bank Transfer'];
  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  // Chart data for statistics
  const riskDistributionData = stats ? [
    { name: 'Low Risk', value: stats.total_transactions - stats.high_risk_count - stats.critical_risk_count, color: '#10b981' },
    { name: 'High Risk', value: stats.high_risk_count, color: '#f59e0b' },
    { name: 'Critical Risk', value: stats.critical_risk_count, color: '#ef4444' },
  ] : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Fraud Detection</h2>
          <p className="text-gray-600">AI-powered transaction fraud detection and risk assessment</p>
        </div>
        <Shield className="h-8 w-8 text-red-600" />
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Transactions</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total_transactions.toLocaleString()}</p>
                </div>
                <TrendingUp className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">High Risk</p>
                  <p className="text-2xl font-bold text-yellow-600">{stats.high_risk_count}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-yellow-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Critical Risk</p>
                  <p className="text-2xl font-bold text-red-600">{stats.critical_risk_count}</p>
                </div>
                <XCircle className="h-8 w-8 text-red-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Risk Score</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {(stats.avg_risk_score * 100).toFixed(1)}%
                  </p>
                </div>
                <Shield className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Risk Distribution Chart */}
      {stats && (
        <Card>
          <CardHeader>
            <CardTitle>Risk Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskDistributionData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  >
                    {riskDistributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Transaction Input Form */}
      <Card>
        <CardHeader>
          <CardTitle>Fraud Detection Analysis</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <Label htmlFor="transactionId">Transaction ID</Label>
              <Input
                id="transactionId"
                value={transactionData.transaction_id}
                onChange={(e) => setTransactionData({...transactionData, transaction_id: e.target.value})}
                placeholder="TXN_001"
              />
            </div>
            <div>
              <Label htmlFor="amount">Amount ($)</Label>
              <Input
                id="amount"
                type="number"
                value={transactionData.amount}
                onChange={(e) => setTransactionData({...transactionData, amount: parseFloat(e.target.value) || 0})}
              />
            </div>
            <div>
              <Label htmlFor="numItems">Number of Items</Label>
              <Input
                id="numItems"
                type="number"
                value={transactionData.num_items}
                onChange={(e) => setTransactionData({...transactionData, num_items: parseInt(e.target.value) || 1})}
              />
            </div>
            <div>
              <Label htmlFor="customerAge">Customer Age (days)</Label>
              <Input
                id="customerAge"
                type="number"
                value={transactionData.customer_age_days}
                onChange={(e) => setTransactionData({...transactionData, customer_age_days: parseInt(e.target.value) || 0})}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <Label htmlFor="hour">Hour of Day</Label>
              <Select 
                value={transactionData.hour_of_day.toString()} 
                onChange={(value: string) => setTransactionData({...transactionData, hour_of_day: parseInt(value)})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Array.from({length: 24}, (_, i) => (
                    <SelectItem key={i} value={i.toString()}>{i}:00</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="dayOfWeek">Day of Week</Label>
              <Select 
                value={transactionData.day_of_week.toString()} 
                onChange={(value: string) => setTransactionData({...transactionData, day_of_week: parseInt(value)})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {dayNames.map((day, index) => (
                    <SelectItem key={index} value={index.toString()}>{day}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="paymentMethod">Payment Method</Label>
              <Select 
                value={transactionData.payment_method.toString()} 
                onChange={(value) => setTransactionData({...transactionData, payment_method: parseInt(value)})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {paymentMethods.map((method, index) => (
                    <SelectItem key={index} value={index.toString()}>{method}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="addressMatch">Address Match</Label>
              <Select 
                value={transactionData.shipping_address_matches.toString()} 
                onChange={(value) => setTransactionData({...transactionData, shipping_address_matches: value === 'true'})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Yes</SelectItem>
                  <SelectItem value="false">No</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex space-x-4">
            <Button onClick={trainModel} disabled={training} variant="outline">
              {training ? 'Training...' : 'Train Model'}
            </Button>
            <Button onClick={detectFraud} disabled={loading}>
              {loading ? 'Analyzing...' : 'Detect Fraud'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Fraud Detection Result */}
      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              {getRiskIcon(result.risk_level)}
              <span>Fraud Detection Result</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Risk Level:</span>
                  <Badge variant={getRiskColor(result.risk_level)}>
                    {result.risk_level.toUpperCase()}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-medium">Risk Score:</span>
                  <span className="text-lg font-bold">
                    {(result.risk_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-medium">Fraud Risk:</span>
                  <span className={`font-bold ${result.is_fraud_risk ? 'text-red-600' : 'text-green-600'}`}>
                    {result.is_fraud_risk ? 'YES' : 'NO'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-medium">Anomaly Score:</span>
                  <span className="text-lg font-mono">
                    {result.anomaly_score.toFixed(3)}
                  </span>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">Risk Factors:</h4>
                {result.risk_factors.length > 0 ? (
                  <ul className="space-y-1">
                    {result.risk_factors.map((factor, index) => (
                      <li key={index} className="flex items-center space-x-2">
                        <AlertTriangle className="h-4 w-4 text-yellow-600" />
                        <span className="text-sm">{factor}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-600">No specific risk factors identified</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default FraudDetectionPanel;