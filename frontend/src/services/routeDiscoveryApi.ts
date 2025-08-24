/**
 * Frontend Route Discovery Service
 * Provides API calls to the backend route discovery system
 */

import { ApiResponse } from '@/types/api';

export interface RouteInfo {
  path: string;
  type: 'page' | 'api' | 'dynamic';
  component: string;
  apiCalls: APICall[];
  dependencies: string[];
  metadata?: Record<string, any>;
}

export interface APICall {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  endpoint: string;
  payload?: object;
  headers?: Record<string, string>;
  authentication: boolean;
  component?: string;
  lineNumber?: number;
}

export interface RouteDiscoveryResult {
  routes: RouteInfo[];
  totalRoutes: number;
  apiCallsCount: number;
  lastScanned: string;
  scanDuration: number;
}

export interface DependencyMap {
  frontend_routes: RouteInfo[];
  api_endpoints: string[];
  dependencies: Array<{
    frontend_route: string;
    api_endpoint: string;
    method: string;
    component: string;
  }>;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Trigger a full route discovery scan
 */
export async function triggerRouteDiscovery(): Promise<ApiResponse<RouteDiscoveryResult>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/debugging/route-discovery/scan/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
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
      message: 'Route discovery completed successfully'
    };
  } catch (error) {
    console.error('Route discovery failed:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Get the latest route discovery results
 */
export async function getRouteDiscoveryResults(): Promise<ApiResponse<RouteDiscoveryResult>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/debugging/route-discovery/results/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
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
      message: 'Route discovery results retrieved successfully'
    };
  } catch (error) {
    console.error('Failed to get route discovery results:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Get dependency mapping between frontend routes and API endpoints
 */
export async function getDependencyMap(): Promise<ApiResponse<DependencyMap>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/debugging/route-discovery/dependencies/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
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
      message: 'Dependency map retrieved successfully'
    };
  } catch (error) {
    console.error('Failed to get dependency map:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Get routes filtered by type
 */
export async function getRoutesByType(type: 'page' | 'api' | 'dynamic'): Promise<ApiResponse<RouteInfo[]>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/debugging/route-discovery/routes/?type=${type}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
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
      message: `Routes of type ${type} retrieved successfully`
    };
  } catch (error) {
    console.error(`Failed to get routes of type ${type}:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Get API calls for a specific route
 */
export async function getAPICallsForRoute(routePath: string): Promise<ApiResponse<APICall[]>> {
  try {
    const encodedPath = encodeURIComponent(routePath);
    const response = await fetch(`${API_BASE_URL}/api/debugging/route-discovery/routes/${encodedPath}/api-calls/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
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
      message: `API calls for route ${routePath} retrieved successfully`
    };
  } catch (error) {
    console.error(`Failed to get API calls for route ${routePath}:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}

/**
 * Validate route discovery accuracy by testing discovered routes
 */
export async function validateRouteDiscovery(): Promise<ApiResponse<{
  totalRoutes: number;
  validRoutes: number;
  invalidRoutes: number;
  errors: string[];
}>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/debugging/route-discovery/validate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
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
      message: 'Route discovery validation completed'
    };
  } catch (error) {
    console.error('Route discovery validation failed:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      data: null
    };
  }
}