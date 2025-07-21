"""
Periodic task schedules for the e-commerce platform.
"""
from celery.schedules import crontab
from django.conf import settings

# Periodic task schedule configuration
CELERY_BEAT_SCHEDULE = {
    # Check inventory levels every hour during business hours
    'check-inventory-levels': {
        'task': 'tasks.tasks.check_inventory_levels_task',
        'schedule': crontab(minute=0),  # Every hour
        'options': {'queue': 'inventory'}
    },
    
    # Clean up old notifications daily at 2 AM
    'cleanup-old-notifications': {
        'task': 'tasks.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'options': {'queue': 'maintenance'}
    },
    
    # Send daily inventory report to admins
    'daily-inventory-report': {
        'task': 'tasks.tasks.send_daily_inventory_report',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
        'options': {'queue': 'reports'}
    },
    
    # Process pending payment status updates every 15 minutes
    'sync-payment-status': {
        'task': 'tasks.payment_monitoring.sync_payment_status_task',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
        'options': {'queue': 'payments'}
    },
    
    # Send abandoned cart reminders daily at 10 AM
    'abandoned-cart-reminders': {
        'task': 'tasks.cart_monitoring.send_abandoned_cart_reminders',
        'schedule': crontab(hour=10, minute=0),  # Daily at 10 AM
        'options': {'queue': 'marketing'}
    },
    
    # Check inventory expiry dates weekly on Monday at 9 AM
    'check-inventory-expiry': {
        'task': 'tasks.inventory_monitoring.check_inventory_expiry_task',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Monday at 9 AM
        'options': {'queue': 'inventory'}
    },
    
    # Monitor order fulfillment delays daily at 9 AM
    'monitor-order-fulfillment': {
        'task': 'tasks.order_monitoring.monitor_order_fulfillment_task',
        'schedule': crontab(hour=9, minute=30),  # Daily at 9:30 AM
        'options': {'queue': 'orders'}
    },
    
    # Monitor failed payments and send reminders daily at 11 AM
    'monitor-failed-payments': {
        'task': 'tasks.payment_monitoring.monitor_failed_payments_task',
        'schedule': crontab(hour=11, minute=0),  # Daily at 11 AM
        'options': {'queue': 'payments'}
    },
    
    # Monitor cart price changes daily at 7 AM
    'monitor-cart-price-changes': {
        'task': 'tasks.cart_monitoring.monitor_cart_price_changes',
        'schedule': crontab(hour=7, minute=0),  # Daily at 7 AM
        'options': {'queue': 'marketing'}
    },
}

# Task routing configuration
CELERY_TASK_ROUTES = {
    # Email tasks
    'tasks.tasks.send_email_task': {'queue': 'emails'},
    'tasks.tasks.send_order_confirmation_email': {'queue': 'emails'},
    'tasks.tasks.send_order_status_update_notification': {'queue': 'emails'},
    'tasks.tasks.send_welcome_email': {'queue': 'emails'},
    
    # SMS tasks
    'tasks.tasks.send_sms_task': {'queue': 'sms'},
    
    # Inventory tasks
    'tasks.tasks.check_inventory_levels_task': {'queue': 'inventory'},
    'tasks.tasks.process_inventory_transaction': {'queue': 'inventory'},
    'tasks.inventory_monitoring.check_inventory_expiry_task': {'queue': 'inventory'},
    'tasks.tasks.send_daily_inventory_report': {'queue': 'reports'},
    
    # Maintenance tasks
    'tasks.tasks.cleanup_old_notifications': {'queue': 'maintenance'},
    
    # Payment tasks
    'tasks.payment_monitoring.sync_payment_status_task': {'queue': 'payments'},
    'tasks.payment_monitoring.monitor_failed_payments_task': {'queue': 'payments'},
    
    # Marketing tasks
    'tasks.cart_monitoring.send_abandoned_cart_reminders': {'queue': 'marketing'},
    'tasks.cart_monitoring.monitor_cart_price_changes': {'queue': 'marketing'},
    
    # Order tasks
    'tasks.order_monitoring.monitor_order_fulfillment_task': {'queue': 'orders'},
    
    # Search tasks
    'apps.search.signals.update_document': {'queue': 'search'},
    'apps.search.signals.delete_document': {'queue': 'search'},
}

# Queue configuration
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_QUEUES = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'emails': {
        'exchange': 'emails',
        'routing_key': 'emails',
    },
    'sms': {
        'exchange': 'sms',
        'routing_key': 'sms',
    },
    'inventory': {
        'exchange': 'inventory',
        'routing_key': 'inventory',
    },
    'payments': {
        'exchange': 'payments',
        'routing_key': 'payments',
    },
    'maintenance': {
        'exchange': 'maintenance',
        'routing_key': 'maintenance',
    },
    'marketing': {
        'exchange': 'marketing',
        'routing_key': 'marketing',
    },
    'reports': {
        'exchange': 'reports',
        'routing_key': 'reports',
    },
    'orders': {
        'exchange': 'orders',
        'routing_key': 'orders',
    },
    'search': {
        'exchange': 'search',
        'routing_key': 'search',
    },
}