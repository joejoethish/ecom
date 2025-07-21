"""
Background tasks package for the e-commerce platform.
"""
from .tasks import (
    send_email_task,
    send_sms_task,
    check_inventory_levels_task,
    send_order_confirmation_email,
    send_order_status_update_notification,
    send_welcome_email,
    process_inventory_transaction,
    cleanup_old_notifications,
    send_daily_inventory_report,
    sync_payment_status_task,
    send_abandoned_cart_reminders
)

# Import monitoring tasks
from .inventory_monitoring import check_inventory_expiry_task
from .order_monitoring import monitor_order_fulfillment_task
from .payment_monitoring import monitor_failed_payments_task
from .cart_monitoring import monitor_cart_price_changes

# Import monitoring utilities
from .monitoring import TaskMonitor, TaskRetryHandler, task_monitor_decorator, TaskHealthChecker