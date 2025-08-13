'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts';
import {
  TrendingUp,
  Eye,
  Heart,
  MessageSquare,
  Users,
  Clock,
  Star,
  BookOpen,
  Download,
  Share2,
  Search,
  Filter,
  BarChart3,
  Activity
} from 'lucide-react';

interface AnalyticsData {
  overview: {
    totalViews: number;
    totalLikes: number;
    totalComments: number;
    totalShares: number;
    averageRating: number;
    totalDocuments: number;
    activeUsers: number;
    averageTimeSpent: number;
  };
  viewsOverTime: Array<{
    date: string;
    views: number;
    likes: number;
    comments: number;
  }>;
  topDocuments: Array<{
    id: string;
    title: string;
    views: number;
    likes: number;
    rating: number;
    category: string;
  }>;
  categoryStats: Array<{
    name: string;
    documents: number;
    views: number;
    color: string;
  }>;
  userEngagement: Array<{
    date: string;
    activeUsers: number;
    newUsers: number;
    returningUsers: number;
  }>;
  searchQueries: Array<{
    query: string;
    count: number;
    results: number;
  }>;
  deviceStats: Array<{
    device: string;
    count: number;
    percentage: number;
  }>;
}

interface DocumentationAnalyticsProps {
  documentId?: string;
  timeRange?: '7d' | '30d' | '90d' | '1y';
}

const DocumentationAnalytics: React.FC<DocumentationAnalyticsProps> = ({
  documentId,
  timeRange = '30d'
}) => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [activeTab, setActiveTab] = useState<'overview' | 'engagement' | 'content' | 'search'>('overview');

  const fetchAnalyticsData = useCallback(async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams({
        time_range: selectedTimeRange
      });
      
      if (documentId) {
        params.append('document_id', documentId);
      }

      const response = await fetch(`/api/documentation/analytics/summary/?${params}`);
      const data = await response.json();
      setAnalyticsData(data);
    } catch (error) {
      console.error('Error fetching analytics data:', error);
    } finally {
      setLoading(false);
    }
  }, [documentId, selectedTimeRange]);

  useEffect(() => {
    fetchAnalyticsData();
  }, [documentId, selectedTimeRange, fetchAnalyticsData]);

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const MetricCard: React.FC<{
    title: string;
    value: string | number;
    icon: React.ReactNode;
    color: string;
    change?: string;
    changeType?: 'positive' | 'negative' | 'neutral';
  }> = ({ title, value, icon, color, change, changeType = 'neutral' }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change && (
            <p className={`text-sm mt-1 ${
              changeType === 'positive' ? 'text-green-600' :
              changeType === 'negative' ? 'text-red-600' :
              'text-gray-600'
            }`}>
              <TrendingUp className="inline w-4 h-4 mr-1" />
              {change}
            </p>
          )}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  );

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No analytics data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {documentId ? 'Document Analytics' : 'Documentation Analytics'}
          </h1>
          <p className="text-gray-600">Track performance and user engagement</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="1y">Last year</option>
          </select>
          
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center">
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: BarChart3 },
            { id: 'engagement', name: 'Engagement', icon: Activity },
            { id: 'content', name: 'Content', icon: BookOpen },
            { id: 'search', name: 'Search', icon: Search }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4 mr-2" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Total Views"
              value={formatNumber(analyticsData.overview.totalViews)}
              icon={<Eye className="w-6 h-6 text-white" />}
              color="bg-blue-500"
              change="+12% from last period"
              changeType="positive"
            />
            <MetricCard
              title="Total Likes"
              value={formatNumber(analyticsData.overview.totalLikes)}
              icon={<Heart className="w-6 h-6 text-white" />}
              color="bg-red-500"
              change="+8% from last period"
              changeType="positive"
            />
            <MetricCard
              title="Active Users"
              value={formatNumber(analyticsData.overview.activeUsers)}
              icon={<Users className="w-6 h-6 text-white" />}
              color="bg-green-500"
              change="+15% from last period"
              changeType="positive"
            />
            <MetricCard
              title="Avg. Time Spent"
              value={formatTime(analyticsData.overview.averageTimeSpent)}
              icon={<Clock className="w-6 h-6 text-white" />}
              color="bg-purple-500"
              change="+5% from last period"
              changeType="positive"
            />
          </div>

          {/* Views Over Time */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Views Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={analyticsData.viewsOverTime}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="views"
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  fillOpacity={0.1}
                />
                <Area
                  type="monotone"
                  dataKey="likes"
                  stroke="#EF4444"
                  fill="#EF4444"
                  fillOpacity={0.1}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Category Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Content by Category</h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={analyticsData.categoryStats}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percentage }: Record<string, unknown>) => `${name} ${percentage}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="documents"
                  >
                    {analyticsData.categoryStats.map((entry: any, index: number) => (
                      <Cell key={`cell-${entry.name}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Device Usage</h3>
              <div className="space-y-3">
                {analyticsData.deviceStats.map((device) => (
                  <div key={device.device} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900">{device.device}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${device.percentage}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600">{device.percentage}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Engagement Tab */}
      {activeTab === 'engagement' && (
        <div className="space-y-6">
          {/* User Engagement Chart */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">User Engagement</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analyticsData.userEngagement}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="activeUsers"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  name="Active Users"
                />
                <Line
                  type="monotone"
                  dataKey="newUsers"
                  stroke="#10B981"
                  strokeWidth={2}
                  name="New Users"
                />
                <Line
                  type="monotone"
                  dataKey="returningUsers"
                  stroke="#F59E0B"
                  strokeWidth={2}
                  name="Returning Users"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Engagement Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <MetricCard
              title="Comments"
              value={formatNumber(analyticsData.overview.totalComments)}
              icon={<MessageSquare className="w-6 h-6 text-white" />}
              color="bg-blue-500"
            />
            <MetricCard
              title="Shares"
              value={formatNumber(analyticsData.overview.totalShares)}
              icon={<Share2 className="w-6 h-6 text-white" />}
              color="bg-green-500"
            />
            <MetricCard
              title="Average Rating"
              value={analyticsData.overview.averageRating.toFixed(1)}
              icon={<Star className="w-6 h-6 text-white" />}
              color="bg-yellow-500"
            />
          </div>
        </div>
      )}

      {/* Content Tab */}
      {activeTab === 'content' && (
        <div className="space-y-6">
          {/* Top Performing Documents */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Performing Documents</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Document
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Category
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Views
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Likes
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rating
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {analyticsData.topDocuments.map((doc) => (
                    <tr key={doc.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{doc.title}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {doc.category}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatNumber(doc.views)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatNumber(doc.likes)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <Star className="w-4 h-4 text-yellow-500 mr-1" />
                          <span className="text-sm text-gray-900">{doc.rating.toFixed(1)}</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Category Performance */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Category Performance</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analyticsData.categoryStats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="views" fill="#3B82F6" name="Views" />
                <Bar dataKey="documents" fill="#10B981" name="Documents" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Search Tab */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          {/* Top Search Queries */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Search Queries</h3>
            <div className="space-y-3">
              {analyticsData.searchQueries.map((query, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <span className="text-sm font-medium text-gray-900">{query.query}</span>
                    <div className="text-xs text-gray-500 mt-1">
                      {query.results} results found
                    </div>
                  </div>
                  <div className="text-sm font-medium text-gray-900">
                    {query.count} searches
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Search Performance Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <MetricCard
              title="Total Searches"
              value={formatNumber(analyticsData.searchQueries.reduce((sum, q) => sum + q.count, 0))}
              icon={<Search className="w-6 h-6 text-white" />}
              color="bg-blue-500"
            />
            <MetricCard
              title="Unique Queries"
              value={analyticsData.searchQueries.length}
              icon={<Filter className="w-6 h-6 text-white" />}
              color="bg-green-500"
            />
            <MetricCard
              title="Avg. Results"
              value={Math.round(analyticsData.searchQueries.reduce((sum, q) => sum + q.results, 0) / analyticsData.searchQueries.length)}
              icon={<BookOpen className="w-6 h-6 text-white" />}
              color="bg-purple-500"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentationAnalytics;