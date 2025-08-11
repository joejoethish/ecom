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
  id: &apos;1&apos;,
  inventory_item: {
    id: &apos;1&apos;,
    product_variant: {
      sku: &apos;TEST-SKU-001&apos;,
      product: {
        name: &apos;Test Product&apos;,
      },
    },
    warehouse: {
      name: &apos;Main Warehouse&apos;,
    },
  },
  transaction_type: &apos;adjustment&apos; as const,
  quantity_change: 10,
  previous_quantity: 100,
  new_quantity: 110,
  reason: &apos;Inventory Count Correction&apos;,
  reference_id: &apos;ADJ-001&apos;,
  user: {
    id: &apos;1&apos;,
    username: &apos;admin&apos;,
  },
  created_at: &apos;2024-01-01T10:00:00Z&apos;,
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

describe(&apos;AdjustmentHistory&apos;, () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (inventoryManagementApi.getTransactions as jest.Mock).mockResolvedValue(mockApiResponse);
  });

  it(&apos;renders adjustment history correctly&apos;, async () => {
    render(<AdjustmentHistory />);
    
    expect(screen.getByText(&apos;Stock Adjustment History&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Export CSV&apos;)).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;SKU: TEST-SKU-001&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Main Warehouse&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;+10&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;100 → 110&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Inventory Count Correction&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;admin&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;renders without title when inventoryId is provided&apos;, async () => {
    render(<AdjustmentHistory inventoryId="1" />);
    
    expect(screen.queryByText(&apos;Stock Adjustment History&apos;)).not.toBeInTheDocument();
    expect(screen.queryByText(&apos;Export CSV&apos;)).not.toBeInTheDocument();
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          inventory_item: &apos;1&apos;,
          transaction_type: &apos;adjustment&apos;,
        })
      );
    });
  });

  it(&apos;applies date filters correctly&apos;, async () => {
    render(<AdjustmentHistory />);
    
    const dateFromInput = screen.getByLabelText(&apos;Date From&apos;);
    const dateToInput = screen.getByLabelText(&apos;Date To&apos;);
    
    fireEvent.change(dateFromInput, { target: { value: &apos;2024-01-01&apos; } });
    fireEvent.change(dateToInput, { target: { value: &apos;2024-01-31&apos; } });
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          date_from: &apos;2024-01-01&apos;,
          date_to: &apos;2024-01-31&apos;,
        })
      );
    });
  });

  it(&apos;applies product search filter correctly&apos;, async () => {
    render(<AdjustmentHistory />);
    
    const productSearchInput = screen.getByPlaceholderText(&apos;Search products...&apos;);
    fireEvent.change(productSearchInput, { target: { value: &apos;Test Product&apos; } });
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          product: &apos;Test Product&apos;,
        })
      );
    });
  });

  it(&apos;applies warehouse filter correctly&apos;, async () => {
    render(<AdjustmentHistory />);
    
    const warehouseInput = screen.getByPlaceholderText(&apos;Warehouse name...&apos;);
    fireEvent.change(warehouseInput, { target: { value: &apos;Main Warehouse&apos; } });
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          warehouse: &apos;Main Warehouse&apos;,
        })
      );
    });
  });

  it(&apos;displays correct adjustment type colors&apos;, async () => {
    const negativeTransaction = {
      ...mockTransaction,
      id: &apos;2&apos;,
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
      expect(screen.getByText(&apos;+10&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;-5&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;handles export functionality&apos;, async () => {
    const mockBlob = new Blob([&apos;csv content&apos;], { type: &apos;text/csv&apos; });
    (inventoryManagementApi.exportTransactions as jest.Mock).mockResolvedValue(mockBlob);
    
    // Mock URL.createObjectURL and related functions
    const mockCreateObjectURL = jest.fn(() => &apos;mock-url&apos;);
    const mockRevokeObjectURL = jest.fn();
    global.URL.createObjectURL = mockCreateObjectURL;
    global.URL.revokeObjectURL = mockRevokeObjectURL;
    
    // Mock document.createElement and appendChild
    const mockLink = {
      href: &apos;&apos;,
      download: &apos;&apos;,
      click: jest.fn(),
    };
    const mockCreateElement = jest.fn(() => mockLink);
    const mockAppendChild = jest.fn();
    const mockRemoveChild = jest.fn();
    
    document.createElement = mockCreateElement;
    document.body.appendChild = mockAppendChild;
    document.body.removeChild = mockRemoveChild;
    
    render(<AdjustmentHistory />);
    
    const exportButton = screen.getByText(&apos;Export CSV&apos;);
    fireEvent.click(exportButton);
    
    await waitFor(() => {
      expect(inventoryManagementApi.exportTransactions).toHaveBeenCalled();
      expect(mockCreateObjectURL).toHaveBeenCalledWith(mockBlob);
      expect(mockLink.click).toHaveBeenCalled();
      expect(mockRevokeObjectURL).toHaveBeenCalledWith(&apos;mock-url&apos;);
    });
  });

  it(&apos;handles pagination correctly&apos;, async () => {
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
      expect(screen.getByText(&apos;Showing 1 to 20 of 50 results&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Page 1 of 3&apos;)).toBeInTheDocument();
    });
    
    const nextButton = screen.getByText(&apos;Next&apos;);
    fireEvent.click(nextButton);
    
    await waitFor(() => {
      expect(inventoryManagementApi.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2,
        })
      );
    });
  });

  it(&apos;displays empty state when no transactions found&apos;, async () => {
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
      expect(screen.getByText(&apos;No adjustment history found&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;handles API errors gracefully&apos;, async () => {
    const consoleSpy = jest.spyOn(console, &apos;error&apos;).mockImplementation(() => {});
    (inventoryManagementApi.getTransactions as jest.Mock).mockRejectedValue(new Error(&apos;API Error&apos;));
    
    render(<AdjustmentHistory />);
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(&apos;Failed to fetch adjustment history:&apos;, expect.any(Error));
    });
    
    consoleSpy.mockRestore();
  });

  it(&apos;formats dates correctly&apos;, async () => {
    render(<AdjustmentHistory />);
    
    await waitFor(() => {
      // Check that the date is formatted (exact format may vary by locale)
      expect(screen.getByText(/1\/1\/2024|2024-01-01/)).toBeInTheDocument();
      expect(screen.getByText(/10:00|10:00:00/)).toBeInTheDocument();
    });
  });

  it(&apos;truncates long reasons with title attribute&apos;, async () => {
    const longReasonTransaction = {
      ...mockTransaction,
      reason: &apos;This is a very long reason that should be truncated in the display but shown in full in the title attribute&apos;,
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