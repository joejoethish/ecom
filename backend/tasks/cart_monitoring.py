"""
Cart monitoring tasks for the e-commerce platform.
"""
import logging
from typing import Dict, Any, List, Optional
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

# Import models
from apps.cart.models import Cart
from apps.orders.models import Order
from apps.authentication.models import User
from apps.notifications.models import Notification

# Import monitoring utilities
from .monitoring import TaskMonitor, TaskRetryHandler, task_monitor_decorator
from .tasks import send_email_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@task_monitor_decorator
def send_abandoned_cart_reminders(self):
    """
    Send reminders to users with abandoned carts.
    """
    try:
        logger.info("Sending abandoned cart reminders")
        
        # Find carts that haven't been updated in 24 hours and have items
        cutoff_time = timezone.now() - timedelta(hours=24)
        abandoned_carts = Cart.objects.filter(
            updated_at__lt=cutoff_time,
            items__isnull=False
        ).select_related('user').prefetch_related('items__product').distinct()
        
        reminder_count = 0
        for cart in abandoned_carts:
            try:
                # Check if user hasn't placed an order recently
                recent_orders = Order.objects.filter(
                    user=cart.user,
                    created_at__gte=cutoff_time
                ).exists()
                
                if not recent_orders:
                    context = {
                        'user': cart.user,
                        'cart': cart,
                        'cart_items': cart.items.all()[:5],  # Show first 5 items
                        'total_items': cart.items.count(),
                        'frontend_url': settings.FRONTEND_URL
                    }
                    
                    send_email_task.delay(
                        subject="Don't forget your items!",
                        message="You have items waiting in your cart.",
                        recipient_list=[cart.user.email],
                        template_name='emails/abandoned_cart_reminder.html',
                        context=context
                    )
                    
                    # Create in-app notification
                    Notification.objects.create(
                        user=cart.user,
                        title="Items in Your Cart",
                        message=f"You have {cart.items.count()} items waiting in your cart. Complete your purchase now!",
                        notification_type="ABANDONED_CART",
                        reference_id=str(cart.id)
                    )
                    
                    reminder_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to send reminder for cart {cart.id}: {str(e)}")
        
        logger.info(f"Abandoned cart reminders sent: {reminder_count}")
        return {"status": "success", "reminder_count": reminder_count}
        
    except Exception as exc:
        logger.error(f"Abandoned cart reminders failed: {str(exc)}")
        TaskRetryHandler.retry_task(self, exc)
        return {"status": "failed", "error": str(exc)}


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@task_monitor_decorator
def monitor_cart_price_changes(self):
    """
    Monitor price changes for items in active carts and notify users.
    """
    try:
        logger.info("Monitoring price changes for items in active carts")
        
        # Find active carts with items
        active_carts = Cart.objects.filter(
            items__isnull=False
        ).select_related('user').prefetch_related('items__product').distinct()
        
        notification_count = 0
        for cart in active_carts:
            try:
                price_changes = []
                
                for cart_item in cart.items.all():
                    product = cart_item.product
                    
                    # Check if price has changed since item was added to cart
                    if cart_item.price != product.price:
                        price_changes.append({
                            'product_name': product.name,
                            'old_price': cart_item.price,
                            'new_price': product.price,
                            'difference': product.price - cart_item.price
                        })
                        
                        # Update cart item price
                        cart_item.price = product.price
                        cart_item.save(update_fields=['price'])
                
                if price_changes:
                    # Send notification about price changes
                    context = {
                        'user': cart.user,
                        'price_changes': price_changes,
                        'total_changes': len(price_changes),
                        'frontend_url': settings.FRONTEND_URL
                    }
                    
                    send_email_task.delay(
                        subject="Price Changes in Your Cart",
                        message=f"Prices for {len(price_changes)} items in your cart have changed.",
                        recipient_list=[cart.user.email],
                        template_name='emails/cart_price_changes.html',
                        context=context
                    )
                    
                    # Create in-app notification
                    Notification.objects.create(
                        user=cart.user,
                        title="Price Changes in Your Cart",
                        message=f"Prices for {len(price_changes)} items in your cart have changed. Please review your cart before checkout.",
                        notification_type="CART_PRICE_CHANGE",
                        reference_id=str(cart.id)
                    )
                    
                    notification_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to process price changes for cart {cart.id}: {str(e)}")
        
        logger.info(f"Cart price change notifications sent: {notification_count}")
        return {"status": "success", "notification_count": notification_count}
        
    except Exception as exc:
        logger.error(f"Cart price change monitoring failed: {str(exc)}")
        TaskRetryHandler.retry_task(self, exc)
        return {"status": "failed", "error": str(exc)}