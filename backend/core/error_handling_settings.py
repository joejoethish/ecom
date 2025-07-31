"""
Django settings configuration for database error handling system
"""

# Database Error Handling Settings
DATABASE_ERROR_HANDLING = {
    # Alert thresholds
    'DB_ALERT_CONNECTION_WARNING': 80.0,
    'DB_ALERT_CONNECTION_CRITICAL': 95.0,
    'DB_ALERT_QUERY_TIME_WARNING': 2.0,
    'DB_ALERT_QUERY_TIME_CRITICAL': 5.0,
    'DB_ALERT_SLOW_QUERIES_WARNING': 10.0,
    'DB_ALERT_SLOW_QUERIES_CRITICAL': 50.0,
    'DB_ALERT_REPLICATION_WARNING': 5.0,
    'DB_ALERT_REPLICATION_CRITICAL': 30.0,
    'DB_ALERT_CPU_WARNING': 80.0,
    'DB_ALERT_CPU_CRITICAL': 95.0,
    'DB_ALERT_MEMORY_WARNING': 85.0,
    'DB_ALERT_MEMORY_CRITICAL': 95.0,
    'DB_ALERT_DISK_WARNING': 85.0,
    'DB_ALERT_DISK_CRITICAL': 95.0,
    'DB_ALERT_HEALTH_WARNING': 70.0,
    'DB_ALERT_HEALTH_CRITICAL': 50.0,
    
    # Circuit breaker settings
    'DB_CIRCUIT_BREAKER_THRESHOLD': 5,
    'DB_CIRCUIT_BREAKER_TIMEOUT': 60,
    
    # Health check settings
    'DB_HEALTH_CHECK_INTERVAL': 60,
    
    # Performance thresholds
    'SLOW_QUERY_THRESHOLD': 2.0,
    'SLOW_REQUEST_THRESHOLD': 5.0,
    
    # Email notifications
    'DATABASE_ALERT_EMAILS': [
        # Add admin email addresses here
        # 'admin@example.com',
    ],
}

# Middleware configuration
DATABASE_ERROR_MIDDLEWARE = [
    'core.middleware.database_error_middleware.DatabaseErrorHandlingMiddleware',
    'core.middleware.database_error_middleware.DatabaseConnectionPoolMiddleware',
    'core.middleware.database_error_middleware.DatabaseMetricsMiddleware',
    'core.middleware.database_error_middleware.DatabaseHealthCheckMiddleware',
]

# Logging configuration for database errors
DATABASE_ERROR_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'database_error': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'database_error_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/database_errors.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'database_error',
        },
        'database_error_console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'database_error',
        },
    },
    'loggers': {
        'core.database_error_handler': {
            'handlers': ['database_error_file', 'database_error_console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.connection_pool': {
            'handlers': ['database_error_file', 'database_error_console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.middleware.database_error_middleware': {
            'handlers': ['database_error_file', 'database_error_console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Cache configuration for error handling
DATABASE_ERROR_CACHE_SETTINGS = {
    'error_metrics_timeout': 300,  # 5 minutes
    'health_check_timeout': 300,   # 5 minutes
    'degradation_mode_timeout': 300,  # 5 minutes
}

def configure_database_error_handling(settings_dict):
    """
    Configure Django settings for database error handling
    
    Usage in settings.py:
        from core.error_handling_settings import configure_database_error_handling
        configure_database_error_handling(globals())
    """
    
    # Add error handling settings
    for key, value in DATABASE_ERROR_HANDLING.items():
        settings_dict[key] = value
    
    # Add middleware
    middleware = settings_dict.get('MIDDLEWARE', [])
    for middleware_class in DATABASE_ERROR_MIDDLEWARE:
        if middleware_class not in middleware:
            middleware.append(middleware_class)
    settings_dict['MIDDLEWARE'] = middleware
    
    # Configure logging
    logging_config = settings_dict.get('LOGGING', {'version': 1, 'disable_existing_loggers': False})
    
    # Merge formatters
    if 'formatters' not in logging_config:
        logging_config['formatters'] = {}
    logging_config['formatters'].update(DATABASE_ERROR_LOGGING['formatters'])
    
    # Merge handlers
    if 'handlers' not in logging_config:
        logging_config['handlers'] = {}
    logging_config['handlers'].update(DATABASE_ERROR_LOGGING['handlers'])
    
    # Merge loggers
    if 'loggers' not in logging_config:
        logging_config['loggers'] = {}
    logging_config['loggers'].update(DATABASE_ERROR_LOGGING['loggers'])
    
    settings_dict['LOGGING'] = logging_config
    
    # Add cache settings
    for key, value in DATABASE_ERROR_CACHE_SETTINGS.items():
        settings_dict[key.upper()] = value