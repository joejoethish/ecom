"""
Base settings for ecommerce project.
"""
import os
from pathlib import Path
from decouple import config

# Import Elasticsearch settings
from .elasticsearch import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'channels',
    'django_elasticsearch_dsl',
    'drf_spectacular',
    'drf_yasg',
]

LOCAL_APPS = [
    'core',  # Core utilities including migration tools
    'apps.authentication',
    'apps.admin_panel',  # Comprehensive admin panel
    'apps.system_settings',  # Comprehensive system settings management
    'apps.integrations',  # Third-party integration management
    'apps.products',
    'apps.orders',
    'apps.cart',
    'apps.inventory',
    'apps.customers',
    'apps.payments',
    'apps.shipping',
    'apps.sellers',
    'apps.analytics',
    'apps.customer_analytics',  # Customer analytics and segmentation
    'apps.content',
    'apps.reviews',
    'apps.search',
    'apps.notifications',
    'apps.chat',
    'apps.promotions',  # Comprehensive promotion and coupon management
    'apps.forms',  # Dynamic form management
    'apps.api_management',  # API management and documentation
    'apps.communications',  # Communication management
    'apps.financial',  # Financial management
    'apps.suppliers',  # Supplier management
    'apps.pricing',  # Pricing management
    'apps.data_management',  # Advanced data import/export management
    'apps.security_management',  # Comprehensive security management system
    'apps.workflow',  # Comprehensive workflow automation system
    'apps.project_management',  # Advanced task and project management system
    'apps.tenants',  # Comprehensive multi-tenant architecture
    'apps.internationalization',  # Comprehensive internationalization system
    # 'apps.logs',  # Temporarily disabled due to import issues
    'tasks',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'apps.authentication.middleware.SecurityHeadersMiddleware',
    'apps.tenants.middleware.TenantMiddleware',  # Multi-tenant support
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'apps.authentication.middleware.CSRFAuthenticationMiddleware',
    'apps.authentication.middleware.AuthenticationRateLimitMiddleware',
    'apps.authentication.middleware.AccountLockoutMiddleware',
    'apps.authentication.middleware.IPSecurityMonitoringMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.database_security_middleware.DatabaseSecurityMiddleware',
    'core.middleware.database_security_middleware.AuthenticationSecurityMiddleware',
    # 'core.middleware.APIVersionMiddleware',  # Not implemented yet
    # 'core.middleware.RequestLoggingMiddleware',  # Not implemented yet
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ecommerce_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecommerce_project.wsgi.application'
ASGI_APPLICATION = 'ecommerce_project.asgi.application'

# Database Configuration with Connection Pooling and Read Replicas
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='ecommerce_db'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default='root'),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='3307'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': True,
            'sql_mode': 'STRICT_TRANS_TABLES',
            'isolation_level': 'read committed',
            # SSL Configuration (use ssl_disabled only if SSL is configured)
            # 'ssl_disabled': config('DB_SSL_DISABLED', default=True, cast=bool),
            # Connection pool settings (handled by Django, not MySQL connector)
            # 'pool_pre_ping': True,
            # 'pool_recycle': 3600,
            'connect_timeout': 10,
            'read_timeout': 30,
            'write_timeout': 30,
        },
        'CONN_MAX_AGE': 3600,  # Connection pooling - 1 hour
        'CONN_HEALTH_CHECKS': True,
    },
    # Read replica configuration (disabled - no replica server available)
    # 'read_replica': {
    #     'ENGINE': 'django.db.backends.mysql',
    #     'NAME': config('DB_READ_NAME', default=config('DB_NAME', default='ecommerce_db')),
    #     'USER': config('DB_READ_USER', default='replica_user'),
    #     'PASSWORD': config('DB_READ_PASSWORD', default='replica_password'),
    #     'HOST': config('DB_READ_HOST', default='127.0.0.1'),
    #     'PORT': config('DB_READ_PORT', default='3308'),
    #     'OPTIONS': {
    #         'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    #         'charset': 'utf8mb4',
    #         'use_unicode': True,
    #         'autocommit': True,
    #         'sql_mode': 'STRICT_TRANS_TABLES',
    #         'isolation_level': 'read committed',
    #         'connect_timeout': 10,
    #         'read_timeout': 30,
    #         'write_timeout': 30,
    #     },
    #     'CONN_MAX_AGE': 3600,
    #     'CONN_HEALTH_CHECKS': True,
    #     'READ_REPLICA': True,  # Mark as read replica
    # }
}

# Database Router Configuration (disabled - no replica available)
# DATABASE_ROUTERS = ['core.database_router.DatabaseRouter']

