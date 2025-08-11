'use client';

import React, { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Upload, FileText, Settings, MapPin } from 'lucide-react';
import { useForm } from 'react-hook-form';

interface CreateImportJobModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: FormData) => void;
  loading: boolean;
}

interface ImportJobForm {
  name: string;
  description: string;
  target_model: string;
  file_format: string;
  skip_duplicates: boolean;
  update_existing: boolean;
  batch_size: number;
  mapping_config: Record<string, any>;
  validation_rules: Record<string, any>;
  transformation_rules: Record<string, any>;
}

const TARGET_MODELS = [
  { value: 'product', label: 'Products' },
  { value: 'customer', label: 'Customers' },
  { value: 'order', label: 'Orders' },
  { value: 'category', label: 'Categories' },
  { value: 'inventory', label: 'Inventory' },
  { value: 'supplier', label: 'Suppliers' },
];

const FILE_FORMATS = [
  { value: 'csv', label: 'CSV' },
  { value: 'excel', label: 'Excel' },
  { value: 'json', label: 'JSON' },
  { value: 'xml', label: 'XML' },
  { value: 'yaml', label: 'YAML' },
];

export default function CreateImportJobModal({
  open,
  onOpenChange,
  onSubmit,
  loading
}: CreateImportJobModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [activeTab, setActiveTab] = useState('basic');
  
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors }
  } = useForm<ImportJobForm>({
    defaultValues: {
      name: '',
      description: '',
      target_model: '',
      file_format: 'csv',
      skip_duplicates: true,
      update_existing: false,
      batch_size: 1000,
      mapping_config: {},
      validation_rules: {},
      transformation_rules: {},
    }
  });

  const watchedValues = watch();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      
      // Auto-detect file format
      const extension = file.name.split('.').pop()?.toLowerCase();
      if (extension && ['csv', 'xlsx', 'xls', 'json', 'xml', 'yaml', 'yml'].includes(extension)) {
        let format = extension;
        if (extension === 'xlsx' || extension === 'xls') format = 'excel';
        if (extension === 'yml') format = 'yaml';
        setValue('file_format', format);
      }
      
      // Auto-generate name if empty
      if (!watchedValues.name) {
        const baseName = file.name.replace(/\.[^/.]+$/, '');
        setValue('name', `Import ${baseName}`);
      }
    }
  };

  const handleFormSubmit = (data: ImportJobForm) => {
    if (!selectedFile) {
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('name', data.name);
    formData.append('description', data.description);
    formData.append('target_model', data.target_model);
    formData.append('file_format', data.file_format);
    formData.append('skip_duplicates', data.skip_duplicates.toString());
    formData.append('update_existing', data.update_existing.toString());
    formData.append('batch_size', data.batch_size.toString());
    formData.append('mapping_config', JSON.stringify(data.mapping_config));
    formData.append('validation_rules', JSON.stringify(data.validation_rules));
    formData.append('transformation_rules', JSON.stringify(data.transformation_rules));

    onSubmit(formData);
  };

  const handleClose = () => {
    reset();
    setSelectedFile(null);
    setActiveTab('basic');
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Create Import Job
          </DialogTitle>
          <DialogDescription>
            Upload and configure a new data import job
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="basic" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Basic
              </TabsTrigger>
              <TabsTrigger value="mapping" className="flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Mapping
              </TabsTrigger>
              <TabsTrigger value="validation" className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Validation
              </TabsTrigger>
              <TabsTrigger value="advanced" className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Advanced
              </TabsTrigger>
            </TabsList>

            <TabsContent value="basic" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Basic Information</CardTitle>
                  <CardDescription>
                    Provide basic details about the import job
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Job Name *</Label>
                      <Input
                        id="name"
                        {...register('name', { required: 'Job name is required' })}
                        placeholder="Enter job name"
                      />
                      {errors.name && (
                        <p className="text-sm text-red-600">{errors.name.message}</p>
                      )}
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="target_model">Target Model *</Label>
                      <Select
                        value={watchedValues.target_model}
                        onValueChange={(value) => setValue('target_model', value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select target model" />
                        </SelectTrigger>
                        <SelectContent>
                          {TARGET_MODELS.map((model) => (
                            <SelectItem key={model.value} value={model.value}>
                              {model.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {errors.target_model && (
                        <p className="text-sm text-red-600">{errors.target_model.message}</p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      {...register('description')}
                      placeholder="Enter job description"
                      rows={3}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="file">Upload File *</Label>
                    <Input
                      id="file"
                      type="file"
                      onChange={handleFileChange}
                      accept=".csv,.xlsx,.xls,.json,.xml,.yaml,.yml"
                    />
                    {selectedFile && (
                      <div className="text-sm text-muted-foreground">
                        Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                      </div>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="file_format">File Format</Label>
                    <Select
                      value={watchedValues.file_format}
                      onValueChange={(value) => setValue('file_format', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {FILE_FORMATS.map((format) => (
                          <SelectItem key={format.value} value={format.value}>
                            {format.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="mapping" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Field Mapping</CardTitle>
                  <CardDescription>
                    Configure how source fields map to target model fields
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8 text-muted-foreground">
                    Field mapping configuration will be available after file upload and analysis
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="validation" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Validation Rules</CardTitle>
                  <CardDescription>
                    Set up data validation rules for the import
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8 text-muted-foreground">
                    Validation rules configuration will be available based on target model
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="advanced" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Advanced Settings</CardTitle>
                  <CardDescription>
                    Configure advanced import options
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Skip Duplicates</Label>
                        <div className="text-sm text-muted-foreground">
                          Skip records that already exist
                        </div>
                      </div>
                      <Switch
                        checked={watchedValues.skip_duplicates}
                        onCheckedChange={(checked) => setValue('skip_duplicates', checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Update Existing</Label>
                        <div className="text-sm text-muted-foreground">
                          Update existing records with new data
                        </div>
                      </div>
                      <Switch
                        checked={watchedValues.update_existing}
                        onCheckedChange={(checked) => setValue('update_existing', checked)}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="batch_size">Batch Size</Label>
                    <Input
                      id="batch_size"
                      type="number"
                      {...register('batch_size', { 
                        min: { value: 1, message: 'Batch size must be at least 1' },
                        max: { value: 10000, message: 'Batch size cannot exceed 10,000' }
                      })}
                      min={1}
                      max={10000}
                    />
                    <div className="text-sm text-muted-foreground">
                      Number of records to process in each batch (1-10,000)
                    </div>
                    {errors.batch_size && (
                      <p className="text-sm text-red-600">{errors.batch_size.message}</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading || !selectedFile}>
              {loading ? 'Creating...' : 'Create Import Job'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}