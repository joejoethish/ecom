'use client';

import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { 
  Plus, Save, Eye, Settings, Trash2, Copy, 
  GripVertical, Type, Mail, Hash, Calendar,
  FileText, Image, CheckSquare, Radio,
  Slider, Star, Signature, Upload
} from 'lucide-react';
import { FieldEditor } from './FieldEditor';
import { FormPreview } from './FormPreview';
import { FormSettings } from './FormSettings';

interface FormBuilderProps {
  form?: any;
  onSave: (formData: any) => void;
  onCancel: () => void;
}

const FIELD_TYPES = [
  { type: 'text', label: 'Text Input', icon: Type },
  { type: 'textarea', label: 'Textarea', icon: FileText },
  { type: 'email', label: 'Email', icon: Mail },
  { type: 'number', label: 'Number', icon: Hash },
  { type: 'tel', label: 'Phone', icon: Hash },
  { type: 'url', label: 'URL', icon: Type },
  { type: 'password', label: 'Password', icon: Type },
  { type: 'date', label: 'Date', icon: Calendar },
  { type: 'datetime', label: 'Date & Time', icon: Calendar },
  { type: 'time', label: 'Time', icon: Calendar },
  { type: 'select', label: 'Select Dropdown', icon: CheckSquare },
  { type: 'multiselect', label: 'Multi-Select', icon: CheckSquare },
  { type: 'radio', label: 'Radio Buttons', icon: Radio },
  { type: 'checkbox', label: 'Checkboxes', icon: CheckSquare },
  { type: 'file', label: 'File Upload', icon: Upload },
  { type: 'image', label: 'Image Upload', icon: Image },
  { type: 'signature', label: 'Digital Signature', icon: Signature },
  { type: 'rating', label: 'Rating', icon: Star },
  { type: 'slider', label: 'Slider', icon: Slider },
  { type: 'hidden', label: 'Hidden Field', icon: Type },
];

