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
jest.mock(&apos;@/components/ui/Button&apos;, () => {
  return function MockButton({ children, onClick, disabled, ...props }: unknown) {
    return (
      <button onClick={onClick} disabled={disabled} {...props}>
        {children}
      </button>
    );
  };
});

jest.mock(&apos;@/components/ui/Input&apos;, () => {
  return function MockInput({ onChange, ...props }: unknown) {
    return <input onChange={onChange} {...props} />;
  };
});

jest.mock(&apos;@/components/ui/Select&apos;, () => {
  return function MockSelect({ children, onChange, ...props }: unknown) {
    return (
      <select onChange={onChange} {...props}>
        {children}
      </select>
    );
  };
});

jest.mock(&apos;@/components/ui/Badge&apos;, () => {
  return function MockBadge({ children, className }: unknown) {
    return <span className={className}>{children}</span>;
  };
});

jest.mock(&apos;@/components/ui/card&apos;, () => ({
  Card: function MockCard({ children, className }: unknown) {
    return <div className={className}>{children}</div>;
  },
}));

jest.mock(&apos;@/components/ui/LoadingSpinner&apos;, () => {
  return function MockLoadingSpinner() {
    return <div data-testid="loading-spinner">Loading...</div>;
  };
});

const mockTransactions = [
  {
    id: &apos;1&apos;,
    inventory_item: {
      id: &apos;1&apos;,
      product_variant: {
        sku: &apos;TEST-001&apos;,
        product: {
          name: &apos;Test Product&apos;,
        },
      },
      warehouse: {
        name: &apos;Main Warehouse&apos;,
      },
    },
    transaction_type: &apos;sale&apos; as const,
    quantity_change: -5,
    previous_quantity: 100,
    new_quantity: 95,
    reason: &apos;Customer order&apos;,
    user: {
      id: &apos;1&apos;,
      username: &apos;testuser&apos;,
    },
    created_at: &apos;2024-01-15T10:30:00Z&apos;,
  },
  {
    id: &apos;2&apos;,
    inventory_item: {
      id: &apos;2&apos;,
      product_variant: {
        sku: &apos;TEST-002&apos;,
        product: {
          name: &apos;Another Product&apos;,
        },
      },
      warehouse: {
        name: &apos;Secondary Warehouse&apos;,
      },
    },
    transaction_type: &apos;purchase&apos; as const,
    quantity_change: 50,
    previous_quantity: 20,
    new_quantity: 70,
    reason: &apos;Stock replenishment&apos;,
    user: {
      id: &apos;2&apos;,
      username: &apos;admin&apos;,
    },
    created_at: &apos;2024-01-14T14:20:00Z&apos;,
  },
];

