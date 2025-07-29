'use client';

import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { useAppDispatch } from '@/store';
import { 
  Filter, 
  Search, 
  CheckCheck, 
  RefreshCw,
  SortDesc,
  SortAsc
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import NotificationCard from './NotificationCard';
import {
  markNotificationRead,
  markAllNotificationsRead
} from '@/store/slices/notificationSlice';
import { AppDispatch } from '@/store';

interface NotificationFilters {
  status?: string;
  channel?: string;
  priority?: string;
  unread_only?: boolean;
}

interface NotificationListProps {
  className?: string;
  maxHeight?: string;
  showFilters?: boolean;
  showActions?: boolean;
  compact?: boolean;
}

const NotificationList: React.FC<NotificationListProps> = ({
  className = '',
  maxHeight = '600px',
  showFilters = true,
  showActions = true,
  compact = false
}) => {
  const dispatch = useAppDispatch();
  const { notifications, unreadCount } = useSelector((state: any) => state.notifications);

  const [searchTerm, setSearchTerm] = useState('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filters, setLocalFilters] = useState<NotificationFilters>({});
  const [selectedNotifications, setSelectedNotifications] = useState<string[]>([]);
  const [loading] = useState({ notifications: false, markingAsRead: false });
  const [errors] = useState({ notifications: null });

  const handleFilterChange = (key: string, value: string | boolean) => {
    const newFilters: any = { ...filters };
    if (value === '' || value === 'all') {
      delete newFilters[key];
    } else {
      newFilters[key] = value;
    }
    setLocalFilters(newFilters);
  };

  const handleClearFilters = () => {
    setLocalFilters({});
    setSearchTerm('');
  };

  const handleMarkAsRead = (notificationId: string) => {
    dispatch(markNotificationRead(notificationId));
  };

  const handleMarkAllAsRead = () => {
    dispatch(markAllNotificationsRead());
  };

  const handleMarkSelectedAsRead = () => {
    if (selectedNotifications.length > 0) {
      selectedNotifications.forEach(id => dispatch(markNotificationRead(id)));
      setSelectedNotifications([]);
    }
  };

  const handleRefresh = () => {
    // Note: In a real app, you would fetch notifications here
    console.log('Refreshing notifications...');
  };

  const handleSelectNotification = (notificationId: string) => {
    setSelectedNotifications(prev => 
      prev.includes(notificationId)
        ? prev.filter(id => id !== notificationId)
        : [...prev, notificationId]
    );
  };

  const handleSelectAll = () => {
    const unreadNotifications = (notifications || []).filter((n: any) => n.status !== 'read');
    setSelectedNotifications(
      selectedNotifications.length === unreadNotifications.length
        ? []
        : unreadNotifications.map((n: any) => n.id)
    );
  };

  // Filter and sort notifications
  const filteredNotifications = (notifications || [])
    .filter((notification: any) => {
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        return (
          (notification.subject || '').toLowerCase().includes(searchLower) ||
          (notification.message || '').toLowerCase().includes(searchLower)
        );
      }
      return true;
    })
    .sort((a: any, b: any) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();
      return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
    });

  const hasActiveFilters = Object.keys(filters).length > 0 || searchTerm;

  return (
    <div className={`bg-white rounded-lg border ${className}`}>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold">Notifications</h3>
            {unreadCount > 0 && (
              <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                {unreadCount} unread
              </Badge>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={loading.notifications}
            >
              <RefreshCw size={16} className={loading.notifications ? 'animate-spin' : ''} />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
            >
              {sortOrder === 'desc' ? <SortDesc size={16} /> : <SortAsc size={16} />}
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <Input
            placeholder="Search notifications..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <select
              value={filters.status || 'all'}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="all">All Status</option>
              <option value="PENDING">Pending</option>
              <option value="SENT">Sent</option>
              <option value="DELIVERED">Delivered</option>
              <option value="READ">Read</option>
              <option value="FAILED">Failed</option>
            </select>

            <select
              value={filters.channel || 'all'}
              onChange={(e) => handleFilterChange('channel', e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="all">All Channels</option>
              <option value="EMAIL">Email</option>
              <option value="SMS">SMS</option>
              <option value="PUSH">Push</option>
              <option value="IN_APP">In-App</option>
            </select>

            <select
              value={filters.priority || 'all'}
              onChange={(e) => handleFilterChange('priority', e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="all">All Priorities</option>
              <option value="URGENT">Urgent</option>
              <option value="HIGH">High</option>
              <option value="NORMAL">Normal</option>
              <option value="LOW">Low</option>
            </select>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleFilterChange('unread_only', !filters.unread_only)}
              className={filters.unread_only ? 'bg-blue-50 text-blue-700' : ''}
            >
              <Filter size={16} className="mr-1" />
              Unread Only
            </Button>

            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearFilters}
                className="text-gray-500"
              >
                Clear Filters
              </Button>
            )}
          </div>
        )}

        {/* Actions */}
        {showActions && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAll}
              disabled={(notifications || []).length === 0}
            >
              {selectedNotifications.length === (notifications || []).filter((n: any) => n.status !== 'read').length
                ? 'Deselect All'
                : 'Select All Unread'
              }
            </Button>

            {selectedNotifications.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleMarkSelectedAsRead}
              >
                <CheckCheck size={16} className="mr-1" />
                Mark Selected as Read ({selectedNotifications.length})
              </Button>
            )}

            {unreadCount > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleMarkAllAsRead}
                disabled={loading.markingAsRead}
              >
                <CheckCheck size={16} className="mr-1" />
                Mark All as Read
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Error Display */}
      {errors.notifications && (
        <div className="p-4 bg-red-50 border-b">
          <p className="text-sm text-red-600">
            {errors.notifications}
          </p>
        </div>
      )}

      {/* Notifications List */}
      <div style={{ maxHeight, overflowY: 'auto' }}>
        <div className="p-4 space-y-3">
          {loading.notifications && (notifications || []).length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw size={24} className="animate-spin text-gray-400" />
              <span className="ml-2 text-gray-500">Loading notifications...</span>
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">
                {hasActiveFilters ? 'No notifications match your filters' : 'No notifications yet'}
              </p>
            </div>
          ) : (
            filteredNotifications.map((notification: any) => (
              <div key={notification.id} className="relative">
                {showActions && (
                  <div className="absolute top-2 left-2 z-10">
                    <input
                      type="checkbox"
                      checked={selectedNotifications.includes(notification.id)}
                      onChange={() => handleSelectNotification(notification.id)}
                      className="rounded border-gray-300"
                    />
                  </div>
                )}
                
                <NotificationCard
                  notification={notification}
                  onMarkAsRead={handleMarkAsRead}
                  compact={compact}
                  showActions={!showActions}
                />
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default NotificationList;