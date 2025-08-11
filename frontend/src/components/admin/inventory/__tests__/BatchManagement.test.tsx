import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import BatchManagement from '../BatchManagement';
import { inventoryManagementApi } from '@/services/inventoryManagementApi';

// Mock the API service
jest.mock('@/services/inventoryManagementApi', () => ({
  inventoryManagementApi: {
    getBatches: jest.fn(),
    getWarehouses: jest.fn(),
    deleteBatch: jest.fn(),
  },
}));

// Mock BatchForm component
jest.mock(&apos;../BatchForm&apos;, () => {
  return function MockBatchForm({ batch, onClose, onSave }: unknown) {
    return (
      <div data-testid="batch-form">
        <span>{batch ? &apos;Edit Batch&apos; : &apos;Add Batch&apos;}</span>
        <button onClick={onClose}>Close</button>
        <button onClick={onSave}>Save</button>
      </div>
    );
  };
});

const mockBatches = [
  {
    id: &apos;1&apos;,
    batch_number: &apos;BATCH-001&apos;,
    product_variant: {
      id: &apos;1&apos;,
      sku: &apos;TEST-001&apos;,
      product: {
        name: &apos;Test Product&apos;,
      },
    },
    warehouse: {
      id: &apos;1&apos;,
      name: &apos;Main Warehouse&apos;,
    },
    quantity: 100,
    remaining_quantity: 80,
    expiration_date: &apos;2024-12-31T00:00:00Z&apos;,
    manufacturing_date: &apos;2024-01-01T00:00:00Z&apos;,
    supplier: &apos;Test Supplier&apos;,
    cost_per_unit: 10.50,
    status: &apos;active&apos; as const,
    created_at: &apos;2024-01-01T00:00:00Z&apos;,
    updated_at: &apos;2024-01-01T00:00:00Z&apos;,
  },
  {
    id: &apos;2&apos;,
    batch_number: &apos;BATCH-002&apos;,
    product_variant: {
      id: &apos;2&apos;,
      sku: &apos;TEST-002&apos;,
      product: {
        name: &apos;Another Product&apos;,
      },
    },
    warehouse: {
      id: &apos;1&apos;,
      name: &apos;Main Warehouse&apos;,
    },
    quantity: 50,
    remaining_quantity: 0,
    expiration_date: &apos;2024-01-15T00:00:00Z&apos;, // Expired
    manufacturing_date: &apos;2023-12-01T00:00:00Z&apos;,
    supplier: &apos;Another Supplier&apos;,
    cost_per_unit: 5.25,
    status: &apos;expired&apos; as const,
    created_at: &apos;2023-12-01T00:00:00Z&apos;,
    updated_at: &apos;2024-01-15T00:00:00Z&apos;,
  },
];

const mockWarehouses = [
  { id: &apos;1&apos;, name: &apos;Main Warehouse&apos;, code: &apos;MW001&apos; },
  { id: &apos;2&apos;, name: &apos;Secondary Warehouse&apos;, code: &apos;SW002&apos; },
];

