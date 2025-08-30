/**
 * Workflow Trace Visualization Component
 * 
 * Provides interactive visualization of workflow traces with timing information
 * using React Flow for visual representation.
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';

interface WorkflowTrace {
  correlationId: string;
  workflowType: string;
  startTime: string;
  endTime?: string;
  status: 'in_progress' | 'completed' | 'failed';
  totalDuration?: number;
  steps: TraceStep[];
  errors: TraceError[];
}

interface TraceStep {
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

interface TraceError {
  timestamp: string;
  component: string;
  error: string;
  stack?: string;
}

const nodeTypes = {
  frontend: ({ data }: { data: any }) => (
    <div className={`px-4 py-2 shadow-md rounded-md bg-blue-100 border-2 ${
      data.status === 'failed' ? 'border-red-500' : 
      data.status === 'completed' ? 'border-green-500' : 'border-blue-500'
    }`}>
      <div className="font-bold text-sm">{data.component}</div>
      <div className="text-xs text-gray-600">{data.operation}</div>
      {data.duration && (
        <div className="text-xs font-medium">{data.duration.toFixed(1)}ms</div>
      )}
    </div>
  ),
  api: ({ data }: { data: any }) => (
    <div className={`px-4 py-2 shadow-md rounded-md bg-green-100 border-2 ${
      data.status === 'failed' ? 'border-red-500' : 
      data.status === 'completed' ? 'border-green-500' : 'border-green-400'
    }`}>
      <div className="font-bold text-sm">{data.component}</div>
      <div className="text-xs text-gray-600">{data.operation}</div>
      {data.duration && (
        <div className="text-xs font-medium">{data.duration.toFixed(1)}ms</div>
      )}
    </div>
  ),
  database: ({ data }: { data: any }) => (
    <div className={`px-4 py-2 shadow-md rounded-md bg-yellow-100 border-2 ${
      data.status === 'failed' ? 'border-red-500' : 
      data.status === 'completed' ? 'border-green-500' : 'border-yellow-500'
    }`}>
      <div className="font-bold text-sm">{data.component}</div>
      <div className="text-xs text-gray-600">{data.operation}</div>
      {data.duration && (
        <div className="text-xs font-medium">{data.duration.toFixed(1)}ms</div>
      )}
    </div>
  ),
};

export function WorkflowTraceVisualization() {
  const [traces, setTraces] = useState<WorkflowTrace[]>([]);
  const [selectedTrace, setSelectedTrace] = useState<WorkflowTrace | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState({
    workflowType: '',
    status: '',
    timeRange: '1h',
  });

  useEffect(() => {
    fetchWorkflowTraces();
  }, [filter]);

  useEffect(() => {
    if (selectedTrace) {
      generateFlowVisualization(selectedTrace);
    }
  }, [selectedTrace]);

  const fetchWorkflowTraces = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter.workflowType) params.append('workflow_type', filter.workflowType);
      if (filter.status) params.append('status', filter.status);
      params.append('time_range', filter.timeRange);

      const response = await fetch(`/api/v1/debugging/workflow-traces/?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setTraces(data.results || data);
      
      // Auto-select the first trace if none selected
      if (data.results?.length > 0 && !selectedTrace) {
        setSelectedTrace(data.results[0]);
      }

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch traces');
    } finally {
      setLoading(false);
    }
  };

  const generateFlowVisualization = (trace: WorkflowTrace) => {
    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];

    // Group steps by layer for positioning
    const layerGroups = {
      frontend: trace.steps.filter(s => s.layer === 'frontend'),
      api: trace.steps.filter(s => s.layer === 'api'),
      database: trace.steps.filter(s => s.layer === 'database'),
    };

    let yOffset = 0;
    const layerSpacing = 200;
    const nodeSpacing = 150;

    // Create nodes for each layer
    Object.entries(layerGroups).forEach(([layer, steps], layerIndex) => {
      steps.forEach((step, stepIndex) => {
        const node: Node = {
          id: step.id,
          type: layer,
          position: {
            x: stepIndex * nodeSpacing,
            y: layerIndex * layerSpacing,
          },
          data: {
            component: step.component,
            operation: step.operation,
            duration: step.duration,
            status: step.status,
            layer: step.layer,
            metadata: step.metadata,
          },
        };
        newNodes.push(node);
      });
    });

    // Create edges based on timing and dependencies
    trace.steps.forEach((step, index) => {
      if (index > 0) {
        const prevStep = trace.steps[index - 1];
        const edge: Edge = {
          id: `${prevStep.id}-${step.id}`,
          source: prevStep.id,
          target: step.id,
          type: 'smoothstep',
          animated: step.status === 'started',
          style: {
            stroke: step.status === 'failed' ? '#ef4444' : 
                   step.status === 'completed' ? '#10b981' : '#6b7280',
            strokeWidth: 2,
          },
          label: step.duration ? `${step.duration.toFixed(1)}ms` : '',
        };
        newEdges.push(edge);
      }
    });

    setNodes(newNodes);
    setEdges(newEdges);
  };

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'in_progress': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms.toFixed(1)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const renderTraceList = () => (
    <div className="bg-white rounded-lg shadow p-4 h-full overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Workflow Traces</h3>
        <button
          onClick={fetchWorkflowTraces}
          className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="space-y-3 mb-4">
        <select
          value={filter.workflowType}
          onChange={(e) => setFilter(prev => ({ ...prev, workflowType: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
        >
          <option value="">All Workflow Types</option>
          <option value="user_login">User Login</option>
          <option value="product_fetch">Product Fetch</option>
          <option value="cart_update">Cart Update</option>
          <option value="checkout">Checkout</option>
        </select>

        <select
          value={filter.status}
          onChange={(e) => setFilter(prev => ({ ...prev, status: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
        >
          <option value="">All Statuses</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="in_progress">In Progress</option>
        </select>

        <select
          value={filter.timeRange}
          onChange={(e) => setFilter(prev => ({ ...prev, timeRange: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
        >
          <option value="1h">Last Hour</option>
          <option value="6h">Last 6 Hours</option>
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
        </select>
      </div>

      {/* Trace List */}
      <div className="space-y-2">
        {traces.map((trace) => (
          <div
            key={trace.correlationId}
            onClick={() => setSelectedTrace(trace)}
            className={`p-3 border rounded cursor-pointer transition-colors ${
              selectedTrace?.correlationId === trace.correlationId
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="font-medium text-sm">{trace.workflowType}</div>
              <div className={`px-2 py-1 rounded text-xs ${getStatusColor(trace.status)}`}>
                {trace.status}
              </div>
            </div>
            <div className="text-xs text-gray-500 mb-1">
              ID: {trace.correlationId.slice(0, 8)}...
            </div>
            <div className="flex items-center justify-between text-xs text-gray-600">
              <span>{new Date(trace.startTime).toLocaleTimeString()}</span>
              <span>{formatDuration(trace.totalDuration)}</span>
            </div>
            {trace.errors.length > 0 && (
              <div className="text-xs text-red-600 mt-1">
                {trace.errors.length} error(s)
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderTraceDetails = () => {
    if (!selectedTrace) {
      return (
        <div className="bg-white rounded-lg shadow p-8 flex items-center justify-center text-gray-500">
          Select a trace to view details
        </div>
      );
    }

    return (
      <div className="bg-white rounded-lg shadow p-4">
        <div className="mb-4">
          <h3 className="text-lg font-semibold mb-2">Trace Details</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">Workflow Type:</span> {selectedTrace.workflowType}
            </div>
            <div>
              <span className="font-medium">Status:</span>
              <span className={`ml-2 px-2 py-1 rounded text-xs ${getStatusColor(selectedTrace.status)}`}>
                {selectedTrace.status}
              </span>
            </div>
            <div>
              <span className="font-medium">Correlation ID:</span> {selectedTrace.correlationId}
            </div>
            <div>
              <span className="font-medium">Duration:</span> {formatDuration(selectedTrace.totalDuration)}
            </div>
            <div>
              <span className="font-medium">Steps:</span> {selectedTrace.steps.length}
            </div>
            <div>
              <span className="font-medium">Errors:</span> {selectedTrace.errors.length}
            </div>
          </div>
        </div>

        {/* Flow Visualization */}
        <div className="h-96 border border-gray-200 rounded">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
          >
            <Controls />
            <MiniMap />
            <Background />
            <Panel position="top-right">
              <div className="bg-white p-2 rounded shadow text-xs">
                <div className="flex items-center mb-1">
                  <div className="w-3 h-3 bg-blue-100 border border-blue-500 rounded mr-2"></div>
                  Frontend
                </div>
                <div className="flex items-center mb-1">
                  <div className="w-3 h-3 bg-green-100 border border-green-500 rounded mr-2"></div>
                  API
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-yellow-100 border border-yellow-500 rounded mr-2"></div>
                  Database
                </div>
              </div>
            </Panel>
          </ReactFlow>
        </div>

        {/* Step Details */}
        <div className="mt-4">
          <h4 className="font-medium mb-2">Step Timeline</h4>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {selectedTrace.steps.map((step, index) => (
              <div key={step.id} className="flex items-center text-sm p-2 bg-gray-50 rounded">
                <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-800 flex items-center justify-center text-xs font-medium mr-3">
                  {index + 1}
                </div>
                <div className="flex-1">
                  <div className="font-medium">{step.component} - {step.operation}</div>
                  <div className="text-xs text-gray-600">{step.layer}</div>
                </div>
                <div className="text-right">
                  <div className={`text-xs px-2 py-1 rounded ${getStatusColor(step.status)}`}>
                    {step.status}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">
                    {formatDuration(step.duration)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Errors */}
        {selectedTrace.errors.length > 0 && (
          <div className="mt-4">
            <h4 className="font-medium mb-2 text-red-800">Errors</h4>
            <div className="space-y-2">
              {selectedTrace.errors.map((error, index) => (
                <div key={index} className="p-3 bg-red-50 border border-red-200 rounded text-sm">
                  <div className="font-medium text-red-800">{error.component}</div>
                  <div className="text-red-700 mt-1">{error.error}</div>
                  <div className="text-xs text-red-600 mt-1">
                    {new Date(error.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="text-red-800">{error}</div>
        <button
          onClick={fetchWorkflowTraces}
          className="mt-2 text-sm bg-red-100 text-red-800 px-3 py-1 rounded hover:bg-red-200"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex space-x-6">
      {/* Trace List Sidebar */}
      <div className="w-80 flex-shrink-0">
        {renderTraceList()}
      </div>

      {/* Main Visualization Area */}
      <div className="flex-1">
        {renderTraceDetails()}
      </div>
    </div>
  );
}