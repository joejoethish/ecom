from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Inventory, InventoryTransaction, PurchaseOrderItem


@receiver(post_save, sender=InventoryTransaction)
def update_inventory_on_transaction(sender, instance, created, **kwargs):
    """
    Update inventory quantities when a transaction is created.
    This is a backup mechanism - normally inventory is updated through the service layer.
    Also sends real-time WebSocket updates for inventory changes.
    """
    if created:
        inventory = instance.inventory
        
        # Skip if this is just an audit record with no quantity change
        if instance.quantity == 0:
            return
        
        # Update last_restocked date for purchases
        if instance.transaction_type == 'PURCHASE' and instance.quantity > 0:
            inventory.last_restocked = timezone.now()
            inventory.save(update_fields=['last_restocked'])
        
        # Send real-time WebSocket update for inventory change
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            import json
            
            channel_layer = get_channel_layer()
            
            # Send to inventory updates group
            product = inventory.product
            
            async_to_sync(channel_layer.group_send)(
                'inventory_updates',
                {
                    'type': 'inventory_update',
                    'update_type': 'stock_change',
                    'product_id': str(product.id),
                    'data': {
                        'product_name': product.name,
                        'sku': product.sku,
                        'previous_quantity': inventory.quantity - instance.quantity if instance.transaction_type in ['IN', 'PURCHASE', 'RETURN'] else inventory.quantity + instance.quantity,
                        'current_quantity': inventory.quantity,
                        'transaction_type': instance.transaction_type,
                        'reference': instance.reference_number,
                        'notes': instance.notes
                    },
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Check for low stock and send alert if needed
            if inventory.quantity <= inventory.minimum_stock_level:
                async_to_sync(channel_layer.group_send)(
                    'inventory_updates',
                    {
                        'type': 'low_stock_alert',
                        'product_id': str(product.id),
                        'product_name': product.name,
                        'current_stock': inventory.quantity,
                        'threshold': inventory.minimum_stock_level,
                        'timestamp': timezone.now().isoformat()
                    }
                )
        except Exception as e:
            # Log the error but don't stop the process
            print(f"Error sending inventory WebSocket update: {str(e)}")


@receiver(post_save, sender=PurchaseOrderItem)
def update_purchase_order_status(sender, instance, **kwargs):
    """
    Update purchase order status when items are received.
    """
    purchase_order = instance.purchase_order
    
    # Skip if the purchase order is already in a final state
    if purchase_order.status in ['RECEIVED', 'CANCELLED']:
        return
    
    # Check if all items are completed
    all_items = purchase_order.items.all()
    all_completed = all(item.is_completed for item in all_items)
    any_received = any(item.quantity_received > 0 for item in all_items)
    
    # Update purchase order status
    if all_completed:
        purchase_order.status = 'RECEIVED'
        if not purchase_order.actual_delivery_date:
            purchase_order.actual_delivery_date = timezone.now().date()
    elif any_received:
        purchase_order.status = 'PARTIAL'
    
    purchase_order.save(update_fields=['status', 'actual_delivery_date'])


@receiver(pre_save, sender=Inventory)
def validate_inventory_thresholds(sender, instance, **kwargs):
    """
    Validate inventory thresholds before saving.
    """
    if instance.minimum_stock_level < 0:
        raise ValidationError("Minimum stock level cannot be negative")
    
    if instance.reorder_point < instance.minimum_stock_level:
        raise ValidationError("Reorder point must be greater than or equal to minimum stock level")
    
    if instance.maximum_stock_level <= instance.reorder_point:
        raise ValidationError("Maximum stock level must be greater than reorder point")