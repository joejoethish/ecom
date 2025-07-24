"""
Logging configuration for the ecommerce platform.
"""
import os
import logging.config
from django.conf import settings

# Define base log directory
LOG_DIR = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs', 'files'))

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Define log file paths
GENERAL_LOG = os.path.join(LOG_DIR, 'ecommerce.log')
ERROR_LOG = os.path.join(LOG_DIR, 'error.log')
SECURITY_LOG = os.path.join(LOG_DIR, 'security.log')
REQUEST_LOG = os.path.join(LOG_DIR, 'requests.log')
PERFORMANCE_LOG = os.path.join(LOG_DIR, 'performance.log')
METRICS_LOG = os.path.join(LOG_DIR, 'metrics.log')
BUSINESS_METRICS_LOG = os.path.join(LOG_DIR, 'business_metrics.log')

# Define logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '%(levelname)s %(message)s',
        },
        'json': {
            '()': 'backend.logs.handlers.JsonFormatter',
            'fmt_dict': {
                'timestamp': '%(asctime)s',
                'level': '%(levelname)s',
                'name': '%(name)s',
                'file': '%(pathname)s',
                'line': '%(lineno)d',
                'message': '%(message)s',
            }
        },
        'colored': {
            '()': 'backend.logs.formatters.ColoredConsoleFormatter',
            'format': '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            'datefmt': '%H:%M:%S',
        },
        'security': {
            '()': 'backend.logs.formatters.SecurityFormatter',
        },
        'metrics': {
            '()': 'backend.logs.formatters.BusinessMetricsFormatter',
        },
        'structured': {
            '()': 'backend.logs.formatters.StructuredFormatter',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'backend.logs.filters.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'backend.logs.filters.RequireDebugFalse',
        },
        'ignore_health_checks': {
            '()': 'backend.logs.filters.IgnoreHealthChecks',
        },
        'sensitive_data': {
            '()': 'backend.logs.filters.SensitiveDataFilter',
        },
        'rate_limit': {
            '()': 'backend.logs.filters.RateLimitFilter',
            'rate': 100,
            'per': 60,
            'burst': 200,
        },
        'environment': {
            '()': 'backend.logs.filters.EnvironmentFilter',
            'environment': getattr(settings, 'ENVIRONMENT', 'development'),
        },
        'user_filter': {
            '()': 'backend.logs.filters.UserFilter',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
            'filters': ['sensitive_data'],
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': GENERAL_LOG,
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
            'filters': ['sensitive_data'],
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': ERROR_LOG,
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
            'filters': ['sensitive_data'],
        },
        'security_file': {
            'level': 'INFO',
            'class': 'backend.logs.handlers.SecurityRotatingFileHandler',
            'filename': SECURITY_LOG,
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'security',
            'filters': ['sensitive_data'],
        },
        'request_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': REQUEST_LOG,
            'when': 'midnight',
            'interval': 1,
            'backupCount': 30,
            'formatter': 'json',
            'filters': ['sensitive_data', 'ignore_health_checks'],
        },
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': PERFORMANCE_LOG,
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'metrics_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': METRICS_LOG,
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'metrics',
        },
        'business_metrics': {
            'level': 'INFO',
            'class': 'backend.logs.handlers.BusinessMetricsHandler',
            'metrics_file': BUSINESS_METRICS_LOG,
            'formatter': 'metrics',
        },
        'database': {
            'level': 'WARNING',
            'class': 'backend.logs.handlers.DatabaseLogHandler',
            'formatter': 'structured',
            'filters': ['sensitive_data', 'rate_limit'],
        },
        'slack': {
            'level': 'ERROR',
            'class': 'backend.logs.handlers.SlackHandler',
            'formatter': 'simple',
            'filters': ['require_debug_false', 'sensitive_data', 'rate_limit'],
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
            'filters': ['require_debug_false', 'sensitive_data', 'rate_limit'],
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'security_file', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'request': {
            'handlers': ['console', 'request_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'security': {
            'handlers': ['console', 'security_file', 'database', 'slack'],
            'level': 'INFO',
            'propagate': False,
        },
        'performance': {
            'handlers': ['console', 'performance_file', 'database'],
            'level': 'INFO',
            'propagate': False,
        },
        'metrics': {
            'handlers': ['metrics_file', 'business_metrics'],
            'level': 'INFO',
            'propagate': False,
        },
        'monitoring': {
            'handlers': ['console', 'performance_file', 'database'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

def configure_logging():
    """
    Configure the logging system based on the settings.
    """
    # Create log directories if they don't exist
    os.makedirs(os.path.dirname(GENERAL_LOG), exist_ok=True)
    os.makedirs(os.path.dirname(ERROR_LOG), exist_ok=True)
    os.makedirs(os.path.dirname(SECURITY_LOG), exist_ok=True)
    os.makedirs(os.path.dirname(REQUEST_LOG), exist_ok=True)
    os.makedirs(os.path.dirname(PERFORMANCE_LOG), exist_ok=True)
    os.makedirs(os.path.dirname(METRICS_LOG), exist_ok=True)
    os.makedirs(os.path.dirname(BUSINESS_METRICS_LOG), exist_ok=True)
    
    # Apply logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging system initialized. Environment: {getattr(settings, 'ENVIRONMENT', 'development')}")