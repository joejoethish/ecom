import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';

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

interface IntegrationStats {
  total_integrations: number;
  active_integrations: number;
  failed_integrations: number;
  total_syncs_today: number;
  successful_syncs_today: number;
  failed_syncs_today: number;
  total_api_calls_today: number;
  average_response_time: number;
  top_providers: Array<{ provider__name: string; count: number }>;
  recent_errors: Array<{
    integration: string;
    message: string;
    created_at: string;
  }>;
}

interface IntegrationCategory {
  id: string;
  name: string;
  category: string;
  description: string;
  icon: string;
  integration_count: number;
}

interface IntegrationProvider {
  id: string;
  name: string;
  slug: string;
  category_name: string;
  description: string;
  website_url: string;
  documentation_url: string;
  logo_url: string;
  status: string;
  supported_features: string[];
  is_popular: boolean;
  integration_count: number;
}

export function useIntegrations() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [stats, setStats] = useState<IntegrationStats | null>(null);
  const [categories, setCategories] = useState<IntegrationCategory[]>([]);
  const [providers, setProviders] = useState<IntegrationProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch integrations
  const fetchIntegrations = async () => {
    try {
      const response = await fetch('/api/integrations/integrations/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to fetch integrations');
      
      const data = await response.json();
      setIntegrations(data.results || data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch integrations');
      toast.error('Failed to load integrations');
    }
  };

  // Fetch stats
  const fetchStats = async () => {
    try {
      const response = await fetch('/api/integrations/integrations/stats/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to fetch stats');
      
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  // Fetch categories
  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/integrations/categories/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to fetch categories');
      
      const data = await response.json();
      setCategories(data.results || data);
    } catch (err) {
      console.error('Failed to fetch categories:', err);
    }
  };

  // Fetch providers
  const fetchProviders = async () => {
    try {
      const response = await fetch('/api/integrations/providers/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to fetch providers');
      
      const data = await response.json();
      setProviders(data.results || data);
    } catch (err) {
      console.error('Failed to fetch providers:', err);
    }
  };

  // Refresh all data
  const refreshIntegrations = async () => {
    setLoading(true);
    await Promise.all([
      fetchIntegrations(),
      fetchStats(),
      fetchCategories(),
      fetchProviders(),
    ]);
    setLoading(false);
  };

  // Create integration
  const createIntegration = async (integrationData: any) => {
    try {
      const response = await fetch('/api/integrations/integrations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`,
        },
        body: JSON.stringify(integrationData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to create integration');
      }

      const newIntegration = await response.json();
      setIntegrations(prev => [newIntegration, ...prev]);
      toast.success('Integration created successfully');
      return newIntegration;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create integration';
      toast.error(message);
      throw err;
    }
  };

  // Update integration
  const updateIntegration = async (id: string, updateData: any) => {
    try {
      const response = await fetch(`/api/integrations/integrations/${id}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`,
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to update integration');
      }

      const updatedIntegration = await response.json();
      setIntegrations(prev => 
        prev.map(integration => 
          integration.id === id ? updatedIntegration : integration
        )
      );
      toast.success('Integration updated successfully');
      return updatedIntegration;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update integration';
      toast.error(message);
      throw err;
    }
  };

  // Delete integration
  const deleteIntegration = async (id: string) => {
    try {
      const response = await fetch(`/api/integrations/integrations/${id}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete integration');
      }

      setIntegrations(prev => prev.filter(integration => integration.id !== id));
      toast.success('Integration deleted successfully');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete integration';
      toast.error(message);
      throw err;
    }
  };

  // Test integration connection
  const testIntegration = async (id: string) => {
    try {
      const response = await fetch(`/api/integrations/integrations/${id}/test_connection/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to test integration');
      }

      const result = await response.json();
      toast.success('Connection test started');
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to test integration';
      toast.error(message);
      throw err;
    }
  };

  // Sync integration data
  const syncIntegration = async (id: string, syncType: string = 'incremental') => {
    try {
      const response = await fetch(`/api/integrations/integrations/${id}/sync_data/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`,
        },
        body: JSON.stringify({ sync_type: syncType }),
      });

      if (!response.ok) {
        throw new Error('Failed to sync integration');
      }

      const result = await response.json();
      toast.success('Data sync started');
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to sync integration';
      toast.error(message);
      throw err;
    }
  };

  // Bulk actions
  const bulkAction = async (integrationIds: string[], action: string, parameters?: any) => {
    try {
      const response = await fetch('/api/integrations/integrations/bulk_action/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`,
        },
        body: JSON.stringify({
          integration_ids: integrationIds,
          action,
          parameters,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to perform bulk ${action}`);
      }

      const result = await response.json();
      toast.success(`Bulk ${action} completed`);
      
      // Refresh integrations after bulk action
      await fetchIntegrations();
      
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : `Failed to perform bulk ${action}`;
      toast.error(message);
      throw err;
    }
  };

  // Initial load
  useEffect(() => {
    refreshIntegrations();
  }, []);

  return {
    integrations,
    stats,
    categories,
    providers,
    loading,
    error,
    refreshIntegrations,
    createIntegration,
    updateIntegration,
    deleteIntegration,
    testIntegration,
    syncIntegration,
    bulkAction,
  };
}