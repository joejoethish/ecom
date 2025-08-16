/**
 * Authentication and authorization utilities for inventory management
 */
import React from 'react';
import { useAuth } from '@/hooks/useAuth';
import { User } from '@/types';

// Define inventory-specific permissions
export enum InventoryPermission {
  VIEW_INVENTORY = 'view_inventory',
  CREATE_INVENTORY = 'create_inventory',
  EDIT_INVENTORY = 'edit_inventory',
  DELETE_INVENTORY = 'delete_inventory',
  ADJUST_STOCK = 'adjust_stock',
  MANAGE_WAREHOUSES = 'manage_warehouses',
  VIEW_TRANSACTIONS = 'view_transactions',
  MANAGE_BATCHES = 'manage_batches',
  VIEW_ALERTS = 'view_alerts',
  CONFIGURE_ALERTS = 'configure_alerts',
  EXPORT_DATA = 'export_data'
}

// Define role-based permissions mapping
const ROLE_PERMISSIONS: Record<string, InventoryPermission[]> = {
  admin: [
    InventoryPermission.VIEW_INVENTORY,
    InventoryPermission.CREATE_INVENTORY,
    InventoryPermission.EDIT_INVENTORY,
    InventoryPermission.DELETE_INVENTORY,
    InventoryPermission.ADJUST_STOCK,
    InventoryPermission.MANAGE_WAREHOUSES,
    InventoryPermission.VIEW_TRANSACTIONS,
    InventoryPermission.MANAGE_BATCHES,
    InventoryPermission.VIEW_ALERTS,
    InventoryPermission.CONFIGURE_ALERTS,
    InventoryPermission.EXPORT_DATA
  ],
  seller: [
    InventoryPermission.VIEW_INVENTORY,
    InventoryPermission.CREATE_INVENTORY,
    InventoryPermission.EDIT_INVENTORY,
    InventoryPermission.ADJUST_STOCK,
    InventoryPermission.VIEW_TRANSACTIONS,
    InventoryPermission.MANAGE_BATCHES,
    InventoryPermission.VIEW_ALERTS,
    InventoryPermission.EXPORT_DATA
  ],
  inventory_manager: [
    InventoryPermission.VIEW_INVENTORY,
    InventoryPermission.CREATE_INVENTORY,
    InventoryPermission.EDIT_INVENTORY,
    InventoryPermission.ADJUST_STOCK,
    InventoryPermission.MANAGE_WAREHOUSES,
    InventoryPermission.VIEW_TRANSACTIONS,
    InventoryPermission.MANAGE_BATCHES,
    InventoryPermission.VIEW_ALERTS,
    InventoryPermission.CONFIGURE_ALERTS,
    InventoryPermission.EXPORT_DATA
  ],
  warehouse_staff: [
    InventoryPermission.VIEW_INVENTORY,
    InventoryPermission.ADJUST_STOCK,
    InventoryPermission.VIEW_TRANSACTIONS,
    InventoryPermission.MANAGE_BATCHES,
    InventoryPermission.VIEW_ALERTS
  ]
};

/**
 * Check if user has specific inventory permission
 */
export const hasInventoryPermission = (user: User | null, permission: InventoryPermission): boolean => {
  if (!user) return false;
  
  // Super admin has all permissions
  if (user.is_superuser) return true;
  
  // Check role-based permissions
  const userRole = user.user_type || 'customer';
  const rolePermissions = ROLE_PERMISSIONS[userRole] || [];
  
  return rolePermissions.includes(permission);
};

/**
 * Check if user has any of the specified permissions
 */
export const hasAnyInventoryPermission = (user: User | null, permissions: InventoryPermission[]): boolean => {
  return permissions.some(permission => hasInventoryPermission(user, permission));
};

/**
 * Check if user has all of the specified permissions
 */
export const hasAllInventoryPermissions = (user: User | null, permissions: InventoryPermission[]): boolean => {
  return permissions.every(permission => hasInventoryPermission(user, permission));
};

