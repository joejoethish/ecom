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