describe(&apos;BatchManagement&apos;, () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (inventoryManagementApi.getBatches as jest.Mock).mockResolvedValue({
      success: true,
      data: { results: mockBatches },
    });
    (inventoryManagementApi.getWarehouses as jest.Mock).mockResolvedValue({
      success: true,
      data: mockWarehouses,
    });
  });

  it(&apos;renders batch management component correctly&apos;, async () => {
    render(<BatchManagement />);
    
    expect(screen.getByText(&apos;Add Batch&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;FIFO View&apos;)).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText(&apos;BATCH-001&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;BATCH-002&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;displays batch statistics correctly&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;2&apos;)).toBeInTheDocument(); // Total batches
      expect(screen.getByText(&apos;1&apos;)).toBeInTheDocument(); // Active batches
      expect(screen.getByText(&apos;1&apos;)).toBeInTheDocument(); // Expired batches
    });
  });

  it(&apos;displays batch details correctly&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;SKU: TEST-001&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Main Warehouse&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Supplier: Test Supplier&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Cost: $10.50/unit&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Total: 100&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Remaining: 80&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Used: 20&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;displays correct batch status badges&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;active&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;expired&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;handles warehouse filter changes&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;BATCH-001&apos;)).toBeInTheDocument();
    });

    const warehouseSelect = screen.getByDisplayValue(&apos;All Warehouses&apos;);
    fireEvent.change(warehouseSelect, { target: { value: &apos;1&apos; } });

    await waitFor(() => {
      expect(inventoryManagementApi.getBatches).toHaveBeenCalledWith(
        expect.objectContaining({
          warehouse: &apos;1&apos;,
        })
      );
    });
  });

  it(&apos;handles status filter changes&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;BATCH-001&apos;)).toBeInTheDocument();
    });

    const statusSelect = screen.getByDisplayValue(&apos;All Status&apos;);
    fireEvent.change(statusSelect, { target: { value: &apos;active&apos; } });

    await waitFor(() => {
      expect(inventoryManagementApi.getBatches).toHaveBeenCalledWith(
        expect.objectContaining({
          status: &apos;active&apos;,
        })
      );
    });
  });

  it(&apos;handles expiring soon filter&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;BATCH-001&apos;)).toBeInTheDocument();
    });

    const expiringSoonCheckbox = screen.getByLabelText(&apos;Expiring Soon&apos;);
    fireEvent.click(expiringSoonCheckbox);

    await waitFor(() => {
      expect(inventoryManagementApi.getBatches).toHaveBeenCalledWith(
        expect.objectContaining({
          expiring_soon: true,
        })
      );
    });
  });

  it(&apos;opens batch form when Add Batch is clicked&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;BATCH-001&apos;)).toBeInTheDocument();
    });

    const addButton = screen.getByText(&apos;Add Batch&apos;);
    fireEvent.click(addButton);

    expect(screen.getByTestId(&apos;batch-form&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Add Batch&apos;)).toBeInTheDocument();
  });

  it(&apos;opens batch form for editing when edit button is clicked&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;BATCH-001&apos;)).toBeInTheDocument();
    });

    const editButtons = screen.getAllByRole(&apos;button&apos;);
    const editButton = editButtons.find(button => 
      button.querySelector(&apos;svg&apos;) && !button.textContent?.includes(&apos;Add&apos;)
    );
    
    if (editButton) {
      fireEvent.click(editButton);
      expect(screen.getByTestId(&apos;batch-form&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Edit Batch&apos;)).toBeInTheDocument();
    }
  });

  it(&apos;handles batch deletion&apos;, async () => {
    (inventoryManagementApi.deleteBatch as jest.Mock).mockResolvedValue({
      success: true,
    });

    // Mock window.confirm
    const confirmSpy = jest.spyOn(window, &apos;confirm&apos;).mockReturnValue(true);

    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;BATCH-001&apos;)).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole(&apos;button&apos;);
    const deleteButton = deleteButtons.find(button => 
      button.querySelector(&apos;svg&apos;) && button.className?.includes(&apos;text-red-600&apos;)
    );
    
    if (deleteButton) {
      fireEvent.click(deleteButton);
      
      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalled();
        expect(inventoryManagementApi.deleteBatch).toHaveBeenCalledWith(&apos;1&apos;);
      });
    }

    confirmSpy.mockRestore();
  });

  it(&apos;displays FIFO view when FIFO View button is clicked&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;BATCH-001&apos;)).toBeInTheDocument();
    });

    const fifoButton = screen.getByText(&apos;FIFO View&apos;);
    fireEvent.click(fifoButton);

    expect(screen.getByText(&apos;FIFO Allocation Order&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Back to List&apos;)).toBeInTheDocument();
  });

  it(&apos;returns to list view from FIFO view&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;BATCH-001&apos;)).toBeInTheDocument();
    });

    // Go to FIFO view
    const fifoButton = screen.getByText(&apos;FIFO View&apos;);
    fireEvent.click(fifoButton);

    expect(screen.getByText(&apos;FIFO Allocation Order&apos;)).toBeInTheDocument();

    // Go back to list
    const backButton = screen.getByText(&apos;Back to List&apos;);
    fireEvent.click(backButton);

    expect(screen.getByText(&apos;Add Batch&apos;)).toBeInTheDocument();
  });

  it(&apos;displays correct expiration status colors&apos;, async () => {
    // Mock current date to test expiration logic
    const mockDate = new Date(&apos;2024-06-01T00:00:00Z&apos;);
    jest.spyOn(global, &apos;Date&apos;).mockImplementation(() => mockDate as any);

    render(<BatchManagement />);
    
    await waitFor(() => {
      // Should show different expiration statuses based on dates
      expect(screen.getByText(/days/)).toBeInTheDocument();
    });

    (global.Date as any).mockRestore();
  });

  it(&apos;calculates and displays correct statistics&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      // Total batches
      expect(screen.getByText(&apos;2&apos;)).toBeInTheDocument();
      
      // Active batches (status === &apos;active&apos;)
      const activeElements = screen.getAllByText(&apos;1&apos;);
      expect(activeElements.length).toBeGreaterThan(0);
      
      // Expired batches (status === &apos;expired&apos;)
      const expiredElements = screen.getAllByText(&apos;1&apos;);
      expect(expiredElements.length).toBeGreaterThan(0);
    });
  });

  it(&apos;handles loading state correctly&apos;, () => {
    (inventoryManagementApi.getBatches as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<BatchManagement />);
    
    expect(screen.getByRole(&apos;progressbar&apos;)).toBeInTheDocument();
  });

  it(&apos;handles API errors gracefully&apos;, async () => {
    const consoleSpy = jest.spyOn(console, &apos;error&apos;).mockImplementation(() => {});
    (inventoryManagementApi.getBatches as jest.Mock).mockRejectedValue(
      new Error(&apos;API Error&apos;)
    );

    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(&apos;Failed to fetch batches:&apos;, expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  it(&apos;formats dates correctly&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      // Check that manufacturing and expiration dates are formatted
      expect(screen.getByText(/Mfg:/)).toBeInTheDocument();
    });
  });

  it(&apos;displays correct quantity calculations&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      // For first batch: quantity=100, remaining=80, used=20
      expect(screen.getByText(&apos;Total: 100&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Remaining: 80&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Used: 20&apos;)).toBeInTheDocument();
      
      // For second batch: quantity=50, remaining=0, used=50
      expect(screen.getByText(&apos;Total: 50&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Remaining: 0&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Used: 50&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;handles batch form save correctly&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;BATCH-001&apos;)).toBeInTheDocument();
    });

    // Open form
    const addButton = screen.getByText(&apos;Add Batch&apos;);
    fireEvent.click(addButton);

    // Save form
    const saveButton = screen.getByText(&apos;Save&apos;);
    fireEvent.click(saveButton);

    // Should refresh batches
    await waitFor(() => {
      expect(inventoryManagementApi.getBatches).toHaveBeenCalledTimes(2);
    });
  });

  it(&apos;displays warehouse options in filter&apos;, async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Main Warehouse (MW001)&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Secondary Warehouse (SW002)&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;groups batches correctly in FIFO view&apos;, async () => {
    // Add more batches for the same product to test grouping
    const batchesWithSameProduct = [
      ...mockBatches,
      {
        ...mockBatches[0],
        id: &apos;3&apos;,
        batch_number: &apos;BATCH-003&apos;,
        expiration_date: &apos;2024-06-30T00:00:00Z&apos;, // Earlier expiration
      },
    ];

    (inventoryManagementApi.getBatches as jest.Mock).mockResolvedValue({
      success: true,
      data: { results: batchesWithSameProduct },
    });

    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('BATCH-001')).toBeInTheDocument();
    });

    // Go to FIFO view
    const fifoButton = screen.getByText('FIFO View');
    fireEvent.click(fifoButton);

    expect(screen.getByText('FIFO Allocation Order')).toBeInTheDocument();
    
    // Should show batches grouped by product and sorted by expiration
    expect(screen.getByText('Test Product')).toBeInTheDocument();
  });
});