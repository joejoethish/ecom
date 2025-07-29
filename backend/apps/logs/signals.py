"""
Signal handlers for logging and monitoring.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import user_logged_in, user_logged_out, user_login_failed
from django.contrib.auth.signals import user_login_failed
from django.core.signals import request_finished, request_started, got_request_exception
from django.db.backends.signals import connection_created

from backend.logs.security import log_login_attempt, log_suspicious_activity
from backend.logs.metrics import log_user_registration
from apps.logs.models import SecurityEvent, SystemLog, BusinessMetric, PerformanceMetric

# Create dedicated loggers
security_logger = logging.getLogger('security')
metrics_logger = logging.getLogger('metrics')
system_logger = logging.getLogger('django')


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Log successful user login.
    """
    if not user:
        return
    
    # Get client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0].strip()
    else:
        ip_address = request.META.get('REMOTE_ADDR', '')
    
    # Log the login attempt
    log_login_attempt(
        username=user.username,
        success=True,
        ip_address=ip_address,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        extra_data={
            'user_id': user.id,
            'email': user.email,
            'path': request.path,
        }
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Log user logout.
    """
    if not user:
        return
    
    # Get client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0].strip()
    else:
        ip_address = request.META.get('REMOTE_ADDR', '')
    
    # Log the logout
    security_logger.info(
        f"User logged out: {user.username}",
        extra={
            'event_type': 'logout',
            'user_id': user.id,
            'username': user.username,
            'ip_address': ip_address,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
    )


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    """
    Log failed login attempts.
    """
    if not request:
        return
    
    # Get client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0].strip()
    else:
        ip_address = request.META.get('REMOTE_ADDR', '')
    
    # Get username from credentials
    username = credentials.get('username', 'unknown')
    
    # Log the failed login attempt
    log_login_attempt(
        username=username,
        success=False,
        ip_address=ip_address,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        extra_data={
            'path': request.path,
        }
    )
    
    # Check for multiple failed login attempts
    try:
        # Count recent failed login attempts from this IP for this username
        recent_failures = SecurityEvent.objects.filter(
            event_type='login_failure',
            username=username,
            ip_address=ip_address,
        ).count()
        
        # If there are multiple failures, log a suspicious activity
        if recent_failures >= 5:
            log_suspicious_activity(
                user_id=None,
                username=username,
                ip_address=ip_address,
                activity_type='multiple_failed_logins',
                details={
                    'failure_count': recent_failures,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                }
            )
    except Exception as e:
        # Log the error but don't fail the operation
        security_logger.error(f"Failed to check for multiple login failures: {str(e)}")


@receiver(post_save, sender='auth.User')
def log_user_creation(sender, instance, created, **kwargs):
    """
    Log user creation.
    """
    if created:
        # Log the user registration
        log_user_registration(
            user_id=instance.id,
            source='admin' if instance.is_staff else 'registration',
        )
        
        # Log security event
        security_logger.info(
            f"User created: {instance.username}",
            extra={
                'event_type': 'user_created',
                'user_id': instance.id,
                'username': instance.username,
                'is_staff': instance.is_staff,
                'is_superuser': instance.is_superuser,
            }
        )


@receiver(got_request_exception)
def log_request_exception(sender, request, **kwargs):
    """
    Log exceptions that occur during request processing.
    """
    # This is already handled by Django's logging system,
    # but we can add additional context or metrics here
    pass


@receiver(connection_created)
def log_db_connection(sender, connection, **kwargs):
    """
    Log database connection creation.
    """
    system_logger.debug(
        f"Database connection created: {connection.alias}",
        extra={
            'event_type': 'db_connection_created',
            'db_alias': connection.alias,
            'db_vendor': connection.vendor,
        }
    )


# Add more signal handlers as needed for specific business events
# For example, you might want to log order creation, payment processing, etc.