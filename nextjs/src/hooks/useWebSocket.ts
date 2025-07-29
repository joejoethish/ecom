import { useEffect, useState, useCallback, useRef } from 'react';
import websocketService, { ConnectionState, WebSocketMessage } from '@/services/websocket';

export { ConnectionState };

interface UseWebSocketOptions {
  url: string;
  autoConnect?: boolean;
  reconnectOnUnmount?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
}

interface UseWebSocketReturn {
  connectionState: ConnectionState;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: any) => boolean;
  connect: () => void;
  disconnect: () => void;
}

/**
 * Custom hook for using WebSockets in React components
 * @param options WebSocket connection options
 * @returns WebSocket state and methods
 */
export const useWebSocket = ({
  url,
  autoConnect = true,
  reconnectOnUnmount = false,
  onOpen,
  onClose,
  onError,
}: UseWebSocketOptions): UseWebSocketReturn => {
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    websocketService.getConnectionState()
  );
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const messageHandlerRef = useRef<((message: WebSocketMessage) => void) | null>(null);
  const connectionStateHandlerRef = useRef<((state: ConnectionState) => void) | null>(null);

  // Connection state change handler
  const handleConnectionStateChange = useCallback((state: ConnectionState) => {
    setConnectionState(state);
    
    if (state === ConnectionState.OPEN && onOpen) {
      onOpen();
    } else if (state === ConnectionState.CLOSED && onClose) {
      onClose();
    }
  }, [onOpen, onClose]);

  // Message handler
  const handleMessage = useCallback((message: WebSocketMessage) => {
    setLastMessage(message);
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    websocketService.connect(url);
  }, [url]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  // Send message through WebSocket
  const sendMessage = useCallback((message: any): boolean => {
    return websocketService.send(message);
  }, []);

  // Set up event handlers and connect if autoConnect is true
  useEffect(() => {
    // Store handlers in refs to avoid recreating them on each render
    messageHandlerRef.current = handleMessage;
    connectionStateHandlerRef.current = handleConnectionStateChange;

    // Register handlers
    websocketService.onConnectionStateChange(handleConnectionStateChange);
    websocketService.onMessage('*', handleMessage);

    // Connect if autoConnect is true
    if (autoConnect) {
      connect();
    }

    // Clean up on unmount
    return () => {
      websocketService.offConnectionStateChange(handleConnectionStateChange);
      websocketService.offMessage('*', handleMessage);
      
      // Disconnect if reconnectOnUnmount is false
      if (!reconnectOnUnmount) {
        disconnect();
      }
    };
  }, [autoConnect, connect, disconnect, handleConnectionStateChange, handleMessage, reconnectOnUnmount]);

  return {
    connectionState,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
  };
};

export default useWebSocket;