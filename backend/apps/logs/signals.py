"""
Signal handlers for logging system events.
"""
import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.core.signals import got_request_exception
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.backends.signals import connection_created

# from apps.logs.security import log_login_attempt, log_suspicious_activity
# from apps.logs.metrics import log_user_registration
from apps.logs.models import SecurityEvent, SystemLog, BusinessMetric, PerformanceMetric


# Create dedicated loggers
security_logger = logging.getLogger('security')
metrics_logger = logging.getLogger('metrics')
system_logger = logging.getLogger('django')

# All signal handlers are commented out for now to avoid import errors
# They can be uncommented once the required modules are implemented

# @receiver(user_logged_in)
# def log_user_login(sender, request, user, **kwargs):
#     """Log successful user login."""
#     pass

# @receiver(user_logged_out)
# def log_user_logout(sender, request, user, **kwargs):
#     """Log user logout."""
#     pass

# @receiver(user_login_failed)
# def log_login_failed(sender, credentials, request, **kwargs):
#     """Log failed login attempts."""
#     pass

# @receiver(post_save, sender='auth.User')
# def log_user_creation(sender, instance, created, **kwargs):
#     """Log user creation."""
#     pass

# @receiver(got_request_exception)
# def log_request_exception(sender, request, **kwargs):
#     """Log request exceptions."""
#     pass

# @receiver(connection_created)
# def log_db_connection(sender, connection, **kwargs):
#     """Log database connections."""
#     pass