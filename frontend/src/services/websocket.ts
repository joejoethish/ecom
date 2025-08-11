/**
 * WebSocket service for real-time communication
 * Handles connection management, reconnection, and message handling
 */

import { store } from '@/store';
import { addNotification } from '@/store/slices/notificationSlice';
import { updateOrderStatus } from '@/store/slices/orderSlice';
import { updateInventoryLevel } from '@/store/slices/inventorySlice';
import { updateChatMessages } from '@/store/slices/chatSlice';

// WebSocket connection states
export enum ConnectionState {
  CONNECTING = 'connecting',
  OPEN = 'open',
  CLOSING = 'closing',
  CLOSED = 'closed',
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  [key: string]: unknown;
}

class WebSocketService {
  private socket: WebSocket | null = null;
  private url: string = '';
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectTimeout: number = 1000;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private connectionState: ConnectionState = ConnectionState.CLOSED;
  private messageHandlers: Map<string, ((message: unknown) => void)[]> = new Map();
  private connectionStateHandlers: ((state: ConnectionState) => void)[] = [];

  /**
   * Connect to a WebSocket endpoint
   * @param url WebSocket URL to connect to
   */
  public connect(url: string): void {
    if (this.socket && this.connectionState === ConnectionState.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    this.url = url;
    this.connectionState = ConnectionState.CONNECTING;
    this.notifyConnectionStateChange();

    try {
      this.socket = new WebSocket(url);
      this.setupEventHandlers();
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.handleConnectionFailure();
    }
  }

  /**
   * Disconnect from the WebSocket server
   */
  public disconnect(): void {
    if (!this.socket) return;

    this.connectionState = ConnectionState.CLOSING;
    this.notifyConnectionStateChange();

    try {
      this.socket.close();
    } catch (error) {
      console.error('Error closing WebSocket connection:', error);
    }

    this.socket = null;
    this.connectionState = ConnectionState.CLOSED;
    this.notifyConnectionStateChange();

    // Clear any reconnection timers
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Send a message through the WebSocket connection
   * @param message Message to send
   * @returns boolean indicating if the message was sent
   */
  public send(message: unknown): boolean {
    if (!this.socket || this.connectionState !== ConnectionState.OPEN) {
      console.error('Cannot send message, WebSocket is not connected');
      return false;
    }

    try {
      this.socket.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
      return false;
    }
  }

  /**
   * Register a handler for specific message types
   * @param messageType Type of message to handle
   * @param handler Function to call when message is received
   */
  public onMessage(messageType: string, handler: (message: unknown) => void): void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)?.push(handler);
  }

  /**
   * Remove a message handler
   * @param messageType Type of message
   * @param handler Handler to remove
   */
  public offMessage(messageType: string, handler: (message: unknown) => void): void {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index !== -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Register a handler for connection state changes
   * @param handler Function to call when connection state changes
   */
  public onConnectionStateChange(handler: (state: ConnectionState) => void): void {
    this.connectionStateHandlers.push(handler);
  }

  /**
   * Remove a connection state change handler
   * @param handler Handler to remove
   */
  public offConnectionStateChange(handler: (state: ConnectionState) => void): void {
    const index = this.connectionStateHandlers.indexOf(handler);
    if (index !== -1) {
      this.connectionStateHandlers.splice(index, 1);
    }
  }

  /**
   * Get the current connection state
   * @returns Current connection state
   */
  public getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  /**
   * Set up WebSocket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.onopen = () => {
      console.log('WebSocket connection established');
      this.connectionState = ConnectionState.OPEN;
      this.notifyConnectionStateChange();
      this.reconnectAttempts = 0;
    };

    this.socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        this.handleMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.socket.onclose = (event) => {
      console.log('WebSocket connection closed:', event.code, event.reason);
      this.connectionState = ConnectionState.CLOSED;
      this.notifyConnectionStateChange();
      this.handleConnectionFailure();
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  /**
   * Handle incoming WebSocket messages
   * @param message Parsed message from the server
   */
  private handleMessage(message: WebSocketMessage): void {
    // Dispatch to specific handlers based on message type
    const handlers = this.messageHandlers.get(message.type) || [];
    handlers.forEach((handler) => {
      try {
        handler(message);
      } catch (error) {
        console.error(`Error in message handler for type ${message.type}:`, error);
      }
    });

    // Also dispatch to Redux store based on message type
    this.dispatchToRedux(message);
  }

  /**
   * Dispatch WebSocket messages to Redux store
   * @param message WebSocket message
   */
  private dispatchToRedux(message: WebSocketMessage): void {
    switch (message.type) {
      case 'notification_message':
      case 'ORDER_UPDATE':
      case 'PAYMENT_CONFIRMATION':
      case 'PAYMENT_FAILED':
      case 'INVENTORY_ALERT':
        store.dispatch(
          addNotification({
            id: Date.now().toString(),
            type: message.notification_type || message.type,
            message: message.message,
            data: message.data || {},
            timestamp: message.timestamp || new Date().toISOString(),
            isRead: false,
          })
        );
        break;

      case 'status_update':
        if (message.data?.order_id) {
          store.dispatch(
            updateOrderStatus({
              orderId: message.data.order_id,
              status: message.status,
              message: message.message,
              trackingData: message.tracking_data || {},
              timestamp: message.timestamp,
            })
          );
        }
        break;

      case 'stock_change':
      case 'low_stock_alert':
        if (message.product_id) {
          store.dispatch(
            updateInventoryLevel({
              productId: message.product_id,
              quantity: message.data?.current_quantity || message.current_stock,
              updateType: message.update_type || message.type,
              data: message.data || {},
              timestamp: message.timestamp,
            })
          );
        }
        break;

      case 'chat_message':
        if (message.room_id) {
          store.dispatch(
            updateChatMessages({
              roomId: message.room_id,
              message: {
                id: message.id || Date.now().toString(),
                content: message.message,
                userId: message.user_id,
                timestamp: message.timestamp || new Date().toISOString(),
                isRead: false,
              },
            })
          );
        }
        break;

      default:
        // Unknown message type, log for debugging
        console.log('Unhandled WebSocket message type:', message.type, message);
    }
  }

  /**
   * Handle connection failures and attempt reconnection
   */
  private handleConnectionFailure(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Maximum reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectTimeout * Math.pow(1.5, this.reconnectAttempts - 1);
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
      this.connect(this.url);
    }, delay);
  }

  /**
   * Notify all connection state change handlers
   */
  private notifyConnectionStateChange(): void {
    this.connectionStateHandlers.forEach((handler) => {
      try {
        handler(this.connectionState);
      } catch (error) {
        console.error('Error in connection state change handler:', error);
      }
    });
  }
}

// Create singleton instance
export const websocketService = new WebSocketService();

export default websocketService;