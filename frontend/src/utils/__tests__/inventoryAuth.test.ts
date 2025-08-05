/**
 * Tests for inventory authentication utilities
 */
import { 
  hasInventoryPermission, 
  hasAnyInventoryPermission, 
  hasAllInventoryPermissions,
  getUserInventoryPermissions,
  canAccessInventoryManagement,
  InventoryPermission 
} from '../inventoryAuth';
import { User } from '@/types';

describe('Inventory Authentication Utilities', () => {
  const mockAdminUser: User = {
    id: '1',
    username: 'admin',
    email: 'admin@example.com',
    user_type: 'admin',
    is_superuser: true,
    is_staff: true,
    is_verified: true,
    created_at: '2023-01-01T00:00:00Z',

  };

  const mockSellerUser: User = {
    id: '2',
    username: 'seller',
    email: 'seller@example.com',
    user_type: 'seller',
    is_superuser: false,
    is_staff: false,
    is_verified: true,
    created_at: '2023-01-01T00:00:00Z',
  };

  const mockCustomerUser: User = {
    id: '3',
    username: 'customer',
    email: 'customer@example.com',
    user_type: 'customer',
    is_superuser: false,
    is_staff: false,
    is_verified: true,
    created_at: '2023-01-01T00:00:00Z',
  };

  const mockInventoryManagerUser: User = {
    id: '4',
    username: 'inventory_manager',
    email: 'inventory@example.com',
    user_type: 'inventory_manager',
    is_superuser: false,
    is_staff: true,
    is_verified: true,
    created_at: '2023-01-01T00:00:00Z',
  };

  const mockWarehouseStaffUser: User = {
    id: '5',
    username: 'warehouse_staff',
    email: 'warehouse@example.com',
    user_type: 'warehouse_staff',
    is_superuser: false,
    is_staff: false,
    is_verified: true,
    created_at: '2023-01-01T00:00:00Z',
  };

  describe('hasInventoryPermission', () => {
    it('should return true for superuser regardless of role', () => {
      expect(hasInventoryPermission(mockAdminUser, InventoryPermission.VIEW_INVENTORY)).toBe(true);
      expect(hasInventoryPermission(mockAdminUser, InventoryPermission.DELETE_INVENTORY)).toBe(true);
      expect(hasInventoryPermission(mockAdminUser, InventoryPermission.MANAGE_WAREHOUSES)).toBe(true);
    });

    it('should return false for null user', () => {
      expect(hasInventoryPermission(null, InventoryPermission.VIEW_INVENTORY)).toBe(false);
    });

    it('should return correct permissions for admin user', () => {
      const nonSuperAdminUser = { ...mockAdminUser, is_superuser: false };
      expect(hasInventoryPermission(nonSuperAdminUser, InventoryPermission.VIEW_INVENTORY)).toBe(true);
      expect(hasInventoryPermission(nonSuperAdminUser, InventoryPermission.DELETE_INVENTORY)).toBe(true);
      expect(hasInventoryPermission(nonSuperAdminUser, InventoryPermission.MANAGE_WAREHOUSES)).toBe(true);
      expect(hasInventoryPermission(nonSuperAdminUser, InventoryPermission.CONFIGURE_ALERTS)).toBe(true);
    });

    it('should return correct permissions for seller user', () => {
      expect(hasInventoryPermission(mockSellerUser, InventoryPermission.VIEW_INVENTORY)).toBe(true);
      expect(hasInventoryPermission(mockSellerUser, InventoryPermission.CREATE_INVENTORY)).toBe(true);
      expect(hasInventoryPermission(mockSellerUser, InventoryPermission.EDIT_INVENTORY)).toBe(true);
      expect(hasInventoryPermission(mockSellerUser, InventoryPermission.DELETE_INVENTORY)).toBe(false);
      expect(hasInventoryPermission(mockSellerUser, InventoryPermission.MANAGE_WAREHOUSES)).toBe(false);
      expect(hasInventoryPermission(mockSellerUser, InventoryPermission.CONFIGURE_ALERTS)).toBe(false);
    });

    it('should return correct permissions for inventory manager user', () => {
      expect(hasInventoryPermission(mockInventoryManagerUser, InventoryPermission.VIEW_INVENTORY)).toBe(true);
      expect(hasInventoryPermission(mockInventoryManagerUser, InventoryPermission.MANAGE_WAREHOUSES)).toBe(true);
      expect(hasInventoryPermission(mockInventoryManagerUser, InventoryPermission.CONFIGURE_ALERTS)).toBe(true);
      expect(hasInventoryPermission(mockInventoryManagerUser, InventoryPermission.DELETE_INVENTORY)).toBe(false);
    });

    it('should return correct permissions for warehouse staff user', () => {
      expect(hasInventoryPermission(mockWarehouseStaffUser, InventoryPermission.VIEW_INVENTORY)).toBe(true);
      expect(hasInventoryPermission(mockWarehouseStaffUser, InventoryPermission.ADJUST_STOCK)).toBe(true);
      expect(hasInventoryPermission(mockWarehouseStaffUser, InventoryPermission.CREATE_INVENTORY)).toBe(false);
      expect(hasInventoryPermission(mockWarehouseStaffUser, InventoryPermission.MANAGE_WAREHOUSES)).toBe(false);
      expect(hasInventoryPermission(mockWarehouseStaffUser, InventoryPermission.CONFIGURE_ALERTS)).toBe(false);
    });

    it('should return false for customer user', () => {
      expect(hasInventoryPermission(mockCustomerUser, InventoryPermission.VIEW_INVENTORY)).toBe(false);
      expect(hasInventoryPermission(mockCustomerUser, InventoryPermission.CREATE_INVENTORY)).toBe(false);
    });
  });

  describe('hasAnyInventoryPermission', () => {
    it('should return true if user has any of the specified permissions', () => {
      const permissions = [InventoryPermission.VIEW_INVENTORY, InventoryPermission.DELETE_INVENTORY];
      expect(hasAnyInventoryPermission(mockSellerUser, permissions)).toBe(true); // Has VIEW_INVENTORY
      expect(hasAnyInventoryPermission(mockCustomerUser, permissions)).toBe(false); // Has none
    });

    it('should return false for empty permissions array', () => {
      expect(hasAnyInventoryPermission(mockAdminUser, [])).toBe(false);
    });
  });

  describe('hasAllInventoryPermissions', () => {
    it('should return true if user has all specified permissions', () => {
      const permissions = [InventoryPermission.VIEW_INVENTORY, InventoryPermission.CREATE_INVENTORY];
      expect(hasAllInventoryPermissions(mockSellerUser, permissions)).toBe(true);
      expect(hasAllInventoryPermissions(mockWarehouseStaffUser, permissions)).toBe(false); // Missing CREATE
    });

    it('should return true for empty permissions array', () => {
      expect(hasAllInventoryPermissions(mockCustomerUser, [])).toBe(true);
    });
  });

  describe('getUserInventoryPermissions', () => {
    it('should return all permissions for superuser', () => {
      const permissions = getUserInventoryPermissions(mockAdminUser);
      expect(permissions).toContain(InventoryPermission.VIEW_INVENTORY);
      expect(permissions).toContain(InventoryPermission.DELETE_INVENTORY);
      expect(permissions).toContain(InventoryPermission.MANAGE_WAREHOUSES);
      expect(permissions).toContain(InventoryPermission.CONFIGURE_ALERTS);
    });

    it('should return role-specific permissions for non-superuser', () => {
      const sellerPermissions = getUserInventoryPermissions(mockSellerUser);
      expect(sellerPermissions).toContain(InventoryPermission.VIEW_INVENTORY);
      expect(sellerPermissions).toContain(InventoryPermission.CREATE_INVENTORY);
      expect(sellerPermissions).not.toContain(InventoryPermission.DELETE_INVENTORY);
      expect(sellerPermissions).not.toContain(InventoryPermission.MANAGE_WAREHOUSES);

      const warehousePermissions = getUserInventoryPermissions(mockWarehouseStaffUser);
      expect(warehousePermissions).toContain(InventoryPermission.VIEW_INVENTORY);
      expect(warehousePermissions).toContain(InventoryPermission.ADJUST_STOCK);
      expect(warehousePermissions).not.toContain(InventoryPermission.CREATE_INVENTORY);
    });

    it('should return empty array for null user', () => {
      expect(getUserInventoryPermissions(null)).toEqual([]);
    });

    it('should return empty array for customer user', () => {
      expect(getUserInventoryPermissions(mockCustomerUser)).toEqual([]);
    });
  });

  describe('canAccessInventoryManagement', () => {
    it('should return true for users with VIEW_INVENTORY permission', () => {
      expect(canAccessInventoryManagement(mockAdminUser)).toBe(true);
      expect(canAccessInventoryManagement(mockSellerUser)).toBe(true);
      expect(canAccessInventoryManagement(mockWarehouseStaffUser)).toBe(true);
    });

    it('should return false for users without VIEW_INVENTORY permission', () => {
      expect(canAccessInventoryManagement(mockCustomerUser)).toBe(false);
      expect(canAccessInventoryManagement(null)).toBe(false);
    });
  });
});