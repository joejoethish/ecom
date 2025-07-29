'use client';

import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useAppDispatch } from '@/store';
import { Save, RefreshCw, Settings, Mail, MessageSquare, Smartphone, Monitor } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import {
  markNotificationRead,
  markAllNotificationsRead
} from '@/store/slices/notificationSlice';
import { AppDispatch } from '@/store';

interface NotificationPreferencesProps {
  className?: string;
}

interface PreferenceState {
  [key: string]: {
    [channel: string]: boolean;
  };
}

const NotificationPreferences: React.FC<NotificationPreferencesProps> = ({
  className = ''
}) => {
  const dispatch = useAppDispatch();
  const { notifications } = useSelector((state: any) => state.notifications);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<any>(null);

  const [localPreferences, setLocalPreferences] = useState<PreferenceState>({});
  const [hasChanges, setHasChanges] = useState(false);

  // Default preferences structure
  const defaultPreferences = {
    order_updates: {
      email: true,
      sms: true,
      push: true,
      in_app: true
    },
    promotional: {
      email: false,
      sms: false,
      push: false,
      in_app: true
    },
    security: {
      email: true,
      sms: true,
      push: true,
      in_app: true
    },
    inventory: {
      email: true,
      sms: false,
      push: true,
      in_app: true
    }
  };

  useEffect(() => {
    // Initialize with default preferences
    setLocalPreferences(defaultPreferences);
  }, []);

  const handlePreferenceChange = (category: string, channel: string, enabled: boolean) => {
    setLocalPreferences(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [channel]: enabled
      }
    }));
    setHasChanges(true);
  };

  const handleSavePreferences = async () => {
    setLoading(true);
    setErrors(null);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setHasChanges(false);
      console.log('Preferences saved:', localPreferences);
    } catch (error: any) {
      setErrors({ preferences: error.message });
    } finally {
      setLoading(false);
    }
  };

  const handleResetPreferences = () => {
    setLocalPreferences(defaultPreferences);
    setHasChanges(true);
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'email':
        return <Mail size={16} className="text-blue-500" />;
      case 'sms':
        return <MessageSquare size={16} className="text-green-500" />;
      case 'push':
        return <Smartphone size={16} className="text-purple-500" />;
      case 'in_app':
        return <Monitor size={16} className="text-orange-500" />;
      default:
        return null;
    }
  };

  const getCategoryTitle = (category: string) => {
    switch (category) {
      case 'order_updates':
        return 'Order Updates';
      case 'promotional':
        return 'Promotional';
      case 'security':
        return 'Security';
      case 'inventory':
        return 'Inventory';
      default:
        return category;
    }
  };

  const getCategoryDescription = (category: string) => {
    switch (category) {
      case 'order_updates':
        return 'Notifications about your order status, shipping updates, and delivery confirmations';
      case 'promotional':
        return 'Marketing emails, special offers, and promotional content';
      case 'security':
        return 'Security alerts, login notifications, and account changes';
      case 'inventory':
        return 'Stock alerts, product availability, and inventory updates';
      default:
        return '';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Notification Preferences</h2>
          <p className="text-gray-600 mt-1">
            Manage how you receive notifications across different channels
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleResetPreferences}
            disabled={loading}
          >
            <RefreshCw size={16} className="mr-1" />
            Reset to Defaults
          </Button>
          
          <Button
            onClick={handleSavePreferences}
            disabled={!hasChanges || loading}
            size="sm"
          >
            <Save size={16} className="mr-1" />
            {loading ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {errors && errors.preferences && (
        <Alert variant="destructive">
          <AlertDescription>
            {errors.preferences}
          </AlertDescription>
        </Alert>
      )}

      {/* Preferences Grid */}
      <div className="grid gap-6">
        {Object.entries(localPreferences).map(([category, channels]) => (
          <Card key={category}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings size={20} />
                {getCategoryTitle(category)}
              </CardTitle>
              <CardDescription>
                {getCategoryDescription(category)}
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(channels).map(([channel, enabled]) => (
                  <div key={channel} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-2">
                      {getChannelIcon(channel)}
                      <span className="font-medium capitalize">{channel.replace('_', ' ')}</span>
                    </div>
                    
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={enabled}
                        onChange={(e) => handlePreferenceChange(category, channel, e.target.checked)}
                        disabled={loading}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Notification Summary</CardTitle>
          <CardDescription>
            Overview of your current notification settings
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {['email', 'sms', 'push', 'in_app'].map(channel => {
              const enabledCount = Object.values(localPreferences).filter(
                (channels: any) => channels[channel]
              ).length;
              const totalCount = Object.keys(localPreferences).length;
              
              return (
                <div key={channel} className="text-center p-3 border rounded-lg">
                  <div className="flex items-center justify-center mb-2">
                    {getChannelIcon(channel)}
                  </div>
                  <div className="font-medium capitalize">{channel.replace('_', ' ')}</div>
                  <Badge variant={enabledCount > 0 ? 'default' : 'secondary'} className="mt-1">
                    {enabledCount}/{totalCount} enabled
                  </Badge>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Changes Indicator */}
      {hasChanges && (
        <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
            <span className="text-sm">You have unsaved changes</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationPreferences;