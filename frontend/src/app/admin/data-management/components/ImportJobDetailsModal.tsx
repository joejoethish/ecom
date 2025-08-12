'use client';

import React from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { 
  FileText, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  XCircle,
  Database,
  Settings,
  Activity
} from 'lucide-react';
import { DataImportJob } from '../hooks/useDataManagement';

interface ImportJobDetailsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  job: DataImportJob;
}

export default function ImportJobDetailsModal({
  open,
  onOpenChange,
  job
}: ImportJobDetailsModalProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'processing':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Import Job Details
          </DialogTitle>
          <DialogDescription>
            Detailed information about the import job
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Status Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {getStatusIcon(job.status)}
                {job.name}
              </CardTitle>
              <CardDescription>{job.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Status</div>
                  <Badge variant={job.status === 'completed' ? 'default' : 'secondary'}>
                    {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Progress</div>
                  <div className="flex items-center gap-2">
                    <Progress value={job.progress_percentage} className="flex-1" />
                    <span className="text-sm">{job.progress_percentage}%</span>
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Target Model</div>
                  <div className="font-medium">{job.content_type_name}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">File Format</div>
                  <div className="font-medium">{job.file_format.toUpperCase()}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Tabs defaultValue="overview" className="space-y-4">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="records">Records</TabsTrigger>
              <TabsTrigger value="errors">Errors</TabsTrigger>
              <TabsTrigger value="config">Configuration</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">File Information</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">File Path:</span>
                      <span className="font-mono text-sm">{job.file_path}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">File Size:</span>
                      <span>{formatFileSize(job.file_size)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Format:</span>
                      <span>{job.file_format.toUpperCase()}</span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Timing</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Created:</span>
                      <span>{new Date(job.created_at).toLocaleString()}</span>
                    </div>
                    {job.started_at && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Started:</span>
                        <span>{new Date(job.started_at).toLocaleString()}</span>
                      </div>
                    )}
                    {job.completed_at && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Completed:</span>
                        <span>{new Date(job.completed_at).toLocaleString()}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Duration:</span>
                      <span>{formatDuration(job.duration)}</span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="records" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Total Records</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{job.total_records}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base text-green-600">Successful</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-600">{job.successful_records}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base text-red-600">Failed</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-red-600">{job.failed_records}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Processed</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{job.processed_records}</div>
                  </CardContent>
                </Card>
              </div>

              {job.total_records > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Processing Progress</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Success Rate</span>
                        <span>{((job.successful_records / job.total_records) * 100).toFixed(1)}%</span>
                      </div>
                      <Progress 
                        value={(job.successful_records / job.total_records) * 100} 
                        className="h-2"
                      />
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="errors" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Validation Errors</CardTitle>
                  <CardDescription>
                    Errors found during data validation
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {job.validation_errors.length > 0 ? (
                    <div className="space-y-2 max-h-60 overflow-y-auto">
                      {job.validation_errors.map((error, index) => (
                        <div key={index} className="p-3 bg-red-50 border border-red-200 rounded-md">
                          <div className="text-sm text-red-800">
                            <strong>Row {error.row}:</strong> {error.message}
                          </div>
                          {error.field && (
                            <div className="text-xs text-red-600 mt-1">
                              Field: {error.field}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-4 text-muted-foreground">
                      No validation errors
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Processing Errors</CardTitle>
                  <CardDescription>
                    Errors that occurred during processing
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {job.error_log.length > 0 ? (
                    <div className="space-y-2 max-h-60 overflow-y-auto">
                      {job.error_log.map((error, index) => (
                        <div key={index} className="p-3 bg-red-50 border border-red-200 rounded-md">
                          <div className="text-sm text-red-800">
                            {error.error || JSON.stringify(error)}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-4 text-muted-foreground">
                      No processing errors
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="config" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Import Settings</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Skip Duplicates:</span>
                      <span>{job.skip_duplicates ? 'Yes' : 'No'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Update Existing:</span>
                      <span>{job.update_existing ? 'Yes' : 'No'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Batch Size:</span>
                      <span>{job.batch_size}</span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Created By</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">User:</span>
                      <span>{job.created_by_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Date:</span>
                      <span>{new Date(job.created_at).toLocaleDateString()}</span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {Object.keys(job.mapping_config).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Field Mapping</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="text-sm bg-muted p-3 rounded-md overflow-x-auto">
                      {JSON.stringify(job.mapping_config, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              )}

              {Object.keys(job.validation_rules).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Validation Rules</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="text-sm bg-muted p-3 rounded-md overflow-x-auto">
                      {JSON.stringify(job.validation_rules, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  );
}