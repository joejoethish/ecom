"""
Development settings for ecommerce project.
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Database - Using SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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