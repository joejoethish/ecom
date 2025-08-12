'use client';

import React, { useState, useEffect } from 'react';
import { Plus, Search, Filter, Download, Upload } from 'lucide-react';
import { FormList } from './components/FormList';
import { FormBuilder } from './components/FormBuilder';
import { FormAnalytics } from './components/FormAnalytics';
import { useFormManagement } from './hooks/useFormManagement';

export default function FormsPage() {
  const [activeTab, setActiveTab] = useState('list');
  const [selectedForm, setSelectedForm] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  
  const {
    forms,
    loading,
    createForm,
    updateForm,
    deleteForm,
    duplicateForm,
    publishForm,
    unpublishForm,
    refreshForms
  } = useFormManagement();

  useEffect(() => {
    refreshForms();
  }, []);

  const handleCreateForm = () => {
    setSelectedForm(null);
    setActiveTab('builder');
  };

  const handleEditForm = (form: any) => {
    setSelectedForm(form);
    setActiveTab('builder');
  };

  const handleViewAnalytics = (form: any) => {
    setSelectedForm(form);
    setActiveTab('analytics');
  };

  const filteredForms = forms.filter(form => {
    const matchesSearch = form.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         form.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || form.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Form Management</h1>
              <p className="mt-2 text-gray-600">
                Create, manage, and analyze your forms with advanced features
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleCreateForm}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create Form
              </button>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('list')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'list'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              All Forms
            </button>
            <button
              onClick={() => setActiveTab('builder')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'builder'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Form Builder
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'analytics'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Analytics
            </button>
          </nav>
        </div>

        {/* Content */}
        {activeTab === 'list' && (
          <div>
            {/* Filters */}
            <div className="mb-6 flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <input
                    type="text"
                    placeholder="Search forms..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">All Status</option>
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="archived">Archived</option>
                </select>
                <button className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                  <Filter className="h-4 w-4 mr-2" />
                  More Filters
                </button>
              </div>
            </div>

            <FormList
              forms={filteredForms}
              loading={loading}
              onEdit={handleEditForm}
              onDelete={deleteForm}
              onDuplicate={duplicateForm}
              onPublish={publishForm}
              onUnpublish={unpublishForm}
              onViewAnalytics={handleViewAnalytics}
            />
          </div>
        )}

        {activeTab === 'builder' && (
          <FormBuilder
            form={selectedForm}
            onSave={(formData) => {
              if (selectedForm) {
                updateForm((selectedForm as any).id, formData);
              } else {
                createForm(formData);
              }
              setActiveTab('list');
            }}
            onCancel={() => setActiveTab('list')}
          />
        )}

        {activeTab === 'analytics' && selectedForm && (
          <FormAnalytics
            form={selectedForm}
            onBack={() => setActiveTab('list')}
          />
        )}
      </div>
    </div>
  );
}