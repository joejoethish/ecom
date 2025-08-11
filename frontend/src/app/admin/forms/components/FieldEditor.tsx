'use client';

import React, { useState } from 'react';
import { X, Plus, Trash2, Settings, Eye, EyeOff } from 'lucide-react';

interface FieldEditorProps {
  field: any;
  onUpdate: (updates: any) => void;
  onClose: () => void;
}

export function FieldEditor({ field, onUpdate, onClose }: FieldEditorProps) {
  const [activeTab, setActiveTab] = useState('basic');

  const handleInputChange = (key: string, value: any) => {
    onUpdate({ [key]: value });
  };

  const handleValidationRuleChange = (rule: string, value: any) => {
    onUpdate({
      validation_rules: {
        ...field.validation_rules,
        [rule]: value
      }
    });
  };

  const handleOptionChange = (index: number, value: string) => {
    const newOptions = [...field.options];
    newOptions[index] = value;
    onUpdate({ options: newOptions });
  };

  const addOption = () => {
    onUpdate({
      options: [...field.options, `Option ${field.options.length + 1}`]
    });
  };

  const removeOption = (index: number) => {
    const newOptions = field.options.filter((_: any, i: number) => i !== index);
    onUpdate({ options: newOptions });
  };

  const handleAttributeChange = (key: string, value: string) => {
    onUpdate({
      attributes: {
        ...field.attributes,
        [key]: value
      }
    });
  };

  const hasOptions = ['select', 'multiselect', 'radio', 'checkbox'].includes(field.field_type);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Field Settings</h3>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-4">
          {['basic', 'validation', 'advanced'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'basic' && (
          <>
            {/* Field Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Field Name
              </label>
              <input
                type="text"
                value={field.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Used for form data (no spaces or special characters)
              </p>
            </div>

            {/* Field Label */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Label
              </label>
              <input
                type="text"
                value={field.label}
                onChange={(e) => handleInputChange('label', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Placeholder */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Placeholder
              </label>
              <input
                type="text"
                value={field.placeholder}
                onChange={(e) => handleInputChange('placeholder', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Help Text */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Help Text
              </label>
              <textarea
                value={field.help_text}
                onChange={(e) => handleInputChange('help_text', e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Default Value */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Default Value
              </label>
              <input
                type="text"
                value={field.default_value}
                onChange={(e) => handleInputChange('default_value', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Options for select/radio/checkbox fields */}
            {hasOptions && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Options
                </label>
                <div className="space-y-2">
                  {field.options.map((option: string, index: number) => (
                    <div key={index} className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={option}
                        onChange={(e) => handleOptionChange(index, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                      <button
                        onClick={() => removeOption(index)}
                        className="p-2 text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={addOption}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Option
                  </button>
                </div>
              </div>
            )}

            {/* Field States */}
            <div className="space-y-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="required"
                  checked={field.is_required}
                  onChange={(e) => handleInputChange('is_required', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="required" className="ml-2 block text-sm text-gray-900">
                  Required field
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="readonly"
                  checked={field.is_readonly}
                  onChange={(e) => handleInputChange('is_readonly', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="readonly" className="ml-2 block text-sm text-gray-900">
                  Read-only field
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="hidden"
                  checked={field.is_hidden}
                  onChange={(e) => handleInputChange('is_hidden', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="hidden" className="ml-2 block text-sm text-gray-900">
                  Hidden field
                </label>
              </div>
            </div>
          </>
        )}

        {activeTab === 'validation' && (
          <>
            {/* Min Length */}
            {['text', 'textarea', 'email', 'url', 'password'].includes(field.field_type) && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Minimum Length
                </label>
                <input
                  type="number"
                  value={field.validation_rules.min_length || ''}
                  onChange={(e) => handleValidationRuleChange('min_length', parseInt(e.target.value) || undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}

            {/* Max Length */}
            {['text', 'textarea', 'email', 'url', 'password'].includes(field.field_type) && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Maximum Length
                </label>
                <input
                  type="number"
                  value={field.validation_rules.max_length || ''}
                  onChange={(e) => handleValidationRuleChange('max_length', parseInt(e.target.value) || undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}

            {/* Min/Max Value for numbers */}
            {field.field_type === 'number' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Minimum Value
                  </label>
                  <input
                    type="number"
                    value={field.validation_rules.min_value || ''}
                    onChange={(e) => handleValidationRuleChange('min_value', parseFloat(e.target.value) || undefined)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Maximum Value
                  </label>
                  <input
                    type="number"
                    value={field.validation_rules.max_value || ''}
                    onChange={(e) => handleValidationRuleChange('max_value', parseFloat(e.target.value) || undefined)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </>
            )}

            {/* Pattern Validation */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Pattern (Regex)
              </label>
              <input
                type="text"
                value={field.validation_rules.pattern || ''}
                onChange={(e) => handleValidationRuleChange('pattern', e.target.value)}
                placeholder="^[A-Za-z0-9]+$"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Pattern Message */}
            {field.validation_rules.pattern && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Pattern Error Message
                </label>
                <input
                  type="text"
                  value={field.validation_rules.pattern_message || ''}
                  onChange={(e) => handleValidationRuleChange('pattern_message', e.target.value)}
                  placeholder="Please enter a valid format"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}

            {/* File Upload Validation */}
            {['file', 'image'].includes(field.field_type) && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Allowed File Types
                  </label>
                  <input
                    type="text"
                    value={field.validation_rules.allowed_types || ''}
                    onChange={(e) => handleValidationRuleChange('allowed_types', e.target.value)}
                    placeholder=".jpg,.png,.pdf"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max File Size (MB)
                  </label>
                  <input
                    type="number"
                    value={field.validation_rules.max_file_size || ''}
                    onChange={(e) => handleValidationRuleChange('max_file_size', parseInt(e.target.value) || undefined)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </>
            )}
          </>
        )}

        {activeTab === 'advanced' && (
          <>
            {/* CSS Classes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                CSS Classes
              </label>
              <input
                type="text"
                value={field.css_classes}
                onChange={(e) => handleInputChange('css_classes', e.target.value)}
                placeholder="custom-class another-class"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Custom Attributes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Custom HTML Attributes
              </label>
              <div className="space-y-2">
                {Object.entries(field.attributes || {}).map(([key, value]) => (
                  <div key={key} className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={key}
                      onChange={(e) => {
                        const newAttributes = { ...field.attributes };
                        delete newAttributes[key];
                        newAttributes[e.target.value] = value;
                        onUpdate({ attributes: newAttributes });
                      }}
                      placeholder="attribute"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                    <input
                      type="text"
                      value={value as string}
                      onChange={(e) => handleAttributeChange(key, e.target.value)}
                      placeholder="value"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                    <button
                      onClick={() => {
                        const newAttributes = { ...field.attributes };
                        delete newAttributes[key];
                        onUpdate({ attributes: newAttributes });
                      }}
                      className="p-2 text-red-500 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => handleAttributeChange('new-attribute', '')}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Attribute
                </button>
              </div>
            </div>

            {/* Conditional Logic */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Conditional Logic
              </label>
              <div className="p-3 border border-gray-200 rounded-md bg-gray-50">
                <p className="text-sm text-gray-600">
                  Show this field only when certain conditions are met
                </p>
                <button className="mt-2 text-sm text-blue-600 hover:text-blue-700">
                  Configure Conditions
                </button>
              </div>
            </div>

            {/* Step Assignment (for multi-step forms) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Step Assignment
              </label>
              <select
                value={field.step}
                onChange={(e) => handleInputChange('step', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={1}>Step 1</option>
                <option value={2}>Step 2</option>
                <option value={3}>Step 3</option>
              </select>
            </div>
          </>
        )}
      </div>
    </div>
  );
}