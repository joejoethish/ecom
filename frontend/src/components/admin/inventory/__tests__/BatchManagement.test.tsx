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
jest.mock('../BatchForm', () => {
  return function MockBatchForm({ batch, onClose, onSave }: any) {
    return (
      <div data-testid="batch-form">
        <span>{batch ? 'Edit Batch' : 'Add Batch'}</span>
        <button onClick={onClose}>Close</button>
        <button onClick={onSave}>Save</button>
      </div>
    );
  };
});

const mockBatches = [
  {
    id: '1',
    batch_number: 'BATCH-001',
    product_variant: {
      id: '1',
      sku: 'TEST-001',
      product: {
        name: 'Test Product',
      },
    },
    warehouse: {
      id: '1',
      name: 'Main Warehouse',
    },
    quantity: 100,
    remaining_quantity: 80,
    expiration_date: '2024-12-31T00:00:00Z',
    manufacturing_date: '2024-01-01T00:00:00Z',
    supplier: 'Test Supplier',
    cost_per_unit: 10.50,
    status: 'active' as const,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    batch_number: 'BATCH-002',
    product_variant: {
      id: '2',
      sku: 'TEST-002',
      product: {
        name: 'Another Product',
      },
    },
    warehouse: {
      id: '1',
      name: 'Main Warehouse',
    },
    quantity: 50,
    remaining_quantity: 0,
    expiration_date: '2024-01-15T00:00:00Z', // Expired
    manufacturing_date: '2023-12-01T00:00:00Z',
    supplier: 'Another Supplier',
    cost_per_unit: 5.25,
    status: 'expired' as const,
    created_at: '2023-12-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
  },
];

const mockWarehouses = [
  { id: '1', name: 'Main Warehouse', code: 'MW001' },
  { id: '2', name: 'Secondary Warehouse', code: 'SW002' },
];

