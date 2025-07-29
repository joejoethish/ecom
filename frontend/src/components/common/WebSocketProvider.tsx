import React, { createContext, useContext, useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import websocketService, { ConnectionState } from '@/services/websocket';
import { getAuthToken } from '@/utils/auth';

interface WebSocketContextType {
  isConnected: boolean;
  connectionState: ConnectionState;
  lastError: string | null;
}

const WebSocketContext = createContext<WebSocketContextType>({
  isConnected: false,
  connectionState: ConnectionState.CLOSED,
  lastError: null,
});

export const useWebSocketContext = () => useContext(WebSocketContext);

interface WebSocketProviderProps {
  children: React.ReactNode;
}

/**
 * Provider component for WebSocket connections
 * Manages global WebSocket state and connections
 */
export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    websocketService.getConnectionState()
  );
  const [lastError, setLastError] = useState<string | null>(null);
  
  // Get user from Redux store
  const user = useSelector((state: RootState) => state.auth.user);
  const isAuthenticated = !!user;
  
  // Get API URL from environment
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const wsUrl = apiUrl.replace(/^http/, 'ws');
  
  // Connect to notification WebSocket when user is authenticated
  useEffect(() => {
    if (isAuthenticated && user?.id) {
      const token = getAuthToken();
      const notificationUrl = `${wsUrl}/ws/notifications/${user.id}/?token=${token}`;
      
      // Register connection state handler
      const handleConnectionStateChange = (state: ConnectionState) => {
        setConnectionState(state);
        
        if (state === ConnectionState.CLOSED) {
          setLastError('WebSocket connection closed');
        } else if (state === ConnectionState.OPEN) {
          setLastError(null);
        }
      };
      
      websocketService.onConnectionStateChange(handleConnectionStateChange);
      
      // Connect to WebSocket
      websocketService.connect(notificationUrl);
      
      // Clean up on unmount
      return () => {
        websocketService.offConnectionStateChange(handleConnectionStateChange);
      };
    } else {
      // Disconnect if user is not authenticated
      websocketService.disconnect();
    }
  }, [isAuthenticated, user?.id, wsUrl]);
  
  const isConnected = connectionState === ConnectionState.OPEN;
  
  const contextValue: WebSocketContextType = {
    isConnected,
    connectionState,
    lastError,
  };
  
  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
};

export default WebSocketProvider;