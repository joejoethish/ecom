'use client';

import React, { useEffect, useState } from 'react';
import { useAppDispatch } from '@/store';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/Badge';
import { markNotificationRead } from '@/store/slices/notificationSlice';
import { AppDispatch } from '@/store';
import type { Notification } from './types';

interface InAppNotificationProps {
  notification: Notification;
  onDismiss?: (id: string) => void;
  autoHide?: boolean;
  autoHideDelay?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
  showActions?: boolean;
}

const InAppNotification: React.FC<InAppNotificationProps> = ({
  notification,
  onDismiss,
  autoHide = true,
  autoHideDelay = 5000,
  position = 'top-right',
  showActions = true
}) => {
  const dispatch = useAppDispatch();
  const [isVisible, setIsVisible] = useState(true);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    if (autoHide && autoHideDelay > 0) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, autoHideDelay);

      return () => clearTimeout(timer);
    }
  }, [autoHide, autoHideDelay]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => {
      setIsVisible(false);
      if (onDismiss) {
        onDismiss(notification.id);
      }
    }, 300); // Animation duration
  };

  const handleMarkAsRead = () => {
    dispatch(markNotificationRead(notification.id));
    handleDismiss();
  };

  const getIcon = () => {
    switch (notification.priority) {
      case 'URGENT':
        return <AlertTriangle size={20} className="text-red-500" />;
      case 'HIGH':
        return <AlertCircle size={20} className="text-orange-500" />;
      case 'NORMAL':
        return <Info size={20} className="text-blue-500" />;
      case 'LOW':
        return <CheckCircle size={20} className="text-green-500" />;
      default:
        return <Info size={20} className="text-gray-500" />;
    }
  };

  const getPositionClasses = () => {
    switch (position) {
      case 'top-right':
        return 'top-4 right-4';
      case 'top-left':
        return 'top-4 left-4';
      case 'bottom-right':
        return 'bottom-4 right-4';
      case 'bottom-left':
        return 'bottom-4 left-4';
      case 'top-center':
        return 'top-4 left-1/2 transform -translate-x-1/2';
      case 'bottom-center':
        return 'bottom-4 left-1/2 transform -translate-x-1/2';
      default:
        return 'top-4 right-4';
    }
  };

  const getPriorityStyles = () => {
    switch (notification.priority) {
      case 'URGENT':
        return 'border-l-4 border-l-red-500 bg-red-50 dark:bg-red-950/20';
      case 'HIGH':
        return 'border-l-4 border-l-orange-500 bg-orange-50 dark:bg-orange-950/20';
      case 'NORMAL':
        return 'border-l-4 border-l-blue-500 bg-blue-50 dark:bg-blue-950/20';
      case 'LOW':
        return 'border-l-4 border-l-green-500 bg-green-50 dark:bg-green-950/20';
      default:
        return 'border-l-4 border-l-gray-500 bg-gray-50 dark:bg-gray-950/20';
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div
      className={`
        fixed z-50 w-80 max-w-sm
        ${getPositionClasses()}
        transition-all duration-300 ease-in-out
        ${isExiting ? 'opacity-0 transform translate-x-full' : 'opacity-100 transform translate-x-0'}
      `}
    >
      <Card className={`shadow-lg ${getPriorityStyles()}`}>
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div className="flex-shrink-0 mt-0.5">
              {getIcon()}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              {/* Header */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex-1">
                  <h4 className="font-medium text-sm text-gray-900 dark:text-white">
                    {notification.subject}
                  </h4>
                  
                  {/* Channel and Priority badges */}
                  <div className="flex items-center gap-1 mt-1">
                    <Badge variant="outline" className="text-xs">
                      {notification.channel_display}
                    </Badge>
                    
                    {notification.priority !== 'NORMAL' && (
                      <Badge 
                        variant="secondary" 
                        className={`text-xs ${
                          notification.priority === 'URGENT' ? 'bg-red-100 text-red-800' :
                          notification.priority === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                          'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {notification.priority_display}
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Close button */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleDismiss}
                  className="h-6 w-6 text-gray-400 hover:text-gray-600"
                >
                  <X size={14} />
                </Button>
              </div>

              {/* Message */}
              <div className="mb-3">
                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">
                  {notification.message}
                </p>
              </div>

              {/* Actions */}
              {showActions && (
                <div className="flex items-center gap-2">
                  {notification.status !== 'READ' && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleMarkAsRead}
                      className="text-xs h-7"
                    >
                      Mark as read
                    </Button>
                  )}
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleDismiss}
                    className="text-xs h-7 text-gray-500"
                  >
                    Dismiss
                  </Button>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default InAppNotification;