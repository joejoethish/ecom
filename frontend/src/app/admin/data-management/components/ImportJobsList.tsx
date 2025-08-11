'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { 
  Upload, 
  Search, 
  Filter, 
  MoreHorizontal, 
  Play, 
  Pause, 
  RotateCcw,
  Trash2,
  Eye,
  Download,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useImportJobs, useCreateImportJob, DataImportJob } from '../hooks/useDataManagement';
import CreateImportJobModal from './CreateImportJobModal';
import ImportJobDetailsModal from './ImportJobDetailsModal';

export default function ImportJobsList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedJob, setSelectedJob] = useState<DataImportJob | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  const { data: importJobsData, isLoading, refetch } = useImportJobs({
    search: searchTerm,
    status: statusFilter !== 'all' ? statusFilter : undefined,
  });

  const createImportJobMutation = useCreateImportJob();

  const importJobs = importJobsData?.results || [];

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
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      completed: 'default',
      processing: 'secondary',
      failed: 'destructive',
      cancelled: 'outline',
      pending: 'outline'
    };
    
    return (
      <Badge variant={variants[status] || 'outline'} className="flex items-center gap-1">
        {getStatusIcon(status)}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
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

  const handleCreateJob = async (data: any) => {
    try {
      await createImportJobMutation.mutateAsync(data);
      setShowCreateModal(false);
    } catch (error) {
      console.error('Failed to create import job:', error);
    }
  };

  const handleViewDetails = (job: DataImportJob) => {
    setSelectedJob(job);
    setShowDetailsModal(true);
  };

  const handleJobAction = async (action: string, job: DataImportJob) => {
    try {
      switch (action) {
        case 'cancel':
          // Implement cancel logic
          break;
        case 'retry':
          // Implement retry logic
          break;
        case 'delete':
          // Implement delete logic
          break;
      }
      refetch();
    } catch (error) {
      console.error(`Failed to ${action} job:`, error);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Import Jobs
              </CardTitle>
              <CardDescription>
                Manage data import operations and monitor their progress
              </CardDescription>
            </div>
            <Button onClick={() => setShowCreateModal(true)}>
              <Upload className="h-4 w-4 mr-2" />
              New Import
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Search import jobs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Target Model</TableHead>
                  <TableHead>Format</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead>Records</TableHead>
                  <TableHead>File Size</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={10} className="text-center py-8">
                      Loading import jobs...
                    </TableCell>
                  </TableRow>
                ) : importJobs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={10} className="text-center py-8">
                      No import jobs found
                    </TableCell>
                  </TableRow>
                ) : (
                  importJobs.map((job) => (
                    <TableRow key={job.id} className="hover:bg-muted/50">
                      <TableCell>
                        <div>
                          <div className="font-medium">{job.name}</div>
                          {job.description && (
                            <div className="text-sm text-muted-foreground">
                              {job.description}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{job.content_type_name}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{job.file_format.toUpperCase()}</Badge>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(job.status)}
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <Progress value={job.progress_percentage} className="w-20" />
                          <div className="text-xs text-muted-foreground">
                            {job.progress_percentage}%
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <div className="text-green-600">✓ {job.successful_records}</div>
                          {job.failed_records > 0 && (
                            <div className="text-red-600">✗ {job.failed_records}</div>
                          )}
                          <div className="text-muted-foreground">
                            / {job.total_records}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{formatFileSize(job.file_size)}</TableCell>
                      <TableCell>{formatDuration(job.duration)}</TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <div>{new Date(job.created_at).toLocaleDateString()}</div>
                          <div className="text-muted-foreground">
                            {job.created_by_name}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleViewDetails(job)}>
                              <Eye className="h-4 w-4 mr-2" />
                              View Details
                            </DropdownMenuItem>
                            {job.status === 'processing' && (
                              <DropdownMenuItem onClick={() => handleJobAction('cancel', job)}>
                                <Pause className="h-4 w-4 mr-2" />
                                Cancel
                              </DropdownMenuItem>
                            )}
                            {job.status === 'failed' && (
                              <DropdownMenuItem onClick={() => handleJobAction('retry', job)}>
                                <RotateCcw className="h-4 w-4 mr-2" />
                                Retry
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuItem 
                              onClick={() => handleJobAction('delete', job)}
                              className="text-red-600"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <CreateImportJobModal
        open={showCreateModal}
        onOpenChange={setShowCreateModal}
        onSubmit={handleCreateJob}
        loading={createImportJobMutation.isPending}
      />

      {selectedJob && (
        <ImportJobDetailsModal
          open={showDetailsModal}
          onOpenChange={setShowDetailsModal}
          job={selectedJob}
        />
      )}
    </div>
  );
}