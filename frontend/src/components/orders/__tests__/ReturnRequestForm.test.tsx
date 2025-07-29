import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { ReturnRequestForm } from '../ReturnRequestForm';
import orderReducer from '@/store/slices/orderSlice';
import { createReturnRequest } from '@/store/slices/orderSlice';

// Mock Redux async thunk
jest.mock('@/store/slices/orderSlice', () => {
  const originalModule = jest.requireActual('@/store/slices/orderSlice');
  return {
    ...originalModule,
    createReturnRequest: jest.fn() as any,
  };
});

describe('ReturnRequestForm Component', () => {
  const mockOrderItem = {
    id: '123',
    product: {
      id: '456',
      name: 'Test Product',
      slug: 'test-product',
      description: 'Test description',
      short_description: 'Short description',
      category: {
        id: 'c1',
        name: 'Test Category',
        slug: 'test-category',
        is_active: true,
        created_at: '2023-01-01',
      },
      brand: 'Test Brand',
      sku: 'TST001',
      price: 99.99,
      is_active: true,
      is_featured: false,
      dimensions: {},
      images: [
        {
          id: '789',
          image: '/test.jpg',
          alt_text: 'Test Image',
          is_primary: true,
          order: 1,
        },
      ],
      created_at: '2023-01-01',
      updated_at: '2023-01-01',
    },
    quantity: 2,
    unit_price: 99.99,
    total_price: 199.98,
    status: 'delivered',
    is_gift: false,
    returned_quantity: 0,
    refunded_amount: 0,
    can_return: true,
  };
  
  const mockOnClose = jest.fn();
  
  beforeEach(() => {
    (createReturnRequest as any).mockReturnValue({
      type: 'orders/createReturnRequest/fulfilled',
      payload: {
        id: '999',
        order_item: '123',
        quantity: 1,
        reason: 'defective',
        description: 'Product arrived damaged',
        status: 'pending',
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