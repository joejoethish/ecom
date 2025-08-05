import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import InventoryManagement from '../InventoryManagement';
import { inventoryManagementApi } from '@/services/inventoryManagementApi';

// Mock the API service
jest.mock('@/services/inventoryManagementApi', () => ({
  inventoryManagementApi: {
    getInventory: jest.fn(),
    getInventoryStats: jest.fn(),
    getWarehouses: jest.fn(),
    deleteInventory: jest.fn(),
  },
}));

// Mock child components
jest.mock('../InventoryForm', () => {
  return function MockInventoryForm({ onClose, onSave }: any) {
    return (
      <div data-testid="inventory-form">
        <button onClick={onClose}>Close Form</button>
        <button onClick={onSave}>Save Form</button>
      </div>
    );
  };
});

jest.mock('../WarehouseManagement', () => {
  return function MockWarehouseManagement() {
    return <div data-testid="warehouse-management">Warehouse Management</div>;
  };
});

jest.mock('../TransactionHistory', () => {
  return function MockTransactionHistory() {
    return <div data-testid="transaction-history">Transaction History</div>;
  };
});

jest.mock('../StockAlerts', () => {
  return function MockStockAlerts() {
    return <div data-testid="stock-alerts">Stock Alerts</div>;
  };
});

jest.mock('../StockAdjustmentModal', () => {
  return function MockStockAdjustmentModal({ onClose, onSuccess }: any) {
    return (
      <div data-testid="stock-adjustment-modal">
        <button onClick={onClose}>Close Modal</button>
        <button onClick={onSuccess}>Success</button>
      </div>
    );
  };
});

jest.mock('../AdjustmentHistory', () => {
  return function MockAdjustmentHistory() {
    return <div data-testid="adjustment-history">Adjustment History</div>;
  };
});

// Mock UI components
jest.mock('@/components/ui/ErrorBoundary', () => ({
  ErrorBoundary: ({ children }: any) => <div>{children}</div>,
  ErrorDisplay: ({ error, onRetry }: any) => (
    <div data-testid="error-display">
      <span>{error}</span>
      <button onClick={onRetry}>Retry</button>
    </div>
  ),
  EmptyState: ({ title, description, action }: any) => (
    <div data-testid="empty-state">
      <span>{title}</span>
      <span>{description}</span>
      {action}
    </div>
  ),
}));

jest.mock('@/components/ui/SkeletonLoader', () => ({
  SkeletonStats: ({ count }: any) => (
    <div data-testid="skeleton-stats">Loading {count} stats...</div>
  ),
  SkeletonInventoryItem: () => (
    <tr data-testid="skeleton-inventory-item">
      <td>Loading...</td>
    </tr>
  ),
}));

jest.mock('@/utils/errorHandling', () => ({
  handleApiResponse: jest.fn((response) => response),
  showErrorToast: jest.fn(),
  showSuccessToast: jest.fn(),
  debounce: jest.fn((fn) => fn),
  withRetry: jest.fn((fn) => fn()),
}));

