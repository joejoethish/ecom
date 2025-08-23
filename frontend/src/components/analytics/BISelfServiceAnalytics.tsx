'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { 
  Bookmark, Play, Download,
  Database, BarChart3, PieChart as PieChartIcon, TrendingUp,
  Table, Code, Save, RefreshCw, Eye
} from 'lucide-react';

interface BISelfServiceAnalyticsProps {
  userId?: string;
}

interface AnalyticsSession {
  id: string;
  name: string;
  description: string;
  user_name: string;
  query_history: any[];
  visualizations: Visualization[];
  insights_discovered: any[];
  bookmarks: Bookmark[];
  collaboration_notes: string;
  is_public: boolean;
  last_accessed: string;
  created_at: string;
  data_sources_names: string[];
  shared_with_users: Array<{id: number; name: string; email: string}>;
  session_duration: number;
}

interface Visualization {
  id: string;
  name: string;
  type: 'line' | 'bar' | 'pie' | 'area' | 'scatter' | 'table';
  config: any;
  data: any[];
  created_at: string;
}

interface Bookmark {
  id: string;
  name: string;
  description?: string;
  url: string;
  filters?: any;
  created_at: string;
}

interface DataSource {
  id: string;
  name: string;
  description: string;
  source_type: string;
  schema_definition: any;
  is_active: boolean;
}