/**
 * Get all permissions for a user
 */
export const getUserInventoryPermissions = (user: User | null): InventoryPermission[] => {
  if (!user) return [];
  
  if (user.is_superuser) {
    return Object.values(InventoryPermission);
  }
  
  const userRole = user.user_type || 'customer';
  return ROLE_PERMISSIONS[userRole] || [];
};

/**
 * Check if user can access inventory management system
 */
export const canAccessInventoryManagement = (user: User | null): boolean => {
  return hasInventoryPermission(user, InventoryPermission.VIEW_INVENTORY);
};

/**
 * React hook for inventory authentication
 */
export const useInventoryAuth = () => {
  const auth = useAuth();
  
  const checkPermission = (permission: InventoryPermission): boolean => {
    return hasInventoryPermission(auth.user, permission);
  };
  
  const checkAnyPermission = (permissions: InventoryPermission[]): boolean => {
    return hasAnyInventoryPermission(auth.user, permissions);
  };
  
  const checkAllPermissions = (permissions: InventoryPermission[]): boolean => {
    return hasAllInventoryPermissions(auth.user, permissions);
  };
  
  const canAccess = canAccessInventoryManagement(auth.user);
  const userPermissions = getUserInventoryPermissions(auth.user);
  
  return {
    ...auth,
    checkPermission,
    checkAnyPermission,
    checkAllPermissions,
    canAccess,
    userPermissions,
    // Convenience methods for common checks
    canViewInventory: checkPermission(InventoryPermission.VIEW_INVENTORY),
    canCreateInventory: checkPermission(InventoryPermission.CREATE_INVENTORY),
    canEditInventory: checkPermission(InventoryPermission.EDIT_INVENTORY),
    canDeleteInventory: checkPermission(InventoryPermission.DELETE_INVENTORY),
    canAdjustStock: checkPermission(InventoryPermission.ADJUST_STOCK),
    canManageWarehouses: checkPermission(InventoryPermission.MANAGE_WAREHOUSES),
    canViewTransactions: checkPermission(InventoryPermission.VIEW_TRANSACTIONS),
    canManageBatches: checkPermission(InventoryPermission.MANAGE_BATCHES),
    canViewAlerts: checkPermission(InventoryPermission.VIEW_ALERTS),
    canConfigureAlerts: checkPermission(InventoryPermission.CONFIGURE_ALERTS),
    canExportData: checkPermission(InventoryPermission.EXPORT_DATA)
  };
};

/**
 * Higher-order component for protecting inventory routes
 */
export const withInventoryAuth = <P extends object>(
  Component: React.ComponentType<P>,
  requiredPermissions: InventoryPermission[] = [InventoryPermission.VIEW_INVENTORY]
) => {
  return function ProtectedInventoryComponent(props: P) {
    const auth = useInventoryAuth();
    
    // Show loading while authentication is being checked
    if (auth.loading) {
      return (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
    }
    
  
    
    // Show access denied if user doesn't have required permissions
    if (!auth.checkAllPermissions(requiredPermissions)) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
          <div className="text-red-600 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-4">
            You don't have permission to access this inventory management feature.
          </p>
          <p className="text-sm text-gray-500">
            Contact your administrator if you believe this is an error.
          </p>
        </div>
      );
    }
    
    return <Component {...props} />;
  };
};

/**
 * Component for conditionally rendering content based on permissions
 */
interface InventoryPermissionGateProps {
  permissions: InventoryPermission[];
  requireAll?: boolean;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export const InventoryPermissionGate: React.FC<InventoryPermissionGateProps> = ({
  permissions,
  requireAll = true,
  fallback = null,
  children
}) => {
  const auth = useInventoryAuth();
  
  const hasPermission = requireAll 
    ? auth.checkAllPermissions(permissions)
    : auth.checkAnyPermission(permissions);
  
  if (!hasPermission) {
    return <>{fallback}</>;
  }
  
  return <>{children}</>;
};