'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Switch } from '@/components/ui/Switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';
import {
  Palette, Shield, Bell, Zap, Globe, Database,
  Save, Upload, AlertTriangle, CheckCircle
} from 'lucide-react';

interface TenantSettings {
  branding: {
    primary_color: string;
    secondary_color: string;
    logo: string | null;
    favicon: string | null;
  };
  features: {
    [key: string]: boolean;
  };
  limits: {
    max_users: number;
    max_products: number;
    max_orders: number;
    max_storage_gb: number;
  };
  notifications: {
    [key: string]: boolean;
  };
  security: {
    [key: string]: any;
  };
  integrations: {
    [key: string]: any;
  };
}

interface TenantSettingsProps {
  tenantId: string;
}

export default function TenantSettings({ tenantId }: TenantSettingsProps) {
  const [settings, setSettings] = useState<TenantSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchSettings();
  }, [tenantId]);

  const fetchSettings = async () => {
    try {
      const response = await fetch(`/api/tenants/${tenantId}/settings/`);
      const data = await response.json();
      setSettings(data);
    } catch (error) {
      console.error('Error fetching settings:', error);
      setMessage({ type: 'error', text: 'Failed to load settings' });
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    if (!settings) return;

    setSaving(true);
    try {
      const response = await fetch(`/api/tenants/${tenantId}/settings/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Settings saved successfully' });
      } else {
        throw new Error('Failed to save settings');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      setMessage({ type: 'error', text: 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  const updateBranding = (field: string, value: string) => {
    if (!settings) return;
    setSettings({
      ...settings,
      branding: {
        ...settings.branding,
        [field]: value,
      },
    });
  };

  const updateFeature = (feature: string, enabled: boolean) => {
    if (!settings) return;
    setSettings({
      ...settings,
      features: {
        ...settings.features,
        [feature]: enabled,
      },
    });
  };

  const updateNotification = (notification: string, enabled: boolean) => {
    if (!settings) return;
    setSettings({
      ...settings,
      notifications: {
        ...settings.notifications,
        [notification]: enabled,
      },
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!settings) {
    return (
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Failed to load settings. Please try again.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Message */}
      {message && (
        <Alert className={
          message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
        }>
          {message.type === 'success' ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <AlertTriangle className="h-4 w-4 text-red-600" />
          )}
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={saveSettings} disabled={saving}>
          <Save className="h-4 w-4 mr-2" />
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>

      <Tabs defaultValue="branding" className="space-y-6">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="branding">
            <Palette className="h-4 w-4 mr-2" />
            Branding
          </TabsTrigger>
          <TabsTrigger value="features">
            <Zap className="h-4 w-4 mr-2" />
            Features
          </TabsTrigger>
          <TabsTrigger value="limits">
            <Database className="h-4 w-4 mr-2" />
            Limits
          </TabsTrigger>
          <TabsTrigger value="notifications">
            <Bell className="h-4 w-4 mr-2" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="security">
            <Shield className="h-4 w-4 mr-2" />
            Security
          </TabsTrigger>
          <TabsTrigger value="integrations">
            <Globe className="h-4 w-4 mr-2" />
            Integrations
          </TabsTrigger>
        </TabsList>

        {/* Branding Tab */}
        <TabsContent value="branding">
          <Card>
            <CardHeader>
              <CardTitle>Branding & Appearance</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="primary-color">Primary Color</Label>
                  <div className="flex items-center space-x-2">
                    <Input
                      id="primary-color"
                      type="color"
                      value={settings.branding.primary_color}
                      onChange={(e) => updateBranding('primary_color', e.target.value)}
                      className="w-16 h-10"
                    />
                    <Input
                      value={settings.branding.primary_color}
                      onChange={(e) => updateBranding('primary_color', e.target.value)}
                      placeholder="#007bff"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="secondary-color">Secondary Color</Label>
                  <div className="flex items-center space-x-2">
                    <Input
                      id="secondary-color"
                      type="color"
                      value={settings.branding.secondary_color}
                      onChange={(e) => updateBranding('secondary_color', e.target.value)}
                      className="w-16 h-10"
                    />
                    <Input
                      value={settings.branding.secondary_color}
                      onChange={(e) => updateBranding('secondary_color', e.target.value)}
                      placeholder="#6c757d"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Logo</Label>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    {settings.branding.logo ? (
                      <img
                        src={settings.branding.logo}
                        alt="Logo"
                        className="mx-auto h-16 object-contain"
                      />
                    ) : (
                      <div className="text-gray-500">
                        <Upload className="h-8 w-8 mx-auto mb-2" />
                        <p>Upload Logo</p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Favicon</Label>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    {settings.branding.favicon ? (
                      <img
                        src={settings.branding.favicon}
                        alt="Favicon"
                        className="mx-auto h-8 w-8 object-contain"
                      />
                    ) : (
                      <div className="text-gray-500">
                        <Upload className="h-8 w-8 mx-auto mb-2" />
                        <p>Upload Favicon</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Features Tab */}
        <TabsContent value="features">
          <Card>
            <CardHeader>
              <CardTitle>Feature Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(settings.features).map(([feature, enabled]) => (
                  <div key={feature} className="flex items-center justify-between">
                    <div>
                      <Label className="text-sm font-medium capitalize">
                        {feature.replace(/_/g, ' ')}
                      </Label>
                      <p className="text-xs text-muted-foreground">
                        {getFeatureDescription(feature)}
                      </p>
                    </div>
                    <Switch
                      checked={enabled}
                      onCheckedChange={(checked) => updateFeature(feature, checked)}
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Limits Tab */}
        <TabsContent value="limits">
          <Card>
            <CardHeader>
              <CardTitle>Usage Limits</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Maximum Users</Label>
                  <div className="flex items-center space-x-2">
                    <Input
                      type="number"
                      value={settings.limits.max_users}
                      readOnly
                      className="bg-gray-50"
                    />
                    <Badge variant="secondary">Plan Limit</Badge>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Maximum Products</Label>
                  <div className="flex items-center space-x-2">
                    <Input
                      type="number"
                      value={settings.limits.max_products}
                      readOnly
                      className="bg-gray-50"
                    />
                    <Badge variant="secondary">Plan Limit</Badge>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Maximum Orders</Label>
                  <div className="flex items-center space-x-2">
                    <Input
                      type="number"
                      value={settings.limits.max_orders}
                      readOnly
                      className="bg-gray-50"
                    />
                    <Badge variant="secondary">Plan Limit</Badge>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Storage Limit (GB)</Label>
                  <div className="flex items-center space-x-2">
                    <Input
                      type="number"
                      value={settings.limits.max_storage_gb}
                      readOnly
                      className="bg-gray-50"
                    />
                    <Badge variant="secondary">Plan Limit</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(settings.notifications).map(([notification, enabled]) => (
                  <div key={notification} className="flex items-center justify-between">
                    <div>
                      <Label className="text-sm font-medium capitalize">
                        {notification.replace(/_/g, ' ')}
                      </Label>
                      <p className="text-xs text-muted-foreground">
                        {getNotificationDescription(notification)}
                      </p>
                    </div>
                    <Switch
                      checked={enabled}
                      onCheckedChange={(checked) => updateNotification(notification, checked)}
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle>Security Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <Alert>
                  <Shield className="h-4 w-4" />
                  <AlertDescription>
                    Security settings are managed at the platform level. Contact support for changes.
                  </AlertDescription>
                </Alert>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Two-Factor Authentication</Label>
                      <p className="text-xs text-muted-foreground">
                        Require 2FA for all users
                      </p>
                    </div>
                    <Badge variant="outline">Enterprise Only</Badge>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>IP Restrictions</Label>
                      <p className="text-xs text-muted-foreground">
                        Limit access to specific IP addresses
                      </p>
                    </div>
                    <Badge variant="outline">Enterprise Only</Badge>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Session Timeout</Label>
                      <p className="text-xs text-muted-foreground">
                        Automatic logout after inactivity
                      </p>
                    </div>
                    <Badge variant="secondary">30 minutes</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Integrations Tab */}
        <TabsContent value="integrations">
          <Card>
            <CardHeader>
              <CardTitle>Third-Party Integrations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Alert>
                  <Globe className="h-4 w-4" />
                  <AlertDescription>
                    Integrations are coming soon. Contact support for custom integrations.
                  </AlertDescription>
                </Alert>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium">Stripe</h4>
                    <p className="text-sm text-muted-foreground">Payment processing</p>
                    <Badge variant="outline" className="mt-2">Coming Soon</Badge>
                  </div>

                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium">Mailgun</h4>
                    <p className="text-sm text-muted-foreground">Email delivery</p>
                    <Badge variant="outline" className="mt-2">Coming Soon</Badge>
                  </div>

                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium">Slack</h4>
                    <p className="text-sm text-muted-foreground">Team notifications</p>
                    <Badge variant="outline" className="mt-2">Coming Soon</Badge>
                  </div>

                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium">Google Analytics</h4>
                    <p className="text-sm text-muted-foreground">Website analytics</p>
                    <Badge variant="outline" className="mt-2">Coming Soon</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function getFeatureDescription(feature: string): string {
  const descriptions: { [key: string]: string } = {
    analytics: 'Advanced analytics and reporting',
    reports: 'Custom report generation',
    api_access: 'REST API access',
    custom_branding: 'Custom colors and logo',
    advanced_permissions: 'Granular user permissions',
    priority_support: '24/7 priority support',
  };
  return descriptions[feature] || 'Feature configuration';
}

function getNotificationDescription(notification: string): string {
  const descriptions: { [key: string]: string } = {
    email_alerts: 'Email notifications for important events',
    usage_warnings: 'Alerts when approaching usage limits',
    billing_reminders: 'Payment and billing notifications',
    security_alerts: 'Security-related notifications',
    system_updates: 'Platform updates and maintenance',
  };
  return descriptions[notification] || 'Notification setting';
}