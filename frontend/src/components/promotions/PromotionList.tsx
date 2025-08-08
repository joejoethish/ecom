'use client';

import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  Plus, 
  Edit, 
  Trash2, 
  Play, 
  Pause, 
  Copy,
  MoreHorizontal,
  Calendar,
  Target,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign
} from 'lucide-react';

interface Promotion {
  id: string;
  name: string;
  promotion_type: string;
  promotion_type_display: string;
  status: string;
  status_display: string;
  discount_value: number;
  start_date: string;
  end_date: string;
  usage_count: number;
  usage_limit_total?: number;
  budget_spent: number;
  budget_limit?: number;
  conversion_rate: number;
  roi: number;
  priority: number;
  is_active: boolean;
  days_remaining?: number;
  usage_percentage: number;
  budget_percentage: number;
  created_by_name: string;
  created_at: string;
}

interface PromotionListProps {
  onCreatePromotion: () => void;
  onEditPromotion: (promotion: Promotion) => void;
  onViewAnalytics: (promotionId: string) => void;
}

const PromotionList: React.FC<PromotionListProps> = ({
  onCreatePromotion,
  onEditPromotion,
  onViewAnalytics
}) => {
  const [promotions, setPromotions] = useState<Promotion[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [selectedPromotions, setSelectedPromotions] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchPromotions();
  }, [currentPage, searchTerm, statusFilter, typeFilter]);

  const fetchPromotions = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        search: searchTerm,
        ...(statusFilter !== 'all' && { status: statusFilter }),
        ...(typeFilter !== 'all' && { type: typeFilter }),
      });

      const response = await fetch(`/api/v1/promotions/promotions/?${params}`);
      const data = await response.json();
      
      setPromotions(data.results || []);
      setTotalPages(Math.ceil(data.count / 20));
    } catch (error) {
      console.error('Error fetching promotions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkAction = async (action: string) => {
    if (selectedPromotions.length === 0) return;

    try {
      const response = await fetch('/api/v1/promotions/promotions/bulk_action/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          promotion_ids: selectedPromotions,
          action: action
        })
      });

      if (response.ok) {
        fetchPromotions();
        setSelectedPromotions([]);
      }
    } catch (error) {
      console.error('Error performing bulk action:', error);
    }
  };

  const handlePromotionAction = async (promotionId: string, action: string) => {
    try {
      const response = await fetch(`/api/v1/promotions/promotions/${promotionId}/${action}/`, {
        method: 'POST',
      });

      if (response.ok) {
        fetchPromotions();
      }
    } catch (error) {
      console.error(`Error ${action} promotion:`, error);
    }
  };

  const getStatusBadge = (status: string, isActive: boolean) => {
    const statusConfig = {
      draft: { color: 'bg-gray-100 text-gray-800', icon: Clock },
      pending_approval: { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      approved: { color: 'bg-blue-100 text-blue-800', icon: CheckCircle },
      active: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      paused: { color: 'bg-orange-100 text-orange-800', icon: Pause },
      expired: { color: 'bg-red-100 text-red-800', icon: AlertTriangle },
      cancelled: { color: 'bg-red-100 text-red-800', icon: AlertTriangle },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.draft;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {status.replace('_', ' ').toUpperCase()}
        {isActive && status === 'active' && (
          <span className="ml-1 w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
        )}
      </span>
    );
  };

  const getProgressBar = (percentage: number, type: 'usage' | 'budget') => {
    const color = percentage >= 90 ? 'bg-red-500' : percentage >= 70 ? 'bg-yellow-500' : 'bg-green-500';
    
    return (
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        ></div>
        <span className="text-xs text-gray-600 mt-1">{percentage.toFixed(1)}%</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Promotions & Coupons</h1>
          <p className="text-gray-600">Manage your promotional campaigns and coupon codes</p>
        </div>
        <button
          onClick={onCreatePromotion}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Create Promotion</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-64">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search promotions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Status</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="expired">Expired</option>
          </select>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value="percentage">Percentage</option>
            <option value="fixed_amount">Fixed Amount</option>
            <option value="bogo">BOGO</option>
            <option value="free_shipping">Free Shipping</option>
          </select>
        </div>

        {/* Bulk Actions */}
        {selectedPromotions.length > 0 && (
          <div className="mt-4 flex items-center space-x-2">
            <span className="text-sm text-gray-600">
              {selectedPromotions.length} selected
            </span>
            <button
              onClick={() => handleBulkAction('activate')}
              className="px-3 py-1 bg-green-100 text-green-800 rounded text-sm hover:bg-green-200"
            >
              Activate
            </button>
            <button
              onClick={() => handleBulkAction('pause')}
              className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded text-sm hover:bg-yellow-200"
            >
              Pause
            </button>
            <button
              onClick={() => handleBulkAction('duplicate')}
              className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm hover:bg-blue-200"
            >
              Duplicate
            </button>
            <button
              onClick={() => handleBulkAction('delete')}
              className="px-3 py-1 bg-red-100 text-red-800 rounded text-sm hover:bg-red-200"
            >
              Delete
            </button>
          </div>
        )}
      </div>

      {/* Promotions Table */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedPromotions.length === promotions.length}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedPromotions(promotions.map(p => p.id));
                      } else {
                        setSelectedPromotions([]);
                      }
                    }}
                    className="rounded border-gray-300"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Promotion
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type & Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Usage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Budget
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Performance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Schedule
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {promotions.map((promotion) => (
                <tr key={promotion.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selectedPromotions.includes(promotion.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedPromotions([...selectedPromotions, promotion.id]);
                        } else {
                          setSelectedPromotions(selectedPromotions.filter(id => id !== promotion.id));
                        }
                      }}
                      className="rounded border-gray-300"
                    />
                  </td>
                  
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{promotion.name}</div>
                      <div className="text-sm text-gray-500">
                        Priority: {promotion.priority} | Created by {promotion.created_by_name}
                      </div>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {promotion.promotion_type_display}
                      </div>
                      <div className="text-sm text-gray-500">
                        {promotion.promotion_type === 'percentage' ? `${promotion.discount_value}%` : `$${promotion.discount_value}`}
                      </div>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4">
                    {getStatusBadge(promotion.status, promotion.is_active)}
                  </td>
                  
                  <td className="px-6 py-4">
                    <div className="w-24">
                      {getProgressBar(promotion.usage_percentage, 'usage')}
                      <div className="text-xs text-gray-600 mt-1">
                        {promotion.usage_count}{promotion.usage_limit_total ? `/${promotion.usage_limit_total}` : ''}
                      </div>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4">
                    <div className="w-24">
                      {promotion.budget_limit ? (
                        <>
                          {getProgressBar(promotion.budget_percentage, 'budget')}
                          <div className="text-xs text-gray-600 mt-1">
                            ${promotion.budget_spent.toFixed(2)}/${promotion.budget_limit.toFixed(2)}
                          </div>
                        </>
                      ) : (
                        <div className="text-sm text-gray-500">
                          ${promotion.budget_spent.toFixed(2)}
                        </div>
                      )}
                    </div>
                  </td>
                  
                  <td className="px-6 py-4">
                    <div className="text-sm">
                      <div className="flex items-center space-x-2">
                        <TrendingUp className="w-4 h-4 text-green-500" />
                        <span>{promotion.conversion_rate.toFixed(2)}%</span>
                      </div>
                      <div className="flex items-center space-x-2 mt-1">
                        <DollarSign className="w-4 h-4 text-blue-500" />
                        <span className={promotion.roi >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {promotion.roi.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4">
                    <div className="text-sm">
                      <div className="flex items-center space-x-1">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        <span>{new Date(promotion.start_date).toLocaleDateString()}</span>
                      </div>
                      <div className="text-gray-500 mt-1">
                        to {new Date(promotion.end_date).toLocaleDateString()}
                      </div>
                      {promotion.days_remaining !== null && (
                        <div className="text-xs text-orange-600 mt-1">
                          {promotion.days_remaining} days left
                        </div>
                      )}
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      {promotion.status === 'active' ? (
                        <button
                          onClick={() => handlePromotionAction(promotion.id, 'deactivate')}
                          className="text-orange-600 hover:text-orange-900"
                          title="Pause"
                        >
                          <Pause className="w-4 h-4" />
                        </button>
                      ) : (
                        <button
                          onClick={() => handlePromotionAction(promotion.id, 'activate')}
                          className="text-green-600 hover:text-green-900"
                          title="Activate"
                        >
                          <Play className="w-4 h-4" />
                        </button>
                      )}
                      
                      <button
                        onClick={() => onEditPromotion(promotion)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Edit"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      
                      <button
                        onClick={() => handlePromotionAction(promotion.id, 'duplicate')}
                        className="text-gray-600 hover:text-gray-900"
                        title="Duplicate"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      
                      <button
                        onClick={() => onViewAnalytics(promotion.id)}
                        className="text-purple-600 hover:text-purple-900"
                        title="Analytics"
                      >
                        <TrendingUp className="w-4 h-4" />
                      </button>
                      
                      <div className="relative">
                        <button className="text-gray-400 hover:text-gray-600">
                          <MoreHorizontal className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing page <span className="font-medium">{currentPage}</span> of{' '}
                  <span className="font-medium">{totalPages}</span>
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    const page = i + 1;
                    return (
                      <button
                        key={page}
                        onClick={() => setCurrentPage(page)}
                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                          currentPage === page
                            ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        {page}
                      </button>
                    );
                  })}
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PromotionList;