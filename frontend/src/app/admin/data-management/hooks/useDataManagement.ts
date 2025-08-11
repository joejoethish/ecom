'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Types
export interface DataImportJob {
  id: string;
  name: string;
  description: string;
  file_path: string;
  file_format: 'csv' | 'excel' | 'json' | 'xml' | 'yaml';
  file_size: number;
  target_model: string;
  content_type_name: string;
  mapping_config: Record<string, any>;
  validation_rules: Record<string, any>;
  transformation_rules: Record<string, any>;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress_percentage: number;
  total_records: number;
  processed_records: number;
  successful_records: number;
  failed_records: number;
  error_log: any[];
  validation_errors: any[];
  processing_log: any[];
  created_by_name: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  skip_duplicates: boolean;
  update_existing: boolean;
  batch_size: number;
  duration?: number;
}

export interface DataExportJob {
  id: string;
  name: string;
  description: string;
  source_model: string;
  content_type_name: string;
  export_format: 'csv' | 'excel' | 'json' | 'xml' | 'yaml' | 'pdf';
  field_mapping: Record<string, any>;
  filter_criteria: Record<string, any>;
  sort_criteria: string[];
  file_path: string;
  file_size: number;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress_percentage: number;
  total_records: number;
  exported_records: number;
  error_log: any[];
  processing_log: any[];
  created_by_name: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  expires_at?: string;
  include_headers: boolean;
  compress_output: boolean;
  encrypt_output: boolean;
  duration?: number;
}

