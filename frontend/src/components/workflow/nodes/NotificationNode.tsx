'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export default function NotificationNode({ data, selected }: NodeProps) {
  const getNotificationIcon = (type: string) => {
    switch (type) {
      case "email":
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
            <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
          </svg>
        );
      case "sms":
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
          </svg>
        );
      case "push":
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 2L3 7v11a1 1 0 001 1h12a1 1 0 001-1V7l-7-5zM9 9a1 1 0 012 0v4a1 1 0 11-2 0V9zm1 8a1 1 0 100-2 1 1 0 000 2z" />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 2L3 7v11a1 1 0 001 1h12a1 1 0 001-1V7l-7-5z" />
          </svg>
        );
    }
  };

  return (
    <div className={`px-4 py-3 shadow-md rounded-lg bg-white border-2 ${
      selected ? 'border-blue-500' : 'border-purple-300'
    } min-w-[160px]`}>
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-purple-400 !border-2 !border-white"
      />
      
      <div className="flex items-center">
        <div className="w-8 h-8 flex items-center justify-center bg-purple-100 rounded-md mr-3">
          {getNotificationIcon(data.config?.type)}
        </div>
        <div className="flex-1">
          <div className="text-sm font-medium text-gray-900">
            {data.label || "Notification"}
          </div>
          <div className="text-xs text-gray-500 capitalize">
            {data.config?.type || "Email"}
          </div>
        </div>
      </div>
      
      {data.config?.subject && (
        <div className="mt-2 text-xs text-gray-600 truncate">
          {data.config.subject}
        </div>
      )}
      
      {data.config?.recipients && data.config.recipients.length > 0 && (
        <div className="mt-1 text-xs text-purple-600">
          {data.config.recipients.length} recipient(s)
        </div>
      )}
      
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-purple-400 !border-2 !border-white"
      />
    </div>
  );
}