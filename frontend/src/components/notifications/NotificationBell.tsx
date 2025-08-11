'use client';

import React, { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useAppDispatch } from '@/store';
import { Bell, BellRing } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import {
  toggleNotificationCenter
} from '@/store/slices/notificationSlice';
import { AppDispatch } from '@/store';

interface NotificationBellProps {
  className?: string;
  showBadge?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const NotificationBell: React.FC<NotificationBellProps> = ({
  className = '',
  showBadge = true,
  size = 'md'
}) => {
  const dispatch = useAppDispatch();
  const { unreadCount, isNotificationCenterOpen } = useSelector((state: any) => state.notifications);

  const handleClick = () => {
    dispatch(toggleNotificationCenter());
  };

  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12'
  };

  const iconSizes = {
    sm: 16,
    md: 20,
    lg: 24
  };

  return (
    <div className={`relative ${className}`}>
      <Button
        variant="ghost"
        size="sm"
        className={`${sizeClasses[size]} relative hover:bg-gray-100 dark:hover:bg-gray-800`}
        onClick={handleClick}
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
      >
        {unreadCount > 0 ? (
          <BellRing 
            size={iconSizes[size]} 
            className="text-blue-600 dark:text-blue-400" 
          />
        ) : (
          <Bell 
            size={iconSizes[size]} 
            className="text-gray-600 dark:text-gray-400" 
          />
        )}
        
        {showBadge && unreadCount > 0 && (
          <Badge
            variant="destructive"
            className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs font-bold"
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </Badge>
        )}
      </Button>
      
      {/* Pulse animation for new notifications */}
      {unreadCount > 0 && (
        <div className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full animate-pulse" />
      )}
    </div>
  );
};

export default NotificationBell;