export interface DataMapping {
  id: string;
  name: string;
  description: string;
  target_model: string;
  content_type_name: string;
  field_mappings: Record<string, any>;
  default_values: Record<string, any>;
  transformation_rules: Record<string, any>;
  validation_rules: Record<string, any>;
  created_by_name: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface DataSyncJob {
  id: string;
  name: string;
  description: string;
  source_type: string;
  source_config: Record<string, any>;
  target_model: string;
  content_type_name: string;
  frequency: 'hourly' | 'daily' | 'weekly' | 'monthly';
  schedule_config: Record<string, any>;
  mapping_config: Record<string, any>;
  sync_mode: string;
  status: 'active' | 'paused' | 'disabled';
  last_run_at?: string;
  next_run_at?: string;
  last_run_status: string;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface DataBackup {
  id: string;
  name: string;
  description: string;
  backup_type: 'full' | 'incremental' | 'differential';
  models_to_backup: string[];
  backup_path: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress_percentage: number;
  file_size: number;
  created_by_name: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  compress_backup: boolean;
  encrypt_backup: boolean;
  retention_days: number;
  duration?: number;
}

export interface DataAuditLog {
  id: string;
  action: 'import' | 'export' | 'sync' | 'backup' | 'restore' | 'transform' | 'validate';
  operation_id: string;
  content_type_name?: string;
  object_id?: string;
  changes: Record<string, any>;
  old_values: Record<string, any>;
  new_values: Record<string, any>;
  user_name: string;
  timestamp: string;
  ip_address?: string;
  user_agent: string;
}

export interface DataQualityRule {
  id: string;
  name: string;
  description: string;
  rule_type: 'required' | 'format' | 'range' | 'unique' | 'reference' | 'custom';
  target_model: string;
  target_field: string;
  rule_config: Record<string, any>;
  is_active: boolean;
  severity: string;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface DataLineage {
  id: string;
  source_type: string;
  source_name: string;
  source_field: string;
  target_type: string;
  target_name: string;
  target_field: string;
  transformation_type: string;
  transformation_config: Record<string, any>;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface DataManagementStats {
  import_jobs: {
    total: number;
    recent: number;
    successful: number;
    failed: number;
    processing: number;
  };
  export_jobs: {
    total: number;
    recent: number;
    successful: number;
    failed: number;
    processing: number;
  };
  data_mappings: {
    total: number;
    active: number;
  };
  sync_jobs: {
    total: number;
    active: number;
    paused: number;
  };
  backups: {
    total: number;
    recent: number;
    successful: number;
  };
  quality_rules: {
    total: number;
    active: number;
  };
}

// API functions
const API_BASE = '/api/admin/data-management';

const api = {
  // Import Jobs
  getImportJobs: async (params?: Record<string, any>): Promise<{ results: DataImportJob[]; count: number }> => {
    const queryString = params ? new URLSearchParams(params).toString() : '';
    const response = await fetch(`${API_BASE}/import-jobs/?${queryString}`);
    if (!response.ok) throw new Error('Failed to fetch import jobs');
    return response.json();
  },

  createImportJob: async (data: FormData): Promise<DataImportJob> => {
    const response = await fetch(`${API_BASE}/import-jobs/`, {
      method: 'POST',
      body: data,
    });
    if (!response.ok) throw new Error('Failed to create import job');
    return response.json();
  },

  cancelImportJob: async (id: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/import-jobs/${id}/cancel/`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to cancel import job');
  },

  retryImportJob: async (id: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/import-jobs/${id}/retry/`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to retry import job');
  },

  validateImportJob: async (id: string): Promise<any> => {
    const response = await fetch(`${API_BASE}/import-jobs/${id}/validate/`);
    if (!response.ok) throw new Error('Failed to validate import job');
    return response.json();
  },

  // Export Jobs
  getExportJobs: async (params?: Record<string, any>): Promise<{ results: DataExportJob[]; count: number }> => {
    const queryString = params ? new URLSearchParams(params).toString() : '';
    const response = await fetch(`${API_BASE}/export-jobs/?${queryString}`);
    if (!response.ok) throw new Error('Failed to fetch export jobs');
    return response.json();
  },

  createExportJob: async (data: any): Promise<DataExportJob> => {
    const response = await fetch(`${API_BASE}/export-jobs/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create export job');
    return response.json();
  },

  downloadExportFile: async (id: string): Promise<Blob> => {
    const response = await fetch(`${API_BASE}/export-jobs/${id}/download/`);
    if (!response.ok) throw new Error('Failed to download export file');
    return response.blob();
  },

  // Data Mappings
  getDataMappings: async (params?: Record<string, any>): Promise<{ results: DataMapping[]; count: number }> => {
    const queryString = params ? new URLSearchParams(params).toString() : '';
    const response = await fetch(`${API_BASE}/mappings/?${queryString}`);
    if (!response.ok) throw new Error('Failed to fetch data mappings');
    return response.json();
  },

  createDataMapping: async (data: any): Promise<DataMapping> => {
    const response = await fetch(`${API_BASE}/mappings/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create data mapping');
    return response.json();
  },

  updateDataMapping: async (id: string, data: any): Promise<DataMapping> => {
    const response = await fetch(`${API_BASE}/mappings/${id}/`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update data mapping');
    return response.json();
  },

  deleteDataMapping: async (id: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/mappings/${id}/`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete data mapping');
  },

  // Sync Jobs
  getSyncJobs: async (): Promise<{ results: DataSyncJob[]; count: number }> => {
    const response = await fetch(`${API_BASE}/sync-jobs/`);
    if (!response.ok) throw new Error('Failed to fetch sync jobs');
    return response.json();
  },

  createSyncJob: async (data: any): Promise<DataSyncJob> => {
    const response = await fetch(`${API_BASE}/sync-jobs/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create sync job');
    return response.json();
  },

  runSyncJob: async (id: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/sync-jobs/${id}/run_now/`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to run sync job');
  },

  // Backups
  getBackups: async (): Promise<{ results: DataBackup[]; count: number }> => {
    const response = await fetch(`${API_BASE}/backups/`);
    if (!response.ok) throw new Error('Failed to fetch backups');
    return response.json();
  },

  createBackup: async (data: any): Promise<DataBackup> => {
    const response = await fetch(`${API_BASE}/backups/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create backup');
    return response.json();
  },

  // Audit Logs
  getAuditLogs: async (params?: Record<string, any>): Promise<{ results: DataAuditLog[]; count: number }> => {
    const queryString = params ? new URLSearchParams(params).toString() : '';
    const response = await fetch(`${API_BASE}/audit-logs/?${queryString}`);
    if (!response.ok) throw new Error('Failed to fetch audit logs');
    return response.json();
  },

  // Quality Rules
  getQualityRules: async (): Promise<{ results: DataQualityRule[]; count: number }> => {
    const response = await fetch(`${API_BASE}/quality-rules/`);
    if (!response.ok) throw new Error('Failed to fetch quality rules');
    return response.json();
  },

  createQualityRule: async (data: any): Promise<DataQualityRule> => {
    const response = await fetch(`${API_BASE}/quality-rules/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create quality rule');
    return response.json();
  },

  // Data Lineage
  getDataLineage: async (): Promise<{ results: DataLineage[]; count: number }> => {
    const response = await fetch(`${API_BASE}/lineage/`);
    if (!response.ok) throw new Error('Failed to fetch data lineage');
    return response.json();
  },

  getLineageGraph: async (): Promise<any> => {
    const response = await fetch(`${API_BASE}/lineage/lineage_graph/`);
    if (!response.ok) throw new Error('Failed to fetch lineage graph');
    return response.json();
  },

  // Stats
  getStats: async (days?: number): Promise<DataManagementStats> => {
    const queryString = days ? `?days=${days}` : '';
    const response = await fetch(`${API_BASE}/stats/dashboard_stats/${queryString}`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
  },
};

// Custom hooks
export const useDataManagement = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: stats } = useQuery({
    queryKey: ['data-management-stats'],
    queryFn: () => api.getStats(),
  });

  return {
    stats,
    loading,
    error,
  };
};

export const useImportJobs = (params?: Record<string, any>) => {
  return useQuery({
    queryKey: ['import-jobs', params],
    queryFn: () => api.getImportJobs(params),
  });
};

export const useExportJobs = (params?: Record<string, any>) => {
  return useQuery({
    queryKey: ['export-jobs', params],
    queryFn: () => api.getExportJobs(params),
  });
};

export const useDataMappings = (params?: Record<string, any>) => {
  return useQuery({
    queryKey: ['data-mappings', params],
    queryFn: () => api.getDataMappings(params),
  });
};

export const useSyncJobs = () => {
  return useQuery({
    queryKey: ['sync-jobs'],
    queryFn: api.getSyncJobs,
  });
};

export const useBackups = () => {
  return useQuery({
    queryKey: ['backups'],
    queryFn: api.getBackups,
  });
};

export const useAuditLogs = (params?: Record<string, any>) => {
  return useQuery({
    queryKey: ['audit-logs', params],
    queryFn: () => api.getAuditLogs(params),
  });
};

export const useQualityRules = () => {
  return useQuery({
    queryKey: ['quality-rules'],
    queryFn: api.getQualityRules,
  });
};

export const useDataLineage = () => {
  return useQuery({
    queryKey: ['data-lineage'],
    queryFn: api.getDataLineage,
  });
};

export const useLineageGraph = () => {
  return useQuery({
    queryKey: ['lineage-graph'],
    queryFn: api.getLineageGraph,
  });
};

// Mutation hooks
export const useCreateImportJob = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.createImportJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['import-jobs'] });
      queryClient.invalidateQueries({ queryKey: ['data-management-stats'] });
    },
  });
};

export const useCreateExportJob = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.createExportJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['export-jobs'] });
      queryClient.invalidateQueries({ queryKey: ['data-management-stats'] });
    },
  });
};

export const useCreateDataMapping = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.createDataMapping,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-mappings'] });
    },
  });
};

export const useUpdateDataMapping = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => api.updateDataMapping(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-mappings'] });
    },
  });
};

export const useDeleteDataMapping = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.deleteDataMapping,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-mappings'] });
    },
  });
};