'use client';

import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  PencilIcon, 
  TrashIcon, 
  CheckIcon, 
  XMarkIcon,
  LanguageIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

interface Translation {
  id: string;
  key: string;
  value: string;
  context: string;
  language: string;
  language_name: string;
  language_code: string;
  is_approved: boolean;
  created_at: string;
  updated_at: string;
}

interface Language {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
}

interface TranslationManagerProps {
  className?: string;
}

export default function TranslationManager({ className = '' }: TranslationManagerProps) {
  const [translations, setTranslations] = useState<Translation[]>([]);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [editingTranslation, setEditingTranslation] = useState<Translation | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTranslation, setNewTranslation] = useState({
    key: '',
    value: '',
    context: '',
    language: ''
  });

  useEffect(() => {
    fetchLanguages();
  }, []);

  useEffect(() => {
    if (selectedLanguage) {
      fetchTranslations();
    }
  }, [selectedLanguage, searchTerm]);

  const fetchLanguages = async () => {
    try {
      const response = await fetch('/api/internationalization/languages/active/');
      if (response.ok) {
        const data = await response.json();
        setLanguages(data);
        if (data.length > 0) {
          setSelectedLanguage(data[0].code);
        }
      }
    } catch (error) {
      console.error('Error fetching languages:', error);
    }
  };

  const fetchTranslations = async () => {
    setLoading(true);
    try {
      let url = `/api/internationalization/translations/?language=${selectedLanguage}`;
      if (searchTerm) {
        url += `&key=${searchTerm}`;
      }
      
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setTranslations(data.results || data);
      }
    } catch (error) {
      console.error('Error fetching translations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddTranslation = async () => {
    if (!newTranslation.key || !newTranslation.value || !newTranslation.language) {
      return;
    }

    try {
      const response = await fetch('/api/internationalization/translations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          key: newTranslation.key,
          value: newTranslation.value,
          context: newTranslation.context,
          language: languages.find(l => l.code === newTranslation.language)?.id,
          is_approved: true
        }),
      });

      if (response.ok) {
        setNewTranslation({ key: '', value: '', context: '', language: '' });
        setShowAddForm(false);
        fetchTranslations();
      }
    } catch (error) {
      console.error('Error adding translation:', error);
    }
  };

  const handleUpdateTranslation = async (translation: Translation) => {
    try {
      const response = await fetch(`/api/internationalization/translations/${translation.id}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          key: translation.key,
          value: translation.value,
          context: translation.context,
          language: translation.language,
          is_approved: translation.is_approved
        }),
      });

      if (response.ok) {
        setEditingTranslation(null);
        fetchTranslations();
      }
    } catch (error) {
      console.error('Error updating translation:', error);
    }
  };

  const handleDeleteTranslation = async (translationId: string) => {
    if (!confirm('Are you sure you want to delete this translation?')) {
      return;
    }

    try {
      const response = await fetch(`/api/internationalization/translations/${translationId}/`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchTranslations();
      }
    } catch (error) {
      console.error('Error deleting translation:', error);
    }
  };

  const handleBulkTranslations = async () => {
    // This would open a modal for bulk translation management
    console.log('Bulk translations feature');
  };

  return (
    <div className={`bg-white rounded-lg shadow-md ${className}`}>
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <LanguageIcon className="h-6 w-6 text-indigo-600" />
            <h3 className="text-lg font-semibold text-gray-900">Translation Manager</h3>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={handleBulkTranslations}
              className="px-4 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-md hover:bg-indigo-100"
            >
              Bulk Import
            </button>
            <button
              onClick={() => setShowAddForm(true)}
              className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700"
            >
              <PlusIcon className="h-4 w-4" />
              <span>Add Translation</span>
            </button>
          </div>
        </div>

        <div className="flex space-x-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Language
            </label>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {languages.map((language) => (
                <option key={language.id} value={language.code}>
                  {language.name} ({language.code})
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search translation keys..."
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Add Translation Form */}
      {showAddForm && (
        <div className="p-6 bg-gray-50 border-b border-gray-200">
          <h4 className="text-md font-medium text-gray-900 mb-4">Add New Translation</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Key
              </label>
              <input
                type="text"
                value={newTranslation.key}
                onChange={(e) => setNewTranslation({ ...newTranslation, key: e.target.value })}
                placeholder="e.g., common.save"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Language
              </label>
              <select
                value={newTranslation.language}
                onChange={(e) => setNewTranslation({ ...newTranslation, language: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Select language</option>
                {languages.map((language) => (
                  <option key={language.id} value={language.code}>
                    {language.name} ({language.code})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Value
              </label>
              <input
                type="text"
                value={newTranslation.value}
                onChange={(e) => setNewTranslation({ ...newTranslation, value: e.target.value })}
                placeholder="Translation value"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Context (Optional)
              </label>
              <input
                type="text"
                value={newTranslation.context}
                onChange={(e) => setNewTranslation({ ...newTranslation, context: e.target.value })}
                placeholder="Context for translators"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
          <div className="flex justify-end space-x-2 mt-4">
            <button
              onClick={() => setShowAddForm(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleAddTranslation}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700"
            >
              Add Translation
            </button>
          </div>
        </div>
      )}

      {/* Translations List */}
      <div className="overflow-x-auto">
        {loading ? (
          <div className="p-6">
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Key
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Context
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {translations.map((translation) => (
                <tr key={translation.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {editingTranslation?.id === translation.id ? (
                      <input
                        type="text"
                        value={editingTranslation.key}
                        onChange={(e) => setEditingTranslation({ ...editingTranslation, key: e.target.value })}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                      />
                    ) : (
                      <div className="text-sm font-medium text-gray-900">{translation.key}</div>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {editingTranslation?.id === translation.id ? (
                      <textarea
                        value={editingTranslation.value}
                        onChange={(e) => setEditingTranslation({ ...editingTranslation, value: e.target.value })}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                        rows={2}
                      />
                    ) : (
                      <div className="text-sm text-gray-900 max-w-xs truncate">{translation.value}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {editingTranslation?.id === translation.id ? (
                      <input
                        type="text"
                        value={editingTranslation.context}
                        onChange={(e) => setEditingTranslation({ ...editingTranslation, context: e.target.value })}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                      />
                    ) : (
                      <div className="text-sm text-gray-500">{translation.context || '-'}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      translation.is_approved 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {translation.is_approved ? 'Approved' : 'Pending'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {editingTranslation?.id === translation.id ? (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleUpdateTranslation(editingTranslation)}
                          className="text-green-600 hover:text-green-900"
                        >
                          <CheckIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setEditingTranslation(null)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <XMarkIcon className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setEditingTranslation(translation)}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteTranslation(translation.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {translations.length === 0 && !loading && (
        <div className="p-6 text-center text-gray-500">
          No translations found for the selected language.
        </div>
      )}
    </div>
  );
}