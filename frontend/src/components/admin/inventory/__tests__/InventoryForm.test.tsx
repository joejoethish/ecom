import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import InventoryForm from '../InventoryForm';
import { inventoryManagementApi } from '@/services/inventoryManagementApi';

// Mock the API service
jest.mock('@/services/inventoryManagementApi', () => ({
  inventoryManagementApi: {
    getWarehouses: jest.fn(),
    searchProductVariants: jest.fn(),
    createInventory: jest.fn(),
    updateInventory: jest.fn(),
  },
}));

// Mock the validation utilities
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

const mockInventoryItem = {
  id: &apos;1&apos;,
  product_variant: {
    id: &apos;1&apos;,
    sku: &apos;TEST-001&apos;,
    product: {
      id: &apos;1&apos;,
      name: &apos;Test Product&apos;,
      images: [],
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

describe(&apos;InventoryForm&apos;, () => {
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
      <InventoryForm
        inventory={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText(&apos;Add Inventory&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(/Product Variant/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Warehouse/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Stock Quantity/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Reorder Level/)).toBeInTheDocument();
    expect(screen.getByText(&apos;Create Inventory&apos;)).toBeInTheDocument();

    await waitFor(() => {
      expect(inventoryManagementApi.getWarehouses).toHaveBeenCalled();
    });
  });

  it(&apos;renders edit form correctly&apos;, async () => {
    render(
      <InventoryForm
        inventory={mockInventoryItem}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText(&apos;Edit Inventory&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Update Inventory&apos;)).toBeInTheDocument();
    
    // Check that form is pre-populated
    expect(screen.getByDisplayValue(&apos;100&apos;)).toBeInTheDocument(); // stock_quantity
    expect(screen.getByDisplayValue(&apos;20&apos;)).toBeInTheDocument(); // reorder_level

    await waitFor(() => {
      expect(inventoryManagementApi.getWarehouses).toHaveBeenCalled();
    });
  });

  it(&apos;validates required fields&apos;, async () => {
    render(
      <InventoryForm
        inventory={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Try to submit without filling required fields
    const submitButton = screen.getByText(&apos;Create Inventory&apos;);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Product variant is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Warehouse is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Stock quantity is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Reorder level is required&apos;)).toBeInTheDocument();
    });

    expect(inventoryManagementApi.createInventory).not.toHaveBeenCalled();
  });

  it(&apos;validates numeric fields&apos;, async () => {
    render(
      <InventoryForm
        inventory={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Fill in invalid numeric values
    const stockQuantityInput = screen.getByLabelText(/Stock Quantity/);
    const reorderLevelInput = screen.getByLabelText(/Reorder Level/);

    fireEvent.change(stockQuantityInput, { target: { value: &apos;-5&apos; } });
    fireEvent.change(reorderLevelInput, { target: { value: &apos;invalid&apos; } });

    const submitButton = screen.getByText(&apos;Create Inventory&apos;);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Stock quantity must be a non-negative number&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Reorder level must be a non-negative number&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;creates inventory successfully&apos;, async () => {
    (inventoryManagementApi.createInventory as jest.Mock).mockResolvedValue({
      success: true,
      data: mockInventoryItem,
    });

    render(
      <InventoryForm
        inventory={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Wait for warehouses to load
    await waitFor(() => {
      expect(screen.getByText(&apos;Main Warehouse (MW001) - New York&apos;)).toBeInTheDocument();
    });

    // Fill in the form
    const productSearchInput = screen.getByLabelText(/Product Variant/);
    fireEvent.change(productSearchInput, { target: { value: &apos;Test&apos; } });
    fireEvent.focus(productSearchInput);

    // Wait for search results and select product
    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText(&apos;Test Product&apos;));

    // Select warehouse
    const warehouseSelect = screen.getByLabelText(/Warehouse/);
    fireEvent.change(warehouseSelect, { target: { value: &apos;1&apos; } });

    // Fill in quantities
    const stockQuantityInput = screen.getByLabelText(/Stock Quantity/);
    const reorderLevelInput = screen.getByLabelText(/Reorder Level/);
    
    fireEvent.change(stockQuantityInput, { target: { value: &apos;100&apos; } });
    fireEvent.change(reorderLevelInput, { target: { value: &apos;20&apos; } });

    // Submit form
    const submitButton = screen.getByText(&apos;Create Inventory&apos;);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(inventoryManagementApi.createInventory).toHaveBeenCalledWith({
        product_variant: &apos;1&apos;,
        warehouse: &apos;1&apos;,
        stock_quantity: 100,
        reorder_level: 20,
      });
      expect(mockOnSave).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it(&apos;updates inventory successfully&apos;, async () => {
    (inventoryManagementApi.updateInventory as jest.Mock).mockResolvedValue({
      success: true,
      data: mockInventoryItem,
    });

    render(
      <InventoryForm
        inventory={mockInventoryItem}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Wait for warehouses to load
    await waitFor(() => {
      expect(screen.getByText(&apos;Main Warehouse (MW001) - New York&apos;)).toBeInTheDocument();
    });

    // Update quantities
    const stockQuantityInput = screen.getByDisplayValue(&apos;100&apos;);
    const reorderLevelInput = screen.getByDisplayValue(&apos;20&apos;);
    
    fireEvent.change(stockQuantityInput, { target: { value: &apos;150&apos; } });
    fireEvent.change(reorderLevelInput, { target: { value: &apos;25&apos; } });

    // Submit form
    const submitButton = screen.getByText(&apos;Update Inventory&apos;);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(inventoryManagementApi.updateInventory).toHaveBeenCalledWith(&apos;1&apos;, {
        stock_quantity: 150,
        reorder_level: 25,
        warehouse: &apos;1&apos;,
      });
      expect(mockOnSave).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it(&apos;handles API errors gracefully&apos;, async () => {
    (inventoryManagementApi.createInventory as jest.Mock).mockResolvedValue({
      success: false,
      error: { message: &apos;Product variant already exists in this warehouse&apos; },
    });

    render(
      <InventoryForm
        inventory={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Fill in valid form data
    const productSearchInput = screen.getByLabelText(/Product Variant/);
    fireEvent.change(productSearchInput, { target: { value: &apos;Test&apos; } });
    fireEvent.focus(productSearchInput);

    await waitFor(() => {
      expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText(&apos;Test Product&apos;));

    const warehouseSelect = screen.getByLabelText(/Warehouse/);
    fireEvent.change(warehouseSelect, { target: { value: &apos;1&apos; } });

    const stockQuantityInput = screen.getByLabelText(/Stock Quantity/);
    const reorderLevelInput = screen.getByLabelText(/Reorder Level/);
    
    fireEvent.change(stockQuantityInput, { target: { value: &apos;100&apos; } });
    fireEvent.change(reorderLevelInput, { target: { value: &apos;20&apos; } });

    // Submit form
    const submitButton = screen.getByText(&apos;Create Inventory&apos;);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Product variant already exists in this warehouse&apos;)).toBeInTheDocument();
    });

    expect(mockOnSave).not.toHaveBeenCalled();
    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it(&apos;closes form when cancel button is clicked&apos;, () => {
    render(
      <InventoryForm
        inventory={null}
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
      <InventoryForm
        inventory={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const closeButton = screen.getByRole('button', { name: '' }); // X button
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });
});