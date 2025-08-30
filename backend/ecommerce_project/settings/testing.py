"""
Testing settings for ecommerce project.
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Use in-memory database for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Use console email backend for tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable Celery for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable caching for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable password validation for tests
AUTH_PASSWORD_VALIDATORS = []

# Apply testing-specific debugging configuration
if 'testing' in DEBUGGING_ENVIRONMENT_CONFIG:
    test_config = DEBUGGING_ENVIRONMENT_CONFIG['testing']
    
    # Update debugging system settings for testing
    DEBUGGING_SYSTEM.update(test_config.get('DEBUGGING_SYSTEM', {}))
    PERFORMANCE_MONITORING.update(test_config.get('PERFORMANCE_MONITORING', {}))
    DEBUGGING_DASHBOARD.update(test_config.get('DEBUGGING_DASHBOARD', {}))
    DEBUGGING_ALERTS.update(test_config.get('DEBUGGING_ALERTS', {}))

# Disable logging during tests to reduce noise
LOGGING['handlers']['console']['level'] = 'CRITICAL'
LOGGING['handlers']['file']['level'] = 'CRITICAL'
LOGGING['root']['level'] = 'CRITICAL'

# Security settings for testing
SECURE_HSTS_SECONDS = 0
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False