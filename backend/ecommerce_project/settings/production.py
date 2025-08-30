"""
Production settings for ecommerce project.
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Production database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'sql_mode': 'traditional',
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'ssl_disabled': config('DB_SSL_DISABLED', default=False, cast=bool),
        },
        'CONN_MAX_AGE': 3600,
        'CONN_HEALTH_CHECKS': True,
    }
}

# Security settings for production
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Static files configuration for production
STATIC_ROOT = '/var/www/static/'
MEDIA_ROOT = '/var/www/media/'

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Celery configuration for production
CELERY_TASK_ALWAYS_EAGER = False
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')

# Logging configuration for production
LOGGING['handlers']['file']['filename'] = '/var/log/django/django.log'
LOGGING['handlers']['file']['level'] = 'WARNING'
LOGGING['root']['level'] = 'WARNING'

# Apply production-specific debugging configuration
if 'production' in DEBUGGING_ENVIRONMENT_CONFIG:
    prod_config = DEBUGGING_ENVIRONMENT_CONFIG['production']
    
    # Update debugging system settings for production
    DEBUGGING_SYSTEM.update(prod_config.get('DEBUGGING_SYSTEM', {}))
    PERFORMANCE_MONITORING.update(prod_config.get('PERFORMANCE_MONITORING', {}))
    WORKFLOW_TRACING.update(prod_config.get('WORKFLOW_TRACING', {}))
    DEBUGGING_DASHBOARD.update(prod_config.get('DEBUGGING_DASHBOARD', {}))
    DEBUGGING_ALERTS.update(prod_config.get('DEBUGGING_ALERTS', {}))
    
    # Production-specific security settings for debugging
    DEBUGGING_SECURITY.update({
        'API_KEY_REQUIRED': True,
        'RATE_LIMITING_ENABLED': True,
        'SENSITIVE_DATA_MASKING': True,
    })

# Payment Gateway Settings (Production Keys)
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
RAZORPAY_KEY_ID = config('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = config('RAZORPAY_KEY_SECRET')

# Production URLs
PAYMENT_SUCCESS_URL = f"{FRONTEND_URL}/payment/success"
PAYMENT_CANCEL_URL = f"{FRONTEND_URL}/payment/cancel"