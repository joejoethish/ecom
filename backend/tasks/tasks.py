"""
Background task definitions for the e-commerce platform.
"""
import logging
from typing import Dict, Any, List, Optional
from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db import models
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, subject: str, message: str, recipient_list: List[str], 
                   html_message: Optional[str] = None, template_name: Optional[str] = None,
                   context: Optional[Dict[str, Any]] = None):
    """
    Send email asynchronously with retry mechanism.
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
        
        # TODO: Integrate with SMS service provider (Twilio, AWS SNS, etc.)
        # For now, we'll log the SMS
        logger.info(f"SMS Content: {message}")
        
        logger.info(f"SMS sent successfully to {phone_number}")
        return {"status": "success", "phone_number": phone_number}
        
    except Exception as exc:
        logger.error(f"SMS task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def check_inventory_levels_task(self):
    """
    Check inventory levels and send alerts for low stock items.
    """
    try:
        # Import models inside the task to avoid circular imports
        from apps.authentication.models import User
        from apps.inventory.models import Inventory
        from apps.notifications.models import Notification
        
        logger.info("Starting inventory level check")
        
        # Find products with low stock
        low_stock_items = Inventory.objects.filter(
            quantity__lte=models.F('minimum_stock_level')
        ).select_related('product')
        
        if not low_stock_items.exists():
            logger.info("No low stock items found")
            return {"status": "success", "low_stock_count": 0}
        
        # Prepare alert data
        alert_data = []
        for inventory in low_stock_items:
            alert_data.append({
                'product_name': inventory.product.name,
                'product_sku': inventory.product.sku,
                'current_stock': inventory.quantity,
                'minimum_level': inventory.minimum_stock_level,
                'reorder_point': inventory.reorder_point
            })
        
        # Send email alert to administrators
        admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
        if admin_emails:
            context = {
                'low_stock_items': alert_data,
                'total_items': len(alert_data),
                'check_time': timezone.now()
            }
            
            send_email_task.delay(
                subject=f"Low Stock Alert - {len(alert_data)} items need attention",
                message=f"There are {len(alert_data)} items with low stock levels.",
                recipient_list=list(admin_emails),
                template_name='emails/inventory_alert.html',
                context=context
            )
        
        logger.info(f"Inventory check completed. Found {len(alert_data)} low stock items")
        return {"status": "success", "low_stock_count": len(alert_data), "items": alert_data}
        
    except Exception as exc:
        logger.error(f"Inventory check failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id: int):
    """
    Send order confirmation email to customer.
    """
    try:
        # Import models inside the task
        from apps.orders.models import Order
        from apps.notifications.models import Notification
        
        logger.info(f"Sending order confirmation email for order {order_id}")
        
        order = Order.objects.get(id=order_id)
        
        context = {
            'order': order,
            'customer': order.user,
            'order_items': order.items.all(),
            'frontend_url': settings.FRONTEND_URL
        }
        
        send_email_task.delay(
            subject=f"Order Confirmation - #{order.order_number}",
            message=f"Your order #{order.order_number} has been confirmed.",
            recipient_list=[order.user.email],
            template_name='emails/order_confirmation.html',
            context=context
        )
        
        # Create in-app notification
        Notification.objects.create(
            user=order.user,
            title=f"Order Confirmed - #{order.order_number}",
            message=f"Your order #{order.order_number} has been confirmed and is being processed.",
            notification_type="ORDER_CONFIRMATION",
            reference_id=str(order.id)
        )
        
        logger.info(f"Order confirmation email sent for order {order_id}")
        return {"status": "success", "order_id": order_id}
        
    except Exception as exc:
        logger.error(f"Order confirmation email failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_status_update_notification(self, order_id: int, status: str):
    """
    Send order status update notification via email and SMS.
    """
    try:
        # Import models inside the task
        from apps.orders.models import Order
        from apps.notifications.models import Notification
        
        logger.info(f"Sending order status update notification for order {order_id}")
        
        order = Order.objects.get(id=order_id)
        
        # Email notification
        context = {
            'order': order,
            'customer': order.user,
            'new_status': status,
            'frontend_url': settings.FRONTEND_URL
        }
        
        send_email_task.delay(
            subject=f"Order Update - #{order.order_number}",
            message=f"Your order #{order.order_number} status has been updated to {status}.",
            recipient_list=[order.user.email],
            template_name='emails/order_status_update.html',
            context=context
        )
        
        # SMS notification if phone number is available
        if hasattr(order.user, 'phone') and order.user.phone:
            sms_message = f"Your order #{order.order_number} status: {status}"
            send_sms_task.delay(
                phone_number=order.user.phone,
                message=sms_message
            )
        
        # Create in-app notification
        Notification.objects.create(
            user=order.user,
            title=f"Order Update - #{order.order_number}",
            message=f"Your order status has been updated to {status}",
            notification_type="ORDER_STATUS_UPDATE",
            reference_id=str(order.id)
        )
        
        logger.info(f"Order status update notification sent for order {order_id}")
        return {"status": "success", "order_id": order_id, "new_status": status}
        
    except Exception as exc:
        logger.error(f"Order status update notification failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_id: int):
    """
    Send welcome email to new user.
    """
    try:
        # Import models inside the task
        from apps.authentication.models import User
        from apps.notifications.models import Notification
        
        logger.info(f"Sending welcome email to user {user_id}")
        
        user = User.objects.get(id=user_id)
        
        context = {
            'user': user,
            'frontend_url': settings.FRONTEND_URL
        }
        
        send_email_task.delay(
            subject="Welcome to our E-commerce Platform!",
            message=f"Welcome {user.first_name or user.username}! Thank you for joining us.",
            recipient_list=[user.email],
            template_name='emails/welcome.html',
            context=context
        )
        
        # Create welcome notification
        Notification.objects.create(
            user=user,
            title="Welcome!",
            message="Welcome to our platform! Start exploring amazing products now!",
            notification_type="WELCOME",
            reference_id=str(user.id)
        )
        
        logger.info(f"Welcome email sent to user {user_id}")
        return {"status": "success", "user_id": user_id}
       
    except Exception as exc:
        logger.error(f"Welcome email failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_inventory_transaction(self, inventory_id: int, transaction_type: str, 
                                quantity: int, reference_number: str = None,
                                notes: str = None, user_id: int = None):
    """
    Process inventory transaction and update stock levels.
    """
    try:
        # Import models inside the task
        from apps.authentication.models import User
        from apps.inventory.models import Inventory, InventoryTransaction
        
        logger.info(f"Processing inventory transaction for inventory {inventory_id}")
        
        inventory = Inventory.objects.select_for_update().get(id=inventory_id)
        user = User.objects.get(id=user_id) if user_id else None
        
        # Create transaction record
        transaction = InventoryTransaction.objects.create(
            inventory=inventory,
            transaction_type=transaction_type,
            quantity=quantity,
            reference_number=reference_number,
            notes=notes,
            created_by=user
        )
        
        # Update inventory quantity
        if transaction_type in ['IN', 'RETURN']:
            inventory.quantity += abs(quantity)
        elif transaction_type == 'OUT':
            inventory.quantity -= abs(quantity)
        
        # Ensure quantity doesn't go negative
        if inventory.quantity < 0:
            inventory.quantity = 0
        
        inventory.save()
       
        # Check if stock level is now below minimum and send alert
        if inventory.quantity <= inventory.minimum_stock_level:
            check_inventory_levels_task.delay()
        
        logger.info(f"Inventory transaction processed successfully for inventory {inventory_id}")
        return {
            "status": "success", 
            "transaction_id": transaction.id,
            "new_quantity": inventory.quantity
        }
        
    except Exception as exc:
        logger.error(f"Inventory transaction failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def cleanup_old_notifications(self, days_old: int = 30):
    """
    Clean up old notifications to prevent database bloat.
    """
    try:
        # Import models inside the task
        from apps.notifications.models import Notification
        
        logger.info(f"Cleaning up notifications older than {days_old} days")
        
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        # Delete old read notifications
        deleted_count, _ = Notification.objects.filter(
            created_at__lt=cutoff_date,
            is_read=True
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        return {"status": "success", "deleted_count": deleted_count}
        
    except Exception as exc:
        logger.error(f"Notification cleanup failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_daily_inventory_report(self):
    """
    Send daily inventory report to administrators.
    """
    try:
        # Import models inside the task
        from apps.authentication.models import User
        from apps.inventory.models import Inventory
        from apps.products.models import Product
        from apps.notifications.models import Notification
        
        logger.info("Generating daily inventory report")
        
        # Get inventory statistics
        total_products = Product.objects.filter(is_active=True).count()
        low_stock_count = Inventory.objects.filter(
            quantity__lte=models.F('minimum_stock_level')
        ).count()
        out_of_stock_count = Inventory.objects.filter(quantity=0).count()
        
        # Get top low stock items
        low_stock_items = Inventory.objects.filter(
            quantity__lte=models.F('minimum_stock_level')
        ).select_related('product').order_by('quantity')[:10]
        
        # Prepare report data
        report_data = {
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'low_stock_items': [
                {
                    'product_name': item.product.name,
                    'sku': item.product.sku,
                    'current_stock': item.quantity,
                    'minimum_level': item.minimum_stock_level
                }
                for item in low_stock_items
            ],
            'report_date': timezone.now().date()
        }
        
        # Send report to administrators
        admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
        if admin_emails:
            send_email_task.delay(
                subject=f"Daily Inventory Report - {timezone.now().date()}",
                message=f"Daily inventory report with {low_stock_count} low stock items.",
                recipient_list=list(admin_emails),
                template_name='emails/daily_inventory_report.html',
                context=report_data
            )
        
        logger.info("Daily inventory report sent successfully")
        return {"status": "success", "report_data": report_data}
        
    except Exception as exc:
        logger.error(f"Daily inventory report failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_payment_status_task(self, payment_id: int = None):
    """
    Sync payment status with payment gateway for pending payments.
    """
    try:
        # Import models inside the task
        from apps.payments.models import Payment
        
        logger.info(f"Syncing payment status for payment {payment_id or 'all pending'}")
        
        if payment_id:
            # Sync specific payment
            try:
                payment = Payment.objects.get(id=payment_id, status='PENDING')
                payments_to_sync = [payment]
            except Payment.DoesNotExist:
                logger.warning(f"Payment {payment_id} not found or not pending")
                return {"status": "failed", "error": "Payment not found"}
        else:
            # Get pending payments from last 24 hours
            cutoff_time = timezone.now() - timedelta(hours=24)
            payments_to_sync = Payment.objects.filter(
                status='PENDING',
                created_at__gte=cutoff_time
            ).select_related('order')
        
        synced_count = 0
        failed_count = 0
        
        for payment in payments_to_sync:
            try:
                # For now, just log the sync attempt
                logger.info(f"Would sync payment {payment.id} with gateway")
                synced_count += 1
                
            except Exception as e:
                logger.error(f"Failed to sync payment {payment.id}: {str(e)}")
                failed_count += 1
        
        logger.info(f"Payment sync completed. Synced: {synced_count}, Failed: {failed_count}")
        return {
            "status": "success", 
            "synced_count": synced_count, 
            "failed_count": failed_count
        }
        
    except Exception as exc:
        logger.error(f"Payment status sync failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_abandoned_cart_reminders(self):
    """
    Send reminders to users with abandoned carts.
    """
    try:
        # Import models inside the task
        from apps.authentication.models import User
        from apps.cart.models import Cart
        from apps.orders.models import Order
        from apps.notifications.models import Notification
        
        logger.info("Sending abandoned cart reminders")
        
        # Find carts abandoned for more than 1 hour with items
        cutoff_time = timezone.now() - timedelta(hours=1)
        abandoned_carts = Cart.objects.filter(
            updated_at__lt=cutoff_time,
            items__isnull=False
        ).select_related('user').prefetch_related('items__product').distinct()
        
        reminder_count = 0
        for cart in abandoned_carts:
            try:
                # Check if user hasn't placed any recent orders
                recent_orders = Order.objects.filter(
                    user=cart.user,
                    created_at__gte=cutoff_time
                ).exists()
                
                if not recent_orders:
                    # Send reminder email
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
        raise self.retry(exc=exc)