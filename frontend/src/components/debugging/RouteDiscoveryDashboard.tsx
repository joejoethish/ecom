/**
 * Route Discovery Dashboard Component
 * Provides interface for triggering and viewing route discovery results
 */

'use client';

import React, { useState, useEffect } from 'react';
import {
  triggerRouteDiscovery,
  getRouteDiscoveryResults,
  getDependencyMap,
  validateRouteDiscovery,
  RouteDiscoveryResult,
  DependencyMap,
  RouteInfo,
  APICall
} from '@/services/routeDiscoveryApi';

interface ValidationResult {
  totalRoutes: number;
  validRoutes: number;
  invalidRoutes: number;
  errors: string[];
}

export default function RouteDiscoveryDashboard() {
  const [discoveryResults, setDiscoveryResults] = useState<RouteDiscoveryResult | null>(null);
  const [dependencyMap, setDependencyMap] = useState<DependencyMap | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'routes' | 'dependencies' | 'validation'>('routes');

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [resultsResponse, dependenciesResponse] = await Promise.all([
        getRouteDiscoveryResults(),
        getDependencyMap()
      ]);

      if (resultsResponse.success) {
        setDiscoveryResults(resultsResponse.data);
      }

      if (dependenciesResponse.success) {
        setDependencyMap(dependenciesResponse.data);
      }
    } catch (err) {
      setError('Failed to load initial data');
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerDiscovery = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await triggerRouteDiscovery();
      
      if (response.success) {
        // Reload data after successful discovery
        await loadInitialData();
      } else {
        setError(response.error || 'Discovery failed');
      }
    } catch (err) {
      setError('Failed to trigger discovery');
    } finally {
      setLoading(false);
    }
  };

  const handleValidateDiscovery = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await validateRouteDiscovery();
      
      if (response.success) {
        setValidationResult(response.data);
        setActiveTab('validation');
      } else {
        setError(response.error || 'Validation failed');
      }
    } catch (err) {
      setError('Failed to validate discovery');
    } finally {
      setLoading(false);
    }
  };

  const renderRouteCard = (route: RouteInfo) => (
    <div key={route.path} className="bg-white rounded-lg shadow p-4 border">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-lg">{route.path}</h3>
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          route.type === 'page' ? 'bg-blue-100 text-blue-800' :
          route.type === 'api' ? 'bg-green-100 text-green-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {route.type}
        </span>
      </div>
      
      <p className="text-sm text-gray-600 mb-2">Component: {route.component}</p>
      
      {route.apiCalls && route.apiCalls.length > 0 && (
        <div className="mt-3">
          <h4 className="font-medium text-sm mb-2">API Calls ({route.apiCalls.length})</h4>
          <div className="space-y-1">
            {route.apiCalls.map((apiCall: APICall, index: number) => (
              <div key={index} className="flex items-center text-xs">
                <span className={`px-2 py-1 rounded mr-2 ${
                  apiCall.method === 'GET' ? 'bg-blue-100 text-blue-700' :
                  apiCall.method === 'POST' ? 'bg-green-100 text-green-700' :
                  apiCall.method === 'PUT' ? 'bg-yellow-100 text-yellow-700' :
                  apiCall.method === 'DELETE' ? 'bg-red-100 text-red-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {apiCall.method}
                </span>
                <span className="text-gray-600">{apiCall.endpoint}</span>
                {apiCall.authentication && (
                  <span className="ml-2 px-1 py-0.5 bg-orange-100 text-orange-700 rounded text-xs">
                    Auth
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderDependencyMap = () => {
    if (!dependencyMap) return null;

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Dependency Overview</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {dependencyMap.frontend_routes.length}
              </div>
              <div className="text-sm text-gray-600">Frontend Routes</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {dependencyMap.api_endpoints.length}
              </div>
              <div className="text-sm text-gray-600">API Endpoints</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {dependencyMap.dependencies.length}
              </div>
              <div className="text-sm text-gray-600">Dependencies</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Route Dependencies</h3>
          <div className="space-y-3">
            {dependencyMap.dependencies.map((dep, index) => (
              <div key={index} className="flex items-center p-3 bg-gray-50 rounded">
                <div className="flex-1">
                  <div className="font-medium">{dep.frontend_route}</div>
                  <div className="text-sm text-gray-600">Component: {dep.component}</div>
                </div>
                <div className="mx-4">
                  <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="flex-1 text-right">
                  <div className="font-medium">{dep.api_endpoint}</div>
                  <div className="text-sm text-gray-600">{dep.method}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderValidationResults = () => {
    if (!validationResult) return null;

    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Validation Results</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-800">
              {validationResult.totalRoutes}
            </div>
            <div className="text-sm text-gray-600">Total Routes</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {validationResult.validRoutes}
            </div>
            <div className="text-sm text-gray-600">Valid Routes</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {validationResult.invalidRoutes}
            </div>
            <div className="text-sm text-gray-600">Invalid Routes</div>
          </div>
        </div>

        {validationResult.errors.length > 0 && (
          <div>
            <h4 className="font-medium text-red-800 mb-2">Validation Errors</h4>
            <div className="space-y-2">
              {validationResult.errors.map((error, index) => (
                <div key={index} className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                  {error}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Route Discovery Dashboard</h1>
        <p className="text-gray-600">
          Analyze and monitor your Next.js application routes and API dependencies
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="text-red-800">{error}</div>
        </div>
      )}

      <div className="mb-6 flex flex-wrap gap-4">
        <button
          onClick={handleTriggerDiscovery}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Scanning...' : 'Trigger Discovery'}
        </button>
        
        <button
          onClick={handleValidateDiscovery}
          disabled={loading}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Validate Routes
        </button>
      </div>

      <div className="mb-6">
        <nav className="flex space-x-8">
          {[
            { key: 'routes', label: 'Routes', count: discoveryResults?.totalRoutes },
            { key: 'dependencies', label: 'Dependencies', count: dependencyMap?.dependencies.length },
            { key: 'validation', label: 'Validation', count: validationResult?.invalidRoutes }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
              {tab.count !== undefined && (
                <span className="ml-2 bg-gray-100 text-gray-900 py-0.5 px-2 rounded-full text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      <div className="min-h-96">
        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {!loading && activeTab === 'routes' && discoveryResults && (
          <div>
            <div className="mb-6 bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Discovery Summary</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {discoveryResults.totalRoutes}
                  </div>
                  <div className="text-sm text-gray-600">Total Routes</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {discoveryResults.apiCallsCount}
                  </div>
                  <div className="text-sm text-gray-600">API Calls</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {discoveryResults.scanDuration}ms
                  </div>
                  <div className="text-sm text-gray-600">Scan Duration</div>
                </div>
              </div>
              {discoveryResults.lastScanned && (
                <div className="mt-4 text-sm text-gray-500">
                  Last scanned: {new Date(discoveryResults.lastScanned).toLocaleString()}
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {discoveryResults.routes.map(renderRouteCard)}
            </div>
          </div>
        )}

        {!loading && activeTab === 'dependencies' && renderDependencyMap()}
        {!loading && activeTab === 'validation' && renderValidationResults()}
      </div>
    </div>
  );
}