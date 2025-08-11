/**
 * Inventory-specific notification integration utilities
 */
import { useCallback, useEffect } from 'react';
import { useAppDispatch } from '@/store';
import { addNotification } from '@/store/slices/notificationSlice';
import { useNotifications } from '@/hooks/useNotifications';
import { useInventoryAuth } from './inventoryAuth';
import { StockAlert } from '@/services/inventoryManagementApi';

// Define inventory notification types
export enum InventoryNotificationType {
  LOW_STOCK = 'low_stock',
  OUT_OF_STOCK = 'out_of_stock',
  EXPIRING_BATCH = 'expiring_batch',
  STOCK_ADJUSTMENT = 'stock_adjustment',
  WAREHOUSE_UPDATE = 'warehouse_update',
  INVENTORY_CREATED = 'inventory_created',
  INVENTORY_UPDATED = 'inventory_updated',
  INVENTORY_DELETED = 'inventory_deleted',
  BATCH_EXPIRED = 'batch_expired',
  REORDER_ALERT = 'reorder_alert'
}

// Notification priority mapping
  [InventoryNotificationType.OUT_OF_STOCK]: &apos;critical&apos;,
  [InventoryNotificationType.EXPIRING_BATCH]: &apos;high&apos;,
  [InventoryNotificationType.LOW_STOCK]: &apos;medium&apos;,
  [InventoryNotificationType.BATCH_EXPIRED]: &apos;high&apos;,
  [InventoryNotificationType.REORDER_ALERT]: &apos;medium&apos;,
  [InventoryNotificationType.STOCK_ADJUSTMENT]: &apos;low&apos;,
  [InventoryNotificationType.WAREHOUSE_UPDATE]: &apos;low&apos;,
  [InventoryNotificationType.INVENTORY_CREATED]: &apos;low&apos;,
  [InventoryNotificationType.INVENTORY_UPDATED]: &apos;low&apos;,
  [InventoryNotificationType.INVENTORY_DELETED]: &apos;medium&apos;
};

// Notification message templates
  [InventoryNotificationType.LOW_STOCK]: (data) => 
    `Low stock alert: ${data.product_name} at ${data.warehouse_name} (${data.current_stock} remaining)`,
  [InventoryNotificationType.OUT_OF_STOCK]: (data) => 
    `Out of stock: ${data.product_name} at ${data.warehouse_name}`,
  [InventoryNotificationType.EXPIRING_BATCH]: (data) => 
    `Batch expiring soon: ${data.product_name} batch ${data.batch_number} expires on ${new Date(data.expiration_date).toLocaleDateString()}`,
  [InventoryNotificationType.STOCK_ADJUSTMENT]: (data) => 
    `Stock adjusted: ${data.product_name} at ${data.warehouse_name} (${data.adjustment > 0 ? &apos;+&apos; : &apos;&apos;}${data.adjustment})`,
  [InventoryNotificationType.WAREHOUSE_UPDATE]: (data) => 
    `Warehouse updated: ${data.warehouse_name}`,
  [InventoryNotificationType.INVENTORY_CREATED]: (data) => 
    `New inventory item added: ${data.product_name} at ${data.warehouse_name}`,
  [InventoryNotificationType.INVENTORY_UPDATED]: (data) => 
    `Inventory updated: ${data.product_name} at ${data.warehouse_name}`,
  [InventoryNotificationType.INVENTORY_DELETED]: (data) => 
    `Inventory item removed: ${data.product_name} from ${data.warehouse_name}`,
  [InventoryNotificationType.BATCH_EXPIRED]: (data) => 
    `Batch expired: ${data.product_name} batch ${data.batch_number}`,
  [InventoryNotificationType.REORDER_ALERT]: (data) => 
    `Reorder needed: ${data.product_name} at ${data.warehouse_name} (below reorder level of ${data.reorder_level})`
};

/**
 * Hook for inventory-specific notifications
 */
