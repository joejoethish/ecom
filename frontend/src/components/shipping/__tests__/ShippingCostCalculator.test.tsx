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

  {
    shipping_partner: {
      id: &apos;1&apos;,
      name: &apos;Shiprocket&apos;
    },
    rate: 150,
    min_delivery_days: 3,
    max_delivery_days: 5,
    is_dynamic_rate: true
  },
  {
    shipping_partner: {
      id: &apos;2&apos;,
      name: &apos;Delhivery&apos;
    },
    rate: 120,
    estimated_delivery_days: 4,
    is_dynamic_rate: false
  }
];

describe(&apos;ShippingCostCalculator&apos;, () => {
  it(&apos;renders calculator form&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    expect(screen.getByText(&apos;Calculate Shipping Cost&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(&apos;Source Pin Code&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(&apos;Destination Pin Code&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(&apos;Weight (kg)&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Calculate Rates&apos;)).toBeInTheDocument();
  });

  it(&apos;pre-fills form with provided props&apos;, () => {
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

    expect(screen.getByDisplayValue(&apos;110001&apos;)).toBeInTheDocument();
    expect(screen.getByDisplayValue(&apos;400001&apos;)).toBeInTheDocument();
    expect(screen.getByDisplayValue(&apos;2.5&apos;)).toBeInTheDocument();
  });

  it(&apos;shows advanced options when toggled&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    const advancedButton = screen.getByText(&apos;Advanced Options&apos;);
    fireEvent.click(advancedButton);

    expect(screen.getByText(&apos;Package Dimensions (cm)&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(&apos;Length&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(&apos;Width&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(&apos;Height&apos;)).toBeInTheDocument();
  });

  it(&apos;handles form input changes&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    const sourceInput = screen.getByLabelText(&apos;Source Pin Code&apos;);
    const destinationInput = screen.getByLabelText(&apos;Destination Pin Code&apos;);
    const weightInput = screen.getByLabelText(&apos;Weight (kg)&apos;);

    fireEvent.change(sourceInput, { target: { value: &apos;110001&apos; } });
    fireEvent.change(destinationInput, { target: { value: &apos;400001&apos; } });
    fireEvent.change(weightInput, { target: { value: &apos;1.5&apos; } });

    expect(sourceInput).toHaveValue(&apos;110001&apos;);
    expect(destinationInput).toHaveValue(&apos;400001&apos;);
    expect(weightInput).toHaveValue(1.5);
  });

  it(&apos;validates form before submission&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    const calculateButton = screen.getByText(&apos;Calculate Rates&apos;);
    expect(calculateButton).toBeDisabled();

    // Fill required fields
    fireEvent.change(screen.getByLabelText(&apos;Source Pin Code&apos;), { target: { value: &apos;110001&apos; } });
    fireEvent.change(screen.getByLabelText(&apos;Destination Pin Code&apos;), { target: { value: &apos;400001&apos; } });
    fireEvent.change(screen.getByLabelText(&apos;Weight (kg)&apos;), { target: { value: &apos;1.5&apos; } });

    expect(calculateButton).not.toBeDisabled();
  });

  it(&apos;shows loading state during calculation&apos;, () => {
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

    expect(screen.getByText(&apos;Calculating...&apos;)).toBeInTheDocument();
  });

  it(&apos;displays shipping rates when available&apos;, () => {
    const store = createMockStore({ shippingRates: mockShippingRates });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    expect(screen.getByText(&apos;Available Shipping Options&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Shiprocket&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Delhivery&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;₹150.00&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;₹120.00&apos;)).toBeInTheDocument();
  });

  it(&apos;shows delivery time estimates&apos;, () => {
    const store = createMockStore({ shippingRates: mockShippingRates });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    expect(screen.getByText(&apos;Delivery: 3-5 days&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Delivery: 4 days&apos;)).toBeInTheDocument();
  });

  it(&apos;shows live rate indicator&apos;, () => {
    const store = createMockStore({ shippingRates: mockShippingRates });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    expect(screen.getByText(&apos;Live Rate&apos;)).toBeInTheDocument();
  });

  it(&apos;handles rate selection&apos;, async () => {
    const mockOnRateSelect = jest.fn();
    const store = createMockStore({ shippingRates: mockShippingRates });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator onRateSelect={mockOnRateSelect} />
      </Provider>
    );

    const shiprocketOption = screen.getByText(&apos;Shiprocket&apos;).closest(&apos;div&apos;);
    if (shiprocketOption) {
      fireEvent.click(shiprocketOption);
    }

    await waitFor(() => {
      expect(mockOnRateSelect).toHaveBeenCalledWith(mockShippingRates[0]);
    });
  });

  it(&apos;shows selected rate details&apos;, () => {
    const store = createMockStore({ shippingRates: mockShippingRates });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    // Select a rate
    const shiprocketOption = screen.getByText(&apos;Shiprocket&apos;).closest(&apos;div&apos;);
    if (shiprocketOption) {
      fireEvent.click(shiprocketOption);
    }

    expect(screen.getByText(&apos;Selected Option:&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Shiprocket - ₹150.00&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Clear Selection&apos;)).toBeInTheDocument();
  });

  it(&apos;handles clear rates&apos;, () => {
    const store = createMockStore({ shippingRates: mockShippingRates });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    const clearButton = screen.getByText(&apos;Clear&apos;);
    fireEvent.click(clearButton);

    // This would trigger the clearShippingRates action
  });

  it(&apos;shows error state&apos;, () => {
    const store = createMockStore({ error: &apos;Failed to calculate rates&apos; });
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    expect(screen.getByText(&apos;Failed to calculate rates&apos;)).toBeInTheDocument();
  });

  it(&apos;handles dimension inputs in advanced mode&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <ShippingCostCalculator />
      </Provider>
    );

    // Open advanced options
    fireEvent.click(screen.getByText(&apos;Advanced Options&apos;));

    const lengthInput = screen.getByLabelText(&apos;Length&apos;);
    const widthInput = screen.getByLabelText(&apos;Width&apos;);
    const heightInput = screen.getByLabelText(&apos;Height&apos;);

    fireEvent.change(lengthInput, { target: { value: &apos;10&apos; } });
    fireEvent.change(widthInput, { target: { value: &apos;8&apos; } });
    fireEvent.change(heightInput, { target: { value: &apos;5&apos; } });

    expect(lengthInput).toHaveValue(10);
    expect(widthInput).toHaveValue(8);
    expect(heightInput).toHaveValue(5);
  });

  it(&apos;shows prompt to calculate when form is valid but no rates&apos;, () => {
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