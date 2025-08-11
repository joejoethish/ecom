'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  AlertTriangle, TrendingUp, TrendingDown, Brain, Target, 
  CheckCircle, Clock, Eye, EyeOff, RefreshCw, Filter,
  Lightbulb, BarChart3, Users, DollarSign, Package
} from 'lucide-react';

interface BIInsightsProps {
  dataSourceId?: string;
}

interface Insight {
  id: string;
  title: string;
  description: string;
  insight_type: 'anomaly' | 'trend' | 'correlation' | 'forecast' | 'threshold' | 'pattern' | 'recommendation' | 'alert';
  severity: 'low' | 'medium' | 'high' | 'critical';
  data_source_name?: string;
  metric_name: string;
  current_value?: number;
  expected_value?: number;
  deviation_percentage?: number;
  confidence_score: number;
  metadata?: any;
  action_items: string[];
  is_acknowledged: boolean;
  acknowledged_by_name?: string;
  acknowledged_at?: string;
  is_resolved: boolean;
  resolution_notes?: string;
  created_at: string;
  age_hours: number;
}

const INSIGHT_TYPE_ICONS = {
  anomaly: AlertTriangle,
  trend: TrendingUp,
  correlation: BarChart3,
  forecast: Target,
  threshold: AlertTriangle,
  pattern: Brain,
  recommendation: Lightbulb,
  alert: AlertTriangle
};

const INSIGHT_TYPE_COLORS = {
  anomaly: 'text-red-500',
  trend: 'text-blue-500',
  correlation: 'text-purple-500',
  forecast: 'text-green-500',
  threshold: 'text-orange-500',
  pattern: 'text-indigo-500',
  recommendation: 'text-yellow-500',
  alert: 'text-red-500'
};

const SEVERITY_COLORS = {
  low: 'bg-blue-100 text-blue-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800'
};

