"""
Order signals for the ecommerce platform.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction

from .models import Order, OrderItem, OrderTracking, ReturnRequest, Replacement, Invoice
from apps.inventory.models import Inventory, InventoryTransaction
from apps.inventory.services import InventoryService


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for order post save.
    
    - Creates initial tracking event for new orders
    - Handles inventory updates based on status changes
    - Triggers notifications for status changes
    """
    if created:
        # Create initial tracking event
        OrderTracking.objects.create(
            order=instance,
            status=instance.status,
            description="Order created successfully",
        )
        
        # Reserve inventory for order items
        for order_item in instance.items.all():
            try:
                inventory = order_item.product.inventory
                InventoryService.reserve_stock(
                    inventory=inventory,
                    quantity=order_item.quantity,
                    user=instance.customer,
                    reference_number=instance.order_number,
                    order=instance,
                    notes=f"Reserved for order {instance.order_number}"
                )
            except Exception as e:
                # Log the error but don't stop the order creation
                print(f"Error reserving inventory for order {instance.order_number}: {str(e)}")
        
        # This would trigger notifications (to be implemented in notifications app)
        # notify_order_created(instance)


@receiver(pre_save, sender=Order)
def order_pre_save(sender, instance, **kwargs):
    """
    Signal handler for order pre save.
    
    - Tracks status changes
    - Handles inventory updates based on status changes
    """
    if instance.pk:
        # Get the old instance to check for status changes
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            
            # Store old status for post_save handler
            instance._old_status = old_instance.status
                
        except Order.DoesNotExist:
            instance._old_status = None


@receiver(post_save, sender=Order)
def order_status_change(sender, instance, created, **kwargs):
    """
    Signal handler for order status changes.
    
    - Updates inventory based on status changes
    - Creates tracking events for status changes
    """
    if not created and hasattr(instance, '_old_status') and instance._old_status != instance.status:
        # Status has changed
        if instance.status == 'cancelled':
            # Release reserved inventory
            for order_item in instance.items.all():
                try:
                    inventory = order_item.product.inventory
                    InventoryService.release_reserved_stock(
                        inventory=inventory,
                        quantity=order_item.quantity,
                        user=instance.customer,
                        reference_number=instance.order_number,
                        order=instance,
                        notes=f"Released due to order cancellation: {instance.order_number}"
                    )
                except Exception as e:
                    # Log the error
                    print(f"Error releasing inventory for cancelled order {instance.order_number}: {str(e)}")
        
        elif instance.status == 'confirmed':
            # Order is confirmed, but inventory remains reserved
            pass
        
        elif instance.status == 'shipped' or instance.status == 'out_for_delivery':
            # Convert reserved inventory to actual deduction
            for order_item in instance.items.all():
                try:
                    inventory = order_item.product.inventory
                    # Release the reservation
                    InventoryService.release_reserved_stock(
                        inventory=inventory,
                        quantity=order_item.quantity,
                        user=instance.customer,
                        reference_number=instance.order_number,
                        order=instance,
                        notes=f"Released reservation for shipped order {instance.order_number}"
                    )
                    
                    # Deduct from actual inventory
                    InventoryService.remove_stock(
                        inventory=inventory,
                        quantity=order_item.quantity,
                        user=instance.customer,
                        transaction_type="SALE",
                        reference_number=instance.order_number,
                        order=instance,
                        notes=f"Deducted for shipped order {instance.order_number}"
                    )
                except Exception as e:
                    # Log the error
                    print(f"Error updating inventory for shipped order {instance.order_number}: {str(e)}")


@receiver(post_save, sender=OrderTracking)
def order_tracking_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for order tracking post save.
    
    - Triggers notifications for tracking updates
    """
    if created:
        # This would trigger notifications (to be implemented in notifications app)
        # notify_order_status_changed(instance.order, instance.status, instance.description)
        pass


@receiver(post_save, sender=ReturnRequest)
def return_request_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for return request post save.
    
    - Creates order tracking event for return requests
    - Triggers notifications for return status changes
    """
    if created:
        # Create order tracking event
        OrderTracking.objects.create(
            order=instance.order,
            status=instance.order.status,
            description=f"Return request created for {instance.quantity} x {instance.order_item.product.name}",
        )
        
        # This would trigger notifications (to be implemented in notifications app)
        # notify_return_request_created(instance)
    else:
        # Handle status changes
        if instance.status == 'completed' and instance.return_received_date:
            # Return is completed, update inventory
            try:
                inventory = instance.order_item.product.inventory
                InventoryService.add_stock(
                    inventory=inventory,
                    quantity=instance.quantity,
                    user=instance.processed_by,
                    transaction_type="RETURN",
                    reference_number=instance.order.order_number,
                    notes=f"Return from order {instance.order.order_number}"
                )
            except Exception as e:
                # Log the error
                print(f"Error updating inventory for return {instance.id}: {str(e)}")


@receiver(pre_save, sender=Replacement)
def replacement_pre_save(sender, instance, **kwargs):
    """
    Signal handler for replacement pre save.
    
    - Tracks status changes
    """
    if instance.pk:
        try:
            old_instance = Replacement.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Replacement.DoesNotExist:
            instance._old_status = None


@receiver(post_save, sender=Replacement)
def replacement_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for replacement post save.
    
    - Creates order tracking event for replacements
    - Triggers notifications for replacement status changes
    - Updates inventory for replacements
    """
    if created:
        # Create order tracking event
        OrderTracking.objects.create(
            order=instance.order,
            status=instance.order.status,
            description=f"Replacement created for {instance.quantity} x {instance.order_item.product.name}",
        )
        
        # This would trigger notifications (to be implemented in notifications app)
        # notify_replacement_created(instance)
    else:
        # Handle status changes
        if hasattr(instance, '_old_status') and instance._old_status != instance.status:
            if instance.status == 'shipped':
                # Deduct replacement product from inventory
                try:
                    inventory = instance.replacement_product.inventory
                    InventoryService.remove_stock(
                        inventory=inventory,
                        quantity=instance.quantity,
                        user=instance.processed_by,
                        transaction_type="SALE",
                        reference_number=f"REPL-{instance.id}",
                        order=instance.order,
                        notes=f"Replacement for order {instance.order.order_number}"
                    )
                except Exception as e:
                    # Log the error
                    print(f"Error updating inventory for replacement {instance.id}: {str(e)}")


@receiver(post_save, sender=Invoice)
def invoice_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for invoice post save.
    
    - Updates order with invoice number
    - Triggers notifications for invoice generation
    """
    if created:
        # Update order with invoice number
        order = instance.order
        order.invoice_number = instance.invoice_number
        order.save(update_fields=['invoice_number'])
        
        # Create order tracking event
        OrderTracking.objects.create(
            order=order,
            status=order.status,
            description=f"Invoice {instance.invoice_number} generated",
        )
        
        # This would trigger notifications (to be implemented in notifications app)
        # notify_invoice_generated(instance)