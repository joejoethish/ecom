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
jest.mock(&apos;@/utils/validation&apos;, () => ({
  validateRequired: jest.fn((value: string, fieldName: string) => {
    if (!value || value.trim().length === 0) {
      return `${fieldName} is required`;
    }
    return null;
  }),
  validateForm: jest.fn((data: Record<string, unknown>, rules: Record<string, (value: unknown) => string | null>) => {
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
    id: &apos;1&apos;,
    name: &apos;Main Warehouse&apos;,
    code: &apos;MW001&apos;,
    address: &apos;123 Main St&apos;,
    city: &apos;New York&apos;,
    state: &apos;NY&apos;,
    postal_code: &apos;10001&apos;,
    country: &apos;USA&apos;,
    phone: &apos;+1234567890&apos;,
    email: &apos;warehouse@example.com&apos;,
    manager: &apos;John Doe&apos;,
    is_active: true,
    created_at: &apos;2024-01-01T00:00:00Z&apos;,
    updated_at: &apos;2024-01-01T00:00:00Z&apos;,
  },
];

const mockProductVariants = [
  {
    id: &apos;1&apos;,
    sku: &apos;TEST-001&apos;,
    product: {
      id: &apos;1&apos;,
      name: &apos;Test Product&apos;,
    },
    attributes: { color: &apos;red&apos;, size: &apos;M&apos; },
  },
];

const mockBatch = {
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
};

describe(&apos;BatchForm&apos;, () => {
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

  it(&apos;renders create form correctly&apos;, async () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText(&apos;Add Product Batch&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(/Batch Number/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Product Variant/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Warehouse/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Quantity/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Manufacturing Date/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Expiration Date/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Supplier/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Cost per Unit/)).toBeInTheDocument();
    expect(screen.getByText(&apos;Create Batch&apos;)).toBeInTheDocument();

    await waitFor(() => {
      expect(inventoryManagementApi.getWarehouses).toHaveBeenCalled();
    });
  });

  it(&apos;renders edit form correctly&apos;, async () => {
    render(
      <BatchForm
        batch={mockBatch}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText(&apos;Edit Product Batch&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Update Batch&apos;)).toBeInTheDocument();
    
    // Check that form is pre-populated
    expect(screen.getByDisplayValue(&apos;BATCH-001&apos;)).toBeInTheDocument();
    expect(screen.getByDisplayValue(&apos;100&apos;)).toBeInTheDocument();
    expect(screen.getByDisplayValue(&apos;Test Supplier&apos;)).toBeInTheDocument();
    expect(screen.getByDisplayValue(&apos;10.5&apos;)).toBeInTheDocument();

    await waitFor(() => {
      expect(inventoryManagementApi.getWarehouses).toHaveBeenCalled();
    });
  });

  it(&apos;validates required fields&apos;, async () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Try to submit without filling required fields
    const submitButton = screen.getByText(&apos;Create Batch&apos;);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Batch number is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Product variant is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Warehouse is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Quantity is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Manufacturing date is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Expiration date is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Supplier is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Cost per unit is required&apos;)).toBeInTheDocument();
    });

    expect(inventoryManagementApi.createBatch).not.toHaveBeenCalled();
  });

  it(&apos;validates numeric fields&apos;, async () => {
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

    fireEvent.change(quantityInput, { target: { value: &apos;-5&apos; } });
    fireEvent.change(costInput, { target: { value: &apos;invalid&apos; } });

    const submitButton = screen.getByText(&apos;Create Batch&apos;);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Quantity must be a positive number&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Cost per unit must be a non-negative number&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;validates date fields&apos;, async () => {
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
      target: { value: futureDate.toISOString().split(&apos;T&apos;)[0] } 
    });

    // Set expiration date in the past
    const expirationDateInput = screen.getByLabelText(/Expiration Date/);
    const pastDate = new Date();
    pastDate.setDate(pastDate.getDate() - 1);
    fireEvent.change(expirationDateInput, { 
      target: { value: pastDate.toISOString().split(&apos;T&apos;)[0] } 
    });

    const submitButton = screen.getByText(&apos;Create Batch&apos;);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Manufacturing date cannot be in the future&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Expiration date must be in the future&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;validates expiration date is after manufacturing date&apos;, async () => {
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
      target: { value: tomorrow.toISOString().split(&apos;T&apos;)[0] } 
    });
    fireEvent.change(expirationDateInput, { 
      target: { value: today.toISOString().split(&apos;T&apos;)[0] } 
    });

    const submitButton = screen.getByText(&apos;Create Batch&apos;);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Expiration date must be after manufacturing date&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;handles product variant search&apos;, async () => {
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
    fireEvent.change(productSearchInput, { target: { value: &apos;Test&apos; } });

    await waitFor(() => {
      expect(inventoryManagementApi.searchProductVariants).toHaveBeenCalledWith(&apos;Test&apos;);
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;SKU: TEST-001&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;selects product variant from search results&apos;, async () => {
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
    fireEvent.change(productSearchInput, { target: { value: &apos;Test&apos; } });

    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });

    // Click on search result
    const productOption = screen.getByText(&apos;Test Product&apos;);
    fireEvent.click(productOption);

    // Should show selected product
    expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;SKU: TEST-001&apos;)).toBeInTheDocument();
  });

  it(&apos;creates batch successfully&apos;, async () => {
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
      expect(screen.getByText(&apos;Main Warehouse (MW001) - New York&apos;)).toBeInTheDocument();
    });

    // Fill in the form
    fireEvent.change(screen.getByLabelText(/Batch Number/), { 
      target: { value: &apos;BATCH-001&apos; } 
    });

    // Select product variant
    const productSearchInput = screen.getByLabelText(/Product Variant/);
    fireEvent.focus(productSearchInput);
    fireEvent.change(productSearchInput, { target: { value: &apos;Test&apos; } });

    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText(&apos;Test Product&apos;));

    // Select warehouse
    const warehouseSelect = screen.getByLabelText(/Warehouse/);
    fireEvent.change(warehouseSelect, { target: { value: &apos;1&apos; } });

    // Fill in other fields
    fireEvent.change(screen.getByLabelText(/Quantity/), { target: { value: &apos;100&apos; } });
    fireEvent.change(screen.getByLabelText(/Manufacturing Date/), { 
      target: { value: &apos;2024-01-01&apos; } 
    });
    fireEvent.change(screen.getByLabelText(/Expiration Date/), { 
      target: { value: &apos;2024-12-31&apos; } 
    });
    fireEvent.change(screen.getByLabelText(/Supplier/), { 
      target: { value: &apos;Test Supplier&apos; } 
    });
    fireEvent.change(screen.getByLabelText(/Cost per Unit/), { 
      target: { value: &apos;10.50&apos; } 
    });

    // Submit form
    const submitButton = screen.getByText(&apos;Create Batch&apos;);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(inventoryManagementApi.createBatch).toHaveBeenCalledWith({
        batch_number: &apos;BATCH-001&apos;,
        product_variant: &apos;1&apos;,
        warehouse: &apos;1&apos;,
        quantity: 100,
        manufacturing_date: &apos;2024-01-01&apos;,
        expiration_date: &apos;2024-12-31&apos;,
        supplier: &apos;Test Supplier&apos;,
        cost_per_unit: 10.50,
      });
      expect(mockOnSave).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it(&apos;updates batch successfully&apos;, async () => {
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
      expect(screen.getByText(&apos;Main Warehouse (MW001) - New York&apos;)).toBeInTheDocument();
    });

    // Update quantity
    const quantityInput = screen.getByDisplayValue(&apos;100&apos;);
    fireEvent.change(quantityInput, { target: { value: &apos;150&apos; } });

    // Submit form
    const submitButton = screen.getByText(&apos;Update Batch&apos;);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(inventoryManagementApi.updateBatch).toHaveBeenCalledWith(&apos;1&apos;, {
        batch_number: &apos;BATCH-001&apos;,
        quantity: 150,
        expiration_date: &apos;2024-12-31&apos;,
        manufacturing_date: &apos;2024-01-01&apos;,
        supplier: &apos;Test Supplier&apos;,
        cost_per_unit: 10.50,
      });
      expect(mockOnSave).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it(&apos;disables product variant and warehouse fields when editing&apos;, async () => {
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

  it(&apos;shows expiring soon warning&apos;, async () => {
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
      target: { value: soonDate.toISOString().split(&apos;T&apos;)[0] } 
    });

    await waitFor(() => {
      expect(screen.getByText(&apos;This batch expires within 30 days&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;handles API errors gracefully&apos;, async () => {
    (inventoryManagementApi.createBatch as jest.Mock).mockResolvedValue({
      success: false,
      error: { message: &apos;Batch number already exists&apos; },
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
      target: { value: &apos;BATCH-001&apos; } 
    });

    const productSearchInput = screen.getByLabelText(/Product Variant/);
    fireEvent.focus(productSearchInput);
    fireEvent.change(productSearchInput, { target: { value: &apos;Test&apos; } });

    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText(&apos;Test Product&apos;));

    const warehouseSelect = screen.getByLabelText(/Warehouse/);
    fireEvent.change(warehouseSelect, { target: { value: &apos;1&apos; } });

    fireEvent.change(screen.getByLabelText(/Quantity/), { target: { value: &apos;100&apos; } });
    fireEvent.change(screen.getByLabelText(/Manufacturing Date/), { 
      target: { value: &apos;2024-01-01&apos; } 
    });
    fireEvent.change(screen.getByLabelText(/Expiration Date/), { 
      target: { value: &apos;2024-12-31&apos; } 
    });
    fireEvent.change(screen.getByLabelText(/Supplier/), { 
      target: { value: &apos;Test Supplier&apos; } 
    });
    fireEvent.change(screen.getByLabelText(/Cost per Unit/), { 
      target: { value: &apos;10.50&apos; } 
    });

    // Submit form
    const submitButton = screen.getByText(&apos;Create Batch&apos;);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Batch number already exists&apos;)).toBeInTheDocument();
    });

    expect(mockOnSave).not.toHaveBeenCalled();
    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it(&apos;closes form when cancel button is clicked&apos;, () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const cancelButton = screen.getByText(&apos;Cancel&apos;);
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it(&apos;closes form when X button is clicked&apos;, () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const closeButton = screen.getByRole(&apos;button&apos;, { name: &apos;&apos; }); // X button
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it(&apos;clears field errors when user starts typing&apos;, async () => {
    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Submit to generate errors
    const submitButton = screen.getByText(&apos;Create Batch&apos;);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Batch number is required&apos;)).toBeInTheDocument();
    });

    // Start typing in batch number field
    const batchNumberInput = screen.getByLabelText(/Batch Number/);
    fireEvent.change(batchNumberInput, { target: { value: &apos;B&apos; } });

    // Error should be cleared
    expect(screen.queryByText(&apos;Batch number is required&apos;)).not.toBeInTheDocument();
  });

  it(&apos;handles warehouse loading error&apos;, async () => {
    const consoleSpy = jest.spyOn(console, &apos;error&apos;).mockImplementation(() => {});
    (inventoryManagementApi.getWarehouses as jest.Mock).mockRejectedValue(
      new Error(&apos;Failed to load warehouses&apos;)
    );

    render(
      <BatchForm
        batch={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(&apos;Failed to load warehouses. Please try again.&apos;)).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it(&apos;debounces product variant search&apos;, async () => {
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