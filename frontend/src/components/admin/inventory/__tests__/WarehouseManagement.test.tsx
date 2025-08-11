import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import WarehouseManagement from '../WarehouseManagement';
import { inventoryManagementApi } from '@/services/inventoryManagementApi';

// Mock the API service
jest.mock('@/services/inventoryManagementApi', () => ({
  inventoryManagementApi: {
    getWarehouses: jest.fn(),
    createWarehouse: jest.fn(),
    updateWarehouse: jest.fn(),
    deleteWarehouse: jest.fn(),
    getInventory: jest.fn(),
  },
}));

const mockWarehouses = [
  {
    id: &apos;1&apos;,
    name: &apos;Main Warehouse&apos;,
    code: &apos;WH001&apos;,
    address: &apos;123 Main St&apos;,
    city: &apos;New York&apos;,
    state: &apos;NY&apos;,
    postal_code: &apos;10001&apos;,
    country: &apos;USA&apos;,
    phone: &apos;+1-555-0123&apos;,
    email: &apos;main@warehouse.com&apos;,
    manager: &apos;John Doe&apos;,
    is_active: true,
    created_at: &apos;2024-01-01T00:00:00Z&apos;,
    updated_at: &apos;2024-01-01T00:00:00Z&apos;,
  },
  {
    id: &apos;2&apos;,
    name: &apos;Secondary Warehouse&apos;,
    code: &apos;WH002&apos;,
    address: &apos;456 Oak Ave&apos;,
    city: &apos;Los Angeles&apos;,
    state: &apos;CA&apos;,
    postal_code: &apos;90001&apos;,
    country: &apos;USA&apos;,
    phone: &apos;+1-555-0456&apos;,
    email: &apos;secondary@warehouse.com&apos;,
    manager: &apos;Jane Smith&apos;,
    is_active: false,
    created_at: &apos;2024-01-02T00:00:00Z&apos;,
    updated_at: &apos;2024-01-02T00:00:00Z&apos;,
  },
];

describe(&apos;WarehouseManagement&apos;, () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (inventoryManagementApi.getWarehouses as jest.Mock).mockResolvedValue({
      success: true,
      data: mockWarehouses,
    });
  });

  it(&apos;renders warehouse management header&apos;, async () => {
    render(<WarehouseManagement />);
    
    expect(screen.getByText(&apos;Warehouse Management&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Manage warehouse locations and their details&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Add Warehouse&apos;)).toBeInTheDocument();
  });

  it(&apos;displays loading state initially&apos;, () => {
    render(<WarehouseManagement />);
    
    // Check for loading spinner by class
    const loadingElement = document.querySelector(&apos;.animate-spin&apos;);
    expect(loadingElement).toBeInTheDocument();
  });

  it(&apos;displays warehouses after loading&apos;, async () => {
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Main Warehouse&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Code: WH001&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Secondary Warehouse&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Code: WH002&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;displays warehouse details correctly&apos;, async () => {
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      // Check first warehouse details
      expect(screen.getByText(&apos;123 Main St&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;New York, NY 10001&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;USA&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;+1-555-0123&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;main@warehouse.com&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Manager: John Doe&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Active&apos;)).toBeInTheDocument();
      
      // Check second warehouse details
      expect(screen.getByText(&apos;456 Oak Ave&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Los Angeles, CA 90001&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;secondary@warehouse.com&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Manager: Jane Smith&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Inactive&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;opens warehouse form when Add Warehouse is clicked&apos;, async () => {
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Main Warehouse&apos;)).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText(&apos;Add Warehouse&apos;));
    
    expect(screen.getByText(&apos;Add Warehouse&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(&apos;Warehouse Name *&apos;)).toBeInTheDocument();
  });

  it(&apos;opens warehouse form for editing when edit button is clicked&apos;, async () => {
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Main Warehouse&apos;)).toBeInTheDocument();
    });
    
    const editButtons = screen.getAllByRole(&apos;button&apos;);
    const editButton = editButtons.find(button => 
      button.querySelector(&apos;svg&apos;) && button.getAttribute(&apos;class&apos;)?.includes(&apos;ghost&apos;)
    );
    
    if (editButton) {
      fireEvent.click(editButton);
      
      await waitFor(() => {
        expect(screen.getByText(&apos;Edit Warehouse&apos;)).toBeInTheDocument();
        expect(screen.getByDisplayValue(&apos;Main Warehouse&apos;)).toBeInTheDocument();
      });
    }
  });

  it(&apos;shows empty state when no warehouses exist&apos;, async () => {
    (inventoryManagementApi.getWarehouses as jest.Mock).mockResolvedValue({
      success: true,
      data: [],
    });
    
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;No warehouses found&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Get started by creating your first warehouse&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;handles delete warehouse with dependencies&apos;, async () => {
    // Mock inventory check to return items (has dependencies)
    (inventoryManagementApi.getInventory as jest.Mock).mockResolvedValue({
      success: true,
      data: { count: 5, results: [] },
    });
    
    // Mock window.alert
    const alertSpy = jest.spyOn(window, &apos;alert&apos;).mockImplementation(() => {});
    
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Main Warehouse&apos;)).toBeInTheDocument();
    });
    
    const deleteButtons = screen.getAllByRole(&apos;button&apos;);
    const deleteButton = deleteButtons.find(button => 
      button.querySelector(&apos;svg&apos;) && button.getAttribute(&apos;class&apos;)?.includes(&apos;text-red-600&apos;)
    );
    
    if (deleteButton) {
      fireEvent.click(deleteButton);
      
      await waitFor(() => {
        expect(alertSpy).toHaveBeenCalledWith(
          expect.stringContaining(&apos;Cannot delete warehouse &quot;Main Warehouse&quot; because it has inventory items&apos;)
        );
      });
    }
    
    alertSpy.mockRestore();
  });

  it(&apos;handles delete warehouse without dependencies&apos;, async () => {
    // Mock inventory check to return no items (no dependencies)
    (inventoryManagementApi.getInventory as jest.Mock).mockResolvedValue({
      success: true,
      data: { count: 0, results: [] },
    });
    
    // Mock deleteWarehouse API call
    (inventoryManagementApi.deleteWarehouse as jest.Mock).mockResolvedValue({
      success: true,
    });
    
    // Mock window.confirm
    const confirmSpy = jest.spyOn(window, &apos;confirm&apos;).mockReturnValue(true);
    
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Main Warehouse&apos;)).toBeInTheDocument();
    });
    
    const deleteButtons = screen.getAllByRole(&apos;button&apos;);
    const deleteButton = deleteButtons.find(button => 
      button.querySelector(&apos;svg&apos;) && button.getAttribute(&apos;class&apos;)?.includes(&apos;text-red-600&apos;)
    );
    
    if (deleteButton) {
      fireEvent.click(deleteButton);
      
      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalledWith(
          expect.stringContaining(&apos;Are you sure you want to delete warehouse &quot;Main Warehouse&quot;?&apos;)
        );
        expect(inventoryManagementApi.deleteWarehouse).toHaveBeenCalledWith(&apos;1&apos;);
      });
    }
    
    confirmSpy.mockRestore();
  });
});

