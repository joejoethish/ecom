'use client';

import React, { useState, useEffect } from 'react';
import { Node } from 'reactflow';

interface PropertiesPanelProps {
  node: Node;
  onUpdateNode: (nodeId: string, data: any) => void;
  onDeleteNode: (nodeId: string) => void;
}

const PropertiesPanel: React.FC<PropertiesPanelProps> = ({
  node,
  onUpdateNode,
  onDeleteNode,
}) => {
  const [nodeData, setNodeData] = useState(node.data);

  useEffect(() => {
    setNodeData(node.data);
  }, [node]);

  const handleUpdate = (field: string, value: any) => {
    const updatedData = {
      ...nodeData,
      [field]: value,
    };
    setNodeData(updatedData);
    onUpdateNode(node.id, updatedData);
  };

  const handleConfigUpdate = (configField: string, value: any) => {
    const updatedConfig = {
      ...nodeData.config,
      [configField]: value,
    };
    const updatedData = {
      ...nodeData,
      config: updatedConfig,
    };
    setNodeData(updatedData);
    onUpdateNode(node.id, updatedData);
  };

  const renderNodeSpecificFields = () => {
    switch (node.type) {
      case 'task':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Task Type
              </label>
              <select
                value={nodeData.config?.task_type || 'custom'}
                onChange={(e) => handleConfigUpdate('task_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="custom">Custom Task</option>
                <option value="data_transformation">Data Transformation</option>
                <option value="api_call">API Call</option>
                <option value="database_operation">Database Operation</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={nodeData.config?.description || ''}
                onChange={(e) => handleConfigUpdate('description', e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Describe what this task does..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Timeout (seconds)
              </label>
              <input
                type="number"
                value={nodeData.config?.timeout || 300}
                onChange={(e) => handleConfigUpdate('timeout', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        );

      case 'decision':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Field to Check
              </label>
              <input
                type="text"
                value={nodeData.config?.condition?.field || ''}
                onChange={(e) => handleConfigUpdate('condition', {
                  ...nodeData.config?.condition,
                  field: e.target.value
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., order.status"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Operator
              </label>
              <select
                value={nodeData.config?.condition?.operator || 'equals'}
                onChange={(e) => handleConfigUpdate('condition', {
                  ...nodeData.config?.condition,
                  operator: e.target.value
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="equals">Equals</option>
                <option value="not_equals">Not Equals</option>
                <option value="greater_than">Greater Than</option>
                <option value="less_than">Less Than</option>
                <option value="contains">Contains</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Value
              </label>
              <input
                type="text"
                value={nodeData.config?.condition?.value || ''}
                onChange={(e) => handleConfigUpdate('condition', {
                  ...nodeData.config?.condition,
                  value: e.target.value
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Value to compare against"
              />
            </div>
          </div>
        );

      case 'approval':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Approver
              </label>
              <select
                value={nodeData.config?.approver_id || ''}
                onChange={(e) => handleConfigUpdate('approver_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select approver...</option>
                <option value="manager">Manager</option>
                <option value="admin">Administrator</option>
                <option value="supervisor">Supervisor</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Approval Message
              </label>
              <textarea
                value={nodeData.config?.message || ''}
                onChange={(e) => handleConfigUpdate('message', e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Message to show to approver..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Timeout (hours)
              </label>
              <input
                type="number"
                value={(nodeData.config?.timeout || 86400) / 3600}
                onChange={(e) => handleConfigUpdate('timeout', parseInt(e.target.value) * 3600)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        );

      case 'notification':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notification Type
              </label>
              <select
                value={nodeData.config?.type || 'email'}
                onChange={(e) => handleConfigUpdate('type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="push">Push Notification</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Recipients
              </label>
              <input
                type="text"
                value={(nodeData.config?.recipients || []).join(', ')}
                onChange={(e) => handleConfigUpdate('recipients', e.target.value.split(',').map(r => r.trim()))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="email1@example.com, email2@example.com"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subject
              </label>
              <input
                type="text"
                value={nodeData.config?.subject || ''}
                onChange={(e) => handleConfigUpdate('subject', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Notification subject"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Message
              </label>
              <textarea
                value={nodeData.config?.message || ''}
                onChange={(e) => handleConfigUpdate('message', e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Notification message..."
              />
            </div>
          </div>
        );

      case 'integration':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Integration
              </label>
              <select
                value={nodeData.config?.integration_id || ''}
                onChange={(e) => handleConfigUpdate('integration_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select integration...</option>
                <option value="api-1">External API</option>
                <option value="webhook-1">Webhook Service</option>
                <option value="email-1">Email Service</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                HTTP Method
              </label>
              <select
                value={nodeData.config?.method || 'GET'}
                onChange={(e) => handleConfigUpdate('method', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Endpoint
              </label>
              <input
                type="text"
                value={nodeData.config?.endpoint || ''}
                onChange={(e) => handleConfigUpdate('endpoint', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="/api/endpoint"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Payload (JSON)
              </label>
              <textarea
                value={JSON.stringify(nodeData.config?.payload || {}, null, 2)}
                onChange={(e) => {
                  try {
                    const payload = JSON.parse(e.target.value);
                    handleConfigUpdate('payload', payload);
                  } catch (error) {
                    // Invalid JSON, don't update
                  }
                }}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                placeholder='{"key": "value"}'
              />
            </div>
          </div>
        );

      case 'delay':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Delay Duration
              </label>
              <div className="flex space-x-2">
                <input
                  type="number"
                  value={nodeData.config?.delay_seconds || 60}
                  onChange={(e) => handleConfigUpdate('delay_seconds', parseInt(e.target.value))}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <select
                  value="seconds"
                  onChange={(e) => {
                    const multiplier = e.target.value === 'minutes' ? 60 : e.target.value === 'hours' ? 3600 : 1;
                    const currentValue = nodeData.config?.delay_seconds || 60;
                    handleConfigUpdate('delay_seconds', currentValue * multiplier);
                  }}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="seconds">Seconds</option>
                  <option value="minutes">Minutes</option>
                  <option value="hours">Hours</option>
                </select>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={nodeData.config?.description || ''}
                onChange={(e) => handleConfigUpdate('description', e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Why is this delay needed?"
              />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-900">Node Properties</h3>
          <button
            onClick={() => onDeleteNode(node.id)}
            className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
            title="Delete node"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clipRule="evenodd" />
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414L9.586 12l-2.293 2.293a1 1 0 101.414 1.414L10 13.414l1.293 1.293a1 1 0 001.414-1.414L11.414 12l1.293-1.293z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Basic properties */}
        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Node ID
            </label>
            <input
              type="text"
              value={node.id}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Node Type
            </label>
            <input
              type="text"
              value={node.type}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 capitalize"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Label
            </label>
            <input
              type="text"
              value={nodeData.label || ''}
              onChange={(e) => handleUpdate('label', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Node label"
            />
          </div>
        </div>

        {/* Node-specific properties */}
        {node.type !== 'start' && node.type !== 'end' && (
          <div className="border-t border-gray-200 pt-4">
            <h4 className="text-sm font-medium text-gray-900 mb-4">Configuration</h4>
            {renderNodeSpecificFields()}
          </div>
        )}

        {/* Position info */}
        <div className="border-t border-gray-200 pt-4 mt-6">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Position</h4>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs text-gray-500 mb-1">X</label>
              <input
                type="number"
                value={Math.round(node.position.x)}
                disabled
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded bg-gray-50 text-gray-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Y</label>
              <input
                type="number"
                value={Math.round(node.position.y)}
                disabled
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded bg-gray-50 text-gray-500"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PropertiesPanel;