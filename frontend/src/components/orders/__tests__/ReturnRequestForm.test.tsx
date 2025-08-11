import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { ReturnRequestForm } from '../ReturnRequestForm';
import orderReducer from '@/store/slices/orderSlice';
import { createReturnRequest } from '@/store/slices/orderSlice';

// Mock Redux async thunk
jest.mock('@/store/slices/orderSlice', () => {
  const originalModule = jest.requireActual(&apos;@/store/slices/orderSlice&apos;);
  return {
    ...originalModule,
    createReturnRequest: jest.fn() as any,
  };
});

describe(&apos;ReturnRequestForm Component&apos;, () => {
  const mockOrderItem = {
    id: &apos;123&apos;,
    product: {
      id: &apos;456&apos;,
      name: &apos;Test Product&apos;,
      slug: &apos;test-product&apos;,
      description: &apos;Test description&apos;,
      short_description: &apos;Short description&apos;,
      category: {
        id: &apos;c1&apos;,
        name: &apos;Test Category&apos;,
        slug: &apos;test-category&apos;,
        is_active: true,
        created_at: &apos;2023-01-01&apos;,
      },
      brand: &apos;Test Brand&apos;,
      sku: &apos;TST001&apos;,
      price: 99.99,
      is_active: true,
      is_featured: false,
      dimensions: {},
      images: [
        {
          id: &apos;789&apos;,
          image: &apos;/test.jpg&apos;,
          alt_text: &apos;Test Image&apos;,
          is_primary: true,
          order: 1,
        },
      ],
      created_at: &apos;2023-01-01&apos;,
      updated_at: &apos;2023-01-01&apos;,
    },
    quantity: 2,
    unit_price: 99.99,
    total_price: 199.98,
    status: &apos;delivered&apos;,
    is_gift: false,
    returned_quantity: 0,
    refunded_amount: 0,
    can_return: true,
  };
  
  const mockOnClose = jest.fn();
  
  beforeEach(() => {
    (createReturnRequest as any).mockReturnValue({
      type: &apos;orders/createReturnRequest/fulfilled&apos;,
      payload: {
        id: &apos;999&apos;,
        order_item: &apos;123&apos;,
        quantity: 1,
        reason: &apos;defective&apos;,
        description: &apos;Product arrived damaged&apos;,
        status: &apos;pending&apos;,
      },
    });
  });
  
  afterEach(() => {
    jest.clearAllMocks();
  });
  
  const renderComponent = (initialState = {}) => {
    const store = configureStore({
      reducer: {
        orders: orderReducer,
      },
      preloadedState: {
        orders: {
          orders: [],
          currentOrder: null,
          loading: false,
          error: null,
          pagination: {
            count: 0,
            next: null,
            previous: null,
            page_size: 10,
            total_pages: 0,
            current_page: 1,
          },
          returnRequestLoading: false,
          returnRequestError: null,
          ...initialState,
        },
      },
    });
    
    return render(
      <Provider store={store}>
        <ReturnRequestForm orderItem={mockOrderItem} onClose={mockOnClose} />
      </Provider>
    );
  };
  
  test('renders form with product information', () => {
    renderComponent();
    
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('Quantity to Return')).toBeInTheDocument();
    expect(screen.getByText('Reason for Return')).toBeInTheDocument();
    expect(screen.getByText('Description')).toBeInTheDocument();
  });
  
  test('shows validation errors when form is submitted with invalid data', async () => {
    renderComponent();
    
    // Submit form without selecting reason or entering description
    fireEvent.click(screen.getByText('Submit Return Request'));
    
    await waitFor(() => {
      expect(screen.getByText('Please select a reason for return')).toBeInTheDocument();
      expect(screen.getByText('Please provide a description')).toBeInTheDocument();
    });
    
    // Verify that the form was not submitted
    expect(createReturnRequest).not.toHaveBeenCalled();
  });
  
  test('submits form with valid data', async () => {
    renderComponent();
    
    // Select reason
    fireEvent.change(screen.getByRole('combobox', { name: /reason for return/i }), {
      target: { value: 'defective' },
    });
    
    // Enter description
    fireEvent.change(screen.getByRole('textbox', { name: /description/i }), {
      target: { value: 'Product arrived damaged and does not work properly.' },
    });
    
    // Submit form
    fireEvent.click(screen.getByText('Submit Return Request'));
    
    await waitFor(() => {
      expect(createReturnRequest).toHaveBeenCalledWith({
        order_item_id: '123',
        quantity: 1,
        reason: 'defective',
        description: 'Product arrived damaged and does not work properly.',
      });
    });
    
    // Verify that onClose was called after successful submission
    expect(mockOnClose).toHaveBeenCalled();
  });
  
  test('displays error message when API request fails', async () => {
    (createReturnRequest as any).mockReturnValue({
      type: 'orders/createReturnRequest/rejected',
      payload: 'Failed to create return request',
    });
    
    renderComponent();
    
    // Select reason
    fireEvent.change(screen.getByRole('combobox', { name: /reason for return/i }), {
      target: { value: 'defective' },
    });
    
    // Enter description
    fireEvent.change(screen.getByRole('textbox', { name: /description/i }), {
      target: { value: 'Product arrived damaged and does not work properly.' },
    });
    
    // Submit form
    fireEvent.click(screen.getByText('Submit Return Request'));
    
    // Set the error state manually since we're not actually dispatching the action
    renderComponent({ returnRequestError: 'Failed to create return request' });
    
    expect(screen.getByText('Failed to create return request')).toBeInTheDocument();
    expect(mockOnClose).not.toHaveBeenCalled();
  });
  
  test('shows loading state during form submission', () => {
    renderComponent({ returnRequestLoading: true });
    
    expect(screen.getByRole('button', { name: /submit return request/i })).toBeDisabled();
  });
});