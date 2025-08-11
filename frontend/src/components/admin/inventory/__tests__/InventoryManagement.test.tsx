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
jest.mock(&apos;../InventoryForm&apos;, () => {
  return function MockInventoryForm({ onClose, onSave }: unknown) {
    return (
      <div data-testid="inventory-form">
        <button onClick={onClose}>Close Form</button>
        <button onClick={onSave}>Save Form</button>
      </div>
    );
  };
});

jest.mock(&apos;../WarehouseManagement&apos;, () => {
  return function MockWarehouseManagement() {
    return <div data-testid="warehouse-management">Warehouse Management</div>;
  };
});

jest.mock(&apos;../TransactionHistory&apos;, () => {
  return function MockTransactionHistory() {
    return <div data-testid="transaction-history">Transaction History</div>;
  };
});

jest.mock(&apos;../StockAlerts&apos;, () => {
  return function MockStockAlerts() {
    return <div data-testid="stock-alerts">Stock Alerts</div>;
  };
});

jest.mock(&apos;../StockAdjustmentModal&apos;, () => {
  return function MockStockAdjustmentModal({ onClose, onSuccess }: unknown) {
    return (
      <div data-testid="stock-adjustment-modal">
        <button onClick={onClose}>Close Modal</button>
        <button onClick={onSuccess}>Success</button>
      </div>
    );
  };
});

jest.mock(&apos;../AdjustmentHistory&apos;, () => {
  return function MockAdjustmentHistory() {
    return <div data-testid="adjustment-history">Adjustment History</div>;
  };
});

// Mock UI components
jest.mock(&apos;@/components/ui/ErrorBoundary&apos;, () => ({
  ErrorBoundary: ({ children }: unknown) => <div>{children}</div>,
  ErrorDisplay: ({ error, onRetry }: unknown) => (
    <div data-testid="error-display">
      <span>{error}</span>
      <button onClick={onRetry}>Retry</button>
    </div>
  ),
  EmptyState: ({ title, description, action }: unknown) => (
    <div data-testid="empty-state">
      <span>{title}</span>
      <span>{description}</span>
      {action}
    </div>
  ),
}));

jest.mock(&apos;@/components/ui/SkeletonLoader&apos;, () => ({
  SkeletonStats: ({ count }: unknown) => (
    <div data-testid="skeleton-stats">Loading {count} stats...</div>
  ),
  SkeletonInventoryItem: () => (
    <tr data-testid="skeleton-inventory-item">
      <td>Loading...</td>
    </tr>
  ),
}));

jest.mock(&apos;@/utils/errorHandling&apos;, () => ({
  handleApiResponse: jest.fn((response) => response),
  showErrorToast: jest.fn(),
  showSuccessToast: jest.fn(),
  debounce: jest.fn((fn) => fn),
  withRetry: jest.fn((fn) => fn()),
}));