# Connection Pool Configuration
CONNECTION_POOL_CONFIG = {
    'default': {
        'pool_name': 'ecommerce_pool',
        'pool_size': config('DB_POOL_SIZE', default=20, cast=int),
        'pool_reset_session': True,
        'pool_pre_ping': True,
        'max_overflow': config('DB_POOL_MAX_OVERFLOW', default=30, cast=int),
        'pool_recycle': 3600,
        'host': config('DB_HOST', default='127.0.0.1'),
        'port': config('DB_PORT', default=3307, cast=int),
        'database': config('DB_NAME', default='ecommerce_db'),
        'user': config('DB_USER', default='root'),
        'password': config('DB_PASSWORD', default='root'),
        'charset': 'utf8mb4',
        'use_unicode': True,
        'autocommit': True,
        'sql_mode': 'STRICT_TRANS_TABLES',
        'connect_timeout': 10,
        'read_timeout': 30,
        'write_timeout': 30,
    }
}

# Database Router Settings
READ_ONLY_APPS = ['analytics', 'reports', 'search']
WRITE_ONLY_APPS = ['admin', 'auth', 'contenttypes', 'sessions']
READ_ONLY_MODELS = []
REPLICA_LAG_THRESHOLD = config('REPLICA_LAG_THRESHOLD', default=5, cast=int)  # seconds

# Connection Monitoring Settings (disabled during testing)
CONNECTION_MONITORING_ENABLED = config('CONNECTION_MONITORING_ENABLED', default=False, cast=bool)
CONNECTION_MONITORING_INTERVAL = config('CONNECTION_MONITORING_INTERVAL', default=30, cast=int)  # seconds

# Replica Monitoring Settings
REPLICA_MONITORING_ENABLED = config('REPLICA_MONITORING_ENABLED', default=False, cast=bool)
REPLICA_CHECK_INTERVAL = config('REPLICA_CHECK_INTERVAL', default=30, cast=int)  # seconds
REPLICA_MAX_FAILURES = config('REPLICA_MAX_FAILURES', default=3, cast=int)
REPLICA_FAILURE_WINDOW = config('REPLICA_FAILURE_WINDOW', default=300, cast=int)  # 5 minutes
REPLICA_ALERT_RECIPIENTS = config('REPLICA_ALERT_RECIPIENTS', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])
REPLICA_METRICS_RETENTION = config('REPLICA_METRICS_RETENTION', default=86400, cast=int)  # 24 hours

# Backup System Settings (scheduler disabled during testing)
BACKUP_SCHEDULER_ENABLED = config('BACKUP_SCHEDULER_ENABLED', default=False, cast=bool)
BACKUP_DIR = config('BACKUP_DIR', default=os.path.join(BASE_DIR, 'backups'))
BACKUP_ENCRYPTION_KEY = config('BACKUP_ENCRYPTION_KEY', default='change-this-key-in-production')
BACKUP_RETENTION_DAYS = config('BACKUP_RETENTION_DAYS', default=30, cast=int)
BACKUP_COMPRESSION_ENABLED = config('BACKUP_COMPRESSION_ENABLED', default=True, cast=bool)
BACKUP_VERIFY_ENABLED = config('BACKUP_VERIFY_ENABLED', default=True, cast=bool)

# Backup Schedule Settings
BACKUP_FULL_HOUR = config('BACKUP_FULL_HOUR', default=2, cast=int)  # 2 AM
BACKUP_FULL_MINUTE = config('BACKUP_FULL_MINUTE', default=0, cast=int)
BACKUP_INCREMENTAL_INTERVAL = config('BACKUP_INCREMENTAL_INTERVAL', default=4, cast=int)  # hours
BACKUP_CLEANUP_HOUR = config('BACKUP_CLEANUP_HOUR', default=3, cast=int)  # 3 AM
BACKUP_CLEANUP_MINUTE = config('BACKUP_CLEANUP_MINUTE', default=0, cast=int)
BACKUP_HEALTH_CHECK_INTERVAL = config('BACKUP_HEALTH_CHECK_INTERVAL', default=30, cast=int)  # minutes

# Backup Alert Settings
BACKUP_MAX_FAILURES = config('BACKUP_MAX_FAILURES', default=3, cast=int)
BACKUP_ALERT_RECIPIENTS = config('BACKUP_ALERT_RECIPIENTS', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])
BACKUP_ALERT_ON_FAILURE = config('BACKUP_ALERT_ON_FAILURE', default=True, cast=bool)
BACKUP_ALERT_ON_SUCCESS = config('BACKUP_ALERT_ON_SUCCESS', default=False, cast=bool)

