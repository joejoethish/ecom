"""
Debugging system configuration settings.
"""
from decouple import config

# E2E Workflow Debugging System Configuration
DEBUGGING_SYSTEM = {
    'ENABLED': config('DEBUGGING_SYSTEM_ENABLED', default=True, cast=bool),
    'CORRELATION_ID_HEADER': 'X-Correlation-ID',
    'PERFORMANCE_MONITORING_ENABLED': config('PERFORMANCE_MONITORING_ENABLED', default=True, cast=bool),
    'WORKFLOW_TRACING_ENABLED': config('WORKFLOW_TRACING_ENABLED', default=True, cast=bool),
    'ERROR_TRACKING_ENABLED': config('ERROR_TRACKING_ENABLED', default=True, cast=bool),
    'ROUTE_DISCOVERY_ENABLED': config('ROUTE_DISCOVERY_ENABLED', default=True, cast=bool),
    'API_VALIDATION_ENABLED': config('API_VALIDATION_ENABLED', default=True, cast=bool),
    'DATABASE_MONITORING_ENABLED': config('DATABASE_MONITORING_ENABLED', default=True, cast=bool),
}

# Performance Monitoring Configuration
PERFORMANCE_MONITORING = {
    'METRICS_RETENTION_DAYS': config('PERFORMANCE_METRICS_RETENTION_DAYS', default=30, cast=int),
    'REAL_TIME_UPDATES': config('PERFORMANCE_REAL_TIME_UPDATES', default=True, cast=bool),
    'ALERT_THRESHOLDS': {
        'api_response_time_warning': config('API_RESPONSE_TIME_WARNING', default=500, cast=int),  # ms
        'api_response_time_critical': config('API_RESPONSE_TIME_CRITICAL', default=2000, cast=int),  # ms
        'database_query_time_warning': config('DB_QUERY_TIME_WARNING', default=100, cast=int),  # ms
        'database_query_time_critical': config('DB_QUERY_TIME_CRITICAL', default=1000, cast=int),  # ms
        'memory_usage_warning': config('MEMORY_USAGE_WARNING', default=80, cast=int),  # percentage
        'memory_usage_critical': config('MEMORY_USAGE_CRITICAL', default=95, cast=int),  # percentage
        'error_rate_warning': config('ERROR_RATE_WARNING', default=5, cast=int),  # percentage
        'error_rate_critical': config('ERROR_RATE_CRITICAL', default=10, cast=int),  # percentage
    },
    'COLLECTION_INTERVAL': config('PERFORMANCE_COLLECTION_INTERVAL', default=30, cast=int),  # seconds
    'BATCH_SIZE': config('PERFORMANCE_BATCH_SIZE', default=100, cast=int),
}

# Workflow Tracing Configuration
WORKFLOW_TRACING = {
    'TRACE_RETENTION_DAYS': config('TRACE_RETENTION_DAYS', default=7, cast=int),
    'MAX_TRACE_STEPS': config('MAX_TRACE_STEPS', default=100, cast=int),
    'TIMEOUT_SECONDS': config('WORKFLOW_TIMEOUT_SECONDS', default=300, cast=int),  # 5 minutes
    'AUTO_CLEANUP_ENABLED': config('TRACE_AUTO_CLEANUP_ENABLED', default=True, cast=bool),
    'DETAILED_LOGGING': config('TRACE_DETAILED_LOGGING', default=False, cast=bool),
}

# Error Tracking Configuration
ERROR_TRACKING = {
    'LOG_RETENTION_DAYS': config('ERROR_LOG_RETENTION_DAYS', default=90, cast=int),
    'MAX_STACK_TRACE_LENGTH': config('MAX_STACK_TRACE_LENGTH', default=5000, cast=int),
    'ALERT_ON_CRITICAL': config('ERROR_ALERT_ON_CRITICAL', default=True, cast=bool),
    'ALERT_ON_HIGH_FREQUENCY': config('ERROR_ALERT_ON_HIGH_FREQUENCY', default=True, cast=bool),
    'HIGH_FREQUENCY_THRESHOLD': config('ERROR_HIGH_FREQUENCY_THRESHOLD', default=10, cast=int),  # errors per minute
    'GROUPING_ENABLED': config('ERROR_GROUPING_ENABLED', default=True, cast=bool),
    'AUTO_RESOLUTION_ENABLED': config('ERROR_AUTO_RESOLUTION_ENABLED', default=False, cast=bool),
}

