'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

  return (
    <div className="relative">
      <div className={`w-24 h-24 transform rotate-45 bg-yellow-400 border-2 ${
        selected ? 'border-blue-500' : 'border-yellow-500'
      } shadow-md`}>
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 !bg-yellow-500 !border-2 !border-white !-translate-x-1/2 !-translate-y-1/2"
          style={{ left: '0%', top: '50%' }}
        />
        
        <Handle
          type="source"
          position={Position.Top}
          id="yes"
          className="w-3 h-3 !bg-green-500 !border-2 !border-white !-translate-x-1/2 !-translate-y-1/2"
          style={{ left: '50%', top: '0%' }}
        />
        
        <Handle
          type="source"
          position={Position.Bottom}
          id="no"
          className="w-3 h-3 !bg-red-500 !border-2 !border-white !-translate-x-1/2 !translate-y-1/2"
          style={{ left: '50%', top: '100%' }}
        />
      </div>
      
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="text-center">
          <div className="w-6 h-6 mx-auto mb-1 flex items-center justify-center">
            <svg className="w-4 h-4 text-yellow-800" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="text-xs font-medium text-yellow-800 whitespace-nowrap">
            {data.label || &apos;Decision&apos;}
          </div>
        </div>
      </div>
      
      {/* Labels for Yes/No paths */}
      <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs font-medium text-green-600 bg-white px-1 rounded">
        Yes
      </div>
      <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 text-xs font-medium text-red-600 bg-white px-1 rounded">
        No
      </div>
    </div>
  );
};

export default DecisionNode;