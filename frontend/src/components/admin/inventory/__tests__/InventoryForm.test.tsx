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

const mockInventoryItem = {
  id: '1',
  product_variant: {
    id: '1',
    sku: 'TEST-001',
    product: {
      id: '1',
      name: 'Test Product',
      images: [],
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

describe('InventoryForm', () => {
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
      <InventoryForm
        inventory={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText('Add Inventory')).toBeInTheDocument();
    expect(screen.getByLabelText(/Product Variant/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Warehouse/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Stock Quantity/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Reorder Level/)).toBeInTheDocument();
    expect(screen.getByText('Create Inventory')).toBeInTheDocument();

    await waitFor(() => {
      expect(inventoryManagementApi.getWarehouses).toHaveBeenCalled();
    });
  });

  it('renders edit form correctly', async () => {
    render(
      <InventoryForm
        inventory={mockInventoryItem}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText('Edit Inventory')).toBeInTheDocument();
    expect(screen.getByText('Update Inventory')).toBeInTheDocument();
    
    // Check that form is pre-populated
    expect(screen.getByDisplayValue('100')).toBeInTheDocument(); // stock_quantity
    expect(screen.getByDisplayValue('20')).toBeInTheDocument(); // reorder_level

    await waitFor(() => {
      expect(inventoryManagementApi.getWarehouses).toHaveBeenCalled();
    });
  });

  it('validates required fields', async () => {
    render(
      <InventoryForm
        inventory={null}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Try to submit without filling required fields
    const submitButton = screen.getByText('Create Inventory');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Product variant is required')).toBeInTheDocument();
      expect(screen.getByText('Warehouse is required')).toBeInTheDocument();
      expect(screen.getByText('Stock quantity is required')).toBeInTheDocument();
      expect(screen.getByText('Reorder level is required')).toBeInTheDocument();
    });

    expect(inventoryManagementApi.createInventory).not.toHaveBeenCalled();
  });

  it('validates numeric fields', async () => {
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

    fireEvent.change(stockQuantityInput, { target: { value: '-5' } });
    fireEvent.change(reorderLevelInput, { target: { value: 'invalid' } });

    const submitButton = screen.getByText('Create Inventory');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Stock quantity must be a non-negative number')).toBeInTheDocument();
      expect(screen.getByText('Reorder level must be a non-negative number')).toBeInTheDocument();
    });
  });

  it('creates inventory successfully', async () => {
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
      expect(screen.getByText('Main Warehouse (MW001) - New York')).toBeInTheDocument();
    });

    // Fill in the form
    const productSearchInput = screen.getByLabelText(/Product Variant/);
    fireEvent.change(productSearchInput, { target: { value: 'Test' } });
    fireEvent.focus(productSearchInput);

    // Wait for search results and select product
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Product'));

    // Select warehouse
    const warehouseSelect = screen.getByLabelText(/Warehouse/);
    fireEvent.change(warehouseSelect, { target: { value: '1' } });

    // Fill in quantities
    const stockQuantityInput = screen.getByLabelText(/Stock Quantity/);
    const reorderLevelInput = screen.getByLabelText(/Reorder Level/);
    
    fireEvent.change(stockQuantityInput, { target: { value: '100' } });
    fireEvent.change(reorderLevelInput, { target: { value: '20' } });

    // Submit form
    const submitButton = screen.getByText('Create Inventory');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(inventoryManagementApi.createInventory).toHaveBeenCalledWith({
        product_variant: '1',
        warehouse: '1',
        stock_quantity: 100,
        reorder_level: 20,
      });
      expect(mockOnSave).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('updates inventory successfully', async () => {
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
      expect(screen.getByText('Main Warehouse (MW001) - New York')).toBeInTheDocument();
    });

    // Update quantities
    const stockQuantityInput = screen.getByDisplayValue('100');
    const reorderLevelInput = screen.getByDisplayValue('20');
    
    fireEvent.change(stockQuantityInput, { target: { value: '150' } });
    fireEvent.change(reorderLevelInput, { target: { value: '25' } });

    // Submit form
    const submitButton = screen.getByText('Update Inventory');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(inventoryManagementApi.updateInventory).toHaveBeenCalledWith('1', {
        stock_quantity: 150,
        reorder_level: 25,
        warehouse: '1',
      });
      expect(mockOnSave).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('handles API errors gracefully', async () => {
    (inventoryManagementApi.createInventory as jest.Mock).mockResolvedValue({
      success: false,
      error: { message: 'Product variant already exists in this warehouse' },
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
    fireEvent.change(productSearchInput, { target: { value: 'Test' } });
    fireEvent.focus(productSearchInput);

    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Product'));

    const warehouseSelect = screen.getByLabelText(/Warehouse/);
    fireEvent.change(warehouseSelect, { target: { value: '1' } });

    const stockQuantityInput = screen.getByLabelText(/Stock Quantity/);
    const reorderLevelInput = screen.getByLabelText(/Reorder Level/);
    
    fireEvent.change(stockQuantityInput, { target: { value: '100' } });
    fireEvent.change(reorderLevelInput, { target: { value: '20' } });

    // Submit form
    const submitButton = screen.getByText('Create Inventory');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Product variant already exists in this warehouse')).toBeInTheDocument();
    });

    expect(mockOnSave).not.toHaveBeenCalled();
    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it('closes form when cancel button is clicked', () => {
    render(
      <InventoryForm
        inventory={null}
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