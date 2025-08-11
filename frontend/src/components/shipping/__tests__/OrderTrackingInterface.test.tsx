import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import OrderTrackingInterface from '../OrderTrackingInterface';
import shippingReducer from '../../../store/slices/shippingSlice';
import { Shipment, ShipmentTracking } from '../../../types/shipping';

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

  id: &apos;1&apos;,
  order: &apos;ORD123456&apos;,
  shipping_partner: &apos;partner1&apos;,
  shipping_partner_name: &apos;Shiprocket&apos;,
  tracking_number: &apos;TRK123456789&apos;,
  status: &apos;IN_TRANSIT&apos;,
  status_display: &apos;In Transit&apos;,
  shipping_address: {
    first_name: &apos;John&apos;,
    last_name: &apos;Doe&apos;,
    address_line_1: &apos;123 Main Street&apos;,
    city: &apos;New Delhi&apos;,
    state: &apos;Delhi&apos;,
    postal_code: &apos;110001&apos;,
    country: &apos;India&apos;
  },
  weight: 1.5,
  dimensions: { length: 10, width: 8, height: 5 },
  shipping_cost: 150,
  created_at: &apos;2024-01-01T00:00:00Z&apos;,
  updated_at: &apos;2024-01-01T00:00:00Z&apos;,
  tracking_updates: [
    {
      id: &apos;1&apos;,
      shipment: &apos;1&apos;,
      status: &apos;SHIPPED&apos;,
      status_display: &apos;Shipped&apos;,
      description: &apos;Package has been shipped&apos;,
      location: &apos;Delhi Hub&apos;,
      timestamp: &apos;2024-01-01T10:00:00Z&apos;,
      created_at: &apos;2024-01-01T10:00:00Z&apos;
    }
  ]
};

describe(&apos;OrderTrackingInterface&apos;, () => {
  it(&apos;renders search interface by default&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText(&apos;Track Your Order&apos;)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(&apos;e.g., TRK123456789 or ORD123456&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Track&apos;)).toBeInTheDocument();
  });

  it(&apos;hides search interface when showSearch is false&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface showSearch={false} />
      </Provider>
    );

    expect(screen.queryByText(&apos;Track Your Order&apos;)).not.toBeInTheDocument();
  });

  it(&apos;handles search form submission&apos;, async () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    const searchInput = screen.getByPlaceholderText(&apos;e.g., TRK123456789 or ORD123456&apos;);
    const trackButton = screen.getByText(&apos;Track&apos;);

    fireEvent.change(searchInput, { target: { value: &apos;TRK123456789&apos; } });
    fireEvent.click(trackButton);

    // The form should submit and trigger tracking
    expect(searchInput).toHaveValue(&apos;TRK123456789&apos;);
  });

  it(&apos;shows loading state&apos;, () => {
    const store = createMockStore({ loading: true });
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText(&apos;Tracking...&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Loading tracking information...&apos;)).toBeInTheDocument();
  });

  it(&apos;shows error state&apos;, () => {
    const store = createMockStore({ error: &apos;Tracking number not found&apos; });
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText(&apos;Tracking number not found&apos;)).toBeInTheDocument();
  });

  it(&apos;displays shipment details when available&apos;, () => {
    const store = createMockStore({ currentShipment: mockShipment });
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText(&apos;Shipment Details&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;TRK123456789&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Shiprocket&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;₹150&apos;)).toBeInTheDocument();
    expect(screen.getAllByText(&apos;In Transit&apos;)).toHaveLength(2);
  });

  it(&apos;displays shipping address&apos;, () => {
    const store = createMockStore({ currentShipment: mockShipment });
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText(&apos;Delivery Address&apos;)).toBeInTheDocument();
    expect(screen.getByText(/123 Main Street.*New Delhi.*Delhi.*110001/)).toBeInTheDocument();
  });

  it(&apos;shows tracking timeline&apos;, () => {
    const store = createMockStore({ currentShipment: mockShipment });
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText(&apos;Tracking Timeline&apos;)).toBeInTheDocument();
  });

  it(&apos;pre-fills search with tracking number prop&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface trackingNumber="TRK987654321" />
      </Provider>
    );

    const searchInput = screen.getByPlaceholderText(&apos;e.g., TRK123456789 or ORD123456&apos;);
    expect(searchInput).toHaveValue(&apos;TRK987654321&apos;);
  });

  it(&apos;shows empty state when no tracking data&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText(&apos;Enter a tracking number or order ID to view shipment details&apos;)).toBeInTheDocument();
  });

  it(&apos;disables track button when input is empty&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    const trackButton = screen.getByText(&apos;Track&apos;);
    expect(trackButton).toBeDisabled();
  });

  it(&apos;enables track button when input has value&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    const searchInput = screen.getByPlaceholderText(&apos;e.g., TRK123456789 or ORD123456&apos;);
    const trackButton = screen.getByText(&apos;Track&apos;);

    fireEvent.change(searchInput, { target: { value: &apos;TRK123&apos; } });
    
    expect(trackButton).not.toBeDisabled();
  });

  it(&apos;shows estimated delivery date when available&apos;, () => {
    const shipmentWithDeliveryDate = {
      ...mockShipment,
      estimated_delivery_date: &apos;2024-01-05T00:00:00Z&apos;
    };
    
    const store = createMockStore({ currentShipment: shipmentWithDeliveryDate });
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText(&apos;Estimated Delivery:&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;05/01/2024&apos;)).toBeInTheDocument();
  });

  it(&apos;shows delivery slot when available&apos;, () => {
    const shipmentWithSlot = {
      ...mockShipment,
      delivery_slot_display: &apos;Morning Slot (9:00 AM - 12:00 PM)&apos;
    };
    
    const store = createMockStore({ currentShipment: shipmentWithSlot });
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText('Delivery Slot:')).toBeInTheDocument();
    expect(screen.getByText('Morning Slot (9:00 AM - 12:00 PM)')).toBeInTheDocument();
  });
});