"""
Maintenance Coordinator Settings

This module provides default settings and configuration for the ongoing maintenance coordinator.
These settings can be overridden in Django settings.py
"""

from datetime import timedelta

# Coordinator Configuration
MAINTENANCE_COORDINATOR_INTERVAL = 60  # seconds between coordinator checks
ENABLE_DATABASE_MONITORING = True
ENABLE_BACKUP_TESTING = True
ENABLE_DISASTER_RECOVERY = True

# Maintenance Windows
MAINTENANCE_WINDOW_START = '02:00'  # 2 AM
MAINTENANCE_WINDOW_END = '06:00'    # 6 AM

# Notification Settings
MAINTENANCE_NOTIFICATION_EMAILS = []  # Override in settings.py
SEND_MAINTENANCE_REPORTS = True
SEND_MAINTENANCE_ALERTS = True
SEND_WEEKLY_MAINTENANCE_REPORTS = True

# Concurrency Settings
MAX_CONCURRENT_MAINTENANCE = 2

# Testing Frequencies
BACKUP_TEST_FREQUENCY_DAYS = 7
DISASTER_RECOVERY_TEST_FREQUENCY_DAYS = 30

# Database Alert Thresholds
DB_ALERT_CONNECTION_WARNING = 80.0      # Connection usage %
DB_ALERT_CONNECTION_CRITICAL = 95.0
DB_ALERT_QUERY_TIME_WARNING = 2.0       # Query time in seconds
DB_ALERT_QUERY_TIME_CRITICAL = 5.0
DB_ALERT_SLOW_QUERIES_WARNING = 10.0    # Slow queries per minute
DB_ALERT_SLOW_QUERIES_CRITICAL = 50.0
DB_ALERT_REPLICATION_WARNING = 5.0      # Replication lag in seconds
DB_ALERT_REPLICATION_CRITICAL = 30.0
DB_ALERT_CPU_WARNING = 80.0             # CPU usage %
DB_ALERT_CPU_CRITICAL = 95.0
DB_ALERT_MEMORY_WARNING = 85.0          # Memory usage %
DB_ALERT_MEMORY_CRITICAL = 95.0
DB_ALERT_DISK_WARNING = 85.0            # Disk usage %
DB_ALERT_DISK_CRITICAL = 95.0
DB_ALERT_HEALTH_WARNING = 70.0          # Health score
DB_ALERT_HEALTH_CRITICAL = 50.0

# Database Maintenance Thresholds
DB_FRAGMENTATION_THRESHOLD = 30.0       # Fragmentation % to trigger optimization
DB_INDEX_SIZE_THRESHOLD = 100.0         # Index size in MB to consider for optimization
DB_ANALYZE_THRESHOLD_DAYS = 7           # Days between table analysis

# Data Cleanup Rules
DATABASE_CLEANUP_RULES = {
    'django_session': {
        'table': 'django_session',
        'date_column': 'expire_date',
        'retention_days': 30,
        'cleanup_type': 'delete'
    },
    'admin_logentry': {
        'table': 'django_admin_log',
        'date_column': 'action_time',
        'retention_days': 90,
        'cleanup_type': 'archive'
    },
    'auth_user_old_passwords': {
        'table': 'auth_user_old_passwords',
        'date_column': 'created_at',
        'retention_days': 365,
        'cleanup_type': 'delete'
    },
    'notifications': {
        'table': 'notifications_notification',
        'date_column': 'created_at',
        'retention_days': 60,
        'cleanup_type': 'delete',
        'additional_criteria': 'is_read = 1'
    },
    'audit_logs': {
        'table': 'audit_log',
        'date_column': 'timestamp',
        'retention_days': 180,
        'cleanup_type': 'archive'
    },
    'password_reset_attempts': {
        'table': 'auth_password_reset_attempt',
        'date_column': 'created_at',
        'retention_days': 30,
        'cleanup_type': 'delete'
    }
}

# Custom Maintenance Schedules
# Override this in settings.py to add custom schedules
CUSTOM_MAINTENANCE_SCHEDULES = {}

