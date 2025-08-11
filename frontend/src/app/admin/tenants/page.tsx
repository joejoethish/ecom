'use client';

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Building2, Users, Settings, BarChart3, Shield,
  Database, CreditCard, Activity
} from 'lucide-react';
import TenantDashboard from '@/components/tenants/TenantDashboard';
import TenantSettings from '@/components/tenants/TenantSettings';
import TenantUserManagement from '@/components/tenants/TenantUserManagement';
import TenantAnalytics from '@/components/tenants/TenantAnalytics';

// Mock tenant data - in real app, this would come from context or API
const mockTenant = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  name: 'Acme Corporation',
  subdomain: 'acme',
  plan: 'professional',
  status: 'active',
  users_count: 12,
  storage_used: 2.5,
  max_storage_gb: 10,
};

export default function TenantsPage() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Building2 className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">{mockTenant.name}</h1>
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <span>{mockTenant.subdomain}.example.com</span>
              <Badge 
                variant={mockTenant.status === 'active' ? 'default' : 'secondary'}
                className="capitalize"
              >
                {mockTenant.status}
              </Badge>
              <Badge variant="outline" className="capitalize">
                {mockTenant.plan}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Users className="h-4 w-4 text-blue-500" />
              <div>
                <p className="text-sm font-medium">{mockTenant.users_count} Users</p>
                <p className="text-xs text-muted-foreground">Active members</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Database className="h-4 w-4 text-green-500" />
              <div>
                <p className="text-sm font-medium">{mockTenant.storage_used} GB</p>
                <p className="text-xs text-muted-foreground">
                  of {mockTenant.max_storage_gb} GB used
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-orange-500" />
              <div>
                <p className="text-sm font-medium">1,234 API Calls</p>
                <p className="text-xs text-muted-foreground">This month</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CreditCard className="h-4 w-4 text-purple-500" />
              <div>
                <p className="text-sm font-medium">$99/month</p>
                <p className="text-xs text-muted-foreground">Current plan</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="dashboard" className="flex items-center space-x-2">
            <BarChart3 className="h-4 w-4" />
            <span>Dashboard</span>
          </TabsTrigger>
          <TabsTrigger value="users" className="flex items-center space-x-2">
            <Users className="h-4 w-4" />
            <span>Users</span>
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center space-x-2">
            <Activity className="h-4 w-4" />
            <span>Analytics</span>
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center space-x-2">
            <Settings className="h-4 w-4" />
            <span>Settings</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <TenantDashboard tenantId={mockTenant.id} />
        </TabsContent>

        <TabsContent value="users">
          <TenantUserManagement tenantId={mockTenant.id} />
        </TabsContent>

        <TabsContent value="analytics">
          <TenantAnalytics tenantId={mockTenant.id} />
        </TabsContent>

        <TabsContent value="settings">
          <TenantSettings tenantId={mockTenant.id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}