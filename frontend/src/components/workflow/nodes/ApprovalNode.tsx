'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export default function ApprovalNode({ data, selected }: NodeProps) {
  return (
    <div className={`px-4 py-3 shadow-md rounded-lg bg-white border-2 ${
      selected ? 'border-blue-500' : 'border-orange-300'
    } min-w-[160px]`}>
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-orange-400 !border-2 !border-white"
      />
      
      <div className="flex items-center">
        <div className="w-8 h-8 flex items-center justify-center bg-orange-100 rounded-md mr-3">
          <svg className="w-4 h-4 text-orange-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="flex-1">
          <div className="text-sm font-medium text-gray-900">
            {data.label || 'Approval'}
          </div>
          <div className="text-xs text-gray-500">
            {data.config?.approver_id ? `By ${data.config.approver_id}` : 'Needs approver'}
          </div>
        </div>
      </div>
      
      {data.config?.message && (
        <div className="mt-2 text-xs text-gray-600 truncate">
          {data.config.message}
        </div>
      )}
      
      {/* Timeout indicator */}
      {data.config?.timeout && (
        <div className="mt-1 text-xs text-orange-600">
          Timeout: {Math.round(data.config.timeout / 3600)}h
        </div>
      )}
      
      <Handle
        type="source"
        position={Position.Right}
        id="approved"
        className="w-3 h-3 !bg-green-500 !border-2 !border-white"
        style={{ top: '30%' }}
      />
      
      <Handle
        type="source"
        position={Position.Right}
        id="rejected"
        className="w-3 h-3 !bg-red-500 !border-2 !border-white"
        style={{ top: '70%' }}
      />
    </div>
  );
}