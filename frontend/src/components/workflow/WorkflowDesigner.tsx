'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { 
  ReactFlow, 
  MiniMap, 
  Controls, 
  Background, 
  useNodesState, 
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  NodeTypes,
  EdgeTypes
} from 'reactflow';
import 'reactflow/dist/style.css';

// Custom node components
import StartNode from './nodes/StartNode';
import EndNode from './nodes/EndNode';
import TaskNode from './nodes/TaskNode';
import DecisionNode from './nodes/DecisionNode';
import ApprovalNode from './nodes/ApprovalNode';
import NotificationNode from './nodes/NotificationNode';
import IntegrationNode from './nodes/IntegrationNode';
import DelayNode from './nodes/DelayNode';

// Toolbar and panels
import NodeToolbar from './NodeToolbar';
import PropertiesPanel from './PropertiesPanel';
import WorkflowSettings from './WorkflowSettings';

interface WorkflowDesignerProps {
  workflowId?: string;
  initialData?: {
    nodes: Node[];
    edges: Edge[];
    workflow_definition: any;
  };
  onSave?: (data: any) => void;
  onExecute?: (data: any) => void;
  readOnly?: boolean;
}

const nodeTypes: NodeTypes = {
  start: StartNode,
  end: EndNode,
  task: TaskNode,
  decision: DecisionNode,
  approval: ApprovalNode,
  notification: NotificationNode,
  integration: IntegrationNode,
  delay: DelayNode,
};

