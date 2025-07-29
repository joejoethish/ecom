import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import ShippingCostCalculator from '../ShippingCostCalculator';
import shippingReducer from '../../../store/slices/shippingSlice';
import { ShippingRateResult } from '../../../types/shipping';

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

const mockShippingRates: ShippingRateResult[] = [
  {
    shipping_partner: {
      id: '1',
      name: 'Shiprocket'
    },
    rate: 150,
    min_delivery_days: 3,
    max_delivery_days: 5,
    is_dynamic_rate: true
  },
  {
    shipping_partner: {
      id: '2',
      name: 'Delhivery'
    },
    rate: 120,
    estimated_delivery_days: 4,
    is_dynamic_rate: false
  }
];

describe('ShippingCostCalculator', () => {
  it('renders calculator form', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    expect(screen.getByText('Calculate Shipping Cost')).toBeInTheDocument();
    expect(screen.getByLabelText('Source Pin Code')).toBeInTheDocument();
    expect(screen.getByLabelText('Destination Pin Code')).toBeInTheDocument();
    expect(screen.getByLabelText('Weight (kg)')).toBeInTheDocument();
    expect(screen.getByText('Calculate Rates')).toBeInTheDocument();
  });

  it('pre-fills form with provided props', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator 
          sourcePinCode="110001"
          destinationPinCode="400001"
          weight={2.5}
        />
      </Provider>
    );

    expect(screen.getByDisplayValue('110001')).toBeInTheDocument();
    expect(screen.getByDisplayValue('400001')).toBeInTheDocument();
    expect(screen.getByDisplayValue('2.5')).toBeInTheDocument();
  });

  it('shows advanced options when toggled', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    const advancedButton = screen.getByText('Advanced Options');
    fireEvent.click(advancedButton);

    expect(screen.getByText('Package Dimensions (cm)')).toBeInTheDocument();
    expect(screen.getByLabelText('Length')).toBeInTheDocument();
    expect(screen.getByLabelText('Width')).toBeInTheDocument();
    expect(screen.getByLabelText('Height')).toBeInTheDocument();
  });

  it('handles form input changes', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    const sourceInput = screen.getByLabelText('Source Pin Code');
    const destinationInput = screen.getByLabelText('Destination Pin Code');
    const weightInput = screen.getByLabelText('Weight (kg)');

    fireEvent.change(sourceInput, { target: { value: '110001' } });
    fireEvent.change(destinationInput, { target: { value: '400001' } });
    fireEvent.change(weightInput, { target: { value: '1.5' } });

    expect(sourceInput).toHaveValue('110001');
    expect(destinationInput).toHaveValue('400001');
    expect(weightInput).toHaveValue(1.5);
  });

  it('validates form before submission', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    const calculateButton = screen.getByText('Calculate Rates');
    expect(calculateButton).toBeDisabled();

    // Fill required fields
    fireEvent.change(screen.getByLabelText('Source Pin Code'), { target: { value: '110001' } });
    fireEvent.change(screen.getByLabelText('Destination Pin Code'), { target: { value: '400001' } });
    fireEvent.change(screen.getByLabelText('Weight (kg)'), { target: { value: '1.5' } });

    expect(calculateButton).not.toBeDisabled();
  });

  it('shows loading state during calculation', () => {
    const store = createMockStore({ loading: true });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator 
          sourcePinCode="110001"
          destinationPinCode="400001"
          weight={1.5}
        />
      </Provider>
    );

    expect(screen.getByText('Calculating...')).toBeInTheDocument();
  });

  it('displays shipping rates when available', () => {
    const store = createMockStore({ shippingRates: mockShippingRates });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    expect(screen.getByText('Available Shipping Options')).toBeInTheDocument();
    expect(screen.getByText('Shiprocket')).toBeInTheDocument();
    expect(screen.getByText('Delhivery')).toBeInTheDocument();
    expect(screen.getByText('₹150.00')).toBeInTheDocument();
    expect(screen.getByText('₹120.00')).toBeInTheDocument();
  });

  it('shows delivery time estimates', () => {
    const store = createMockStore({ shippingRates: mockShippingRates });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    expect(screen.getByText('Delivery: 3-5 days')).toBeInTheDocument();
    expect(screen.getByText('Delivery: 4 days')).toBeInTheDocument();
  });

  it('shows live rate indicator', () => {
    const store = createMockStore({ shippingRates: mockShippingRates });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    expect(screen.getByText('Live Rate')).toBeInTheDocument();
  });

  it('handles rate selection', async () => {
    const mockOnRateSelect = jest.fn();
    const store = createMockStore({ shippingRates: mockShippingRates });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator onRateSelect={mockOnRateSelect} />
      </Provider>
    );

    const shiprocketOption = screen.getByText('Shiprocket').closest('div');
    if (shiprocketOption) {
      fireEvent.click(shiprocketOption);
    }

    await waitFor(() => {
      expect(mockOnRateSelect).toHaveBeenCalledWith(mockShippingRates[0]);
    });
  });

  it('shows selected rate details', () => {
    const store = createMockStore({ shippingRates: mockShippingRates });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    // Select a rate
    const shiprocketOption = screen.getByText('Shiprocket').closest('div');
    if (shiprocketOption) {
      fireEvent.click(shiprocketOption);
    }

    expect(screen.getByText('Selected Option:')).toBeInTheDocument();
    expect(screen.getByText('Shiprocket - ₹150.00')).toBeInTheDocument();
    expect(screen.getByText('Clear Selection')).toBeInTheDocument();
  });

  it('handles clear rates', () => {
    const store = createMockStore({ shippingRates: mockShippingRates });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    const clearButton = screen.getByText('Clear');
    fireEvent.click(clearButton);

    // This would trigger the clearShippingRates action
  });

  it('shows error state', () => {
    const store = createMockStore({ error: 'Failed to calculate rates' });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    expect(screen.getByText('Failed to calculate rates')).toBeInTheDocument();
  });

  it('handles dimension inputs in advanced mode', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    // Open advanced options
    fireEvent.click(screen.getByText('Advanced Options'));

    const lengthInput = screen.getByLabelText('Length');
    const widthInput = screen.getByLabelText('Width');
    const heightInput = screen.getByLabelText('Height');

    fireEvent.change(lengthInput, { target: { value: '10' } });
    fireEvent.change(widthInput, { target: { value: '8' } });
    fireEvent.change(heightInput, { target: { value: '5' } });

    expect(lengthInput).toHaveValue(10);
    expect(widthInput).toHaveValue(8);
    expect(heightInput).toHaveValue(5);
  });

  it('shows prompt to calculate when form is valid but no rates', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator 
          sourcePinCode="110001"
          destinationPinCode="400001"
          weight={1.5}
        />
      </Provider>
    );

    expect(screen.getByText('Click "Calculate Rates" to see available shipping options')).toBeInTheDocument();
  });
});