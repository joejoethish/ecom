/**
 * Debugging API Service
 * 
 * Provides API calls for the debugging dashboard functionality.
 */

import { ApiResponse } from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface SystemHealthMetrics {
  frontend: {
    status: 'healthy' | 'warning' | 'error';
    responseTime: number;
    errorRate: number;
    activeUsers: number;
    memoryUsage: number;
  };
  backend: {
    status: 'healthy' | 'warning' | 'error';
    responseTime: number;
    errorRate: number;
    activeConnections: number;
    cpuUsage: number;
  };
  database: {
    status: 'healthy' | 'warning' | 'error';
    queryTime: number;
    connectionPool: number;
    slowQueries: number;
    diskUsage: number;
  };
  timestamp: string;
}

export interface WorkflowTrace {
  correlationId: string;
  workflowType: string;
  startTime: string;
  endTime?: string;
  status: 'in_progress' | 'completed' | 'failed';
  totalDuration?: number;
  steps: TraceStep[];
  errors: TraceError[];
}

export interface TraceStep {
  id: string;
  layer: 'frontend' | 'api' | 'database';
  component: string;
  operation: string;
  startTime: string;
  endTime?: string;
  duration?: number;
  status: 'started' | 'completed' | 'failed';
  metadata?: Record<string, any>;
}

export interface TraceError {
  timestamp: string;
  component: string;
  error: string;
  stack?: string;
}

export interface ApiEndpoint {
  path: string;
  method: string;
  description: string;
  parameters: Parameter[];
  authentication: boolean;
  permissions: string[];
}

export interface Parameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  required: boolean;
  description: string;
  example?: any;
}

export interface ErrorGroup {
  id: string;
  errorType: string;
  errorMessage: string;
  count: number;
  firstSeen: string;
  lastSeen: string;
  affectedComponents: string[];
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'investigating' | 'resolved' | 'ignored';
  resolutionSuggestions: ResolutionSuggestion[];
  recentOccurrences: ErrorOccurrence[];
}

export interface ResolutionSuggestion {
  type: 'code_fix' | 'configuration' | 'infrastructure' | 'monitoring';
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  estimatedEffort: string;
  steps: string[];
}

export interface ErrorOccurrence {
  id: string;
  timestamp: string;
  correlationId: string;
  layer: 'frontend' | 'api' | 'database';
  component: string;
  stackTrace?: string;
  metadata: Record<string, any>;
  userAgent?: string;
  userId?: string;
}

/**
 * Get system health metrics
 */
export async function getSystemHealth(): Promise<ApiResponse<SystemHealthMetrics>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/debugging/system-health/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      data,
      message: 'System health retrieved successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Get workflow traces with optional filters
 */
export async function getWorkflowTraces(filters?: {
  workflowType?: string;
  status?: string;
  timeRange?: string;
}): Promise<ApiResponse<{ results: WorkflowTrace[]; count: number }>> {
  try {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/debugging/workflow-traces/?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      data,
      message: 'Workflow traces retrieved successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Get API endpoints for testing
 */
export async function getApiEndpoints(): Promise<ApiResponse<ApiEndpoint[]>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/debugging/api-endpoints/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      data: data.results || data,
      message: 'API endpoints retrieved successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Execute API test
 */
export async function executeApiTest(request: {
  endpoint: string;
  method: string;
  headers: Record<string, string>;
  payload?: any;
}): Promise<ApiResponse<{
  status: number;
  statusText: string;
  responseTime: number;
  responseData: any;
  correlationId: string;
}>> {
  try {
    const startTime = performance.now();
    
    const requestOptions: RequestInit = {
      method: request.method,
      headers: {
        ...request.headers,
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    };

    if (request.payload && ['POST', 'PUT', 'PATCH'].includes(request.method)) {
      requestOptions.body = JSON.stringify(request.payload);
    }

    const response = await fetch(`${API_BASE_URL}${request.endpoint}`, requestOptions);
    const endTime = performance.now();
    
    const responseData = await response.json().catch(() => null);

    return {
      success: true,
      data: {
        status: response.status,
        statusText: response.statusText,
        responseTime: endTime - startTime,
        responseData,
        correlationId: response.headers.get('X-Correlation-ID') || '',
      },
      message: 'API test executed successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Get replayable requests
 */
export async function getReplayableRequests(): Promise<ApiResponse<Array<{
  correlationId: string;
  originalRequest: {
    method: string;
    url: string;
    headers: Record<string, string>;
    payload?: any;
  };
}>>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/debugging/replayable-requests/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      data: data.results || data,
      message: 'Replayable requests retrieved successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Replay a request with modifications
 */
export async function replayRequest(request: {
  originalCorrelationId: string;
  modifications?: {
    headers?: Record<string, string>;
    payload?: any;
  };
}): Promise<ApiResponse<{
  status: number;
  statusText: string;
  responseTime: number;
  responseData: any;
  correlationId: string;
}>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/debugging/replay-request/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: JSON.stringify({
        original_correlation_id: request.originalCorrelationId,
        modifications: request.modifications,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      data,
      message: 'Request replayed successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Get error groups with optional filters
 */
export async function getErrorGroups(filters?: {
  severity?: string;
  status?: string;
  layer?: string;
  timeRange?: string;
}): Promise<ApiResponse<{ results: ErrorGroup[]; count: number }>> {
  try {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/debugging/error-groups/?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      data,
      message: 'Error groups retrieved successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Get error analytics
 */
export async function getErrorAnalytics(filters?: {
  timeRange?: string;
}): Promise<ApiResponse<{
  totalErrors: number;
  errorsByLayer: Record<string, number>;
  errorsByType: Record<string, number>;
  errorTrends: Array<{ date: string; count: number }>;
  topComponents: Array<{ component: string; count: number }>;
}>> {
  try {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/debugging/error-analytics/?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      data,
      message: 'Error analytics retrieved successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Update error group status
 */
export async function updateErrorGroupStatus(
  groupId: string, 
  status: 'open' | 'investigating' | 'resolved' | 'ignored'
): Promise<ApiResponse<ErrorGroup>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/debugging/error-groups/${groupId}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: JSON.stringify({ status }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      data,
      message: 'Error group status updated successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Send trace event to backend
 */
export async function sendTraceEvent(event: {
  eventType: string;
  correlationId: string;
  data: Record<string, any>;
}): Promise<ApiResponse<void>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/debugging/trace-events/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Correlation-ID': event.correlationId,
      },
      body: JSON.stringify({
        event_type: event.eventType,
        timestamp: Date.now(),
        ...event.data,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return {
      success: true,
      data: null,
      message: 'Trace event sent successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Send performance metric to backend
 */
export async function sendPerformanceMetric(metric: {
  correlationId: string;
  layer: 'frontend' | 'api' | 'database';
  component: string;
  metricName: string;
  metricValue: number;
  metadata?: Record<string, any>;
}): Promise<ApiResponse<void>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/debugging/metrics/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Correlation-ID': metric.correlationId,
      },
      body: JSON.stringify({
        layer: metric.layer,
        component: metric.component,
        metric_name: metric.metricName,
        metric_value: metric.metricValue,
        correlation_id: metric.correlationId,
        timestamp: Date.now(),
        metadata: metric.metadata || {},
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return {
      success: true,
      data: null,
      message: 'Performance metric sent successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}