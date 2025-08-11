'use client';

import React, { useState, useEffect } from 'react';
import { 
  X, 
  Target, 
  Settings, 
  DollarSign, 
  Clock,
  AlertCircle,
  Info,
  Plus
} from 'lucide-react';

interface PromotionFormData {
  name: string;
  description: string;
  internal_notes: string;
  promotion_type: string;
  discount_value: number;
  max_discount_amount?: number;
  buy_quantity: number;
  get_quantity: number;
  get_discount_percentage: number;
  start_date: string;
  end_date: string;
  timezone: string;
  usage_limit_total?: number;
  usage_limit_per_customer?: number;
  minimum_order_amount?: number;
  minimum_quantity?: number;
  target_type: string;
  target_customer_segments: string[];
  target_customer_ids: string[];
  allowed_channels: string[];
  can_stack_with_other_promotions: boolean;
  stackable_promotion_types: string[];
  excluded_promotion_ids: string[];
  priority: number;
  is_ab_test: boolean;
  ab_test_group: string;
  ab_test_traffic_percentage: number;
  requires_approval: boolean;
  budget_limit?: number;
  product_ids: string[];
  category_ids: string[];
  excluded_product_ids: string[];
  excluded_category_ids: string[];
  coupon_codes: string[];
}

interface PromotionFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: PromotionFormData) => void;
  initialData?: Partial<PromotionFormData>;
  isEditing?: boolean;
}

