'use client';

import React from 'react';

interface NodeToolbarProps {
  onAddNode: (nodeType: string) => void;
}

const nodeCategories = [
  {
    name: 'Flow Control',
    nodes: [
      {
        type: 'start',
        name: 'Start',
        icon: '▶️',
        description: 'Workflow entry point',
      },
      {
        type: 'end',
        name: 'End',
        icon: '⏹️',
        description: 'Workflow completion',
      },
      {
        type: 'decision',
        name: 'Decision',
        icon: '🔀',
        description: 'Conditional branching',
      },
    ],
  },
  {
    name: 'Actions',
    nodes: [
      {
        type: 'task',
        name: 'Task',
        icon: '⚙️',
        description: 'Execute custom task',
      },
      {
        type: 'approval',
        name: 'Approval',
        icon: '✅',
        description: 'Request approval',
      },
      {
        type: 'notification',
        name: 'Notification',
        icon: '📧',
        description: 'Send notification',
      },
      {
        type: 'integration',
        name: 'Integration',
        icon: '🔗',
        description: 'External system call',
      },
      {
        type: 'delay',
        name: 'Delay',
        icon: '⏰',
        description: 'Wait for specified time',
      },
    ],
  },
];

export default function NodeToolbar({ onAddNode }: NodeToolbarProps) {
  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-4">Workflow Nodes</h3>
        
        {nodeCategories.map((category) => (
          <div key={category.name} className="mb-6">
            <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
              {category.name}
            </h4>
            
            <div className="space-y-2">
              {category.nodes.map((node) => (
                <button
                  key={node.type}
                  onClick={() => onAddNode(node.type)}
                  className="w-full flex items-center p-3 text-left border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors group"
                >
                  <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-gray-100 rounded-md group-hover:bg-blue-100 mr-3">
                    <span className="text-lg">{node.icon}</span>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 group-hover:text-blue-900">
                      {node.name}
                    </p>
                    <p className="text-xs text-gray-500 group-hover:text-blue-700 truncate">
                      {node.description}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ))}
        
        {/* Quick Actions */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
            Quick Actions
          </h4>
          
          <div className="space-y-2">
            <button
              onClick={() => {
                onAddNode("start");
                onAddNode("task");
                onAddNode("end");
              }}
              className="w-full px-3 py-2 text-sm text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50"
            >
              Create Basic Flow
            </button>
            
            <button
              onClick={() => {
                onAddNode("start");
                onAddNode("approval");
                onAddNode("notification");
                onAddNode("end");
              }}
              className="w-full px-3 py-2 text-sm text-green-600 border border-green-300 rounded-md hover:bg-green-50"
            >
              Create Approval Flow
            </button>
          </div>
        </div>
        
        {/* Templates */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
            Templates
          </h4>
          
          <div className="space-y-2">
            <button className="w-full px-3 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">
              Order Processing
            </button>
            <button className="w-full px-3 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">
              Customer Onboarding
            </button>
            <button className="w-full px-3 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">
              Inventory Alert
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}