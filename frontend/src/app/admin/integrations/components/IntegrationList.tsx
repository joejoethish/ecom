import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Play, 
  Pause, 
  RefreshCw, 
  Settings, 
  Trash2, 
  ExternalLink,
  MoreVertical,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react';

interface Integration {
  id: string;
  name: string;
  provider_name: string;
  provider_logo: string;
  category_name: string;
  status: 'active' | 'inactive' | 'error' | 'testing' | 'pending';
  environment: 'production' | 'sandbox' | 'development';
  health_status: 'healthy' | 'warning' | 'critical' | 'inactive';
  last_sync_at: string | null;
  last_sync_status: string | null;
  error_count: number;
  created_at: string;
  created_by_name: string;
}

interface IntegrationListProps {
  integrations: Integration[];
  loading: boolean;
  onTest: (id: string) => void;
  onSync: (id: string) => void;
  onEdit: (id: string, data: any) => void;
  onDelete: (id: string) => void;
  getStatusColor: (status: string) => string;
  getHealthStatusIcon: (status: string) => React.ReactNode;
}

export default function IntegrationList({
  integrations,
  loading,
  onTest,
  onSync,
  onEdit,
  onDelete,
  getStatusColor,
  getHealthStatusIcon
}: IntegrationListProps) {
  const [selectedIntegrations, setSelectedIntegrations] = useState<string[]>([]);

  const handleSelectIntegration = (id: string) => {
    setSelectedIntegrations(prev => 
      prev.includes(id) 
        ? prev.filter(item => item !== id)
        : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedIntegrations.length === integrations.length) {
      setSelectedIntegrations([]);
    } else {
      setSelectedIntegrations(integrations.map(integration => integration.id));
    }
  };

  const formatLastSync = (lastSyncAt: string | null) => {
    if (!lastSyncAt) return 'Never';
    
    const date = new Date(lastSyncAt);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays}d ago`;
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                  <div className="w-20 h-6 bg-gray-200 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (integrations.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <Settings className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No integrations found</h3>
          <p className="text-gray-500 mb-4">
            Get started by adding your first integration from the marketplace.
          </p>
          <Button>Browse Marketplace</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Bulk Actions */}
      {selectedIntegrations.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                {selectedIntegrations.length} integration(s) selected
              </span>
              <div className="flex space-x-2">
                <Button variant="outline" size="sm">
                  <Play className="h-4 w-4 mr-2" />
                  Activate
                </Button>
                <Button variant="outline" size="sm">
                  <Pause className="h-4 w-4 mr-2" />
                  Deactivate
                </Button>
                <Button variant="outline" size="sm">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Sync
                </Button>
                <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Integrations List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Integrations ({integrations.length})</CardTitle>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedIntegrations.length === integrations.length}
                onChange={handleSelectAll}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-500">Select All</span>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-gray-200">
            {integrations.map((integration) => (
              <div key={integration.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-center space-x-4">
                  {/* Selection Checkbox */}
                  <input
                    type="checkbox"
                    checked={selectedIntegrations.includes(integration.id)}
                    onChange={() => handleSelectIntegration(integration.id)}
                    className="rounded border-gray-300"
                  />

                  {/* Provider Logo */}
                  <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                    {integration.provider_logo ? (
                      <img
                        src={integration.provider_logo}
                        alt={integration.provider_name}
                        className="w-8 h-8 object-contain"
                      />
                    ) : (
                      <Settings className="h-6 w-6 text-gray-400" />
                    )}
                  </div>

                  {/* Integration Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <h3 className="text-lg font-medium text-gray-900 truncate">
                        {integration.name}
                      </h3>
                      {getHealthStatusIcon(integration.health_status)}
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>{integration.provider_name}</span>
                      <span>•</span>
                      <span>{integration.category_name}</span>
                      <span>•</span>
                      <span className="capitalize">{integration.environment}</span>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                      <span>Last sync: {formatLastSync(integration.last_sync_at)}</span>
                      {integration.error_count > 0 && (
                        <>
                          <span>•</span>
                          <span className="text-red-600">
                            {integration.error_count} error(s)
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div className="flex flex-col items-end space-y-2">
                    <Badge className={getStatusColor(integration.status)}>
                      {integration.status}
                    </Badge>
                    {integration.last_sync_status && (
                      <Badge variant="outline" className="text-xs">
                        {integration.last_sync_status}
                      </Badge>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onTest(integration.id)}
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Test
                    </Button>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onSync(integration.id)}
                    >
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Sync
                    </Button>

                    <div className="relative">
                      <Button variant="outline" size="sm">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                      {/* Dropdown menu would go here */}
                    </div>
                  </div>
                </div>

                {/* Additional Details (expandable) */}
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Created by:</span>
                      <p className="font-medium">{integration.created_by_name}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Created:</span>
                      <p className="font-medium">
                        {new Date(integration.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500">Environment:</span>
                      <p className="font-medium capitalize">{integration.environment}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Health:</span>
                      <div className="flex items-center space-x-1">
                        {getHealthStatusIcon(integration.health_status)}
                        <span className="font-medium capitalize">
                          {integration.health_status}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}