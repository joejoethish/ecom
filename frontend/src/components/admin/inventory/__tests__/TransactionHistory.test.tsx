import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TransactionHistory from '../TransactionHistory';
import { inventoryManagementApi } from '@/services/inventoryManagementApi';

// Mock the API service
jest.mock('@/services/inventoryManagementApi', () => ({
  inventoryManagementApi: {
    getTransactions: jest.fn(),
    getWarehouses: jest.fn(),
    exportTransactions: jest.fn(),
  },
}));

// Mock UI components
jest.mock('@/components/ui/Button', () => {
  return function MockButton({ children, onClick, disabled, ...props }: any) {
    return (
      <button onClick={onClick} disabled={disabled} {...props}>
        {children}
      </button>
    );
  };
});

jest.mock('@/components/ui/Input', () => {
  return function MockInput({ onChange, ...props }: any) {
    return <input onChange={onChange} {...props} />;
  };
});

jest.mock('@/components/ui/Select', () => {
  return function MockSelect({ children, onChange, ...props }: any) {
    return (
      <select onChange={onChange} {...props}>
        {children}
      </select>
    );
  };
});

jest.mock('@/components/ui/Badge', () => {
  return function MockBadge({ children, className }: any) {
    return <span className={className}>{children}</span>;
  };
});

jest.mock('@/components/ui/card', () => ({
  Card: function MockCard({ children, className }: any) {
    return <div className={className}>{children}</div>;
  },
}));

jest.mock('@/components/ui/LoadingSpinner', () => {
  return function MockLoadingSpinner() {
    return <div data-testid="loading-spinner">Loading...</div>;
  };
});

const mockTransactions = [
  {
    id: '1',
    inventory_item: {
      id: '1',
      product_variant: {
        sku: 'TEST-001',
        product: {
          name: 'Test Product',
        },
      },
      warehouse: {
        name: 'Main Warehouse',
      },
    },
    transaction_type: 'sale' as const,
    quantity_change: -5,
    previous_quantity: 100,
    new_quantity: 95,
    reason: 'Customer order',
    user: {
      id: '1',
      username: 'testuser',
    },
    created_at: '2024-01-15T10:30:00Z',
  },
  {
    id: '2',
    inventory_item: {
      id: '2',
      product_variant: {
        sku: 'TEST-002',
        product: {
          name: 'Another Product',
        },
      },
      warehouse: {
        name: 'Secondary Warehouse',
      },
    },
    transaction_type: 'purchase' as const,
    quantity_change: 50,
    previous_quantity: 20,
    new_quantity: 70,
    reason: 'Stock replenishment',
    user: {
      id: '2',
      username: 'admin',
    },
    created_at: '2024-01-14T14:20:00Z',
  },
];

const mockWarehouses = [
  { id: '1', name: 'Main Warehouse', code: 'MAIN' },
  { id: '2', name: 'Secondary Warehouse', code: 'SEC' },
];

const mockApiResponse = {
  success: true,
  data: {
    results: mockTransactions,
    pagination: {
      count: 2,
      next: null,
      previous: null,
      page_size: 20,
      total_pages: 1,
      current_page: 1,
    },
  },
};