const mockInventoryItems = [
  {
    id: '1',
    product_variant: {
      id: '1',
      sku: 'TEST-001',
      product: {
        id: '1',
        name: 'Test Product',
        images: [
          {
            id: '1',
            image: '/test-image.jpg',
            is_primary: true,
          },
        ],
      },
      attributes: { color: 'red', size: 'M' },
    },
    warehouse: {
      id: '1',
      name: 'Main Warehouse',
      code: 'MW001',
      city: 'New York',
    },
    stock_quantity: 100,
    reserved_quantity: 10,
    available_quantity: 90,
    reorder_level: 20,
    last_stock_update: '2024-01-01T00:00:00Z',
    stock_status: 'in_stock' as const,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const mockStats = {
  total_products: 150,
  total_warehouses: 3,
  low_stock_items: 12,
  out_of_stock_items: 5,
  total_stock_value: 50000,
  total_transactions_today: 25,
};

const mockWarehouses = [
  { id: '1', name: 'Main Warehouse', code: 'MW001' },
  { id: '2', name: 'Secondary Warehouse', code: 'SW002' },
];

describe('InventoryManagement', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (inventoryManagementApi.getInventory as jest.Mock).mockResolvedValue({
      success: true,
      data: { results: mockInventoryItems },
    });
    (inventoryManagementApi.getInventoryStats as jest.Mock).mockResolvedValue({
      success: true,
      data: mockStats,
    });
    (inventoryManagementApi.getWarehouses as jest.Mock).mockResolvedValue({
      success: true,
      data: mockWarehouses,
    });
  });

  it('renders inventory management tabs correctly', async () => {
    render(<InventoryManagement />);
    
    expect(screen.getByText('Inventory')).toBeInTheDocument();
    expect(screen.getByText('Warehouses')).toBeInTheDocument();
    expect(screen.getByText('Batches')).toBeInTheDocument();
    expect(screen.getByText('Transactions')).toBeInTheDocument();
    expect(screen.getByText('Adjustments')).toBeInTheDocument();
    expect(screen.getByText('Alerts')).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    render(<InventoryManagement />);
    
    expect(screen.getByTestId('skeleton-stats')).toBeInTheDocument();
  });

  it('displays stats after loading', async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument(); // total_products
      expect(screen.getByText('3')).toBeInTheDocument(); // total_warehouses
      expect(screen.getByText('12')).toBeInTheDocument(); // low_stock_items
      expect(screen.getByText('5')).toBeInTheDocument(); // out_of_stock_items
    });
  });

  it('displays inventory items after loading', async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
      expect(screen.getByText('SKU: TEST-001')).toBeInTheDocument();
      expect(screen.getByText('Main Warehouse')).toBeInTheDocument();
      expect(screen.getByText('MW001 • New York')).toBeInTheDocument();
    });
  });

  it('handles search filter changes', async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search inventory...');
    fireEvent.change(searchInput, { target: { value: 'test search' } });

    await waitFor(() => {
      expect(inventoryManagementApi.getInventory).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'test search',
        })
      );
    });
  });

  it('handles warehouse filter changes', async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const warehouseSelect = screen.getByDisplayValue('All Warehouses');
    fireEvent.change(warehouseSelect, { target: { value: '1' } });

    await waitFor(() => {
      expect(inventoryManagementApi.getInventory).toHaveBeenCalledWith(
        expect.objectContaining({
          warehouse: '1',
        })
      );
    });
  });

  it('handles stock status filter changes', async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const statusSelect = screen.getByDisplayValue('All Stock Status');
    fireEvent.change(statusSelect, { target: { value: 'low_stock' } });

    await waitFor(() => {
      expect(inventoryManagementApi.getInventory).toHaveBeenCalledWith(
        expect.objectContaining({
          stock_status: 'low_stock',
        })
      );
    });
  });

  it('opens inventory form when Add Inventory is clicked', async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const addButton = screen.getByText('Add Inventory');
    fireEvent.click(addButton);

    expect(screen.getByTestId('inventory-form')).toBeInTheDocument();
  });

  it('opens inventory form for editing when edit button is clicked', async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const editButtons = screen.getAllByRole('button');
    const editButton = editButtons.find(button => 
      button.getAttribute('title') === 'Edit Inventory'
    );
    
    if (editButton) {
      fireEvent.click(editButton);
      expect(screen.getByTestId('inventory-form')).toBeInTheDocument();
    }
  });

  it('handles inventory deletion', async () => {
    (inventoryManagementApi.deleteInventory as jest.Mock).mockResolvedValue({
      success: true,
    });

    // Mock window.confirm
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole('button');
    const deleteButton = deleteButtons.find(button => 
      button.getAttribute('title') === 'Delete Inventory'
    );
    
    if (deleteButton) {
      fireEvent.click(deleteButton);
      
      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalled();
        expect(inventoryManagementApi.deleteInventory).toHaveBeenCalledWith('1');
      });
    }

    confirmSpy.mockRestore();
  });

  it('opens stock adjustment modal when adjust button is clicked', async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const adjustButtons = screen.getAllByRole('button');
    const adjustButton = adjustButtons.find(button => 
      button.getAttribute('title') === 'Adjust Stock'
    );
    
    if (adjustButton) {
      fireEvent.click(adjustButton);
      expect(screen.getByTestId('stock-adjustment-modal')).toBeInTheDocument();
    }
  });

  it('handles bulk stock adjustment', async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Select an item
    const checkbox = screen.getAllByRole('checkbox')[1]; // First is select all
    fireEvent.click(checkbox);

    // Click bulk adjust button
    const bulkAdjustButton = screen.getByText(/Adjust Selected/);
    fireEvent.click(bulkAdjustButton);

    expect(screen.getByTestId('stock-adjustment-modal')).toBeInTheDocument();
  });

  it('handles select all functionality', async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const selectAllCheckbox = screen.getAllByRole('checkbox')[0];
    fireEvent.click(selectAllCheckbox);

    // Should show bulk adjust button
    expect(screen.getByText(/Adjust Selected \(1\)/)).toBeInTheDocument();
  });

  it('handles refresh functionality', async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(inventoryManagementApi.getInventory).toHaveBeenCalledTimes(2);
      expect(inventoryManagementApi.getInventoryStats).toHaveBeenCalledTimes(2);
    });
  });

  it('switches between tabs correctly', async () => {
    render(<InventoryManagement />);
    
    // Click on Warehouses tab
    const warehousesTab = screen.getByText('Warehouses');
    fireEvent.click(warehousesTab);
    
    expect(screen.getByTestId('warehouse-management')).toBeInTheDocument();

    // Click on Transactions tab
    const transactionsTab = screen.getByText('Transactions');
    fireEvent.click(transactionsTab);
    
    expect(screen.getByTestId('transaction-history')).toBeInTheDocument();

    // Click on Alerts tab
    const alertsTab = screen.getByText('Alerts');
    fireEvent.click(alertsTab);
    
    expect(screen.getByTestId('stock-alerts')).toBeInTheDocument();

    // Click on Adjustments tab
    const adjustmentsTab = screen.getByText('Adjustments');
    fireEvent.click(adjustmentsTab);
    
    expect(screen.getByTestId('adjustment-history')).toBeInTheDocument();
  });

  it('displays empty state when no inventory items', async () => {
    (inventoryManagementApi.getInventory as jest.Mock).mockResolvedValue({
      success: true,
      data: { results: [] },
    });

    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
      expect(screen.getByText('No inventory items found')).toBeInTheDocument();
    });
  });

  it('displays error state when API fails', async () => {
    (inventoryManagementApi.getInventory as jest.Mock).mockResolvedValue({
      success: false,
      error: { message: 'API Error' },
    });

    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByTestId('error-display')).toBeInTheDocument();
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('handles stats API error gracefully', async () => {
    (inventoryManagementApi.getInventoryStats as jest.Mock).mockResolvedValue({
      success: false,
      error: { message: 'Stats API Error' },
    });

    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Stats API Error')).toBeInTheDocument();
    });
  });

  it('handles warehouses API error gracefully', async () => {
    (inventoryManagementApi.getWarehouses as jest.Mock).mockResolvedValue({
      success: false,
      error: { message: 'Warehouses API Error' },
    });

    render(<InventoryManagement />);
    
    await waitFor(() => {
      const warehouseSelect = screen.getByDisplayValue('Error loading warehouses');
      expect(warehouseSelect).toBeDisabled();
    });
  });

  it('displays correct stock status badges', async () => {
    const inventoryWithDifferentStatuses = [
      { ...mockInventoryItems[0], stock_status: 'in_stock' },
      { ...mockInventoryItems[0], id: '2', stock_status: 'low_stock' },
      { ...mockInventoryItems[0], id: '3', stock_status: 'out_of_stock' },
    ];

    (inventoryManagementApi.getInventory as jest.Mock).mockResolvedValue({
      success: true,
      data: { results: inventoryWithDifferentStatuses },
    });

    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('in stock')).toBeInTheDocument();
      expect(screen.getByText('low stock')).toBeInTheDocument();
      expect(screen.getByText('out of stock')).toBeInTheDocument();
    });
  });

  it('formats dates correctly', async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      // Check that the date is formatted (exact format may vary by locale)
      expect(screen.getByText(/1\/1\/2024|2024-01-01/)).toBeInTheDocument();
    });
  });

  it('handles image loading errors gracefully', async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      const image = screen.getByAltText('Test Product');
      expect(image).toBeInTheDocument();
      
      // Simulate image load error
      fireEvent.error(image);
      
      // Image should be hidden
      expect(image).toHaveStyle('display: none');
    });
  });
});