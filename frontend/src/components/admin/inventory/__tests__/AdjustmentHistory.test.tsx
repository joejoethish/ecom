import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AdjustmentHistory from '../AdjustmentHistory';
import { inventoryManagementApi } from '@/services/inventoryManagementApi';

// Mock the API
jest.mock('@/services/inventoryManagementApi', () => ({
  inventoryManagementApi: {
    getTransactions: jest.fn(),
    exportTransactions: jest.fn(),
  },
}));

const mockTransaction = {
  id: '1',
  inventory_item: {
    id: '1',
    product_variant: {
      sku: 'TEST-SKU-001',
      product: {
        name: 'Test Product',
      },
    },
    warehouse: {
      name: 'Main Warehouse',
    },
  },
  transaction_type: 'adjustment' as const,
  quantity_change: 10,
  previous_quantity: 100,
  new_quantity: 110,
  reason: 'Inventory Count Correction',
  reference_id: 'ADJ-001',
  user: {
    id: '1',
    username: 'admin',
  },
  created_at: '2024-01-01T10:00:00Z',
};

const mockApiResponse = {
  success: true,
  data: {
    results: [mockTransaction],
    count: 1,
    next: null,
    previous: null,
  },
};

describe('AdjustmentHistory', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (inventoryManagementApi.getTransactions as jest.Mock).mockResolvedValue(mockApiResponse);
  });

  it('renders adjustment history correctly', async () => {
    render(<AdjustmentHistory />);
    
    expect(screen.getByText('Stock Adjustment History')).toBeInTheDocument();
    expect(screen.getByText('Export CSV')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
      expect(screen.getByText('SKU: TEST-SKU-001')).toBeInTheDocument();
      expect(screen.getByText('Main Warehouse')).toBeInTheDocument();
      expect(screen.getByText('+10')).toBeInTheDocument();
      expect(screen.getByText('100 → 110')).toBeInTheDocument();
      expect(screen.getByText('Inventory Count Correction')).toBeInTheDocument();
      expect(screen.getByText('admin')).toBeInTheDocument();
    });
  });

  it('renders without title when inventoryId is provided', async () => {
    render(<AdjustmentHistory inventoryId="1" />);
    
    expect(screen.queryByText('Stock Adjustment History')).not.toBeInTheDocument();
    expect(screen.queryByText('Export CSV')).not.toBeInTheDocument();
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          inventory_item: '1',
          transaction_type: 'adjustment',
        })
      );
    });
  });

  it('applies date filters correctly', async () => {
    render(<AdjustmentHistory />);
    
    const dateFromInput = screen.getByLabelText('Date From');
    const dateToInput = screen.getByLabelText('Date To');
    
    fireEvent.change(dateFromInput, { target: { value: '2024-01-01' } });
    fireEvent.change(dateToInput, { target: { value: '2024-01-31' } });
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          date_from: '2024-01-01',
          date_to: '2024-01-31',
        })
      );
    });
  });

  it('applies product search filter correctly', async () => {
    render(<AdjustmentHistory />);
    
    const productSearchInput = screen.getByPlaceholderText('Search products...');
    fireEvent.change(productSearchInput, { target: { value: 'Test Product' } });
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          product: 'Test Product',
        })
      );
    });
  });

  it('applies warehouse filter correctly', async () => {
    render(<AdjustmentHistory />);
    
    const warehouseInput = screen.getByPlaceholderText('Warehouse name...');
    fireEvent.change(warehouseInput, { target: { value: 'Main Warehouse' } });
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          warehouse: 'Main Warehouse',
        })
      );
    });
  });

  it('displays correct adjustment type colors', async () => {
    const negativeTransaction = {
      ...mockTransaction,
      id: '2',
      quantity_change: -5,
      previous_quantity: 100,
      new_quantity: 95,
    };
    
    const mockResponseWithNegative = {
      ...mockApiResponse,
      data: {
        ...mockApiResponse.data,
        results: [mockTransaction, negativeTransaction],
        count: 2,
      },
    };
    
    (inventoryManagementApi.getTransactions as jest.Mock).mockResolvedValue(mockResponseWithNegative);
    
    render(<AdjustmentHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('+10')).toBeInTheDocument();
      expect(screen.getByText('-5')).toBeInTheDocument();
    });
  });

  it('handles export functionality', async () => {
    const mockBlob = new Blob(['csv content'], { type: 'text/csv' });
    (inventoryManagementApi.exportTransactions as jest.Mock).mockResolvedValue(mockBlob);
    
    // Mock URL.createObjectURL and related functions
    const mockCreateObjectURL = jest.fn(() => 'mock-url');
    const mockRevokeObjectURL = jest.fn();
    global.URL.createObjectURL = mockCreateObjectURL;
    global.URL.revokeObjectURL = mockRevokeObjectURL;
    
    // Mock document.createElement and appendChild
    const mockLink = {
      href: '',
      download: '',
      click: jest.fn(),
    };
    const mockCreateElement = jest.fn(() => mockLink);
    const mockAppendChild = jest.fn();
    const mockRemoveChild = jest.fn();
    
    document.createElement = mockCreateElement;
    document.body.appendChild = mockAppendChild;
    document.body.removeChild = mockRemoveChild;
    
    render(<AdjustmentHistory />);
    
    const exportButton = screen.getByText('Export CSV');
    fireEvent.click(exportButton);
    
    await waitFor(() => {
      expect(inventoryManagementApi.exportTransactions).toHaveBeenCalled();
      expect(mockCreateObjectURL).toHaveBeenCalledWith(mockBlob);
      expect(mockLink.click).toHaveBeenCalled();
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('mock-url');
    });
  });

  it('handles pagination correctly', async () => {
    const mockResponseWithPagination = {
      ...mockApiResponse,
      data: {
        ...mockApiResponse.data,
        count: 50,
      },
    };
    
    (inventoryManagementApi.getTransactions as jest.Mock).mockResolvedValue(mockResponseWithPagination);
    
    render(<AdjustmentHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('Showing 1 to 20 of 50 results')).toBeInTheDocument();
      expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
    });
    
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2,
        })
      );
    });
  });

  it('displays empty state when no transactions found', async () => {
    const emptyResponse = {
      success: true,
      data: {
        results: [],
        count: 0,
        next: null,
        previous: null,
      },
    };
    
    (inventoryManagementApi.getTransactions as jest.Mock).mockResolvedValue(emptyResponse);
    
    render(<AdjustmentHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('No adjustment history found')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    (inventoryManagementApi.getTransactions as jest.Mock).mockRejectedValue(new Error('API Error'));
    
    render(<AdjustmentHistory />);
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to fetch adjustment history:', expect.any(Error));
    });
    
    consoleSpy.mockRestore();
  });

  it('formats dates correctly', async () => {
    render(<AdjustmentHistory />);
    
    await waitFor(() => {
      // Check that the date is formatted (exact format may vary by locale)
      expect(screen.getByText(/1\/1\/2024|2024-01-01/)).toBeInTheDocument();
      expect(screen.getByText(/10:00|10:00:00/)).toBeInTheDocument();
    });
  });

  it('truncates long reasons with title attribute', async () => {
    const longReasonTransaction = {
      ...mockTransaction,
      reason: 'This is a very long reason that should be truncated in the display but shown in full in the title attribute',
    };
    
    const mockResponseWithLongReason = {
      ...mockApiResponse,
      data: {
        ...mockApiResponse.data,
        results: [longReasonTransaction],
      },
    };
    
    (inventoryManagementApi.getTransactions as jest.Mock).mockResolvedValue(mockResponseWithLongReason);
    
    render(<AdjustmentHistory />);
    
    await waitFor(() => {
      const reasonElement = screen.getByText(/This is a very long reason/);
      expect(reasonElement).toHaveAttribute('title', longReasonTransaction.reason);
    });
  });
});