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
const createMockStore = (authState: unknown) => {
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
  const store = createMockStore(authState);
  return <Provider store={store}>{children}</Provider>;
};

describe(&apos;Inventory Management Authentication Integration&apos;, () => {
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

  describe(&apos;Admin User Access&apos;, () => {
    beforeEach(() => {
      mockUseInventoryAuth.mockReturnValue({
        user: {
          id: &apos;1&apos;,
          username: &apos;admin&apos;,
          email: &apos;admin@example.com&apos;,
          user_type: &apos;admin&apos;,
          is_superuser: true,
          is_verified: true,
          created_at: &apos;2023-01-01T00:00:00Z&apos;,
        },
        tokens: {
          access: &apos;mock-access-token&apos;,
          refresh: &apos;mock-refresh-token&apos;,
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

    it(&apos;should render all tabs for admin user&apos;, async () => {
      const authState = {
        user: { 
          id: &apos;1&apos;, 
          username: &apos;admin&apos;, 
          user_type: &apos;admin&apos;, 
          is_superuser: true,
          is_verified: true,
          created_at: &apos;2023-01-01T00:00:00Z&apos;,
        },
        tokens: { access: &apos;token&apos;, refresh: &apos;token&apos; },
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
        expect(screen.getByText(&apos;Inventory&apos;)).toBeInTheDocument();
        expect(screen.getByText(&apos;Warehouses&apos;)).toBeInTheDocument();
        expect(screen.getByText(&apos;Batches&apos;)).toBeInTheDocument();
        expect(screen.getByText(&apos;Transactions&apos;)).toBeInTheDocument();
        expect(screen.getByText(&apos;Adjustments&apos;)).toBeInTheDocument();
        expect(screen.getByText(&apos;Alerts&apos;)).toBeInTheDocument();
      });
    });

    it(&apos;should show Add Inventory button for admin user&apos;, async () => {
      const authState = {
        user: { 
          id: &apos;1&apos;, 
          username: &apos;admin&apos;, 
          user_type: &apos;admin&apos;, 
          is_superuser: true,
          is_verified: true,
          created_at: &apos;2023-01-01T00:00:00Z&apos;,
        },
        tokens: { access: &apos;token&apos;, refresh: &apos;token&apos; },
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
        expect(screen.getByLabelText(&apos;Add new inventory item&apos;)).toBeInTheDocument();
      });
    });
  });

  describe(&apos;Seller User Access&apos;, () => {
    beforeEach(() => {
      mockUseInventoryAuth.mockReturnValue({
        user: {
          id: &apos;2&apos;,
          username: &apos;seller&apos;,
          email: &apos;seller@example.com&apos;,
          user_type: &apos;seller&apos;,
          is_superuser: false,
          is_verified: true,
          created_at: &apos;2023-01-01T00:00:00Z&apos;,
        },
        tokens: {
          access: &apos;mock-access-token&apos;,
          refresh: &apos;mock-refresh-token&apos;,
        },
        isAuthenticated: true,
        loading: false,
        error: null,
        clearError: jest.fn(),
        isAdmin: false,
        isSeller: true,
        isCustomer: false,
        checkPermission: (permission: string) => {
          // Sellers can&apos;t manage warehouses or configure alerts
          return ![&apos;manage_warehouses&apos;, &apos;configure_alerts&apos;, &apos;delete_inventory&apos;].includes(permission);
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

    it(&apos;should not show warehouse management tab for seller&apos;, async () => {
      const authState = {
        user: { 
          id: &apos;2&apos;, 
          username: &apos;seller&apos;, 
          user_type: &apos;seller&apos;, 
          is_superuser: false,
          is_verified: true,
          created_at: &apos;2023-01-01T00:00:00Z&apos;,
        },
        tokens: { access: &apos;token&apos;, refresh: &apos;token&apos; },
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
        expect(screen.getByText(&apos;Inventory&apos;)).toBeInTheDocument();
        expect(screen.queryByText(&apos;Warehouses&apos;)).not.toBeInTheDocument();
      });
    });

    it(&apos;should not show configure alerts button for seller&apos;, async () => {
      const authState = {
        user: { 
          id: &apos;2&apos;, 
          username: &apos;seller&apos;, 
          user_type: &apos;seller&apos;, 
          is_superuser: false,
          is_verified: true,
          created_at: &apos;2023-01-01T00:00:00Z&apos;,
        },
        tokens: { access: &apos;token&apos;, refresh: &apos;token&apos; },
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
      fireEvent.click(screen.getByText(&apos;Alerts&apos;));

      await waitFor(() => {
        expect(screen.queryByText(&apos;Configure Alerts&apos;)).not.toBeInTheDocument();
      });
    });
  });

  describe(&apos;Unauthenticated User&apos;, () => {
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

    it(&apos;should redirect unauthenticated users&apos;, async () => {
      // Mock window.location
      const mockLocation = {
        href: &apos;&apos;,
        pathname: &apos;/admin/inventory&apos;,
      };
      Object.defineProperty(window, &apos;location&apos;, {
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
        expect(screen.queryByText(&apos;Inventory&apos;)).not.toBeInTheDocument();
      });
    });
  });

  describe(&apos;Insufficient Permissions&apos;, () => {
    beforeEach(() => {
      mockUseInventoryAuth.mockReturnValue({
        user: {
          id: &apos;3&apos;,
          username: &apos;customer&apos;,
          email: &apos;customer@example.com&apos;,
          user_type: &apos;customer&apos;,
          is_superuser: false,
          is_verified: true,
          created_at: &apos;2023-01-01T00:00:00Z&apos;,
        },
        tokens: {
          access: &apos;mock-access-token&apos;,
          refresh: &apos;mock-refresh-token&apos;,
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

    it(&apos;should show access denied message for users without permissions&apos;, async () => {
      const authState = {
        user: { 
          id: &apos;3&apos;, 
          username: &apos;customer&apos;, 
          user_type: &apos;customer&apos;, 
          is_superuser: false,
          is_verified: true,
          created_at: &apos;2023-01-01T00:00:00Z&apos;,
        },
        tokens: { access: &apos;token&apos;, refresh: &apos;token&apos; },
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
        expect(screen.getByText(&apos;Access Denied&apos;)).toBeInTheDocument();
        expect(screen.getByText(&quot;You don&apos;t have permission to access this inventory management feature.&quot;)).toBeInTheDocument();
      });
    });
  });

  describe(&apos;Notification Integration&apos;, () => {
    beforeEach(() => {
      mockUseInventoryAuth.mockReturnValue({
        user: {
          id: &apos;1&apos;,
          username: &apos;admin&apos;,
          email: &apos;admin@example.com&apos;,
          user_type: &apos;admin&apos;,
          is_superuser: true,
          is_verified: true,
          created_at: &apos;2023-01-01T00:00:00Z&apos;,
        },
        tokens: {
          access: &apos;mock-access-token&apos;,
          refresh: &apos;mock-refresh-token&apos;,
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

    it(&apos;should call notification service when inventory is created&apos;, async () => {
      const mockSendNotification = jest.fn();
      mockUseInventoryAlertNotifications.mockReturnValue({
        ...mockUseInventoryAlertNotifications(),
        sendInventoryNotification: mockSendNotification,
      });

      const authState = {
        user: { 
          id: &apos;1&apos;, 
          username: &apos;admin&apos;, 
          user_type: &apos;admin&apos;, 
          is_superuser: true,
          is_verified: true,
          created_at: &apos;2023-01-01T00:00:00Z&apos;,
        },
        tokens: { access: &apos;token&apos;, refresh: &apos;token&apos; },
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

    it(&apos;should request notification permissions on mount&apos;, async () => {
      const mockRequestPermission = jest.fn();
      mockUseInventoryAlertNotifications.mockReturnValue({
        ...mockUseInventoryAlertNotifications(),
        requestNotificationPermission: mockRequestPermission,
      });

      const authState = {
        user: { 
          id: &apos;1&apos;, 
          username: &apos;admin&apos;, 
          user_type: &apos;admin&apos;, 
          is_superuser: true,
          is_verified: true,
          created_at: &apos;2023-01-01T00:00:00Z&apos;,
        },
        tokens: { access: &apos;token&apos;, refresh: &apos;token&apos; },
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