const PromotionForm: React.FC<PromotionFormProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  isEditing = false
}) => {
  const [formData, setFormData] = useState<PromotionFormData>({
    name: '',
    description: '',
    internal_notes: '',
    promotion_type: 'percentage',
    discount_value: 0,
    max_discount_amount: undefined,
    buy_quantity: 1,
    get_quantity: 1,
    get_discount_percentage: 100,
    start_date: '',
    end_date: '',
    timezone: 'UTC',
    usage_limit_total: undefined,
    usage_limit_per_customer: undefined,
    minimum_order_amount: undefined,
    minimum_quantity: undefined,
    target_type: 'all_customers',
    target_customer_segments: [],
    target_customer_ids: [],
    allowed_channels: ['website'],
    can_stack_with_other_promotions: false,
    stackable_promotion_types: [],
    excluded_promotion_ids: [],
    priority: 1,
    is_ab_test: false,
    ab_test_group: '',
    ab_test_traffic_percentage: 100,
    requires_approval: false,
    budget_limit: undefined,
    product_ids: [],
    category_ids: [],
    excluded_product_ids: [],
    excluded_category_ids: [],
    coupon_codes: []
  });

  const [activeTab, setActiveTab] = useState('basic');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [newCouponCode, setNewCouponCode] = useState('');

  useEffect(() => {
    if (initialData) {
      setFormData(prev => ({ ...prev, ...initialData }));
    }
  }, [initialData]);

  const handleInputChange = (field: keyof PromotionFormData, value: string | number | boolean | Date) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Promotion name is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    if (formData.discount_value <= 0) {
      newErrors.discount_value = 'Discount value must be greater than 0';
    }

    if (formData.promotion_type === 'percentage' && formData.discount_value > 100) {
      newErrors.discount_value = 'Percentage discount cannot exceed 100%';
    }

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required';
    }

    if (!formData.end_date) {
      newErrors.end_date = 'End date is required';
    }

    if (formData.start_date && formData.end_date && new Date(formData.start_date) >= new Date(formData.end_date)) {
      newErrors.end_date = 'End date must be after start date';
    }

    if (formData.promotion_type === 'bogo') {
      if (formData.buy_quantity < 1) {
        newErrors.buy_quantity = 'Buy quantity must be at least 1';
      }
      if (formData.get_quantity < 1) {
        newErrors.get_quantity = 'Get quantity must be at least 1';
      }
    }

    if (formData.is_ab_test && !formData.ab_test_group.trim()) {
      newErrors.ab_test_group = 'A/B test group is required for A/B test promotions';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const addCouponCode = () => {
    if (newCouponCode.trim() && !formData.coupon_codes.includes(newCouponCode.trim().toUpperCase())) {
      handleInputChange('coupon_codes', [...formData.coupon_codes, newCouponCode.trim().toUpperCase()]);
      setNewCouponCode('');
    }
  };

  const removeCouponCode = (code: string) => {
    handleInputChange('coupon_codes', formData.coupon_codes.filter(c => c !== code));
  };

  if (!isOpen) return null;

  const tabs = [
    { id: 'basic', label: 'Basic Info', icon: Info },
    { id: 'discount', label: 'Discount', icon: DollarSign },
    { id: 'timing', label: 'Timing', icon: Clock },
    { id: 'targeting', label: 'Targeting', icon: Target },
    { id: 'limits', label: 'Limits & Rules', icon: Settings },
    { id: 'advanced', label: 'Advanced', icon: AlertCircle },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            {isEditing ? 'Edit Promotion' : 'Create New Promotion'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Form Content */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
          <div className="p-6 space-y-6">
            {/* Basic Info Tab */}
            {activeTab === 'basic' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Promotion Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      errors.name ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter promotion name"
                  />
                  {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description *
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    rows={3}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      errors.description ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Describe the promotion"
                  />
                  {errors.description && <p className="text-red-500 text-sm mt-1">{errors.description}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Internal Notes
                  </label>
                  <textarea
                    value={formData.internal_notes}
                    onChange={(e) => handleInputChange('internal_notes', e.target.value)}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Internal notes (not visible to customers)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Priority
                  </label>
                  <input
                    type="number"
                    value={formData.priority}
                    onChange={(e) => handleInputChange('priority', parseInt(e.target.value) || 1)}
                    min="1"
                    max="100"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-sm text-gray-500 mt-1">Higher numbers have higher priority</p>
                </div>
              </div>
            )}

            {/* Discount Tab */}
            {activeTab === 'discount' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Promotion Type *
                  </label>
                  <select
                    value={formData.promotion_type}
                    onChange={(e) => handleInputChange('promotion_type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="percentage">Percentage Discount</option>
                    <option value="fixed_amount">Fixed Amount Discount</option>
                    <option value="bogo">Buy One Get One</option>
                    <option value="free_shipping">Free Shipping</option>
                    <option value="bundle">Bundle Discount</option>
                    <option value="tiered">Tiered Discount</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Discount Value *
                  </label>
                  <div className="relative">
                    {formData.promotion_type === 'percentage' && (
                      <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500">%</span>
                    )}
                    {formData.promotion_type === 'fixed_amount' && (
                      <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                    )}
                    <input
                      type="number"
                      value={formData.discount_value}
                      onChange={(e) => handleInputChange('discount_value', parseFloat(e.target.value) || 0)}
                      min="0"
                      step="0.01"
                      className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                        formData.promotion_type === 'fixed_amount' ? 'pl-8' : ''
                      } ${errors.discount_value ? 'border-red-300' : 'border-gray-300'}`}
                    />
                  </div>
                  {errors.discount_value && <p className="text-red-500 text-sm mt-1">{errors.discount_value}</p>}
                </div>

                {formData.promotion_type === 'percentage' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Maximum Discount Amount
                    </label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                      <input
                        type="number"
                        value={formData.max_discount_amount || ''}
                        onChange={(e) => handleInputChange('max_discount_amount', parseFloat(e.target.value) || undefined)}
                        min="0"
                        step="0.01"
                        className="w-full pl-8 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="No limit"
                      />
                    </div>
                  </div>
                )}

                {formData.promotion_type === 'bogo' && (
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Buy Quantity *
                      </label>
                      <input
                        type="number"
                        value={formData.buy_quantity}
                        onChange={(e) => handleInputChange('buy_quantity', parseInt(e.target.value) || 1)}
                        min="1"
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                          errors.buy_quantity ? 'border-red-300' : 'border-gray-300'
                        }`}
                      />
                      {errors.buy_quantity && <p className="text-red-500 text-sm mt-1">{errors.buy_quantity}</p>}
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Get Quantity *
                      </label>
                      <input
                        type="number"
                        value={formData.get_quantity}
                        onChange={(e) => handleInputChange('get_quantity', parseInt(e.target.value) || 1)}
                        min="1"
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                          errors.get_quantity ? 'border-red-300' : 'border-gray-300'
                        }`}
                      />
                      {errors.get_quantity && <p className="text-red-500 text-sm mt-1">{errors.get_quantity}</p>}
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Get Discount %
                      </label>
                      <input
                        type="number"
                        value={formData.get_discount_percentage}
                        onChange={(e) => handleInputChange('get_discount_percentage', parseFloat(e.target.value) || 100)}
                        min="0"
                        max="100"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                )}

                {/* Coupon Codes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Coupon Codes
                  </label>
                  <div className="flex space-x-2 mb-2">
                    <input
                      type="text"
                      value={newCouponCode}
                      onChange={(e) => setNewCouponCode(e.target.value.toUpperCase())}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Enter coupon code"
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCouponCode())}
                    />
                    <button
                      type="button"
                      onClick={addCouponCode}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {formData.coupon_codes.map((code) => (
                      <span
                        key={code}
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                      >
                        {code}
                        <button
                          type="button"
                          onClick={() => removeCouponCode(code)}
                          className="ml-2 text-blue-600 hover:text-blue-800"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Timing Tab */}
            {activeTab === 'timing' && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Date & Time *
                    </label>
                    <input
                      type="datetime-local"
                      value={formData.start_date}
                      onChange={(e) => handleInputChange('start_date', e.target.value)}
                      className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                        errors.start_date ? 'border-red-300' : 'border-gray-300'
                      }`}
                    />
                    {errors.start_date && <p className="text-red-500 text-sm mt-1">{errors.start_date}</p>}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      End Date & Time *
                    </label>
                    <input
                      type="datetime-local"
                      value={formData.end_date}
                      onChange={(e) => handleInputChange('end_date', e.target.value)}
                      className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                        errors.end_date ? 'border-red-300' : 'border-gray-300'
                      }`}
                    />
                    {errors.end_date && <p className="text-red-500 text-sm mt-1">{errors.end_date}</p>}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Timezone
                  </label>
                  <select
                    value={formData.timezone}
                    onChange={(e) => handleInputChange('timezone', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">Eastern Time</option>
                    <option value="America/Chicago">Central Time</option>
                    <option value="America/Denver">Mountain Time</option>
                    <option value="America/Los_Angeles">Pacific Time</option>
                  </select>
                </div>
              </div>
            )}

            {/* Targeting Tab */}
            {activeTab === 'targeting' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Target Audience
                  </label>
                  <select
                    value={formData.target_type}
                    onChange={(e) => handleInputChange('target_type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="all_customers">All Customers</option>
                    <option value="customer_segment">Customer Segment</option>
                    <option value="specific_customers">Specific Customers</option>
                    <option value="new_customers">New Customers</option>
                    <option value="returning_customers">Returning Customers</option>
                    <option value="vip_customers">VIP Customers</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Allowed Channels
                  </label>
                  <div className="space-y-2">
                    {['website', 'mobile_app', 'email', 'sms', 'social_media', 'in_store'].map((channel) => (
                      <label key={channel} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.allowed_channels.includes(channel)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              handleInputChange('allowed_channels', [...formData.allowed_channels, channel]);
                            } else {
                              handleInputChange('allowed_channels', formData.allowed_channels.filter(c => c !== channel));
                            }
                          }}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700 capitalize">
                          {channel.replace('_', ' ')}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Limits & Rules Tab */}
            {activeTab === 'limits' && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Total Usage Limit
                    </label>
                    <input
                      type="number"
                      value={formData.usage_limit_total || ''}
                      onChange={(e) => handleInputChange('usage_limit_total', parseInt(e.target.value) || undefined)}
                      min="1"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="No limit"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Usage Limit Per Customer
                    </label>
                    <input
                      type="number"
                      value={formData.usage_limit_per_customer || ''}
                      onChange={(e) => handleInputChange('usage_limit_per_customer', parseInt(e.target.value) || undefined)}
                      min="1"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="No limit"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Minimum Order Amount
                    </label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                      <input
                        type="number"
                        value={formData.minimum_order_amount || ''}
                        onChange={(e) => handleInputChange('minimum_order_amount', parseFloat(e.target.value) || undefined)}
                        min="0"
                        step="0.01"
                        className="w-full pl-8 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="No minimum"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Minimum Quantity
                    </label>
                    <input
                      type="number"
                      value={formData.minimum_quantity || ''}
                      onChange={(e) => handleInputChange('minimum_quantity', parseInt(e.target.value) || undefined)}
                      min="1"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="No minimum"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Budget Limit
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                    <input
                      type="number"
                      value={formData.budget_limit || ''}
                      onChange={(e) => handleInputChange('budget_limit', parseFloat(e.target.value) || undefined)}
                      min="0"
                      step="0.01"
                      className="w-full pl-8 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="No limit"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.can_stack_with_other_promotions}
                      onChange={(e) => handleInputChange('can_stack_with_other_promotions', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      Allow stacking with other promotions
                    </span>
                  </label>
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.requires_approval}
                      onChange={(e) => handleInputChange('requires_approval', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      Requires approval before activation
                    </span>
                  </label>
                </div>
              </div>
            )}

            {/* Advanced Tab */}
            {activeTab === 'advanced' && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.is_ab_test}
                      onChange={(e) => handleInputChange('is_ab_test', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      Enable A/B Testing
                    </span>
                  </label>
                </div>

                {formData.is_ab_test && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        A/B Test Group *
                      </label>
                      <input
                        type="text"
                        value={formData.ab_test_group}
                        onChange={(e) => handleInputChange('ab_test_group', e.target.value)}
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                          errors.ab_test_group ? 'border-red-300' : 'border-gray-300'
                        }`}
                        placeholder="e.g., A, B, Control"
                      />
                      {errors.ab_test_group && <p className="text-red-500 text-sm mt-1">{errors.ab_test_group}</p>}
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Traffic Percentage
                      </label>
                      <input
                        type="number"
                        value={formData.ab_test_traffic_percentage}
                        onChange={(e) => handleInputChange('ab_test_traffic_percentage', parseFloat(e.target.value) || 100)}
                        min="0"
                        max="100"
                        step="0.1"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-4 p-6 border-t bg-gray-50">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              {isEditing ? 'Update Promotion' : 'Create Promotion'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PromotionForm;