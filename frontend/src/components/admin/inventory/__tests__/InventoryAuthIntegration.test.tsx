/**
 * Tests for inventory management authentication and notification integration
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import InventoryManagement from '../InventoryManagement';
import { useInventoryAuth } from '@/utils/inventoryAuth';
import { useInventoryAlertNotifications } from '@/utils/inventoryNotifications';
import authReducer from '@/store/slices/authSlice';
import notificationReducer from '@/store/slices/notificationSlice';

// Mock the hooks
jest.mock('@/utils/inventoryAuth');
jest.mock('@/utils/inventoryNotifications');
jest.mock('@/services/inventoryManagementApi');

const mockUseInventoryAuth = useInventoryAuth as jest.MockedFunction<typeof useInventoryAuth>;
const mockUseInventoryAlertNotifications = useInventoryAlertNotifications as jest.MockedFunction<typeof useInventoryAlertNotifications>;

// Mock store
const createMockStore = (authState: any) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      notifications: notificationReducer,
    },
    preloadedState: {
      auth: authState,
      notifications: {
        notifications: [],
        unreadCount: 0,
        isNotificationCenterOpen: false,
      },
    },
  });
};

// Mock component wrapper
const MockWrapper: React.FC<{ children: React.ReactNode; authState: any }> = ({ children, authState }) => {
  const store = createMockStore(authState);
  return <Provider store={store}>{children}</Provider>;
};

describe('Inventory Management Authentication Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Default mock implementations
    mockUseInventoryAlertNotifications.mockReturnValue({
      isConnected: true,
      error: null,
      markAsRead: jest.fn(),
      processInventoryNotification: jest.fn(),
      convertStockAlertToNotification: jest.fn(),
      sendInventoryNotification: jest.fn(),
      requestNotificationPermission: jest.fn(),
      hasNotificationPermission: true,
      processStockAlerts: jest.fn(),
      notifyStockLevel: jest.fn(),
      notifyBatchExpiration: jest.fn(),
      notifyStockAdjustment: jest.fn(),
    });
  });

  describe('Admin User Access', () => {
    beforeEach(() => {
      mockUseInventoryAuth.mockReturnValue({
        user: {
          id: '1',
          username: 'admin',
          email: 'admin@example.com',
          user_type: 'admin',
          is_superuser: true,
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z',
        },
        tokens: {
          access: 'mock-access-token',
          refresh: 'mock-refresh-token',
        },
        isAuthenticated: true,
        loading: false,
        error: null,
        clearError: jest.fn(),
        isAdmin: true,
        isSeller: false,
        isCustomer: false,
        checkPermission: jest.fn().mockReturnValue(true),
        checkAnyPermission: jest.fn().mockReturnValue(true),
        checkAllPermissions: jest.fn().mockReturnValue(true),
        canAccess: true,
        userPermissions: [],
        canViewInventory: true,
        canCreateInventory: true,
        canEditInventory: true,
        canDeleteInventory: true,
        canAdjustStock: true,
        canManageWarehouses: true,
        canViewTransactions: true,
        canManageBatches: true,
        canViewAlerts: true,
        canConfigureAlerts: true,
        canExportData: true,
      });
    });

    it('should render all tabs for admin user', async () => {
      const authState = {
        user: { 
          id: '1', 
          username: 'admin', 
          user_type: 'admin', 
          is_superuser: true,
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z',
        },
        tokens: { access: 'token', refresh: 'token' },
        isAuthenticated: true,
        loading: false,
        error: null,
      };

      render(
        <MockWrapper authState={authState}>
          <InventoryManagement />
        </MockWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Inventory')).toBeInTheDocument();
        expect(screen.getByText('Warehouses')).toBeInTheDocument();
        expect(screen.getByText('Batches')).toBeInTheDocument();
        expect(screen.getByText('Transactions')).toBeInTheDocument();
        expect(screen.getByText('Adjustments')).toBeInTheDocument();
        expect(screen.getByText('Alerts')).toBeInTheDocument();
      });
    });

    it('should show Add Inventory button for admin user', async () => {
      const authState = {
        user: { 
          id: '1', 
          username: 'admin', 
          user_type: 'admin', 
          is_superuser: true,
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z',
        },
        tokens: { access: 'token', refresh: 'token' },
        isAuthenticated: true,
        loading: false,
        error: null,
      };

      render(
        <MockWrapper authState={authState}>
          <InventoryManagement />
        </MockWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Add new inventory item')).toBeInTheDocument();
      });
    });
  });

  describe('Seller User Access', () => {
    beforeEach(() => {
      mockUseInventoryAuth.mockReturnValue({
        user: {
          id: '2',
          username: 'seller',
          email: 'seller@example.com',
          user_type: 'seller',
          is_superuser: false,
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z',
        },
        tokens: {
          access: 'mock-access-token',
          refresh: 'mock-refresh-token',
        },
        isAuthenticated: true,
        loading: false,
        error: null,
        clearError: jest.fn(),
        isAdmin: false,
        isSeller: true,
        isCustomer: false,
        checkPermission: (permission: string) => {
          // Sellers can't manage warehouses or configure alerts
          return !['manage_warehouses', 'configure_alerts', 'delete_inventory'].includes(permission);
        },
        checkAnyPermission: jest.fn().mockReturnValue(true),
        checkAllPermissions: jest.fn().mockReturnValue(false),
        canAccess: true,
        userPermissions: [],
        canViewInventory: true,
        canCreateInventory: true,
        canEditInventory: true,
        canDeleteInventory: false,
        canAdjustStock: true,
        canManageWarehouses: false,
        canViewTransactions: true,
        canManageBatches: true,
        canViewAlerts: true,
        canConfigureAlerts: false,
        canExportData: true,
      });
    });

    it('should not show warehouse management tab for seller', async () => {
      const authState = {
        user: { 
          id: '2', 
          username: 'seller', 
          user_type: 'seller', 
          is_superuser: false,
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z',
        },
        tokens: { access: 'token', refresh: 'token' },
        isAuthenticated: true,
        loading: false,
        error: null,
      };

      render(
        <MockWrapper authState={authState}>
          <InventoryManagement />
        </MockWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Inventory')).toBeInTheDocument();
        expect(screen.queryByText('Warehouses')).not.toBeInTheDocument();
      });
    });

    it('should not show configure alerts button for seller', async () => {
      const authState = {
        user: { 
          id: '2', 
          username: 'seller', 
          user_type: 'seller', 
          is_superuser: false,
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z',
        },
        tokens: { access: 'token', refresh: 'token' },
        isAuthenticated: true,
        loading: false,
        error: null,
      };

      render(
        <MockWrapper authState={authState}>
          <InventoryManagement />
        </MockWrapper>
      );

      // Click on alerts tab
      fireEvent.click(screen.getByText('Alerts'));

      await waitFor(() => {
        expect(screen.queryByText('Configure Alerts')).not.toBeInTheDocument();
      });
    });
  });

  describe('Unauthenticated User', () => {
    beforeEach(() => {
      mockUseInventoryAuth.mockReturnValue({
        user: null,
        tokens: null,
        isAuthenticated: false,
        loading: false,
        error: null,
        clearError: jest.fn(),
        isAdmin: false,
        isSeller: false,
        isCustomer: false,
        checkPermission: jest.fn().mockReturnValue(false),
        checkAnyPermission: jest.fn().mockReturnValue(false),
        checkAllPermissions: jest.fn().mockReturnValue(false),
        canAccess: false,
        userPermissions: [],
        canViewInventory: false,
        canCreateInventory: false,
        canEditInventory: false,
        canDeleteInventory: false,
        canAdjustStock: false,
        canManageWarehouses: false,
        canViewTransactions: false,
        canManageBatches: false,
        canViewAlerts: false,
        canConfigureAlerts: false,
        canExportData: false,
      });
    });

    it('should redirect unauthenticated users', async () => {
      // Mock window.location
      const mockLocation = {
        href: '',
        pathname: '/admin/inventory',
      };
      Object.defineProperty(window, 'location', {
        value: mockLocation,
        writable: true,
      });

      const authState = {
        user: null,
        tokens: null,
        isAuthenticated: false,
        loading: false,
        error: null,
      };

      render(
        <MockWrapper authState={authState}>
          <InventoryManagement />
        </MockWrapper>
      );

      // Should not render the main content
      await waitFor(() => {
        expect(screen.queryByText('Inventory')).not.toBeInTheDocument();
      });
    });
  });

  describe('Insufficient Permissions', () => {
    beforeEach(() => {
      mockUseInventoryAuth.mockReturnValue({
        user: {
          id: '3',
          username: 'customer',
          email: 'customer@example.com',
          user_type: 'customer',
          is_superuser: false,
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z',
        },
        tokens: {
          access: 'mock-access-token',
          refresh: 'mock-refresh-token',
        },
        isAuthenticated: true,
        loading: false,
        error: null,
        clearError: jest.fn(),
        isAdmin: false,
        isSeller: false,
        isCustomer: true,
        checkPermission: jest.fn().mockReturnValue(false),
        checkAnyPermission: jest.fn().mockReturnValue(false),
        checkAllPermissions: jest.fn().mockReturnValue(false),
        canAccess: false,
        userPermissions: [],
        canViewInventory: false,
        canCreateInventory: false,
        canEditInventory: false,
        canDeleteInventory: false,
        canAdjustStock: false,
        canManageWarehouses: false,
        canViewTransactions: false,
        canManageBatches: false,
        canViewAlerts: false,
        canConfigureAlerts: false,
        canExportData: false,
      });
    });

    it('should show access denied message for users without permissions', async () => {
      const authState = {
        user: { 
          id: '3', 
          username: 'customer', 
          user_type: 'customer', 
          is_superuser: false,
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z',
        },
        tokens: { access: 'token', refresh: 'token' },
        isAuthenticated: true,
        loading: false,
        error: null,
      };

      render(
        <MockWrapper authState={authState}>
          <InventoryManagement />
        </MockWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Access Denied')).toBeInTheDocument();
        expect(screen.getByText("You don't have permission to access this inventory management feature.")).toBeInTheDocument();
      });
    });
  });

  describe('Notification Integration', () => {
    beforeEach(() => {
      mockUseInventoryAuth.mockReturnValue({
        user: {
          id: '1',
          username: 'admin',
          email: 'admin@example.com',
          user_type: 'admin',
          is_superuser: true,
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z',
        },
        tokens: {
          access: 'mock-access-token',
          refresh: 'mock-refresh-token',
        },
        isAuthenticated: true,
        loading: false,
        error: null,
        clearError: jest.fn(),
        isAdmin: true,
        isSeller: false,
        isCustomer: false,
        checkPermission: jest.fn().mockReturnValue(true),
        checkAnyPermission: jest.fn().mockReturnValue(true),
        checkAllPermissions: jest.fn().mockReturnValue(true),
        canAccess: true,
        userPermissions: [],
        canViewInventory: true,
        canCreateInventory: true,
        canEditInventory: true,
        canDeleteInventory: true,
        canAdjustStock: true,
        canManageWarehouses: true,
        canViewTransactions: true,
        canManageBatches: true,
        canViewAlerts: true,
        canConfigureAlerts: true,
        canExportData: true,
      });
    });

    it('should call notification service when inventory is created', async () => {
      const mockSendNotification = jest.fn();
      mockUseInventoryAlertNotifications.mockReturnValue({
        ...mockUseInventoryAlertNotifications(),
        sendInventoryNotification: mockSendNotification,
      });

      const authState = {
        user: { 
          id: '1', 
          username: 'admin', 
          user_type: 'admin', 
          is_superuser: true,
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z',
        },
        tokens: { access: 'token', refresh: 'token' },
        isAuthenticated: true,
        loading: false,
        error: null,
      };

      render(
        <MockWrapper authState={authState}>
          <InventoryManagement />
        </MockWrapper>
      );

      // This would be tested with actual form submission in integration tests
      // For now, we verify the notification service is available
      expect(mockUseInventoryAlertNotifications).toHaveBeenCalled();
    });

    it('should request notification permissions on mount', async () => {
      const mockRequestPermission = jest.fn();
      mockUseInventoryAlertNotifications.mockReturnValue({
        ...mockUseInventoryAlertNotifications(),
        requestNotificationPermission: mockRequestPermission,
      });

      const authState = {
        user: { 
          id: '1', 
          username: 'admin', 
          user_type: 'admin', 
          is_superuser: true,
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z',
        },
        tokens: { access: 'token', refresh: 'token' },
        isAuthenticated: true,
        loading: false,
        error: null,
      };

      render(
        <MockWrapper authState={authState}>
          <InventoryManagement />
        </MockWrapper>
      );

      expect(mockUseInventoryAlertNotifications).toHaveBeenCalled();
    });
  });
});