# Database Security Settings
DB_SECURITY_ENABLED = config('DB_SECURITY_ENABLED', default=True, cast=bool)
DB_AUDIT_ENABLED = config('DB_AUDIT_ENABLED', default=True, cast=bool)
DB_THREAT_DETECTION_ENABLED = config('DB_THREAT_DETECTION_ENABLED', default=True, cast=bool)
DB_SECURITY_MIDDLEWARE_ENABLED = config('DB_SECURITY_MIDDLEWARE_ENABLED', default=True, cast=bool)
DB_SECURITY_LOG_ALL_QUERIES = config('DB_SECURITY_LOG_ALL_QUERIES', default=False, cast=bool)
AUTH_SECURITY_MIDDLEWARE_ENABLED = config('AUTH_SECURITY_MIDDLEWARE_ENABLED', default=True, cast=bool)

# Database Security Thresholds
DB_MAX_FAILED_ATTEMPTS = config('DB_MAX_FAILED_ATTEMPTS', default=5, cast=int)
DB_LOCKOUT_DURATION = config('DB_LOCKOUT_DURATION', default=3600, cast=int)  # 1 hour in seconds
DB_SUSPICIOUS_QUERY_THRESHOLD = config('DB_SUSPICIOUS_QUERY_THRESHOLD', default=100, cast=int)  # queries per hour
DB_RAPID_QUERY_THRESHOLD = config('DB_RAPID_QUERY_THRESHOLD', default=10, cast=int)  # queries per minute

# Database SSL Configuration
DB_SSL_ENABLED = config('DB_SSL_ENABLED', default=False, cast=bool)
DB_SSL_CA = config('DB_SSL_CA', default='/etc/mysql/ssl/ca-cert.pem')
DB_SSL_CERT = config('DB_SSL_CERT', default='/etc/mysql/ssl/client-cert.pem')
DB_SSL_KEY = config('DB_SSL_KEY', default='/etc/mysql/ssl/client-key.pem')

# Security Alert Settings
SECURITY_ALERT_RECIPIENTS = config('SECURITY_ALERT_RECIPIENTS', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])
SECURITY_ALERT_ON_HIGH_SEVERITY = config('SECURITY_ALERT_ON_HIGH_SEVERITY', default=True, cast=bool)
SECURITY_ALERT_ON_CRITICAL_SEVERITY = config('SECURITY_ALERT_ON_CRITICAL_SEVERITY', default=True, cast=bool)


# Password validation
# Requirements: 3.4 - Enhanced password strength validation for reset endpoint
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'first_name', 'last_name', 'email'),
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Additional password security settings
PASSWORD_RESET_TIMEOUT = 3600  # 1 hour in seconds
PASSWORD_RESET_RATE_LIMIT = 5  # Maximum requests per hour per IP

# Authentication Rate Limiting Settings
AUTH_RATE_LIMITING = {
    'ENABLED': config('AUTH_RATE_LIMITING_ENABLED', default=True, cast=bool),
    'LOGIN_ATTEMPTS': config('AUTH_LOGIN_RATE_LIMIT', default=5, cast=int),
    'LOGIN_WINDOW': config('AUTH_LOGIN_RATE_WINDOW', default=900, cast=int),  # 15 minutes
    'REGISTER_ATTEMPTS': config('AUTH_REGISTER_RATE_LIMIT', default=10, cast=int),
    'REGISTER_WINDOW': config('AUTH_REGISTER_RATE_WINDOW', default=3600, cast=int),  # 1 hour
    'PASSWORD_RESET_ATTEMPTS': config('AUTH_PASSWORD_RESET_RATE_LIMIT', default=5, cast=int),
    'PASSWORD_RESET_WINDOW': config('AUTH_PASSWORD_RESET_RATE_WINDOW', default=3600, cast=int),  # 1 hour
    'EMAIL_VERIFICATION_ATTEMPTS': config('AUTH_EMAIL_VERIFICATION_RATE_LIMIT', default=3, cast=int),
    'EMAIL_VERIFICATION_WINDOW': config('AUTH_EMAIL_VERIFICATION_RATE_WINDOW', default=3600, cast=int),  # 1 hour
    'ADMIN_LOGIN_ATTEMPTS': config('AUTH_ADMIN_LOGIN_RATE_LIMIT', default=3, cast=int),
    'ADMIN_LOGIN_WINDOW': config('AUTH_ADMIN_LOGIN_RATE_WINDOW', default=900, cast=int),  # 15 minutes
}

