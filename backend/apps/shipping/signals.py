from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Shipment, ShipmentTracking

@receiver(post_save, sender=Shipment)
def shipment_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Shipment post_save
    
    Creates initial tracking entry when a shipment is created
    Updates order status when shipment status changes
    """
    if created:
        # Create initial tracking entry
        ShipmentTracking.objects.create(
            shipment=instance,
            status=instance.status,
            description="Shipment created",
            location="",
            timestamp=timezone.now()
        )
    else:
        # Get the order
        order = instance.order
        
        # Update order status based on shipment status
        if instance.status == 'SHIPPED' and order.status == 'CONFIRMED':
            order.status = 'SHIPPED'
            order.save(update_fields=['status'])
        elif instance.status == 'DELIVERED' and order.status == 'SHIPPED':
            order.status = 'DELIVERED'
            order.save(update_fields=['status'])
        elif instance.status == 'RETURNED' and order.status != 'RETURNED':
            order.status = 'RETURNED'
            order.save(update_fields=['status'])
        elif instance.status == 'CANCELLED' and order.status != 'CANCELLED':
            order.status = 'CANCELLED'
            order.save(update_fields=['status'])


@receiver(post_save, sender=ShipmentTracking)
def shipment_tracking_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for ShipmentTracking post_save
    
    Updates shipment status when a new tracking entry is created
    """
    if created:
        shipment = instance.shipment
        
        # Update shipment status if the new tracking status is different
        if shipment.status != instance.status:
            shipment.status = instance.status
            
            # Update timestamps based on status
            if instance.status == 'SHIPPED' and not shipment.shipped_at:
                shipment.shipped_at = instance.timestamp
            elif instance.status == 'DELIVERED' and not shipment.delivered_at:
                shipment.delivered_at = instance.timestamp
                
            shipment.save(update_fields=['status', 'shipped_at', 'delivered_at'])
            
            # Trigger notifications (would be implemented in a real system)
            # notify_shipment_status_change(shipment)