/**
 * Main Debugging Dashboard Component
 * 
 * Provides a comprehensive interface for system monitoring, workflow tracing,
 * and debugging tools with real-time updates.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { SystemHealthPanel } from './SystemHealthPanel';
import { WorkflowTraceVisualization } from './WorkflowTraceVisualization';
import { DebuggingToolsInterface } from './DebuggingToolsInterface';
import { ErrorAnalysisInterface } from './ErrorAnalysisInterface';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useCorrelationId } from '@/hooks/useCorrelationId';
import { ConnectionState } from '@/hooks/useWebSocket';

interface DashboardTab {
  id: string;
  label: string;
  icon: React.ReactNode;
  component: React.ComponentType;
}

export function DebuggingDashboard() {
  const [activeTab, setActiveTab] = useState('health');
  const [isConnected, setIsConnected] = useState(false);
  const { correlationId } = useCorrelationId();

  // WebSocket connection for real-time updates
  const { 
    connectionState, 
    sendMessage, 
    lastMessage 
  } = useWebSocket({
    url: '/ws/debugging/',
    onOpen: () => setIsConnected(true),
    onClose: () => setIsConnected(false),
    onError: (error: Event) => console.error('WebSocket error:', error),
  });

  useEffect(() => {
    setIsConnected(connectionState === ConnectionState.OPEN);
  }, [connectionState]);

  const tabs: DashboardTab[] = [
    {
      id: 'health',
      label: 'System Health',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      component: SystemHealthPanel,
    },
    {
      id: 'traces',
      label: 'Workflow Traces',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      component: WorkflowTraceVisualization,
    },
    {
      id: 'tools',
      label: 'Debug Tools',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
      component: DebuggingToolsInterface,
    },
    {
      id: 'errors',
      label: 'Error Analysis',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      ),
      component: ErrorAnalysisInterface,
    },
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || SystemHealthPanel;

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar Navigation */}
      <div className="w-64 bg-white shadow-lg">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-gray-900">Debug Dashboard</h1>
          <div className="mt-2 flex items-center">
            <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          {correlationId && (
            <div className="mt-2 text-xs text-gray-500 font-mono">
              ID: {correlationId.slice(0, 8)}...
            </div>
          )}
        </div>

        <nav className="mt-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center px-6 py-3 text-left hover:bg-gray-50 transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-50 border-r-2 border-blue-500 text-blue-700'
                  : 'text-gray-700'
              }`}
            >
              <span className="mr-3">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Quick Actions */}
        <div className="absolute bottom-0 left-0 right-0 w-64 p-6 border-t">
          <div className="space-y-2">
            <button
              onClick={() => sendMessage({ type: 'refresh_data' })}
              className="w-full px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Refresh Data
            </button>
            <button
              onClick={() => window.location.reload()}
              className="w-full px-3 py-2 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
            >
              Reset Dashboard
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full p-6">
          <ActiveComponent />
        </div>
      </div>
    </div>
  );
}