export function FormBuilder({ form, onSave, onCancel }: FormBuilderProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    slug: '',
    status: 'draft',
    is_multi_step: false,
    steps_config: { steps: [{ name: 'Step 1', fields: [] }] },
    auto_save_enabled: true,
    requires_approval: false,
    encryption_enabled: false,
    spam_protection_enabled: true,
    analytics_enabled: true,
    settings: {},
    fields: []
  });

  const [selectedField, setSelectedField] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (form) {
      setFormData({
        ...form,
        fields: form.fields || []
      });
    }
  }, [form]);

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '');
  };

  const handleFormDataChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
      ...(field === 'name' && !form ? { slug: generateSlug(value) } : {})
    }));
  };

  const addField = (fieldType: string) => {
    const newField = {
      id: `field_${Date.now()}`,
      name: `field_${formData.fields.length + 1}`,
      label: `New ${fieldType} Field`,
      field_type: fieldType,
      placeholder: '',
      help_text: '',
      default_value: '',
      options: fieldType === 'select' || fieldType === 'radio' || fieldType === 'checkbox' ? ['Option 1', 'Option 2'] : [],
      validation_rules: {},
      conditional_logic: {},
      is_required: false,
      is_readonly: false,
      is_hidden: false,
      order: formData.fields.length,
      step: formData.is_multi_step ? activeStep + 1 : 1,
      css_classes: '',
      attributes: {}
    };

    setFormData(prev => ({
      ...prev,
      fields: [...prev.fields, newField]
    }));

    setSelectedField(newField);
  };

  const updateField = (fieldId: string, updates: any) => {
    setFormData(prev => ({
      ...prev,
      fields: prev.fields.map(field =>
        field.id === fieldId ? { ...field, ...updates } : field
      )
    }));
  };

  const deleteField = (fieldId: string) => {
    setFormData(prev => ({
      ...prev,
      fields: prev.fields.filter(field => field.id !== fieldId)
    }));
    setSelectedField(null);
  };

  const duplicateField = (fieldId: string) => {
    const fieldToDuplicate = formData.fields.find(field => field.id === fieldId);
    if (fieldToDuplicate) {
      const duplicatedField = {
        ...fieldToDuplicate,
        id: `field_${Date.now()}`,
        name: `${fieldToDuplicate.name}_copy`,
        label: `${fieldToDuplicate.label} (Copy)`,
        order: formData.fields.length
      };

      setFormData(prev => ({
        ...prev,
        fields: [...prev.fields, duplicatedField]
      }));
    }
  };

  const handleDragEnd = (result: any) => {
    if (!result.destination) return;

    const items = Array.from(formData.fields);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    // Update order values
    const updatedItems = items.map((item, index) => ({
      ...item,
      order: index
    }));

    setFormData(prev => ({
      ...prev,
      fields: updatedItems
    }));
  };

  const addStep = () => {
    const newStep = {
      name: `Step ${formData.steps_config.steps.length + 1}`,
      fields: []
    };

    setFormData(prev => ({
      ...prev,
      steps_config: {
        ...prev.steps_config,
        steps: [...prev.steps_config.steps, newStep]
      }
    }));
  };

  const getCurrentStepFields = () => {
    if (!formData.is_multi_step) return formData.fields;
    return formData.fields.filter(field => field.step === activeStep + 1);
  };

  const handleSave = () => {
    // Validate form data
    if (!formData.name.trim()) {
      alert('Form name is required');
      return;
    }

    if (!formData.slug.trim()) {
      alert('Form slug is required');
      return;
    }

    onSave(formData);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar - Field Types */}
      <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
        <div className="p-4">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Field Types</h3>
          <div className="space-y-2">
            {FIELD_TYPES.map((fieldType) => {
              const Icon = fieldType.icon;
              return (
                <button
                  key={fieldType.type}
                  onClick={() => addField(fieldType.type)}
                  className="w-full flex items-center px-3 py-2 text-sm text-gray-700 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <Icon className="h-4 w-4 mr-3 text-gray-400" />
                  {fieldType.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleFormDataChange('name', e.target.value)}
                placeholder="Form Name"
                className="text-xl font-semibold text-gray-900 bg-transparent border-none focus:outline-none focus:ring-0 p-0"
              />
              <input
                type="text"
                value={formData.description}
                onChange={(e) => handleFormDataChange('description', e.target.value)}
                placeholder="Form Description"
                className="block mt-1 text-sm text-gray-600 bg-transparent border-none focus:outline-none focus:ring-0 p-0"
              />
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowPreview(true)}
                className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <Eye className="h-4 w-4 mr-2" />
                Preview
              </button>
              <button
                onClick={() => setShowSettings(true)}
                className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </button>
              <button
                onClick={handleSave}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                <Save className="h-4 w-4 mr-2" />
                Save Form
              </button>
              <button
                onClick={onCancel}
                className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>

          {/* Multi-step navigation */}
          {formData.is_multi_step && (
            <div className="mt-4 flex items-center space-x-4">
              {formData.steps_config.steps.map((step: any, index: number) => (
                <button
                  key={index}
                  onClick={() => setActiveStep(index)}
                  className={`px-3 py-1 rounded-md text-sm font-medium ${
                    activeStep === index
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {step.name}
                </button>
              ))}
              <button
                onClick={addStep}
                className="inline-flex items-center px-2 py-1 text-sm text-blue-600 hover:text-blue-700"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Step
              </button>
            </div>
          )}
        </div>

        {/* Form Builder Area */}
        <div className="flex-1 flex">
          {/* Fields List */}
          <div className="flex-1 p-6 overflow-y-auto">
            <DragDropContext onDragEnd={handleDragEnd}>
              <Droppable droppableId="form-fields">
                {(provided) => (
                  <div
                    {...provided.droppableProps}
                    ref={provided.innerRef}
                    className="space-y-3"
                  >
                    {getCurrentStepFields().length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <Type className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                        <p>No fields added yet</p>
                        <p className="text-sm">Drag field types from the sidebar to get started</p>
                      </div>
                    ) : (
                      getCurrentStepFields().map((field, index) => (
                        <Draggable key={field.id} draggableId={field.id} index={index}>
                          {(provided, snapshot) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              className={`bg-white border rounded-lg p-4 ${
                                snapshot.isDragging ? 'shadow-lg' : 'shadow-sm'
                              } ${selectedField?.id === field.id ? 'ring-2 ring-blue-500' : ''}`}
                              onClick={() => setSelectedField(field)}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-3">
                                  <div {...provided.dragHandleProps}>
                                    <GripVertical className="h-4 w-4 text-gray-400" />
                                  </div>
                                  <div>
                                    <p className="font-medium text-gray-900">{field.label}</p>
                                    <p className="text-sm text-gray-500">{field.field_type}</p>
                                  </div>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      duplicateField(field.id);
                                    }}
                                    className="p-1 text-gray-400 hover:text-gray-600"
                                  >
                                    <Copy className="h-4 w-4" />
                                  </button>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      deleteField(field.id);
                                    }}
                                    className="p-1 text-gray-400 hover:text-red-600"
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </button>
                                </div>
                              </div>
                            </div>
                          )}
                        </Draggable>
                      ))
                    )}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </DragDropContext>
          </div>

          {/* Field Editor */}
          {selectedField && (
            <div className="w-80 bg-white border-l border-gray-200">
              <FieldEditor
                field={selectedField}
                onUpdate={(updates) => updateField(selectedField.id, updates)}
                onClose={() => setSelectedField(null)}
              />
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      {showPreview && (
        <FormPreview
          form={formData}
          onClose={() => setShowPreview(false)}
        />
      )}

      {showSettings && (
        <FormSettings
          form={formData}
          onUpdate={handleFormDataChange}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}