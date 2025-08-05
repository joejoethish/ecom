'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/card';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { 
  AlertTriangle, 
  Bell, 
  Check, 
  X, 
  Settings, 
  Clock,
  RefreshCw
} from 'lucide-react';
import { 
  inventoryManagementApi, 
  type StockAlert, 
  type AlertFilters 
} from '@/services/inventoryManagementApi';
import { useInventoryAuth, InventoryPermission, InventoryPermissionGate } from '@/utils/inventoryAuth';
import { useInventoryAlertNotifications } from '@/utils/inventoryNotifications';

interface StockAlertsProps {
  className?: string;
}

export default function StockAlerts({ className = '' }: StockAlertsProps) {
  // Authentication and permissions
  const auth = useInventoryAuth();
  const notifications = useInventoryAlertNotifications();
  
  const [alerts, setAlerts] = useState<StockAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<StockAlert | null>(null);
  const [showAlertDetails, setShowAlertDetails] = useState(false);
  const [showConfiguration, setShowConfiguration] = useState(false);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    page_size: 20,
    total_pages: 0,
    current_page: 1
  });

  const [filters, setFilters] = useState<AlertFilters>({
    alert_type: undefined,
    priority: undefined,
    is_acknowledged: undefined,
    warehouse: '',
    page: 1,
    page_size: 20,
    ordering: '-created_at'
  });

  const [warehouses, setWarehouses] = useState<Array<{ id: string; name: string; code: string }>>([]);
  const [alertStats, setAlertStats] = useState({
    total_alerts: 0,
    critical_alerts: 0,
    high_priority_alerts: 0,
    unacknowledged_alerts: 0
  });

  // WebSocket connection for real-time updates
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    fetchAlerts();
    fetchWarehouses();
    setupWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [filters]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await inventoryManagementApi.getAlerts(filters);
      
      if (response.success && response.data) {
        setAlerts(response.data.results);
        setPagination({
          count: response.data.results.length,
          next: null,
          previous: null,
          page_size: filters.page_size || 20,
          total_pages: Math.ceil(response.data.results.length / (filters.page_size || 20)),
          current_page: filters.page || 1
        });

        // Update alert stats
        const stats = response.data.results.reduce((acc, alert) => {
          acc.total_alerts++;
          if (alert.priority === 'critical') acc.critical_alerts++;
          if (alert.priority === 'high') acc.high_priority_alerts++;
          if (!alert.is_acknowledged) acc.unacknowledged_alerts++;
          return acc;
        }, {
          total_alerts: 0,
          critical_alerts: 0,
          high_priority_alerts: 0,
          unacknowledged_alerts: 0
        });
        setAlertStats(stats);
      }
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchWarehouses = async () => {
    try {
      const response = await inventoryManagementApi.getWarehouses();
      if (response.success && response.data) {
        setWarehouses(response.data.map((w: any) => ({ 
          id: w.id, 
          name: w.name, 
          code: w.code 
        })));
      }
    } catch (error) {
      console.error('Failed to fetch warehouses:', error);
    }
  };

  const setupWebSocket = () => {
    if (!auth.canViewAlerts) return;

    try {
      const wsUrl = `ws://localhost:8000/ws/inventory/alerts/`;
      const websocket = new WebSocket(wsUrl);
      
      websocket.onopen = () => {
        console.log('WebSocket connected for stock alerts');
      };
      
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'stock_alert') {
          // Process new alert
          notifications.processInventoryNotification(data);
          fetchAlerts(); // Refresh alerts list
        }
      };
      
      websocket.onclose = () => {
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 5 seconds
        setTimeout(setupWebSocket, 5000);
      };
      
      setWs(websocket);
    } catch (error) {
      console.error('Failed to setup WebSocket:', error);
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      const response = await inventoryManagementApi.acknowledgeAlert(alertId);
      if (response.success) {
        fetchAlerts(); // Refresh the list
        notifications.markAsRead(alertId);
      }
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const handleDismissAlert = async (alertId: string) => {
    try {
      const response = await inventoryManagementApi.dismissAlert(alertId);
      if (response.success) {
        fetchAlerts(); // Refresh the list
      }
    } catch (error) {
      console.error('Failed to dismiss alert:', error);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchAlerts();
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getAlertTypeIcon = (alertType: string) => {
    switch (alertType) {
      case 'low_stock': return <AlertTriangle className="h-4 w-4" />;
      case 'out_of_stock': return <X className="h-4 w-4" />;
      case 'expiring_batch': return <Clock className="h-4 w-4" />;
      default: return <Bell className="h-4 w-4" />;
    }
  };

  if (!auth.canViewAlerts) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
        <AlertTriangle className="h-16 w-16 text-red-600 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Access Denied</h2>
        <p className="text-gray-600">
          You don't have permission to view stock alerts.
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Alert Statistics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <Bell className="h-5 w-5 text-blue-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Total Alerts</p>
              <p className="text-2xl font-bold">{alertStats.total_alerts}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Critical</p>
              <p className="text-2xl font-bold text-red-600">{alertStats.critical_alerts}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-orange-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">High Priority</p>
              <p className="text-2xl font-bold text-orange-600">{alertStats.high_priority_alerts}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <Clock className="h-5 w-5 text-yellow-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Unacknowledged</p>
              <p className="text-2xl font-bold text-yellow-600">{alertStats.unacknowledged_alerts}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters and Actions */}
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="flex flex-col sm:flex-row gap-3 flex-1">
          <Select
            value={filters.alert_type || ''}
            onChange={(e) => setFilters({ ...filters, alert_type: e.target.value as any })}
            className="min-w-[160px]"
          >
            <option value="">All Alert Types</option>
            <option value="low_stock">Low Stock</option>
            <option value="out_of_stock">Out of Stock</option>
            <option value="expiring_batch">Expiring Batch</option>
          </Select>
          
          <Select
            value={filters.priority || ''}
            onChange={(e) => setFilters({ ...filters, priority: e.target.value as any })}
            className="min-w-[140px]"
          >
            <option value="">All Priorities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </Select>
          
          <Select
            value={filters.warehouse || ''}
            onChange={(e) => setFilters({ ...filters, warehouse: e.target.value })}
            className="min-w-[160px]"
          >
            <option value="">All Warehouses</option>
            {warehouses.map((warehouse) => (
              <option key={warehouse.id} value={warehouse.id}>
                {warehouse.name} ({warehouse.code})
              </option>
            ))}
          </Select>
          
          <Select
            value={filters.is_acknowledged?.toString() || ''}
            onChange={(e) => setFilters({ 
              ...filters, 
              is_acknowledged: e.target.value === '' ? undefined : e.target.value === 'true'
            })}
            className="min-w-[140px]"
          >
            <option value="">All Status</option>
            <option value="false">Unacknowledged</option>
            <option value="true">Acknowledged</option>
          </Select>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <InventoryPermissionGate permissions={[InventoryPermission.CONFIGURE_ALERTS]}>
            <Button
              onClick={() => setShowConfiguration(true)}
              className="flex items-center gap-2"
            >
              <Settings className="h-4 w-4" />
              Configure
            </Button>
          </InventoryPermissionGate>
        </div>
      </div>

      {/* Alerts List */}
      <Card>
        {loading ? (
          <div className="p-8 text-center">
            <LoadingSpinner />
            <p className="mt-2 text-gray-600">Loading alerts...</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="p-8 text-center">
            <Bell className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No alerts found</h3>
            <p className="text-gray-600">
              {Object.values(filters).some(v => v !== undefined && v !== '') 
                ? 'Try adjusting your filters to see more alerts.'
                : 'All your inventory levels are looking good!'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {alerts.map((alert) => (
              <div key={alert.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {getAlertTypeIcon(alert.alert_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <Badge className={getPriorityColor(alert.priority)}>
                          {alert.priority.toUpperCase()}
                        </Badge>
                        <span className="text-sm text-gray-500">
                          {alert.alert_type.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-gray-900 mb-1">
                        {alert.inventory_item.product_variant.product.name}
                      </p>
                      <p className="text-sm text-gray-600 mb-2">
                        SKU: {alert.inventory_item.product_variant.sku} • 
                        Warehouse: {alert.inventory_item.warehouse.name}
                      </p>
                      <p className="text-sm text-gray-700">{alert.message}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(alert.created_at).toLocaleString()}
                        {alert.is_acknowledged && alert.acknowledged_by && (
                          <span className="ml-2">
                            • Acknowledged by {alert.acknowledged_by.username}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-4">
                    {!alert.is_acknowledged && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleAcknowledgeAlert(alert.id)}
                        className="flex items-center gap-1"
                      >
                        <Check className="h-3 w-3" />
                        Acknowledge
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDismissAlert(alert.id)}
                      className="flex items-center gap-1 text-red-600 hover:text-red-700"
                    >
                      <X className="h-3 w-3" />
                      Dismiss
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Pagination */}
      {pagination.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-700">
            Showing {((pagination.current_page - 1) * pagination.page_size) + 1} to{' '}
            {Math.min(pagination.current_page * pagination.page_size, pagination.count)} of{' '}
            {pagination.count} alerts
          </p>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setFilters({ ...filters, page: pagination.current_page - 1 })}
              disabled={!pagination.previous}
            >
              Previous
            </Button>
            <span className="text-sm text-gray-700">
              Page {pagination.current_page} of {pagination.total_pages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setFilters({ ...filters, page: pagination.current_page + 1 })}
              disabled={!pagination.next}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}