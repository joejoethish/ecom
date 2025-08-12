'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export default function IntegrationNode({ data, selected }: NodeProps) {
  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET':
        return 'text-green-600 bg-green-100';
      case 'POST':
        return 'text-blue-600 bg-blue-100';
      case 'PUT':
        return 'text-yellow-600 bg-yellow-100';
      case 'DELETE':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className={`px-4 py-3 shadow-md rounded-lg bg-white border-2 ${
      selected ? 'border-blue-500' : 'border-indigo-300'
    } min-w-[160px]`}>
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-indigo-400 !border-2 !border-white"
      />
      
      <div className="flex items-center">
        <div className="w-8 h-8 flex items-center justify-center bg-indigo-100 rounded-md mr-3">
          <svg className="w-4 h-4 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="flex-1">
          <div className="text-sm font-medium text-gray-900">
            {data.label || 'Integration'}
          </div>
          <div className="text-xs text-gray-500">
            {data.config?.integration_id || 'No integration'}
          </div>
        </div>
      </div>
      
      {data.config?.method && (
        <div className="mt-2 flex items-center justify-between">
          <span className={`px-2 py-1 text-xs font-medium rounded ${getMethodColor(data.config.method)}`}>
            {data.config.method}
          </span>
          {data.config?.endpoint && (
            <span className="text-xs text-gray-500 truncate ml-2">
              {data.config.endpoint}
            </span>
          )}
        </div>
      )}
      
      <Handle
        type="source"
        position={Position.Right}
        id="success"
        className="w-3 h-3 !bg-green-500 !border-2 !border-white"
        style={{ top: '30%' }}
      />
      
      <Handle
        type="source"
        position={Position.Right}
        id="error"
        className="w-3 h-3 !bg-red-500 !border-2 !border-white"
        style={{ top: '70%' }}
      />
    </div>
  );
}