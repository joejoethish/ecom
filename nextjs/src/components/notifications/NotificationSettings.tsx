'use client';

import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useAppDispatch } from '@/store';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Separator } from '@/components/ui/Separator';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import {
  BarChart3,
  Bell,
  Mail,
  MessageSquare,
  Smartphone,
  Monitor,
  TrendingUp,
  Users,
  Clock,
  CheckCircle,
  XCircle,
  RefreshCw
} from 'lucide-react';
import NotificationPreferences from './NotificationPreferences';
import {
  markNotificationRead,
  markAllNotificationsRead
} from '@/store/slices/notificationSlice';
import { AppDispatch } from '@/store';

interface NotificationSettingsProps {
  className?: string;
}

const NotificationSettings: React.FC<NotificationSettingsProps> = ({
  className = ''
}) => {
  const dispatch = useAppDispatch();
  const { notifications } = useSelector((state: any) => state.notifications);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Mock stats data
  const [stats] = useState({
    total_notifications: 1250,
    unread_count: 45,
    read_count: 1205,
    failed_count: 12,
    email_count: 650,
    sms_count: 200,
    push_count: 300,
    in_app_count: 100,
    today_count: 25,
    this_week_count: 180,
    this_month_count: 750
  });

  const [settings] = useState({
    global_enabled: true,
    rate_limiting: {
      enabled: true,
      max_per_hour: 100,
      max_per_day: 500
    },
    retry_settings: {
      max_retries: 3,
      retry_delay: 300
    }
  });

  useEffect(() => {
    // In a real app, you would fetch stats and settings here
    console.log('Loading notification settings...');
  }, []);

  const handleRefreshStats = () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setLoading(false);
      console.log('Stats refreshed');
    }, 1000);
  };

  const StatCard = ({ 
    title, 
    value, 
    icon: Icon, 
    color = 'blue',
    description 
  }: {
    title: string;
    value: number | string;
    icon: any;
    color?: string;
    description?: string;
  }) => (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            {description && (
              <p className="text-xs text-gray-500 mt-1">{description}</p>
            )}
          </div>
          <div className={`p-3 rounded-full bg-${color}-100`}>
            <Icon size={24} className={`text-${color}-600`} />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Notification Settings</h1>
          <p className="text-gray-600 mt-1">
            Manage notification preferences, view statistics, and configure system settings
          </p>
        </div>
        
        <Button
          variant="outline"
          onClick={handleRefreshStats}
          disabled={loading}
        >
          <RefreshCw size={16} className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh Stats
        </Button>
      </div>

      {/* Error Display */}
      {errors && errors.stats && (
        <Alert variant="destructive">
          <AlertDescription>
            {errors.stats}
          </AlertDescription>
        </Alert>
      )}

      {/* Tabs */}
      <div className="w-full">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'overview', label: 'Overview', icon: BarChart3 },
              { id: 'preferences', label: 'Preferences', icon: Bell },
              { id: 'system', label: 'System Settings', icon: Monitor }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon size={16} className="mr-2" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="mt-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Overview Stats */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                  title="Total Notifications"
                  value={stats.total_notifications.toLocaleString()}
                  icon={Bell}
                  color="blue"
                />
                
                <StatCard
                  title="Unread"
                  value={stats.unread_count}
                  icon={Mail}
                  color="orange"
                  description={`${((stats.unread_count / stats.total_notifications) * 100).toFixed(1)}% of total`}
                />
                
                <StatCard
                  title="Read"
                  value={stats.read_count.toLocaleString()}
                  icon={CheckCircle}
                  color="green"
                  description={`${((stats.read_count / stats.total_notifications) * 100).toFixed(1)}% of total`}
                />
                
                <StatCard
                  title="Failed"
                  value={stats.failed_count}
                  icon={XCircle}
                  color="red"
                  description={`${((stats.failed_count / stats.total_notifications) * 100).toFixed(1)}% of total`}
                />
              </div>

              {/* Channel Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle>Channel Distribution</CardTitle>
                  <CardDescription>
                    Breakdown of notifications by delivery channel
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <Mail size={20} className="text-blue-500" />
                        <span className="font-medium">Email</span>
                      </div>
                      <Badge variant="secondary">{stats.email_count}</Badge>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <MessageSquare size={20} className="text-green-500" />
                        <span className="font-medium">SMS</span>
                      </div>
                      <Badge variant="secondary">{stats.sms_count}</Badge>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <Smartphone size={20} className="text-purple-500" />
                        <span className="font-medium">Push</span>
                      </div>
                      <Badge variant="secondary">{stats.push_count}</Badge>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <Monitor size={20} className="text-orange-500" />
                        <span className="font-medium">In-App</span>
                      </div>
                      <Badge variant="secondary">{stats.in_app_count}</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Time-based Stats */}
              <Card>
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                  <CardDescription>
                    Notification activity over different time periods
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 border rounded-lg">
                      <Clock size={24} className="mx-auto mb-2 text-blue-500" />
                      <div className="font-bold text-2xl">{stats.today_count}</div>
                      <div className="text-sm text-gray-600">Today</div>
                    </div>
                    
                    <div className="text-center p-4 border rounded-lg">
                      <TrendingUp size={24} className="mx-auto mb-2 text-green-500" />
                      <div className="font-bold text-2xl">{stats.this_week_count}</div>
                      <div className="text-sm text-gray-600">This Week</div>
                    </div>
                    
                    <div className="text-center p-4 border rounded-lg">
                      <Users size={24} className="mx-auto mb-2 text-purple-500" />
                      <div className="font-bold text-2xl">{stats.this_month_count}</div>
                      <div className="text-sm text-gray-600">This Month</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Performance Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Delivery Success Rate</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span>Success Rate</span>
                        <span className="font-bold text-green-600">
                          {stats.total_notifications > 0 
                            ? (((stats.total_notifications - stats.failed_count) / stats.total_notifications) * 100).toFixed(1)
                            : 0}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-green-600 h-2 rounded-full" 
                          style={{ 
                            width: stats.total_notifications > 0 
                              ? `${((stats.total_notifications - stats.failed_count) / stats.total_notifications) * 100}%`
                              : '0%'
                          }}
                        ></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Failure Rate</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span>Failure Rate</span>
                        <span className="font-bold text-red-600">
                          {stats.total_notifications > 0 
                            ? ((stats.failed_count / stats.total_notifications) * 100).toFixed(1)
                            : 0}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-red-600 h-2 rounded-full" 
                          style={{ 
                            width: stats.total_notifications > 0 
                              ? `${(stats.failed_count / stats.total_notifications) * 100}%`
                              : '0%'
                          }}
                        ></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {activeTab === 'preferences' && (
            <NotificationPreferences />
          )}

          {activeTab === 'system' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Global Settings</CardTitle>
                  <CardDescription>
                    System-wide notification configuration
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">Global Notifications</div>
                      <div className="text-sm text-gray-600">
                        Enable or disable all notifications system-wide
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.global_enabled}
                        className="sr-only peer"
                        readOnly
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Rate Limiting</CardTitle>
                  <CardDescription>
                    Control notification frequency to prevent spam
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Max per Hour
                      </label>
                      <input
                        type="number"
                        value={settings.rate_limiting.max_per_hour}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Max per Day
                      </label>
                      <input
                        type="number"
                        value={settings.rate_limiting.max_per_day}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        readOnly
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Retry Settings</CardTitle>
                  <CardDescription>
                    Configure retry behavior for failed notifications
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Max Retries
                      </label>
                      <input
                        type="number"
                        value={settings.retry_settings.max_retries}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Retry Delay (seconds)
                      </label>
                      <input
                        type="number"
                        value={settings.retry_settings.retry_delay}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        readOnly
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NotificationSettings;