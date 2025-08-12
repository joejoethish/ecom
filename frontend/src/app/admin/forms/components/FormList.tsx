'use client';

import React from 'react';
import { 
  Edit, Trash2, Copy, Eye, BarChart3, 
  Play, Pause, Calendar, Users, TrendingUp 
} from 'lucide-react';
// Removed unused imports

interface Form {
  id: string;
  name: string;
  description?: string;
  status: string;
  is_multi_step?: boolean;
  submission_count?: number;
  conversion_rate?: number;
  created_at: string;
  slug: string;
}

interface FormListProps {
  forms: Form[];
  loading: boolean;
  onEdit: (form: Form) => void;
  onDelete: (id: string) => void;
  onDuplicate: (id: string) => void;
  onPublish: (id: string) => void;
  onUnpublish: (id: string) => void;
  onViewAnalytics: (form: Form) => void;
}

export function FormList({
  forms,
  loading,
  onEdit,
  onDelete,
  onDuplicate,
  onPublish,
  onUnpublish,
  onViewAnalytics
}: FormListProps) {
  const getStatusBadge = (status: string) => {
    const statusConfig = {
      draft: { color: 'bg-gray-100 text-gray-800', label: 'Draft' },
      active: { color: 'bg-green-100 text-green-800', label: 'Active' },
      inactive: { color: 'bg-yellow-100 text-yellow-800', label: 'Inactive' },
      archived: { color: 'bg-red-100 text-red-800', label: 'Archived' }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.draft;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        {config.label}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center space-x-4">
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/6"></div>
                <div className="h-4 bg-gray-200 rounded w-1/6"></div>
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (forms.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="p-12 text-center">
          <div className="mx-auto h-12 w-12 text-gray-400">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No forms</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by creating your first form.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Form
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Submissions
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Conversion
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {forms.map((form) => (
              <tr key={form.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {form.name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {form.description || 'No description'}
                    </div>
                    {form.is_multi_step && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 mt-1">
                        Multi-step
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusBadge(form.status)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm text-gray-900">
                    <Users className="h-4 w-4 mr-1 text-gray-400" />
                    {form.submission_count || 0}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm text-gray-900">
                    <TrendingUp className="h-4 w-4 mr-1 text-gray-400" />
                    {form.conversion_rate ? `${form.conversion_rate.toFixed(1)}%` : '0%'}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 mr-1" />
                    {formatDate(form.created_at)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => onEdit(form)}
                      className="text-blue-600 hover:text-blue-900 p-1"
                      title="Edit form"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                    
                    <button
                      onClick={() => onViewAnalytics(form)}
                      className="text-green-600 hover:text-green-900 p-1"
                      title="View analytics"
                    >
                      <BarChart3 className="h-4 w-4" />
                    </button>
                    
                    <button
                      onClick={() => onDuplicate(form.id)}
                      className="text-gray-600 hover:text-gray-900 p-1"
                      title="Duplicate form"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                    
                    {form.status === 'active' ? (
                      <button
                        onClick={() => onUnpublish(form.id)}
                        className="text-yellow-600 hover:text-yellow-900 p-1"
                        title="Unpublish form"
                      >
                        <Pause className="h-4 w-4" />
                      </button>
                    ) : (
                      <button
                        onClick={() => onPublish(form.id)}
                        className="text-green-600 hover:text-green-900 p-1"
                        title="Publish form"
                      >
                        <Play className="h-4 w-4" />
                      </button>
                    )}
                    
                    <button
                      onClick={() => window.open(`/forms/${form.slug}`, '_blank')}
                      className="text-purple-600 hover:text-purple-900 p-1"
                      title="Preview form"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    
                    <button
                      onClick={() => onDelete(form.id)}
                      className="text-red-600 hover:text-red-900 p-1"
                      title="Delete form"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}