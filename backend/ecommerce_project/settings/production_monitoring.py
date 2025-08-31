"""
Production Monitoring Settings

Configuration settings for production monitoring and alerting system.
"""

import os
from decouple import config

# Production Monitoring Configuration
PRODUCTION_MONITORING = {
    'ENABLED': config('PRODUCTION_MONITORING_ENABLED', default=True, cast=bool),
    'LOG_ROTATION_ENABLED': config('LOG_ROTATION_ENABLED', default=True, cast=bool),
    'ALERTING_ENABLED': config('ALERTING_ENABLED', default=True, cast=bool),
    'HEALTH_CHECKS_ENABLED': config('HEALTH_CHECKS_ENABLED', default=True, cast=bool),
    'METRICS_COLLECTION_ENABLED': config('METRICS_COLLECTION_ENABLED', default=True, cast=bool),
}

# Logging Configuration for Production
LOG_DIR = config('LOG_DIR', default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs'))

# Log Rotation Settings
LOG_ROTATION = {
    'MAX_BYTES': config('LOG_MAX_BYTES', default=50 * 1024 * 1024, cast=int),  # 50MB
    'BACKUP_COUNT': config('LOG_BACKUP_COUNT', default=10, cast=int),
    'CLEANUP_DAYS': config('LOG_CLEANUP_DAYS', default=30, cast=int),
}

# Alerting Configuration
ALERTING_CONFIG = {
    'ENABLED': config('ALERTING_ENABLED', default=True, cast=bool),
    'COOLDOWN_MINUTES': config('ALERT_COOLDOWN_MINUTES', default=15, cast=int),
    'ESCALATION_MINUTES': config('ALERT_ESCALATION_MINUTES', default=60, cast=int),
    'AUTO_RESOLVE_MINUTES': config('ALERT_AUTO_RESOLVE_MINUTES', default=30, cast=int),
}

# Email Alert Configuration
ALERT_EMAIL_RECIPIENTS = config('ALERT_EMAIL_RECIPIENTS', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])
ALERT_EMAIL_ENABLED = config('ALERT_EMAIL_ENABLED', default=bool(ALERT_EMAIL_RECIPIENTS), cast=bool)

# Webhook Alert Configuration
ALERT_WEBHOOK_URL = config('ALERT_WEBHOOK_URL', default='')
ALERT_WEBHOOK_HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': config('ALERT_WEBHOOK_AUTH', default=''),
}
ALERT_WEBHOOK_ENABLED = config('ALERT_WEBHOOK_ENABLED', default=bool(ALERT_WEBHOOK_URL), cast=bool)

# Slack Alert Configuration
SLACK_WEBHOOK_URL = config('SLACK_WEBHOOK_URL', default='')
SLACK_ALERT_CHANNEL = config('SLACK_ALERT_CHANNEL', default='#alerts')
SLACK_ALERTS_ENABLED = config('SLACK_ALERTS_ENABLED', default=bool(SLACK_WEBHOOK_URL), cast=bool)

# Performance Thresholds
PERFORMANCE_THRESHOLDS = {
    # API Response Time Thresholds (milliseconds)
    'api_response_time_warning': config('API_RESPONSE_TIME_WARNING', default=500, cast=float),
    'api_response_time_critical': config('API_RESPONSE_TIME_CRITICAL', default=2000, cast=float),
    
    # Database Query Time Thresholds (milliseconds)
    'database_query_time_warning': config('DB_QUERY_TIME_WARNING', default=100, cast=float),
    'database_query_time_critical': config('DB_QUERY_TIME_CRITICAL', default=500, cast=float),
    
    # Memory Usage Thresholds (percentage)
    'memory_usage_warning': config('MEMORY_USAGE_WARNING', default=80, cast=float),
    'memory_usage_critical': config('MEMORY_USAGE_CRITICAL', default=95, cast=float),
    
    # CPU Usage Thresholds (percentage)
    'cpu_usage_warning': config('CPU_USAGE_WARNING', default=80, cast=float),
    'cpu_usage_critical': config('CPU_USAGE_CRITICAL', default=95, cast=float),
    
    # Error Rate Thresholds (errors per minute)
    'error_rate_warning': config('ERROR_RATE_WARNING', default=1, cast=float),
    'error_rate_critical': config('ERROR_RATE_CRITICAL', default=5, cast=float),
    
    # Disk Usage Thresholds (percentage)
    'disk_usage_warning': config('DISK_USAGE_WARNING', default=85, cast=float),
    'disk_usage_critical': config('DISK_USAGE_CRITICAL', default=95, cast=float),
    
    # Connection Pool Usage Thresholds (percentage)
    'connection_pool_usage_warning': config('CONNECTION_POOL_WARNING', default=80, cast=float),
    'connection_pool_usage_critical': config('CONNECTION_POOL_CRITICAL', default=95, cast=float),
    
    # Cache Hit Rate Thresholds (percentage - lower is worse)
    'cache_hit_rate_warning': config('CACHE_HIT_RATE_WARNING', default=70, cast=float),
    'cache_hit_rate_critical': config('CACHE_HIT_RATE_CRITICAL', default=50, cast=float),
}

