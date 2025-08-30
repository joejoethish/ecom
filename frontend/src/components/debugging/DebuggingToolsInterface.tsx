/**
 * Debugging Tools Interface Component
 * 
 * Provides tools for request replay, payload modification, and API testing.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useCorrelationId } from '@/hooks/useCorrelationId';

interface ApiEndpoint {
  path: string;
  method: string;
  description: string;
  parameters: Parameter[];
  authentication: boolean;
  permissions: string[];
}

interface Parameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  required: boolean;
  description: string;
  example?: any;
}

interface TestRequest {
  endpoint: string;
  method: string;
  headers: Record<string, string>;
  payload?: any;
  expectedStatus?: number;
}

interface TestResult {
  success: boolean;
  status: number;
  statusText: string;
  responseTime: number;
  responseData: any;
  error?: string;
  correlationId?: string;
}

interface ReplayRequest {
  correlationId: string;
  originalRequest: {
    method: string;
    url: string;
    headers: Record<string, string>;
    payload?: any;
  };
  modifications?: {
    headers?: Record<string, string>;
    payload?: any;
  };
}

export function DebuggingToolsInterface() {
  const [activeTab, setActiveTab] = useState<'api-test' | 'request-replay' | 'payload-editor'>('api-test');
  const [endpoints, setEndpoints] = useState<ApiEndpoint[]>([]);
  const [selectedEndpoint, setSelectedEndpoint] = useState<ApiEndpoint | null>(null);
  const [testRequest, setTestRequest] = useState<TestRequest>({
    endpoint: '',
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    payload: null,
  });
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [replayRequests, setReplayRequests] = useState<ReplayRequest[]>([]);
  const [selectedReplay, setSelectedReplay] = useState<ReplayRequest | null>(null);
  const { correlationId } = useCorrelationId();

  useEffect(() => {
    fetchApiEndpoints();
    fetchReplayableRequests();
  }, []);

  const fetchApiEndpoints = async () => {
    try {
      const response = await fetch('/api/v1/debugging/api-endpoints/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setEndpoints(data.results || data);
      }
    } catch (error) {
      console.error('Failed to fetch API endpoints:', error);
    }
  };

  const fetchReplayableRequests = async () => {
    try {
      const response = await fetch('/api/v1/debugging/replayable-requests/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setReplayRequests(data.results || data);
      }
    } catch (error) {
      console.error('Failed to fetch replayable requests:', error);
    }
  };

  const executeApiTest = async () => {
    setLoading(true);
    setTestResult(null);

    try {
      const startTime = performance.now();
      
      const requestHeaders = {
        ...testRequest.headers,
        'X-Correlation-ID': correlationId,
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      };

      const requestOptions: RequestInit = {
        method: testRequest.method,
        headers: requestHeaders,
      };

      if (testRequest.payload && ['POST', 'PUT', 'PATCH'].includes(testRequest.method)) {
        requestOptions.body = JSON.stringify(testRequest.payload);
      }

      const response = await fetch(testRequest.endpoint, requestOptions);
      const endTime = performance.now();
      
      const responseData = await response.json().catch(() => null);

      const result: TestResult = {
        success: response.ok,
        status: response.status,
        statusText: response.statusText,
        responseTime: endTime - startTime,
        responseData,
        correlationId: response.headers.get('X-Correlation-ID') || correlationId,
      };

      setTestResult(result);
    } catch (error) {
      setTestResult({
        success: false,
        status: 0,
        statusText: 'Network Error',
        responseTime: 0,
        responseData: null,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  };

  const replayRequest = async (request: ReplayRequest) => {
    setLoading(true);

    try {
      const response = await fetch('/api/v1/debugging/replay-request/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'X-Correlation-ID': correlationId,
        },
        body: JSON.stringify({
          original_correlation_id: request.correlationId,
          modifications: request.modifications,
        }),
      });

      const result = await response.json();
      setTestResult({
        success: response.ok,
        status: response.status,
        statusText: response.statusText,
        responseTime: result.response_time || 0,
        responseData: result.response_data,
        correlationId: result.correlation_id,
      });
    } catch (error) {
      setTestResult({
        success: false,
        status: 0,
        statusText: 'Replay Error',
        responseTime: 0,
        responseData: null,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  };

  const generatePayloadFromEndpoint = (endpoint: ApiEndpoint) => {
    const payload: any = {};
    
    endpoint.parameters
      .filter(p => p.required && ['POST', 'PUT', 'PATCH'].includes(endpoint.method))
      .forEach(param => {
        switch (param.type) {
          case 'string':
            payload[param.name] = param.example || 'example_string';
            break;
          case 'number':
            payload[param.name] = param.example || 123;
            break;
          case 'boolean':
            payload[param.name] = param.example !== undefined ? param.example : true;
            break;
          case 'object':
            payload[param.name] = param.example || {};
            break;
          case 'array':
            payload[param.name] = param.example || [];
            break;
        }
      });

    return Object.keys(payload).length > 0 ? payload : null;
  };

  const renderApiTestTab = () => (
    <div className="space-y-6">
      {/* Endpoint Selection */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">API Endpoint Testing</h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Endpoint List */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Endpoint
            </label>
            <div className="max-h-64 overflow-y-auto border border-gray-300 rounded">
              {endpoints.map((endpoint, index) => (
                <div
                  key={index}
                  onClick={() => {
                    setSelectedEndpoint(endpoint);
                    setTestRequest(prev => ({
                      ...prev,
                      endpoint: endpoint.path,
                      method: endpoint.method,
                      payload: generatePayloadFromEndpoint(endpoint),
                    }));
                  }}
                  className={`p-3 border-b cursor-pointer hover:bg-gray-50 ${
                    selectedEndpoint?.path === endpoint.path ? 'bg-blue-50 border-blue-200' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{endpoint.path}</div>
                      <div className="text-sm text-gray-600">{endpoint.description}</div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      endpoint.method === 'GET' ? 'bg-blue-100 text-blue-800' :
                      endpoint.method === 'POST' ? 'bg-green-100 text-green-800' :
                      endpoint.method === 'PUT' ? 'bg-yellow-100 text-yellow-800' :
                      endpoint.method === 'DELETE' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {endpoint.method}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Request Configuration */}
          <div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Endpoint URL
                </label>
                <input
                  type="text"
                  value={testRequest.endpoint}
                  onChange={(e) => setTestRequest(prev => ({ ...prev, endpoint: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="/api/v1/example"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  HTTP Method
                </label>
                <select
                  value={testRequest.method}
                  onChange={(e) => setTestRequest(prev => ({ ...prev, method: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="PATCH">PATCH</option>
                  <option value="DELETE">DELETE</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Headers (JSON)
                </label>
                <textarea
                  value={JSON.stringify(testRequest.headers, null, 2)}
                  onChange={(e) => {
                    try {
                      const headers = JSON.parse(e.target.value);
                      setTestRequest(prev => ({ ...prev, headers }));
                    } catch (error) {
                      // Invalid JSON, ignore
                    }
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
                  rows={4}
                />
              </div>

              {['POST', 'PUT', 'PATCH'].includes(testRequest.method) && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Request Payload (JSON)
                  </label>
                  <textarea
                    value={testRequest.payload ? JSON.stringify(testRequest.payload, null, 2) : ''}
                    onChange={(e) => {
                      try {
                        const payload = e.target.value ? JSON.parse(e.target.value) : null;
                        setTestRequest(prev => ({ ...prev, payload }));
                      } catch (error) {
                        // Invalid JSON, ignore
                      }
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
                    rows={6}
                    placeholder="{}"
                  />
                </div>
              )}

              <button
                onClick={executeApiTest}
                disabled={loading || !testRequest.endpoint}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Testing...' : 'Execute Test'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Test Results */}
      {testResult && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Test Results</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div className="text-center">
              <div className={`text-2xl font-bold ${testResult.success ? 'text-green-600' : 'text-red-600'}`}>
                {testResult.status}
              </div>
              <div className="text-sm text-gray-600">{testResult.statusText}</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {testResult.responseTime.toFixed(1)}ms
              </div>
              <div className="text-sm text-gray-600">Response Time</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {testResult.correlationId?.slice(0, 8) || 'N/A'}
              </div>
              <div className="text-sm text-gray-600">Correlation ID</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${testResult.success ? 'text-green-600' : 'text-red-600'}`}>
                {testResult.success ? '✓' : '✗'}
              </div>
              <div className="text-sm text-gray-600">Status</div>
            </div>
          </div>

          {testResult.error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
              <strong>Error:</strong> {testResult.error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Response Data
            </label>
            <pre className="bg-gray-50 p-4 rounded-md text-sm overflow-x-auto">
              {JSON.stringify(testResult.responseData, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );

  const renderRequestReplayTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Request Replay</h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Replayable Requests */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Recent Requests
            </label>
            <div className="max-h-64 overflow-y-auto border border-gray-300 rounded">
              {replayRequests.map((request, index) => (
                <div
                  key={index}
                  onClick={() => setSelectedReplay(request)}
                  className={`p-3 border-b cursor-pointer hover:bg-gray-50 ${
                    selectedReplay?.correlationId === request.correlationId ? 'bg-blue-50 border-blue-200' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{request.originalRequest.method} {request.originalRequest.url}</div>
                      <div className="text-sm text-gray-600">ID: {request.correlationId.slice(0, 8)}...</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Request Modification */}
          <div>
            {selectedReplay && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Original Request
                  </label>
                  <pre className="bg-gray-50 p-3 rounded text-sm overflow-x-auto">
                    {JSON.stringify(selectedReplay.originalRequest, null, 2)}
                  </pre>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Header Modifications (JSON)
                  </label>
                  <textarea
                    value={JSON.stringify(selectedReplay.modifications?.headers || {}, null, 2)}
                    onChange={(e) => {
                      try {
                        const headers = JSON.parse(e.target.value);
                        setSelectedReplay(prev => prev ? {
                          ...prev,
                          modifications: { ...prev.modifications, headers }
                        } : null);
                      } catch (error) {
                        // Invalid JSON, ignore
                      }
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
                    rows={3}
                    placeholder="{}"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Payload Modifications (JSON)
                  </label>
                  <textarea
                    value={JSON.stringify(selectedReplay.modifications?.payload || {}, null, 2)}
                    onChange={(e) => {
                      try {
                        const payload = JSON.parse(e.target.value);
                        setSelectedReplay(prev => prev ? {
                          ...prev,
                          modifications: { ...prev.modifications, payload }
                        } : null);
                      } catch (error) {
                        // Invalid JSON, ignore
                      }
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
                    rows={4}
                    placeholder="{}"
                  />
                </div>

                <button
                  onClick={() => selectedReplay && replayRequest(selectedReplay)}
                  disabled={loading}
                  className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Replaying...' : 'Replay Request'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const renderPayloadEditorTab = () => (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Payload Editor & Validator</h3>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            JSON Payload
          </label>
          <textarea
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
            rows={12}
            placeholder="Enter JSON payload here..."
          />
          <div className="mt-2 flex space-x-2">
            <button className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
              Validate JSON
            </button>
            <button className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700">
              Format JSON
            </button>
            <button className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700">
              Minify JSON
            </button>
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Schema Validation
          </label>
          <div className="bg-gray-50 p-4 rounded-md text-sm">
            <p>Payload validation results will appear here...</p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { key: 'api-test', label: 'API Testing' },
            { key: 'request-replay', label: 'Request Replay' },
            { key: 'payload-editor', label: 'Payload Editor' },
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
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'api-test' && renderApiTestTab()}
      {activeTab === 'request-replay' && renderRequestReplayTab()}
      {activeTab === 'payload-editor' && renderPayloadEditorTab()}
    </div>
  );
}