'use client';

import React from 'react';
// Simple date formatting function to replace date-fns
const formatDistanceToNow = (date: Date | string) => {
  const now = new Date();
  const past = new Date(date);
  const diffInSeconds = Math.floor((now.getTime() - past.getTime()) / 1000);
  
  if (diffInSeconds < 60) return 'just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  return `${Math.floor(diffInSeconds / 86400)}d ago`;
};
import { 
  Mail, 
  MessageSquare, 
  Smartphone, 
  Monitor,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Package,
  CreditCard,
  Truck,
  Star,
  Bell
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import type { Notification } from './types';

interface NotificationCardProps {
  notification: Notification;
  onMarkAsRead?: (id: string) => void;
  onRemove?: (id: string) => void;
  compact?: boolean;
  showActions?: boolean;
}

  notification,
  onMarkAsRead,
  onRemove,
  compact = false,
  showActions = true
}) => {
  const isUnread = notification.status !== &apos;READ&apos;;

  // Get channel icon
  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case &apos;EMAIL&apos;:
        return <Mail size={16} className="text-blue-500" />;
      case &apos;SMS&apos;:
        return <MessageSquare size={16} className="text-green-500" />;
      case &apos;PUSH&apos;:
        return <Smartphone size={16} className="text-purple-500" />;
      case &apos;IN_APP&apos;:
        return <Monitor size={16} className="text-orange-500" />;
      default:
        return <Bell size={16} className="text-gray-500" />;
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case &apos;SENT&apos;:
      case &apos;DELIVERED&apos;:
        return <CheckCircle size={16} className="text-green-500" />;
      case &apos;READ&apos;:
        return <CheckCircle size={16} className="text-blue-500" />;
      case &apos;FAILED&apos;:
        return <XCircle size={16} className="text-red-500" />;
      case &apos;PENDING&apos;:
        return <Clock size={16} className="text-yellow-500" />;
      default:
        return <AlertCircle size={16} className="text-gray-500" />;
    }
  };

  // Get priority color
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case &apos;URGENT&apos;:
        return &apos;bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200&apos;;
      case &apos;HIGH&apos;:
        return &apos;bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200&apos;;
      case &apos;NORMAL&apos;:
        return &apos;bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200&apos;;
      case &apos;LOW&apos;:
        return &apos;bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200&apos;;
      default:
        return &apos;bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200&apos;;
    }
  };

  // Get template type icon
  const getTemplateIcon = (templateType?: string) => {
    if (!templateType) return null;
    
    switch (templateType) {
      case &apos;ORDER_CONFIRMATION&apos;:
      case &apos;ORDER_STATUS_UPDATE&apos;:
        return <Package size={16} className="text-blue-500" />;
      case &apos;PAYMENT_SUCCESS&apos;:
      case &apos;PAYMENT_FAILED&apos;:
        return <CreditCard size={16} className="text-green-500" />;
      case &apos;SHIPPING_UPDATE&apos;:
      case &apos;DELIVERY_CONFIRMATION&apos;:
        return <Truck size={16} className="text-purple-500" />;
      case &apos;REVIEW_REQUEST&apos;:
        return <Star size={16} className="text-yellow-500" />;
      default:
        return null;
    }
  };

  const handleMarkAsRead = () => {
    if (onMarkAsRead && isUnread) {
      onMarkAsRead(notification.id);
    }
  };

  const handleRemove = () => {
    if (onRemove) {
      onRemove(notification.id);
    }
  };

  return (
    <Card 
      className={`
        transition-all duration-200 hover:shadow-md
        ${isUnread ? 'border-l-4 border-l-blue-500 bg-blue-50/50 dark:bg-blue-950/20' : ''}
        ${compact ? 'p-2' : 'p-4'}
      `}
    >
      <CardContent className={compact ? 'p-2' : 'p-4'}>
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div className="flex-shrink-0 mt-1">
            {getTemplateIcon(notification.template?.template_type) || getChannelIcon(notification.channel)}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Header */}
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex-1">
                <h4 className={`font-medium text-sm ${isUnread ? 'text-gray-900 dark:text-white' : 'text-gray-700 dark:text-gray-300'}`}>
                  {notification.subject}
                </h4>
                
                {/* Metadata */}
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex items-center gap-1">
                    {getChannelIcon(notification.channel)}
                    <span className="text-xs text-gray-500">
                      {notification.channel_display}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-1">
                    {getStatusIcon(notification.status)}
                    <span className="text-xs text-gray-500">
                      {notification.status_display}
                    </span>
                  </div>
                  
                  {notification.priority !== &apos;NORMAL&apos; && (
                    <Badge 
                      variant="secondary" 
                      className={`text-xs ${getPriorityColor(notification.priority)}`}
                    >
                      {notification.priority_display}
                    </Badge>
                  )}
                </div>
              </div>

              {/* Timestamp */}
              <div className="flex-shrink-0 text-xs text-gray-500">
                {formatDistanceToNow(notification.created_at)}
              </div>
            </div>

            {/* Message */}
            {!compact && (
              <div className="mb-3">
                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                  {notification.message}
                </p>
              </div>
            )}

            {/* Error message for failed notifications */}
            {notification.status === &apos;FAILED&apos; && notification.error_message && (
              <div className="mb-3 p-2 bg-red-50 dark:bg-red-950/20 rounded-md">
                <p className="text-xs text-red-600 dark:text-red-400">
                  Error: {notification.error_message}
                </p>
              </div>
            )}

            {/* Actions */}
            {showActions && (
              <div className="flex items-center gap-2">
                {isUnread && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleMarkAsRead}
                    className="text-xs"
                  >
                    Mark as read
                  </Button>
                )}
                
                {onRemove && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleRemove}
                    className="text-xs text-gray-500 hover:text-red-600"
                  >
                    Remove
                  </Button>
                )}
                
                {notification.can_retry && notification.status === &apos;FAILED&apos; && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs text-orange-600 hover:text-orange-700"
                  >
                    Retry
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default NotificationCard;