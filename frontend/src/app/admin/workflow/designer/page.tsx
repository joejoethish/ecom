'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import WorkflowDesigner from '@/components/workflow/WorkflowDesigner';

const WorkflowDesignerPage: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const workflowId = searchParams.get('id');
  
  const [workflowData, setWorkflowData] = useState<any>(null);
  const [loading, setLoading] = useState(!!workflowId);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (workflowId) {
      // Load existing workflow data
      // This would be an API call in a real implementation
      setTimeout(() => {
        setWorkflowData({
          id: workflowId,
          name: 'Sample Workflow',
          nodes: [
            {
              id: 'start-1',
              type: 'start',
              position: { x: 100, y: 100 },
              data: { label: 'Start' },
            },
            {
              id: 'task-1',
              type: 'task',
              position: { x: 300, y: 100 },
              data: {
                label: 'Process Order',
                config: {
                  task_type: 'custom',
                  description: 'Process the incoming order',
                  timeout: 300,
                },
              },
            },
            {
              id: 'end-1',
              type: 'end',
              position: { x: 500, y: 100 },
              data: { label: 'End' },
            },
          ],
          edges: [
            {
              id: 'edge-1',
              source: 'start-1',
              target: 'task-1',
              type: 'default',
            },
            {
              id: 'edge-2',
              source: 'task-1',
              target: 'end-1',
              type: 'default',
            },
          ],
          workflow_definition: {
            name: 'Sample Workflow',
            description: 'A sample workflow for demonstration',
            trigger_type: 'manual',
          },
        });
        setLoading(false);
      }, 1000);
    }
  }, [workflowId]);

  const handleSave = async (data: any) => {
    setSaving(true);
    
    try {
      // Save workflow data
      // This would be an API call in a real implementation
      console.log('Saving workflow:', data);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Show success message
      alert('Workflow saved successfully!');
      
      // Redirect to workflow list if this is a new workflow
      if (!workflowId) {
        router.push('/admin/workflow');
      }
    } catch (error) {
      console.error('Error saving workflow:', error);
      alert('Error saving workflow. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleExecute = async (data: any) => {
    try {
      // Execute workflow
      // This would be an API call in a real implementation
      console.log('Executing workflow:', data);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Show success message
      alert('Workflow execution started!');
      
      // Redirect to executions view
      router.push('/admin/workflow?tab=executions');
    } catch (error) {
      console.error('Error executing workflow:', error);
      alert('Error executing workflow. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading workflow...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => router.back()}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">
              {workflowId ? 'Edit Workflow' : 'Create New Workflow'}
            </h1>
            <p className="text-sm text-gray-600">
              Design your automated workflow using the visual editor
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {saving && (
            <div className="flex items-center text-blue-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
              <span className="text-sm">Saving...</span>
            </div>
          )}
          
          <button
            onClick={() => router.push('/admin/workflow/templates')}
            className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Use Template
          </button>
        </div>
      </div>

      {/* Designer */}
      <div className="flex-1">
        <WorkflowDesigner
          workflowId={workflowId || undefined}
          initialData={workflowData}
          onSave={handleSave}
          onExecute={handleExecute}
        />
      </div>

      {/* Help Panel */}
      <div className="bg-gray-50 border-t border-gray-200 px-4 py-2">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center space-x-6">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
              <span>Start Node</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
              <span>End Node</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
              <span>Task Node</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
              <span>Decision Node</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <span>Drag nodes from the toolbar to create your workflow</span>
            <button
              onClick={() => window.open('/docs/workflow-designer', '_blank')}
              className="text-blue-600 hover:text-blue-800"
            >
              View Documentation
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowDesignerPage;