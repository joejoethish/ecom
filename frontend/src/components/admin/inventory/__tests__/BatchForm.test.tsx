import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import BatchForm from '../BatchForm';
import { inventoryManagementApi } from '@/services/inventoryManagementApi';

// Mock the API service
jest.mock('@/services/inventoryManagementApi', () => ({
  inventoryManagementApi: {
    getWarehouses: jest.fn(),
    searchProductVariants: jest.fn(),
    createBatch: jest.fn(),
    updateBatch: jest.fn(),
  },
}));

// Mock validation utilities
jest.mock('@/utils/validation', () => ({
  validateRequired: jest.fn((value: string, fieldName: string) => {
    if (!value || value.trim().length === 0) {
      return `${fieldName} is required`;
    }
    return null;
  }),
  validateForm: jest.fn((data: Record<string, any>, rules: Record<string, (value: any) => string | null>) => {
    const errors: Record<string, string> = {};
    Object.keys(rules).forEach(field => {
      const error = rules[field](data[field]);
      if (error) {
        errors[field] = error;
      }
    });
    return errors;
  }),
}));

const mockWarehouses = [
  {
    id: '1',
    name: 'Main Warehouse',
    code: 'MW001',
    address: '123 Main St',
    city: 'New York',
    state: 'NY',
    postal_code: '10001',
    country: 'USA',
    phone: '+1234567890',
    email: 'warehouse@example.com',
    manager: 'John Doe',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const mockProductVariants = [
  {
    id: '1',
    sku: 'TEST-001',
    product: {
      id: '1',
      name: 'Test Product',
    },
    attributes: { color: 'red', size: 'M' },
  },
];

const mockBatch = {
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
};

describe('BatchForm', () => {
  const mockOnClose = jest.fn();
  const mockOnSave = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (inventoryManagementApi.getWarehouses as jest.Mock).mockResolvedValue({
      success: true,
      data: mockWarehouses,
    });
    (inventoryManagementApi.searchProductVariants as jest.Mock).mockResolvedValue({
      success: true,
      data: mockProductVariants,
    });
  });

  it('renders create form correctly', async () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText('Add Product Batch')).toBeInTheDocument();
    expect(screen.getByLabelText(/Batch Number/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Product Variant/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Warehouse/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Quantity/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Manufacturing Date/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Expiration Date/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Supplier/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Cost per Unit/)).toBeInTheDocument();
    expect(screen.getByText('Create Batch')).toBeInTheDocument();

    await waitFor(() => {
      expect(inventoryManagementApi.getWarehouses).toHaveBeenCalled();
    });
  });

  it('renders edit form correctly', async () => {
    render(
      <BatchForm
        batch={mockBatch}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText('Edit Product Batch')).toBeInTheDocument();
    expect(screen.getByText('Update Batch')).toBeInTheDocument();
    
    // Check that form is pre-populated
    expect(screen.getByDisplayValue('BATCH-001')).toBeInTheDocument();
    expect(screen.getByDisplayValue('100')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Supplier')).toBeInTheDocument();
    expect(screen.getByDisplayValue('10.5')).toBeInTheDocument();

    await waitFor(() => {
      expect(inventoryManagementApi.getWarehouses).toHaveBeenCalled();
    });
  });

  it('validates required fields', async () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Try to submit without filling required fields
    const submitButton = screen.getByText('Create Batch');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Batch number is required')).toBeInTheDocument();
      expect(screen.getByText('Product variant is required')).toBeInTheDocument();
      expect(screen.getByText('Warehouse is required')).toBeInTheDocument();
      expect(screen.getByText('Quantity is required')).toBeInTheDocument();
      expect(screen.getByText('Manufacturing date is required')).toBeInTheDocument();
      expect(screen.getByText('Expiration date is required')).toBeInTheDocument();
      expect(screen.getByText('Supplier is required')).toBeInTheDocument();
      expect(screen.getByText('Cost per unit is required')).toBeInTheDocument();
    });

    expect(inventoryManagementApi.createBatch).not.toHaveBeenCalled();
  });

  it('validates numeric fields', async () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Fill in invalid numeric values
    const quantityInput = screen.getByLabelText(/Quantity/);
    const costInput = screen.getByLabelText(/Cost per Unit/);

    fireEvent.change(quantityInput, { target: { value: '-5' } });
    fireEvent.change(costInput, { target: { value: 'invalid' } });

    const submitButton = screen.getByText('Create Batch');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Quantity must be a positive number')).toBeInTheDocument();
      expect(screen.getByText('Cost per unit must be a non-negative number')).toBeInTheDocument();
    });
  });

  it('validates date fields', async () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Set manufacturing date in the future
    const manufacturingDateInput = screen.getByLabelText(/Manufacturing Date/);
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 1);
    fireEvent.change(manufacturingDateInput, { 
      target: { value: futureDate.toISOString().split('T')[0] } 
    });

    // Set expiration date in the past
    const expirationDateInput = screen.getByLabelText(/Expiration Date/);
    const pastDate = new Date();
    pastDate.setDate(pastDate.getDate() - 1);
    fireEvent.change(expirationDateInput, { 
      target: { value: pastDate.toISOString().split('T')[0] } 
    });

    const submitButton = screen.getByText('Create Batch');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Manufacturing date cannot be in the future')).toBeInTheDocument();
      expect(screen.getByText('Expiration date must be in the future')).toBeInTheDocument();
    });
  });

  it('validates expiration date is after manufacturing date', async () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Set manufacturing date after expiration date
    const manufacturingDateInput = screen.getByLabelText(/Manufacturing Date/);
    const expirationDateInput = screen.getByLabelText(/Expiration Date/);
    
    const today = new Date();
    const tomorrow = new Date();
    tomorrow.setDate(today.getDate() + 1);
    
    fireEvent.change(manufacturingDateInput, { 
      target: { value: tomorrow.toISOString().split('T')[0] } 
    });
    fireEvent.change(expirationDateInput, { 
      target: { value: today.toISOString().split('T')[0] } 
    });

    const submitButton = screen.getByText('Create Batch');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Expiration date must be after manufacturing date')).toBeInTheDocument();
    });
  });

  it('handles product variant search', async () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const productSearchInput = screen.getByLabelText(/Product Variant/);
    
    // Focus on input to show search dropdown
    fireEvent.focus(productSearchInput);
    fireEvent.change(productSearchInput, { target: { value: 'Test' } });

    await waitFor(() => {
      expect(inventoryManagementApi.searchProductVariants).toHaveBeenCalledWith('Test');
      expect(screen.getByText('Test Product')).toBeInTheDocument();
      expect(screen.getByText('SKU: TEST-001')).toBeInTheDocument();
    });
  });

  it('selects product variant from search results', async () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const productSearchInput = screen.getByLabelText(/Product Variant/);
    
    // Focus and search
    fireEvent.focus(productSearchInput);
    fireEvent.change(productSearchInput, { target: { value: 'Test' } });

    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Click on search result
    const productOption = screen.getByText('Test Product');
    fireEvent.click(productOption);

    // Should show selected product
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('SKU: TEST-001')).toBeInTheDocument();
  });

  it('creates batch successfully', async () => {
    (inventoryManagementApi.createBatch as jest.Mock).mockResolvedValue({
      success: true,
      data: mockBatch,
    });

    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Wait for warehouses to load
    await waitFor(() => {
      expect(screen.getByText('Main Warehouse (MW001) - New York')).toBeInTheDocument();
    });

    // Fill in the form
    fireEvent.change(screen.getByLabelText(/Batch Number/), { 
      target: { value: 'BATCH-001' } 
    });

    // Select product variant
    const productSearchInput = screen.getByLabelText(/Product Variant/);
    fireEvent.focus(productSearchInput);
    fireEvent.change(productSearchInput, { target: { value: 'Test' } });

    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Product'));

    // Select warehouse
    const warehouseSelect = screen.getByLabelText(/Warehouse/);
    fireEvent.change(warehouseSelect, { target: { value: '1' } });

    // Fill in other fields
    fireEvent.change(screen.getByLabelText(/Quantity/), { target: { value: '100' } });
    fireEvent.change(screen.getByLabelText(/Manufacturing Date/), { 
      target: { value: '2024-01-01' } 
    });
    fireEvent.change(screen.getByLabelText(/Expiration Date/), { 
      target: { value: '2024-12-31' } 
    });
    fireEvent.change(screen.getByLabelText(/Supplier/), { 
      target: { value: 'Test Supplier' } 
    });
    fireEvent.change(screen.getByLabelText(/Cost per Unit/), { 
      target: { value: '10.50' } 
    });

    // Submit form
    const submitButton = screen.getByText('Create Batch');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(inventoryManagementApi.createBatch).toHaveBeenCalledWith({
        batch_number: 'BATCH-001',
        product_variant: '1',
        warehouse: '1',
        quantity: 100,
        manufacturing_date: '2024-01-01',
        expiration_date: '2024-12-31',
        supplier: 'Test Supplier',
        cost_per_unit: 10.50,
      });
      expect(mockOnSave).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('updates batch successfully', async () => {
    (inventoryManagementApi.updateBatch as jest.Mock).mockResolvedValue({
      success: true,
      data: mockBatch,
    });

    render(
      <BatchForm
        batch={mockBatch}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Wait for warehouses to load
    await waitFor(() => {
      expect(screen.getByText('Main Warehouse (MW001) - New York')).toBeInTheDocument();
    });

    // Update quantity
    const quantityInput = screen.getByDisplayValue('100');
    fireEvent.change(quantityInput, { target: { value: '150' } });

    // Submit form
    const submitButton = screen.getByText('Update Batch');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(inventoryManagementApi.updateBatch).toHaveBeenCalledWith('1', {
        batch_number: 'BATCH-001',
        quantity: 150,
        expiration_date: '2024-12-31',
        manufacturing_date: '2024-01-01',
        supplier: 'Test Supplier',
        cost_per_unit: 10.50,
      });
      expect(mockOnSave).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('disables product variant and warehouse fields when editing', async () => {
    render(
      <BatchForm
        batch={mockBatch}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      const productSearchInput = screen.getByLabelText(/Product Variant/);
      const warehouseSelect = screen.getByLabelText(/Warehouse/);
      
      expect(productSearchInput).toBeDisabled();
      expect(warehouseSelect).toBeDisabled();
    });
  });

  it('shows expiring soon warning', async () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Set expiration date within 30 days
    const expirationDateInput = screen.getByLabelText(/Expiration Date/);
    const soonDate = new Date();
    soonDate.setDate(soonDate.getDate() + 15); // 15 days from now
    
    fireEvent.change(expirationDateInput, { 
      target: { value: soonDate.toISOString().split('T')[0] } 
    });

    await waitFor(() => {
      expect(screen.getByText('This batch expires within 30 days')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    (inventoryManagementApi.createBatch as jest.Mock).mockResolvedValue({
      success: false,
      error: { message: 'Batch number already exists' },
    });

    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Fill in valid form data
    fireEvent.change(screen.getByLabelText(/Batch Number/), { 
      target: { value: 'BATCH-001' } 
    });

    const productSearchInput = screen.getByLabelText(/Product Variant/);
    fireEvent.focus(productSearchInput);
    fireEvent.change(productSearchInput, { target: { value: 'Test' } });

    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Product'));

    const warehouseSelect = screen.getByLabelText(/Warehouse/);
    fireEvent.change(warehouseSelect, { target: { value: '1' } });

    fireEvent.change(screen.getByLabelText(/Quantity/), { target: { value: '100' } });
    fireEvent.change(screen.getByLabelText(/Manufacturing Date/), { 
      target: { value: '2024-01-01' } 
    });
    fireEvent.change(screen.getByLabelText(/Expiration Date/), { 
      target: { value: '2024-12-31' } 
    });
    fireEvent.change(screen.getByLabelText(/Supplier/), { 
      target: { value: 'Test Supplier' } 
    });
    fireEvent.change(screen.getByLabelText(/Cost per Unit/), { 
      target: { value: '10.50' } 
    });

    // Submit form
    const submitButton = screen.getByText('Create Batch');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Batch number already exists')).toBeInTheDocument();
    });

    expect(mockOnSave).not.toHaveBeenCalled();
    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it('closes form when cancel button is clicked', () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('closes form when X button is clicked', () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const closeButton = screen.getByRole('button', { name: '' }); // X button
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('clears field errors when user starts typing', async () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Submit to generate errors
    const submitButton = screen.getByText('Create Batch');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Batch number is required')).toBeInTheDocument();
    });

    // Start typing in batch number field
    const batchNumberInput = screen.getByLabelText(/Batch Number/);
    fireEvent.change(batchNumberInput, { target: { value: 'B' } });

    // Error should be cleared
    expect(screen.queryByText('Batch number is required')).not.toBeInTheDocument();
  });

  it('handles warehouse loading error', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    (inventoryManagementApi.getWarehouses as jest.Mock).mockRejectedValue(
      new Error('Failed to load warehouses')
    );

    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load warehouses. Please try again.')).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it('debounces product variant search', async () => {
    jest.useFakeTimers();

    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const productSearchInput = screen.getByLabelText(/Product Variant/);
    fireEvent.focus(productSearchInput);
    
    // Type multiple characters quickly
    fireEvent.change(productSearchInput, { target: { value: 'T' } });
    fireEvent.change(productSearchInput, { target: { value: 'Te' } });
    fireEvent.change(productSearchInput, { target: { value: 'Tes' } });
    fireEvent.change(productSearchInput, { target: { value: 'Test' } });

    // Fast-forward time to trigger debounced search
    jest.advanceTimersByTime(300);

    await waitFor(() => {
      // Should only call search once with the final value
      expect(inventoryManagementApi.searchProductVariants).toHaveBeenCalledTimes(1);
      expect(inventoryManagementApi.searchProductVariants).toHaveBeenCalledWith('Test');
    });

    jest.useRealTimers();
  });
});