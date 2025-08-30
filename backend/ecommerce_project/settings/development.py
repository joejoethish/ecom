"""
Development settings for ecommerce project.
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Add testserver to ALLOWED_HOSTS for Django test client
ALLOWED_HOSTS += ['testserver']

# Database - Using MySQL for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='ecommerce_db'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default='root'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3307'),
        'OPTIONS': {
            'sql_mode': 'traditional',
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Add debug toolbar for development
INSTALLED_APPS += [
    'debug_toolbar',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# Debug toolbar configuration
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files serving in development
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Payment Gateway Settings
# Stripe API Keys (Test Keys)
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='pk_test_your_stripe_public_key')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='sk_test_your_stripe_secret_key')

# Razorpay API Keys (Test Keys)
RAZORPAY_KEY_ID = config('RAZORPAY_KEY_ID', default='rzp_test_your_razorpay_key_id')
RAZORPAY_KEY_SECRET = config('RAZORPAY_KEY_SECRET', default='your_razorpay_key_secret')

# Payment Success and Cancel URLs
PAYMENT_SUCCESS_URL = f"{FRONTEND_URL}/payment/success"
PAYMENT_CANCEL_URL = f"{FRONTEND_URL}/payment/cancel"

# Security settings for development (to suppress warnings)
# Note: These should be True in production
SECURE_HSTS_SECONDS = 0  # Disabled for development
SECURE_SSL_REDIRECT = False  # Disabled for development
SESSION_COOKIE_SECURE = False  # Disabled for development (no HTTPS in dev)
CSRF_COOKIE_SECURE = False  # Disabled for development (no HTTPS in dev)

# Apply development-specific debugging configuration
if 'development' in DEBUGGING_ENVIRONMENT_CONFIG:
    dev_config = DEBUGGING_ENVIRONMENT_CONFIG['development']
    
    # Update debugging system settings
    DEBUGGING_SYSTEM.update(dev_config.get('DEBUGGING_SYSTEM', {}))
    PERFORMANCE_MONITORING.update(dev_config.get('PERFORMANCE_MONITORING', {}))
    WORKFLOW_TRACING.update(dev_config.get('WORKFLOW_TRACING', {}))
    DEBUGGING_DASHBOARD.update(dev_config.get('DEBUGGING_DASHBOARD', {}))
    
    # Enable additional debugging features for development
    DEBUGGING_SYSTEM['DETAILED_LOGGING'] = True
    DEBUGGING_SYSTEM['VERBOSE_ERRORS'] = True