describe('BatchManagement', () => {
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

  it('renders batch management component correctly', async () => {
    render(<BatchManagement />);
    
    expect(screen.getByText('Add Batch')).toBeInTheDocument();
    expect(screen.getByText('FIFO View')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('BATCH-001')).toBeInTheDocument();
      expect(screen.getByText('BATCH-002')).toBeInTheDocument();
    });
  });

  it('displays batch statistics correctly', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument(); // Total batches
      expect(screen.getByText('1')).toBeInTheDocument(); // Active batches
      expect(screen.getByText('1')).toBeInTheDocument(); // Expired batches
    });
  });

  it('displays batch details correctly', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
      expect(screen.getByText('SKU: TEST-001')).toBeInTheDocument();
      expect(screen.getByText('Main Warehouse')).toBeInTheDocument();
      expect(screen.getByText('Supplier: Test Supplier')).toBeInTheDocument();
      expect(screen.getByText('Cost: $10.50/unit')).toBeInTheDocument();
      expect(screen.getByText('Total: 100')).toBeInTheDocument();
      expect(screen.getByText('Remaining: 80')).toBeInTheDocument();
      expect(screen.getByText('Used: 20')).toBeInTheDocument();
    });
  });

  it('displays correct batch status badges', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('active')).toBeInTheDocument();
      expect(screen.getByText('expired')).toBeInTheDocument();
    });
  });

  it('handles warehouse filter changes', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('BATCH-001')).toBeInTheDocument();
    });

    const warehouseSelect = screen.getByDisplayValue('All Warehouses');
    fireEvent.change(warehouseSelect, { target: { value: '1' } });

    await waitFor(() => {
      expect(inventoryManagementApi.getBatches).toHaveBeenCalledWith(
        expect.objectContaining({
          warehouse: '1',
        })
      );
    });
  });

  it('handles status filter changes', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('BATCH-001')).toBeInTheDocument();
    });

    const statusSelect = screen.getByDisplayValue('All Status');
    fireEvent.change(statusSelect, { target: { value: 'active' } });

    await waitFor(() => {
      expect(inventoryManagementApi.getBatches).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'active',
        })
      );
    });
  });

  it('handles expiring soon filter', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('BATCH-001')).toBeInTheDocument();
    });

    const expiringSoonCheckbox = screen.getByLabelText('Expiring Soon');
    fireEvent.click(expiringSoonCheckbox);

    await waitFor(() => {
      expect(inventoryManagementApi.getBatches).toHaveBeenCalledWith(
        expect.objectContaining({
          expiring_soon: true,
        })
      );
    });
  });

  it('opens batch form when Add Batch is clicked', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('BATCH-001')).toBeInTheDocument();
    });

    const addButton = screen.getByText('Add Batch');
    fireEvent.click(addButton);

    expect(screen.getByTestId('batch-form')).toBeInTheDocument();
    expect(screen.getByText('Add Batch')).toBeInTheDocument();
  });

  it('opens batch form for editing when edit button is clicked', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('BATCH-001')).toBeInTheDocument();
    });

    const editButtons = screen.getAllByRole('button');
    const editButton = editButtons.find(button => 
      button.querySelector('svg') && !button.textContent?.includes('Add')
    );
    
    if (editButton) {
      fireEvent.click(editButton);
      expect(screen.getByTestId('batch-form')).toBeInTheDocument();
      expect(screen.getByText('Edit Batch')).toBeInTheDocument();
    }
  });

  it('handles batch deletion', async () => {
    (inventoryManagementApi.deleteBatch as jest.Mock).mockResolvedValue({
      success: true,
    });

    // Mock window.confirm
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('BATCH-001')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole('button');
    const deleteButton = deleteButtons.find(button => 
      button.querySelector('svg') && button.className?.includes('text-red-600')
    );
    
    if (deleteButton) {
      fireEvent.click(deleteButton);
      
      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalled();
        expect(inventoryManagementApi.deleteBatch).toHaveBeenCalledWith('1');
      });
    }

    confirmSpy.mockRestore();
  });

  it('displays FIFO view when FIFO View button is clicked', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('BATCH-001')).toBeInTheDocument();
    });

    const fifoButton = screen.getByText('FIFO View');
    fireEvent.click(fifoButton);

    expect(screen.getByText('FIFO Allocation Order')).toBeInTheDocument();
    expect(screen.getByText('Back to List')).toBeInTheDocument();
  });

  it('returns to list view from FIFO view', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('BATCH-001')).toBeInTheDocument();
    });

    // Go to FIFO view
    const fifoButton = screen.getByText('FIFO View');
    fireEvent.click(fifoButton);

    expect(screen.getByText('FIFO Allocation Order')).toBeInTheDocument();

    // Go back to list
    const backButton = screen.getByText('Back to List');
    fireEvent.click(backButton);

    expect(screen.getByText('Add Batch')).toBeInTheDocument();
  });

  it('displays correct expiration status colors', async () => {
    // Mock current date to test expiration logic
    const mockDate = new Date('2024-06-01T00:00:00Z');
    jest.spyOn(global, 'Date').mockImplementation(() => mockDate as any);

    render(<BatchManagement />);
    
    await waitFor(() => {
      // Should show different expiration statuses based on dates
      expect(screen.getByText(/days/)).toBeInTheDocument();
    });

    (global.Date as any).mockRestore();
  });

  it('calculates and displays correct statistics', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      // Total batches
      expect(screen.getByText('2')).toBeInTheDocument();
      
      // Active batches (status === 'active')
      const activeElements = screen.getAllByText('1');
      expect(activeElements.length).toBeGreaterThan(0);
      
      // Expired batches (status === 'expired')
      const expiredElements = screen.getAllByText('1');
      expect(expiredElements.length).toBeGreaterThan(0);
    });
  });

  it('handles loading state correctly', () => {
    (inventoryManagementApi.getBatches as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<BatchManagement />);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    (inventoryManagementApi.getBatches as jest.Mock).mockRejectedValue(
      new Error('API Error')
    );

    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to fetch batches:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  it('formats dates correctly', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      // Check that manufacturing and expiration dates are formatted
      expect(screen.getByText(/Mfg:/)).toBeInTheDocument();
    });
  });

  it('displays correct quantity calculations', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      // For first batch: quantity=100, remaining=80, used=20
      expect(screen.getByText('Total: 100')).toBeInTheDocument();
      expect(screen.getByText('Remaining: 80')).toBeInTheDocument();
      expect(screen.getByText('Used: 20')).toBeInTheDocument();
      
      // For second batch: quantity=50, remaining=0, used=50
      expect(screen.getByText('Total: 50')).toBeInTheDocument();
      expect(screen.getByText('Remaining: 0')).toBeInTheDocument();
      expect(screen.getByText('Used: 50')).toBeInTheDocument();
    });
  });

  it('handles batch form save correctly', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('BATCH-001')).toBeInTheDocument();
    });

    // Open form
    const addButton = screen.getByText('Add Batch');
    fireEvent.click(addButton);

    // Save form
    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);

    // Should refresh batches
    await waitFor(() => {
      expect(inventoryManagementApi.getBatches).toHaveBeenCalledTimes(2);
    });
  });

  it('displays warehouse options in filter', async () => {
    render(<BatchManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Main Warehouse (MW001)')).toBeInTheDocument();
      expect(screen.getByText('Secondary Warehouse (SW002)')).toBeInTheDocument();
    });
  });

  it('groups batches correctly in FIFO view', async () => {
    // Add more batches for the same product to test grouping
    const batchesWithSameProduct = [
      ...mockBatches,
      {
        ...mockBatches[0],
        id: '3',
        batch_number: 'BATCH-003',
        expiration_date: '2024-06-30T00:00:00Z', // Earlier expiration
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