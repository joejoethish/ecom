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
const NOTIFICATION_PRIORITY: Record<string, 'low' | 'medium' | 'high' | 'critical'> = {
  [InventoryNotificationType.OUT_OF_STOCK]: 'critical',
  [InventoryNotificationType.EXPIRING_BATCH]: 'high',
  [InventoryNotificationType.LOW_STOCK]: 'medium',
  [InventoryNotificationType.BATCH_EXPIRED]: 'high',
  [InventoryNotificationType.REORDER_ALERT]: 'medium',
  [InventoryNotificationType.STOCK_ADJUSTMENT]: 'low',
  [InventoryNotificationType.WAREHOUSE_UPDATE]: 'low',
  [InventoryNotificationType.INVENTORY_CREATED]: 'low',
  [InventoryNotificationType.INVENTORY_UPDATED]: 'low',
  [InventoryNotificationType.INVENTORY_DELETED]: 'medium'
};

// Notification message templates
const NOTIFICATION_MESSAGES: Record<string, (data: any) => string> = {
  [InventoryNotificationType.LOW_STOCK]: (data) => 
    `Low stock alert: ${data.product_name} at ${data.warehouse_name} (${data.current_stock} remaining)`,
  [InventoryNotificationType.OUT_OF_STOCK]: (data) => 
    `Out of stock: ${data.product_name} at ${data.warehouse_name}`,
  [InventoryNotificationType.EXPIRING_BATCH]: (data) => 
    `Batch expiring soon: ${data.product_name} batch ${data.batch_number} expires on ${new Date(data.expiration_date).toLocaleDateString()}`,
  [InventoryNotificationType.STOCK_ADJUSTMENT]: (data) => 
    `Stock adjusted: ${data.product_name} at ${data.warehouse_name} (${data.adjustment > 0 ? '+' : ''}${data.adjustment})`,
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
  const { isConnected, markAsRead, error } = useNotifications();

  // Process inventory-specific notifications
  const processInventoryNotification = useCallback((notification: any) => {
    // Only process if user has permission to view inventory
    if (!auth.canViewInventory) {
      return;
    }

    const notificationType = notification.type || notification.notification_type;
    const priority = NOTIFICATION_PRIORITY[notificationType] || 'medium';
    
    // Generate appropriate message
    const messageGenerator = NOTIFICATION_MESSAGES[notificationType];
    const message = messageGenerator 
      ? messageGenerator(notification.data || {})
      : notification.message || 'Inventory notification';

    // Add to notification store
    dispatch(addNotification({
      id: notification.id || `inventory-${Date.now()}`,
      type: notificationType,
      message,
      data: {
        ...notification.data,
        priority,
        category: 'inventory'
      },
      timestamp: notification.timestamp || new Date().toISOString(),
      isRead: false
    }));

    // Show browser notification if supported and permitted
    if ('Notification' in window && Notification.permission === 'granted') {
      showBrowserNotification(message, priority, notification.data);
    }
  }, [dispatch, auth.canViewInventory]);

  // Show browser notification
  const showBrowserNotification = (message: string, priority: string, data: any) => {
    const options: NotificationOptions = {
      body: message,
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      tag: `inventory-${data?.inventory_id || 'general'}`,
      requireInteraction: priority === 'critical',
      silent: priority === 'low'
    };

    const notification = new Notification('Inventory Alert', options);
    
    // Auto-close after 5 seconds for non-critical notifications
    if (priority !== 'critical') {
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
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return Notification.permission === 'granted';
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
        category: 'inventory',
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
    data: any,
    options?: {
      priority?: 'low' | 'medium' | 'high' | 'critical';
      showBrowser?: boolean;
    }
  ) => {
    const priority = options?.priority || NOTIFICATION_PRIORITY[type] || 'medium';
    const messageGenerator = NOTIFICATION_MESSAGES[type];
    const message = messageGenerator ? messageGenerator(data) : `Inventory notification: ${type}`;

    const notification = {
      id: `inventory-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      message,
      data: {
        ...data,
        priority,
        category: 'inventory'
      },
      timestamp: new Date().toISOString(),
      isRead: false
    };

    // Add to store
    dispatch(addNotification(notification));

    // Show browser notification if requested
    if (options?.showBrowser && 'Notification' in window && Notification.permission === 'granted') {
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
    hasNotificationPermission: 'Notification' in window && Notification.permission === 'granted'
  };
};

/**
 * Hook for managing inventory alert notifications
 */
export const useInventoryAlertNotifications = () => {
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
    inventoryItem: any,
    type: 'low_stock' | 'out_of_stock' | 'reorder_alert'
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
        priority: type === 'out_of_stock' ? 'critical' : 'medium',
        showBrowser: true
      }
    );
  }, [inventoryNotifications]);

  // Send batch expiration notification
  const notifyBatchExpiration = useCallback((batch: any, daysUntilExpiration: number) => {
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
    inventoryItem: any,
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