# Example custom schedules:
# CUSTOM_MAINTENANCE_SCHEDULES = {
#     'hourly_health_check': {
#         'database_alias': 'default',
#         'task_type': 'health_check',
#         'schedule_cron': '0 * * * *',  # Every hour
#         'enabled': True
#     },
#     'bi_weekly_deep_clean': {
#         'database_alias': 'default',
#         'task_type': 'deep_clean',
#         'schedule_cron': '0 3 */14 * *',  # Every 14 days at 3 AM
#         'enabled': True
#     }
# }

# Celery Task Settings
CELERY_TASK_ROUTES = {
    'tasks.database_maintenance_tasks.*': {'queue': 'maintenance'},
}

CELERY_BEAT_SCHEDULE = {
    # These are handled by the coordinator, but can be used as fallback
    'daily-maintenance-fallback': {
        'task': 'tasks.database_maintenance_tasks.run_daily_maintenance_task',
        'schedule': timedelta(days=1),
        'args': ('default', False),
        'options': {'queue': 'maintenance'}
    },
    'weekly-maintenance-fallback': {
        'task': 'tasks.database_maintenance_tasks.weekly_maintenance_task',
        'schedule': timedelta(weeks=1),
        'args': ('default',),
        'options': {'queue': 'maintenance'}
    },
}

# Logging Configuration
MAINTENANCE_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'maintenance': {
            'format': '{levelname} {asctime} {name} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'maintenance_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/maintenance.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'maintenance',
        },
        'maintenance_console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'maintenance',
        },
    },
    'loggers': {
        'core.ongoing_maintenance_coordinator': {
            'handlers': ['maintenance_file', 'maintenance_console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.database_maintenance': {
            'handlers': ['maintenance_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.database_monitor': {
            'handlers': ['maintenance_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'tasks.database_maintenance_tasks': {
            'handlers': ['maintenance_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Performance Monitoring Settings
PERFORMANCE_MONITORING_ENABLED = True
PERFORMANCE_METRICS_RETENTION_DAYS = 30
PERFORMANCE_ALERT_THRESHOLDS = {
    'query_time_increase_percent': 20,
    'connection_usage_increase_percent': 15,
    'disk_usage_increase_percent': 10,
    'memory_usage_increase_percent': 15,
}

# Backup Testing Settings
BACKUP_TEST_ENABLED = True
BACKUP_TEST_SAMPLE_SIZE = 3  # Number of backups to test randomly
BACKUP_INTEGRITY_CHECK_TIMEOUT = 300  # seconds

# Disaster Recovery Settings
DISASTER_RECOVERY_ENABLED = True
DISASTER_RECOVERY_TEST_TIMEOUT = 600  # seconds
DISASTER_RECOVERY_NOTIFICATION_DELAY = 300  # seconds before sending alerts

# Security Monitoring Settings
SECURITY_MONITORING_ENABLED = True
SECURITY_AUDIT_RETENTION_DAYS = 365
SECURITY_ALERT_THRESHOLDS = {
    'failed_login_attempts_per_hour': 10,
    'suspicious_query_patterns_per_hour': 5,
    'privilege_escalation_attempts_per_day': 1,
}

# Capacity Planning Settings
CAPACITY_PLANNING_ENABLED = True
CAPACITY_FORECAST_DAYS = 90
CAPACITY_WARNING_THRESHOLD_DAYS = 30  # Days before projected capacity limit

# Integration Settings
MONITORING_INTEGRATIONS = {
    'prometheus': {
        'enabled': False,
        'endpoint': 'http://localhost:9090',
        'job_name': 'mysql_maintenance'
    },
    'grafana': {
        'enabled': False,
        'dashboard_url': 'http://localhost:3000/d/mysql-maintenance'
    },
    'slack': {
        'enabled': False,
        'webhook_url': '',
        'channel': '#database-alerts'
    },
    'pagerduty': {
        'enabled': False,
        'integration_key': '',
        'service_key': ''
    }
}

# Health Check Settings
HEALTH_CHECK_ENABLED = True
HEALTH_CHECK_INTERVAL = 300  # seconds
HEALTH_CHECK_TIMEOUT = 30    # seconds
HEALTH_CHECK_ENDPOINTS = [
    'database_connection',
    'backup_system',
    'monitoring_system',
    'replication_status'
]