const CHART_TYPES = [
  { value: 'line', label: 'Line Chart', icon: TrendingUp },
  { value: 'bar', label: 'Bar Chart', icon: BarChart3 },
  { value: 'pie', label: 'Pie Chart', icon: PieChartIcon },
  { value: 'area', label: 'Area Chart', icon: BarChart3 },
  { value: 'scatter', label: 'Scatter Plot', icon: BarChart3 },
  { value: 'table', label: 'Data Table', icon: Table }
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export default function BISelfServiceAnalytics({ userId: _userId }: BISelfServiceAnalyticsProps) {
  const [sessions, setSessions] = useState<AnalyticsSession[]>([]);
  const [currentSession, setCurrentSession] = useState<AnalyticsSession | null>(null);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [selectedDataSource, setSelectedDataSource] = useState<DataSource | null>(null);
  const [queryBuilder, setQueryBuilder] = useState({
    select: ['*'],
    from: '',
    where: [],
    groupBy: [],
    orderBy: [],
    limit: 100
  });
  const [queryResult, setQueryResult] = useState<any[]>([]);
  const [selectedVisualization, setSelectedVisualization] = useState<string>('table');
  const [visualizationConfig] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [executingQuery, setExecutingQuery] = useState(false);
  const [selectedTab] = useState('explore');

  const fetchSessions = useCallback(async () => {
    try {
      const response = await fetch('/api/analytics/bi/analytics-sessions/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch analytics sessions');
      
      const data = await response.json();
      setSessions(data.results || data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sessions');
    }
  }, []);

  const fetchDataSources = useCallback(async () => {
    try {
      const response = await fetch('/api/analytics/bi/data-sources/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch data sources');
      
      const data = await response.json();
      setDataSources(data.results || data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data sources');
    }
  }, []);

  const createNewSession = async () => {
    try {
      const name = prompt('Enter session name:');
      if (!name) return;

      const response = await fetch('/api/analytics/bi/analytics-sessions/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          name,
          description: 'Self-service analytics session',
          query_history: [],
          visualizations: [],
          insights_discovered: [],
          bookmarks: []
        })
      });

      if (!response.ok) throw new Error('Failed to create session');
      
      const newSession = await response.json();
      setSessions(prev => [newSession, ...prev]);
      setCurrentSession(newSession);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session');
    }
  };

  const executeQuery = async () => {
    if (!selectedDataSource) {
      setError('Please select a data source');
      return;
    }

    try {
      setExecutingQuery(true);
      setError(null);

      // Simulate query execution
      // In a real implementation, this would send the query to the backend
      const mockData = generateMockData(queryBuilder.limit);
      setQueryResult(mockData);

      // Add query to history
      if (currentSession) {
        const queryHistory = [...(currentSession.query_history || [])];
        queryHistory.push({
          id: Date.now().toString(),
          query: queryBuilder,
          data_source: selectedDataSource.name,
          executed_at: new Date().toISOString(),
          result_count: mockData.length
        });

        setCurrentSession(prev => prev ? { ...prev, query_history: queryHistory } : null);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute query');
    } finally {
      setExecutingQuery(false);
    }
  };

  const generateMockData = (limit: number) => {
    const data = [];
    for (let i = 0; i < Math.min(limit, 50); i++) {
      data.push({
        id: i + 1,
        date: new Date(2024, 0, i + 1).toISOString().split('T')[0],
        revenue: Math.floor(Math.random() * 10000) + 5000,
        orders: Math.floor(Math.random() * 100) + 20,
        customers: Math.floor(Math.random() * 50) + 10,
        category: ['Electronics', 'Clothing', 'Books', 'Home'][Math.floor(Math.random() * 4)],
        region: ['North', 'South', 'East', 'West'][Math.floor(Math.random() * 4)]
      });
    }
    return data;
  };

  const saveVisualization = async () => {
    if (!currentSession || !queryResult.length) return;

    try {
      const name = prompt('Enter visualization name:');
      if (!name) return;

      const visualization: Visualization = {
        id: Date.now().toString(),
        name,
        type: selectedVisualization as any,
        config: visualizationConfig,
        data: queryResult,
        created_at: new Date().toISOString()
      };

      const response = await fetch(`/api/analytics/bi/analytics-sessions/${currentSession.id}/save_visualization/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ visualization })
      });

      if (!response.ok) throw new Error('Failed to save visualization');

      // Update current session
      const updatedVisualizations = [...(currentSession.visualizations || []), visualization];
      setCurrentSession(prev => prev ? { ...prev, visualizations: updatedVisualizations } : null);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save visualization');
    }
  };

  const addBookmark = async () => {
    if (!currentSession) return;

    try {
      const name = prompt('Enter bookmark name:');
      if (!name) return;

      const bookmark: Bookmark = {
        id: Date.now().toString(),
        name,
        description: 'Bookmarked query and filters',
        url: typeof window !== 'undefined' ? window.location.href : '',
        filters: queryBuilder,
        created_at: new Date().toISOString()
      };

      const response = await fetch(`/api/analytics/bi/analytics-sessions/${currentSession.id}/add_bookmark/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ bookmark })
      });

      if (!response.ok) throw new Error('Failed to add bookmark');

      // Update current session
      const updatedBookmarks = [...(currentSession.bookmarks || []), bookmark];
      setCurrentSession(prev => prev ? { ...prev, bookmarks: updatedBookmarks } : null);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add bookmark');
    }
  };

  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      await Promise.all([fetchSessions(), fetchDataSources()]);
      setLoading(false);
    };

    initializeData();
  }, [fetchSessions, fetchDataSources]);

  const renderQueryBuilder = () => {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Code className="w-5 h-5 mr-2" />
            Query Builder
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Data Source Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">Data Source</label>
            <select
              value={selectedDataSource?.id || ''}
              onChange={(e) => {
                const source = dataSources.find(ds => ds.id === e.target.value);
                setSelectedDataSource(source || null);
                setQueryBuilder(prev => ({ ...prev, from: source?.name || '' }));
              }}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="">Select a data source</option>
              {dataSources.map(source => (
                <option key={source.id} value={source.id}>
                  {source.name} ({source.source_type})
                </option>
              ))}
            </select>
          </div>

          {/* Select Fields */}
          <div>
            <label className="block text-sm font-medium mb-2">Select Fields</label>
            <div className="flex flex-wrap gap-2">
              {['*', 'date', 'revenue', 'orders', 'customers', 'category', 'region'].map(field => (
                <Button
                  key={field}
                  size="sm"
                  variant={queryBuilder.select.includes(field) ? 'primary' : 'outline'}
                  onClick={() => {
                    if (field === '*') {
                      setQueryBuilder(prev => ({ ...prev, select: ['*'] }));
                    } else {
                      setQueryBuilder(prev => ({
                        ...prev,
                        select: prev.select.includes('*') 
                          ? [field]
                          : prev.select.includes(field)
                            ? prev.select.filter(f => f !== field)
                            : [...prev.select, field]
                      }));
                    }
                  }}
                >
                  {field}
                </Button>
              ))}
            </div>
          </div>

          {/* Filters */}
          <div>
            <label className="block text-sm font-medium mb-2">Filters</label>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <select className="px-3 py-2 border rounded-md">
                  <option>revenue</option>
                  <option>orders</option>
                  <option>customers</option>
                </select>
                <select className="px-3 py-2 border rounded-md">
                  <option value="gt">Greater than</option>
                  <option value="lt">Less than</option>
                  <option value="eq">Equal to</option>
                  <option value="gte">Greater than or equal</option>
                  <option value="lte">Less than or equal</option>
                </select>
                <input
                  type="number"
                  placeholder="Value"
                  className="px-3 py-2 border rounded-md"
                />
                <Button size="sm" variant="outline">Add</Button>
              </div>
            </div>
          </div>

          {/* Limit */}
          <div>
            <label className="block text-sm font-medium mb-2">Limit</label>
            <input
              type="number"
              value={queryBuilder.limit}
              onChange={(e) => setQueryBuilder(prev => ({ ...prev, limit: parseInt(e.target.value) || 100 }))}
              className="w-32 px-3 py-2 border rounded-md"
              min="1"
              max="1000"
            />
          </div>

          {/* Execute Button */}
          <div className="flex items-center space-x-2">
            <Button
              onClick={executeQuery}
              disabled={executingQuery || !selectedDataSource}
            >
              {executingQuery ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Play className="w-4 h-4 mr-2" />
              )}
              Execute Query
            </Button>
            <Button variant="outline" onClick={addBookmark} disabled={!currentSession}>
              <Bookmark className="w-4 h-4 mr-2" />
              Bookmark
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderVisualization = () => {
    if (!queryResult.length) {
      return (
        <Card>
          <CardContent className="flex items-center justify-center h-64">
            <div className="text-center">
              <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Execute a query to see results</p>
            </div>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Data Visualization</CardTitle>
            <div className="flex items-center space-x-2">
              <select
                value={selectedVisualization}
                onChange={(e) => setSelectedVisualization(e.target.value)}
                className="px-3 py-2 border rounded-md"
              >
                {CHART_TYPES.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
              <Button size="sm" onClick={saveVisualization} disabled={!currentSession}>
                <Save className="w-4 h-4 mr-1" />
                Save
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {selectedVisualization === 'table' && (
            <div className="overflow-auto max-h-96">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    {Object.keys(queryResult[0] || {}).map(key => (
                      <th key={key} className="text-left p-2">{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {queryResult.slice(0, 20).map((row, index) => (
                    <tr key={index} className="border-b">
                      {Object.values(row).map((value, i) => (
                        <td key={i} className="p-2">
                          {typeof value === 'number' ? value.toLocaleString() : String(value)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {selectedVisualization === 'line' && (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={queryResult.slice(0, 20)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="revenue" stroke="#8884d8" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {selectedVisualization === 'bar' && (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={queryResult.slice(0, 20)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="revenue" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {selectedVisualization === 'pie' && (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={queryResult.slice(0, 6)}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="revenue"
                    nameKey="category"
                  >
                    {queryResult.slice(0, 6).map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderSavedVisualizations = () => {
    if (!currentSession?.visualizations?.length) {
      return (
        <div className="text-center py-12">
          <Eye className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No saved visualizations</h3>
          <p className="text-gray-500">Create and save visualizations to see them here.</p>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {currentSession.visualizations.map(viz => (
          <Card key={viz.id}>
            <CardHeader>
              <CardTitle className="text-lg">{viz.name}</CardTitle>
              <p className="text-sm text-gray-600">
                {viz.type} • {new Date(viz.created_at).toLocaleDateString()}
              </p>
            </CardHeader>
            <CardContent>
              <div className="h-32 bg-gray-50 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-8 h-8 text-gray-400" />
              </div>
              <div className="mt-4 flex items-center justify-between">
                <Badge variant="outline">{viz.type}</Badge>
                <div className="flex items-center space-x-2">
                  <Button size="sm" variant="outline">
                    <Eye className="w-4 h-4" />
                  </Button>
                  <Button size="sm" variant="outline">
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin mr-2" />
        <span>Loading analytics workspace...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Self-Service Analytics</h1>
          <p className="text-gray-600">Explore data and create visualizations</p>
        </div>
        <div className="flex items-center space-x-2">
          {currentSession && (
            <Badge variant="secondary">
              Session: {currentSession.name}
            </Badge>
          )}
          <Button onClick={createNewSession}>
            <Database className="w-4 h-4 mr-2" />
            New Session
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Session Selection */}
      {sessions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Analytics Sessions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sessions.map(session => (
                <div
                  key={session.id}
                  className={`p-4 border rounded-lg cursor-pointer hover:shadow-md transition-shadow ${
                    currentSession?.id === session.id ? 'border-blue-500 bg-blue-50' : ''
                  }`}
                  onClick={() => setCurrentSession(session)}
                >
                  <h3 className="font-semibold">{session.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{session.description}</p>
                  <div className="flex items-center justify-between mt-2">
                    <Badge variant="outline">
                      {session.visualizations?.length || 0} visualizations
                    </Badge>
                    <span className="text-xs text-gray-500">
                      {new Date(session.last_accessed).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <Tabs defaultValue={selectedTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="explore">Explore Data</TabsTrigger>
          <TabsTrigger value="visualizations">Visualizations</TabsTrigger>
          <TabsTrigger value="bookmarks">Bookmarks</TabsTrigger>
        </TabsList>

        <TabsContent value="explore" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-6">
              {renderQueryBuilder()}
            </div>
            <div>
              {renderVisualization()}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="visualizations" className="mt-6">
          {renderSavedVisualizations()}
        </TabsContent>

        <TabsContent value="bookmarks" className="mt-6">
          {currentSession?.bookmarks?.length ? (
            <div className="space-y-4">
              {currentSession.bookmarks.map(bookmark => (
                <Card key={bookmark.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold">{bookmark.name}</h3>
                        <p className="text-sm text-gray-600">{bookmark.description}</p>
                        <span className="text-xs text-gray-500">
                          {new Date(bookmark.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <Button size="sm" variant="outline">
                        <Eye className="w-4 h-4 mr-1" />
                        Load
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Bookmark className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No bookmarks saved</h3>
              <p className="text-gray-500">Bookmark queries and filters to access them quickly.</p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}