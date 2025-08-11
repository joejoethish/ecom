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
    id: '1',
    name: 'Main Warehouse',
    code: 'WH001',
    address: '123 Main St',
    city: 'New York',
    state: 'NY',
    postal_code: '10001',
    country: 'USA',
    phone: '+1-555-0123',
    email: 'main@warehouse.com',
    manager: 'John Doe',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: 'Secondary Warehouse',
    code: 'WH002',
    address: '456 Oak Ave',
    city: 'Los Angeles',
    state: 'CA',
    postal_code: '90001',
    country: 'USA',
    phone: '+1-555-0456',
    email: 'secondary@warehouse.com',
    manager: 'Jane Smith',
    is_active: false,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
];

describe('WarehouseManagement', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (inventoryManagementApi.getWarehouses as jest.Mock).mockResolvedValue({
      success: true,
      data: mockWarehouses,
    });
  });

  it('renders warehouse management header', async () => {
    render(<WarehouseManagement />);
    
    expect(screen.getByText('Warehouse Management')).toBeInTheDocument();
    expect(screen.getByText('Manage warehouse locations and their details')).toBeInTheDocument();
    expect(screen.getByText('Add Warehouse')).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    render(<WarehouseManagement />);
    
    // Check for loading spinner by class
    const loadingElement = document.querySelector('.animate-spin');
    expect(loadingElement).toBeInTheDocument();
  });

  it('displays warehouses after loading', async () => {
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Main Warehouse')).toBeInTheDocument();
      expect(screen.getByText('Code: WH001')).toBeInTheDocument();
      expect(screen.getByText('Secondary Warehouse')).toBeInTheDocument();
      expect(screen.getByText('Code: WH002')).toBeInTheDocument();
    });
  });

  it('displays warehouse details correctly', async () => {
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      // Check first warehouse details
      expect(screen.getByText('123 Main St')).toBeInTheDocument();
      expect(screen.getByText('New York, NY 10001')).toBeInTheDocument();
      expect(screen.getByText('USA')).toBeInTheDocument();
      expect(screen.getByText('+1-555-0123')).toBeInTheDocument();
      expect(screen.getByText('main@warehouse.com')).toBeInTheDocument();
      expect(screen.getByText('Manager: John Doe')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
      
      // Check second warehouse details
      expect(screen.getByText('456 Oak Ave')).toBeInTheDocument();
      expect(screen.getByText('Los Angeles, CA 90001')).toBeInTheDocument();
      expect(screen.getByText('secondary@warehouse.com')).toBeInTheDocument();
      expect(screen.getByText('Manager: Jane Smith')).toBeInTheDocument();
      expect(screen.getByText('Inactive')).toBeInTheDocument();
    });
  });

  it('opens warehouse form when Add Warehouse is clicked', async () => {
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Main Warehouse')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Add Warehouse'));
    
    expect(screen.getByText('Add Warehouse')).toBeInTheDocument();
    expect(screen.getByLabelText('Warehouse Name *')).toBeInTheDocument();
  });

  it('opens warehouse form for editing when edit button is clicked', async () => {
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Main Warehouse')).toBeInTheDocument();
    });
    
    const editButtons = screen.getAllByRole('button');
    const editButton = editButtons.find(button => 
      button.querySelector('svg') && button.getAttribute('class')?.includes('ghost')
    );
    
    if (editButton) {
      fireEvent.click(editButton);
      
      await waitFor(() => {
        expect(screen.getByText('Edit Warehouse')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Main Warehouse')).toBeInTheDocument();
      });
    }
  });

  it('shows empty state when no warehouses exist', async () => {
    (inventoryManagementApi.getWarehouses as jest.Mock).mockResolvedValue({
      success: true,
      data: [],
    });
    
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('No warehouses found')).toBeInTheDocument();
      expect(screen.getByText('Get started by creating your first warehouse')).toBeInTheDocument();
    });
  });

  it('handles delete warehouse with dependencies', async () => {
    // Mock inventory check to return items (has dependencies)
    (inventoryManagementApi.getInventory as jest.Mock).mockResolvedValue({
      success: true,
      data: { count: 5, results: [] },
    });
    
    // Mock window.alert
    const alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {});
    
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Main Warehouse')).toBeInTheDocument();
    });
    
    const deleteButtons = screen.getAllByRole('button');
    const deleteButton = deleteButtons.find(button => 
      button.querySelector('svg') && button.getAttribute('class')?.includes('text-red-600')
    );
    
    if (deleteButton) {
      fireEvent.click(deleteButton);
      
      await waitFor(() => {
        expect(alertSpy).toHaveBeenCalledWith(
          expect.stringContaining('Cannot delete warehouse "Main Warehouse" because it has inventory items')
        );
      });
    }
    
    alertSpy.mockRestore();
  });

  it('handles delete warehouse without dependencies', async () => {
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
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
    
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Main Warehouse')).toBeInTheDocument();
    });
    
    const deleteButtons = screen.getAllByRole('button');
    const deleteButton = deleteButtons.find(button => 
      button.querySelector('svg') && button.getAttribute('class')?.includes('text-red-600')
    );
    
    if (deleteButton) {
      fireEvent.click(deleteButton);
      
      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalledWith(
          expect.stringContaining('Are you sure you want to delete warehouse "Main Warehouse"?')
        );
        expect(inventoryManagementApi.deleteWarehouse).toHaveBeenCalledWith('1');
      });
    }
    
    confirmSpy.mockRestore();
  });
});

describe('WarehouseForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (inventoryManagementApi.getWarehouses as jest.Mock).mockResolvedValue({
      success: true,
      data: mockWarehouses,
    });
  });

  it('validates required fields', async () => {
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Main Warehouse')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Add Warehouse'));
    
    // Try to submit empty form
    const submitButton = screen.getByText('Create Warehouse');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Warehouse name is required')).toBeInTheDocument();
      expect(screen.getByText('Warehouse code is required')).toBeInTheDocument();
      expect(screen.getByText('Address is required')).toBeInTheDocument();
      expect(screen.getByText('City is required')).toBeInTheDocument();
      expect(screen.getByText('State is required')).toBeInTheDocument();
      expect(screen.getByText('Postal code is required')).toBeInTheDocument();
      expect(screen.getByText('Country is required')).toBeInTheDocument();
      expect(screen.getByText('Manager name is required')).toBeInTheDocument();
    });
  });

  it('validates warehouse code uniqueness', async () => {
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Main Warehouse')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Add Warehouse'));
    
    // Fill form with duplicate warehouse code
    fireEvent.change(screen.getByLabelText('Warehouse Name *'), {
      target: { value: 'Test Warehouse' },
    });
    fireEvent.change(screen.getByLabelText('Warehouse Code *'), {
      target: { value: 'WH001' }, // This code already exists
    });
    
    const submitButton = screen.getByText('Create Warehouse');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Warehouse code already exists. Please choose a different code.')).toBeInTheDocument();
    });
  });

  it('validates email format', async () => {
    render(<WarehouseManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Main Warehouse')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Add Warehouse'));
    
    // Fill email with invalid format
    fireEvent.change(screen.getByLabelText('Email Address'), {
      target: { value: 'invalid-email' },
    });
    
    const submitButton = screen.getByText('Create Warehouse');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
    });
  });

  it('creates warehouse successfully', async () => {
    (inventoryManagementApi.createWarehouse as jest.Mock).mockResolvedValue({
      success: true,
      data: { ...mockWarehouses[0], id: '3' },
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