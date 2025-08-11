'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Plus, 
  Search, 
  Filter, 
  Download, 
  Share2, 
  Edit, 
  Trash2, 
  Copy, 
  Eye,
  BarChart3,
  LineChart,
  PieChart,
  TrendingUp,
  Zap,
  Clock,
  Users,
  Star,
  MoreVertical
} from 'lucide-react';
import AdvancedChart from '../components/AdvancedChart';
import ChartBuilder from '../components/ChartBuilder';

interface Chart {
  id: string;
  title: string;
  description: string;
  chartType: string;
  status: 'active' | 'draft' | 'archived';
  isRealTime: boolean;
  createdBy: {
    id: string;
    name: string;
    avatar?: string;
  };
  createdAt: string;
  updatedAt: string;
  accessCount: number;
  templateName?: string;
}

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

const ChartManagementPage: React.FC = () => {
  const [charts, setCharts] = useState<Chart[]>([]);
  const [templates, setTemplates] = useState<ChartTemplate[]>([]);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // UI State
  const [view, setView] = useState<'grid' | 'list'>('grid');
  const [showBuilder, setShowBuilder] = useState(false);
  const [editingChart, setEditingChart] = useState<Chart | null>(null);
  const [selectedCharts, setSelectedCharts] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('updated');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const chartTypeIcons = {
    line: LineChart,
    bar: BarChart3,
    pie: PieChart,
    area: TrendingUp,
    doughnut: PieChart,
    radar: Zap,
  };

  // Load data
  useEffect(() => {
    loadCharts();
    loadTemplates();
    loadDataSources();
  }, []);

  const loadCharts = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/charts/');
      if (!response.ok) throw new Error('Failed to load charts');
      const data = await response.json();
      setCharts(data.results || data);
    } catch (err) {
      setError('Failed to load charts');
      console.error('Load charts error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await fetch('/api/admin/chart-templates/');
      if (!response.ok) throw new Error('Failed to load templates');
      const data = await response.json();
      setTemplates(data.results || data);
    } catch (err) {
      console.error('Load templates error:', err);
    }
  };

  const loadDataSources = async () => {
    try {
      const response = await fetch('/api/admin/data-sources/');
      if (!response.ok) throw new Error('Failed to load data sources');
      const data = await response.json();
      setDataSources(data.results || data);
    } catch (err) {
      console.error('Load data sources error:', err);
    }
  };

  // Filter and sort charts
  const filteredCharts = charts
    .filter(chart => {
      if (searchTerm && !chart.title.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      if (statusFilter !== 'all' && chart.status !== statusFilter) {
        return false;
      }
      if (typeFilter !== 'all' && chart.chartType !== typeFilter) {
        return false;
      }
      return true;
    })
    .sort((a, b) => {
      let aValue, bValue;
      
      switch (sortBy) {
        case 'title':
          aValue = a.title.toLowerCase();
          bValue = b.title.toLowerCase();
          break;
        case 'created':
          aValue = new Date(a.createdAt).getTime();
          bValue = new Date(b.createdAt).getTime();
          break;
        case 'updated':
          aValue = new Date(a.updatedAt).getTime();
          bValue = new Date(b.updatedAt).getTime();
          break;
        case 'views':
          aValue = a.accessCount;
          bValue = b.accessCount;
          break;
        default:
          return 0;
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  // Chart actions
  const handleCreateChart = () => {
    setEditingChart(null);
    setShowBuilder(true);
  };

  const handleEditChart = (chart: Chart) => {
    setEditingChart(chart);
    setShowBuilder(true);
  };

  const handleSaveChart = async (chartData: any) => {
    try {
      const url = editingChart 
        ? `/api/admin/charts/${editingChart.id}/`
        : '/api/admin/charts/';
      
      const method = editingChart ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(chartData),
      });
      
      if (!response.ok) throw new Error('Failed to save chart');
      
      await loadCharts();
      setShowBuilder(false);
      setEditingChart(null);
      
    } catch (err) {
      setError('Failed to save chart');
      console.error('Save chart error:', err);
    }
  };

  const handleDeleteChart = async (chartId: string) => {
    if (!confirm('Are you sure you want to delete this chart?')) return;
    
    try {
      const response = await fetch(`/api/admin/charts/${chartId}/`, {
        method: 'DELETE',
      });
      
      if (!response.ok) throw new Error('Failed to delete chart');
      
      await loadCharts();
      
    } catch (err) {
      setError('Failed to delete chart');
      console.error('Delete chart error:', err);
    }
  };

  const handleDuplicateChart = async (chartId: string) => {
    try {
      const response = await fetch(`/api/admin/charts/${chartId}/duplicate/`, {
        method: 'POST',
      });
      
      if (!response.ok) throw new Error('Failed to duplicate chart');
      
      await loadCharts();
      
    } catch (err) {
      setError('Failed to duplicate chart');
      console.error('Duplicate chart error:', err);
    }
  };

  const handleExportChart = async (chartId: string, format: string) => {
    try {
      const response = await fetch(`/api/admin/charts/${chartId}/export/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ format }),
      });
      
      if (!response.ok) throw new Error('Failed to export chart');
      
      const data = await response.json();
      
      // Download the exported file
      const downloadResponse = await fetch(`/api/admin/charts/${chartId}/download_export/?export_id=${data.id}`);
      const blob = await downloadResponse.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chart.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
      
    } catch (err) {
      setError('Failed to export chart');
      console.error('Export chart error:', err);
    }
  };

  const handleShareChart = async (chartId: string, shareType: string) => {
    try {
      const response = await fetch(`/api/admin/charts/${chartId}/share/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ share_type: shareType }),
      });
      
      if (!response.ok) throw new Error('Failed to create share link');
      
      const data = await response.json();
      
      if (shareType === 'public_link') {
        const shareUrl = `${window.location.origin}/shared/chart/${data.share_token}`;
        navigator.clipboard.writeText(shareUrl);
        alert('Share link copied to clipboard!');
      } else if (shareType === 'embed_code') {
        const embedResponse = await fetch(`/api/admin/charts/${chartId}/embed_code/?share_token=${data.share_token}`);
        const embedData = await embedResponse.json();
        navigator.clipboard.writeText(embedData.embed_code);
        alert('Embed code copied to clipboard!');
      }
      
    } catch (err) {
      setError('Failed to share chart');
      console.error('Share chart error:', err);
    }
  };

  // Bulk actions
  const handleBulkDelete = async () => {
    if (!confirm(`Are you sure you want to delete ${selectedCharts.length} charts?`)) return;
    
    try {
      await Promise.all(
        selectedCharts.map(chartId =>
          fetch(`/api/admin/charts/${chartId}/`, { method: 'DELETE' })
        )
      );
      
      await loadCharts();
      setSelectedCharts([]);
      
    } catch (err) {
      setError('Failed to delete charts');
      console.error('Bulk delete error:', err);
    }
  };

  const handleBulkExport = async (format: string) => {
    try {
      await Promise.all(
        selectedCharts.map(chartId => handleExportChart(chartId, format))
      );
      
      setSelectedCharts([]);
      
    } catch (err) {
      setError('Failed to export charts');
      console.error('Bulk export error:', err);
    }
  };

  // Chart selection
  const toggleChartSelection = (chartId: string) => {
    setSelectedCharts(prev =>
      prev.includes(chartId)
        ? prev.filter(id => id !== chartId)
        : [...prev, chartId]
    );
  };

  const selectAllCharts = () => {
    setSelectedCharts(filteredCharts.map(chart => chart.id));
  };

  const clearSelection = () => {
    setSelectedCharts([]);
  };

  if (showBuilder) {
    return (
      <ChartBuilder
        initialChart={editingChart}
        templates={templates}
        dataSources={dataSources}
        onSave={handleSaveChart}
        onCancel={() => {
          setShowBuilder(false);
          setEditingChart(null);
        }}
        className="min-h-screen"
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Charts
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Create and manage advanced data visualizations
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 border border-gray-300 dark:border-gray-600 rounded-lg"
              >
                <Filter className="w-4 h-4 mr-2" />
                Filters
              </button>
              
              <button
                onClick={handleCreateChart}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
              >
                <Plus className="w-4 h-4" />
                <span>Create Chart</span>
              </button>
            </div>
          </div>
          
          {/* Search and Controls */}
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search charts..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white w-64"
                />
              </div>
              
              {selectedCharts.length > 0 && (
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {selectedCharts.length} selected
                  </span>
                  <button
                    onClick={() => handleBulkExport('pdf')}
                    className="px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded"
                  >
                    Export
                  </button>
                  <button
                    onClick={handleBulkDelete}
                    className="px-3 py-1 text-sm bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded"
                  >
                    Delete
                  </button>
                  <button
                    onClick={clearSelection}
                    className="px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                  >
                    Clear
                  </button>
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
              >
                <option value="updated">Last Updated</option>
                <option value="created">Created Date</option>
                <option value="title">Title</option>
                <option value="views">Views</option>
              </select>
              
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </button>
              
              <div className="flex border border-gray-300 dark:border-gray-600 rounded-lg">
                <button
                  onClick={() => setView('grid')}
                  className={`p-2 ${view === 'grid' ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300' : 'text-gray-600 dark:text-gray-400'}`}
                >
                  <div className="w-4 h-4 grid grid-cols-2 gap-0.5">
                    <div className="bg-current rounded-sm"></div>
                    <div className="bg-current rounded-sm"></div>
                    <div className="bg-current rounded-sm"></div>
                    <div className="bg-current rounded-sm"></div>
                  </div>
                </button>
                <button
                  onClick={() => setView('list')}
                  className={`p-2 ${view === 'list' ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300' : 'text-gray-600 dark:text-gray-400'}`}
                >
                  <div className="w-4 h-4 flex flex-col space-y-0.5">
                    <div className="h-0.5 bg-current rounded"></div>
                    <div className="h-0.5 bg-current rounded"></div>
                    <div className="h-0.5 bg-current rounded"></div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
        
        {/* Filters Panel */}
        {showFilters && (
          <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
            <div className="flex items-center space-x-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Status
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="draft">Draft</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Chart Type
                </label>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
                >
                  <option value="all">All Types</option>
                  <option value="line">Line Chart</option>
                  <option value="bar">Bar Chart</option>
                  <option value="pie">Pie Chart</option>
                  <option value="area">Area Chart</option>
                  <option value="doughnut">Doughnut Chart</option>
                  <option value="radar">Radar Chart</option>
                </select>
              </div>
              
              <button
                onClick={() => {
                  setStatusFilter('all');
                  setTypeFilter('all');
                  setSearchTerm('');
                }}
                className="mt-6 px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              >
                Clear Filters
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-6">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="text-red-800">{error}</div>
          </div>
        )}
        
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredCharts.length === 0 ? (
          <div className="text-center py-12">
            <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No charts found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {searchTerm || statusFilter !== 'all' || typeFilter !== 'all'
                ? 'Try adjusting your filters or search terms.'
                : 'Get started by creating your first chart.'}
            </p>
            <button
              onClick={handleCreateChart}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Create Chart
            </button>
          </div>
        ) : (
          <div className={view === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6' : 'space-y-4'}>
            {filteredCharts.map(chart => {
              const ChartIcon = chartTypeIcons[chart.chartType as keyof typeof chartTypeIcons] || BarChart3;
              const isSelected = selectedCharts.includes(chart.id);
              
              if (view === 'list') {
                return (
                  <div
                    key={chart.id}
                    className={`bg-white dark:bg-gray-800 border rounded-lg p-4 hover:shadow-md transition-shadow ${
                      isSelected ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleChartSelection(chart.id)}
                          className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                        />
                        
                        <div className="flex items-center space-x-3">
                          <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                            <ChartIcon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                          </div>
                          
                          <div>
                            <h3 className="font-medium text-gray-900 dark:text-white">
                              {chart.title}
                            </h3>
                            <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                              <span>{chart.chartType}</span>
                              <span>•</span>
                              <span>{chart.status}</span>
                              {chart.isRealTime && (
                                <>
                                  <span>•</span>
                                  <span className="flex items-center">
                                    <Clock className="w-3 h-3 mr-1" />
                                    Real-time
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
                          <Eye className="w-4 h-4" />
                          <span>{chart.accessCount}</span>
                        </div>
                        
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {new Date(chart.updatedAt).toLocaleDateString()}
                        </div>
                        
                        <div className="relative">
                          <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                            <MoreVertical className="w-4 h-4" />
                          </button>
                          
                          {/* Action menu would go here */}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              }
              
              return (
                <div
                  key={chart.id}
                  className={`bg-white dark:bg-gray-800 border rounded-lg overflow-hidden hover:shadow-md transition-shadow ${
                    isSelected ? 'border-blue-500 ring-2 ring-blue-200 dark:ring-blue-800' : 'border-gray-200 dark:border-gray-700'
                  }`}
                >
                  {/* Chart Preview */}
                  <div className="h-48 bg-gray-50 dark:bg-gray-700 flex items-center justify-center">
                    <ChartIcon className="w-12 h-12 text-gray-400" />
                  </div>
                  
                  {/* Chart Info */}
                  <div className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900 dark:text-white truncate">
                          {chart.title}
                        </h3>
                        {chart.description && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                            {chart.description}
                          </p>
                        )}
                      </div>
                      
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleChartSelection(chart.id)}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-3">
                      <div className="flex items-center space-x-2">
                        <span className="capitalize">{chart.chartType}</span>
                        {chart.isRealTime && (
                          <span className="flex items-center bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300 px-2 py-1 rounded-full text-xs">
                            <Clock className="w-3 h-3 mr-1" />
                            Live
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        <Eye className="w-3 h-3" />
                        <span>{chart.accessCount}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        Updated {new Date(chart.updatedAt).toLocaleDateString()}
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        <button
                          onClick={() => handleEditChart(chart)}
                          className="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        
                        <button
                          onClick={() => handleDuplicateChart(chart.id)}
                          className="p-1 text-gray-400 hover:text-green-600 dark:hover:text-green-400"
                          title="Duplicate"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                        
                        <button
                          onClick={() => handleShareChart(chart.id, 'public_link')}
                          className="p-1 text-gray-400 hover:text-purple-600 dark:hover:text-purple-400"
                          title="Share"
                        >
                          <Share2 className="w-4 h-4" />
                        </button>
                        
                        <button
                          onClick={() => handleExportChart(chart.id, 'png')}
                          className="p-1 text-gray-400 hover:text-orange-600 dark:hover:text-orange-400"
                          title="Export"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        
                        <button
                          onClick={() => handleDeleteChart(chart.id)}
                          className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChartManagementPage;