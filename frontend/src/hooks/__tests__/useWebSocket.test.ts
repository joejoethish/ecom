import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';
import websocketService, { ConnectionState } from '@/services/websocket';

// Mock the websocket service
jest.mock('@/services/websocket', () => ({
  __esModule: true,
  ConnectionState: {
    CONNECTING: 'connecting',
    OPEN: 'open',
    CLOSING: 'closing',
    CLOSED: 'closed',
  },
  default: {
    connect: jest.fn(),
    disconnect: jest.fn(),
    send: jest.fn(),
    getConnectionState: jest.fn(),
    onConnectionStateChange: jest.fn(),
    offConnectionStateChange: jest.fn(),
    onMessage: jest.fn(),
    offMessage: jest.fn(),
  },
}));

describe('useWebSocket', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (websocketService.getConnectionState as jest.Mock).mockReturnValue(ConnectionState.CLOSED);
  });

  it('should connect to WebSocket when autoConnect is true', () => {
    const url = 'ws://localhost:8000/ws/test/';
    renderHook(() => useWebSocket({ url, autoConnect: true }));
    
    expect(websocketService.connect).toHaveBeenCalledWith(url);
  });

  it('should not connect to WebSocket when autoConnect is false', () => {
    const url = 'ws://localhost:8000/ws/test/';
    renderHook(() => useWebSocket({ url, autoConnect: false }));
    
    expect(websocketService.connect).not.toHaveBeenCalled();
  });

  it('should disconnect from WebSocket on unmount when reconnectOnUnmount is false', () => {
    const url = 'ws://localhost:8000/ws/test/';
    const { unmount } = renderHook(() => useWebSocket({ url, reconnectOnUnmount: false }));
    
    unmount();
    
    expect(websocketService.disconnect).toHaveBeenCalled();
  });

  it('should not disconnect from WebSocket on unmount when reconnectOnUnmount is true', () => {
    const url = 'ws://localhost:8000/ws/test/';
    const { unmount } = renderHook(() => useWebSocket({ url, reconnectOnUnmount: true }));
    
    unmount();
    
    expect(websocketService.disconnect).not.toHaveBeenCalled();
  });

  it('should register and unregister connection state handler', () => {
    const url = 'ws://localhost:8000/ws/test/';
    const { unmount } = renderHook(() => useWebSocket({ url }));
    
    expect(websocketService.onConnectionStateChange).toHaveBeenCalled();
    
    unmount();
    
    expect(websocketService.offConnectionStateChange).toHaveBeenCalled();
  });

  it('should register and unregister message handler', () => {
    const url = 'ws://localhost:8000/ws/test/';
    const { unmount } = renderHook(() => useWebSocket({ url }));
    
    expect(websocketService.onMessage).toHaveBeenCalled();
    
    unmount();
    
    expect(websocketService.offMessage).toHaveBeenCalled();
  });

  it('should call onOpen when connection state changes to OPEN', () => {
    const onOpen = jest.fn();
    const url = 'ws://localhost:8000/ws/test/';
    
    renderHook(() => useWebSocket({ url, onOpen }));
    
    // Get the connection state handler
    const connectionStateHandler = (websocketService.onConnectionStateChange as jest.Mock).mock.calls[0][0];
    
    // Simulate connection state change to OPEN
    act(() => {
      connectionStateHandler(ConnectionState.OPEN);
    });
    
    expect(onOpen).toHaveBeenCalled();
  });

  it('should call onClose when connection state changes to CLOSED', () => {
    const onClose = jest.fn();
    const url = 'ws://localhost:8000/ws/test/';
    
    renderHook(() => useWebSocket({ url, onClose }));
    
    // Get the connection state handler
    const connectionStateHandler = (websocketService.onConnectionStateChange as jest.Mock).mock.calls[0][0];
    
    // Simulate connection state change to CLOSED
    act(() => {
      connectionStateHandler(ConnectionState.CLOSED);
    });
    
    expect(onClose).toHaveBeenCalled();
  });

  it('should send message through WebSocket service', () => {
    const url = 'ws://localhost:8000/ws/test/';
    (websocketService.send as jest.Mock).mockReturnValue(true);
    
    const { result } = renderHook(() => useWebSocket({ url }));
    
    const message = { type: 'test', data: 'test data' };
    const success = result.current.sendMessage(message);
    
    expect(websocketService.send).toHaveBeenCalledWith(message);
    expect(success).toBe(true);
  });
});