'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import { DatePicker } from '@/components/ui/date-picker';
import { Textarea } from '@/components/ui/textarea';
import { 
  FileText, Download, Calendar, TrendingUp, 
  BarChart3, PieChart, Activity, Database,
  RefreshCw, Plus, Eye, Settings
} from 'lucide-react';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

interface PerformanceReport {
  id: string;
  name: string;
  report_type: string;
  date_range_start: string;
  date_range_end: string;
  metrics_included: string[];
  report_data: Record<string, any>;
  insights_parsed: any[];
  recommendations_parsed: any[];
  generated_at: string;
  generated_by_username: string;
  is_scheduled: boolean;
}

interface CapacityForecast {
  historical_data: number[];
  forecast: number[];
  trend: string;
  slope: number;
  confidence: number;
}

interface CapacityRecommendation {
  type: string;
  resource: string;
  message: string;
  recommendation: string;
  urgency: string;
}

const PerformanceReports: React.FC = () => {
  const [reports, setReports] = useState<PerformanceReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedReport, setSelectedReport] = useState<PerformanceReport | null>(null);
  const [capacityData, setCapacityData] = useState<{
    forecasts: Record<string, CapacityForecast>;
    recommendations: CapacityRecommendation[];
  } | null>(null);

  // Report generation form state
  const [reportForm, setReportForm] = useState({
    report_type: 'custom',
    start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
    end_date: new Date(),
    metrics_included: ['response_time', 'database', 'system_metrics']
  });

  useEffect(() => {
    fetchReports();
    fetchCapacityPlanning();
  }, []);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/performance/reports/');
      const data = await response.json();
      setReports(data.results || []);
    } catch (error) {
      console.error('Error fetching reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCapacityPlanning = async () => {
    try {
      const response = await fetch('/api/admin/performance/reports/capacity_planning/');
      const data = await response.json();
      setCapacityData(data);
    } catch (error) {
      console.error('Error fetching capacity planning data:', error);
    }
  };

  const generateReport = async () => {
    try {
      setGenerating(true);
      const response = await fetch('/api/admin/performance/reports/generate_report/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          report_type: reportForm.report_type,
          start_date: reportForm.start_date.toISOString(),
          end_date: reportForm.end_date.toISOString(),
          metrics_included: reportForm.metrics_included,
        }),
      });

      if (response.ok) {
        const newReport = await response.json();
        setReports([newReport, ...reports]);
      }
    } catch (error) {
      console.error('Error generating report:', error);
    } finally {
      setGenerating(false);
    }
  };

  const downloadReport = async (reportId: string) => {
    try {
      const response = await fetch(`/api/admin/performance/reports/${reportId}/download/`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `performance-report-${reportId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };

  const getReportTypeIcon = (type: string) => {
    switch (type) {
      case 'daily': return <Calendar className="h-4 w-4" />;
      case 'weekly': return <BarChart3 className="h-4 w-4" />;
      case 'monthly': return <TrendingUp className="h-4 w-4" />;
      case 'sla': return <Activity className="h-4 w-4" />;
      case 'capacity': return <Database className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'critical': return 'bg-red-500 text-white';
      case 'high': return 'bg-orange-500 text-white';
      case 'medium': return 'bg-yellow-500 text-black';
      case 'low': return 'bg-green-500 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  const renderCapacityChart = (metric: string, data: CapacityForecast) => {
    const chartData = [
      ...data.historical_data.map((value, index) => ({
        day: index - data.historical_data.length + 1,
        historical: value,
        forecast: null,
        type: 'historical'
      })),
      ...data.forecast.map((value, index) => ({
        day: index + 1,
        historical: null,
        forecast: value,
        type: 'forecast'
      }))
    ];

    return (
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="day" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="historical" 
            stroke="#8884d8" 
            strokeWidth={2}
            name="Historical"
            connectNulls={false}
          />
          <Line 
            type="monotone" 
            dataKey="forecast" 
            stroke="#82ca9d" 
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Forecast"
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading reports...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Performance Reports</h1>
          <p className="text-gray-600">Generate and analyze performance reports</p>
        </div>
        <div className="flex space-x-2">
          <Dialog>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Generate Report
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Generate Performance Report</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Report Type</label>
                    <Select 
                      value={reportForm.report_type} 
                      onValueChange={(value) => setReportForm({...reportForm, report_type: value})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="custom">Custom Report</SelectItem>
                        <SelectItem value="daily">Daily Report</SelectItem>
                        <SelectItem value="weekly">Weekly Report</SelectItem>
                        <SelectItem value="monthly">Monthly Report</SelectItem>
                        <SelectItem value="sla">SLA Report</SelectItem>
                        <SelectItem value="capacity">Capacity Report</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Date Range</label>
                    <div className="flex space-x-2">
                      <DatePicker
                        date={reportForm.start_date}
                        onDateChange={(date) => setReportForm({...reportForm, start_date: date || new Date()})}
                      />
                      <DatePicker
                        date={reportForm.end_date}
                        onDateChange={(date) => setReportForm({...reportForm, end_date: date || new Date()})}
                      />
                    </div>
                  </div>
                </div>
                
                <div>
                  <label className="text-sm font-medium">Metrics to Include</label>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {[
                      { id: 'response_time', label: 'Response Time' },
                      { id: 'database', label: 'Database Performance' },
                      { id: 'system_metrics', label: 'System Metrics' },
                      { id: 'errors', label: 'Error Analysis' },
                      { id: 'user_experience', label: 'User Experience' },
                      { id: 'capacity', label: 'Capacity Planning' }
                    ].map((metric) => (
                      <div key={metric.id} className="flex items-center space-x-2">
                        <Checkbox
                          id={metric.id}
                          checked={reportForm.metrics_included.includes(metric.id)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setReportForm({
                                ...reportForm,
                                metrics_included: [...reportForm.metrics_included, metric.id]
                              });
                            } else {
                              setReportForm({
                                ...reportForm,
                                metrics_included: reportForm.metrics_included.filter(m => m !== metric.id)
                              });
                            }
                          }}
                        />
                        <label htmlFor={metric.id} className="text-sm">{metric.label}</label>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="flex justify-end space-x-2">
                  <Button variant="outline">Cancel</Button>
                  <Button onClick={generateReport} disabled={generating}>
                    {generating ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <FileText className="h-4 w-4 mr-2" />
                        Generate Report
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
          <Button variant="outline" onClick={fetchReports}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Capacity Planning Section */}
      {capacityData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="h-5 w-5 mr-2" />
              Capacity Planning & Forecasting
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {Object.entries(capacityData.forecasts).map(([metric, data]) => (
                <div key={metric} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium capitalize">{metric.replace('_', ' ')}</h4>
                    <Badge variant={data.trend === 'increasing' ? 'destructive' : 'secondary'}>
                      {data.trend}
                    </Badge>
                  </div>
                  {renderCapacityChart(metric, data)}
                  <p className="text-sm text-gray-600">
                    Confidence: {data.confidence.toFixed(1)}%
                  </p>
                </div>
              ))}
            </div>
            
            {capacityData.recommendations.length > 0 && (
              <div className="mt-6">
                <h4 className="font-medium mb-3">Capacity Recommendations</h4>
                <div className="space-y-2">
                  {capacityData.recommendations.map((rec, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 border rounded-lg">
                      <Badge className={getUrgencyColor(rec.urgency)}>
                        {rec.urgency}
                      </Badge>
                      <div className="flex-1">
                        <p className="font-medium">{rec.message}</p>
                        <p className="text-sm text-gray-600">{rec.recommendation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Reports List */}
      <Card>
        <CardHeader>
          <CardTitle>Generated Reports ({reports.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {reports.map((report) => (
              <div key={report.id} className="border rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      {getReportTypeIcon(report.report_type)}
                      <h3 className="font-semibold">{report.name}</h3>
                      <Badge variant="outline">
                        {report.report_type}
                      </Badge>
                      {report.is_scheduled && (
                        <Badge variant="secondary">Scheduled</Badge>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-500 mb-2">
                      <span>
                        Period: {new Date(report.date_range_start).toLocaleDateString()} - {new Date(report.date_range_end).toLocaleDateString()}
                      </span>
                      <span>Generated by: {report.generated_by_username}</span>
                      <span>Generated: {new Date(report.generated_at).toLocaleString()}</span>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500">Metrics:</span>
                      {report.metrics_included.map((metric) => (
                        <Badge key={metric} variant="outline" className="text-xs">
                          {metric.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => setSelectedReport(report)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                        <DialogHeader>
                          <DialogTitle>{selectedReport?.name}</DialogTitle>
                        </DialogHeader>
                        {selectedReport && (
                          <div className="space-y-6">
                            {/* Report Summary */}
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label className="text-sm font-medium">Report Type</label>
                                <p>{selectedReport.report_type}</p>
                              </div>
                              <div>
                                <label className="text-sm font-medium">Date Range</label>
                                <p>
                                  {new Date(selectedReport.date_range_start).toLocaleDateString()} - {new Date(selectedReport.date_range_end).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            
                            {/* Insights */}
                            {selectedReport.insights_parsed.length > 0 && (
                              <div>
                                <h4 className="font-medium mb-3">Key Insights</h4>
                                <div className="space-y-2">
                                  {selectedReport.insights_parsed.map((insight, index) => (
                                    <div key={index} className="p-3 border rounded-lg">
                                      <div className="flex items-center space-x-2 mb-1">
                                        <Badge variant={insight.type === 'critical' ? 'destructive' : 'secondary'}>
                                          {insight.type}
                                        </Badge>
                                        <span className="font-medium">{insight.category}</span>
                                      </div>
                                      <p className="text-sm">{insight.message}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {/* Recommendations */}
                            {selectedReport.recommendations_parsed.length > 0 && (
                              <div>
                                <h4 className="font-medium mb-3">Recommendations</h4>
                                <div className="space-y-2">
                                  {selectedReport.recommendations_parsed.map((rec, index) => (
                                    <div key={index} className="p-3 border rounded-lg">
                                      <p className="font-medium">{rec.type}</p>
                                      <p className="text-sm text-gray-600">{rec.recommendation}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {/* Report Data */}
                            {selectedReport.report_data && Object.keys(selectedReport.report_data).length > 0 && (
                              <div>
                                <h4 className="font-medium mb-3">Report Data</h4>
                                <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
                                  {JSON.stringify(selectedReport.report_data, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        )}
                      </DialogContent>
                    </Dialog>
                    
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => downloadReport(report.id)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
            
            {reports.length === 0 && (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No reports generated yet</p>
                <p className="text-sm text-gray-400">Generate your first performance report to get started</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PerformanceReports;