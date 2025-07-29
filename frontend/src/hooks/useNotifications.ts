import { useEffect, useState, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { RootState, useAppDispatch } from '@/store';
import { addNotification, markNotificationRead } from '@/store/slices/notificationSlice';
import useWebSocket, { ConnectionState } from './useWebSocket';
import { getAuthToken } from '@/utils/auth';

interface UseNotificationsReturn {
  isConnected: boolean;
  markAsRead: (notificationId: string) => void;
  error: string | null;
}

/**
 * Custom hook for real-time notifications
 * @returns Notification state and methods
 */
export const useNotifications = (): UseNotificationsReturn => {
  const [error, setError] = useState<string | null>(null);
  const dispatch = useAppDispatch();
  
  // Get current user from Redux store
  const user = useSelector((state: RootState) => state.auth.user);
  
  // Get API URL from environment
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const wsUrl = apiUrl.replace(/^http/, 'ws');
  
  // Get auth token for WebSocket authentication
  const token = getAuthToken();
  
  // Connect to WebSocket for notifications
  const { connectionState, lastMessage, sendMessage } = useWebSocket({
    url: user ? `${wsUrl}/ws/notifications/${user.id}/?token=${token}` : '',
    autoConnect: !!user, // Only connect if user is logged in
    reconnectOnUnmount: true, // Keep connection alive when component unmounts
    onOpen: () => {
      setError(null);
    },
    onClose: () => {
      setError('Connection to notification server lost.');
    },
    onError: () => {
      setError('Error connecting to notification server.');
    },
  });
  
  // Process incoming notifications
  useEffect(() => {
    if (lastMessage && (lastMessage.type || lastMessage.notification_type)) {
      dispatch(
        addNotification({
          id: lastMessage.id || Date.now().toString(),
          type: lastMessage.notification_type || lastMessage.type,
          message: lastMessage.message,
          data: lastMessage.data || {},
          timestamp: lastMessage.timestamp || new Date().toISOString(),
          isRead: false,
        })
      );
    }
  }, [lastMessage, dispatch]);
  
  // Mark notification as read
  const markAsRead = useCallback(
    (notificationId: string) => {
      // Update in Redux store
      dispatch(markNotificationRead(notificationId));
      
      // Send to server
      sendMessage({
        type: 'mark_read',
        notification_id: notificationId,
      });
    },
    [dispatch, sendMessage]
  );
  
  // Determine if connected
  const isConnected = connectionState === ConnectionState.OPEN;
  
  return {
    isConnected,
    markAsRead,
    error,
  };
};

export default useNotifications;