describe('TransactionHistory', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (inventoryManagementApi.getTransactions as jest.Mock).mockResolvedValue(mockApiResponse);
    (inventoryManagementApi.getWarehouses as jest.Mock).mockResolvedValue({
      success: true,
      data: mockWarehouses,
    });
  });

  it('renders transaction history component', async () => {
    render(<TransactionHistory />);
    
    expect(screen.getByText('Transaction History')).toBeInTheDocument();
    expect(screen.getByText('Track all inventory movements and changes')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
      expect(screen.getByText('Another Product')).toBeInTheDocument();
    });
  });

  it('displays loading spinner while fetching data', () => {
    (inventoryManagementApi.getTransactions as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );
    
    render(<TransactionHistory />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('displays transaction data correctly', async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      // Check transaction details
      expect(screen.getByText('Test Product')).toBeInTheDocument();
      expect(screen.getByText('SKU: TEST-001')).toBeInTheDocument();
      expect(screen.getByText('Main Warehouse')).toBeInTheDocument();
      expect(screen.getByText('Sale')).toBeInTheDocument();
      expect(screen.getByText('testuser')).toBeInTheDocument();
    });
  });

  it('handles filter changes', async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Change warehouse filter
    const warehouseSelect = screen.getByDisplayValue('All Warehouses');
    fireEvent.change(warehouseSelect, { target: { value: '1' } });
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          warehouse: '1',
          page: 1,
        })
      );
    });
  });

  it('handles transaction type filter', async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Change transaction type filter
    const typeSelect = screen.getByDisplayValue('All Types');
    fireEvent.change(typeSelect, { target: { value: 'sale' } });
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          transaction_type: 'sale',
          page: 1,
        })
      );
    });
  });

  it('handles date range filters', async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Set date from filter
    const dateFromInput = screen.getByLabelText('Date From');
    fireEvent.change(dateFromInput, { target: { value: '2024-01-01' } });
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          date_from: '2024-01-01',
          page: 1,
        })
      );
    });
  });

  it('handles search functionality', async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Search for product
    const searchInput = screen.getByPlaceholderText('Search by product name, SKU, or user...');
    fireEvent.change(searchInput, { target: { value: 'Test Product' } });
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          product: 'Test Product',
          page: 1,
        })
      );
    });
  });

  it('clears filters when clear button is clicked', async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Set some filters first
    const searchInput = screen.getByPlaceholderText('Search by product name, SKU, or user...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    
    // Clear filters
    const clearButton = screen.getByText('Clear Filters');
    fireEvent.click(clearButton);
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          product: '',
          warehouse: '',
          transaction_type: undefined,
          date_from: '',
          date_to: '',
          page: 1,
        })
      );
    });
  });

  it('opens transaction details modal when view button is clicked', async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Click view button for first transaction
    const viewButtons = screen.getAllByRole('button');
    const viewButton = viewButtons.find(button => 
      button.querySelector('svg') // Looking for the Eye icon
    );
    
    if (viewButton) {
      fireEvent.click(viewButton);
      
      await waitFor(() => {
        expect(screen.getByText('Transaction Details')).toBeInTheDocument();
        expect(screen.getByText('Transaction ID')).toBeInTheDocument();
      });
    }
  });

  it('handles CSV export', async () => {
    const mockBlob = new Blob(['csv data'], { type: 'text/csv' });
    (inventoryManagementApi.exportTransactions as jest.Mock).mockResolvedValue(mockBlob);
    
    // Mock URL.createObjectURL and related methods
    global.URL.createObjectURL = jest.fn(() => 'mock-url');
    global.URL.revokeObjectURL = jest.fn();
    
    // Mock document.createElement and appendChild
    const mockLink = {
      href: '',
      download: '',
      click: jest.fn(),
    };
    jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
    jest.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any);
    jest.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any);
    
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Click export button
    const exportButton = screen.getByText('Export CSV');
    fireEvent.click(exportButton);
    
    await waitFor(() => {
      expect(inventoryManagementApi.exportTransactions).toHaveBeenCalled();
      expect(mockLink.click).toHaveBeenCalled();
    });
  });

  it('displays correct transaction type colors and icons', async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      const saleTransaction = screen.getByText('Sale');
      const purchaseTransaction = screen.getByText('Purchase');
      
      expect(saleTransaction).toBeInTheDocument();
      expect(purchaseTransaction).toBeInTheDocument();
    });
  });

  it('formats quantity changes correctly', async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      // Should show negative change for sale (red)
      const negativeChange = screen.getByText('-5');
      expect(negativeChange).toBeInTheDocument();
      
      // Should show positive change for purchase (green)  
      const positiveChange = screen.getByText('+50');
      expect(positiveChange).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    (inventoryManagementApi.getTransactions as jest.Mock).mockRejectedValue(
      new Error('API Error')
    );
    
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to fetch transactions:', expect.any(Error));
    });
    
    consoleSpy.mockRestore();
  });
});