"""
Order monitoring tasks for the e-commerce platform.
"""
import logging
from typing import Dict, Any, List, Optional
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

# Import models
from apps.orders.models import Order
from apps.authentication.models import User
from apps.notifications.models import Notification

# Import monitoring utilities
from .monitoring import TaskMonitor, TaskRetryHandler, task_monitor_decorator
from .tasks import send_email_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@task_monitor_decorator
def monitor_order_fulfillment_task(self, max_days: int = 3):
    """
    Monitor orders that have been confirmed but not shipped within the specified timeframe.
    
    Args:
        max_days: Maximum number of days an order should remain in confirmed status
    """
    try:
        logger.info(f"Monitoring order fulfillment for delays exceeding {max_days} days")
        
        # Calculate the threshold date
        threshold_date = timezone.now() - timedelta(days=max_days)
        
        # Find orders that have been confirmed but not shipped for too long
        delayed_orders = Order.objects.filter(
            status='CONFIRMED',
            updated_at__lt=threshold_date
        ).select_related('user')
        
        if not delayed_orders.exists():
            logger.info("No delayed orders found")
            return {"status": "success", "delayed_count": 0}
        
        # Prepare alert data
        alert_data = []
        for order in delayed_orders:
            days_delayed = (timezone.now() - order.updated_at).days
            alert_data.append({
                'order_number': order.order_number,
                'order_id': order.id,
                'customer_name': f"{order.user.first_name} {order.user.last_name}",
                'order_date': order.created_at,
                'days_delayed': days_delayed
            })
        
        # Send email alert to administrators
        admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
        if admin_emails:
            context = {
                'delayed_orders': alert_data,
                'total_orders': len(alert_data),
                'check_time': timezone.now(),
                'max_days': max_days,
                'frontend_url': settings.FRONTEND_URL
            }
            
            send_email_task.delay(
                subject=f"Order Fulfillment Alert - {len(alert_data)} orders delayed",
                message=f"There are {len(alert_data)} orders that have been confirmed but not shipped for more than {max_days} days.",
                recipient_list=list(admin_emails),
                template_name='emails/order_fulfillment_alert.html',
                context=context
            )
            
            # Create in-app notifications for admins
            for admin_id in User.objects.filter(is_staff=True).values_list('id', flat=True):
                Notification.objects.create(
                    user_id=admin_id,
                    title=f"Order Fulfillment Alert - {len(alert_data)} orders",
                    message=f"There are {len(alert_data)} orders delayed in fulfillment for more than {max_days} days.",
                    notification_type="ORDER_FULFILLMENT_DELAY",
                    reference_id="order_fulfillment_delay"
                )
        
        logger.info(f"Order fulfillment monitoring completed. Found {len(alert_data)} delayed orders")
        return {"status": "success", "delayed_count": len(alert_data), "orders": alert_data}
        
    except Exception as exc:
        logger.error(f"Order fulfillment monitoring failed: {str(exc)}")
        TaskRetryHandler.retry_task(self, exc)
        return {"status": "failed", "error": str(exc)}