export const useInventoryNotifications = () => {
  const dispatch = useAppDispatch();
  const auth = useInventoryAuth();

  // Process inventory-specific notifications
  const processInventoryNotification = useCallback((notification: unknown) => {
    // Only process if user has permission to view inventory
    if (!auth.canViewInventory) {
      return;
    }

    const notificationType = notification.type || notification.notification_type;
    const priority = NOTIFICATION_PRIORITY[notificationType] || &apos;medium&apos;;
    
    // Generate appropriate message
    const messageGenerator = NOTIFICATION_MESSAGES[notificationType];
    const message = messageGenerator 
      ? messageGenerator(notification.data || {})
      : notification.message || &apos;Inventory notification&apos;;

    // Add to notification store
    dispatch(addNotification({
      id: notification.id || `inventory-${Date.now()}`,
      type: notificationType,
      message,
      data: {
        ...notification.data,
        priority,
        category: &apos;inventory&apos;
      },
      timestamp: notification.timestamp || new Date().toISOString(),
      isRead: false
    }));

    // Show browser notification if supported and permitted
    if (&apos;Notification&apos; in window && Notification.permission === &apos;granted&apos;) {
      showBrowserNotification(message, priority, notification.data);
    }
  }, [dispatch, auth.canViewInventory]);

  // Show browser notification
  const showBrowserNotification = (message: string, priority: string, data: unknown) => {
      body: message,
      icon: &apos;/favicon.ico&apos;,
      badge: &apos;/favicon.ico&apos;,
      tag: `inventory-${data?.inventory_id || &apos;general&apos;}`,
      requireInteraction: priority === &apos;critical&apos;,
      silent: priority === &apos;low&apos;
    };

    const notification = new Notification(&apos;Inventory Alert&apos;, options);
    
    // Auto-close after 5 seconds for non-critical notifications
    if (priority !== &apos;critical&apos;) {
      setTimeout(() => notification.close(), 5000);
    }

    // Handle click to focus the inventory management page
    notification.onclick = () => {
      window.focus();
      if (data?.inventory_id) {
        // Navigate to specific inventory item if available
        window.location.hash = `#inventory-${data.inventory_id}`;
      }
      notification.close();
    };
  };

  // Request notification permission
  const requestNotificationPermission = useCallback(async () => {
    if (&apos;Notification&apos; in window && Notification.permission === &apos;default&apos;) {
      const permission = await Notification.requestPermission();
      return permission === &apos;granted&apos;;
    }
    return Notification.permission === &apos;granted&apos;;
  }, []);

  // Convert stock alert to notification format
  const convertStockAlertToNotification = useCallback((alert: StockAlert) => {
    const notificationType = alert.alert_type as InventoryNotificationType;
    const messageGenerator = NOTIFICATION_MESSAGES[notificationType];
    
    const message = messageGenerator ? messageGenerator({
      product_name: alert.inventory_item.product_variant.product.name,
      warehouse_name: alert.inventory_item.warehouse.name,
      sku: alert.inventory_item.product_variant.sku
    }) : alert.message;

    return {
      id: alert.id,
      type: notificationType,
      message,
      data: {
        priority: alert.priority,
        category: &apos;inventory&apos;,
        alert_id: alert.id,
        inventory_id: alert.inventory_item.id,
        product_name: alert.inventory_item.product_variant.product.name,
        warehouse_name: alert.inventory_item.warehouse.name,
        sku: alert.inventory_item.product_variant.sku
      },
      timestamp: alert.created_at,
      isRead: alert.is_acknowledged
    };
  }, []);

  // Send inventory notification
  const sendInventoryNotification = useCallback((
    type: InventoryNotificationType,
    data: unknown,
    options?: {
      priority?: &apos;low&apos; | &apos;medium&apos; | &apos;high&apos; | &apos;critical&apos;;
      showBrowser?: boolean;
    }
  ) => {
    const priority = options?.priority || NOTIFICATION_PRIORITY[type] || &apos;medium&apos;;
    const messageGenerator = NOTIFICATION_MESSAGES[type];
    const message = messageGenerator ? messageGenerator(data) : `Inventory notification: ${type}`;

    const notification = {
      id: `inventory-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      message,
      data: {
        ...data,
        priority,
        category: &apos;inventory&apos;
      },
      timestamp: new Date().toISOString(),
      isRead: false
    };

    // Add to store
    dispatch(addNotification(notification));

    // Show browser notification if requested
    if (options?.showBrowser && &apos;Notification&apos; in window && Notification.permission === &apos;granted&apos;) {
      showBrowserNotification(message, priority, data);
    }

    return notification;
  }, [dispatch]);

  return {
    isConnected,
    error,
    markAsRead,
    processInventoryNotification,
    convertStockAlertToNotification,
    sendInventoryNotification,
    requestNotificationPermission,
    hasNotificationPermission: &apos;Notification&apos; in window && Notification.permission === &apos;granted&apos;
  };
};

/**
 * Hook for managing inventory alert notifications
 */
  const inventoryNotifications = useInventoryNotifications();
  const auth = useInventoryAuth();

  // Process stock alerts and convert to notifications
  const processStockAlerts = useCallback((alerts: StockAlert[]) => {
    if (!auth.canViewAlerts) {
      return;
    }

    alerts.forEach(alert => {
      if (!alert.is_acknowledged) {
        const notification = inventoryNotifications.convertStockAlertToNotification(alert);
        inventoryNotifications.processInventoryNotification(notification);
      }
    });
  }, [auth.canViewAlerts, inventoryNotifications]);

  // Send stock level notification
  const notifyStockLevel = useCallback((
    inventoryItem: unknown,
    type: &apos;low_stock&apos; | &apos;out_of_stock&apos; | &apos;reorder_alert&apos;
  ) => {
    return inventoryNotifications.sendInventoryNotification(
      type as InventoryNotificationType,
      {
        inventory_id: inventoryItem.id,
        product_name: inventoryItem.product_variant.product.name,
        warehouse_name: inventoryItem.warehouse.name,
        current_stock: inventoryItem.stock_quantity,
        reorder_level: inventoryItem.reorder_level
      },
      {
        priority: type === &apos;out_of_stock&apos; ? &apos;critical&apos; : &apos;medium&apos;,
        showBrowser: true
      }
    );
  }, [inventoryNotifications]);

  // Send batch expiration notification
  const notifyBatchExpiration = useCallback((batch: unknown, daysUntilExpiration: number) => {
    const type = daysUntilExpiration <= 0 
      ? InventoryNotificationType.BATCH_EXPIRED 
      : InventoryNotificationType.EXPIRING_BATCH;

    return inventoryNotifications.sendInventoryNotification(
      type,
      {
        batch_id: batch.id,
        batch_number: batch.batch_number,
        product_name: batch.product_variant.product.name,
        warehouse_name: batch.warehouse.name,
        expiration_date: batch.expiration_date,
        days_until_expiration: daysUntilExpiration
      },
      {
        priority: daysUntilExpiration <= 0 ? 'high' : 'medium',
        showBrowser: true
      }
    );
  }, [inventoryNotifications]);

  // Send stock adjustment notification
  const notifyStockAdjustment = useCallback((
    inventoryItem: unknown,
    adjustment: number,
    reason: string
  ) => {
    return inventoryNotifications.sendInventoryNotification(
      InventoryNotificationType.STOCK_ADJUSTMENT,
      {
        inventory_id: inventoryItem.id,
        product_name: inventoryItem.product_variant.product.name,
        warehouse_name: inventoryItem.warehouse.name,
        adjustment,
        reason,
        new_stock: inventoryItem.stock_quantity
      },
      {
        priority: 'low',
        showBrowser: false
      }
    );
  }, [inventoryNotifications]);

  return {
    ...inventoryNotifications,
    processStockAlerts,
    notifyStockLevel,
    notifyBatchExpiration,
    notifyStockAdjustment
  };
};

export default useInventoryNotifications;