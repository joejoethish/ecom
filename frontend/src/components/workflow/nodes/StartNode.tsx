'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
export default function StartNode({ data, selected }: NodeProps) {
  return (
    <div className={`px-4 py-2 shadow-md rounded-full bg-green-500 text-white border-2 ${
      selected ? 'border-blue-500' : 'border-green-600'
    }`}>
      <div className="flex items-center">
        <div className="w-6 h-6 flex items-center justify-center mr-2">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="text-sm font-medium">
          {data.label || "Start"}
        </div>
      </div>
      
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-green-600 !border-2 !border-white"
      />
    </div>
  );
};
