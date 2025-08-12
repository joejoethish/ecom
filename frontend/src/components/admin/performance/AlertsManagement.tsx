'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { 
  AlertTriangle, CheckCircle, Clock, Filter, 
  Search, Eye, MessageSquare, X, RefreshCw
} from 'lucide-react';

interface PerformanceAlert {
  id: string;
  name: string;
  description: string;
  metric_type: string;
  threshold_value: number;
  current_value: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'acknowledged' | 'resolved' | 'suppressed';
  triggered_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  acknowledged_by_username?: string;
  duration: number;
  metadata: Record<string, any>;
}

const AlertsManagement: React.FC = () => {
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [filteredAlerts, setFilteredAlerts] = useState<PerformanceAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [selectedAlert, setSelectedAlert] = useState<PerformanceAlert | null>(null);
  const [acknowledgeComment, setAcknowledgeComment] = useState('');
  const [resolveComment, setResolveComment] = useState('');

  useEffect(() => {
    fetchAlerts();
  }, []);

  useEffect(() => {
    filterAlerts();
  }, [alerts, searchTerm, statusFilter, severityFilter]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/performance/alerts/');
      const data = await response.json();
      setAlerts(data.results || []);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterAlerts = () => {
    let filtered = alerts;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(alert =>
        alert.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.metric_type.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(alert => alert.status === statusFilter);
    }

    // Severity filter
    if (severityFilter !== 'all') {
      filtered = filtered.filter(alert => alert.severity === severityFilter);
    }

    setFilteredAlerts(filtered);
  };

  const acknowledgeAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/admin/performance/alerts/${alertId}/acknowledge/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ comment: acknowledgeComment }),
      });

      if (response.ok) {
        fetchAlerts();
        setAcknowledgeComment('');
      }
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  const resolveAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/admin/performance/alerts/${alertId}/resolve/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ comment: resolveComment }),
      });

      if (response.ok) {
        fetchAlerts();
        setResolveComment('');
      }
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500 text-white';
      case 'high': return 'bg-orange-500 text-white';
      case 'medium': return 'bg-yellow-500 text-black';
      case 'low': return 'bg-green-500 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-red-100 text-red-800';
      case 'acknowledged': return 'bg-yellow-100 text-yellow-800';
      case 'resolved': return 'bg-green-100 text-green-800';
      case 'suppressed': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <AlertTriangle className="h-4 w-4" />;
      case 'acknowledged': return <Clock className="h-4 w-4" />;
      case 'resolved': return <CheckCircle className="h-4 w-4" />;
      case 'suppressed': return <X className="h-4 w-4" />;
      default: return <AlertTriangle className="h-4 w-4" />;
    }
  };

  const formatDuration = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes}m`;
    } else if (minutes < 1440) {
      return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
    } else {
      return `${Math.floor(minutes / 1440)}d ${Math.floor((minutes % 1440) / 60)}h`;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading alerts...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Performance Alerts</h1>
          <p className="text-gray-600">Monitor and manage performance alerts</p>
        </div>
        <Button onClick={fetchAlerts}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search alerts..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={statusFilter} onChange={setStatusFilter}>
              <SelectTrigger className="w-full md:w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="acknowledged">Acknowledged</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                <SelectItem value="suppressed">Suppressed</SelectItem>
              </SelectContent>
            </Select>
            <Select value={severityFilter} onChange={setSeverityFilter}>
              <SelectTrigger className="w-full md:w-48">
                <SelectValue placeholder="Filter by severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severities</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Alerts Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {['active', 'acknowledged', 'resolved', 'critical'].map((type) => {
          const count = type === 'critical' 
            ? alerts.filter(a => a.severity === 'critical').length
            : alerts.filter(a => a.status === type).length;
          
          return (
            <Card key={type}>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 capitalize">
                      {type} {type === 'critical' ? 'Severity' : 'Alerts'}
                    </p>
                    <p className="text-2xl font-bold">{count}</p>
                  </div>
                  {getStatusIcon(type)}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Alerts List */}
      <Card>
        <CardHeader>
          <CardTitle>Alerts ({filteredAlerts.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredAlerts.map((alert) => (
              <div key={alert.id} className="border rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <Badge className={getSeverityColor(alert.severity)}>
                        {alert.severity}
                      </Badge>
                      <Badge variant="outline" className={getStatusColor(alert.status)}>
                        {getStatusIcon(alert.status)}
                        <span className="ml-1">{alert.status}</span>
                      </Badge>
                      <span className="text-sm text-gray-500">
                        {formatDuration(alert.duration)}
                      </span>
                    </div>
                    
                    <h3 className="font-semibold text-lg mb-1">{alert.name}</h3>
                    <p className="text-gray-600 mb-2">{alert.description}</p>
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>Metric: {alert.metric_type}</span>
                      <span>Current: {alert.current_value.toFixed(2)}</span>
                      <span>Threshold: {alert.threshold_value.toFixed(2)}</span>
                      <span>Triggered: {new Date(alert.triggered_at).toLocaleString()}</span>
                    </div>
                    
                    {alert.acknowledged_by_username && (
                      <p className="text-sm text-gray-500 mt-1">
                        Acknowledged by {alert.acknowledged_by_username} at{' '}
                        {alert.acknowledged_at && new Date(alert.acknowledged_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm" onClick={() => setSelectedAlert(alert)}>
                          <Eye className="h-4 w-4" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl">
                        <DialogHeader>
                          <DialogTitle>Alert Details</DialogTitle>
                        </DialogHeader>
                        {selectedAlert && (
                          <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label className="text-sm font-medium">Name</label>
                                <p>{selectedAlert.name}</p>
                              </div>
                              <div>
                                <label className="text-sm font-medium">Severity</label>
                                <Badge className={getSeverityColor(selectedAlert.severity)}>
                                  {selectedAlert.severity}
                                </Badge>
                              </div>
                              <div>
                                <label className="text-sm font-medium">Status</label>
                                <Badge variant="outline" className={getStatusColor(selectedAlert.status)}>
                                  {selectedAlert.status}
                                </Badge>
                              </div>
                              <div>
                                <label className="text-sm font-medium">Duration</label>
                                <p>{formatDuration(selectedAlert.duration)}</p>
                              </div>
                            </div>
                            
                            <div>
                              <label className="text-sm font-medium">Description</label>
                              <p>{selectedAlert.description}</p>
                            </div>
                            
                            <div className="grid grid-cols-3 gap-4">
                              <div>
                                <label className="text-sm font-medium">Metric Type</label>
                                <p>{selectedAlert.metric_type}</p>
                              </div>
                              <div>
                                <label className="text-sm font-medium">Current Value</label>
                                <p>{selectedAlert.current_value.toFixed(2)}</p>
                              </div>
                              <div>
                                <label className="text-sm font-medium">Threshold</label>
                                <p>{selectedAlert.threshold_value.toFixed(2)}</p>
                              </div>
                            </div>
                            
                            {selectedAlert.metadata && Object.keys(selectedAlert.metadata).length > 0 && (
                              <div>
                                <label className="text-sm font-medium">Metadata</label>
                                <pre className="bg-gray-100 p-2 rounded text-sm">
                                  {JSON.stringify(selectedAlert.metadata, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        )}
                      </DialogContent>
                    </Dialog>
                    
                    {alert.status === 'active' && (
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="outline" size="sm">
                            <MessageSquare className="h-4 w-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Acknowledge Alert</DialogTitle>
                          </DialogHeader>
                          <div className="space-y-4">
                            <Textarea
                              placeholder="Add a comment (optional)..."
                              value={acknowledgeComment}
                              onChange={(e) => setAcknowledgeComment(e.target.value)}
                            />
                            <div className="flex justify-end space-x-2">
                              <Button variant="outline">Cancel</Button>
                              <Button onClick={() => acknowledgeAlert(alert.id)}>
                                Acknowledge
                              </Button>
                            </div>
                          </div>
                        </DialogContent>
                      </Dialog>
                    )}
                    
                    {alert.status === 'acknowledged' && (
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="outline" size="sm">
                            <CheckCircle className="h-4 w-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Resolve Alert</DialogTitle>
                          </DialogHeader>
                          <div className="space-y-4">
                            <Textarea
                              placeholder="Resolution details..."
                              value={resolveComment}
                              onChange={(e) => setResolveComment(e.target.value)}
                            />
                            <div className="flex justify-end space-x-2">
                              <Button variant="outline">Cancel</Button>
                              <Button onClick={() => resolveAlert(alert.id)}>
                                Resolve
                              </Button>
                            </div>
                          </div>
                        </DialogContent>
                      </Dialog>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {filteredAlerts.length === 0 && (
              <div className="text-center py-8">
                <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No alerts found matching your criteria</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AlertsManagement;