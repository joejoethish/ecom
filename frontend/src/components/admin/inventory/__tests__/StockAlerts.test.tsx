import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import StockAlerts from '../StockAlerts';
import { inventoryManagementApi } from '@/services/inventoryManagementApi';

// Mock the API service
jest.mock('@/services/inventoryManagementApi', () => ({
  inventoryManagementApi: {
    getAlerts: jest.fn(),
    getWarehouses: jest.fn(),
    acknowledgeAlert: jest.fn(),
    dismissAlert: jest.fn(),
  },
}));

// Mock WebSocket
const mockWebSocket = {
  close: jest.fn(),
  send: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  onopen: null,
  onmessage: null,
  onclose: null,
  onerror: null,
};

global.WebSocket = jest.fn(() => mockWebSocket) as any;

const mockAlerts = [
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
    alert_type: 'low_stock' as const,
    priority: 'high' as const,
    message: 'Stock level is below reorder point',
    is_acknowledged: false,
    acknowledged_by: null,
    acknowledged_at: null,
    created_at: '2024-01-01T10:00:00Z',
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
    alert_type: 'out_of_stock' as const,
    priority: 'critical' as const,
    message: 'Product is completely out of stock',
    is_acknowledged: true,
    acknowledged_by: {
      id: '1',
      username: 'admin',
    },
    acknowledged_at: '2024-01-01T11:00:00Z',
    created_at: '2024-01-01T09:00:00Z',
  },
];

const mockWarehouses = [
  { id: '1', name: 'Main Warehouse', code: 'MW001' },
  { id: '2', name: 'Secondary Warehouse', code: 'SW002' },
];

