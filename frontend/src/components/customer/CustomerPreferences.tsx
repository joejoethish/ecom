'use client';

import { useState, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '@/hooks/redux';
import { fetchCustomerProfile, updateCustomerPreferences } from '@/store/slices/customerSlice';
import { Button } from '@/components/ui/Button';
import toast from 'react-hot-toast';

const LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
];

const CURRENCY_OPTIONS = [
  { value: 'USD', label: 'US Dollar ($)' },
  { value: 'EUR', label: 'Euro (€)' },
  { value: 'GBP', label: 'British Pound (£)' },
  { value: 'CAD', label: 'Canadian Dollar (C$)' },
];

export function CustomerPreferences() {
  const dispatch = useAppDispatch();
  const { profile, loading } = useAppSelector((state) => state.customer);
  
  const [formData, setFormData] = useState({
    newsletter_subscription: false,
    sms_notifications: false,
    email_notifications: true,
    language: 'en',
    currency: 'USD',
  });
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    if (!profile) {
      dispatch(fetchCustomerProfile());
    }
  }, [dispatch, profile]);

  useEffect(() => {
    if (profile?.preferences) {
      setFormData(profile.preferences);
    }
  }, [profile]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await dispatch(updateCustomerPreferences(formData)).unwrap();
      toast.success('Preferences updated successfully!');
      setIsEditing(false);
    } catch (error: any) {
      toast.error(error || 'Failed to update preferences');
    }
  };

  const handleCancel = () => {
    if (profile?.preferences) {
      setFormData(profile.preferences);
    }
    setIsEditing(false);
  };

  const handleRefresh = async () => {
    try {
      await dispatch(fetchCustomerProfile()).unwrap();
      toast.success('Preferences refreshed');
    } catch (error: any) {
      toast.error('Failed to refresh preferences');
    }
  };

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Preferences</h2>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              loading={loading}
            >
              Refresh
            </Button>
            {!isEditing && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsEditing(true)}
              >
                Edit Preferences
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="px-6 py-4">
        {!isEditing ? (
          <div className="space-y-6">
            {/* Notification Preferences */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Notifications</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">Email Notifications</p>
                    <p className="text-sm text-gray-500">Receive order updates and promotions via email</p>
                  </div>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    formData.email_notifications 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {formData.email_notifications ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">SMS Notifications</p>
                    <p className="text-sm text-gray-500">Receive order updates via SMS</p>
                  </div>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    formData.sms_notifications 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {formData.sms_notifications ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">Newsletter Subscription</p>
                    <p className="text-sm text-gray-500">Receive our newsletter with deals and updates</p>
                  </div>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    formData.newsletter_subscription 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {formData.newsletter_subscription ? 'Subscribed' : 'Unsubscribed'}
                  </span>
                </div>
              </div>
            </div>

            {/* Localization Preferences */}
            <div className="border-t pt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Localization</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Language</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {LANGUAGE_OPTIONS.find(lang => lang.value === formData.language)?.label || formData.language}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Currency</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {CURRENCY_OPTIONS.find(curr => curr.value === formData.currency)?.label || formData.currency}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Notification Preferences */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Notifications</h3>
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="flex items-center h-5">
                    <input
                      id="email_notifications"
                      name="email_notifications"
                      type="checkbox"
                      checked={formData.email_notifications}
                      onChange={handleChange}
                      className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                  </div>
                  <div className="ml-3 text-sm">
                    <label htmlFor="email_notifications" className="font-medium text-gray-700">
                      Email Notifications
                    </label>
                    <p className="text-gray-500">Receive order updates and promotions via email</p>
                  </div>
                </div>
                
                <div className="flex items-start">
                  <div className="flex items-center h-5">
                    <input
                      id="sms_notifications"
                      name="sms_notifications"
                      type="checkbox"
                      checked={formData.sms_notifications}
                      onChange={handleChange}
                      className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                  </div>
                  <div className="ml-3 text-sm">
                    <label htmlFor="sms_notifications" className="font-medium text-gray-700">
                      SMS Notifications
                    </label>
                    <p className="text-gray-500">Receive order updates via SMS</p>
                  </div>
                </div>
                
                <div className="flex items-start">
                  <div className="flex items-center h-5">
                    <input
                      id="newsletter_subscription"
                      name="newsletter_subscription"
                      type="checkbox"
                      checked={formData.newsletter_subscription}
                      onChange={handleChange}
                      className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                  </div>
                  <div className="ml-3 text-sm">
                    <label htmlFor="newsletter_subscription" className="font-medium text-gray-700">
                      Newsletter Subscription
                    </label>
                    <p className="text-gray-500">Receive our newsletter with deals and updates</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Localization Preferences */}
            <div className="border-t pt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Localization</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Language
                  </label>
                  <select
                    name="language"
                    value={formData.language}
                    onChange={handleChange}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  >
                    {LANGUAGE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Currency
                  </label>
                  <select
                    name="currency"
                    value={formData.currency}
                    onChange={handleChange}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  >
                    {CURRENCY_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={handleCancel}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                loading={loading}
              >
                Save Preferences
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}