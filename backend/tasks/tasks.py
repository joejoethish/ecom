"""
Background tasks for the e-commerce platform.
"""
import logging
from typing import List, Optional, Dict, Any
from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db import models
from datetime import timedelta

# Import models
from apps.authentication.models import User
from apps.orders.models import Order
from apps.inventory.models import Inventory, InventoryTransaction
from apps.notifications.models import Notification, NotificationTemplate
from apps.products.models import Product

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, subject: str, message: str, recipient_list: List[str], 
                   html_message: Optional[str] = None, template_name: Optional[str] = None,
                   context: Optional[Dict[str, Any]] = None):
    """
    Send email asynchronously with retry mechanism and monitoring.
    """
    try:
        logger.info(f"Sending email to {recipient_list} with subject: {subject}")
        
        # Render HTML content from template if provided
        if template_name and context:
            html_message = render_to_string(template_name, context)
        
        if html_message:
            # Send HTML email
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
        else:
            # Send plain text email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=False
            )
        
        logger.info(f"Email sent successfully to {recipient_list}")
        return {"status": "success", "recipients": recipient_list}
        
    except Exception as exc:
        logger.error(f"Email task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms_task(self, phone_number: str, message: str, template_name: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
    """
    Send SMS notification asynchronously.
    """
    try:
        logger.info(f"Sending SMS to {phone_number}")
        
        # Render message from template if provided
        if template_name and context:
            message = render_to_string(template_name, context)
        
        # SMS sending logic would go here
        # For now, we'll just log it
        logger.info(f"SMS sent to {phone_number}: {message}")
        
        return {"status": "success", "phone_number": phone_number}
        
    except Exception as exc:
        logger.error(f"SMS task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task
def check_low_inventory():
    """
    Check for products with low inventory and send alerts.
    """
    try:
        low_stock_threshold = 10
        low_stock_products = Product.objects.filter(
            stock_quantity__lte=low_stock_threshold,
            is_active=True
        )
        
        if low_stock_products.exists():
            # Send notification to admin users
            admin_users = User.objects.filter(is_staff=True, is_active=True)
            
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    title="Low Inventory Alert",
                    message=f"{low_stock_products.count()} products are running low on stock",
                    notification_type='inventory_alert'
                )
        
        logger.info(f"Inventory check completed. {low_stock_products.count()} products with low stock")
        return {"status": "success", "low_stock_count": low_stock_products.count()}
        
    except Exception as exc:
        logger.error(f"Inventory check failed: {str(exc)}")
        raise exc


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id: int):
    """
    Send order confirmation email to customer.
    """
    try:
        order = Order.objects.get(id=order_id)
        
        context = {
            'order': order,
            'customer': order.user,
            'order_items': order.items.all(),
            'frontend_url': settings.FRONTEND_URL
        }
        
        send_email_task.delay(
            subject=f"Order Confirmation - #{order.order_number}",
            message=f"Thank you for your order #{order.order_number}",
            recipient_list=[order.user.email],
            template_name='emails/order_confirmation.html',
            context=context
        )
        
        logger.info(f"Order confirmation email queued for order {order_id}")
        return {"status": "success", "order_id": order_id}
        
    except Exception as exc:
        logger.error(f"Order confirmation email failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task
def cleanup_old_notifications():
    """
    Clean up old notifications to prevent database bloat.
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = Notification.objects.filter(
            created_at__lt=cutoff_date,
            is_read=True
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        return {"status": "success", "deleted_count": deleted_count}
        
    except Exception as exc:
        logger.error(f"Notification cleanup failed: {str(exc)}")
        raise exc


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_status_update_notification(self, order_id: int, status: str):
    """
    Send order status update notification to customer.
    """
    try:
        order = Order.objects.get(id=order_id)
        
        context = {
            'order': order,
            'customer': order.user,
            'new_status': status,
            'frontend_url': settings.FRONTEND_URL
        }
        
        send_email_task.delay(
            subject=f"Order Update - #{order.order_number}",
            message=f"Your order status has been updated to {status}",
            recipient_list=[order.user.email],
            template_name='emails/order_status_update.html',
            context=context
        )
        
        # Create in-app notification
        Notification.objects.create(
            user=order.user,
            title=f"Order Update - #{order.order_number}",
            message=f"Your order status has been updated to {status}",
            notification_type='order_update'
        )
        
        logger.info(f"Order status update notification sent for order {order_id}")
        return {"status": "success", "order_id": order_id, "new_status": status}
        
    except Exception as exc:
        logger.error(f"Order status update notification failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_inventory_transaction(self, inventory_id: int, transaction_type: str, 
                                quantity: int, reference_number: str = None,
                                notes: str = None, user_id: int = None):
    """
    Process inventory transaction asynchronously.
    """
    try:
        inventory = Inventory.objects.get(id=inventory_id)
        user = User.objects.get(id=user_id) if user_id else None
        
        # Create inventory transaction record
        transaction = InventoryTransaction.objects.create(
            inventory=inventory,
            transaction_type=transaction_type,
            quantity=quantity,
            reference_number=reference_number,
            notes=notes,
            user=user
        )
        
        # Update inventory quantity
        if transaction_type == 'IN':
            inventory.quantity += abs(quantity)
        elif transaction_type == 'OUT':
            inventory.quantity -= abs(quantity)
        
        # Ensure quantity doesn't go negative
        if inventory.quantity < 0:
            inventory.quantity = 0
        
        inventory.save()
        
        logger.info(f"Inventory transaction processed: {transaction.id}")
        return {
            "status": "success", 
            "transaction_id": transaction.id,
            "new_quantity": inventory.quantity
        }
        
    except Exception as exc:
        logger.error(f"Inventory transaction failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task
def check_inventory_levels_task():
    """
    Check inventory levels and send alerts for low stock.
    """
    try:
        return check_low_inventory()
    except Exception as exc:
        logger.error(f"Inventory levels check failed: {str(exc)}")
        raise exc