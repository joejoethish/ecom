'use client';

import React, { useState } from 'react';
import { X, Smartphone, Tablet, Monitor } from 'lucide-react';

interface FormPreviewProps {
  form: any;
  onClose: () => void;
}

export function FormPreview({ form, onClose }: FormPreviewProps) {
  const [viewMode, setViewMode] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [formData, setFormData] = useState<Record<string, any>>({});

  const handleInputChange = (fieldName: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const renderField = (field: any) => {
    const commonProps = {
      id: field.id,
      name: field.name,
      placeholder: field.placeholder,
      required: field.is_required,
      readOnly: field.is_readonly,
      className: `w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 ${field.css_classes}`,
      value: formData[field.name] || field.default_value || '',
      onChange: (e: any) => handleInputChange(field.name, e.target.value)
    };

    switch (field.field_type) {
      case 'text':
      case 'email':
      case 'url':
      case 'tel':
        return <input type={field.field_type} {...commonProps} />;
      
      case 'password':
        return <input type="password" {...commonProps} />;
      
      case 'number':
        return <input type="number" {...commonProps} />;
      
      case 'textarea':
        return (
          <textarea
            {...commonProps}
            rows={4}
            onChange={(e) => handleInputChange(field.name, e.target.value)}
          />
        );
      
      case 'select':
        return (
          <select
            {...commonProps}
            onChange={(e) => handleInputChange(field.name, e.target.value)}
          >
            <option value="">Select an option</option>
            {field.options.map((option: string, index: number) => (
              <option key={index} value={option}>
                {option}
              </option>
            ))}
          </select>
        );
      
      case 'radio':
        return (
          <div className="space-y-2">
            {field.options.map((option: string, index: number) => (
              <label key={index} className="flex items-center">
                <input
                  type="radio"
                  name={field.name}
                  value={option}
                  checked={formData[field.name] === option}
                  onChange={(e) => handleInputChange(field.name, e.target.value)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">{option}</span>
              </label>
            ))}
          </div>
        );
      
      case 'checkbox':
        return (
          <div className="space-y-2">
            {field.options.map((option: string, index: number) => (
              <label key={index} className="flex items-center">
                <input
                  type="checkbox"
                  name={`${field.name}[]`}
                  value={option}
                  checked={(formData[field.name] || []).includes(option)}
                  onChange={(e) => {
                    const currentValues = formData[field.name] || [];
                    const newValues = e.target.checked
                      ? [...currentValues, option]
                      : currentValues.filter((v: string) => v !== option);
                    handleInputChange(field.name, newValues);
                  }}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">{option}</span>
              </label>
            ))}
          </div>
        );
      
      case 'date':
        return <input type="date" {...commonProps} />;
      
      case 'datetime':
        return <input type="datetime-local" {...commonProps} />;
      
      case 'time':
        return <input type="time" {...commonProps} />;
      
      case 'file':
      case 'image':
        return (
          <input
            type="file"
            {...commonProps}
            accept={field.field_type === 'image' ? 'image/*' : undefined}
            onChange={(e) => handleInputChange(field.name, e.target.files?.[0])}
          />
        );
      
      case 'rating':
        return (
          <div className="flex space-x-1">
            {[1, 2, 3, 4, 5].map((rating) => (
              <button
                key={rating}
                type="button"
                onClick={() => handleInputChange(field.name, rating)}
                className={`h-8 w-8 ${
                  (formData[field.name] || 0) >= rating
                    ? 'text-yellow-400'
                    : 'text-gray-300'
                } hover:text-yellow-400`}
              >
                ★
              </button>
            ))}
          </div>
        );
      
      case 'slider':
        return (
          <div>
            <input
              type="range"
              {...commonProps}
              min={field.validation_rules?.min_value || 0}
              max={field.validation_rules?.max_value || 100}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="text-center text-sm text-gray-600 mt-1">
              {formData[field.name] || field.default_value || 0}
            </div>
          </div>
        );
      
      case 'signature':
        return (
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <p className="text-gray-500">Digital signature area</p>
            <p className="text-sm text-gray-400 mt-1">Click to sign</p>
          </div>
        );
      
      case 'hidden':
        return <input type="hidden" {...commonProps} />;
      
      default:
        return <input type="text" {...commonProps} />;
    }
  };

  const getViewportClass = () => {
    switch (viewMode) {
      case 'mobile':
        return 'max-w-sm';
      case 'tablet':
        return 'max-w-2xl';
      case 'desktop':
      default:
        return 'max-w-4xl';
    }
  };

  const getCurrentStepFields = (step: number) => {
    if (!form.is_multi_step) return form.fields;
    return form.fields.filter((field: any) => field.step === step);
  };

  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = form.is_multi_step 
    ? Math.max(...form.fields.map((f: any) => f.step), 1)
    : 1;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full h-full max-w-6xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Form Preview</h2>
            <p className="text-sm text-gray-600">{form.name}</p>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Viewport Toggle */}
            <div className="flex items-center space-x-2 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('desktop')}
                className={`p-2 rounded ${viewMode === 'desktop' ? 'bg-white shadow' : ''}`}
                title="Desktop view"
              >
                <Monitor className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('tablet')}
                className={`p-2 rounded ${viewMode === 'tablet' ? 'bg-white shadow' : ''}`}
                title="Tablet view"
              >
                <Tablet className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('mobile')}
                className={`p-2 rounded ${viewMode === 'mobile' ? 'bg-white shadow' : ''}`}
                title="Mobile view"
              >
                <Smartphone className="h-4 w-4" />
              </button>
            </div>
            
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Preview Content */}
        <div className="flex-1 overflow-auto bg-gray-50 p-6">
          <div className={`mx-auto bg-white rounded-lg shadow-sm p-8 ${getViewportClass()}`}>
            <form onSubmit={(e) => e.preventDefault()}>
              {/* Form Header */}
              <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-900 mb-2">{form.name}</h1>
                {form.description && (
                  <p className="text-gray-600">{form.description}</p>
                )}
              </div>

              {/* Multi-step Progress */}
              {form.is_multi_step && totalSteps > 1 && (
                <div className="mb-8">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-sm font-medium text-gray-700">
                      Step {currentStep} of {totalSteps}
                    </span>
                    <span className="text-sm text-gray-500">
                      {Math.round((currentStep / totalSteps) * 100)}% Complete
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${(currentStep / totalSteps) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Form Fields */}
              <div className="space-y-6">
                {getCurrentStepFields(currentStep).map((field: any) => (
                  <div key={field.id} className={field.is_hidden ? 'hidden' : ''}>
                    <label
                      htmlFor={field.id}
                      className="block text-sm font-medium text-gray-700 mb-2"
                    >
                      {field.label}
                      {field.is_required && (
                        <span className="text-red-500 ml-1">*</span>
                      )}
                    </label>
                    
                    {renderField(field)}
                    
                    {field.help_text && (
                      <p className="mt-1 text-sm text-gray-500">{field.help_text}</p>
                    )}
                  </div>
                ))}
              </div>

              {/* Navigation Buttons */}
              <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
                {form.is_multi_step && currentStep > 1 && (
                  <button
                    type="button"
                    onClick={() => setCurrentStep(prev => prev - 1)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Previous
                  </button>
                )}
                
                <div className="ml-auto">
                  {form.is_multi_step && currentStep < totalSteps ? (
                    <button
                      type="button"
                      onClick={() => setCurrentStep(prev => prev + 1)}
                      className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                    >
                      Next
                    </button>
                  ) : (
                    <button
                      type="submit"
                      className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700"
                    >
                      Submit
                    </button>
                  )}
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}