'use client';

import { useState, useEffect } from 'react';
import { useAppSelector } from '@/store';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/Badge';
import { Switch } from '@/components/ui/Switch';

interface NotificationPreference {
  id: string;
  type: string;
  label: string;
  description: string;
  email: boolean;
  push: boolean;
  sms: boolean;
}

export default function NotificationsPage() {
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const [preferences, setPreferences] = useState<NotificationPreference[]>([
    {
      id: '1',
      type: 'order_updates',
      label: 'Order Updates',
      description: 'Get notified about order status changes, shipping updates, and delivery confirmations',
      email: true,
      push: true,
      sms: false,
    },
    {
      id: '2',
      type: 'promotions',
      label: 'Promotions & Offers',
      description: 'Receive notifications about special deals, discounts, and promotional offers',
      email: true,
      push: false,
      sms: false,
    },
    {
      id: '3',
      type: 'product_updates',
      label: 'Product Updates',
      description: 'Get notified when items in your wishlist go on sale or are back in stock',
      email: false,
      push: true,
      sms: false,
    },
    {
      id: '4',
      type: 'account_security',
      label: 'Account Security',
      description: 'Important security notifications about your account and login activities',
      email: true,
      push: true,
      sms: true,
    },
    {
      id: '5',
      type: 'newsletter',
      label: 'Newsletter',
      description: 'Weekly newsletter with new products, trends, and shopping tips',
      email: false,
      push: false,
      sms: false,
    },
  ]);

  const [isSaving, setIsSaving] = useState(false);

  const handlePreferenceChange = (id: string, channel: 'email' | 'push' | 'sms', value: boolean) => {
    setPreferences(prev => 
      prev.map(pref => 
        pref.id === id ? { ...pref, [channel]: value } : pref
      )
    );
  };

  const handleSavePreferences = async () => {
    setIsSaving(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      // Here you would make an actual API call to save preferences
      console.log('Saving preferences:', preferences);
    } catch (error) {
      console.error('Error saving preferences:', error);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="p-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Sign In Required
          </h1>
          <p className="text-gray-600 mb-6">
            Please sign in to manage your notification preferences.
          </p>
          <Button onClick={() => window.location.href = '/auth/login'}>
            Sign In
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Notification Preferences</h1>
          <p className="mt-2 text-gray-600">
            Manage how you receive notifications about orders, promotions, and account updates.
          </p>
        </div>

        <Card className="p-6">
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pb-4 border-b border-gray-200">
              <div className="font-medium text-gray-900">Notification Type</div>
              <div className="text-center font-medium text-gray-900">Email</div>
              <div className="text-center font-medium text-gray-900">Push</div>
              <div className="text-center font-medium text-gray-900">SMS</div>
            </div>

            {preferences.map((preference) => (
              <div key={preference.id} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-start py-4 border-b border-gray-100 last:border-b-0">
                <div className="space-y-1">
                  <div className="font-medium text-gray-900 flex items-center gap-2">
                    {preference.label}
                    {preference.type === 'account_security' && (
                      <Badge variant="secondary" className="text-xs">Required</Badge>
                    )}
                  </div>
                  <div className="text-sm text-gray-600">
                    {preference.description}
                  </div>
                </div>
                
                <div className="flex justify-center">
                  <Switch
                    checked={preference.email}
                    onCheckedChange={(checked) => 
                      handlePreferenceChange(preference.id, 'email', checked)
                    }
                    disabled={preference.type === 'account_security'}
                  />
                </div>
                
                <div className="flex justify-center">
                  <Switch
                    checked={preference.push}
                    onCheckedChange={(checked) => 
                      handlePreferenceChange(preference.id, 'push', checked)
                    }
                    disabled={preference.type === 'account_security'}
                  />
                </div>
                
                <div className="flex justify-center">
                  <Switch
                    checked={preference.sms}
                    onCheckedChange={(checked) => 
                      handlePreferenceChange(preference.id, 'sms', checked)
                    }
                    disabled={preference.type === 'account_security'}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="flex justify-between items-center">
              <div className="text-sm text-gray-600">
                Security notifications cannot be disabled for account safety.
              </div>
              <Button 
                onClick={handleSavePreferences}
                disabled={isSaving}
                className="min-w-[120px]"
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </div>
        </Card>

        <div className="mt-8">
          <Card className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Notification History
            </h2>
            <div className="space-y-4">
              <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    Order #12345 has been shipped
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    2 hours ago via Email and Push
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
                <div className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    Special offer: 20% off Electronics
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    1 day ago via Email
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                <div className="flex-shrink-0 w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    Item in your wishlist is now on sale
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    3 days ago via Push
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}