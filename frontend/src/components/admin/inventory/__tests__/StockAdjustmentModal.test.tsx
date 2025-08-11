import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import StockAdjustmentModal from '../StockAdjustmentModal';
import { inventoryManagementApi } from '@/services/inventoryManagementApi';

// Mock the API
jest.mock('@/services/inventoryManagementApi', () => ({
  inventoryManagementApi: {
    adjustStock: jest.fn(),
    bulkAdjustStock: jest.fn(),
  },
}));

const mockInventoryItem = {
  id: &apos;1&apos;,
  product_variant: {
    id: &apos;1&apos;,
    sku: &apos;TEST-SKU-001&apos;,
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
};

const mockProps = {
  inventory: mockInventoryItem,
  onClose: jest.fn(),
  onSuccess: jest.fn(),
};

describe(&apos;StockAdjustmentModal&apos;, () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it(&apos;renders single item adjustment modal correctly&apos;, () => {
    render(<StockAdjustmentModal {...mockProps} />);
    
    expect(screen.getByText(&apos;Stock Adjustment&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;SKU: TEST-SKU-001&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Main Warehouse (MW001)&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;100&apos;)).toBeInTheDocument(); // Current stock
    expect(screen.getByText(&apos;10&apos;)).toBeInTheDocument(); // Reserved
    expect(screen.getByText(&apos;90&apos;)).toBeInTheDocument(); // Available
  });

  it(&apos;renders bulk adjustment modal correctly&apos;, () => {
    const bulkProps = {
      ...mockProps,
      inventory: [mockInventoryItem, { ...mockInventoryItem, id: &apos;2&apos; }],
    };
    
    render(<StockAdjustmentModal {...bulkProps} />);
    
    expect(screen.getByText(&apos;Bulk Stock Adjustment&apos;)).toBeInTheDocument();
    expect(screen.getAllByText(&apos;Test Product&apos;)).toHaveLength(2);
  });

  it(&apos;updates adjustment amount correctly&apos;, () => {
    render(<StockAdjustmentModal {...mockProps} />);
    
    const adjustmentInput = screen.getByDisplayValue(&apos;0&apos;);
    fireEvent.change(adjustmentInput, { target: { value: &apos;10&apos; } });
    
    expect(adjustmentInput).toHaveValue(10);
    expect(screen.getByText(&apos;New Stock Quantity: 110&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;New Available: 100&apos;)).toBeInTheDocument();
  });

  it(&apos;handles quick adjustment buttons&apos;, () => {
    render(<StockAdjustmentModal {...mockProps} />);
    
    const plusOneButton = screen.getByRole(&apos;button&apos;, { name: &apos;&apos; }); // Plus icon button
    const adjustmentInput = screen.getByDisplayValue(&apos;0&apos;);
    
    // Find the +1 button (with Plus icon)
    const quickButtons = screen.getAllByRole(&apos;button&apos;);
    const plusButton = quickButtons.find(button => 
      button.querySelector(&apos;svg&apos;) && button.textContent === &apos;&apos;
    );
    
    if (plusButton) {
      fireEvent.click(plusButton);
      expect(adjustmentInput).toHaveValue(1);
    }
  });

  it(&apos;validates required reason field&apos;, async () => {
    render(<StockAdjustmentModal {...mockProps} />);
    
    // Set adjustment amount
    const adjustmentInput = screen.getByDisplayValue(&apos;0&apos;);
    fireEvent.change(adjustmentInput, { target: { value: &apos;10&apos; } });
    
    // Try to submit without reason
    const submitButton = screen.getByText(&apos;Apply Adjustments&apos;);
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Please provide a reason for all adjustments&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;validates negative stock quantity&apos;, async () => {
    render(<StockAdjustmentModal {...mockProps} />);
    
    // Set adjustment that would make stock negative
    const adjustmentInput = screen.getByDisplayValue(&apos;0&apos;);
    fireEvent.change(adjustmentInput, { target: { value: &apos;-150&apos; } });
    
    // Set reason
    const reasonSelect = screen.getByDisplayValue(&apos;&apos;);
    fireEvent.change(reasonSelect, { target: { value: &apos;Inventory Count Correction&apos; } });
    
    // Try to submit
    const submitButton = screen.getByText(&apos;Apply Adjustments&apos;);
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/New quantity cannot be negative/)).toBeInTheDocument();
    });
  });

  it(&apos;validates available quantity would not go negative&apos;, async () => {
    render(<StockAdjustmentModal {...mockProps} />);
    
    // Set adjustment that would make available quantity negative
    const adjustmentInput = screen.getByDisplayValue(&apos;0&apos;);
    fireEvent.change(adjustmentInput, { target: { value: &apos;-95&apos; } }); // Available is 90, so -95 would be negative
    
    // Set reason
    const reasonSelect = screen.getByDisplayValue(&apos;&apos;);
    fireEvent.change(reasonSelect, { target: { value: &apos;Inventory Count Correction&apos; } });
    
    // Try to submit
    const submitButton = screen.getByText(&apos;Apply Adjustments&apos;);
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Adjustment would result in negative available quantity/)).toBeInTheDocument();
    });
  });

  it(&apos;submits single adjustment successfully&apos;, async () => {
    const mockAdjustStock = inventoryManagementApi.adjustStock as jest.MockedFunction<typeof inventoryManagementApi.adjustStock>;
    mockAdjustStock.mockResolvedValue({ success: true, data: mockInventoryItem });
    
    render(<StockAdjustmentModal {...mockProps} />);
    
    // Set adjustment amount
    const adjustmentInput = screen.getByDisplayValue(&apos;0&apos;);
    fireEvent.change(adjustmentInput, { target: { value: &apos;10&apos; } });
    
    // Set reason
    const reasonSelect = screen.getByDisplayValue(&apos;&apos;);
    fireEvent.change(reasonSelect, { target: { value: &apos;Inventory Count Correction&apos; } });
    
    // Submit
    const submitButton = screen.getByText(&apos;Apply Adjustments&apos;);
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockAdjustStock).toHaveBeenCalledWith(&apos;1&apos;, {
        adjustment: 10,
        reason: &apos;Inventory Count Correction&apos;,
      });
      expect(mockProps.onSuccess).toHaveBeenCalled();
      expect(mockProps.onClose).toHaveBeenCalled();
    });
  });

  it(&apos;submits bulk adjustment successfully&apos;, async () => {
    const mockBulkAdjustStock = inventoryManagementApi.bulkAdjustStock as jest.MockedFunction<typeof inventoryManagementApi.bulkAdjustStock>;
    mockBulkAdjustStock.mockResolvedValue({ success: true, data: [mockInventoryItem] });
    
    const bulkProps = {
      ...mockProps,
      inventory: [mockInventoryItem, { ...mockInventoryItem, id: &apos;2&apos; }],
    };
    
    render(<StockAdjustmentModal {...bulkProps} />);
    
    // Set adjustment amounts for both items
    const adjustmentInputs = screen.getAllByDisplayValue(&apos;0&apos;);
    fireEvent.change(adjustmentInputs[0], { target: { value: &apos;10&apos; } });
    fireEvent.change(adjustmentInputs[1], { target: { value: &apos;5&apos; } });
    
    // Set reasons for both items
    const reasonSelects = screen.getAllByDisplayValue(&apos;&apos;);
    fireEvent.change(reasonSelects[0], { target: { value: &apos;Inventory Count Correction&apos; } });
    fireEvent.change(reasonSelects[1], { target: { value: &apos;Damaged Goods&apos; } });
    
    // Submit
    const submitButton = screen.getByText(&apos;Apply Adjustments&apos;);
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockBulkAdjustStock).toHaveBeenCalledWith([
        {
          inventory_id: &apos;1&apos;,
          adjustment: 10,
          reason: &apos;Inventory Count Correction&apos;,
        },
        {
          inventory_id: &apos;2&apos;,
          adjustment: 5,
          reason: &apos;Damaged Goods&apos;,
        },
      ]);
      expect(mockProps.onSuccess).toHaveBeenCalled();
      expect(mockProps.onClose).toHaveBeenCalled();
    });
  });

  it(&apos;handles custom reason input&apos;, async () => {
    const mockAdjustStock = inventoryManagementApi.adjustStock as jest.MockedFunction<typeof inventoryManagementApi.adjustStock>;
    mockAdjustStock.mockResolvedValue({ success: true, data: mockInventoryItem });
    
    render(<StockAdjustmentModal {...mockProps} />);
    
    // Set adjustment amount
    const adjustmentInput = screen.getByDisplayValue(&apos;0&apos;);
    fireEvent.change(adjustmentInput, { target: { value: &apos;10&apos; } });
    
    // Set reason to &quot;Other&quot;
    const reasonSelect = screen.getByDisplayValue(&apos;&apos;);
    fireEvent.change(reasonSelect, { target: { value: &apos;Other&apos; } });
    
    // Custom reason input should appear
    await waitFor(() => {
      expect(screen.getByPlaceholderText(&apos;Please specify the reason for adjustment&apos;)).toBeInTheDocument();
    });
    
    // Set custom reason
    const customReasonInput = screen.getByPlaceholderText(&apos;Please specify the reason for adjustment&apos;);
    fireEvent.change(customReasonInput, { target: { value: &apos;Custom test reason&apos; } });
    
    // Submit
    const submitButton = screen.getByText(&apos;Apply Adjustments&apos;);
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockAdjustStock).toHaveBeenCalledWith(&apos;1&apos;, {
        adjustment: 10,
        reason: &apos;Custom test reason&apos;,
      });
    });
  });

  it(&apos;handles API errors gracefully&apos;, async () => {
    const mockAdjustStock = inventoryManagementApi.adjustStock as jest.MockedFunction<typeof inventoryManagementApi.adjustStock>;
    mockAdjustStock.mockResolvedValue({
      success: false,
      error: {
        message: &apos;API Error occurred&apos;,
        code: &apos;api_error&apos;,
        status_code: 500
      }
    });
    
    render(<StockAdjustmentModal {...mockProps} />);
    
    // Set adjustment amount
    const adjustmentInput = screen.getByDisplayValue(&apos;0&apos;);
    fireEvent.change(adjustmentInput, { target: { value: &apos;10&apos; } });
    
    // Set reason
    const reasonSelect = screen.getByDisplayValue(&apos;&apos;);
    fireEvent.change(reasonSelect, { target: { value: &apos;Inventory Count Correction&apos; } });
    
    // Submit
    const submitButton = screen.getByText(&apos;Apply Adjustments&apos;);
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;API Error occurred&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;closes modal when close button is clicked&apos;, () => {
    render(<StockAdjustmentModal {...mockProps} />);
    
    const closeButton = screen.getByRole('button', { name: '' }); // X icon button
    fireEvent.click(closeButton);
    
    expect(mockProps.onClose).toHaveBeenCalled();
  });
});