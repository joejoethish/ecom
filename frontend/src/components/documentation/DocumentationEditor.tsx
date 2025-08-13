'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Save, 
  Eye, 
  Settings, 
  Tag, 
  Clock, 
  FileText,
  Link,
  Bold,
  Italic,
  List,
  ListOrdered,
  Quote,
  Code,
  Heading1,
  Heading2,
  Heading3
} from 'lucide-react';

interface DocumentationData {
  id?: string;
  title: string;
  content: string;
  excerpt: string;
  category: string;
  template?: string;
  status: string;
  visibility: string;
  metadata: Record<string, unknown>;
  tags: string[];
  version: string;
  meta_title: string;
  meta_description: string;
}

interface Category {
  id: string;
  name: string;
  slug: string;
}

interface Template {
  id: string;
  name: string;
  content_template: string;
}

interface Tag {
  id: string;
  name: string;
  slug: string;
}

interface DocumentationEditorProps {
  documentId?: string;
  onSave?: (data: DocumentationData) => void;
  onCancel?: () => void;
}

const DocumentationEditor: React.FC<DocumentationEditorProps> = ({
  documentId,
  onSave,
  onCancel
}) => {
  const [document, setDocument] = useState<DocumentationData>({
    title: '',
    content: '',
    excerpt: '',
    category: '',
    status: 'draft',
    visibility: 'internal',
    metadata: {},
    tags: [],
    version: '1.0',
    meta_title: '',
    meta_description: ''
  });

  const [categories, setCategories] = useState<Category[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'editor' | 'preview' | 'settings'>('editor');
  const [wordCount, setWordCount] = useState(0);
  const [characterCount, setCharacterCount] = useState(0);

  const contentRef = useRef<HTMLTextAreaElement>(null);

  const fetchInitialData = async () => {
    try {
      const [categoriesRes, templatesRes, tagsRes] = await Promise.all([
        fetch('/api/documentation/categories/'),
        fetch('/api/documentation/templates/'),
        fetch('/api/documentation/tags/')
      ]);

      const [categoriesData, templatesData, tagsData] = await Promise.all([
        categoriesRes.json(),
        templatesRes.json(),
        tagsRes.json()
      ]);

      setCategories(categoriesData.results || []);
      setTemplates(templatesData.results || []);
      setAvailableTags(tagsData.results || []);
    } catch (error) {
      console.error('Error fetching initial data:', error);
    }
  };

  const fetchDocument = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/documentation/documents/${documentId}/`);
      const data = await response.json();
      setDocument(data);
      setTags(data.tags || []);
    } catch (error) {
      console.error('Error fetching document:', error);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  const updateWordCount = useCallback(() => {
    const words = document.content.trim().split(/\s+/).filter(word => word.length > 0);
    setWordCount(words.length);
    setCharacterCount(document.content.length);
  }, [document.content]);

  useEffect(() => {
    fetchInitialData();
    if (documentId) {
      fetchDocument();
    }
  }, [documentId, fetchDocument]);

  useEffect(() => {
    updateWordCount();
  }, [document.content, updateWordCount]);

  // Duplicate function removed

  const handleSave = async () => {
    try {
      setSaving(true);
      const payload = {
        ...document,
        tags: tags.map(tag => tag.id)
      };

      const url = documentId 
        ? `/api/documentation/documents/${documentId}/`
        : '/api/documentation/documents/';
      
      const method = documentId ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const savedDocument = await response.json();
        if (onSave) {
          onSave(savedDocument);
        }
      } else {
        throw new Error('Failed to save document');
      }
    } catch (error) {
      console.error('Error saving document:', error);
    } finally {
      setSaving(false);
    }
  };

  const insertText = (before: string, after: string = '') => {
    if (!contentRef.current) return;

    const textarea = contentRef.current;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = document.content.substring(start, end);
    
    const newText = before + selectedText + after;
    const newContent = 
      document.content.substring(0, start) + 
      newText + 
      document.content.substring(end);

    setDocument(prev => ({ ...prev, content: newContent }));

    // Set cursor position
    setTimeout(() => {
      textarea.focus();
      const newCursorPos = start + before.length + selectedText.length + after.length;
      textarea.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };

  const formatText = (type: string) => {
    switch (type) {
      case 'bold':
        insertText('**', '**');
        break;
      case 'italic':
        insertText('*', '*');
        break;
      case 'code':
        insertText('`', '`');
        break;
      case 'h1':
        insertText('# ');
        break;
      case 'h2':
        insertText('## ');
        break;
      case 'h3':
        insertText('### ');
        break;
      case 'ul':
        insertText('- ');
        break;
      case 'ol':
        insertText('1. ');
        break;
      case 'quote':
        insertText('> ');
        break;
      case 'link':
        insertText('[', '](url)');
        break;
    }
  };

  const addTag = (tagId: string) => {
    const tag = availableTags.find(t => t.id === tagId);
    if (tag && !tags.find(t => t.id === tagId)) {
      setTags(prev => [...prev, tag]);
    }
  };

  const removeTag = (tagId: string) => {
    setTags(prev => prev.filter(t => t.id !== tagId));
  };

  const applyTemplate = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template) {
      setDocument(prev => ({
        ...prev,
        content: template.content_template,
        template: templateId
      }));
    }
  };

  const ToolbarButton: React.FC<{
    icon: React.ReactNode;
    title: string;
    onClick: () => void;
    active?: boolean;
  }> = ({ icon, title, onClick, active }) => (
    <button
      type="button"
      title={title}
      onClick={onClick}
      className={`p-2 rounded hover:bg-gray-100 ${active ? 'bg-blue-100 text-blue-600' : 'text-gray-600'}`}
    >
      {icon}
    </button>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <input
              type="text"
              placeholder="Document title..."
              value={document.title}
              onChange={(e) => setDocument(prev => ({ ...prev, title: e.target.value }))}
              className="text-xl font-semibold border-none outline-none bg-transparent"
            />
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <span>{wordCount} words</span>
              <span>•</span>
              <span>{characterCount} characters</span>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setActiveTab('editor')}
              className={`px-3 py-1 rounded ${activeTab === 'editor' ? 'bg-blue-100 text-blue-600' : 'text-gray-600'}`}
            >
              <FileText className="w-4 h-4 inline mr-1" />
              Editor
            </button>
            <button
              onClick={() => setActiveTab('preview')}
              className={`px-3 py-1 rounded ${activeTab === 'preview' ? 'bg-blue-100 text-blue-600' : 'text-gray-600'}`}
            >
              <Eye className="w-4 h-4 inline mr-1" />
              Preview
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`px-3 py-1 rounded ${activeTab === 'settings' ? 'bg-blue-100 text-blue-600' : 'text-gray-600'}`}
            >
              <Settings className="w-4 h-4 inline mr-1" />
              Settings
            </button>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      {activeTab === 'editor' && (
        <div className="border-b border-gray-200 p-2">
          <div className="flex items-center space-x-1">
            <ToolbarButton
              icon={<Bold className="w-4 h-4" />}
              title="Bold"
              onClick={() => formatText('bold')}
            />
            <ToolbarButton
              icon={<Italic className="w-4 h-4" />}
              title="Italic"
              onClick={() => formatText('italic')}
            />
            <ToolbarButton
              icon={<Code className="w-4 h-4" />}
              title="Code"
              onClick={() => formatText('code')}
            />
            <div className="w-px h-6 bg-gray-300 mx-2" />
            <ToolbarButton
              icon={<Heading1 className="w-4 h-4" />}
              title="Heading 1"
              onClick={() => formatText('h1')}
            />
            <ToolbarButton
              icon={<Heading2 className="w-4 h-4" />}
              title="Heading 2"
              onClick={() => formatText('h2')}
            />
            <ToolbarButton
              icon={<Heading3 className="w-4 h-4" />}
              title="Heading 3"
              onClick={() => formatText('h3')}
            />
            <div className="w-px h-6 bg-gray-300 mx-2" />
            <ToolbarButton
              icon={<List className="w-4 h-4" />}
              title="Bullet List"
              onClick={() => formatText('ul')}
            />
            <ToolbarButton
              icon={<ListOrdered className="w-4 h-4" />}
              title="Numbered List"
              onClick={() => formatText('ol')}
            />
            <ToolbarButton
              icon={<Quote className="w-4 h-4" />}
              title="Quote"
              onClick={() => formatText('quote')}
            />
            <ToolbarButton
              icon={<Link className="w-4 h-4" />}
              title="Link"
              onClick={() => formatText('link')}
            />
          </div>
        </div>
      )}

      {/* Content Area */}
      <div className="p-4">
        {activeTab === 'editor' && (
          <div className="space-y-4">
            <textarea
              ref={contentRef}
              value={document.content}
              onChange={(e) => setDocument(prev => ({ ...prev, content: e.target.value }))}
              placeholder="Start writing your documentation..."
              className="w-full h-96 p-4 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              onSelect={() => {
                // Selection handling removed
              }}
            />
            
            {/* Excerpt */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Excerpt (Optional)
              </label>
              <textarea
                value={document.excerpt}
                onChange={(e) => setDocument(prev => ({ ...prev, excerpt: e.target.value }))}
                placeholder="Brief description of the document..."
                className="w-full h-20 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                maxLength={500}
              />
              <p className="text-xs text-gray-500 mt-1">
                {document.excerpt.length}/500 characters
              </p>
            </div>
          </div>
        )}

        {activeTab === 'preview' && (
          <div className="prose max-w-none">
            <div dangerouslySetInnerHTML={{ __html: document.content }} />
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            {/* Basic Settings */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category
                </label>
                <select
                  value={document.category}
                  onChange={(e) => setDocument(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select category...</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Template
                </label>
                <select
                  value={document.template || ''}
                  onChange={(e) => applyTemplate(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No template</option>
                  {templates.map(template => (
                    <option key={template.id} value={template.id}>
                      {template.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <select
                  value={document.status}
                  onChange={(e) => setDocument(prev => ({ ...prev, status: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="draft">Draft</option>
                  <option value="review">Under Review</option>
                  <option value="approved">Approved</option>
                  <option value="published">Published</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Visibility
                </label>
                <select
                  value={document.visibility}
                  onChange={(e) => setDocument(prev => ({ ...prev, visibility: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="public">Public</option>
                  <option value="internal">Internal</option>
                  <option value="restricted">Restricted</option>
                  <option value="private">Private</option>
                </select>
              </div>
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tags
              </label>
              <div className="flex flex-wrap gap-2 mb-2">
                {tags.map(tag => (
                  <span
                    key={tag.id}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {tag.name}
                    <button
                      type="button"
                      onClick={() => removeTag(tag.id)}
                      className="ml-1 text-blue-600 hover:text-blue-800"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    addTag(e.target.value);
                    e.target.value = '';
                  }
                }}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Add tag...</option>
                {availableTags
                  .filter(tag => !tags.find(t => t.id === tag.id))
                  .map(tag => (
                    <option key={tag.id} value={tag.id}>
                      {tag.name}
                    </option>
                  ))}
              </select>
            </div>

            {/* SEO Settings */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">SEO Settings</h3>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Meta Title
                </label>
                <input
                  type="text"
                  value={document.meta_title}
                  onChange={(e) => setDocument(prev => ({ ...prev, meta_title: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  maxLength={200}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Meta Description
                </label>
                <textarea
                  value={document.meta_description}
                  onChange={(e) => setDocument(prev => ({ ...prev, meta_description: e.target.value }))}
                  className="w-full h-20 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  maxLength={300}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <Clock className="w-4 h-4" />
            <span>Auto-saved 2 minutes ago</span>
          </div>
          <div className="flex items-center space-x-2">
            {onCancel && (
              <button
                onClick={onCancel}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
            )}
            <button
              onClick={handleSave}
              disabled={saving}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center"
            >
              <Save className="w-4 h-4 mr-2" />
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentationEditor;