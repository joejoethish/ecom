import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import OrdersPage from '../page';
import { apiClient } from '@/utils/api';
import { toast } from 'react-hot-toast';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  useParams: () => ({}),
}));

// Mock next/link
jest.mock('next/link', () => {
  return function MockLink({ children, href, ...props }: any) {
    return <a href={href} {...props}>{children}</a>;
  };
});

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock API client
jest.mock('@/utils/api', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const mockOrdersData = {
  results: [
    {
      id: 'order-1',
      order_number: 'ORD-001',
      status: 'delivered',
      payment_status: 'paid',
      total_amount: 199.99,
      items: [
        {
          id: 'item-1',
          product: {
            id: 'prod-1',
            name: 'Test Product',
          },
          quantity: 2,
        },
      ],
      tracking_number: 'TRK123456',
      estimated_delivery_date: '2023-01-15T00:00:00Z',
      actual_delivery_date: '2023-01-14T00:00:00Z',
      has_invoice: true,
      can_cancel: false,
      can_return: true,
      created_at: '2023-01-01T00:00:00Z',
    },
    {
      id: 'order-2',
      order_number: 'ORD-002',
      status: 'pending',
      payment_status: 'pending',
      total_amount: 99.99,
      items: [
        {
          id: 'item-2',
          product: {
            id: 'prod-2',
            name: 'Another Product',
          },
          quantity: 1,
        },
      ],
      tracking_number: null,
      estimated_delivery_date: null,
      has_invoice: false,
      can_cancel: true,
      can_return: false,
      created_at: '2023-01-10T00:00:00Z',
    },
  ],
};

describe('OrdersPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (apiClient.get as jest.Mock).mockResolvedValue({
      success: true,
      data: mockOrdersData,
    });
  });

  it('renders orders page with data', async () => {
    render(<OrdersPage />);
    
    await waitFor(() => {
      expect(screen.getByText('My Orders')).toBeInTheDocument();
      expect(screen.getByText('Order #ORD-001')).toBeInTheDocument();
      expect(screen.getByText('Order #ORD-002')).toBeInTheDocument();
    });
  });

  it('displays order information correctly', async () => {
    render(<OrdersPage />);
    
    await waitFor(() => {
      expect(screen.getByText('$199.99')).toBeInTheDocument();
      expect(screen.getByText('$99.99')).toBeInTheDocument();
      expect(screen.getByText('Delivered')).toBeInTheDocument();
      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(screen.getByText('2 items')).toBeInTheDocument();
      expect(screen.getByText('1 item')).toBeInTheDocument();
    });
  });

  it('handles search functionality', async () => {
    render(<OrdersPage />);
    
    await waitFor(() => {
      expect(screen.getByText('My Orders')).toBeInTheDocument();
    });
    
    const searchInput = screen.getByPlaceholderText(
      'Search by order number or tracking number...'
    );
    const searchButton = screen.getByRole('button', { name: /search/i });
    
    fireEvent.change(searchInput, { target: { value: 'ORD-001' } });
    fireEvent.click(searchButton);
    
    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('search=ORD-001')
      );
    });
  });

  it('renders empty state when no orders', async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({
      success: true,
      data: { results: [] },
    });
    
    render(<OrdersPage />);
    
    await waitFor(() => {
      expect(screen.getByText('No orders found')).toBeInTheDocument();
      expect(screen.getByText("You haven't placed any orders yet")).toBeInTheDocument();
      expect(screen.getByText('Start Shopping')).toBeInTheDocument();
    });
  });

  it('renders loading state', () => {
    (apiClient.get as jest.Mock).mockImplementation(() => 
      new Promise(() => {}) // Never resolves
    );
    
    render(<OrdersPage />);
    
    // Should render skeleton loaders
    expect(document.querySelectorAll('.animate-pulse')).toHaveLength(5);
  });

  it('handles API error', async () => {
    (apiClient.get as jest.Mock).mockRejectedValue(
      new Error('Failed to load orders')
    );
    
    render(<OrdersPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Error Loading Orders')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });
    
    expect(toast.error).toHaveBeenCalledWith('Failed to load orders');
  });
});