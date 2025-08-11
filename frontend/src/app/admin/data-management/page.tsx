'use client';

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Upload, 
  Download, 
  Database, 
  Sync, 
  Shield, 
  FileText,
  BarChart3,
  Settings,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle
} from 'lucide-react';
import ImportJobsList from './components/ImportJobsList';
import ExportJobsList from './components/ExportJobsList';
import DataMappingsList from './components/DataMappingsList';
import SyncJobsList from './components/SyncJobsList';
import BackupsList from './components/BackupsList';
import AuditLogsList from './components/AuditLogsList';
import QualityRulesList from './components/QualityRulesList';
import DataLineageView from './components/DataLineageView';
import DataManagementStats from './components/DataManagementStats';
import { useDataManagement } from './hooks/useDataManagement';

export default function DataManagementPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const { stats, loading } = useDataManagement();

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'processing':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      completed: 'default',
      processing: 'secondary',
      failed: 'destructive',
      pending: 'outline'
    };
    
    return (
      <Badge variant={variants[status] || 'outline'} className="flex items-center gap-1">
        {getStatusIcon(status)}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Management</h1>
          <p className="text-muted-foreground">
            Comprehensive data import, export, and management system
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
          <Button variant="outline" size="sm">
            <FileText className="h-4 w-4 mr-2" />
            Documentation
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-9">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="import" className="flex items-center gap-2">
            <Upload className="h-4 w-4" />
            Import
          </TabsTrigger>
          <TabsTrigger value="export" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export
          </TabsTrigger>
          <TabsTrigger value="mappings" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            Mappings
          </TabsTrigger>
          <TabsTrigger value="sync" className="flex items-center gap-2">
            <Sync className="h-4 w-4" />
            Sync
          </TabsTrigger>
          <TabsTrigger value="backups" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Backups
          </TabsTrigger>
          <TabsTrigger value="quality" className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4" />
            Quality
          </TabsTrigger>
          <TabsTrigger value="lineage" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Lineage
          </TabsTrigger>
          <TabsTrigger value="audit" className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Audit
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <DataManagementStats />
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Import Jobs</CardTitle>
                <Upload className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.import_jobs?.total || 0}</div>
                <div className="flex items-center gap-2 mt-2">
                  {getStatusBadge('processing')}
                  <span className="text-sm text-muted-foreground">
                    {stats?.import_jobs?.processing || 0} processing
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Export Jobs</CardTitle>
                <Download className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.export_jobs?.total || 0}</div>
                <div className="flex items-center gap-2 mt-2">
                  {getStatusBadge('completed')}
                  <span className="text-sm text-muted-foreground">
                    {stats?.export_jobs?.successful || 0} successful
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Data Mappings</CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.data_mappings?.total || 0}</div>
                <div className="flex items-center gap-2 mt-2">
                  {getStatusBadge('completed')}
                  <span className="text-sm text-muted-foreground">
                    {stats?.data_mappings?.active || 0} active
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Sync Jobs</CardTitle>
                <Sync className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.sync_jobs?.total || 0}</div>
                <div className="flex items-center gap-2 mt-2">
                  {getStatusBadge('processing')}
                  <span className="text-sm text-muted-foreground">
                    {stats?.sync_jobs?.active || 0} active
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Latest data management operations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Upload className="h-4 w-4 text-blue-500" />
                      <div>
                        <p className="text-sm font-medium">Product Import</p>
                        <p className="text-xs text-muted-foreground">2 minutes ago</p>
                      </div>
                    </div>
                    {getStatusBadge('completed')}
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Download className="h-4 w-4 text-green-500" />
                      <div>
                        <p className="text-sm font-medium">Customer Export</p>
                        <p className="text-xs text-muted-foreground">5 minutes ago</p>
                      </div>
                    </div>
                    {getStatusBadge('processing')}
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Sync className="h-4 w-4 text-purple-500" />
                      <div>
                        <p className="text-sm font-medium">Inventory Sync</p>
                        <p className="text-xs text-muted-foreground">10 minutes ago</p>
                      </div>
                    </div>
                    {getStatusBadge('failed')}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>System Health</CardTitle>
                <CardDescription>Data management system status</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Import Queue</span>
                    <Badge variant="default">Healthy</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Export Queue</span>
                    <Badge variant="default">Healthy</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Sync Services</span>
                    <Badge variant="secondary">Warning</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Storage Usage</span>
                    <Badge variant="outline">75%</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="import">
          <ImportJobsList />
        </TabsContent>

        <TabsContent value="export">
          <ExportJobsList />
        </TabsContent>

        <TabsContent value="mappings">
          <DataMappingsList />
        </TabsContent>

        <TabsContent value="sync">
          <SyncJobsList />
        </TabsContent>

        <TabsContent value="backups">
          <BackupsList />
        </TabsContent>

        <TabsContent value="quality">
          <QualityRulesList />
        </TabsContent>

        <TabsContent value="lineage">
          <DataLineageView />
        </TabsContent>

        <TabsContent value="audit">
          <AuditLogsList />
        </TabsContent>
      </Tabs>
    </div>
  );
}