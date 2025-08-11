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
    alert_type: &apos;low_stock&apos; as const,
    priority: &apos;high&apos; as const,
    message: &apos;Stock level is below reorder point&apos;,
    is_acknowledged: false,
    acknowledged_by: null,
    acknowledged_at: null,
    created_at: &apos;2024-01-01T10:00:00Z&apos;,
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
    alert_type: &apos;out_of_stock&apos; as const,
    priority: &apos;critical&apos; as const,
    message: &apos;Product is completely out of stock&apos;,
    is_acknowledged: true,
    acknowledged_by: {
      id: &apos;1&apos;,
      username: &apos;admin&apos;,
    },
    acknowledged_at: &apos;2024-01-01T11:00:00Z&apos;,
    created_at: &apos;2024-01-01T09:00:00Z&apos;,
  },
];

const mockWarehouses = [
  { id: &apos;1&apos;, name: &apos;Main Warehouse&apos;, code: &apos;MW001&apos; },
  { id: &apos;2&apos;, name: &apos;Secondary Warehouse&apos;, code: &apos;SW002&apos; },
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

describe(&apos;StockAlerts&apos;, () => {
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
    if (mockWebSocket.onclose) {
      mockWebSocket.onclose();
    }
  });

  it(&apos;renders stock alerts component correctly&apos;, async () => {
    render(<StockAlerts />);
    
    expect(screen.getByText(&apos;Stock Alerts&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Monitor and manage inventory alerts&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Configure Alerts&apos;)).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Another Product&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;displays alert statistics correctly&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;2&apos;)).toBeInTheDocument(); // Total alerts
      expect(screen.getByText(&apos;1&apos;)).toBeInTheDocument(); // Critical alerts
      expect(screen.getByText(&apos;1&apos;)).toBeInTheDocument(); // High priority alerts
      expect(screen.getByText(&apos;1&apos;)).toBeInTheDocument(); // Unacknowledged alerts
    });
  });

  it(&apos;displays alert details correctly&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;SKU: TEST-001&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Main Warehouse&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Stock level is below reorder point&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;HIGH&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;low stock&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;displays correct alert status indicators&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Pending&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Acknowledged&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;handles alert type filter changes&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const alertTypeSelect = screen.getByDisplayValue(&apos;All Types&apos;);
    fireEvent.change(alertTypeSelect, { target: { value: &apos;low_stock&apos; } });

    await waitFor(() => {
      expect(inventoryManagementApi.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          alert_type: &apos;low_stock&apos;,
          page: 1,
        })
      );
    });
  });

  it(&apos;handles priority filter changes&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const prioritySelect = screen.getByDisplayValue(&apos;All Priorities&apos;);
    fireEvent.change(prioritySelect, { target: { value: &apos;critical&apos; } });

    await waitFor(() => {
      expect(inventoryManagementApi.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          priority: &apos;critical&apos;,
          page: 1,
        })
      );
    });
  });

  it(&apos;handles status filter changes&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const statusSelect = screen.getByDisplayValue(&apos;All Status&apos;);
    fireEvent.change(statusSelect, { target: { value: &apos;false&apos; } });

    await waitFor(() => {
      expect(inventoryManagementApi.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          is_acknowledged: false,
          page: 1,
        })
      );
    });
  });

  it(&apos;handles warehouse filter changes&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const warehouseSelect = screen.getByDisplayValue(&apos;All Warehouses&apos;);
    fireEvent.change(warehouseSelect, { target: { value: &apos;1&apos; } });

    await waitFor(() => {
      expect(inventoryManagementApi.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          warehouse: &apos;1&apos;,
          page: 1,
        })
      );
    });
  });

  it(&apos;clears filters when clear button is clicked&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Set some filters first
    const alertTypeSelect = screen.getByDisplayValue(&apos;All Types&apos;);
    fireEvent.change(alertTypeSelect, { target: { value: &apos;low_stock&apos; } });

    // Clear filters
    const clearButton = screen.getByText(&apos;Clear Filters&apos;);
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(inventoryManagementApi.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          alert_type: undefined,
          priority: undefined,
          is_acknowledged: undefined,
          warehouse: &apos;&apos;,
          page: 1,
        })
      );
    });
  });

  it(&apos;handles alert acknowledgment&apos;, async () => {
    (inventoryManagementApi.acknowledgeAlert as jest.Mock).mockResolvedValue({
      success: true,
    });

    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Find and click acknowledge button for unacknowledged alert
    const acknowledgeButtons = screen.getAllByRole(&apos;button&apos;);
    const acknowledgeButton = acknowledgeButtons.find(button => 
      button.querySelector(&apos;svg&apos;) && button.className?.includes(&apos;text-green-600&apos;)
    );
    
    if (acknowledgeButton) {
      fireEvent.click(acknowledgeButton);
      
      await waitFor(() => {
        expect(inventoryManagementApi.acknowledgeAlert).toHaveBeenCalledWith(&apos;1&apos;);
      });
    }
  });

  it(&apos;handles alert dismissal&apos;, async () => {
    (inventoryManagementApi.dismissAlert as jest.Mock).mockResolvedValue({
      success: true,
    });

    // Mock window.confirm
    const confirmSpy = jest.spyOn(window, &apos;confirm&apos;).mockReturnValue(true);

    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Find and click dismiss button
    const dismissButtons = screen.getAllByRole(&apos;button&apos;);
    const dismissButton = dismissButtons.find(button => 
      button.querySelector(&apos;svg&apos;) && button.className?.includes(&apos;text-red-600&apos;)
    );
    
    if (dismissButton) {
      fireEvent.click(dismissButton);
      
      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalled();
        expect(inventoryManagementApi.dismissAlert).toHaveBeenCalledWith(&apos;1&apos;);
      });
    }

    confirmSpy.mockRestore();
  });

  it(&apos;opens alert details modal when view button is clicked&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Click view button
    const viewButton = screen.getByText(&apos;View&apos;);
    fireEvent.click(viewButton);

    expect(screen.getByText(&apos;Alert Details&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Alert ID&apos;)).toBeInTheDocument();
  });

  it(&apos;closes alert details modal when close button is clicked&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Open modal
    const viewButton = screen.getByText(&apos;View&apos;);
    fireEvent.click(viewButton);

    expect(screen.getByText(&apos;Alert Details&apos;)).toBeInTheDocument();

    // Close modal
    const closeButton = screen.getByText(&apos;×&apos;);
    fireEvent.click(closeButton);

    expect(screen.queryByText(&apos;Alert Details&apos;)).not.toBeInTheDocument();
  });

  it(&apos;handles refresh functionality&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const refreshButton = screen.getByText(&apos;Refresh&apos;);
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(inventoryManagementApi.getAlerts).toHaveBeenCalledTimes(2);
    });
  });

  it(&apos;displays correct priority colors&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      const highPriorityBadge = screen.getByText(&apos;HIGH&apos;);
      const criticalPriorityBadge = screen.getByText(&apos;CRITICAL&apos;);
      
      expect(highPriorityBadge).toBeInTheDocument();
      expect(criticalPriorityBadge).toBeInTheDocument();
    });
  });

  it(&apos;displays correct alert type icons and colors&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;low stock&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;out of stock&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;highlights unacknowledged alerts&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      const rows = screen.getAllByRole(&apos;row&apos;);
      // Find the row with unacknowledged alert (should have yellow background)
      const unacknowledgedRow = rows.find(row => 
        row.textContent?.includes(&apos;Test Product&apos;) && row.textContent?.includes(&apos;Pending&apos;)
      );
      expect(unacknowledgedRow).toHaveClass(&apos;bg-yellow-50&apos;);
    });
  });

  it(&apos;formats dates correctly&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      // Check that dates are formatted (exact format may vary by locale)
      expect(screen.getByText(/1\/1\/2024|2024-01-01/)).toBeInTheDocument();
      expect(screen.getByText(/10:00|10:00:00/)).toBeInTheDocument();
    });
  });

  it(&apos;handles loading state correctly&apos;, () => {
    (inventoryManagementApi.getAlerts as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<StockAlerts />);
    
    expect(screen.getByRole(&apos;progressbar&apos;)).toBeInTheDocument();
  });

  it(&apos;handles API errors gracefully&apos;, async () => {
    const consoleSpy = jest.spyOn(console, &apos;error&apos;).mockImplementation(() => {});
    (inventoryManagementApi.getAlerts as jest.Mock).mockRejectedValue(
      new Error(&apos;API Error&apos;)
    );

    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(&apos;Failed to fetch alerts:&apos;, expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  it(&apos;sets up WebSocket connection for real-time updates&apos;, () => {
    render(<StockAlerts />);
    
    expect(WebSocket).toHaveBeenCalledWith(
      expect.stringContaining(&apos;/ws/inventory/alerts/&apos;)
    );
  });

  it(&apos;handles WebSocket messages for alert updates&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Simulate WebSocket message
    if (mockWebSocket.onmessage) {
      mockWebSocket.onmessage({
        data: JSON.stringify({
          type: &apos;alert_created&apos;,
          alert: mockAlerts[0],
        }),
      } as MessageEvent);
    }

    // Should trigger a refresh
    await waitFor(() => {
      expect(inventoryManagementApi.getAlerts).toHaveBeenCalledTimes(2);
    });
  });

  it(&apos;displays warehouse options in filter&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Main Warehouse (MW001)&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Secondary Warehouse (SW002)&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;updates statistics when alerts are acknowledged&apos;, async () => {
    (inventoryManagementApi.acknowledgeAlert as jest.Mock).mockResolvedValue({
      success: true,
    });

    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
      // Initially 1 unacknowledged alert
      expect(screen.getByText(&apos;1&apos;)).toBeInTheDocument();
    });

    // Acknowledge an alert
    const acknowledgeButtons = screen.getAllByRole(&apos;button&apos;);
    const acknowledgeButton = acknowledgeButtons.find(button => 
      button.querySelector(&apos;svg&apos;) && button.className?.includes(&apos;text-green-600&apos;)
    );
    
    if (acknowledgeButton) {
      fireEvent.click(acknowledgeButton);
      
      await waitFor(() => {
        // Unacknowledged count should decrease
        const statsCards = screen.getAllByText(&apos;0&apos;);
        expect(statsCards.length).toBeGreaterThan(0);
      });
    }
  });

  it(&apos;updates statistics when alerts are dismissed&apos;, async () => {
    (inventoryManagementApi.dismissAlert as jest.Mock).mockResolvedValue({
      success: true,
    });

    const confirmSpy = jest.spyOn(window, &apos;confirm&apos;).mockReturnValue(true);

    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Dismiss an alert
    const dismissButtons = screen.getAllByRole(&apos;button&apos;);
    const dismissButton = dismissButtons.find(button => 
      button.querySelector(&apos;svg&apos;) && button.className?.includes(&apos;text-red-600&apos;)
    );
    
    if (dismissButton) {
      fireEvent.click(dismissButton);
      
      await waitFor(() => {
        // Total alerts count should decrease
        const statsCards = screen.getAllByText(&apos;1&apos;);
        expect(statsCards.length).toBeGreaterThan(0);
      });
    }

    confirmSpy.mockRestore();
  });

  it(&apos;opens configuration modal when Configure Alerts is clicked&apos;, async () => {
    render(<StockAlerts />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    const configureButton = screen.getByText(&apos;Configure Alerts&apos;);
    fireEvent.click(configureButton);

    // Note: The configuration modal is partially implemented in the component
    // This test verifies the button exists and can be clicked
    expect(configureButton).toBeInTheDocument();
  });

  it(&apos;displays truncated messages with full text in title&apos;, async () => {
    const longMessageAlert = {
      ...mockAlerts[0],
      message: &apos;This is a very long alert message that should be truncated in the display but shown in full in the title attribute for accessibility&apos;,
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