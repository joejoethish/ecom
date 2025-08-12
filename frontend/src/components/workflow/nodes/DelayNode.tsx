'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export default function DelayNode({ data, selected }: NodeProps) {
  const formatDuration = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds}s`;
    } else if (seconds < 3600) {
      return `${Math.round(seconds / 60)}m`;
    } else if (seconds < 86400) {
      return `${Math.round(seconds / 3600)}h`;
    } else {
      return `${Math.round(seconds / 86400)}d`;
    }
  };

  return (
    <div className={`px-4 py-3 shadow-md rounded-lg bg-white border-2 ${
      selected ? 'border-blue-500' : 'border-amber-300'
    } min-w-[140px]`}>
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-amber-400 !border-2 !border-white"
      />
      
      <div className="flex items-center">
        <div className="w-8 h-8 flex items-center justify-center bg-amber-100 rounded-md mr-3">
          <svg className="w-4 h-4 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="flex-1">
          <div className="text-sm font-medium text-gray-900">
            {data.label || 'Delay'}
          </div>
          <div className="text-xs text-gray-500">
            Wait {formatDuration(data.config?.delay_seconds || 60)}
          </div>
        </div>
      </div>
      
      {data.config?.description && (
        <div className="mt-2 text-xs text-gray-600 truncate">
          {data.config.description}
        </div>
      )}
      
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-amber-400 !border-2 !border-white"
      />
    </div>
  );
}