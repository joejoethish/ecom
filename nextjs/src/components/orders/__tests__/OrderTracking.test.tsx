import React from 'react';
import { render, screen } from '@testing-library/react';
import OrderTracking from '../OrderTracking';
import { OrderTracking as OrderTrackingType } from '@/types';

describe('OrderTracking Component', () => {
  const mockEvents: OrderTrackingType[] = [
    {
      id: '1',
      status: 'pending',
      description: 'Order placed successfully',
      created_at: '2023-01-01T10:00:00Z',
    },
    {
      id: '2',
      status: 'confirmed',
      description: 'Order confirmed',
      created_at: '2023-01-01T11:00:00Z',
    },
    {
      id: '3',
      status: 'processing',
      description: 'Order is being processed',
      created_at: '2023-01-01T12:00:00Z',
    },
    {
      id: '4',
      status: 'shipped',
      description: 'Order has been shipped',
      location: 'Warehouse A',
      created_by: 'John Doe',
      created_at: '2023-01-02T10:00:00Z',
    },
  ];

  test('renders loading state initially', () => {
    // Mock the hook to return loading state
    jest.mock('@/hooks/useOrderTracking', () => ({
      useOrderTracking: () => ({
        isConnected: false,
        trackingEvents: [],
        currentStatus: null,
        isLoading: true,
        error: null,
      }),
    }));
    
    render(<OrderTracking orderId="test-order-id" />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  test('renders error state when there is an error', () => {
    // Mock the hook to return error state
    jest.mock('@/hooks/useOrderTracking', () => ({
      useOrderTracking: () => ({
        isConnected: false,
        trackingEvents: [],
        currentStatus: null,
        isLoading: false,
        error: 'Failed to load tracking information',
      }),
    }));
    
    render(<OrderTracking orderId="test-order-id" />);
    expect(screen.getByText(/Failed to load tracking information/i)).toBeInTheDocument();
  });

  test('renders tracking events when available', () => {
    // Mock the hook to return tracking events
    jest.mock('@/hooks/useOrderTracking', () => ({
      useOrderTracking: () => ({
        isConnected: true,
        trackingEvents: mockEvents,
        currentStatus: 'shipped',
        isLoading: false,
        error: null,
      }),
    }));
    
    render(<OrderTracking orderId="test-order-id" />);
    // This test would need to be adjusted based on the actual component implementation
    expect(screen.getByText(/tracking/i)).toBeInTheDocument();
  });
});