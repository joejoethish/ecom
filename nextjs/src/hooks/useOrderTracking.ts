import { useEffect, useState, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import useWebSocket, { ConnectionState } from './useWebSocket';
import { getAuthToken } from '@/utils/auth';

interface OrderTrackingEvent {
  status: string;
  message: string;
  location?: string;
  timestamp: string;
}

interface UseOrderTrackingReturn {
  isConnected: boolean;
  trackingEvents: OrderTrackingEvent[];
  currentStatus: string;
  isLoading: boolean;
  error: string | null;
}

/**
 * Custom hook for real-time order tracking
 * @param orderId Order ID to track
 * @returns Order tracking state
 */
export const useOrderTracking = (orderId: string): UseOrderTrackingReturn => {
  const [trackingEvents, setTrackingEvents] = useState<OrderTrackingEvent[]>([]);
  const [currentStatus, setCurrentStatus] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Get API URL from environment
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const wsUrl = apiUrl.replace(/^http/, 'ws');
  
  // Get auth token for WebSocket authentication
  const token = getAuthToken();
  
  // Connect to WebSocket for order tracking
  const { connectionState, lastMessage } = useWebSocket({
    url: `${wsUrl}/ws/orders/tracking/${orderId}/?token=${token}`,
    autoConnect: true,
    reconnectOnUnmount: false,
    onOpen: () => {
      setError(null);
    },
    onClose: () => {
      setError('Connection to order tracking server lost. Please refresh the page.');
    },
    onError: () => {
      setError('Error connecting to order tracking server.');
    },
  });
  
  // Process initial status message
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'initial_status') {
      setIsLoading(false);
      setCurrentStatus(lastMessage.order.status);
      
      if (lastMessage.order.tracking_events && Array.isArray(lastMessage.order.tracking_events)) {
        setTrackingEvents(lastMessage.order.tracking_events);
      }
    }
  }, [lastMessage]);
  
  // Process status update messages
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'status_update') {
      setCurrentStatus(lastMessage.status);
      
      // Add new tracking event to the list
      if (lastMessage.tracking_data) {
        setTrackingEvents((prevEvents) => [
          {
            status: lastMessage.status,
            message: lastMessage.message,
            location: lastMessage.tracking_data.location,
            timestamp: lastMessage.tracking_data.timestamp,
          },
          ...prevEvents,
        ]);
      }
    }
  }, [lastMessage]);
  
  // Determine if connected
  const isConnected = connectionState === ConnectionState.OPEN;
  
  return {
    isConnected,
    trackingEvents,
    currentStatus,
    isLoading,
    error,
  };
};

export default useOrderTracking;