export default function BIInsights({ dataSourceId }: BIInsightsProps) {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState('all');
  const [filters, setFilters] = useState({
    insight_type: '',
    severity: '',
    is_acknowledged: ''
  });
  const [generatingInsights, setGeneratingInsights] = useState(false);

  const fetchInsights = useCallback(async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (filters.insight_type) params.append('insight_type', filters.insight_type);
      if (filters.severity) params.append('severity', filters.severity);
      if (filters.is_acknowledged) params.append('is_acknowledged', filters.is_acknowledged);

      const response = await fetch(`/api/analytics/bi/insights/?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch insights');
      
      const data = await response.json();
      setInsights(data.results || data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const generateInsights = async () => {
    try {
      setGeneratingInsights(true);
      
      const response = await fetch('/api/analytics/bi/insights/generate_insights/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          data_source_id: dataSourceId,
          insight_types: ['anomaly', 'trend', 'pattern'],
          date_range: '30d',
          confidence_threshold: 70.0
        })
      });

      if (!response.ok) throw new Error('Failed to generate insights');
      
      const data = await response.json();
      
      // Refresh insights list
      await fetchInsights();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate insights');
    } finally {
      setGeneratingInsights(false);
    }
  };

  const acknowledgeInsight = async (insightId: string) => {
    try {
      const response = await fetch(`/api/analytics/bi/insights/${insightId}/acknowledge_insight/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to acknowledge insight');
      
      // Update local state
      setInsights(prev => prev.map(insight => 
        insight.id === insightId 
          ? { ...insight, is_acknowledged: true, acknowledged_at: new Date().toISOString() }
          : insight
      ));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to acknowledge insight');
    }
  };

  const resolveInsight = async (insightId: string, resolutionNotes: string) => {
    try {
      const response = await fetch(`/api/analytics/bi/insights/${insightId}/resolve_insight/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ resolution_notes: resolutionNotes })
      });

      if (!response.ok) throw new Error('Failed to resolve insight');
      
      // Update local state
      setInsights(prev => prev.map(insight => 
        insight.id === insightId 
          ? { ...insight, is_resolved: true, resolution_notes: resolutionNotes }
          : insight
      ));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve insight');
    }
  };

  useEffect(() => {
    fetchInsights();
  }, [fetchInsights]);

  const filteredInsights = insights.filter(insight => {
    if (selectedTab === 'unacknowledged') return !insight.is_acknowledged;
    if (selectedTab === 'acknowledged') return insight.is_acknowledged && !insight.is_resolved;
    if (selectedTab === 'resolved') return insight.is_resolved;
    return true; // 'all' tab
  });

  const getInsightIcon = (type: string) => {
    const IconComponent = INSIGHT_TYPE_ICONS[type as keyof typeof INSIGHT_TYPE_ICONS] || Brain;
    return IconComponent;
  };

  const getInsightColor = (type: string) => {
    return INSIGHT_TYPE_COLORS[type as keyof typeof INSIGHT_TYPE_COLORS] || 'text-gray-500';
  };

  const getSeverityBadge = (severity: string) => {
    const colorClass = SEVERITY_COLORS[severity as keyof typeof SEVERITY_COLORS] || 'bg-gray-100 text-gray-800';
    return (
      <Badge className={colorClass}>
        {severity.toUpperCase()}
      </Badge>
    );
  };

  const renderInsightCard = (insight: Insight) => {
    const IconComponent = getInsightIcon(insight.insight_type);
    const iconColor = getInsightColor(insight.insight_type);

    return (
      <Card key={insight.id} className={`mb-4 ${insight.severity === 'critical' ? 'border-red-500' : ''}`}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <IconComponent className={`w-5 h-5 mt-1 ${iconColor}`} />
              <div className="flex-1">
                <CardTitle className="text-lg">{insight.title}</CardTitle>
                <div className="flex items-center space-x-2 mt-1">
                  {getSeverityBadge(insight.severity)}
                  <Badge variant="outline">{insight.insight_type}</Badge>
                  <span className="text-sm text-gray-500">
                    {insight.age_hours < 1 ? 'Just now' : `${Math.floor(insight.age_hours)}h ago`}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {insight.is_resolved ? (
                <Badge className="bg-green-100 text-green-800">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Resolved
                </Badge>
              ) : insight.is_acknowledged ? (
                <Badge className="bg-blue-100 text-blue-800">
                  <Eye className="w-3 h-3 mr-1" />
                  Acknowledged
                </Badge>
              ) : (
                <Badge className="bg-gray-100 text-gray-800">
                  <EyeOff className="w-3 h-3 mr-1" />
                  New
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-gray-700 mb-4">{insight.description}</p>
          
          {/* Metrics */}
          {(insight.current_value !== undefined || insight.expected_value !== undefined) && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 p-3 bg-gray-50 rounded-lg">
              {insight.current_value !== undefined && (
                <div>
                  <p className="text-sm text-gray-600">Current Value</p>
                  <p className="font-semibold">{insight.current_value.toLocaleString()}</p>
                </div>
              )}
              {insight.expected_value !== undefined && (
                <div>
                  <p className="text-sm text-gray-600">Expected Value</p>
                  <p className="font-semibold">{insight.expected_value.toLocaleString()}</p>
                </div>
              )}
              {insight.deviation_percentage !== undefined && (
                <div>
                  <p className="text-sm text-gray-600">Deviation</p>
                  <p className="font-semibold text-red-600">{insight.deviation_percentage.toFixed(1)}%</p>
                </div>
              )}
              <div>
                <p className="text-sm text-gray-600">Confidence</p>
                <p className="font-semibold">{insight.confidence_score.toFixed(1)}%</p>
              </div>
            </div>
          )}

          {/* Action Items */}
          {insight.action_items && insight.action_items.length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold mb-2">Recommended Actions:</h4>
              <ul className="list-disc list-inside space-y-1">
                {insight.action_items.map((action, index) => (
                  <li key={index} className="text-sm text-gray-700">{action}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Resolution Notes */}
          {insight.is_resolved && insight.resolution_notes && (
            <div className="mb-4 p-3 bg-green-50 rounded-lg">
              <h4 className="font-semibold text-green-800 mb-1">Resolution Notes:</h4>
              <p className="text-sm text-green-700">{insight.resolution_notes}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {insight.data_source_name && (
                <span>Source: {insight.data_source_name}</span>
              )}
            </div>
            <div className="flex items-center space-x-2">
              {!insight.is_acknowledged && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => acknowledgeInsight(insight.id)}
                >
                  <Eye className="w-4 h-4 mr-1" />
                  Acknowledge
                </Button>
              )}
              {insight.is_acknowledged && !insight.is_resolved && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    const notes = prompt('Enter resolution notes:');
                    if (notes) resolveInsight(insight.id, notes);
                  }}
                >
                  <CheckCircle className="w-4 h-4 mr-1" />
                  Resolve
                </Button>
              )}
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
        <span>Loading insights...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Business Intelligence Insights</h1>
          <p className="text-gray-600">Automated insights and anomaly detection</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            onClick={generateInsights}
            disabled={generatingInsights}
          >
            {generatingInsights ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Brain className="w-4 h-4 mr-2" />
            )}
            Generate Insights
          </Button>
          <Button variant="outline" onClick={fetchInsights}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Insight Type</label>
              <select
                value={filters.insight_type}
                onChange={(e) => setFilters(prev => ({ ...prev, insight_type: e.target.value }))}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="">All Types</option>
                <option value="anomaly">Anomaly</option>
                <option value="trend">Trend</option>
                <option value="pattern">Pattern</option>
                <option value="recommendation">Recommendation</option>
                <option value="alert">Alert</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Severity</label>
              <select
                value={filters.severity}
                onChange={(e) => setFilters(prev => ({ ...prev, severity: e.target.value }))}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="">All Severities</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Status</label>
              <select
                value={filters.is_acknowledged}
                onChange={(e) => setFilters(prev => ({ ...prev, is_acknowledged: e.target.value }))}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="">All Status</option>
                <option value="false">Unacknowledged</option>
                <option value="true">Acknowledged</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Insights Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="all">
            All ({insights.length})
          </TabsTrigger>
          <TabsTrigger value="unacknowledged">
            New ({insights.filter(i => !i.is_acknowledged).length})
          </TabsTrigger>
          <TabsTrigger value="acknowledged">
            Acknowledged ({insights.filter(i => i.is_acknowledged && !i.is_resolved).length})
          </TabsTrigger>
          <TabsTrigger value="resolved">
            Resolved ({insights.filter(i => i.is_resolved).length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value={selectedTab} className="mt-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
                <span className="text-red-700">{error}</span>
              </div>
            </div>
          )}

          {filteredInsights.length === 0 ? (
            <div className="text-center py-12">
              <Brain className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No insights found</h3>
              <p className="text-gray-500 mb-4">
                {selectedTab === 'all' 
                  ? 'Generate insights to see automated analysis and recommendations.'
                  : `No ${selectedTab} insights available.`
                }
              </p>
              {selectedTab === 'all' && (
                <Button onClick={generateInsights} disabled={generatingInsights}>
                  <Brain className="w-4 h-4 mr-2" />
                  Generate Insights
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {filteredInsights.map(renderInsightCard)}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}