describe(&apos;WarehouseForm&apos;, () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (inventoryManagementApi.getWarehouses as jest.Mock).mockResolvedValue({
      success: true,
      data: mockWarehouses,
    });
  });

  it(&apos;validates required fields&apos;, async () => {
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Main Warehouse&apos;)).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText(&apos;Add Warehouse&apos;));
    
    // Try to submit empty form
    const submitButton = screen.getByText(&apos;Create Warehouse&apos;);
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Warehouse name is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Warehouse code is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Address is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;City is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;State is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Postal code is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Country is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Manager name is required&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;validates warehouse code uniqueness&apos;, async () => {
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Main Warehouse&apos;)).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText(&apos;Add Warehouse&apos;));
    
    // Fill form with duplicate warehouse code
    fireEvent.change(screen.getByLabelText(&apos;Warehouse Name *&apos;), {
      target: { value: &apos;Test Warehouse&apos; },
    });
    fireEvent.change(screen.getByLabelText(&apos;Warehouse Code *&apos;), {
      target: { value: &apos;WH001&apos; }, // This code already exists
    });
    
    const submitButton = screen.getByText(&apos;Create Warehouse&apos;);
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Warehouse code already exists. Please choose a different code.&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;validates email format&apos;, async () => {
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Main Warehouse&apos;)).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText(&apos;Add Warehouse&apos;));
    
    // Fill email with invalid format
    fireEvent.change(screen.getByLabelText(&apos;Email Address&apos;), {
      target: { value: &apos;invalid-email&apos; },
    });
    
    const submitButton = screen.getByText(&apos;Create Warehouse&apos;);
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Please enter a valid email address&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;creates warehouse successfully&apos;, async () => {
    (inventoryManagementApi.createWarehouse as jest.Mock).mockResolvedValue({
      success: true,
      data: { id: &apos;3&apos;, ...mockWarehouses[0] },
    });
    
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Main Warehouse')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Add Warehouse'));
    
    // Fill form with valid data
    fireEvent.change(screen.getByLabelText('Warehouse Name *'), {
      target: { value: 'New Warehouse' },
    });
    fireEvent.change(screen.getByLabelText('Warehouse Code *'), {
      target: { value: 'WH003' },
    });
    fireEvent.change(screen.getByLabelText('Street Address *'), {
      target: { value: '789 Pine St' },
    });
    fireEvent.change(screen.getByLabelText('City *'), {
      target: { value: 'Chicago' },
    });
    fireEvent.change(screen.getByLabelText('State/Province *'), {
      target: { value: 'IL' },
    });
    fireEvent.change(screen.getByLabelText('Postal Code *'), {
      target: { value: '60601' },
    });
    fireEvent.change(screen.getByLabelText('Country *'), {
      target: { value: 'USA' },
    });
    fireEvent.change(screen.getByLabelText('Manager Name *'), {
      target: { value: 'Bob Johnson' },
    });
    
    const submitButton = screen.getByText('Create Warehouse');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(inventoryManagementApi.createWarehouse).toHaveBeenCalledWith({
        name: 'New Warehouse',
        code: 'WH003',
        address: '789 Pine St',
        city: 'Chicago',
        state: 'IL',
        postal_code: '60601',
        country: 'USA',
        phone: '',
        email: '',
        manager: 'Bob Johnson',
        is_active: true,
      });
    });
  });
});