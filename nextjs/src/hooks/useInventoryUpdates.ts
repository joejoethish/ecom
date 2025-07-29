import { useEffect, useState, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { RootState, useAppDispatch } from '@/store';
import { updateInventoryLevel } from '@/store/slices/inventorySlice';
import useWebSocket, { ConnectionState } from './useWebSocket';
import { getAuthToken } from '@/utils/auth';

interface InventoryAlert {
  productId: string;
  productName: string;
  currentStock: number;
  threshold: number;
  timestamp: string;
}

interface UseInventoryUpdatesReturn {
  isConnected: boolean;
  lowStockAlerts: InventoryAlert[];
  error: string | null;
}

/**
 * Custom hook for real-time inventory updates
 * @returns Inventory update state
 */
export const useInventoryUpdates = (): UseInventoryUpdatesReturn => {
  const [lowStockAlerts, setLowStockAlerts] = useState<InventoryAlert[]>([]);
  const [error, setError] = useState<string | null>(null);
  const dispatch = useAppDispatch();
  
  // Get current user from Redux store
  const user = useSelector((state: RootState) => state.auth.user);
  const isAdmin = user?.is_staff || user?.is_superuser;
  const isSeller = !!user?.seller_profile;
  
  // Get API URL from environment
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const wsUrl = apiUrl.replace(/^http/, 'ws');
  
  // Get auth token for WebSocket authentication
  const token = getAuthToken();
  
  // Connect to WebSocket for inventory updates (only for admin/seller)
  const { connectionState, lastMessage } = useWebSocket({
    url: (isAdmin || isSeller) ? `${wsUrl}/ws/inventory/updates/?token=${token}` : '',
    autoConnect: !!(isAdmin || isSeller), // Only connect if user is admin or seller
    reconnectOnUnmount: true, // Keep connection alive when component unmounts
    onOpen: () => {
      setError(null);
    },
    onClose: () => {
      setError('Connection to inventory update server lost.');
    },
    onError: () => {
      setError('Error connecting to inventory update server.');
    },
  });
  
  // Process inventory updates
  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.type === 'stock_change' && lastMessage.product_id) {
        // Update inventory in Redux store
        dispatch(
          updateInventoryLevel({
            productId: lastMessage.product_id,
            quantity: lastMessage.data?.current_quantity,
            updateType: 'stock_change',
            data: lastMessage.data || {},
            timestamp: lastMessage.timestamp,
          })
        );
      } else if (lastMessage.type === 'low_stock_alert' && lastMessage.product_id) {
        // Add to low stock alerts
        const alert: InventoryAlert = {
          productId: lastMessage.product_id,
          productName: lastMessage.product_name,
          currentStock: lastMessage.current_stock,
          threshold: lastMessage.threshold,
          timestamp: lastMessage.timestamp,
        };
        
        setLowStockAlerts((prevAlerts) => {
          // Check if alert already exists
          const exists = prevAlerts.some((a) => a.productId === alert.productId);
          if (exists) {
            // Update existing alert
            return prevAlerts.map((a) =>
              a.productId === alert.productId ? alert : a
            );
          } else {
            // Add new alert
            return [...prevAlerts, alert];
          }
        });
        
        // Also update inventory in Redux store
        dispatch(
          updateInventoryLevel({
            productId: lastMessage.product_id,
            quantity: lastMessage.current_stock,
            updateType: 'low_stock_alert',
            data: {
              product_name: lastMessage.product_name,
              threshold: lastMessage.threshold,
            },
            timestamp: lastMessage.timestamp,
          })
        );
      }
    }
  }, [lastMessage, dispatch]);
  
  // Determine if connected
  const isConnected = connectionState === ConnectionState.OPEN;
  
  return {
    isConnected,
    lowStockAlerts,
    error,
  };
};

export default useInventoryUpdates;