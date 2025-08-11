'use client';

import React, { useState, useEffect } from 'react';
import { 
  GlobeAltIcon, 
  CurrencyDollarIcon, 
  ClockIcon, 
  LanguageIcon,
  ChartBarIcon,
  CogIcon,
  DocumentTextIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import LanguageSelector from '@/components/internationalization/LanguageSelector';
import CurrencySelector from '@/components/internationalization/CurrencySelector';
import TimezoneSelector from '@/components/internationalization/TimezoneSelector';
import CurrencyConverter from '@/components/internationalization/CurrencyConverter';
import TranslationManager from '@/components/internationalization/TranslationManager';

interface InternationalizationStats {
  total_languages: number;
  active_languages: number;
  total_currencies: number;
  active_currencies: number;
  total_translations: number;
  approved_translations: number;
  localized_users: number;
  total_users: number;
}

export default function InternationalizationPage() {
  const [stats, setStats] = useState<InternationalizationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [userPreferences, setUserPreferences] = useState({
    language: 'en',
    currency: 'USD',
    timezone: 'UTC'
  });

  useEffect(() => {
    fetchStats();
    fetchUserPreferences();
  }, []);

  const fetchStats = async () => {
    try {
      // This would be a real API endpoint for internationalization stats
      const mockStats: InternationalizationStats = {
        total_languages: 25,
        active_languages: 12,
        total_currencies: 50,
        active_currencies: 20,
        total_translations: 2500,
        approved_translations: 2200,
        localized_users: 850,
        total_users: 1200
      };
      setStats(mockStats);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserPreferences = async () => {
    try {
      const response = await fetch('/api/internationalization/user-localization/my_preferences/');
      if (response.ok) {
        const data = await response.json();
        setUserPreferences(data);
      }
    } catch (error) {
      console.error('Error fetching user preferences:', error);
    }
  };

  const handleLanguageChange = async (languageCode: string) => {
    try {
      const response = await fetch('/api/internationalization/user-localization/set_preferences/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ language: languageCode }),
      });

      if (response.ok) {
        setUserPreferences(prev => ({ ...prev, language: languageCode }));
      }
    } catch (error) {
      console.error('Error updating language:', error);
    }
  };

  const handleCurrencyChange = async (currencyCode: string) => {
    try {
      const response = await fetch('/api/internationalization/user-localization/set_preferences/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ currency: currencyCode }),
      });

      if (response.ok) {
        setUserPreferences(prev => ({ ...prev, currency: currencyCode }));
      }
    } catch (error) {
      console.error('Error updating currency:', error);
    }
  };

  const handleTimezoneChange = async (timezoneName: string) => {
    try {
      const response = await fetch('/api/internationalization/user-localization/set_preferences/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ timezone: timezoneName }),
      });

      if (response.ok) {
        setUserPreferences(prev => ({ ...prev, timezone: timezoneName }));
      }
    } catch (error) {
      console.error('Error updating timezone:', error);
    }
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'translations', name: 'Translations', icon: LanguageIcon },
    { id: 'currencies', name: 'Currencies', icon: CurrencyDollarIcon },
    { id: 'settings', name: 'Settings', icon: CogIcon },
    { id: 'compliance', name: 'Compliance', icon: ShieldCheckIcon },
    { id: 'reports', name: 'Reports', icon: DocumentTextIcon },
  ];

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Internationalization</h1>
          <p className="text-gray-600">Manage languages, currencies, translations, and localization settings</p>
        </div>
        <div className="flex items-center space-x-4">
          <LanguageSelector
            currentLanguage={userPreferences.language}
            onLanguageChange={handleLanguageChange}
          />
          <CurrencySelector
            currentCurrency={userPreferences.currency}
            onCurrencyChange={handleCurrencyChange}
          />
          <TimezoneSelector
            currentTimezone={userPreferences.timezone}
            onTimezoneChange={handleTimezoneChange}
          />
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <GlobeAltIcon className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Languages</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.active_languages}/{stats.total_languages}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <CurrencyDollarIcon className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Currencies</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.active_currencies}/{stats.total_currencies}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <LanguageIcon className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Translations</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.approved_translations}/{stats.total_translations}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <ClockIcon className="h-6 w-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Localized Users</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.localized_users}/{stats.total_users}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-5 w-5" />
                <span>{tab.name}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CurrencyConverter className="lg:col-span-1" />
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <button
                  onClick={() => setActiveTab('translations')}
                  className="w-full text-left px-4 py-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="font-medium text-gray-900">Manage Translations</div>
                  <div className="text-sm text-gray-600">Add, edit, and approve translations</div>
                </button>
                <button
                  onClick={() => setActiveTab('currencies')}
                  className="w-full text-left px-4 py-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="font-medium text-gray-900">Update Exchange Rates</div>
                  <div className="text-sm text-gray-600">Refresh currency exchange rates</div>
                </button>
                <button
                  onClick={() => setActiveTab('compliance')}
                  className="w-full text-left px-4 py-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="font-medium text-gray-900">Check Compliance</div>
                  <div className="text-sm text-gray-600">Review regional compliance status</div>
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'translations' && (
          <TranslationManager />
        )}

        {activeTab === 'currencies' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CurrencyConverter />
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Exchange Rate Management</h3>
              <div className="space-y-4">
                <button className="w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                  Update All Exchange Rates
                </button>
                <div className="text-sm text-gray-600">
                  Last updated: {new Date().toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Internationalization Settings</h3>
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Language
                  </label>
                  <LanguageSelector
                    currentLanguage={userPreferences.language}
                    onLanguageChange={handleLanguageChange}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Currency
                  </label>
                  <CurrencySelector
                    currentCurrency={userPreferences.currency}
                    onCurrencyChange={handleCurrencyChange}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Timezone
                  </label>
                  <TimezoneSelector
                    currentTimezone={userPreferences.timezone}
                    onTimezoneChange={handleTimezoneChange}
                    className="w-full"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'compliance' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Regional Compliance</h3>
            <div className="text-gray-600">
              Compliance management features will be implemented here.
            </div>
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Internationalization Reports</h3>
            <div className="text-gray-600">
              Reporting features will be implemented here.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}