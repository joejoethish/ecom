"""
Order signals for the ecommerce platform.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from .models import Order, OrderItem, OrderTracking, ReturnRequest, Replacement, Invoice
from apps.inventory.models import Inventory, InventoryTransaction
from apps.inventory.services import InventoryService
from apps.notifications.models import Notification, NotificationTemplate

# Import background tasks
from tasks.tasks import (
    send_order_confirmation_email,
    send_order_status_update_notification,
    process_inventory_transaction,
    check_inventory_levels_task,
    send_email_task,
    send_sms_task
)


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
        
        # Send order confirmation email asynchronously
        send_order_confirmation_email.delay(instance.id)


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
        # Status has changed - send notification asynchronously
        send_order_status_update_notification.delay(instance.id, instance.status)
        
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
    - Sends real-time WebSocket updates
    """
    if created:
        # Create notification for the customer
        try:
            # Get notification template if available
            template_name = f"order_{instance.status.lower()}"
            template = NotificationTemplate.objects.filter(name=template_name).first()
            
            if template:
                notification_text = template.content.format(
                    order_number=instance.order.order_number,
                    status=instance.status,
                    description=instance.description
                )
            else:
                notification_text = f"Order #{instance.order.order_number} status: {instance.status} - {instance.description}"
            
            # Create in-app notification
            Notification.objects.create(
                user=instance.order.user,
                title=f"Order #{instance.order.order_number} Update",
                message=notification_text,
                notification_type="ORDER_UPDATE",
                reference_id=str(instance.order.id)
            )
            
            # Send email notification asynchronously
            context = {
                'order': instance.order,
                'customer': instance.order.user,
                'status': instance.status,
                'description': instance.description,
                'tracking_date': instance.created_at,
                'frontend_url': settings.FRONTEND_URL
            }
            
            send_email_task.delay(
                subject=f"Order #{instance.order.order_number} Update",
                message=notification_text,
                recipient_list=[instance.order.user.email],
                template_name='emails/order_status_update.html',
                context=context
            )
            
            # Send SMS if phone number is available
            if hasattr(instance.order.user, 'phone') and instance.order.user.phone:
                sms_message = f"Order #{instance.order.order_number} status: {instance.status}. {instance.description}"
                send_sms_task.delay(
                    phone_number=instance.order.user.phone,
                    message=sms_message
                )
            
            # Send real-time WebSocket update
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            import json
            from django.utils import timezone
            
            channel_layer = get_channel_layer()
            
            # Send to order tracking group
            order_group_name = f'order_tracking_{instance.order.id}'
            tracking_data = {
                'status': instance.status,
                'message': instance.description,
                'location': instance.location if hasattr(instance, 'location') else None,
                'timestamp': instance.created_at.isoformat()
            }
            
            async_to_sync(channel_layer.group_send)(
                order_group_name,
                {
                    'type': 'order_update',
                    'status': instance.status,
                    'message': instance.description,
                    'tracking_data': tracking_data,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Also send to user's notification channel
            user_notification_group = f'notifications_{instance.order.user.id}'
            async_to_sync(channel_layer.group_send)(
                user_notification_group,
                {
                    'type': 'notification_message',
                    'notification_type': 'ORDER_UPDATE',
                    'message': notification_text,
                    'data': {
                        'order_id': str(instance.order.id),
                        'order_number': instance.order.order_number,
                        'status': instance.status
                    },
                    'timestamp': timezone.now().isoformat()
                }
            )
                
        except Exception as e:
            # Log the error but don't stop the process
            print(f"Error sending order tracking notification: {str(e)}")


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