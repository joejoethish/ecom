"""
Payment monitoring tasks for the e-commerce platform.
"""
import logging
from typing import Dict, Any, List, Optional
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

# Import models
from apps.payments.models import Payment
from apps.orders.models import Order, OrderTracking
from apps.authentication.models import User
from apps.notifications.models import Notification

# Import monitoring utilities
from .monitoring import TaskMonitor, TaskRetryHandler, task_monitor_decorator
from .tasks import send_email_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
@task_monitor_decorator
def sync_payment_status_task(self, payment_id: Optional[int] = None):
    """
    Sync payment status with payment gateways for pending payments.
    
    Args:
        payment_id: Specific payment ID to sync, if None syncs all pending payments
    """
    try:
        logger.info(f"Syncing payment status with gateways{f' for payment {payment_id}' if payment_id else ''}")
        
        from apps.payments.models import Payment
        
        if payment_id:
            # Sync specific payment
            try:
                payment = Payment.objects.get(id=payment_id, status='PENDING')
                payments_to_sync = [payment]
            except Payment.DoesNotExist:
                logger.warning(f"Payment {payment_id} not found or not pending")
                return {"status": "success", "synced_count": 0, "message": "Payment not found or not pending"}
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
                # Implement actual payment gateway status sync based on payment method
                gateway_status = None
                
                if payment.payment_method.gateway == 'RAZORPAY':
                    # Sync with Razorpay
                    gateway_status = sync_razorpay_payment_status(payment)
                elif payment.payment_method.gateway == 'STRIPE':
                    # Sync with Stripe
                    gateway_status = sync_stripe_payment_status(payment)
                else:
                    logger.info(f"No sync implementation for gateway {payment.payment_method.gateway}")
                    continue
                
                if gateway_status:
                    # Update payment status based on gateway response
                    old_status = payment.status
                    payment.status = gateway_status.get('status', payment.status)
                    payment.gateway_response = gateway_status
                    
                    if payment.status == 'COMPLETED' and old_status != 'COMPLETED':
                        payment.payment_date = timezone.now()
                        
                        # Create order tracking event
                        OrderTracking.objects.create(
                            order=payment.order,
                            status=payment.order.status,
                            description=f"Payment of {payment.amount} {payment.currency} received via {payment.payment_method.name}"
                        )
                        
                        # Create notification for user
                        Notification.objects.create(
                            user=payment.user,
                            title="Payment Confirmed",
                            message=f"Your payment of {payment.amount} {payment.currency} for order #{payment.order.order_number} has been confirmed.",
                            notification_type="PAYMENT_CONFIRMED",
                            reference_id=str(payment.order.id)
                        )
                    
                    payment.save(update_fields=['status', 'gateway_response', 'payment_date'])
                    
                    logger.info(f"Payment {payment.id} status updated from {old_status} to {payment.status}")
                    synced_count += 1
                else:
                    logger.warning(f"No status update received for payment {payment.id}")
                
            except Exception as e:
                logger.error(f"Failed to sync payment {payment.id}: {str(e)}")
                failed_count += 1
        
        logger.info(f"Payment status sync completed. Synced {synced_count} payments, {failed_count} failed")
        return {
            "status": "success", 
            "synced_count": synced_count, 
            "failed_count": failed_count
        }
        
    except Exception as exc:
        logger.error(f"Payment status sync failed: {str(exc)}")
        TaskRetryHandler.retry_task(self, exc)
        return {"status": "failed", "error": str(exc)}


def sync_razorpay_payment_status(payment):
    """
    Sync payment status with Razorpay gateway.
    
    Args:
        payment: Payment instance
        
    Returns:
        dict: Gateway response with status
    """
    try:
        # TODO: Implement actual Razorpay API call
        # This is a placeholder implementation
        logger.info(f"Syncing Razorpay payment {payment.gateway_payment_id}")
        
        # Simulate API call
        # In production, this would be:
        # import razorpay
        # client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        # payment_details = client.payment.fetch(payment.gateway_payment_id)
        
        # For now, return a mock response
        return {
            "status": "COMPLETED",  # This would come from actual API response
            "gateway_payment_id": payment.gateway_payment_id,
            "synced_at": timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Razorpay sync failed for payment {payment.id}: {str(e)}")
        return None


def sync_stripe_payment_status(payment):
    """
    Sync payment status with Stripe gateway.
    
    Args:
        payment: Payment instance
        
    Returns:
        dict: Gateway response with status
    """
    try:
        # TODO: Implement actual Stripe API call
        # This is a placeholder implementation
        logger.info(f"Syncing Stripe payment {payment.gateway_payment_id}")
        
        # Simulate API call
        # In production, this would be:
        # import stripe
        # stripe.api_key = settings.STRIPE_SECRET_KEY
        # payment_intent = stripe.PaymentIntent.retrieve(payment.gateway_payment_id)
        
        # For now, return a mock response
        return {
            "status": "COMPLETED",  # This would come from actual API response
            "gateway_payment_id": payment.gateway_payment_id,
            "synced_at": timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Stripe sync failed for payment {payment.id}: {str(e)}")
        return None


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@task_monitor_decorator
def monitor_failed_payments_task(self, days: int = 3):
    """
    Monitor failed payments and send reminders to customers.
    
    Args:
        days: Number of days to look back for failed payments
    """
    try:
        logger.info(f"Monitoring failed payments from the last {days} days")
        
        # Calculate the threshold date
        threshold_date = timezone.now() - timedelta(days=days)
        
        # Find failed payments from the last few days
        failed_payments = Payment.objects.filter(
            status='FAILED',
            updated_at__gte=threshold_date
        ).select_related('user', 'order')
        
        if not failed_payments.exists():
            logger.info("No failed payments found in the specified period")
            return {"status": "success", "failed_count": 0}
        
        reminder_count = 0
        for payment in failed_payments:
            try:
                # Check if the order is still pending payment
                if payment.order.payment_status == 'failed':
                    # Send reminder email
                    context = {
                        'user': payment.user,
                        'order': payment.order,
                        'payment': payment,
                        'frontend_url': settings.FRONTEND_URL
                    }
                    
                    send_email_task.delay(
                        subject=f"Complete Your Order #{payment.order.order_number}",
                        message=f"Your order #{payment.order.order_number} is waiting for payment. Please complete your purchase.",
                        recipient_list=[payment.user.email],
                        template_name='emails/payment_reminder.html',
                        context=context
                    )
                    
                    # Create in-app notification
                    Notification.objects.create(
                        user=payment.user,
                        title="Complete Your Order",
                        message=f"Your order #{payment.order.order_number} is waiting for payment. Please complete your purchase.",
                        notification_type="PAYMENT_REMINDER",
                        reference_id=str(payment.order.id)
                    )
                    
                    reminder_count += 1
            except Exception as e:
                logger.error(f"Failed to send payment reminder for payment {payment.id}: {str(e)}")
        
        logger.info(f"Payment reminders sent: {reminder_count}")
        return {"status": "success", "reminder_count": reminder_count}
        
    except Exception as exc:
        logger.error(f"Failed payment monitoring failed: {str(exc)}")
        TaskRetryHandler.retry_task(self, exc)
        return {"status": "failed", "error": str(exc)}