'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingUp, 
  TrendingDown, 
  Upload, 
  Download, 
  Database, 
  Sync,
  Shield,
  CheckCircle,
  AlertTriangle,
  Clock
} from 'lucide-react';
import { useDataManagement } from '../hooks/useDataManagement';

export default function DataManagementStats() {

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="h-2 bg-gray-200 rounded w-full"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const calculateSuccessRate = (successful: number, total: number) => {
    if (total === 0) return 0;
    return Math.round((successful / total) * 100);
  };

  const getStatusColor = (rate: number) => {
    if (rate >= 90) return &apos;text-green-600&apos;;
    if (rate >= 70) return &apos;text-yellow-600&apos;;
    return &apos;text-red-600&apos;;
  };

  const importSuccessRate = calculateSuccessRate(
    stats?.import_jobs?.successful || 0,
    stats?.import_jobs?.total || 0
  );

  const exportSuccessRate = calculateSuccessRate(
    stats?.export_jobs?.successful || 0,
    stats?.export_jobs?.total || 0
  );

  return (
    <div className="space-y-6">
      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Import Jobs</CardTitle>
            <Upload className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.import_jobs?.total || 0}</div>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="secondary" className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {stats?.import_jobs?.processing || 0} processing
              </Badge>
            </div>
            <div className="mt-3">
              <div className="flex justify-between text-xs text-muted-foreground mb-1">
                <span>Success Rate</span>
                <span className={getStatusColor(importSuccessRate)}>
                  {importSuccessRate}%
                </span>
              </div>
              <Progress value={importSuccessRate} className="h-1" />
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
              <Badge variant="secondary" className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {stats?.export_jobs?.processing || 0} processing
              </Badge>
            </div>
            <div className="mt-3">
              <div className="flex justify-between text-xs text-muted-foreground mb-1">
                <span>Success Rate</span>
                <span className={getStatusColor(exportSuccessRate)}>
                  {exportSuccessRate}%
                </span>
              </div>
              <Progress value={exportSuccessRate} className="h-1" />
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
              <Badge variant="default" className="flex items-center gap-1">
                <CheckCircle className="h-3 w-3" />
                {stats?.data_mappings?.active || 0} active
              </Badge>
            </div>
            <div className="mt-3">
              <div className="flex justify-between text-xs text-muted-foreground mb-1">
                <span>Active Rate</span>
                <span className="text-green-600">
                  {stats?.data_mappings?.total ? 
                    Math.round((stats.data_mappings.active / stats.data_mappings.total) * 100) : 0}%
                </span>
              </div>
              <Progress 
                value={stats?.data_mappings?.total ? 
                  (stats.data_mappings.active / stats.data_mappings.total) * 100 : 0} 
                className="h-1" 
              />
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
              <Badge variant="default" className="flex items-center gap-1">
                <CheckCircle className="h-3 w-3" />
                {stats?.sync_jobs?.active || 0} active
              </Badge>
              {(stats?.sync_jobs?.paused || 0) > 0 && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  {stats?.sync_jobs?.paused} paused
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Activity</CardTitle>
            <CardDescription>Last 30 days</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Upload className="h-4 w-4 text-blue-500" />
                <span className="text-sm">Import Jobs</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{stats?.import_jobs?.recent || 0}</span>
                <TrendingUp className="h-3 w-3 text-green-500" />
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Download className="h-4 w-4 text-green-500" />
                <span className="text-sm">Export Jobs</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{stats?.export_jobs?.recent || 0}</span>
                <TrendingUp className="h-3 w-3 text-green-500" />
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-purple-500" />
                <span className="text-sm">Backups</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{stats?.backups?.recent || 0}</span>
                <TrendingUp className="h-3 w-3 text-green-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Success Rates</CardTitle>
            <CardDescription>Overall performance metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Import Success</span>
                <span className={getStatusColor(importSuccessRate)}>
                  {importSuccessRate}%
                </span>
              </div>
              <Progress value={importSuccessRate} className="h-2" />
            </div>
            
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Export Success</span>
                <span className={getStatusColor(exportSuccessRate)}>
                  {exportSuccessRate}%
                </span>
              </div>
              <Progress value={exportSuccessRate} className="h-2" />
            </div>
            
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Backup Success</span>
                <span className="text-green-600">
                  {stats?.backups?.total ? 
                    Math.round((stats.backups.successful / stats.backups.total) * 100) : 0}%
                </span>
              </div>
              <Progress 
                value={stats?.backups?.total ? 
                  (stats.backups.successful / stats.backups.total) * 100 : 0} 
                className="h-2" 
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">System Health</CardTitle>
            <CardDescription>Current system status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm">Import Queue</span>
              <Badge variant={stats?.import_jobs?.processing ? 'secondary' : 'default'}>
                {stats?.import_jobs?.processing ? &apos;Active&apos; : &apos;Idle&apos;}
              </Badge>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm">Export Queue</span>
              <Badge variant={stats?.export_jobs?.processing ? 'secondary' : 'default'}>
                {stats?.export_jobs?.processing ? &apos;Active&apos; : &apos;Idle&apos;}
              </Badge>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm">Sync Services</span>
              <Badge variant={stats?.sync_jobs?.active ? 'default' : 'outline'}>
                {stats?.sync_jobs?.active ? &apos;Running&apos; : &apos;Stopped&apos;}
              </Badge>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm">Quality Rules</span>
              <Badge variant="default">
                {stats?.quality_rules?.active || 0} Active
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}