const mockInventoryItems = [
  {
    id: &apos;1&apos;,
    product_variant: {
      id: &apos;1&apos;,
      sku: &apos;TEST-001&apos;,
      product: {
        id: &apos;1&apos;,
        name: &apos;Test Product&apos;,
        images: [
          {
            id: &apos;1&apos;,
            image: &apos;/test-image.jpg&apos;,
            is_primary: true,
          },
        ],
      },
      attributes: { color: &apos;red&apos;, size: &apos;M&apos; },
    },
    warehouse: {
      id: &apos;1&apos;,
      name: &apos;Main Warehouse&apos;,
      code: &apos;MW001&apos;,
      city: &apos;New York&apos;,
    },
    stock_quantity: 100,
    reserved_quantity: 10,
    available_quantity: 90,
    reorder_level: 20,
    last_stock_update: &apos;2024-01-01T00:00:00Z&apos;,
    stock_status: &apos;in_stock&apos; as const,
    created_at: &apos;2024-01-01T00:00:00Z&apos;,
    updated_at: &apos;2024-01-01T00:00:00Z&apos;,
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
  { id: &apos;1&apos;, name: &apos;Main Warehouse&apos;, code: &apos;MW001&apos; },
  { id: &apos;2&apos;, name: &apos;Secondary Warehouse&apos;, code: &apos;SW002&apos; },
];

describe(&apos;InventoryManagement&apos;, () => {
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

  it(&apos;renders inventory management tabs correctly&apos;, async () => {
    render(<InventoryManagement />);
    
    expect(screen.getByText(&apos;Inventory&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Warehouses&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Batches&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Transactions&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Adjustments&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Alerts&apos;)).toBeInTheDocument();
  });

  it(&apos;displays loading state initially&apos;, () => {
    render(<InventoryManagement />);
    
    expect(screen.getByTestId(&apos;skeleton-stats&apos;)).toBeInTheDocument();
  });

  it(&apos;displays stats after loading&apos;, async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;150&apos;)).toBeInTheDocument(); // total_products
      expect(screen.getByText(&apos;3&apos;)).toBeInTheDocument(); // total_warehouses
      expect(screen.getByText(&apos;12&apos;)).toBeInTheDocument(); // low_stock_items
      expect(screen.getByText(&apos;5&apos;)).toBeInTheDocument(); // out_of_stock_items
    });
  });

  it(&apos;displays inventory items after loading&apos;, async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;SKU: TEST-001&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Main Warehouse&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;MW001 • New York&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;handles search filter changes&apos;, async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(&apos;Search inventory...&apos;);
    fireEvent.change(searchInput, { target: { value: &apos;test search&apos; } });

    await waitFor(() => {
      expect(inventoryManagementApi.getInventory).toHaveBeenCalledWith(
        expect.objectContaining({
          search: &apos;test search&apos;,
        })
      );
    });
  });

  it(&apos;handles warehouse filter changes&apos;, async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const warehouseSelect = screen.getByDisplayValue(&apos;All Warehouses&apos;);
    fireEvent.change(warehouseSelect, { target: { value: &apos;1&apos; } });

    await waitFor(() => {
      expect(inventoryManagementApi.getInventory).toHaveBeenCalledWith(
        expect.objectContaining({
          warehouse: &apos;1&apos;,
        })
      );
    });
  });

  it(&apos;handles stock status filter changes&apos;, async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const statusSelect = screen.getByDisplayValue(&apos;All Stock Status&apos;);
    fireEvent.change(statusSelect, { target: { value: &apos;low_stock&apos; } });

    await waitFor(() => {
      expect(inventoryManagementApi.getInventory).toHaveBeenCalledWith(
        expect.objectContaining({
          stock_status: &apos;low_stock&apos;,
        })
      );
    });
  });

  it(&apos;opens inventory form when Add Inventory is clicked&apos;, async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const addButton = screen.getByText(&apos;Add Inventory&apos;);
    fireEvent.click(addButton);

    expect(screen.getByTestId(&apos;inventory-form&apos;)).toBeInTheDocument();
  });

  it(&apos;opens inventory form for editing when edit button is clicked&apos;, async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const editButtons = screen.getAllByRole(&apos;button&apos;);
    const editButton = editButtons.find(button => 
      button.getAttribute(&apos;title&apos;) === &apos;Edit Inventory&apos;
    );
    
    if (editButton) {
      fireEvent.click(editButton);
      expect(screen.getByTestId(&apos;inventory-form&apos;)).toBeInTheDocument();
    }
  });

  it(&apos;handles inventory deletion&apos;, async () => {
    (inventoryManagementApi.deleteInventory as jest.Mock).mockResolvedValue({
      success: true,
    });

    // Mock window.confirm
    const confirmSpy = jest.spyOn(window, &apos;confirm&apos;).mockReturnValue(true);

    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole(&apos;button&apos;);
    const deleteButton = deleteButtons.find(button => 
      button.getAttribute(&apos;title&apos;) === &apos;Delete Inventory&apos;
    );
    
    if (deleteButton) {
      fireEvent.click(deleteButton);
      
      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalled();
        expect(inventoryManagementApi.deleteInventory).toHaveBeenCalledWith(&apos;1&apos;);
      });
    }

    confirmSpy.mockRestore();
  });

  it(&apos;opens stock adjustment modal when adjust button is clicked&apos;, async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const adjustButtons = screen.getAllByRole(&apos;button&apos;);
    const adjustButton = adjustButtons.find(button => 
      button.getAttribute(&apos;title&apos;) === &apos;Adjust Stock&apos;
    );
    
    if (adjustButton) {
      fireEvent.click(adjustButton);
      expect(screen.getByTestId(&apos;stock-adjustment-modal&apos;)).toBeInTheDocument();
    }
  });

  it(&apos;handles bulk stock adjustment&apos;, async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Select an item
    const checkbox = screen.getAllByRole(&apos;checkbox&apos;)[1]; // First is select all
    fireEvent.click(checkbox);

    // Click bulk adjust button
    const bulkAdjustButton = screen.getByText(/Adjust Selected/);
    fireEvent.click(bulkAdjustButton);

    expect(screen.getByTestId(&apos;stock-adjustment-modal&apos;)).toBeInTheDocument();
  });

  it(&apos;handles select all functionality&apos;, async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const selectAllCheckbox = screen.getAllByRole(&apos;checkbox&apos;)[0];
    fireEvent.click(selectAllCheckbox);

    // Should show bulk adjust button
    expect(screen.getByText(/Adjust Selected \(1\)/)).toBeInTheDocument();
  });

  it(&apos;handles refresh functionality&apos;, async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const refreshButton = screen.getByText(&apos;Refresh&apos;);
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(inventoryManagementApi.getInventory).toHaveBeenCalledTimes(2);
      expect(inventoryManagementApi.getInventoryStats).toHaveBeenCalledTimes(2);
    });
  });

  it(&apos;switches between tabs correctly&apos;, async () => {
    render(<InventoryManagement />);
    
    // Click on Warehouses tab
    const warehousesTab = screen.getByText(&apos;Warehouses&apos;);
    fireEvent.click(warehousesTab);
    
    expect(screen.getByTestId(&apos;warehouse-management&apos;)).toBeInTheDocument();

    // Click on Transactions tab
    const transactionsTab = screen.getByText(&apos;Transactions&apos;);
    fireEvent.click(transactionsTab);
    
    expect(screen.getByTestId(&apos;transaction-history&apos;)).toBeInTheDocument();

    // Click on Alerts tab
    const alertsTab = screen.getByText(&apos;Alerts&apos;);
    fireEvent.click(alertsTab);
    
    expect(screen.getByTestId(&apos;stock-alerts&apos;)).toBeInTheDocument();

    // Click on Adjustments tab
    const adjustmentsTab = screen.getByText(&apos;Adjustments&apos;);
    fireEvent.click(adjustmentsTab);
    
    expect(screen.getByTestId(&apos;adjustment-history&apos;)).toBeInTheDocument();
  });

  it(&apos;displays empty state when no inventory items&apos;, async () => {
    (inventoryManagementApi.getInventory as jest.Mock).mockResolvedValue({
      success: true,
      data: { results: [] },
    });

    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByTestId(&apos;empty-state&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;No inventory items found&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;displays error state when API fails&apos;, async () => {
    (inventoryManagementApi.getInventory as jest.Mock).mockResolvedValue({
      success: false,
      error: { message: &apos;API Error&apos; },
    });

    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByTestId(&apos;error-display&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;API Error&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;handles stats API error gracefully&apos;, async () => {
    (inventoryManagementApi.getInventoryStats as jest.Mock).mockResolvedValue({
      success: false,
      error: { message: &apos;Stats API Error&apos; },
    });

    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Stats API Error&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;handles warehouses API error gracefully&apos;, async () => {
    (inventoryManagementApi.getWarehouses as jest.Mock).mockResolvedValue({
      success: false,
      error: { message: &apos;Warehouses API Error&apos; },
    });

    render(<InventoryManagement />);
    
    await waitFor(() => {
      const warehouseSelect = screen.getByDisplayValue(&apos;Error loading warehouses&apos;);
      expect(warehouseSelect).toBeDisabled();
    });
  });

  it(&apos;displays correct stock status badges&apos;, async () => {
    const inventoryWithDifferentStatuses = [
      { ...mockInventoryItems[0], stock_status: &apos;in_stock&apos; },
      { ...mockInventoryItems[0], id: &apos;2&apos;, stock_status: &apos;low_stock&apos; },
      { ...mockInventoryItems[0], id: &apos;3&apos;, stock_status: &apos;out_of_stock&apos; },
    ];

    (inventoryManagementApi.getInventory as jest.Mock).mockResolvedValue({
      success: true,
      data: { results: inventoryWithDifferentStatuses },
    });

    render(<InventoryManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;in stock&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;low stock&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;out of stock&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;formats dates correctly&apos;, async () => {
    render(<InventoryManagement />);
    
    await waitFor(() => {
      // Check that the date is formatted (exact format may vary by locale)
      expect(screen.getByText(/1\/1\/2024|2024-01-01/)).toBeInTheDocument();
    });
  });

  it(&apos;handles image loading errors gracefully&apos;, async () => {
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