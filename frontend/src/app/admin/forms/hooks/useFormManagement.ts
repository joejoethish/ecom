'use client';

import { useState, useCallback } from 'react';

interface Form {
  id: string;
  name: string;
  slug: string;
  description: string;
  status: 'draft' | 'active' | 'inactive' | 'archived';
  is_multi_step: boolean;
  created_at: string;
  updated_at: string;
  published_at?: string;
  submission_count: number;
  conversion_rate: number;
  fields: any[];
}

export function useFormManagement() {
  const [forms, setForms] = useState<Form[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiCall = async (url: string, options: RequestInit = {}) => {
    const token = localStorage.getItem('admin_token');
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  };

  const refreshForms = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall('/api/admin/forms/forms/');
      setForms(data.results || data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch forms');
      console.error('Error fetching forms:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createForm = useCallback(async (formData: Partial<Form>) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall('/api/admin/forms/forms/', {
        method: 'POST',
        body: JSON.stringify(formData),
      });
      setForms(prev => [data, ...prev]);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create form');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateForm = useCallback(async (id: string, formData: Partial<Form>) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall(`/api/admin/forms/forms/${id}/`, {
        method: 'PUT',
        body: JSON.stringify(formData),
      });
      setForms(prev => prev.map(form => form.id === id ? data : form));
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update form');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteForm = useCallback(async (id: string) => {
    if (!confirm('Are you sure you want to delete this form? This action cannot be undone.')) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await apiCall(`/api/admin/forms/forms/${id}/`, {
        method: 'DELETE',
      });
      setForms(prev => prev.filter(form => form.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete form');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const duplicateForm = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall(`/api/admin/forms/forms/${id}/duplicate/`, {
        method: 'POST',
      });
      setForms(prev => [data, ...prev]);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to duplicate form');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const publishForm = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall(`/api/admin/forms/forms/${id}/publish/`, {
        method: 'POST',
      });
      setForms(prev => prev.map(form => 
        form.id === id ? { ...form, status: 'active', published_at: new Date().toISOString() } : form
      ));
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to publish form');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const unpublishForm = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall(`/api/admin/forms/forms/${id}/unpublish/`, {
        method: 'POST',
      });
      setForms(prev => prev.map(form => 
        form.id === id ? { ...form, status: 'inactive' } : form
      ));
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unpublish form');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getFormAnalytics = useCallback(async (id: string, params: any = {}) => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams(params).toString();
      const data = await apiCall(`/api/admin/forms/forms/${id}/analytics/?${queryParams}`);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getFormSubmissions = useCallback(async (formId: string, params: any = {}) => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams({ form_id: formId, ...params }).toString();
      const data = await apiCall(`/api/admin/forms/submissions/?${queryParams}`);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch submissions');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const approveSubmission = useCallback(async (submissionId: string, comments: string = '') => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall(`/api/admin/forms/submissions/${submissionId}/approve/`, {
        method: 'POST',
        body: JSON.stringify({ comments }),
      });
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve submission');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const rejectSubmission = useCallback(async (submissionId: string, comments: string = '') => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall(`/api/admin/forms/submissions/${submissionId}/reject/`, {
        method: 'POST',
        body: JSON.stringify({ comments }),
      });
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject submission');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const exportSubmissions = useCallback(async (formId: string, format: string = 'csv') => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall(`/api/admin/forms/submissions/export/?form_id=${formId}&format=${format}`);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export submissions');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getFormTemplates = useCallback(async (type?: string) => {
    setLoading(true);
    setError(null);
    try {
      const url = type 
        ? `/api/admin/forms/templates/by_type/?type=${type}`
        : '/api/admin/forms/templates/';
      const data = await apiCall(url);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch templates');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const createFormFromTemplate = useCallback(async (templateId: string, formData: any) => {
    setLoading(true);
    setError(null);
    try {
      const template = await apiCall(`/api/admin/forms/templates/${templateId}/`);
      const newFormData = {
        ...formData,
        template: templateId,
        schema: template.schema,
        settings: template.settings,
      };
      const data = await createForm(newFormData);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create form from template');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [createForm]);

  const createABTest = useCallback(async (testData: any) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall('/api/admin/forms/ab-tests/', {
        method: 'POST',
        body: JSON.stringify(testData),
      });
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create A/B test');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const startABTest = useCallback(async (testId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall(`/api/admin/forms/ab-tests/${testId}/start/`, {
        method: 'POST',
      });
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start A/B test');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const stopABTest = useCallback(async (testId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall(`/api/admin/forms/ab-tests/${testId}/stop/`, {
        method: 'POST',
      });
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop A/B test');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    forms,
    loading,
    error,
    refreshForms,
    createForm,
    updateForm,
    deleteForm,
    duplicateForm,
    publishForm,
    unpublishForm,
    getFormAnalytics,
    getFormSubmissions,
    approveSubmission,
    rejectSubmission,
    exportSubmissions,
    getFormTemplates,
    createFormFromTemplate,
    createABTest,
    startABTest,
    stopABTest,
  };
}