# Account Lockout Settings
ACCOUNT_LOCKOUT = {
    'ENABLED': config('ACCOUNT_LOCKOUT_ENABLED', default=True, cast=bool),
    'MAX_FAILED_ATTEMPTS': config('ACCOUNT_LOCKOUT_MAX_ATTEMPTS', default=5, cast=int),
    'LOCKOUT_DURATION_MINUTES': config('ACCOUNT_LOCKOUT_DURATION', default=30, cast=int),
    'RESET_ON_SUCCESS': config('ACCOUNT_LOCKOUT_RESET_ON_SUCCESS', default=True, cast=bool),
}

# IP Security Monitoring Settings
IP_SECURITY_MONITORING = {
    'ENABLED': config('IP_SECURITY_MONITORING_ENABLED', default=True, cast=bool),
    'REQUESTS_PER_MINUTE_THRESHOLD': config('IP_REQUESTS_PER_MINUTE_THRESHOLD', default=30, cast=int),
    'FAILED_LOGINS_PER_HOUR_THRESHOLD': config('IP_FAILED_LOGINS_PER_HOUR_THRESHOLD', default=10, cast=int),
    'ENDPOINTS_PER_MINUTE_THRESHOLD': config('IP_ENDPOINTS_PER_MINUTE_THRESHOLD', default=10, cast=int),
    'LOG_SUSPICIOUS_ACTIVITY': config('IP_LOG_SUSPICIOUS_ACTIVITY', default=True, cast=bool),
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'authentication.User'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.CustomPageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    'DEFAULT_VERSIONING_CLASS': 'core.versioning.CustomURLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
    'VERSION_PARAM': 'version',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# API Versioning Configuration
API_VERSIONS = ['v1', 'v2']
DEFAULT_API_VERSION = 'v1'
RECOMMENDED_API_VERSION = 'v2'
DEPRECATED_API_VERSIONS = ['v1']  # v1 is now deprecated
API_SUNSET_DATES = {
    'v1': '2025-12-31',  # v1 will be removed on December 31, 2025
}

# Version-specific feature flags
API_VERSION_FEATURES = {
    'v1': {
        'advanced_search': False,
        'bulk_operations': False,
        'enhanced_analytics': False,
    },
    'v2': {
        'advanced_search': True,
        'bulk_operations': True,
        'enhanced_analytics': True,
    }
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

# Frontend URL for email links
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

# Celery Configuration - Disabled for development
CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@ecommerce.com')

# SMS Configuration (for future integration)
SMS_BACKEND = config('SMS_BACKEND', default='console')  # console, twilio, aws_sns
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='')

# Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# DRF Spectacular Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'E-Commerce Platform API',
    'DESCRIPTION': 'A comprehensive API for the multi-vendor e-commerce platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': r'/api/v[0-9]',
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_SPLIT_RESPONSE': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'defaultModelsExpandDepth': 3,
        'defaultModelExpandDepth': 3,
        'docExpansion': 'list',
    },
    'TAGS': [
        {'name': 'Authentication', 'description': 'Authentication endpoints'},
        {'name': 'Products', 'description': 'Product management endpoints'},
        {'name': 'Orders', 'description': 'Order management endpoints'},
        {'name': 'Cart', 'description': 'Shopping cart endpoints'},
        {'name': 'Inventory', 'description': 'Inventory management endpoints'},
        {'name': 'Customers', 'description': 'Customer management endpoints'},
        {'name': 'Payments', 'description': 'Payment processing endpoints'},
        {'name': 'Shipping', 'description': 'Shipping and logistics endpoints'},
        {'name': 'Sellers', 'description': 'Seller management endpoints'},
        {'name': 'Analytics', 'description': 'Analytics and reporting endpoints'},
        {'name': 'Content', 'description': 'Content management endpoints'},
        {'name': 'Reviews', 'description': 'Product review endpoints'},
        {'name': 'Search', 'description': 'Search and filtering endpoints'},
        {'name': 'Notifications', 'description': 'Notification management endpoints'},
    ],
    'SERVERS': [
        {'url': '/api/v1', 'description': 'API v1 (Legacy)'},
        {'url': '/api/v2', 'description': 'API v2 (Current)'},
    ],
    'SECURITY': [
        {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': 'Enter your bearer token in the format: Bearer <token>'
            }
        }
    ],
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'Bearer': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'JWT token authentication'
            }
        }
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
        'hideHostname': False,
        'expandResponses': '200,201',
        'pathInMiddlePanel': True,
    },
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}