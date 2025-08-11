import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { WebSocketProvider, useWebSocketContext } from '../WebSocketProvider';
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
    getConnectionState: jest.fn(),
    onConnectionStateChange: jest.fn(),
    offConnectionStateChange: jest.fn(),
  },
}));

// Mock the auth utility
jest.mock('@/utils/auth', () => ({
  getAuthToken: jest.fn().mockReturnValue('mock-token'),
}));

// Create a mock Redux store
const mockStore = configureStore([]);

// Test component that uses the WebSocket context
const TestComponent = () => {
  const { isConnected, connectionState, lastError } = useWebSocketContext();
  return (
    <div>
      <div data-testid="connection-state">{connectionState}</div>
      <div data-testid="is-connected">{isConnected.toString()}</div>
      <div data-testid="last-error">{lastError || 'no error'}</div>
    </div>
  );
};

describe('WebSocketProvider', () => {
  let store: any;
  
  beforeEach(() => {
    jest.clearAllMocks();
    (websocketService.getConnectionState as jest.Mock).mockReturnValue(ConnectionState.CLOSED);
    
    // Create a fresh store for each test
    store = mockStore({
      auth: {
        user: {
          id: '123',
          username: 'testuser',
        },
      },
    });
  });
  
  it('should render children and provide WebSocket context', () => {
    render(
      <Provider store={store}>
        <WebSocketProvider>
          <TestComponent />
        </WebSocketProvider>
      </Provider>
    );
    
    expect(screen.getByTestId('connection-state')).toHaveTextContent('closed');
    expect(screen.getByTestId('is-connected')).toHaveTextContent('false');
    expect(screen.getByTestId('last-error')).toHaveTextContent('no error');
  });
  
  it('should connect to WebSocket when user is authenticated', () => {
    render(
      <Provider store={store}>
        <WebSocketProvider>
          <div>Test</div>
        </WebSocketProvider>
      </Provider>
    );
    
    expect(websocketService.connect).toHaveBeenCalledWith(
      expect.stringContaining('/ws/notifications/123/?token=mock-token')
    );
  });
  
  it('should not connect to WebSocket when user is not authenticated', () => {
    const unauthenticatedStore = mockStore({
      auth: {
        user: null,
      },
    });
    
    render(
      <Provider store={unauthenticatedStore}>
        <WebSocketProvider>
          <div>Test</div>
        </WebSocketProvider>
      </Provider>
    );
    
    expect(websocketService.connect).not.toHaveBeenCalled();
  });
  
  it('should disconnect from WebSocket when component unmounts', () => {
    const { unmount } = render(
      <Provider store={store}>
        <WebSocketProvider>
          <div>Test</div>
        </WebSocketProvider>
      </Provider>
    );
    
    unmount();
    
    // Should unregister the connection state handler
    expect(websocketService.offConnectionStateChange).toHaveBeenCalled();
  });
  
  it('should update connection state when WebSocket connection changes', () => {
    render(
      <Provider store={store}>
        <WebSocketProvider>
          <TestComponent />
        </WebSocketProvider>
      </Provider>
    );
    
    // Get the connection state handler
    const connectionStateHandler = (websocketService.onConnectionStateChange as jest.Mock).mock.calls[0][0];
    
    // Simulate connection state change to OPEN
    act(() => {
      connectionStateHandler(ConnectionState.OPEN);
    });
    
    expect(screen.getByTestId('connection-state')).toHaveTextContent('open');
    expect(screen.getByTestId('is-connected')).toHaveTextContent('true');
    
    // Simulate connection state change to CLOSED
    act(() => {
      connectionStateHandler(ConnectionState.CLOSED);
    });
    
    expect(screen.getByTestId('connection-state')).toHaveTextContent('closed');
    expect(screen.getByTestId('is-connected')).toHaveTextContent('false');
    expect(screen.getByTestId('last-error')).toHaveTextContent('WebSocket connection closed');
  });
});

// Helper function to simulate React act
function act(callback: () => void) {
  callback();
}