# Route Discovery Configuration
ROUTE_DISCOVERY = {
    'FRONTEND_PATH': config('FRONTEND_PATH', default='../frontend'),
    'SCAN_INTERVAL_HOURS': config('ROUTE_SCAN_INTERVAL_HOURS', default=24, cast=int),
    'AUTO_SCAN_ENABLED': config('ROUTE_AUTO_SCAN_ENABLED', default=True, cast=bool),
    'INCLUDE_PATTERNS': config('ROUTE_INCLUDE_PATTERNS', default='*.tsx,*.ts,*.jsx,*.js', cast=lambda v: [s.strip() for s in v.split(',')]),
    'EXCLUDE_PATTERNS': config('ROUTE_EXCLUDE_PATTERNS', default='node_modules,*.test.*,*.spec.*', cast=lambda v: [s.strip() for s in v.split(',')]),
    'MAX_FILE_SIZE_MB': config('ROUTE_MAX_FILE_SIZE_MB', default=5, cast=int),
}

# API Validation Configuration
API_VALIDATION = {
    'AUTO_VALIDATION_ENABLED': config('API_AUTO_VALIDATION_ENABLED', default=True, cast=bool),
    'VALIDATION_INTERVAL_HOURS': config('API_VALIDATION_INTERVAL_HOURS', default=6, cast=int),
    'TIMEOUT_SECONDS': config('API_VALIDATION_TIMEOUT', default=30, cast=int),
    'RETRY_ATTEMPTS': config('API_VALIDATION_RETRY_ATTEMPTS', default=3, cast=int),
    'INCLUDE_AUTHENTICATION_TESTS': config('API_INCLUDE_AUTH_TESTS', default=True, cast=bool),
    'INCLUDE_PERMISSION_TESTS': config('API_INCLUDE_PERMISSION_TESTS', default=True, cast=bool),
    'GENERATE_TEST_DATA': config('API_GENERATE_TEST_DATA', default=True, cast=bool),
}

# Database Monitoring Configuration
DATABASE_MONITORING = {
    'QUERY_LOGGING_ENABLED': config('DB_QUERY_LOGGING_ENABLED', default=True, cast=bool),
    'SLOW_QUERY_THRESHOLD_MS': config('DB_SLOW_QUERY_THRESHOLD_MS', default=100, cast=int),
    'CONNECTION_MONITORING_ENABLED': config('DB_CONNECTION_MONITORING_ENABLED', default=True, cast=bool),
    'HEALTH_CHECK_INTERVAL': config('DB_HEALTH_CHECK_INTERVAL', default=60, cast=int),  # seconds
    'MIGRATION_VALIDATION_ENABLED': config('DB_MIGRATION_VALIDATION_ENABLED', default=True, cast=bool),
    'INTEGRITY_CHECK_ENABLED': config('DB_INTEGRITY_CHECK_ENABLED', default=True, cast=bool),
    'PERFORMANCE_ANALYSIS_ENABLED': config('DB_PERFORMANCE_ANALYSIS_ENABLED', default=True, cast=bool),
}

# Dashboard Configuration
DEBUGGING_DASHBOARD = {
    'ENABLED': config('DEBUGGING_DASHBOARD_ENABLED', default=True, cast=bool),
    'REAL_TIME_UPDATES': config('DASHBOARD_REAL_TIME_UPDATES', default=True, cast=bool),
    'WEBSOCKET_ENABLED': config('DASHBOARD_WEBSOCKET_ENABLED', default=True, cast=bool),
    'UPDATE_INTERVAL_SECONDS': config('DASHBOARD_UPDATE_INTERVAL', default=5, cast=int),
    'MAX_CONCURRENT_CONNECTIONS': config('DASHBOARD_MAX_CONNECTIONS', default=50, cast=int),
    'AUTHENTICATION_REQUIRED': config('DASHBOARD_AUTH_REQUIRED', default=True, cast=bool),
    'ADMIN_ONLY': config('DASHBOARD_ADMIN_ONLY', default=False, cast=bool),
    'DATA_RETENTION_HOURS': config('DASHBOARD_DATA_RETENTION_HOURS', default=24, cast=int),
}

