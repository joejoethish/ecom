'use client';

import React, { useState } from 'react';
import PromotionDashboard from './PromotionDashboard';
import PromotionList from './PromotionList';
import PromotionForm from './PromotionForm';

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

const PromotionManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'promotions'>('dashboard');
  const [showPromotionForm, setShowPromotionForm] = useState(false);
  const [editingPromotion, setEditingPromotion] = useState<Promotion | null>(null);
  const [showAnalytics, setShowAnalytics] = useState<string | null>(null);

  const handleCreatePromotion = () => {
    setEditingPromotion(null);
    setShowPromotionForm(true);
  };

  const handleEditPromotion = (promotion: Promotion) => {
    setEditingPromotion(promotion);
    setShowPromotionForm(true);
  };

  const handleCloseForm = () => {
    setShowPromotionForm(false);
    setEditingPromotion(null);
  };

  const handleSubmitPromotion = async (formData: any) => {
    try {
      const url = editingPromotion 
        ? `/api/v1/promotions/promotions/${editingPromotion.id}/`
        : '/api/v1/promotions/promotions/';
      
      const method = editingPromotion ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        handleCloseForm();
        // Refresh the data - in a real app, you might want to use a state management solution
        window.location.reload();
      } else {
        const errorData = await response.json();
        console.error('Error saving promotion:', errorData);
        // Handle error - show toast notification, etc.
      }
    } catch (error) {
      console.error('Error saving promotion:', error);
      // Handle error
    }
  };

  const handleViewAnalytics = (promotionId: string) => {
    setShowAnalytics(promotionId);
    // In a real app, you might navigate to a dedicated analytics page
    // or show a modal with detailed analytics
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'dashboard'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('promotions')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'promotions'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Promotions
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && <PromotionDashboard />}
        
        {activeTab === 'promotions' && (
          <PromotionList
            onCreatePromotion={handleCreatePromotion}
            onEditPromotion={handleEditPromotion}
            onViewAnalytics={handleViewAnalytics}
          />
        )}
      </div>

      {/* Promotion Form Modal */}
      <PromotionForm
        isOpen={showPromotionForm}
        onClose={handleCloseForm}
        onSubmit={handleSubmitPromotion}
        initialData={editingPromotion || undefined}
        isEditing={!!editingPromotion}
      />

      {/* Analytics Modal - Placeholder */}
      {showAnalytics && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-xl font-semibold text-gray-900">
                Promotion Analytics
              </h2>
              <button
                onClick={() => setShowAnalytics(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6">
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Detailed Analytics Coming Soon
                </h3>
                <p className="text-gray-500">
                  Advanced analytics and reporting features will be available in the next update.
                </p>
                <p className="text-sm text-gray-400 mt-2">
                  Promotion ID: {showAnalytics}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PromotionManagement;