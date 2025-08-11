'use client';

import React, { useState } from 'react';

interface WorkflowSettingsProps {
  settings: any;
  onSave: (settings: any) => void;
  onClose: () => void;
}

const WorkflowSettings: React.FC<WorkflowSettingsProps> = ({
  settings,
  onSave,
  onClose,
}) => {
  const [formData, setFormData] = useState({
    name: settings.name || '',
    description: settings.description || '',
    trigger_type: settings.trigger_type || 'manual',
    trigger_config: settings.trigger_config || {},
    variables: settings.variables || {},
    timeout: settings.timeout || 3600,
    retry_count: settings.retry_count || 3,
    retry_delay: settings.retry_delay || 60,
    error_handling: settings.error_handling || 'stop',
    notifications: settings.notifications || {
      on_success: false,
      on_failure: true,
      recipients: [],
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
    onClose();
  };

  const handleVariableChange = (key: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      variables: {
        ...prev.variables,
        [key]: value,
      },
    }));
  };

  const addVariable = () => {
    const key = prompt('Variable name:');
    if (key && !formData.variables[key]) {
      handleVariableChange(key, '');
    }
  };

  const removeVariable = (key: string) => {
    const newVariables = { ...formData.variables };
    delete newVariables[key];
    setFormData(prev => ({
      ...prev,
      variables: newVariables,
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Workflow Settings</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-md font-medium text-gray-900">Basic Information</h3>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Workflow Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter workflow name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Describe what this workflow does"
              />
            </div>
          </div>

          {/* Trigger Configuration */}
          <div className="space-y-4">
            <h3 className="text-md font-medium text-gray-900">Trigger Configuration</h3>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Trigger Type
              </label>
              <select
                value={formData.trigger_type}
                onChange={(e) => setFormData(prev => ({ ...prev, trigger_type: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="manual">Manual</option>
                <option value="scheduled">Scheduled</option>
                <option value="event">Event-based</option>
                <option value="webhook">Webhook</option>
                <option value="api">API Call</option>
              </select>
            </div>

            {formData.trigger_type === 'scheduled' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cron Expression
                </label>
                <input
                  type="text"
                  value={formData.trigger_config.cron || ''}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    trigger_config: { ...prev.trigger_config, cron: e.target.value }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0 0 * * *"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Example: "0 0 * * *" runs daily at midnight
                </p>
              </div>
            )}

            {formData.trigger_type === 'event' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Event Type
                </label>
                <select
                  value={formData.trigger_config.event_type || ''}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    trigger_config: { ...prev.trigger_config, event_type: e.target.value }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select event type</option>
                  <option value="order_created">Order Created</option>
                  <option value="order_updated">Order Updated</option>
                  <option value="customer_registered">Customer Registered</option>
                  <option value="product_updated">Product Updated</option>
                  <option value="inventory_low">Low Inventory</option>
                </select>
              </div>
            )}
          </div>

          {/* Execution Settings */}
          <div className="space-y-4">
            <h3 className="text-md font-medium text-gray-900">Execution Settings</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Timeout (seconds)
                </label>
                <input
                  type="number"
                  value={formData.timeout}
                  onChange={(e) => setFormData(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Retry Count
                </label>
                <input
                  type="number"
                  value={formData.retry_count}
                  onChange={(e) => setFormData(prev => ({ ...prev, retry_count: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Error Handling
              </label>
              <select
                value={formData.error_handling}
                onChange={(e) => setFormData(prev => ({ ...prev, error_handling: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="stop">Stop on Error</option>
                <option value="continue">Continue on Error</option>
                <option value="retry">Retry on Error</option>
              </select>
            </div>
          </div>

          {/* Variables */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-md font-medium text-gray-900">Variables</h3>
              <button
                type="button"
                onClick={addVariable}
                className="px-3 py-1 text-sm text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50"
              >
                Add Variable
              </button>
            </div>

            <div className="space-y-2">
              {Object.entries(formData.variables).map(([key, value]) => (
                <div key={key} className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={key}
                    disabled
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                  />
                  <input
                    type="text"
                    value={value as string}
                    onChange={(e) => handleVariableChange(key, e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Variable value"
                  />
                  <button
                    type="button"
                    onClick={() => removeVariable(key)}
                    className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Notifications */}
          <div className="space-y-4">
            <h3 className="text-md font-medium text-gray-900">Notifications</h3>
            
            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.notifications.on_success}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    notifications: { ...prev.notifications, on_success: e.target.checked }
                  }))}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Notify on successful completion</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.notifications.on_failure}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    notifications: { ...prev.notifications, on_failure: e.target.checked }
                  }))}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Notify on failure</span>
              </label>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notification Recipients
                </label>
                <input
                  type="text"
                  value={(formData.notifications.recipients || []).join(', ')}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    notifications: {
                      ...prev.notifications,
                      recipients: e.target.value.split(',').map(r => r.trim()).filter(r => r)
                    }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="admin@example.com, manager@example.com"
                />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              Save Settings
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default WorkflowSettings;