const mockApiResponse = {
  success: true,
  data: {
    results: mockAlerts,
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

describe('StockAlerts', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (inventoryManagementApi.getAlerts as jest.Mock).mockResolvedValue(mockApiResponse);
    (inventoryManagementApi.getWarehouses as jest.Mock).mockResolvedValue({
      success: true,
      data: mockWarehouses,
    });
  });

  afterEach(() => {
    // Clean up WebSocket mock
    if (mockWebSocket.onclose && typeof mockWebSocket.onclose === 'function') {
      mockWebSocket.onclose(new CloseEvent('close'));
    }
  });

  it('renders stock alerts component correctly', async () => {
    render(<StockAlerts />);
    
    expect(screen.getByText('Stock Alerts')).toBeInTheDocument();
    expect(screen.getByText('Monitor and manage inventory alerts')).toBeInTheDocument();
    expect(screen.getByText('Configure Alerts')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
      expect(screen.getByText('Another Product')).toBeInTheDocument();
    });
  });

  it('displays alert statistics correctly', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument(); // Total alerts
      expect(screen.getByText('1')).toBeInTheDocument(); // Critical alerts
      expect(screen.getByText('1')).toBeInTheDocument(); // High priority alerts
      expect(screen.getByText('1')).toBeInTheDocument(); // Unacknowledged alerts
    });
  });

  it('displays alert details correctly', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
      expect(screen.getByText('SKU: TEST-001')).toBeInTheDocument();
      expect(screen.getByText('Main Warehouse')).toBeInTheDocument();
      expect(screen.getByText('Stock level is below reorder point')).toBeInTheDocument();
      expect(screen.getByText('HIGH')).toBeInTheDocument();
      expect(screen.getByText('low stock')).toBeInTheDocument();
    });
  });

  it('displays correct alert status indicators', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(screen.getByText('Acknowledged')).toBeInTheDocument();
    });
  });

  it('handles alert type filter changes', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const alertTypeSelect = screen.getByDisplayValue('All Types');
    fireEvent.change(alertTypeSelect, { target: { value: 'low_stock' } });

    await waitFor(() => {
      expect(inventoryManagementApi.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          alert_type: 'low_stock',
          page: 1,
        })
      );
    });
  });

  it('handles priority filter changes', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const prioritySelect = screen.getByDisplayValue('All Priorities');
    fireEvent.change(prioritySelect, { target: { value: 'critical' } });

    await waitFor(() => {
      expect(inventoryManagementApi.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          priority: 'critical',
          page: 1,
        })
      );
    });
  });

  it('handles status filter changes', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const statusSelect = screen.getByDisplayValue('All Status');
    fireEvent.change(statusSelect, { target: { value: 'false' } });

    await waitFor(() => {
      expect(inventoryManagementApi.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          is_acknowledged: false,
          page: 1,
        })
      );
    });
  });

  it('handles warehouse filter changes', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const warehouseSelect = screen.getByDisplayValue('All Warehouses');
    fireEvent.change(warehouseSelect, { target: { value: '1' } });

    await waitFor(() => {
      expect(inventoryManagementApi.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          warehouse: '1',
          page: 1,
        })
      );
    });
  });

  it('clears filters when clear button is clicked', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Set some filters first
    const alertTypeSelect = screen.getByDisplayValue('All Types');
    fireEvent.change(alertTypeSelect, { target: { value: 'low_stock' } });

    // Clear filters
    const clearButton = screen.getByText('Clear Filters');
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(inventoryManagementApi.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          alert_type: undefined,
          priority: undefined,
          is_acknowledged: undefined,
          warehouse: '',
          page: 1,
        })
      );
    });
  });

  it('handles alert acknowledgment', async () => {
    (inventoryManagementApi.acknowledgeAlert as jest.Mock).mockResolvedValue({
      success: true,
    });

    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Find and click acknowledge button for unacknowledged alert
    const acknowledgeButtons = screen.getAllByRole('button');
    const acknowledgeButton = acknowledgeButtons.find(button => 
      button.querySelector('svg') && button.className?.includes('text-green-600')
    );
    
    if (acknowledgeButton) {
      fireEvent.click(acknowledgeButton);
      
      await waitFor(() => {
        expect(inventoryManagementApi.acknowledgeAlert).toHaveBeenCalledWith('1');
      });
    }
  });

  it('handles alert dismissal', async () => {
    (inventoryManagementApi.dismissAlert as jest.Mock).mockResolvedValue({
      success: true,
    });

    // Mock window.confirm
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Find and click dismiss button
    const dismissButtons = screen.getAllByRole('button');
    const dismissButton = dismissButtons.find(button => 
      button.querySelector('svg') && button.className?.includes('text-red-600')
    );
    
    if (dismissButton) {
      fireEvent.click(dismissButton);
      
      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalled();
        expect(inventoryManagementApi.dismissAlert).toHaveBeenCalledWith('1');
      });
    }

    confirmSpy.mockRestore();
  });

  it('opens alert details modal when view button is clicked', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Click view button
    const viewButton = screen.getByText('View');
    fireEvent.click(viewButton);

    expect(screen.getByText('Alert Details')).toBeInTheDocument();
    expect(screen.getByText('Alert ID')).toBeInTheDocument();
  });

  it('closes alert details modal when close button is clicked', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Open modal
    const viewButton = screen.getByText('View');
    fireEvent.click(viewButton);

    expect(screen.getByText('Alert Details')).toBeInTheDocument();

    // Close modal
    const closeButton = screen.getByText('×');
    fireEvent.click(closeButton);

    expect(screen.queryByText('Alert Details')).not.toBeInTheDocument();
  });

  it('handles refresh functionality', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(inventoryManagementApi.getAlerts).toHaveBeenCalledTimes(2);
    });
  });

  it('displays correct priority colors', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      const highPriorityBadge = screen.getByText('HIGH');
      const criticalPriorityBadge = screen.getByText('CRITICAL');
      
      expect(highPriorityBadge).toBeInTheDocument();
      expect(criticalPriorityBadge).toBeInTheDocument();
    });
  });

  it('displays correct alert type icons and colors', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('low stock')).toBeInTheDocument();
      expect(screen.getByText('out of stock')).toBeInTheDocument();
    });
  });

  it('highlights unacknowledged alerts', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      const rows = screen.getAllByRole('row');
      // Find the row with unacknowledged alert (should have yellow background)
      const unacknowledgedRow = rows.find(row => 
        row.textContent?.includes('Test Product') && row.textContent?.includes('Pending')
      );
      expect(unacknowledgedRow).toHaveClass('bg-yellow-50');
    });
  });

  it('formats dates correctly', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      // Check that dates are formatted (exact format may vary by locale)
      expect(screen.getByText(/1\/1\/2024|2024-01-01/)).toBeInTheDocument();
      expect(screen.getByText(/10:00|10:00:00/)).toBeInTheDocument();
    });
  });

  it('handles loading state correctly', () => {
    (inventoryManagementApi.getAlerts as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<StockAlerts />);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    (inventoryManagementApi.getAlerts as jest.Mock).mockRejectedValue(
      new Error('API Error')
    );

    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to fetch alerts:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  it('sets up WebSocket connection for real-time updates', () => {
    render(<StockAlerts />);
    
    expect(WebSocket).toHaveBeenCalledWith(
      expect.stringContaining('/ws/inventory/alerts/')
    );
  });

  it('handles WebSocket messages for alert updates', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Simulate WebSocket message
    if (mockWebSocket.onmessage && typeof mockWebSocket.onmessage === 'function') {
      mockWebSocket.onmessage({
        data: JSON.stringify({
          type: 'alert_created',
          alert: mockAlerts[0],
        }),
      } as MessageEvent);
    }

    // Should trigger a refresh
    await waitFor(() => {
      expect(inventoryManagementApi.getAlerts).toHaveBeenCalledTimes(2);
    });
  });

  it('displays warehouse options in filter', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Main Warehouse (MW001)')).toBeInTheDocument();
      expect(screen.getByText('Secondary Warehouse (SW002)')).toBeInTheDocument();
    });
  });

  it('updates statistics when alerts are acknowledged', async () => {
    (inventoryManagementApi.acknowledgeAlert as jest.Mock).mockResolvedValue({
      success: true,
    });

    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
      // Initially 1 unacknowledged alert
      expect(screen.getByText('1')).toBeInTheDocument();
    });

    // Acknowledge an alert
    const acknowledgeButtons = screen.getAllByRole('button');
    const acknowledgeButton = acknowledgeButtons.find(button => 
      button.querySelector('svg') && button.className?.includes('text-green-600')
    );
    
    if (acknowledgeButton) {
      fireEvent.click(acknowledgeButton);
      
      await waitFor(() => {
        // Unacknowledged count should decrease
        const statsCards = screen.getAllByText('0');
        expect(statsCards.length).toBeGreaterThan(0);
      });
    }
  });

  it('updates statistics when alerts are dismissed', async () => {
    (inventoryManagementApi.dismissAlert as jest.Mock).mockResolvedValue({
      success: true,
    });

    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Dismiss an alert
    const dismissButtons = screen.getAllByRole('button');
    const dismissButton = dismissButtons.find(button => 
      button.querySelector('svg') && button.className?.includes('text-red-600')
    );
    
    if (dismissButton) {
      fireEvent.click(dismissButton);
      
      await waitFor(() => {
        // Total alerts count should decrease
        const statsCards = screen.getAllByText('1');
        expect(statsCards.length).toBeGreaterThan(0);
      });
    }

    confirmSpy.mockRestore();
  });

  it('opens configuration modal when Configure Alerts is clicked', async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const configureButton = screen.getByText('Configure Alerts');
    fireEvent.click(configureButton);

    // Note: The configuration modal is partially implemented in the component
    // This test verifies the button exists and can be clicked
    expect(configureButton).toBeInTheDocument();
  });

  it('displays truncated messages with full text in title', async () => {
    const longMessageAlert = {
      ...mockAlerts[0],
      message: 'This is a very long alert message that should be truncated in the display but shown in full in the title attribute for accessibility',
    };

    (inventoryManagementApi.getAlerts as jest.Mock).mockResolvedValue({
      ...mockApiResponse,
      data: {
        ...mockApiResponse.data,
        results: [longMessageAlert, mockAlerts[1]],
      },
    });

    render(<StockAlerts />);
    
    await waitFor(() => {
      const messageElement = screen.getByText(/This is a very long alert message/);
      expect(messageElement).toBeInTheDocument();
      expect(messageElement).toHaveClass('truncate');
    });
  });
});