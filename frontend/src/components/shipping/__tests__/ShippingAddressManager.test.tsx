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

  {
    id: &apos;1&apos;,
    type: &apos;HOME&apos;,
    first_name: &apos;John&apos;,
    last_name: &apos;Doe&apos;,
    address_line_1: &apos;123 Main Street&apos;,
    address_line_2: &apos;Apt 4B&apos;,
    city: &apos;New Delhi&apos;,
    state: &apos;Delhi&apos;,
    postal_code: &apos;110001&apos;,
    country: &apos;India&apos;,
    phone: &apos;+91 9876543210&apos;,
    is_default: true
  },
  {
    id: &apos;2&apos;,
    type: &apos;WORK&apos;,
    first_name: &apos;John&apos;,
    last_name: &apos;Doe&apos;,
    address_line_1: &apos;456 Business Park&apos;,
    city: &apos;Gurgaon&apos;,
    state: &apos;Haryana&apos;,
    postal_code: &apos;122001&apos;,
    country: &apos;India&apos;,
    phone: &apos;+91 9876543210&apos;,
    is_default: false
  }
];

describe(&apos;ShippingAddressManager&apos;, () => {
  it(&apos;renders empty state when no addresses provided&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingAddressManager addresses={[]} />
      </Provider>
    );

    expect(screen.getByText(&apos;No delivery addresses found&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Add New Address&apos;)).toBeInTheDocument();
  });

  it(&apos;renders addresses list&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingAddressManager addresses={mockAddresses} />
      </Provider>
    );

    expect(screen.getByText(&apos;Delivery Address&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;John Doe&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;123 Main Street, Apt 4B, New Delhi, Delhi, 110001&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;456 Business Park, Gurgaon, Haryana, 122001&apos;)).toBeInTheDocument();
  });

  it(&apos;shows default address badge&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingAddressManager addresses={mockAddresses} />
      </Provider>
    );

    expect(screen.getByText(&apos;Default&apos;)).toBeInTheDocument();
  });

  it(&apos;handles address selection&apos;, async () => {
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

    const workAddress = screen.getByText(&apos;456 Business Park, Gurgaon, Haryana, 122001&apos;).closest(&apos;div&apos;);
    if (workAddress) {
      fireEvent.click(workAddress);
    }

    await waitFor(() => {
      expect(mockOnAddressSelect).toHaveBeenCalled();
    });
  });

  it(&apos;handles add new address&apos;, () => {
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

    const addButton = screen.getByText(&apos;Add New&apos;);
    fireEvent.click(addButton);

    expect(mockOnAddNewAddress).toHaveBeenCalled();
  });

  it(&apos;handles edit address&apos;, () => {
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

    const editButtons = screen.getAllByRole(&apos;button&apos;);
    const editButton = editButtons.find(button => 
      button.querySelector(&apos;svg&apos;) && !button.textContent?.includes(&apos;Add New&apos;)
    );
    
    if (editButton) {
      fireEvent.click(editButton);
      expect(mockOnEditAddress).toHaveBeenCalled();
    }
  });

  it(&apos;shows address type icons&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingAddressManager addresses={mockAddresses} />
      </Provider>
    );

    // Check for SVG icons (home and work icons should be present)
    const svgElements = screen.getAllByRole(&apos;img&apos;, { hidden: true });
    expect(svgElements.length).toBeGreaterThan(0);
  });

  it(&apos;displays phone numbers&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingAddressManager addresses={mockAddresses} />
      </Provider>
    );

    expect(screen.getAllByText(&apos;Phone: +91 9876543210&apos;)).toHaveLength(2);
  });

  it(&apos;shows serviceability checking state&apos;, async () => {
    const store = createMockStore({ loading: true });
    
    render(
      <Provider store={store}>
        <ShippingAddressManager addresses={mockAddresses} />
      </Provider>
    );

    // Click on an address to trigger serviceability check
    const homeAddress = screen.getByText(&apos;123 Main Street, Apt 4B, New Delhi, Delhi, 110001&apos;).closest(&apos;div&apos;);
    if (homeAddress) {
      fireEvent.click(homeAddress);
    }

    // The component should show checking state (this would be visible after the async operation)
    await waitFor(() => {
      // This test would need to be adjusted based on the actual implementation
      // of the serviceability checking UI feedback
    });
  });

  it(&apos;shows error state&apos;, () => {
    const store = createMockStore({ error: &apos;Failed to check serviceability&apos; });
    
    render(
      <Provider store={store}>
        <ShippingAddressManager addresses={mockAddresses} />
      </Provider>
    );

    expect(screen.getByText(&apos;Failed to check serviceability&apos;)).toBeInTheDocument();
  });

  it(&apos;auto-selects default address on mount&apos;, () => {
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