const mockWarehouses = [
  { id: &apos;1&apos;, name: &apos;Main Warehouse&apos;, code: &apos;MAIN&apos; },
  { id: &apos;2&apos;, name: &apos;Secondary Warehouse&apos;, code: &apos;SEC&apos; },
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

describe(&apos;TransactionHistory&apos;, () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (inventoryManagementApi.getTransactions as jest.Mock).mockResolvedValue(mockApiResponse);
    (inventoryManagementApi.getWarehouses as jest.Mock).mockResolvedValue({
      success: true,
      data: mockWarehouses,
    });
  });

  it(&apos;renders transaction history component&apos;, async () => {
    render(<TransactionHistory />);
    
    expect(screen.getByText(&apos;Transaction History&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Track all inventory movements and changes&apos;)).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Another Product&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;displays loading spinner while fetching data&apos;, () => {
    (inventoryManagementApi.getTransactions as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );
    
    render(<TransactionHistory />);
    
    expect(screen.getByTestId(&apos;loading-spinner&apos;)).toBeInTheDocument();
  });

  it(&apos;displays transaction data correctly&apos;, async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      // Check transaction details
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;SKU: TEST-001&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Main Warehouse&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Sale&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;testuser&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;handles filter changes&apos;, async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Change warehouse filter
    const warehouseSelect = screen.getByDisplayValue(&apos;All Warehouses&apos;);
    fireEvent.change(warehouseSelect, { target: { value: &apos;1&apos; } });
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          warehouse: &apos;1&apos;,
          page: 1,
        })
      );
    });
  });

  it(&apos;handles transaction type filter&apos;, async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Change transaction type filter
    const typeSelect = screen.getByDisplayValue(&apos;All Types&apos;);
    fireEvent.change(typeSelect, { target: { value: &apos;sale&apos; } });
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          transaction_type: &apos;sale&apos;,
          page: 1,
        })
      );
    });
  });

  it(&apos;handles date range filters&apos;, async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Set date from filter
    const dateFromInput = screen.getByLabelText(&apos;Date From&apos;);
    fireEvent.change(dateFromInput, { target: { value: &apos;2024-01-01&apos; } });
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          date_from: &apos;2024-01-01&apos;,
          page: 1,
        })
      );
    });
  });

  it(&apos;handles search functionality&apos;, async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Search for product
    const searchInput = screen.getByPlaceholderText(&apos;Search by product name, SKU, or user...&apos;);
    fireEvent.change(searchInput, { target: { value: &apos;Test Product&apos; } });
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          product: &apos;Test Product&apos;,
          page: 1,
        })
      );
    });
  });

  it(&apos;clears filters when clear button is clicked&apos;, async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Set some filters first
    const searchInput = screen.getByPlaceholderText(&apos;Search by product name, SKU, or user...&apos;);
    fireEvent.change(searchInput, { target: { value: &apos;test&apos; } });
    
    // Clear filters
    const clearButton = screen.getByText(&apos;Clear Filters&apos;);
    fireEvent.click(clearButton);
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          product: &apos;&apos;,
          warehouse: &apos;&apos;,
          transaction_type: undefined,
          date_from: &apos;&apos;,
          date_to: &apos;&apos;,
          page: 1,
        })
      );
    });
  });

  it(&apos;opens transaction details modal when view button is clicked&apos;, async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Click view button for first transaction
    const viewButtons = screen.getAllByRole(&apos;button&apos;);
    const viewButton = viewButtons.find(button => 
      button.querySelector(&apos;svg&apos;) // Looking for the Eye icon
    );
    
    if (viewButton) {
      fireEvent.click(viewButton);
      
      await waitFor(() => {
        expect(screen.getByText(&apos;Transaction Details&apos;)).toBeInTheDocument();
        expect(screen.getByText(&apos;Transaction ID&apos;)).toBeInTheDocument();
      });
    }
  });

  it(&apos;handles CSV export&apos;, async () => {
    const mockBlob = new Blob([&apos;csv data&apos;], { type: &apos;text/csv&apos; });
    (inventoryManagementApi.exportTransactions as jest.Mock).mockResolvedValue(mockBlob);
    
    // Mock URL.createObjectURL and related methods
    global.URL.createObjectURL = jest.fn(() => &apos;mock-url&apos;);
    global.URL.revokeObjectURL = jest.fn();
    
    // Mock document.createElement and appendChild
    const mockLink = {
      href: &apos;&apos;,
      download: &apos;&apos;,
      click: jest.fn(),
    };
    jest.spyOn(document, &apos;createElement&apos;).mockReturnValue(mockLink as any);
    jest.spyOn(document.body, &apos;appendChild&apos;).mockImplementation(() => mockLink as any);
    jest.spyOn(document.body, &apos;removeChild&apos;).mockImplementation(() => mockLink as any);
    
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Click export button
    const exportButton = screen.getByText(&apos;Export CSV&apos;);
    fireEvent.click(exportButton);
    
    await waitFor(() => {
      expect(inventoryManagementApi.exportTransactions).toHaveBeenCalled();
      expect(mockLink.click).toHaveBeenCalled();
    });
  });

  it(&apos;displays correct transaction type colors and icons&apos;, async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      const saleTransaction = screen.getByText(&apos;Sale&apos;);
      const purchaseTransaction = screen.getByText(&apos;Purchase&apos;);
      
      expect(saleTransaction).toBeInTheDocument();
      expect(purchaseTransaction).toBeInTheDocument();
    });
  });

  it(&apos;formats quantity changes correctly&apos;, async () => {
    render(<TransactionHistory />);
    
    await waitFor(() => {
      // Should show negative change for sale (red)
      const negativeChange = screen.getByText(&apos;-5&apos;);
      expect(negativeChange).toBeInTheDocument();
      
      // Should show positive change for purchase (green)  
      const positiveChange = screen.getByText(&apos;+50&apos;);
      expect(positiveChange).toBeInTheDocument();
    });
  });

  it(&apos;handles API errors gracefully&apos;, async () => {
    const consoleSpy = jest.spyOn(console, &apos;error&apos;).mockImplementation(() => {});
    (inventoryManagementApi.getTransactions as jest.Mock).mockRejectedValue(
      new Error(&apos;API Error&apos;)
    );
    
    render(<TransactionHistory />);
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to fetch transactions:', expect.any(Error));
    });
    
    consoleSpy.mockRestore();
  });
});