"""
Inventory monitoring tasks for the e-commerce platform.
"""
import logging
from typing import Dict, Any, List, Optional
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

# Import models
from apps.inventory.models import Inventory
from apps.products.models import Product
from apps.authentication.models import User
from apps.notifications.models import Notification

# Import monitoring utilities
from .monitoring import TaskMonitor, TaskRetryHandler, task_monitor_decorator
from .tasks import send_email_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@task_monitor_decorator
def check_inventory_expiry_task(self, days_threshold: int = 30):
    """
    Check inventory for items approaching expiry date and send alerts.
    
    Args:
        days_threshold: Number of days threshold for expiry warning
    """
    try:
        logger.info(f"Checking inventory for items expiring within {days_threshold} days")
        
        # Calculate the threshold date
        threshold_date = timezone.now().date() + timedelta(days=days_threshold)
        
        # Find products with expiry dates approaching the threshold
        # Note: This assumes Inventory model has an expiry_date field
        expiring_items = Inventory.objects.filter(
            expiry_date__lte=threshold_date,
            expiry_date__gt=timezone.now().date(),
            quantity__gt=0
        ).select_related('product')
        
        if not expiring_items.exists():
            logger.info("No expiring items found")
            return {"status": "success", "expiring_count": 0}
        
        # Prepare alert data
        alert_data = []
        for inventory in expiring_items:
            days_until_expiry = (inventory.expiry_date - timezone.now().date()).days
            alert_data.append({
                'product_name': inventory.product.name,
                'product_sku': inventory.product.sku,
                'current_stock': inventory.quantity,
                'expiry_date': inventory.expiry_date,
                'days_until_expiry': days_until_expiry
            })
        
        # Send email alert to administrators
        admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
        if admin_emails:
            context = {
                'expiring_items': alert_data,
                'total_items': len(alert_data),
                'check_time': timezone.now(),
                'days_threshold': days_threshold,
                'frontend_url': settings.FRONTEND_URL
            }
            
            send_email_task.delay(
                subject=f"Inventory Expiry Alert - {len(alert_data)} items expiring soon",
                message=f"There are {len(alert_data)} items expiring within {days_threshold} days.",
                recipient_list=list(admin_emails),
                template_name='emails/inventory_expiry_alert.html',
                context=context
            )
            
            # Create in-app notifications for admins
            for admin_id in User.objects.filter(is_staff=True).values_list('id', flat=True):
                Notification.objects.create(
                    user_id=admin_id,
                    title=f"Inventory Expiry Alert - {len(alert_data)} items",
                    message=f"There are {len(alert_data)} items expiring within {days_threshold} days.",
                    notification_type="INVENTORY_EXPIRY",
                    reference_id="inventory_expiry"
                )
        
        logger.info(f"Inventory expiry check completed. Found {len(alert_data)} expiring items")
        return {"status": "success", "expiring_count": len(alert_data), "items": alert_data}
        
    except Exception as exc:
        logger.error(f"Inventory expiry check failed: {str(exc)}")
        TaskRetryHandler.retry_task(self, exc)
        return {"status": "failed", "error": str(exc)}