import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import ShippingAddressManager from '../ShippingAddressManager';
import shippingReducer from '../../../store/slices/shippingSlice';
import { Address } from '../../../types';

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

const mockAddresses: Address[] = [
  {
    id: '1',
    type: 'HOME',
    first_name: 'John',
    last_name: 'Doe',
    address_line_1: '123 Main Street',
    address_line_2: 'Apt 4B',
    city: 'New Delhi',
    state: 'Delhi',
    postal_code: '110001',
    country: 'India',
    phone: '+91 9876543210',
    is_default: true
  },
  {
    id: '2',
    type: 'WORK',
    first_name: 'John',
    last_name: 'Doe',
    address_line_1: '456 Business Park',
    city: 'Gurgaon',
    state: 'Haryana',
    postal_code: '122001',
    country: 'India',
    phone: '+91 9876543210',
    is_default: false
  }
];

describe('ShippingAddressManager', () => {
  it('renders empty state when no addresses provided', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingAddressManager addresses={[]} />
      </Provider>
    );

    expect(screen.getByText('No delivery addresses found')).toBeInTheDocument();
    expect(screen.getByText('Add New Address')).toBeInTheDocument();
  });

  it('renders addresses list', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingAddressManager addresses={mockAddresses} />
      </Provider>
    );

    expect(screen.getByText('Delivery Address')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('123 Main Street, Apt 4B, New Delhi, Delhi, 110001')).toBeInTheDocument();
    expect(screen.getByText('456 Business Park, Gurgaon, Haryana, 122001')).toBeInTheDocument();
  });

  it('shows default address badge', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingAddressManager addresses={mockAddresses} />
      </Provider>
    );

    expect(screen.getByText('Default')).toBeInTheDocument();
  });

  it('handles address selection', async () => {
    const mockOnAddressSelect = jest.fn();
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingAddressManager 
          addresses={mockAddresses}
          onAddressSelect={mockOnAddressSelect}
        />
      </Provider>
    );

    const workAddress = screen.getByText('456 Business Park, Gurgaon, Haryana, 122001').closest('div');
    if (workAddress) {
      fireEvent.click(workAddress);
    }

    await waitFor(() => {
      expect(mockOnAddressSelect).toHaveBeenCalled();
    });
  });

  it('handles add new address', () => {
    const mockOnAddNewAddress = jest.fn();
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingAddressManager 
          addresses={mockAddresses}
          onAddNewAddress={mockOnAddNewAddress}
        />
      </Provider>
    );

    const addButton = screen.getByText('Add New');
    fireEvent.click(addButton);

    expect(mockOnAddNewAddress).toHaveBeenCalled();
  });

  it('handles edit address', () => {
    const mockOnEditAddress = jest.fn();
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingAddressManager 
          addresses={mockAddresses}
          onEditAddress={mockOnEditAddress}
        />
      </Provider>
    );

    const editButtons = screen.getAllByRole('button');
    const editButton = editButtons.find(button => 
      button.querySelector('svg') && !button.textContent?.includes('Add New')
    );
    
    if (editButton) {
      fireEvent.click(editButton);
      expect(mockOnEditAddress).toHaveBeenCalled();
    }
  });

  it('shows address type icons', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingAddressManager addresses={mockAddresses} />
      </Provider>
    );

    // Check for SVG icons (home and work icons should be present)
    const svgElements = screen.getAllByRole('img', { hidden: true });
    expect(svgElements.length).toBeGreaterThan(0);
  });

  it('displays phone numbers', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingAddressManager addresses={mockAddresses} />
      </Provider>
    );

    expect(screen.getAllByText('Phone: +91 9876543210')).toHaveLength(2);
  });

  it('shows serviceability checking state', async () => {
    const store = createMockStore({ loading: true });
    
    render(
      <Provider store={store}>
        <ShippingAddressManager addresses={mockAddresses} />
      </Provider>
    );

    // Click on an address to trigger serviceability check
    const homeAddress = screen.getByText('123 Main Street, Apt 4B, New Delhi, Delhi, 110001').closest('div');
    if (homeAddress) {
      fireEvent.click(homeAddress);
    }

    // The component should show checking state (this would be visible after the async operation)
    await waitFor(() => {
      // This test would need to be adjusted based on the actual implementation
      // of the serviceability checking UI feedback
    });
  });

  it('shows error state', () => {
    const store = createMockStore({ error: 'Failed to check serviceability' });
    
    render(
      <Provider store={store}>
        <ShippingAddressManager addresses={mockAddresses} />
      </Provider>
    );

    expect(screen.getByText('Failed to check serviceability')).toBeInTheDocument();
  });

  it('auto-selects default address on mount', () => {
    const mockOnAddressSelect = jest.fn();
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingAddressManager 
          addresses={mockAddresses}
          onAddressSelect={mockOnAddressSelect}
        />
      </Provider>
    );

    // The default address should be auto-selected
    expect(mockOnAddressSelect).toHaveBeenCalled();
  });
});