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
    
    # Clean up expired password reset tokens every 6 hours
    'cleanup-password-reset-tokens': {
        'task': 'apps.authentication.tasks.cleanup_expired_password_reset_tokens',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
        'options': {'queue': 'maintenance'}
    },
    
    # Clean up old password reset attempts daily at 3 AM
    'cleanup-password-reset-attempts': {
        'task': 'apps.authentication.tasks.cleanup_old_password_reset_attempts',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
        'options': {'queue': 'maintenance'}
    },
    
    # Monitor password reset token performance daily at 6 AM
    'monitor-password-reset-performance': {
        'task': 'apps.authentication.tasks.monitor_password_reset_token_performance',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6 AM
        'options': {'queue': 'monitoring'}
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
    
    # Database maintenance tasks
    
    # Daily database maintenance at 1 AM
    'daily-database-maintenance': {
        'task': 'tasks.database_maintenance_tasks.run_daily_maintenance_task',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
        'options': {'queue': 'maintenance'}
    },
    
    # Analyze tables every 6 hours
    'analyze-database-tables': {
        'task': 'tasks.database_maintenance_tasks.analyze_tables_task',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
        'options': {'queue': 'maintenance'}
    },
    
    # Optimize fragmented tables daily at 2:30 AM
    'optimize-fragmented-tables': {
        'task': 'tasks.database_maintenance_tasks.optimize_fragmented_tables_task',
        'schedule': crontab(hour=2, minute=30),  # Daily at 2:30 AM
        'options': {'queue': 'maintenance'}
    },
    
    # Clean up old data daily at 3:30 AM
    'cleanup-old-data': {
        'task': 'tasks.database_maintenance_tasks.cleanup_old_data_task',
        'schedule': crontab(hour=3, minute=30),  # Daily at 3:30 AM
        'options': {'queue': 'maintenance'}
    },
    
    # Collect database statistics every 4 hours
    'collect-database-statistics': {
        'task': 'tasks.database_maintenance_tasks.collect_database_statistics_task',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
        'options': {'queue': 'monitoring'}
    },
    
    # Generate maintenance recommendations daily at 8:30 AM
    'generate-maintenance-recommendations': {
        'task': 'tasks.database_maintenance_tasks.generate_maintenance_recommendations_task',
        'schedule': crontab(hour=8, minute=30),  # Daily at 8:30 AM
        'options': {'queue': 'monitoring'}
    },
    
    # Archive old orders weekly on Sunday at 4 AM
    'archive-old-orders': {
        'task': 'tasks.database_maintenance_tasks.archive_old_orders_task',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),  # Sunday at 4 AM
        'options': {'queue': 'maintenance'}
    },
    
    # Rebuild indexes weekly on Saturday at 5 AM
    'rebuild-database-indexes': {
        'task': 'tasks.database_maintenance_tasks.rebuild_indexes_task',
        'schedule': crontab(hour=5, minute=0, day_of_week=6),  # Saturday at 5 AM
        'options': {'queue': 'maintenance'}
    },
    
    # Weekly comprehensive maintenance on Sunday at 6 AM
    'weekly-database-maintenance': {
        'task': 'tasks.database_maintenance_tasks.weekly_maintenance_task',
        'schedule': crontab(hour=6, minute=0, day_of_week=0),  # Sunday at 6 AM
        'options': {'queue': 'maintenance'}
    },
    
    # Performance monitoring tasks
    
    # Collect performance metrics every 5 minutes
    'collect-performance-metrics': {
        'task': 'tasks.performance_monitoring_tasks.collect_performance_metrics',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'monitoring'}
    },
    
    # Analyze query performance every 15 minutes
    'analyze-query-performance': {
        'task': 'tasks.performance_monitoring_tasks.analyze_query_performance',
        'schedule': crontab(minute='*/15'),
        'options': {'queue': 'monitoring'}
    },
    
    # Detect performance regressions every 10 minutes
    'detect-performance-regressions': {
        'task': 'tasks.performance_monitoring_tasks.detect_performance_regressions',
        'schedule': crontab(minute='*/10'),
        'options': {'queue': 'monitoring'}
    },
    
    # Generate capacity recommendations every 30 minutes
    'generate-capacity-recommendations': {
        'task': 'tasks.performance_monitoring_tasks.generate_capacity_recommendations',
        'schedule': crontab(minute='*/30'),
        'options': {'queue': 'monitoring'}
    },
    
    # Daily performance report at 7 AM
    'daily-performance-report': {
        'task': 'tasks.performance_monitoring_tasks.generate_daily_performance_report',
        'schedule': crontab(hour=7, minute=0),
        'options': {'queue': 'reports'}
    },
    
    # Clean up old performance data daily at 2 AM
    'cleanup-performance-data': {
        'task': 'tasks.performance_monitoring_tasks.cleanup_old_performance_data',
        'schedule': crontab(hour=2, minute=0),
        'options': {'queue': 'maintenance'}
    },
    
    # Update performance baselines weekly on Mondays at 3 AM
    'update-performance-baselines': {
        'task': 'tasks.performance_monitoring_tasks.update_performance_baselines',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),
        'options': {'queue': 'monitoring'}
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
    
    # Authentication tasks
    'apps.authentication.tasks.cleanup_expired_password_reset_tokens': {'queue': 'maintenance'},
    'apps.authentication.tasks.cleanup_old_password_reset_attempts': {'queue': 'maintenance'},
    'apps.authentication.tasks.monitor_password_reset_token_performance': {'queue': 'monitoring'},
    'apps.authentication.tasks.send_password_reset_security_alert': {'queue': 'security'},
    
    # Search tasks
    'apps.search.signals.update_document': {'queue': 'search'},
    'apps.search.signals.delete_document': {'queue': 'search'},
    
    # Database maintenance tasks
    'tasks.database_maintenance_tasks.run_daily_maintenance_task': {'queue': 'maintenance'},
    'tasks.database_maintenance_tasks.analyze_tables_task': {'queue': 'maintenance'},
    'tasks.database_maintenance_tasks.optimize_fragmented_tables_task': {'queue': 'maintenance'},
    'tasks.database_maintenance_tasks.cleanup_old_data_task': {'queue': 'maintenance'},
    'tasks.database_maintenance_tasks.collect_database_statistics_task': {'queue': 'monitoring'},
    'tasks.database_maintenance_tasks.rebuild_indexes_task': {'queue': 'maintenance'},
    'tasks.database_maintenance_tasks.archive_old_orders_task': {'queue': 'maintenance'},
    'tasks.database_maintenance_tasks.generate_maintenance_recommendations_task': {'queue': 'monitoring'},
    'tasks.database_maintenance_tasks.weekly_maintenance_task': {'queue': 'maintenance'},
    'tasks.database_maintenance_tasks.send_maintenance_report': {'queue': 'reports'},
    
    # Performance monitoring tasks
    'tasks.performance_monitoring_tasks.collect_performance_metrics': {'queue': 'monitoring'},
    'tasks.performance_monitoring_tasks.analyze_query_performance': {'queue': 'monitoring'},
    'tasks.performance_monitoring_tasks.detect_performance_regressions': {'queue': 'monitoring'},
    'tasks.performance_monitoring_tasks.generate_capacity_recommendations': {'queue': 'monitoring'},
    'tasks.performance_monitoring_tasks.generate_daily_performance_report': {'queue': 'reports'},
    'tasks.performance_monitoring_tasks.cleanup_old_performance_data': {'queue': 'maintenance'},
    'tasks.performance_monitoring_tasks.update_performance_baselines': {'queue': 'monitoring'},
    'tasks.database_maintenance_tasks.send_maintenance_alert': {'queue': 'alerts'},
    'tasks.database_maintenance_tasks.send_weekly_maintenance_report': {'queue': 'reports'},
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
    'monitoring': {
        'exchange': 'monitoring',
        'routing_key': 'monitoring',
    },
    'security': {
        'exchange': 'security',
        'routing_key': 'security',
    },
    'alerts': {
        'exchange': 'alerts',
        'routing_key': 'alerts',
    },
}