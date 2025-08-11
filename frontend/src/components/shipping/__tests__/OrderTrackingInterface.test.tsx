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

const mockShipment: Shipment = {
  id: '1',
  order: 'ORD123456',
  shipping_partner: 'partner1',
  shipping_partner_name: 'Shiprocket',
  tracking_number: 'TRK123456789',
  status: 'IN_TRANSIT',
  status_display: 'In Transit',
  shipping_address: {
    first_name: 'John',
    last_name: 'Doe',
    address_line_1: '123 Main Street',
    city: 'New Delhi',
    state: 'Delhi',
    postal_code: '110001',
    country: 'India'
  },
  weight: 1.5,
  dimensions: { length: 10, width: 8, height: 5 },
  shipping_cost: 150,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  tracking_updates: [
    {
      id: '1',
      shipment: '1',
      status: 'SHIPPED',
      status_display: 'Shipped',
      description: 'Package has been shipped',
      location: 'Delhi Hub',
      timestamp: '2024-01-01T10:00:00Z',
      created_at: '2024-01-01T10:00:00Z'
    }
  ]
};

describe('OrderTrackingInterface', () => {
  it('renders search interface by default', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText('Track Your Order')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('e.g., TRK123456789 or ORD123456')).toBeInTheDocument();
    expect(screen.getByText('Track')).toBeInTheDocument();
  });

  it('hides search interface when showSearch is false', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface showSearch={false} />
      </Provider>
    );

    expect(screen.queryByText('Track Your Order')).not.toBeInTheDocument();
  });

  it('handles search form submission', async () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    const searchInput = screen.getByPlaceholderText('e.g., TRK123456789 or ORD123456');
    const trackButton = screen.getByText('Track');

    fireEvent.change(searchInput, { target: { value: 'TRK123456789' } });
    fireEvent.click(trackButton);

    // The form should submit and trigger tracking
    expect(searchInput).toHaveValue('TRK123456789');
  });

  it('shows loading state', () => {
    const store = createMockStore({ loading: true });
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText('Tracking...')).toBeInTheDocument();
    expect(screen.getByText('Loading tracking information...')).toBeInTheDocument();
  });

  it('shows error state', () => {
    const store = createMockStore({ error: 'Tracking number not found' });
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText('Tracking number not found')).toBeInTheDocument();
  });

  it('displays shipment details when available', () => {
    const store = createMockStore({ currentShipment: mockShipment });
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText('Shipment Details')).toBeInTheDocument();
    expect(screen.getByText('TRK123456789')).toBeInTheDocument();
    expect(screen.getByText('Shiprocket')).toBeInTheDocument();
    expect(screen.getByText('₹150')).toBeInTheDocument();
    expect(screen.getAllByText('In Transit')).toHaveLength(2);
  });

  it('displays shipping address', () => {
    const store = createMockStore({ currentShipment: mockShipment });
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText('Delivery Address')).toBeInTheDocument();
    expect(screen.getByText(/123 Main Street.*New Delhi.*Delhi.*110001/)).toBeInTheDocument();
  });

  it('shows tracking timeline', () => {
    const store = createMockStore({ currentShipment: mockShipment });
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText('Tracking Timeline')).toBeInTheDocument();
  });

  it('pre-fills search with tracking number prop', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface trackingNumber="TRK987654321" />
      </Provider>
    );

    const searchInput = screen.getByPlaceholderText('e.g., TRK123456789 or ORD123456');
    expect(searchInput).toHaveValue('TRK987654321');
  });

  it('shows empty state when no tracking data', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText('Enter a tracking number or order ID to view shipment details')).toBeInTheDocument();
  });

  it('disables track button when input is empty', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    const trackButton = screen.getByText('Track');
    expect(trackButton).toBeDisabled();
  });

  it('enables track button when input has value', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    const searchInput = screen.getByPlaceholderText('e.g., TRK123456789 or ORD123456');
    const trackButton = screen.getByText('Track');

    fireEvent.change(searchInput, { target: { value: 'TRK123' } });
    
    expect(trackButton).not.toBeDisabled();
  });

  it('shows estimated delivery date when available', () => {
    const shipmentWithDeliveryDate = {
      ...mockShipment,
      estimated_delivery_date: '2024-01-05T00:00:00Z'
    };
    
    const store = createMockStore({ currentShipment: shipmentWithDeliveryDate });
    
    render(
      <Provider store={store}>
        <OrderTrackingInterface />
      </Provider>
    );

    expect(screen.getByText('Estimated Delivery:')).toBeInTheDocument();
    expect(screen.getByText('05/01/2024')).toBeInTheDocument();
  });

  it('shows delivery slot when available', () => {
    const shipmentWithSlot = {
      ...mockShipment,
      delivery_slot_display: 'Morning Slot (9:00 AM - 12:00 PM)'
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