const WorkflowDesigner: React.FC<WorkflowDesignerProps> = ({
  workflowId,
  initialData,
  onSave,
  onExecute,
  readOnly = false
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialData?.nodes || []);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialData?.edges || []);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [workflowSettings, setWorkflowSettings] = useState(initialData?.workflow_definition || {});
  const [isValidating, setIsValidating] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const reactFlowInstance = useRef<any>(null);

  // Node creation counter for unique IDs
  const nodeIdCounter = useRef(1);

  const onConnect = useCallback(
    (params: Connection) => {
      if (readOnly || !params.source || !params.target) return;
      
      const edge: Edge = {
        ...params,
        source: params.source,
        target: params.target,
        id: `edge-${params.source}-${params.target}`,
        type: 'default',
        animated: false,
      };
      
      setEdges((eds) => addEdge(edge, eds));
    },
    [setEdges, readOnly]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    if (readOnly) return;
    setSelectedNode(node);
  }, [readOnly]);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const addNode = useCallback((nodeType: string) => {
    if (readOnly) return;
    
    const newNode: Node = {
      id: `${nodeType}-${nodeIdCounter.current++}`,
      type: nodeType,
      position: { x: 250, y: 250 },
      data: {
        label: `${nodeType.charAt(0).toUpperCase() + nodeType.slice(1)} Node`,
        config: getDefaultNodeConfig(nodeType),
      },
    };

    setNodes((nds) => nds.concat(newNode));
  }, [setNodes, readOnly]);

  const updateNodeData = useCallback((nodeId: string, newData: any) => {
    if (readOnly) return;
    
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...newData } }
          : node
      )
    );
  }, [setNodes, readOnly]);

  const deleteNode = useCallback((nodeId: string) => {
    if (readOnly) return;
    
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
    
    if (selectedNode?.id === nodeId) {
      setSelectedNode(null);
    }
  }, [setNodes, setEdges, selectedNode, readOnly]);

  const validateWorkflow = useCallback(() => {
    setIsValidating(true);
    const errors: string[] = [];

    // Check for start node
    const startNodes = nodes.filter(node => node.type === 'start');
    if (startNodes.length === 0) {
      errors.push('Workflow must have a start node');
    } else if (startNodes.length > 1) {
      errors.push('Workflow can only have one start node');
    }

    // Check for end nodes
    const endNodes = nodes.filter(node => node.type === 'end');
    if (endNodes.length === 0) {
      errors.push('Workflow must have at least one end node');
    }

    // Check for orphaned nodes
    const connectedNodeIds = new Set();
    edges.forEach(edge => {
      connectedNodeIds.add(edge.source);
      connectedNodeIds.add(edge.target);
    });

    const orphanedNodes = nodes.filter(node => 
      !connectedNodeIds.has(node.id) && nodes.length > 1
    );
    
    if (orphanedNodes.length > 0) {
      errors.push(`Found ${orphanedNodes.length} orphaned node(s)`);
    }

    // Check for cycles (simplified)
    const hasCycles = detectCycles(nodes, edges);
    if (hasCycles) {
      errors.push('Workflow contains cycles');
    }

    setValidationErrors(errors);
    setIsValidating(false);
    
    return errors.length === 0;
  }, [nodes, edges]);

  const handleSave = useCallback(() => {
    if (!validateWorkflow()) {
      return;
    }

    const workflowData = {
      nodes: nodes.map(node => ({
        id: node.id,
        type: node.type,
        name: node.data.label,
        position: node.position,
        config: node.data.config,
      })),
      connections: edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        condition: edge.data?.condition || {},
        label: edge.label || '',
      })),
      workflow_definition: workflowSettings,
    };

    onSave?.(workflowData);
  }, [nodes, edges, workflowSettings, validateWorkflow, onSave]);

  const handleExecute = useCallback(() => {
    if (!validateWorkflow()) {
      return;
    }

    const executionData = {
      workflow_id: workflowId,
      trigger_data: {},
    };

    onExecute?.(executionData);
  }, [workflowId, validateWorkflow, onExecute]);

  // Initialize React Flow instance
  const onInit = useCallback((instance: any) => {
    reactFlowInstance.current = instance;
  }, []);

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-semibold text-gray-900">Workflow Designer</h2>
          {validationErrors.length > 0 && (
            <div className="flex items-center text-red-600">
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span className="text-sm">{validationErrors.length} error(s)</span>
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowSettings(true)}
            className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Settings
          </button>
          
          {!readOnly && (
            <>
              <button
                onClick={validateWorkflow}
                disabled={isValidating}
                className="px-3 py-1.5 text-sm text-blue-600 hover:text-blue-700 border border-blue-300 rounded-md hover:bg-blue-50 disabled:opacity-50"
              >
                {isValidating ? 'Validating...' : 'Validate'}
              </button>
              
              <button
                onClick={handleSave}
                className="px-3 py-1.5 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-md"
              >
                Save
              </button>
            </>
          )}
          
          <button
            onClick={handleExecute}
            disabled={validationErrors.length > 0}
            className="px-3 py-1.5 text-sm text-white bg-green-600 hover:bg-green-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Execute
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex">
        {/* Node toolbar */}
        {!readOnly && (
          <div className="w-64 bg-white border-r border-gray-200">
            <NodeToolbar onAddNode={addNode} />
          </div>
        )}

        {/* Flow canvas */}
        <div className="flex-1 relative" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            onInit={onInit}
            nodeTypes={nodeTypes}
            fitView
            attributionPosition="bottom-left"
            className="bg-gray-50"
          >
            <MiniMap />
            <Controls />
            <Background color="#aaa" gap={16} />
          </ReactFlow>
        </div>

        {/* Properties panel */}
        {selectedNode && !readOnly && (
          <div className="w-80 bg-white border-l border-gray-200">
            <PropertiesPanel
              node={selectedNode}
              onUpdateNode={updateNodeData}
              onDeleteNode={deleteNode}
            />
          </div>
        )}
      </div>

      {/* Validation errors */}
      {validationErrors.length > 0 && (
        <div className="bg-red-50 border-t border-red-200 px-4 py-3">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Validation Errors
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <ul className="list-disc pl-5 space-y-1">
                  {validationErrors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Settings modal */}
      {showSettings && (
        <WorkflowSettings
          settings={workflowSettings}
          onSave={setWorkflowSettings}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
};

// Helper functions
function getDefaultNodeConfig(nodeType: string): any {
  switch (nodeType) {
    case 'task':
      return {
        task_type: 'custom',
        description: '',
        timeout: 300,
      };
    case 'decision':
      return {
        condition: {
          field: '',
          operator: 'equals',
          value: '',
        },
      };
    case 'approval':
      return {
        approver_id: '',
        request_data: {},
        timeout: 86400, // 24 hours
      };
    case 'notification':
      return {
        type: 'email',
        recipients: [],
        subject: '',
        message: '',
      };
    case 'integration':
      return {
        integration_id: '',
        method: 'GET',
        endpoint: '',
        payload: {},
      };
    case 'delay':
      return {
        delay_seconds: 60,
      };
    default:
      return {};
  }
}

function detectCycles(nodes: Node[], edges: Edge[]): boolean {
  // Build adjacency list
  const graph: { [key: string]: string[] } = {};
  nodes.forEach(node => {
    graph[node.id] = [];
  });
  
  edges.forEach(edge => {
    if (graph[edge.source]) {
      graph[edge.source].push(edge.target);
    }
  });

  // DFS to detect cycles
  const visited = new Set<string>();
  const recStack = new Set<string>();

  function dfs(nodeId: string): boolean {
    if (recStack.has(nodeId)) {
      return true; // Cycle detected
    }
    if (visited.has(nodeId)) {
      return false;
    }

    visited.add(nodeId);
    recStack.add(nodeId);

    for (const neighbor of graph[nodeId] || []) {
      if (dfs(neighbor)) {
        return true;
      }
    }

    recStack.delete(nodeId);
    return false;
  }

  for (const nodeId of Object.keys(graph)) {
    if (!visited.has(nodeId)) {
      if (dfs(nodeId)) {
        return true;
      }
    }
  }

  return false;
}

export default WorkflowDesigner;