'use client';

import { useState, useEffect, useCallback } from 'react';

interface DashboardLayout {
  id: string;
  name: string;
  description: string;
  owner: string;
  is_shared: boolean;
  shared_with_roles: string[];
  layout_config: any;
  widget_positions: WidgetPosition[];
  is_active: boolean;
}

interface WidgetPosition {
  id: string;
  widget: any;
  x: number;
  y: number;
  width: number;
  height: number;
  widget_config: any;
  is_visible: boolean;
  order: number;
}

export function useDashboard() {
  const [layout, setLayout] = useState<DashboardLayout | null>(null);
  const [widgets, setWidgets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard layout and widgets
  const fetchDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Get user's default layout or create one
      const preferencesResponse = await fetch('/api/admin/dashboard/preferences/my/');
      let layoutId = null;

      if (preferencesResponse.ok) {
        const preferences = await preferencesResponse.json();
        layoutId = preferences.default_layout;
      }

      if (!layoutId) {
        // Create a default layout
        const createResponse = await fetch('/api/admin/dashboard/layouts/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: 'My Dashboard',
            description: 'Default dashboard layout',
            layout_config: {
              grid_size: 12,
              theme: 'light'
            }
          })
        });

        if (createResponse.ok) {
          const newLayout = await createResponse.json();
          layoutId = newLayout.id;
        }
      }

      if (layoutId) {
        // Fetch the layout with widgets
        const layoutResponse = await fetch(`/api/admin/dashboard/layouts/${layoutId}/`);
        if (layoutResponse.ok) {
          const layoutData = await layoutResponse.json();
          setLayout(layoutData);
          
          // Extract widgets from widget positions
          const widgetList = layoutData.widget_positions
            ?.filter((pos: WidgetPosition) => pos.is_visible)
            ?.sort((a: WidgetPosition, b: WidgetPosition) => a.order - b.order)
            ?.map((pos: WidgetPosition) => ({
              ...pos.widget,
              x: pos.x,
              y: pos.y,
              width: pos.width,
              height: pos.height,
              widget_config: pos.widget_config,
              position_id: pos.id
            })) || [];
          
          setWidgets(widgetList);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  // Update dashboard layout
  const updateLayout = useCallback(async (updates: Partial<DashboardLayout>) => {
    if (!layout) return;

    try {
      const response = await fetch(`/api/admin/dashboard/layouts/${layout.id}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates)
      });

      if (response.ok) {
        const updatedLayout = await response.json();
        setLayout(updatedLayout);
      }
    } catch (err) {
      console.error('Failed to update layout:', err);
    }
  }, [layout]);

  // Add widget to dashboard
  const addWidget = useCallback(async (widgetId: string, position: { x: number; y: number; width: number; height: number }) => {
    if (!layout) return;

    try {
      const response = await fetch(`/api/admin/dashboard/layouts/${layout.id}/add-widget/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          widget_id: widgetId,
          ...position,
          order: widgets.length
        })
      });

      if (response.ok) {
        // Refresh dashboard to get updated widgets
        await fetchDashboard();
      }
    } catch (err) {
      console.error('Failed to add widget:', err);
    }
  }, [layout, widgets.length, fetchDashboard]);

  // Remove widget from dashboard
  const removeWidget = useCallback(async (widgetId: string) => {
    if (!layout) return;

    try {
      const response = await fetch(`/api/admin/dashboard/layouts/${layout.id}/remove-widget/`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          widget_id: widgetId
        })
      });

      if (response.ok) {
        // Remove widget from local state
        setWidgets(prev => prev.filter(w => w.id !== widgetId));
      }
    } catch (err) {
      console.error('Failed to remove widget:', err);
    }
  }, [layout]);

  // Update widget position
  const updateWidgetPosition = useCallback(async (widgetId: string, position: { x: number; y: number; width: number; height: number; order?: number }) => {
    if (!layout) return;

    try {
      const response = await fetch(`/api/admin/dashboard/layouts/${layout.id}/update-positions/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          positions: [{
            widget_id: widgetId,
            ...position
          }]
        })
      });

      if (response.ok) {
        // Update local widget state
        setWidgets(prev => prev.map(w => 
          w.id === widgetId 
            ? { ...w, ...position }
            : w
        ));
      }
    } catch (err) {
      console.error('Failed to update widget position:', err);
    }
  }, [layout]);

  // Refresh widget data
  const refreshWidget = useCallback(async (widgetId: string) => {
    try {
      const response = await fetch(`/api/admin/dashboard/widgets/${widgetId}/data/`);
      if (response.ok) {
        const data = await response.json();
        // Widget component will handle the data update
        return data;
      }
    } catch (err) {
      console.error('Failed to refresh widget:', err);
    }
  }, []);

  // Export dashboard
  const exportDashboard = useCallback(async (format: 'pdf' | 'png' | 'csv' | 'excel') => {
    if (!layout) return;

    try {
      const response = await fetch('/api/admin/dashboard/exports/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: `${layout.name} Export`,
          export_type: format === 'pdf' || format === 'png' ? 'pdf' : 'data',
          format: format,
          dashboard_layout: layout.id,
          include_data: true,
          include_charts: true
        })
      });

      if (response.ok) {
        const exportData = await response.json();
        // Poll for export completion
        const checkExport = async () => {
          const statusResponse = await fetch(`/api/admin/dashboard/exports/${exportData.id}/`);
          if (statusResponse.ok) {
            const status = await statusResponse.json();
            if (status.status === 'completed') {
              // Download the file
              const downloadResponse = await fetch(`/api/admin/dashboard/exports/${exportData.id}/download/`);
              if (downloadResponse.ok) {
                const downloadData = await downloadResponse.json();
                window.open(downloadData.download_url, '_blank');
              }
            } else if (status.status === 'processing') {
              // Check again in 2 seconds
              setTimeout(checkExport, 2000);
            }
          }
        };
        
        setTimeout(checkExport, 1000);
      }
    } catch (err) {
      console.error('Failed to export dashboard:', err);
      throw err;
    }
  }, [layout]);

  // Duplicate dashboard
  const duplicateDashboard = useCallback(async () => {
    if (!layout) return;

    try {
      const response = await fetch(`/api/admin/dashboard/layouts/${layout.id}/duplicate/`, {
        method: 'POST'
      });

      if (response.ok) {
        const duplicatedLayout = await response.json();
        return duplicatedLayout;
      }
    } catch (err) {
      console.error('Failed to duplicate dashboard:', err);
    }
  }, [layout]);

  // Set as default dashboard
  const setAsDefault = useCallback(async () => {
    if (!layout) return;

    try {
      const response = await fetch(`/api/admin/dashboard/layouts/${layout.id}/set-default/`, {
        method: 'POST'
      });

      if (response.ok) {
        return true;
      }
    } catch (err) {
      console.error('Failed to set as default:', err);
    }
    return false;
  }, [layout]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return {
    layout,
    widgets,
    loading,
    error,
    updateLayout,
    addWidget,
    removeWidget,
    updateWidgetPosition,
    refreshWidget,
    exportDashboard,
    duplicateDashboard,
    setAsDefault,
    refetch: fetchDashboard
  };
}