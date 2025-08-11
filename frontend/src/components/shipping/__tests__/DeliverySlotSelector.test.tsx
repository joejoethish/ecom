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

  {
    id: &apos;1&apos;,
    name: &apos;Morning Slot&apos;,
    start_time: &apos;09:00&apos;,
    end_time: &apos;12:00&apos;,
    day_of_week: 1,
    day_of_week_display: &apos;Monday&apos;,
    additional_fee: 0,
    max_orders: 50,
    is_active: true,
    available_capacity: 25,
    created_at: &apos;2024-01-01T00:00:00Z&apos;,
    updated_at: &apos;2024-01-01T00:00:00Z&apos;
  },
  {
    id: &apos;2&apos;,
    name: &apos;Evening Slot&apos;,
    start_time: &apos;18:00&apos;,
    end_time: &apos;21:00&apos;,
    day_of_week: 1,
    day_of_week_display: &apos;Monday&apos;,
    additional_fee: 50,
    max_orders: 30,
    is_active: true,
    available_capacity: 15,
    created_at: &apos;2024-01-01T00:00:00Z&apos;,
    updated_at: &apos;2024-01-01T00:00:00Z&apos;
  }
];

describe(&apos;DeliverySlotSelector&apos;, () => {
  it(&apos;renders without pincode message when no pincode provided&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector />
      </Provider>
    );

    expect(screen.getByText(&apos;Please enter a pincode to view available delivery slots.&apos;)).toBeInTheDocument();
  });

  it(&apos;renders loading state&apos;, () => {
    const store = createMockStore({ loading: true });
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector pincode="110001" />
      </Provider>
    );

    expect(screen.getByText(&apos;Loading delivery slots...&apos;)).toBeInTheDocument();
  });

  it(&apos;renders error state&apos;, () => {
    const store = createMockStore({ error: &apos;Failed to load slots&apos; });
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector pincode="110001" />
      </Provider>
    );

    expect(screen.getByText(&apos;Error loading delivery slots: Failed to load slots&apos;)).toBeInTheDocument();
  });

  it(&apos;renders delivery slots when available&apos;, () => {
    const store = createMockStore({ deliverySlots: mockDeliverySlots });
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector pincode="110001" />
      </Provider>
    );

    expect(screen.getByText(&apos;Select Delivery Date&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Select Delivery Time&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Morning Slot&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Evening Slot&apos;)).toBeInTheDocument();
  });

  it(&apos;handles slot selection&apos;, async () => {
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

    const morningSlot = screen.getByText(&apos;Morning Slot&apos;).closest(&apos;div&apos;);
    if (morningSlot) {
      fireEvent.click(morningSlot);
    }

    await waitFor(() => {
      expect(mockOnSelect).toHaveBeenCalledWith(mockDeliverySlots[0]);
    });
  });

  it(&apos;shows additional fee for premium slots&apos;, () => {
    const store = createMockStore({ deliverySlots: mockDeliverySlots });
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector pincode="110001" />
      </Provider>
    );

    expect(screen.getByText(&apos;Free&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;+₹50&apos;)).toBeInTheDocument();
  });

  it(&apos;shows slot availability&apos;, () => {
    const store = createMockStore({ deliverySlots: mockDeliverySlots });
    
    render(
      <Provider store={store}>
        <DeliverySlotSelector pincode="110001" />
      </Provider>
    );

    expect(screen.getByText(&apos;25 slots left&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;15 slots left&apos;)).toBeInTheDocument();
  });

  it(&apos;disables unavailable slots&apos;, () => {
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

    const slotCard = screen.getByText(&apos;Morning Slot&apos;).closest(&apos;div&apos;);
    expect(slotCard).toHaveClass(&apos;opacity-50&apos;, &apos;cursor-not-allowed&apos;);
    expect(screen.getByText(&apos;Not available&apos;)).toBeInTheDocument();
  });

  it(&apos;shows selected slot state&apos;, () => {
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