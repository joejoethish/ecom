import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { useRouter } from 'next/navigation';
import { OrderHistory } from '../OrderHistory';
import orderReducer from '@/store/slices/orderSlice';
import { fetchOrders } from '@/store/slices/orderSlice';

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter: jest.fn(),
}));

// Mock Redux async thunk
jest.mock('@/store/slices/orderSlice', () => {
  const originalModule = jest.requireActual('@/store/slices/orderSlice');
  return {
    ...originalModule,
    fetchOrders: jest.fn() as any,
  };
});

describe('OrderHistory Component', () => {
  const mockRouter = {
    push: jest.fn(),
  };
  
  const mockOrders = [
    {
      id: '1',
      order_number: 'ORD-20230101-12345',
      status: 'DELIVERED',
      total_amount: 99.99,
      payment_status: 'COMPLETED',
      items: [{ id: '1', product: { name: 'Test Product' }, quantity: 1 }],
      created_at: '2023-01-01T12:00:00Z',
    },
    {
      id: '2',
      order_number: 'ORD-20230102-67890',
      status: 'PROCESSING',
      total_amount: 149.99,
      payment_status: 'COMPLETED',
      items: [{ id: '2', product: { name: 'Another Product' }, quantity: 2 }],
      created_at: '2023-01-02T12:00:00Z',
    },
  ];
  
  const mockPagination = {
    count: 2,
    next: null,
    previous: null,
    page_size: 10,
    total_pages: 1,
    current_page: 1,
  };
  
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (fetchOrders as any).mockReturnValue({
      type: 'orders/fetchOrders/fulfilled',
      payload: {
        results: mockOrders,
        pagination: mockPagination,
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
        <OrderHistory />
      </Provider>
    );
  };
  
  test('renders loading state initially', () => {
    renderComponent({ loading: true });
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
  
  test('renders error message when there is an error', () => {
    renderComponent({ error: 'Failed to fetch orders' });
    expect(screen.getByText(/Failed to fetch orders/i)).toBeInTheDocument();
    expect(screen.getByText(/Try Again/i)).toBeInTheDocument();
  });
  
  test('renders empty state when there are no orders', () => {
    renderComponent({ orders: [] });
    expect(screen.getByText(/You haven't placed any orders yet/i)).toBeInTheDocument();
    expect(screen.getByText(/Start Shopping/i)).toBeInTheDocument();
  });
  
  test('renders order list when orders are available', () => {
    renderComponent({ orders: mockOrders, pagination: mockPagination });
    
    expect(screen.getByText('Order History')).toBeInTheDocument();
    expect(screen.getByText('ORD-20230101-12345')).toBeInTheDocument();
    expect(screen.getByText('ORD-20230102-67890')).toBeInTheDocument();
    expect(screen.getByText('DELIVERED')).toBeInTheDocument();
    expect(screen.getByText('PROCESSING')).toBeInTheDocument();
  });
  
  test('navigates to order details when view button is clicked', () => {
    renderComponent({ orders: mockOrders, pagination: mockPagination });
    
    const viewButtons = screen.getAllByText(/View Order Details/i);
    fireEvent.click(viewButtons[0]);
    
    expect(mockRouter.push).toHaveBeenCalledWith('/orders/1');
  });
  
  test('handles pagination correctly', () => {
    renderComponent({
      orders: mockOrders,
      pagination: {
        ...mockPagination,
        total_pages: 3,
        current_page: 2,
      },
    });
    
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);
    
    expect(fetchOrders).toHaveBeenCalledWith(3);
  });
});