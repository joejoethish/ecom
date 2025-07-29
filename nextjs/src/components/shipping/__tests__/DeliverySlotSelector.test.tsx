import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import DeliverySlotSelector from '../DeliverySlotSelector';
import shippingReducer from '../../../store/slices/shippingSlice';
import { DeliverySlot } from '../../../types/shipping';

// Mock store
const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      shipping: shippingReducer
    },
    preloadedState: {
      shipping: {
        partners: [],
        serviceableAreas: [],
        deliverySlots: [],
        shipments: [],
        currentShipment: null,
        shippingRates: [],
        selectedDeliverySlot: null,
        selectedShippingAddress: null,
        loading: false,
        error: null,
        ...initialState
      }
    }
  });
};

const mockDeliverySlots: DeliverySlot[] = [
  {
    id: '1',
    name: 'Morning Slot',
    start_time: '09:00',
    end_time: '12:00',
    day_of_week: 1,
    day_of_week_display: 'Monday',
    additional_fee: 0,
    max_orders: 50,
    is_active: true,
    available_capacity: 25,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: '2',
    name: 'Evening Slot',
    start_time: '18:00',
    end_time: '21:00',
    day_of_week: 1,
    day_of_week_display: 'Monday',
    additional_fee: 50,
    max_orders: 30,
    is_active: true,
    available_capacity: 15,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
];

describe('DeliverySlotSelector', () => {
  it('renders without pincode message when no pincode provided', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector />
      </Provider>
    );

    expect(screen.getByText('Please enter a pincode to view available delivery slots.')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    const store = createMockStore({ loading: true });
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector pincode="110001" />
      </Provider>
    );

    expect(screen.getByText('Loading delivery slots...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    const store = createMockStore({ error: 'Failed to load slots' });
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector pincode="110001" />
      </Provider>
    );

    expect(screen.getByText('Error loading delivery slots: Failed to load slots')).toBeInTheDocument();
  });

  it('renders delivery slots when available', () => {
    const store = createMockStore({ deliverySlots: mockDeliverySlots });
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector pincode="110001" />
      </Provider>
    );

    expect(screen.getByText('Select Delivery Date')).toBeInTheDocument();
    expect(screen.getByText('Select Delivery Time')).toBeInTheDocument();
    expect(screen.getByText('Morning Slot')).toBeInTheDocument();
    expect(screen.getByText('Evening Slot')).toBeInTheDocument();
  });

  it('handles slot selection', async () => {
    const mockOnSelect = jest.fn();
    const store = createMockStore({ deliverySlots: mockDeliverySlots });
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector 
          pincode="110001" 
          onSelect={mockOnSelect}
        />
      </Provider>
    );

    const morningSlot = screen.getByText('Morning Slot').closest('div');
    if (morningSlot) {
      fireEvent.click(morningSlot);
    }

    await waitFor(() => {
      expect(mockOnSelect).toHaveBeenCalledWith(mockDeliverySlots[0]);
    });
  });

  it('shows additional fee for premium slots', () => {
    const store = createMockStore({ deliverySlots: mockDeliverySlots });
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector pincode="110001" />
      </Provider>
    );

    expect(screen.getByText('Free')).toBeInTheDocument();
    expect(screen.getByText('+₹50')).toBeInTheDocument();
  });

  it('shows slot availability', () => {
    const store = createMockStore({ deliverySlots: mockDeliverySlots });
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector pincode="110001" />
      </Provider>
    );

    expect(screen.getByText('25 slots left')).toBeInTheDocument();
    expect(screen.getByText('15 slots left')).toBeInTheDocument();
  });

  it('disables unavailable slots', () => {
    const unavailableSlots = [
      {
        ...mockDeliverySlots[0],
        is_active: false,
        available_capacity: 0
      }
    ];
    
    const store = createMockStore({ deliverySlots: unavailableSlots });
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector pincode="110001" />
      </Provider>
    );

    const slotCard = screen.getByText('Morning Slot').closest('div');
    expect(slotCard).toHaveClass('opacity-50', 'cursor-not-allowed');
    expect(screen.getByText('Not available')).toBeInTheDocument();
  });

  it('shows selected slot state', () => {
    const selectedSlot = mockDeliverySlots[0];
    const store = createMockStore({ 
      deliverySlots: mockDeliverySlots,
      selectedDeliverySlot: selectedSlot
    });
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector pincode="110001" />
      </Provider>
    );

    const selectedCard = screen.getByText('Morning Slot').closest('div');
    expect(selectedCard).toHaveClass('border-2', 'border-blue-500', 'bg-blue-50');
    expect(screen.getByText('Selected')).toBeInTheDocument();
  });
});