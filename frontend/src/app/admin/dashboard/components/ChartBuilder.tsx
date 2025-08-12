'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Save, 
  Eye, 
  Settings, 
  Database, 
  Palette, 
  Layout,
  Filter,
  BarChart3,
  LineChart,
  PieChart,
  TrendingUp,
  Zap,
  Copy,
  Trash2
} from 'lucide-react';
import AdvancedChart from './AdvancedChart';

interface ChartTemplate {
  id: string;
  name: string;
  description: string;
  chartType: string;
  category: string;
  config: any;
  dataSource: string;
}

interface DataSource {
  id: string;
  name: string;
  endpoint: string;
  description: string;
  fields: Array<{
    name: string;
    type: string;
    description: string;
  }>;
}

interface ChartBuilderProps {
  initialChart?: any;
  templates?: ChartTemplate[];
  dataSources?: DataSource[];
  onSave?: (chart: any) => void;
  onCancel?: () => void;
  className?: string;
}

const ChartBuilder: React.FC<ChartBuilderProps> = ({
  initialChart,
  templates = [],
  dataSources = [],
  onSave,
  onCancel,
  className = '',
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [chart, setChart] = useState({
    title: '',
    description: '',
    chartType: 'line',
    dataSource: '',
    config: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: '',
        },
        legend: {
          display: true,
          position: 'top',
        },
        tooltip: {
          enabled: true,
        },
      },
      scales: {
        x: {
          display: true,
          title: {
            display: false,
            text: '',
          },
        },
        y: {
          display: true,
          beginAtZero: true,
          title: {
            display: false,
            text: '',
          },
        },
      },
    },
    theme: 'light',
    colors: ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6'],
    isRealTime: false,
    refreshInterval: 30000,
    ...initialChart,
  });
  
  const [previewData, setPreviewData] = useState({
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [{
      label: 'Sample Data',
      data: [12, 19, 3, 5, 2, 3],
      backgroundColor: '#3B82F6',
      borderColor: '#3B82F6',
    }],
  });
  
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [selectedDataSource, setSelectedDataSource] = useState<string>('');
  const [dataSourceFields, setDataSourceFields] = useState<any[]>([]);
  const [filters, setFilters] = useState<any[]>([]);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  const chartTypes = [
    { value: 'line', label: 'Line Chart', icon: LineChart, description: 'Show trends over time' },
    { value: 'bar', label: 'Bar Chart', icon: BarChart3, description: 'Compare categories' },
    { value: 'pie', label: 'Pie Chart', icon: PieChart, description: 'Show proportions' },
    { value: 'area', label: 'Area Chart', icon: TrendingUp, description: 'Filled line chart' },
    { value: 'doughnut', label: 'Doughnut Chart', icon: PieChart, description: 'Pie chart with center hole' },
    { value: 'radar', label: 'Radar Chart', icon: Zap, description: 'Multi-dimensional data' },
  ];

  const themes = [
    { value: 'light', label: 'Light', colors: ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6'] },
    { value: 'dark', label: 'Dark', colors: ['#60A5FA', '#F87171', '#34D399', '#FBBF24', '#A78BFA'] },
    { value: 'colorful', label: 'Colorful', colors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'] },
    { value: 'minimal', label: 'Minimal', colors: ['#6C7B7F', '#9B9B9B', '#C4C4C4', '#E0E0E0', '#F5F5F5'] },
  ];

  const steps = [
    { id: 1, title: 'Template & Type', icon: Layout },
    { id: 2, title: 'Data Source', icon: Database },
    { id: 3, title: 'Configuration', icon: Settings },
    { id: 4, title: 'Styling', icon: Palette },
    { id: 5, title: 'Preview & Save', icon: Eye },
  ];

  // Load template
  const handleTemplateSelect = useCallback((templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template) {
      setChart((prev: any) => ({
        ...prev,
        chartType: template.chartType,
        config: { ...prev.config, ...template.config },
        dataSource: template.dataSource,
      }));
      setSelectedTemplate(templateId);
      setSelectedDataSource(template.dataSource);
    }
  }, [templates]);

  // Load data source fields
  useEffect(() => {
    if (selectedDataSource) {
      const dataSource = dataSources.find(ds => ds.id === selectedDataSource);
      if (dataSource) {
        setDataSourceFields(dataSource.fields);
      }
    }
  }, [selectedDataSource, dataSources]);

  // Generate preview data
  const generatePreviewData = useCallback(async () => {
    if (!selectedDataSource) {
      // Generate sample data based on chart type
      const sampleLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
      const sampleData = Array.from({ length: 6 }, () => Math.floor(Math.random() * 100));
      
      setPreviewData({
        labels: sampleLabels,
        datasets: [{
          label: 'Sample Data',
          data: sampleData,
          backgroundColor: chart.colors[0],
          borderColor: chart.colors[0],
        }],
      });
      return;
    }

    try {
      setIsPreviewLoading(true);
      
      // Fetch preview data from selected data source
      const response = await fetch(`/api/admin/charts/preview-data/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          dataSource: selectedDataSource,
          chartType: chart.chartType,
          config: chart.config,
          filters: filters,
        }),
      });
      
      const data = await response.json();
      setPreviewData(data);
      
    } catch (error) {
      console.error('Failed to generate preview data:', error);
    } finally {
      setIsPreviewLoading(false);
    }
  }, [selectedDataSource, chart.chartType, chart.config, chart.colors, filters]);

  // Update preview when chart changes
  useEffect(() => {
    generatePreviewData();
  }, [generatePreviewData]);

  // Handle chart property changes
  const updateChart = useCallback((updates: any) => {
    setChart((prev: any) => ({ ...prev, ...updates }));
  }, []);

  const updateConfig = useCallback((configUpdates: any) => {
    setChart((prev: any) => ({
      ...prev,
      config: { ...prev.config, ...configUpdates },
    }));
  }, []);

  // Handle save
  const handleSave = useCallback(() => {
    if (onSave) {
      onSave({
        ...chart,
        dataSource: selectedDataSource,
      });
    }
  }, [chart, selectedDataSource, onSave]);

  // Render step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Choose Template or Chart Type
              </h3>
              
              {/* Templates */}
              {templates.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Templates
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {templates.map(template => (
                      <div
                        key={template.id}
                        className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                          selectedTemplate === template.id
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                        }`}
                        onClick={() => handleTemplateSelect(template.id)}
                      >
                        <div className="font-medium text-gray-900 dark:text-white">
                          {template.name}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {template.description}
                        </div>
                        <div className="text-xs text-gray-500 mt-2">
                          {template.category} • {template.chartType}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Chart Types */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Chart Types
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {chartTypes.map(type => {
                    const Icon = type.icon;
                    return (
                      <div
                        key={type.value}
                        className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                          chart.chartType === type.value
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                        }`}
                        onClick={() => updateChart({ chartType: type.value })}
                      >
                        <div className="flex items-center space-x-3">
                          <Icon className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                          <div>
                            <div className="font-medium text-gray-900 dark:text-white">
                              {type.label}
                            </div>
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                              {type.description}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Select Data Source
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {dataSources.map(dataSource => (
                  <div
                    key={dataSource.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedDataSource === dataSource.id
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedDataSource(dataSource.id)}
                  >
                    <div className="flex items-start space-x-3">
                      <Database className="w-6 h-6 text-gray-600 dark:text-gray-400 mt-1" />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 dark:text-white">
                          {dataSource.name}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {dataSource.description}
                        </div>
                        <div className="text-xs text-gray-500 mt-2">
                          {dataSource.fields.length} fields available
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Data Source Fields */}
              {dataSourceFields.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Available Fields
                  </h4>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {dataSourceFields.map(field => (
                        <div key={field.name} className="flex items-center justify-between">
                          <div>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              {field.name}
                            </span>
                            <span className="text-xs text-gray-500 ml-2">
                              ({field.type})
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Chart Configuration
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Basic Settings */}
                <div className="space-y-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Basic Settings
                  </h4>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Chart Title
                    </label>
                    <input
                      type="text"
                      value={chart.title}
                      onChange={(e) => updateChart({ title: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      placeholder="Enter chart title"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Description
                    </label>
                    <textarea
                      value={chart.description}
                      onChange={(e) => updateChart({ description: e.target.value })}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      placeholder="Enter chart description"
                    />
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="realTime"
                      checked={chart.isRealTime}
                      onChange={(e) => updateChart({ isRealTime: e.target.checked })}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                    <label htmlFor="realTime" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Enable real-time updates
                    </label>
                  </div>
                  
                  {chart.isRealTime && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Refresh Interval (seconds)
                      </label>
                      <input
                        type="number"
                        value={chart.refreshInterval / 1000}
                        onChange={(e) => updateChart({ refreshInterval: parseInt(e.target.value) * 1000 })}
                        min="5"
                        max="3600"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>
                  )}
                </div>
                
                {/* Display Options */}
                <div className="space-y-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Display Options
                  </h4>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="showTitle"
                      checked={chart.config.plugins?.title?.display}
                      onChange={(e) => updateConfig({
                        plugins: {
                          ...chart.config.plugins,
                          title: {
                            ...chart.config.plugins?.title,
                            display: e.target.checked,
                          },
                        },
                      })}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                    <label htmlFor="showTitle" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Show title
                    </label>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="showLegend"
                      checked={chart.config.plugins?.legend?.display}
                      onChange={(e) => updateConfig({
                        plugins: {
                          ...chart.config.plugins,
                          legend: {
                            ...chart.config.plugins?.legend,
                            display: e.target.checked,
                          },
                        },
                      })}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                    <label htmlFor="showLegend" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Show legend
                    </label>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="showGrid"
                      checked={chart.config.scales?.x?.grid?.display !== false}
                      onChange={(e) => updateConfig({
                        scales: {
                          ...chart.config.scales,
                          x: {
                            ...chart.config.scales?.x,
                            grid: { display: e.target.checked },
                          },
                          y: {
                            ...chart.config.scales?.y,
                            grid: { display: e.target.checked },
                          },
                        },
                      })}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                    <label htmlFor="showGrid" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Show grid lines
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Chart Styling
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Theme Selection */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Theme
                  </h4>
                  <div className="space-y-3">
                    {themes.map(theme => (
                      <div
                        key={theme.value}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                          chart.theme === theme.value
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                        }`}
                        onClick={() => updateChart({ theme: theme.value, colors: theme.colors })}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-gray-900 dark:text-white">
                            {theme.label}
                          </span>
                          <div className="flex space-x-1">
                            {theme.colors.slice(0, 5).map((color, index) => (
                              <div
                                key={index}
                                className="w-4 h-4 rounded-full"
                                style={{ backgroundColor: color }}
                              />
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Custom Colors */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Custom Colors
                  </h4>
                  <div className="space-y-3">
                    {chart.colors.map((color: string, index: number) => (
                      <div key={index} className="flex items-center space-x-3">
                        <input
                          type="color"
                          value={color}
                          onChange={(e) => {
                            const newColors = [...chart.colors];
                            newColors[index] = e.target.value;
                            updateChart({ colors: newColors });
                          }}
                          className="w-8 h-8 rounded border border-gray-300"
                        />
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          Color {index + 1}
                        </span>
                      </div>
                    ))}
                    <button
                      onClick={() => updateChart({ colors: [...chart.colors, '#000000'] })}
                      className="text-sm text-blue-600 hover:text-blue-700"
                    >
                      + Add Color
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Preview & Save
              </h3>
              
              {/* Chart Preview */}
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-6">
                <AdvancedChart
                  id="preview"
                  title={chart.title || 'Chart Preview'}
                  description={chart.description}
                  data={previewData}
                  config={chart.config}
                  theme={chart.theme}
                  colors={chart.colors}
                  isRealTime={chart.isRealTime}
                  refreshInterval={chart.refreshInterval}
                  height={400}
                  showControls={false}
                  isEmbedded={true}
                />
              </div>
              
              {/* Chart Summary */}
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                  Chart Summary
                </h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Type:</span>
                    <span className="ml-2 text-gray-900 dark:text-white">
                      {chartTypes.find(t => t.value === chart.chartType)?.label}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Data Source:</span>
                    <span className="ml-2 text-gray-900 dark:text-white">
                      {dataSources.find(ds => ds.id === selectedDataSource)?.name || 'Sample Data'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Theme:</span>
                    <span className="ml-2 text-gray-900 dark:text-white">
                      {themes.find(t => t.value === chart.theme)?.label}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Real-time:</span>
                    <span className="ml-2 text-gray-900 dark:text-white">
                      {chart.isRealTime ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={`bg-white dark:bg-gray-900 ${className}`}>
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {initialChart ? 'Edit Chart' : 'Create New Chart'}
          </h2>
          <div className="flex items-center space-x-3">
            {onCancel && (
              <button
                onClick={onCancel}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              >
                Cancel
              </button>
            )}
            <button
              onClick={handleSave}
              disabled={!chart.title || !selectedDataSource}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <Save className="w-4 h-4" />
              <span>Save Chart</span>
            </button>
          </div>
        </div>
      </div>

      {/* Steps Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center space-x-8">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = currentStep === step.id;
            const isCompleted = currentStep > step.id;
            
            return (
              <button
                key={step.id}
                onClick={() => setCurrentStep(step.id)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                    : isCompleted
                    ? 'text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="text-sm font-medium">{step.title}</span>
                {isCompleted && (
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Step Content */}
      <div className="p-6">
        {renderStepContent()}
      </div>

      {/* Navigation */}
      <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
            disabled={currentStep === 1}
            className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          
          <div className="flex items-center space-x-2">
            {steps.map((step) => (
              <div
                key={step.id}
                className={`w-2 h-2 rounded-full ${
                  currentStep === step.id
                    ? 'bg-blue-600'
                    : currentStep > step.id
                    ? 'bg-green-500'
                    : 'bg-gray-300 dark:bg-gray-600'
                }`}
              />
            ))}
          </div>
          
          <button
            onClick={() => setCurrentStep(Math.min(5, currentStep + 1))}
            disabled={currentStep === 5}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {currentStep === 5 ? 'Finish' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChartBuilder;