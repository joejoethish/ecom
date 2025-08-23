'use client';

import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Search, 
  Filter, 
  Plus, 
  TrendingUp, 
  Users, 
  Eye, 
  Heart,
  Star,
  Clock,
  Tag
} from 'lucide-react';

interface DocumentationStats {
  totalDocuments: number;
  publishedDocuments: number;
  draftDocuments: number;
  totalViews: number;
  totalLikes: number;
  totalComments: number;
  totalBookmarks: number;
  averageRating: number;
}

interface RecentDocument {
  id: string;
  title: string;
  category: string;
  author: string;
  status: string;
  updatedAt: string;
  viewCount: number;
  likeCount: number;
}

interface PopularDocument {
  id: string;
  title: string;
  category: string;
  viewCount: number;
  likeCount: number;
  rating: number;
}

const DocumentationDashboard: React.FC = () => {
  const [stats, setStats] = useState<DocumentationStats | null>(null);
  const [recentDocuments, setRecentDocuments] = useState<RecentDocument[]>([]);
  const [popularDocuments, setPopularDocuments] = useState<PopularDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard statistics
      const statsResponse = await fetch('/api/documentation/dashboard/stats/');
      const statsData = await statsResponse.json();
      setStats(statsData);

      // Fetch recent documents
      const recentResponse = await fetch('/api/documentation/documents/?ordering=-updated_at&limit=10');
      const recentData = await recentResponse.json();
      setRecentDocuments(recentData.results || []);

      // Fetch popular documents
      const popularResponse = await fetch('/api/documentation/documents/?ordering=-view_count&limit=10');
      const popularData = await popularResponse.json();
      setPopularDocuments(popularData.results || []);

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      if (typeof window !== 'undefined') {
        window.location.href = `/documentation/search?q=${encodeURIComponent(searchQuery)}`;
      }
    }
  };

  const StatCard: React.FC<{
    title: string;
    value: number | string;
    icon: React.ReactNode;
    color: string;
    change?: string;
  }> = ({ title, value, icon, color, change }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change && (
            <p className="text-sm text-green-600 mt-1">
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

  const DocumentCard: React.FC<{ document: RecentDocument | PopularDocument }> = ({ document }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="font-medium text-gray-900 hover:text-blue-600 cursor-pointer">
            {document.title}
          </h3>
          <p className="text-sm text-gray-500 mt-1">{document.category}</p>
          {'author' in document && (
            <p className="text-xs text-gray-400 mt-1">by {document.author}</p>
          )}
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <div className="flex items-center">
            <Eye className="w-4 h-4 mr-1" />
            {document.viewCount}
          </div>
          <div className="flex items-center">
            <Heart className="w-4 h-4 mr-1" />
            {document.likeCount}
          </div>
          {'rating' in document && (
            <div className="flex items-center">
              <Star className="w-4 h-4 mr-1 text-yellow-500" />
              {document.rating.toFixed(1)}
            </div>
          )}
        </div>
      </div>
      {'updatedAt' in document && (
        <div className="flex items-center mt-2 text-xs text-gray-400">
          <Clock className="w-3 h-3 mr-1" />
          Updated {new Date(document.updatedAt).toLocaleDateString()}
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Documentation Dashboard</h1>
          <p className="text-gray-600">Manage and track your documentation</p>
        </div>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center">
          <Plus className="w-4 h-4 mr-2" />
          New Document
        </button>
      </div>

      {/* Search Bar */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <form onSubmit={handleSearch} className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search documentation..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={selectedFilter}
            onChange={(e) => setSelectedFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Documents</option>
            <option value="published">Published</option>
            <option value="draft">Draft</option>
            <option value="review">Under Review</option>
          </select>
          <button
            type="submit"
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center"
          >
            <Filter className="w-4 h-4 mr-2" />
            Search
          </button>
        </form>
      </div>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Documents"
            value={stats.totalDocuments}
            icon={<BookOpen className="w-6 h-6 text-white" />}
            color="bg-blue-500"
            change="+12% from last month"
          />
          <StatCard
            title="Total Views"
            value={stats.totalViews.toLocaleString()}
            icon={<Eye className="w-6 h-6 text-white" />}
            color="bg-green-500"
            change="+8% from last month"
          />
          <StatCard
            title="Total Likes"
            value={stats.totalLikes}
            icon={<Heart className="w-6 h-6 text-white" />}
            color="bg-red-500"
            change="+15% from last month"
          />
          <StatCard
            title="Average Rating"
            value={stats.averageRating.toFixed(1)}
            icon={<Star className="w-6 h-6 text-white" />}
            color="bg-yellow-500"
          />
        </div>
      )}

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Documents */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Documents</h2>
            <p className="text-sm text-gray-600">Latest updates and additions</p>
          </div>
          <div className="p-6 space-y-4">
            {recentDocuments.length > 0 ? (
              recentDocuments.map((doc) => (
                <DocumentCard key={doc.id} document={doc} />
              ))
            ) : (
              <p className="text-gray-500 text-center py-8">No recent documents found</p>
            )}
          </div>
        </div>

        {/* Popular Documents */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Popular Documents</h2>
            <p className="text-sm text-gray-600">Most viewed and liked content</p>
          </div>
          <div className="p-6 space-y-4">
            {popularDocuments.length > 0 ? (
              popularDocuments.map((doc) => (
                <DocumentCard key={doc.id} document={doc} />
              ))
            ) : (
              <p className="text-gray-500 text-center py-8">No popular documents found</p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <Plus className="w-8 h-8 text-blue-600 mb-2" />
            <span className="text-sm font-medium">New Document</span>
          </button>
          <button className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <Tag className="w-8 h-8 text-green-600 mb-2" />
            <span className="text-sm font-medium">Manage Categories</span>
          </button>
          <button className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <Users className="w-8 h-8 text-purple-600 mb-2" />
            <span className="text-sm font-medium">Team Collaboration</span>
          </button>
          <button className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <TrendingUp className="w-8 h-8 text-orange-600 mb-2" />
            <span className="text-sm font-medium">Analytics</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default DocumentationDashboard;