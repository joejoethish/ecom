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
jest.mock(&apos;@/store/slices/orderSlice&apos;, () => {
  const originalModule = jest.requireActual(&apos;@/store/slices/orderSlice&apos;);
  return {
    ...originalModule,
    fetchOrders: jest.fn() as any,
  };
});

describe(&apos;OrderHistory Component&apos;, () => {
  const mockRouter = {
    push: jest.fn(),
  };
  
  const mockOrders = [
    {
      id: &apos;1&apos;,
      order_number: &apos;ORD-20230101-12345&apos;,
      status: &apos;DELIVERED&apos;,
      total_amount: 99.99,
      payment_status: &apos;COMPLETED&apos;,
      items: [{ id: &apos;1&apos;, product: { name: &apos;Test Product&apos; }, quantity: 1 }],
      created_at: &apos;2023-01-01T12:00:00Z&apos;,
    },
    {
      id: &apos;2&apos;,
      order_number: &apos;ORD-20230102-67890&apos;,
      status: &apos;PROCESSING&apos;,
      total_amount: 149.99,
      payment_status: &apos;COMPLETED&apos;,
      items: [{ id: &apos;2&apos;, product: { name: &apos;Another Product&apos; }, quantity: 2 }],
      created_at: &apos;2023-01-02T12:00:00Z&apos;,
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
      type: &apos;orders/fetchOrders/fulfilled&apos;,
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