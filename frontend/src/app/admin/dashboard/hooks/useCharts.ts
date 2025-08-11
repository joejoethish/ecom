'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

interface Chart {
  id: string;
  title: string;
  description: string;
  chartType: string;
  config: any;
  dataSource: string;
  theme: string;
  colors: string[];
  isRealTime: boolean;
  refreshInterval: number;
  status: 'active' | 'draft' | 'archived';
  createdBy: {
    id: string;
    name: string;
  };
  createdAt: string;
  updatedAt: string;
  accessCount: number;
}

interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    [key: string]: any;
  }>;
  metadata?: {
    [key: string]: any;
  };
}

interface ChartFilters {
  search?: string;
  status?: string;
  chartType?: string;
  dateFrom?: string;
  dateTo?: string;
  createdBy?: string;
}

interface UseChartsOptions {
  autoLoad?: boolean;
  filters?: ChartFilters;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  pageSize?: number;
}

interface UseChartsReturn {
  charts: Chart[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  currentPage: number;
  totalPages: number;
  
  // Actions
  loadCharts: () => Promise<void>;
  createChart: (chartData: Partial<Chart>) => Promise<Chart>;
  updateChart: (id: string, chartData: Partial<Chart>) => Promise<Chart>;
  deleteChart: (id: string) => Promise<void>;
  duplicateChart: (id: string) => Promise<Chart>;
  
  // Data operations
  getChartData: (id: string, filters?: any) => Promise<ChartData>;
  exportChart: (id: string, format: string, options?: any) => Promise<string>;
  shareChart: (id: string, shareType: string, options?: any) => Promise<any>;
  
  // Pagination
  setPage: (page: number) => void;
  nextPage: () => void;
  prevPage: () => void;
  
  // Filters
  setFilters: (filters: ChartFilters) => void;
  clearFilters: () => void;
  
  // Sorting
  setSorting: (sortBy: string, sortOrder?: 'asc' | 'desc') => void;
  
  // Real-time updates
  subscribeToRealTimeUpdates: (chartId: string) => () => void;
}

export const useCharts = (options: UseChartsOptions = {}): UseChartsReturn => {
  const {
    autoLoad = true,
    filters: initialFilters = {},
    sortBy: initialSortBy = 'updatedAt',
    sortOrder: initialSortOrder = 'desc',
    pageSize = 20,
  } = options;

  // State
  const [charts, setCharts] = useState<Chart[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState<ChartFilters>(initialFilters);
  const [sortBy, setSortBy] = useState(initialSortBy);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>(initialSortOrder);

  // Refs for cleanup
  const abortControllerRef = useRef<AbortController | null>(null);
  const realTimeSubscriptions = useRef<Map<string, () => void>>(new Map());

  // Computed values
  const totalPages = Math.ceil(totalCount / pageSize);

  // Build query parameters
  const buildQueryParams = useCallback(() => {
    const params = new URLSearchParams();
    
    // Pagination
    params.set('page', currentPage.toString());
    params.set('page_size', pageSize.toString());
    
    // Sorting
    const sortField = sortOrder === 'desc' ? `-${sortBy}` : sortBy;
    params.set('ordering', sortField);
    
    // Filters
    if (filters.search) params.set('search', filters.search);
    if (filters.status) params.set('status', filters.status);
    if (filters.chartType) params.set('chart_type', filters.chartType);
    if (filters.dateFrom) params.set('created_at__gte', filters.dateFrom);
    if (filters.dateTo) params.set('created_at__lte', filters.dateTo);
    if (filters.createdBy) params.set('created_by', filters.createdBy);
    
    return params.toString();
  }, [currentPage, pageSize, sortBy, sortOrder, filters]);

  // Load charts
  const loadCharts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Cancel previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      
      abortControllerRef.current = new AbortController();
      
      const queryParams = buildQueryParams();
      const response = await fetch(`/api/admin/charts/?${queryParams}`, {
        signal: abortControllerRef.current.signal,
      });
      
      if (!response.ok) {
        throw new Error(`Failed to load charts: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      setCharts(data.results || data);
      setTotalCount(data.count || data.length || 0);
      
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to load charts');
        console.error('Load charts error:', err);
      }
    } finally {
      setLoading(false);
    }
  }, [buildQueryParams]);

  // Create chart
  const createChart = useCallback(async (chartData: Partial<Chart>): Promise<Chart> => {
    try {
      setError(null);
      
      const response = await fetch('/api/admin/charts/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(chartData),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create chart: ${response.statusText}`);
      }
      
      const newChart = await response.json();
      
      // Refresh charts list
      await loadCharts();
      
      return newChart;
      
    } catch (err: any) {
      setError(err.message || 'Failed to create chart');
      throw err;
    }
  }, [loadCharts]);

  // Update chart
  const updateChart = useCallback(async (id: string, chartData: Partial<Chart>): Promise<Chart> => {
    try {
      setError(null);
      
      const response = await fetch(`/api/admin/charts/${id}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(chartData),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to update chart: ${response.statusText}`);
      }
      
      const updatedChart = await response.json();
      
      // Update local state
      setCharts(prev => prev.map(chart => 
        chart.id === id ? updatedChart : chart
      ));
      
      return updatedChart;
      
    } catch (err: any) {
      setError(err.message || 'Failed to update chart');
      throw err;
    }
  }, []);

  // Delete chart
  const deleteChart = useCallback(async (id: string): Promise<void> => {
    try {
      setError(null);
      
      const response = await fetch(`/api/admin/charts/${id}/`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete chart: ${response.statusText}`);
      }
      
      // Remove from local state
      setCharts(prev => prev.filter(chart => chart.id !== id));
      setTotalCount(prev => prev - 1);
      
      // Clean up real-time subscription
      const unsubscribe = realTimeSubscriptions.current.get(id);
      if (unsubscribe) {
        unsubscribe();
        realTimeSubscriptions.current.delete(id);
      }
      
    } catch (err: any) {
      setError(err.message || 'Failed to delete chart');
      throw err;
    }
  }, []);

  // Duplicate chart
  const duplicateChart = useCallback(async (id: string): Promise<Chart> => {
    try {
      setError(null);
      
      const response = await fetch(`/api/admin/charts/${id}/duplicate/`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to duplicate chart: ${response.statusText}`);
      }
      
      const duplicatedChart = await response.json();
      
      // Refresh charts list
      await loadCharts();
      
      return duplicatedChart;
      
    } catch (err: any) {
      setError(err.message || 'Failed to duplicate chart');
      throw err;
    }
  }, [loadCharts]);

  // Get chart data
  const getChartData = useCallback(async (id: string, dataFilters?: any): Promise<ChartData> => {
    try {
      setError(null);
      
      const params = new URLSearchParams();
      if (dataFilters) {
        Object.entries(dataFilters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            params.set(key, String(value));
          }
        });
      }
      
      const queryString = params.toString();
      const url = `/api/admin/charts/${id}/data/${queryString ? `?${queryString}` : ''}`;
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Failed to get chart data: ${response.statusText}`);
      }
      
      return await response.json();
      
    } catch (err: any) {
      setError(err.message || 'Failed to get chart data');
      throw err;
    }
  }, []);

  // Export chart
  const exportChart = useCallback(async (id: string, format: string, exportOptions?: any): Promise<string> => {
    try {
      setError(null);
      
      const response = await fetch(`/api/admin/charts/${id}/export/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          format,
          ...exportOptions,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to export chart: ${response.statusText}`);
      }
      
      const exportData = await response.json();
      
      // Download the file
      const downloadResponse = await fetch(`/api/admin/charts/${id}/download_export/?export_id=${exportData.id}`);
      
      if (!downloadResponse.ok) {
        throw new Error('Failed to download exported file');
      }
      
      const blob = await downloadResponse.blob();
      const url = window.URL.createObjectURL(blob);
      
      // Create download link
      const a = document.createElement('a');
      a.href = url;
      a.download = `chart-${id}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      return exportData.file_path;
      
    } catch (err: any) {
      setError(err.message || 'Failed to export chart');
      throw err;
    }
  }, []);

  // Share chart
  const shareChart = useCallback(async (id: string, shareType: string, shareOptions?: any): Promise<any> => {
    try {
      setError(null);
      
      const response = await fetch(`/api/admin/charts/${id}/share/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          share_type: shareType,
          ...shareOptions,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to share chart: ${response.statusText}`);
      }
      
      const shareData = await response.json();
      
      // Handle different share types
      if (shareType === 'public_link') {
        const shareUrl = `${window.location.origin}/shared/chart/${shareData.share_token}`;
        
        // Copy to clipboard
        if (navigator.clipboard) {
          await navigator.clipboard.writeText(shareUrl);
        }
        
        return { ...shareData, shareUrl };
      } else if (shareType === 'embed_code') {
        const embedResponse = await fetch(`/api/admin/charts/${id}/embed_code/?share_token=${shareData.share_token}`);
        const embedData = await embedResponse.json();
        
        // Copy to clipboard
        if (navigator.clipboard) {
          await navigator.clipboard.writeText(embedData.embed_code);
        }
        
        return { ...shareData, ...embedData };
      }
      
      return shareData;
      
    } catch (err: any) {
      setError(err.message || 'Failed to share chart');
      throw err;
    }
  }, []);

  // Pagination
  const setPage = useCallback((page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  }, [totalPages]);

  const nextPage = useCallback(() => {
    setPage(currentPage + 1);
  }, [currentPage, setPage]);

  const prevPage = useCallback(() => {
    setPage(currentPage - 1);
  }, [currentPage, setPage]);

  // Filters
  const updateFilters = useCallback((newFilters: ChartFilters) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({});
    setCurrentPage(1);
  }, []);

  // Sorting
  const setSorting = useCallback((newSortBy: string, newSortOrder?: 'asc' | 'desc') => {
    setSortBy(newSortBy);
    if (newSortOrder) {
      setSortOrder(newSortOrder);
    } else {
      // Toggle sort order if same field
      setSortOrder(prev => newSortBy === sortBy ? (prev === 'asc' ? 'desc' : 'asc') : 'desc');
    }
    setCurrentPage(1);
  }, [sortBy]);

  // Real-time updates
  const subscribeToRealTimeUpdates = useCallback((chartId: string) => {
    // Clean up existing subscription
    const existingUnsubscribe = realTimeSubscriptions.current.get(chartId);
    if (existingUnsubscribe) {
      existingUnsubscribe();
    }

    // Create new subscription
    let intervalId: NodeJS.Timeout;
    let isSubscribed = true;

    const fetchRealTimeData = async () => {
      if (!isSubscribed) return;

      try {
        const response = await fetch(`/api/admin/charts/${chartId}/realtime/`);
        if (response.ok && isSubscribed) {
          const data = await response.json();
          
          // Update chart in local state
          setCharts(prev => prev.map(chart => {
            if (chart.id === chartId) {
              return {
                ...chart,
                // Update any real-time fields here
                accessCount: data.accessCount || chart.accessCount,
              };
            }
            return chart;
          }));
        }
      } catch (err) {
        console.error('Real-time update error:', err);
      }
    };

    // Start polling
    intervalId = setInterval(fetchRealTimeData, 30000); // 30 seconds

    // Unsubscribe function
    const unsubscribe = () => {
      isSubscribed = false;
      if (intervalId) {
        clearInterval(intervalId);
      }
      realTimeSubscriptions.current.delete(chartId);
    };

    realTimeSubscriptions.current.set(chartId, unsubscribe);
    
    return unsubscribe;
  }, []);

  // Effects
  useEffect(() => {
    if (autoLoad) {
      loadCharts();
    }
  }, [autoLoad, loadCharts]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Cancel any pending requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      
      // Clean up real-time subscriptions
      realTimeSubscriptions.current.forEach(unsubscribe => unsubscribe());
      realTimeSubscriptions.current.clear();
    };
  }, []);

  return {
    charts,
    loading,
    error,
    totalCount,
    currentPage,
    totalPages,
    
    // Actions
    loadCharts,
    createChart,
    updateChart,
    deleteChart,
    duplicateChart,
    
    // Data operations
    getChartData,
    exportChart,
    shareChart,
    
    // Pagination
    setPage,
    nextPage,
    prevPage,
    
    // Filters
    setFilters: updateFilters,
    clearFilters,
    
    // Sorting
    setSorting,
    
    // Real-time updates
    subscribeToRealTimeUpdates,
  };
};