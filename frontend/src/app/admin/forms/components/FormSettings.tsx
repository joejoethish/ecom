'use client';

import React, { useState } from 'react';
import { X, Save, Shield, Zap, BarChart3, Mail, Webhook } from 'lucide-react';

interface FormSettingsProps {
  form: any;
  onUpdate: (field: string, value: any) => void;
  onClose: () => void;
}

export function FormSettings({ form, onUpdate, onClose }: FormSettingsProps) {
  const [activeTab, setActiveTab] = useState('general');

  const handleSave = () => {
    // Settings are automatically saved through onUpdate
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Form Settings</h2>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleSave}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <Save className="h-4 w-4 mr-2" />
              Save Settings
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <div className="w-64 bg-gray-50 border-r border-gray-200 overflow-y-auto">
            <nav className="p-4 space-y-2">
              {[
                { id: 'general', label: 'General', icon: Zap },
                { id: 'security', label: 'Security', icon: Shield },
                { id: 'analytics', label: 'Analytics', icon: BarChart3 },
                { id: 'notifications', label: 'Notifications', icon: Mail },
                { id: 'integrations', label: 'Integrations', icon: Webhook },
              ].map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                      activeTab === tab.id
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="h-4 w-4 mr-3" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeTab === 'general' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">General Settings</h3>
                  
                  {/* Form Slug */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Form URL Slug
                    </label>
                    <div className="flex">
                      <span className="inline-flex items-center px-3 py-2 border border-r-0 border-gray-300 bg-gray-50 text-gray-500 text-sm rounded-l-md">
                        /forms/
                      </span>
                      <input
                        type="text"
                        value={form.slug}
                        onChange={(e) => onUpdate('slug', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-r-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <p className="mt-1 text-sm text-gray-500">
                      This will be the public URL for your form
                    </p>
                  </div>

                  {/* Multi-step Form */}
                  <div className="mb-6">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="multi-step"
                        checked={form.is_multi_step}
                        onChange={(e) => onUpdate('is_multi_step', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="multi-step" className="ml-2 block text-sm text-gray-900">
                        Enable multi-step form
                      </label>
                    </div>
                    <p className="mt-1 text-sm text-gray-500">
                      Break your form into multiple steps for better user experience
                    </p>
                  </div>

                  {/* Auto-save */}
                  <div className="mb-6">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="auto-save"
                        checked={form.auto_save_enabled}
                        onChange={(e) => onUpdate('auto_save_enabled', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="auto-save" className="ml-2 block text-sm text-gray-900">
                        Enable auto-save
                      </label>
                    </div>
                    <p className="mt-1 text-sm text-gray-500">
                      Automatically save user progress as they fill out the form
                    </p>
                  </div>

                  {/* Approval Workflow */}
                  <div className="mb-6">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="approval"
                        checked={form.requires_approval}
                        onChange={(e) => onUpdate('requires_approval', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="approval" className="ml-2 block text-sm text-gray-900">
                        Require approval for submissions
                      </label>
                    </div>
                    <p className="mt-1 text-sm text-gray-500">
                      All form submissions will need manual approval before processing
                    </p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Security Settings</h3>
                  
                  {/* Data Encryption */}
                  <div className="mb-6">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="encryption"
                        checked={form.encryption_enabled}
                        onChange={(e) => onUpdate('encryption_enabled', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="encryption" className="ml-2 block text-sm text-gray-900">
                        Enable data encryption
                      </label>
                    </div>
                    <p className="mt-1 text-sm text-gray-500">
                      Encrypt sensitive form data before storing in the database
                    </p>
                  </div>

                  {/* Spam Protection */}
                  <div className="mb-6">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="spam-protection"
                        checked={form.spam_protection_enabled}
                        onChange={(e) => onUpdate('spam_protection_enabled', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="spam-protection" className="ml-2 block text-sm text-gray-900">
                        Enable spam protection
                      </label>
                    </div>
                    <p className="mt-1 text-sm text-gray-500">
                      Automatically detect and filter spam submissions
                    </p>
                  </div>

                  {/* CAPTCHA */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      CAPTCHA Protection
                    </label>
                    <select
                      value={form.settings?.captcha_type || 'none'}
                      onChange={(e) => onUpdate('settings', { 
                        ...form.settings, 
                        captcha_type: e.target.value 
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="none">No CAPTCHA</option>
                      <option value="recaptcha">Google reCAPTCHA</option>
                      <option value="hcaptcha">hCaptcha</option>
                      <option value="simple">Simple Math CAPTCHA</option>
                    </select>
                  </div>

                  {/* Rate Limiting */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Rate Limiting (submissions per hour)
                    </label>
                    <input
                      type="number"
                      value={form.settings?.rate_limit || 10}
                      onChange={(e) => onUpdate('settings', { 
                        ...form.settings, 
                        rate_limit: parseInt(e.target.value) 
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'analytics' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Analytics Settings</h3>
                  
                  {/* Enable Analytics */}
                  <div className="mb-6">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="analytics"
                        checked={form.analytics_enabled}
                        onChange={(e) => onUpdate('analytics_enabled', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="analytics" className="ml-2 block text-sm text-gray-900">
                        Enable form analytics
                      </label>
                    </div>
                    <p className="mt-1 text-sm text-gray-500">
                      Track form views, submissions, and conversion rates
                    </p>
                  </div>

                  {/* Google Analytics */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Google Analytics Tracking ID
                    </label>
                    <input
                      type="text"
                      value={form.settings?.ga_tracking_id || ''}
                      onChange={(e) => onUpdate('settings', { 
                        ...form.settings, 
                        ga_tracking_id: e.target.value 
                      })}
                      placeholder="GA-XXXXXXXXX-X"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  {/* Conversion Tracking */}
                  <div className="mb-6">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="conversion-tracking"
                        checked={form.settings?.conversion_tracking || false}
                        onChange={(e) => onUpdate('settings', { 
                          ...form.settings, 
                          conversion_tracking: e.target.checked 
                        })}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="conversion-tracking" className="ml-2 block text-sm text-gray-900">
                        Enable conversion tracking
                      </label>
                    </div>
                  </div>

                  {/* A/B Testing */}
                  <div className="mb-6">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="ab-testing"
                        checked={form.settings?.ab_testing_enabled || false}
                        onChange={(e) => onUpdate('settings', { 
                          ...form.settings, 
                          ab_testing_enabled: e.target.checked 
                        })}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="ab-testing" className="ml-2 block text-sm text-gray-900">
                        Enable A/B testing
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Notification Settings</h3>
                  
                  {/* Email Notifications */}
                  <div className="mb-6">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="email-notifications"
                        checked={form.settings?.email_notifications || false}
                        onChange={(e) => onUpdate('settings', { 
                          ...form.settings, 
                          email_notifications: e.target.checked 
                        })}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="email-notifications" className="ml-2 block text-sm text-gray-900">
                        Send email notifications
                      </label>
                    </div>
                  </div>

                  {/* Notification Email */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Notification Email Address
                    </label>
                    <input
                      type="email"
                      value={form.settings?.notification_email || ''}
                      onChange={(e) => onUpdate('settings', { 
                        ...form.settings, 
                        notification_email: e.target.value 
                      })}
                      placeholder="admin@example.com"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  {/* Auto-responder */}
                  <div className="mb-6">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="auto-responder"
                        checked={form.settings?.auto_responder || false}
                        onChange={(e) => onUpdate('settings', { 
                          ...form.settings, 
                          auto_responder: e.target.checked 
                        })}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="auto-responder" className="ml-2 block text-sm text-gray-900">
                        Send auto-responder email
                      </label>
                    </div>
                  </div>

                  {/* Auto-responder Message */}
                  {form.settings?.auto_responder && (
                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Auto-responder Message
                      </label>
                      <textarea
                        value={form.settings?.auto_responder_message || ''}
                        onChange={(e) => onUpdate('settings', { 
                          ...form.settings, 
                          auto_responder_message: e.target.value 
                        })}
                        rows={4}
                        placeholder="Thank you for your submission..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'integrations' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Integration Settings</h3>
                  
                  {/* Webhook URL */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Webhook URL
                    </label>
                    <input
                      type="url"
                      value={form.settings?.webhook_url || ''}
                      onChange={(e) => onUpdate('settings', { 
                        ...form.settings, 
                        webhook_url: e.target.value 
                      })}
                      placeholder="https://example.com/webhook"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                    <p className="mt-1 text-sm text-gray-500">
                      Send form submissions to this URL via POST request
                    </p>
                  </div>

                  {/* CRM Integration */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      CRM Integration
                    </label>
                    <select
                      value={form.settings?.crm_integration || 'none'}
                      onChange={(e) => onUpdate('settings', { 
                        ...form.settings, 
                        crm_integration: e.target.value 
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="none">No CRM Integration</option>
                      <option value="salesforce">Salesforce</option>
                      <option value="hubspot">HubSpot</option>
                      <option value="pipedrive">Pipedrive</option>
                      <option value="zoho">Zoho CRM</option>
                    </select>
                  </div>

                  {/* Email Marketing */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Marketing Integration
                    </label>
                    <select
                      value={form.settings?.email_marketing || 'none'}
                      onChange={(e) => onUpdate('settings', { 
                        ...form.settings, 
                        email_marketing: e.target.value 
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="none">No Email Marketing</option>
                      <option value="mailchimp">Mailchimp</option>
                      <option value="constant_contact">Constant Contact</option>
                      <option value="campaign_monitor">Campaign Monitor</option>
                      <option value="aweber">AWeber</option>
                    </select>
                  </div>

                  {/* Zapier Integration */}
                  <div className="mb-6">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="zapier"
                        checked={form.settings?.zapier_enabled || false}
                        onChange={(e) => onUpdate('settings', { 
                          ...form.settings, 
                          zapier_enabled: e.target.checked 
                        })}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="zapier" className="ml-2 block text-sm text-gray-900">
                        Enable Zapier integration
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}