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
  id: '1',
  product_variant: {
    id: '1',
    sku: 'TEST-SKU-001',
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
};

const mockProps = {
  inventory: mockInventoryItem,
  onClose: jest.fn(),
  onSuccess: jest.fn(),
};

describe('StockAdjustmentModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders single item adjustment modal correctly', () => {
    render(<StockAdjustmentModal {...mockProps} />);
    
    expect(screen.getByText('Stock Adjustment')).toBeInTheDocument();
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('SKU: TEST-SKU-001')).toBeInTheDocument();
    expect(screen.getByText('Main Warehouse (MW001)')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument(); // Current stock
    expect(screen.getByText('10')).toBeInTheDocument(); // Reserved
    expect(screen.getByText('90')).toBeInTheDocument(); // Available
  });

  it('renders bulk adjustment modal correctly', () => {
    const bulkProps = {
      ...mockProps,
      inventory: [mockInventoryItem, { ...mockInventoryItem, id: '2' }],
    };
    
    render(<StockAdjustmentModal {...bulkProps} />);
    
    expect(screen.getByText('Bulk Stock Adjustment')).toBeInTheDocument();
    expect(screen.getAllByText('Test Product')).toHaveLength(2);
  });

  it('updates adjustment amount correctly', () => {
    render(<StockAdjustmentModal {...mockProps} />);
    
    const adjustmentInput = screen.getByDisplayValue('0');
    fireEvent.change(adjustmentInput, { target: { value: '10' } });
    
    expect(adjustmentInput).toHaveValue(10);
    expect(screen.getByText('New Stock Quantity: 110')).toBeInTheDocument();
    expect(screen.getByText('New Available: 100')).toBeInTheDocument();
  });

  it('handles quick adjustment buttons', () => {
    render(<StockAdjustmentModal {...mockProps} />);
    
    const plusOneButton = screen.getByRole('button', { name: '' }); // Plus icon button
    const adjustmentInput = screen.getByDisplayValue('0');
    
    // Find the +1 button (with Plus icon)
    const quickButtons = screen.getAllByRole('button');
    const plusButton = quickButtons.find(button => 
      button.querySelector('svg') && button.textContent === ''
    );
    
    if (plusButton) {
      fireEvent.click(plusButton);
      expect(adjustmentInput).toHaveValue(1);
    }
  });

  it('validates required reason field', async () => {
    render(<StockAdjustmentModal {...mockProps} />);
    
    // Set adjustment amount
    const adjustmentInput = screen.getByDisplayValue('0');
    fireEvent.change(adjustmentInput, { target: { value: '10' } });
    
    // Try to submit without reason
    const submitButton = screen.getByText('Apply Adjustments');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Please provide a reason for all adjustments')).toBeInTheDocument();
    });
  });

  it('validates negative stock quantity', async () => {
    render(<StockAdjustmentModal {...mockProps} />);
    
    // Set adjustment that would make stock negative
    const adjustmentInput = screen.getByDisplayValue('0');
    fireEvent.change(adjustmentInput, { target: { value: '-150' } });
    
    // Set reason
    const reasonSelect = screen.getByDisplayValue('');
    fireEvent.change(reasonSelect, { target: { value: 'Inventory Count Correction' } });
    
    // Try to submit
    const submitButton = screen.getByText('Apply Adjustments');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/New quantity cannot be negative/)).toBeInTheDocument();
    });
  });

  it('validates available quantity would not go negative', async () => {
    render(<StockAdjustmentModal {...mockProps} />);
    
    // Set adjustment that would make available quantity negative
    const adjustmentInput = screen.getByDisplayValue('0');
    fireEvent.change(adjustmentInput, { target: { value: '-95' } }); // Available is 90, so -95 would be negative
    
    // Set reason
    const reasonSelect = screen.getByDisplayValue('');
    fireEvent.change(reasonSelect, { target: { value: 'Inventory Count Correction' } });
    
    // Try to submit
    const submitButton = screen.getByText('Apply Adjustments');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Adjustment would result in negative available quantity/)).toBeInTheDocument();
    });
  });

  it('submits single adjustment successfully', async () => {
    const mockAdjustStock = inventoryManagementApi.adjustStock as jest.MockedFunction<typeof inventoryManagementApi.adjustStock>;
    mockAdjustStock.mockResolvedValue({ success: true, data: mockInventoryItem });
    
    render(<StockAdjustmentModal {...mockProps} />);
    
    // Set adjustment amount
    const adjustmentInput = screen.getByDisplayValue('0');
    fireEvent.change(adjustmentInput, { target: { value: '10' } });
    
    // Set reason
    const reasonSelect = screen.getByDisplayValue('');
    fireEvent.change(reasonSelect, { target: { value: 'Inventory Count Correction' } });
    
    // Submit
    const submitButton = screen.getByText('Apply Adjustments');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockAdjustStock).toHaveBeenCalledWith('1', {
        adjustment: 10,
        reason: 'Inventory Count Correction',
      });
      expect(mockProps.onSuccess).toHaveBeenCalled();
      expect(mockProps.onClose).toHaveBeenCalled();
    });
  });

  it('submits bulk adjustment successfully', async () => {
    const mockBulkAdjustStock = inventoryManagementApi.bulkAdjustStock as jest.MockedFunction<typeof inventoryManagementApi.bulkAdjustStock>;
    mockBulkAdjustStock.mockResolvedValue({ success: true, data: [mockInventoryItem] });
    
    const bulkProps = {
      ...mockProps,
      inventory: [mockInventoryItem, { ...mockInventoryItem, id: '2' }],
    };
    
    render(<StockAdjustmentModal {...bulkProps} />);
    
    // Set adjustment amounts for both items
    const adjustmentInputs = screen.getAllByDisplayValue('0');
    fireEvent.change(adjustmentInputs[0], { target: { value: '10' } });
    fireEvent.change(adjustmentInputs[1], { target: { value: '5' } });
    
    // Set reasons for both items
    const reasonSelects = screen.getAllByDisplayValue('');
    fireEvent.change(reasonSelects[0], { target: { value: 'Inventory Count Correction' } });
    fireEvent.change(reasonSelects[1], { target: { value: 'Damaged Goods' } });
    
    // Submit
    const submitButton = screen.getByText('Apply Adjustments');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockBulkAdjustStock).toHaveBeenCalledWith([
        {
          inventory_id: '1',
          adjustment: 10,
          reason: 'Inventory Count Correction',
        },
        {
          inventory_id: '2',
          adjustment: 5,
          reason: 'Damaged Goods',
        },
      ]);
      expect(mockProps.onSuccess).toHaveBeenCalled();
      expect(mockProps.onClose).toHaveBeenCalled();
    });
  });

  it('handles custom reason input', async () => {
    const mockAdjustStock = inventoryManagementApi.adjustStock as jest.MockedFunction<typeof inventoryManagementApi.adjustStock>;
    mockAdjustStock.mockResolvedValue({ success: true, data: mockInventoryItem });
    
    render(<StockAdjustmentModal {...mockProps} />);
    
    // Set adjustment amount
    const adjustmentInput = screen.getByDisplayValue('0');
    fireEvent.change(adjustmentInput, { target: { value: '10' } });
    
    // Set reason to "Other"
    const reasonSelect = screen.getByDisplayValue('');
    fireEvent.change(reasonSelect, { target: { value: 'Other' } });
    
    // Custom reason input should appear
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Please specify the reason for adjustment')).toBeInTheDocument();
    });
    
    // Set custom reason
    const customReasonInput = screen.getByPlaceholderText('Please specify the reason for adjustment');
    fireEvent.change(customReasonInput, { target: { value: 'Custom test reason' } });
    
    // Submit
    const submitButton = screen.getByText('Apply Adjustments');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockAdjustStock).toHaveBeenCalledWith('1', {
        adjustment: 10,
        reason: 'Custom test reason',
      });
    });
  });

  it('handles API errors gracefully', async () => {
    const mockAdjustStock = inventoryManagementApi.adjustStock as jest.MockedFunction<typeof inventoryManagementApi.adjustStock>;
    mockAdjustStock.mockResolvedValue({
      success: false,
      error: {
        message: 'API Error occurred',
        code: 'api_error',
        status_code: 500
      }
    });
    
    render(<StockAdjustmentModal {...mockProps} />);
    
    // Set adjustment amount
    const adjustmentInput = screen.getByDisplayValue('0');
    fireEvent.change(adjustmentInput, { target: { value: '10' } });
    
    // Set reason
    const reasonSelect = screen.getByDisplayValue('');
    fireEvent.change(reasonSelect, { target: { value: 'Inventory Count Correction' } });
    
    // Submit
    const submitButton = screen.getByText('Apply Adjustments');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('API Error occurred')).toBeInTheDocument();
    });
  });

  it('closes modal when close button is clicked', () => {
    render(<StockAdjustmentModal {...mockProps} />);
    
    const closeButton = screen.getByRole('button', { name: '' }); // X icon button
    fireEvent.click(closeButton);
    
    expect(mockProps.onClose).toHaveBeenCalled();
  });
});