# Health Check Configuration
HEALTH_CHECK_CONFIG = {
    'ENABLED': config('HEALTH_CHECKS_ENABLED', default=True, cast=bool),
    'TIMEOUT_SECONDS': config('HEALTH_CHECK_TIMEOUT', default=10, cast=int),
    'DATABASE_CHECK_ENABLED': config('DB_HEALTH_CHECK_ENABLED', default=True, cast=bool),
    'CACHE_CHECK_ENABLED': config('CACHE_HEALTH_CHECK_ENABLED', default=True, cast=bool),
    'FILESYSTEM_CHECK_ENABLED': config('FILESYSTEM_HEALTH_CHECK_ENABLED', default=True, cast=bool),
    'MEMORY_CHECK_ENABLED': config('MEMORY_HEALTH_CHECK_ENABLED', default=True, cast=bool),
    'EXTERNAL_SERVICES_CHECK_ENABLED': config('EXTERNAL_SERVICES_HEALTH_CHECK_ENABLED', default=True, cast=bool),
}

# Metrics Collection Configuration
METRICS_COLLECTION_CONFIG = {
    'ENABLED': config('METRICS_COLLECTION_ENABLED', default=True, cast=bool),
    'COLLECTION_INTERVAL_SECONDS': config('METRICS_COLLECTION_INTERVAL', default=30, cast=int),
    'RETENTION_DAYS': config('METRICS_RETENTION_DAYS', default=30, cast=int),
    'BATCH_SIZE': config('METRICS_BATCH_SIZE', default=100, cast=int),
    'BUFFER_SIZE': config('METRICS_BUFFER_SIZE', default=1000, cast=int),
}

# Dashboard Configuration
PRODUCTION_DASHBOARD_CONFIG = {
    'ENABLED': config('PRODUCTION_DASHBOARD_ENABLED', default=True, cast=bool),
    'REFRESH_INTERVAL_SECONDS': config('DASHBOARD_REFRESH_INTERVAL', default=30, cast=int),
    'MAX_CHART_DATA_POINTS': config('DASHBOARD_MAX_CHART_POINTS', default=100, cast=int),
    'DEFAULT_TIME_RANGE': config('DASHBOARD_DEFAULT_TIME_RANGE', default='1h'),
    'REQUIRE_AUTHENTICATION': config('DASHBOARD_REQUIRE_AUTH', default=True, cast=bool),
    'REQUIRE_STAFF_ACCESS': config('DASHBOARD_REQUIRE_STAFF', default=True, cast=bool),
}

# Security Configuration for Production Monitoring
MONITORING_SECURITY_CONFIG = {
    'API_KEY_REQUIRED': config('MONITORING_API_KEY_REQUIRED', default=False, cast=bool),
    'API_KEY': config('MONITORING_API_KEY', default=''),
    'IP_WHITELIST': config('MONITORING_IP_WHITELIST', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]),
    'RATE_LIMIT_ENABLED': config('MONITORING_RATE_LIMIT_ENABLED', default=True, cast=bool),
    'RATE_LIMIT_REQUESTS': config('MONITORING_RATE_LIMIT_REQUESTS', default=100, cast=int),
    'RATE_LIMIT_WINDOW_SECONDS': config('MONITORING_RATE_LIMIT_WINDOW', default=3600, cast=int),  # 1 hour
}

# Optimization Engine Configuration
OPTIMIZATION_ENGINE_CONFIG = {
    'ENABLED': config('OPTIMIZATION_ENGINE_ENABLED', default=True, cast=bool),
    'ANALYSIS_WINDOW_HOURS': config('OPTIMIZATION_ANALYSIS_WINDOW', default=24, cast=int),
    'MIN_CONFIDENCE_SCORE': config('OPTIMIZATION_MIN_CONFIDENCE', default=0.7, cast=float),
    'MAX_RECOMMENDATIONS': config('OPTIMIZATION_MAX_RECOMMENDATIONS', default=10, cast=int),
}

# Integration with Django Settings
DEBUGGING_SYSTEM = {
    'PRODUCTION_MONITORING_ENABLED': PRODUCTION_MONITORING['ENABLED'],
    'ALERTING_ENABLED': ALERTING_CONFIG['ENABLED'],
    'HEALTH_CHECKS_ENABLED': HEALTH_CHECK_CONFIG['ENABLED'],
    'METRICS_COLLECTION_ENABLED': METRICS_COLLECTION_CONFIG['ENABLED'],
    'DASHBOARD_ENABLED': PRODUCTION_DASHBOARD_CONFIG['ENABLED'],
}

