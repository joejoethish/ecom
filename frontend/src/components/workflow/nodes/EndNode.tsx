'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export default function EndNode({ data, selected }: NodeProps) {
  return (
    <div className={`px-4 py-2 shadow-md rounded-full bg-red-500 text-white border-2 ${
      selected ? 'border-blue-500' : 'border-red-600'
    }`}>
      <div className="flex items-center">
        <div className="w-6 h-6 flex items-center justify-center mr-2">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 012 0v4l.707.707a1 1 0 11-1.414 1.414L8 11.828V7z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="text-sm font-medium">
          {data.label || 'End'}
        </div>
      </div>
      
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-red-600 !border-2 !border-white"
      />
    </div>
  );
}