# Alert Configuration
DEBUGGING_ALERTS = {
    'ENABLED': config('DEBUGGING_ALERTS_ENABLED', default=True, cast=bool),
    'EMAIL_NOTIFICATIONS': config('ALERT_EMAIL_NOTIFICATIONS', default=False, cast=bool),
    'WEBHOOK_NOTIFICATIONS': config('ALERT_WEBHOOK_NOTIFICATIONS', default=False, cast=bool),
    'SLACK_NOTIFICATIONS': config('ALERT_SLACK_NOTIFICATIONS', default=False, cast=bool),
    'RECIPIENTS': config('ALERT_RECIPIENTS', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]),
    'WEBHOOK_URL': config('ALERT_WEBHOOK_URL', default=''),
    'SLACK_WEBHOOK_URL': config('ALERT_SLACK_WEBHOOK_URL', default=''),
    'RATE_LIMIT_MINUTES': config('ALERT_RATE_LIMIT_MINUTES', default=15, cast=int),
}

# Environment-specific overrides
DEBUGGING_ENVIRONMENT_CONFIG = {
    'development': {
        'DEBUGGING_SYSTEM': {
            'PERFORMANCE_MONITORING_ENABLED': True,
            'WORKFLOW_TRACING_ENABLED': True,
            'ERROR_TRACKING_ENABLED': True,
            'ROUTE_DISCOVERY_ENABLED': True,
            'API_VALIDATION_ENABLED': True,
            'DATABASE_MONITORING_ENABLED': True,
        },
        'PERFORMANCE_MONITORING': {
            'REAL_TIME_UPDATES': True,
            'COLLECTION_INTERVAL': 10,  # More frequent in development
        },
        'WORKFLOW_TRACING': {
            'DETAILED_LOGGING': True,
            'TIMEOUT_SECONDS': 600,  # Longer timeout for debugging
        },
        'DEBUGGING_DASHBOARD': {
            'AUTHENTICATION_REQUIRED': False,  # Easier access in development
            'UPDATE_INTERVAL_SECONDS': 2,  # More frequent updates
        },
    },
    'production': {
        'DEBUGGING_SYSTEM': {
            'PERFORMANCE_MONITORING_ENABLED': True,
            'WORKFLOW_TRACING_ENABLED': False,  # Disabled in production for performance
            'ERROR_TRACKING_ENABLED': True,
            'ROUTE_DISCOVERY_ENABLED': False,  # Disabled in production
            'API_VALIDATION_ENABLED': False,  # Disabled in production
            'DATABASE_MONITORING_ENABLED': True,
        },
        'PERFORMANCE_MONITORING': {
            'REAL_TIME_UPDATES': False,  # Batch processing in production
            'COLLECTION_INTERVAL': 60,
        },
        'WORKFLOW_TRACING': {
            'DETAILED_LOGGING': False,
        },
        'DEBUGGING_DASHBOARD': {
            'AUTHENTICATION_REQUIRED': True,
            'ADMIN_ONLY': True,
            'UPDATE_INTERVAL_SECONDS': 30,
        },
        'DEBUGGING_ALERTS': {
            'EMAIL_NOTIFICATIONS': True,
            'WEBHOOK_NOTIFICATIONS': True,
        },
    },
    'testing': {
        'DEBUGGING_SYSTEM': {
            'ENABLED': False,  # Disabled during tests
        },
        'PERFORMANCE_MONITORING': {
            'REAL_TIME_UPDATES': False,
        },
        'DEBUGGING_DASHBOARD': {
            'ENABLED': False,
        },
        'DEBUGGING_ALERTS': {
            'ENABLED': False,
        },
    },
}

# Security Configuration
DEBUGGING_SECURITY = {
    'CORS_ALLOWED_ORIGINS': config('DEBUGGING_CORS_ORIGINS', default='http://localhost:3000', cast=lambda v: [s.strip() for s in v.split(',')]),
    'API_KEY_REQUIRED': config('DEBUGGING_API_KEY_REQUIRED', default=False, cast=bool),
    'API_KEY': config('DEBUGGING_API_KEY', default=''),
    'RATE_LIMITING_ENABLED': config('DEBUGGING_RATE_LIMITING_ENABLED', default=True, cast=bool),
    'MAX_REQUESTS_PER_MINUTE': config('DEBUGGING_MAX_REQUESTS_PER_MINUTE', default=100, cast=int),
    'IP_WHITELIST': config('DEBUGGING_IP_WHITELIST', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]),
    'SENSITIVE_DATA_MASKING': config('DEBUGGING_SENSITIVE_DATA_MASKING', default=True, cast=bool),
}