PERFORMANCE_MONITORING = {
    'ENABLED': PRODUCTION_MONITORING['ENABLED'],
    'COLLECTION_INTERVAL': METRICS_COLLECTION_CONFIG['COLLECTION_INTERVAL_SECONDS'],
    'ALERT_THRESHOLDS': PERFORMANCE_THRESHOLDS,
    'RETENTION_DAYS': METRICS_COLLECTION_CONFIG['RETENTION_DAYS'],
}

DEBUGGING_DASHBOARD = {
    'ENABLED': PRODUCTION_DASHBOARD_CONFIG['ENABLED'],
    'REFRESH_INTERVAL': PRODUCTION_DASHBOARD_CONFIG['REFRESH_INTERVAL_SECONDS'],
    'REQUIRE_AUTHENTICATION': PRODUCTION_DASHBOARD_CONFIG['REQUIRE_AUTHENTICATION'],
    'REQUIRE_STAFF_ACCESS': PRODUCTION_DASHBOARD_CONFIG['REQUIRE_STAFF_ACCESS'],
    'REAL_TIME_UPDATES': config('DASHBOARD_REAL_TIME_UPDATES', default=True, cast=bool),
    'WEBSOCKET_ENABLED': config('DASHBOARD_WEBSOCKET_ENABLED', default=True, cast=bool),
}

DEBUGGING_ALERTS = {
    'EMAIL_ENABLED': ALERT_EMAIL_ENABLED,
    'EMAIL_RECIPIENTS': ALERT_EMAIL_RECIPIENTS,
    'WEBHOOK_ENABLED': ALERT_WEBHOOK_ENABLED,
    'WEBHOOK_URL': ALERT_WEBHOOK_URL,
    'SLACK_ENABLED': SLACK_ALERTS_ENABLED,
    'SLACK_WEBHOOK_URL': SLACK_WEBHOOK_URL,
    'SLACK_CHANNEL': SLACK_ALERT_CHANNEL,
    'COOLDOWN_MINUTES': ALERTING_CONFIG['COOLDOWN_MINUTES'],
    'ESCALATION_MINUTES': ALERTING_CONFIG['ESCALATION_MINUTES'],
    'AUTO_RESOLVE_MINUTES': ALERTING_CONFIG['AUTO_RESOLVE_MINUTES'],
}

DEBUGGING_SECURITY = {
    'API_KEY_REQUIRED': MONITORING_SECURITY_CONFIG['API_KEY_REQUIRED'],
    'API_KEY': MONITORING_SECURITY_CONFIG['API_KEY'],
    'IP_WHITELIST': MONITORING_SECURITY_CONFIG['IP_WHITELIST'],
    'RATE_LIMIT_ENABLED': MONITORING_SECURITY_CONFIG['RATE_LIMIT_ENABLED'],
}

# Environment-specific overrides
ENVIRONMENT = config('ENVIRONMENT', default='development')

if ENVIRONMENT == 'production':
    # Production-specific settings
    PRODUCTION_MONITORING['ENABLED'] = True
    ALERTING_CONFIG['ENABLED'] = True
    HEALTH_CHECK_CONFIG['ENABLED'] = True
    METRICS_COLLECTION_CONFIG['ENABLED'] = True
    MONITORING_SECURITY_CONFIG['API_KEY_REQUIRED'] = True
    PRODUCTION_DASHBOARD_CONFIG['REQUIRE_AUTHENTICATION'] = True
    PRODUCTION_DASHBOARD_CONFIG['REQUIRE_STAFF_ACCESS'] = True
    
elif ENVIRONMENT == 'staging':
    # Staging-specific settings
    PRODUCTION_MONITORING['ENABLED'] = True
    ALERTING_CONFIG['ENABLED'] = True
    HEALTH_CHECK_CONFIG['ENABLED'] = True
    METRICS_COLLECTION_CONFIG['ENABLED'] = True
    MONITORING_SECURITY_CONFIG['API_KEY_REQUIRED'] = False
    
elif ENVIRONMENT == 'development':
    # Development-specific settings
    PRODUCTION_MONITORING['ENABLED'] = config('DEV_MONITORING_ENABLED', default=False, cast=bool)
    ALERTING_CONFIG['ENABLED'] = config('DEV_ALERTING_ENABLED', default=False, cast=bool)
    HEALTH_CHECK_CONFIG['ENABLED'] = True
    METRICS_COLLECTION_CONFIG['ENABLED'] = config('DEV_METRICS_ENABLED', default=False, cast=bool)
    MONITORING_SECURITY_CONFIG['API_KEY_REQUIRED'] = False
    PRODUCTION_DASHBOARD_CONFIG['REQUIRE_AUTHENTICATION'] = False
    PRODUCTION_DASHBOARD_CONFIG['REQUIRE_STAFF_ACCESS'] = False