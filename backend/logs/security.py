"""
Security logging utilities for the ecommerce platform.
"""
import logging
import json
from django.utils import timezone
from django.conf import settings

# Create a dedicated security logger
security_logger = logging.getLogger('security')


def log_login_attempt(username, success, ip_address, user_agent=None, extra_data=None):
    """
    Log a login attempt.
    
    Args:
        username: The username used in the login attempt
        success: Boolean indicating if the login was successful
        ip_address: IP address of the client
        user_agent: User agent string from the request
        extra_data: Any additional data to include in the log
    """
    event_type = 'login_success' if success else 'login_failure'
    
    extra = {
        'event_type': event_type,
        'username': username,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'extra_data': extra_data or {},
    }
    
    if success:
        security_logger.info(f"Successful login for user: {username}", extra=extra)
    else:
        security_logger.warning(f"Failed login attempt for user: {username}", extra=extra)


def log_password_change(user_id, username, ip_address, user_agent=None, reset=False):
    """
    Log a password change or reset event.
    
    Args:
        user_id: ID of the user
        username: Username of the user
        ip_address: IP address of the client
        user_agent: User agent string from the request
        reset: Boolean indicating if this was a password reset (True) or change (False)
    """
    event_type = 'password_reset' if reset else 'password_change'
    
    extra = {
        'event_type': event_type,
        'user_id': user_id,
        'username': username,
        'ip_address': ip_address,
        'user_agent': user_agent,
    }
    
    security_logger.info(
        f"{'Password reset' if reset else 'Password change'} for user: {username}",
        extra=extra
    )


def log_permission_change(user_id, username, changed_by_id, changed_by_username, 
                         permission, action, ip_address):
    """
    Log a permission change event.
    
    Args:
        user_id: ID of the user whose permissions were changed
        username: Username of the user whose permissions were changed
        changed_by_id: ID of the user who made the change
        changed_by_username: Username of the user who made the change
        permission: The permission that was changed
        action: The action taken (add, remove)
        ip_address: IP address of the client
    """
    extra = {
        'event_type': 'permission_change',
        'user_id': user_id,
        'username': username,
        'changed_by_id': changed_by_id,
        'changed_by_username': changed_by_username,
        'permission': permission,
        'action': action,
        'ip_address': ip_address,
    }
    
    security_logger.info(
        f"Permission '{permission}' {action}ed for user: {username} by {changed_by_username}",
        extra=extra
    )


def log_access_violation(user_id, username, ip_address, resource, action, user_agent=None):
    """
    Log an access violation attempt.
    
    Args:
        user_id: ID of the user (or None for anonymous)
        username: Username of the user (or 'anonymous')
        ip_address: IP address of the client
        resource: The resource that was accessed
        action: The action attempted (read, write, delete, etc.)
        user_agent: User agent string from the request
    """
    extra = {
        'event_type': 'access_violation',
        'user_id': user_id,
        'username': username,
        'ip_address': ip_address,
        'resource': resource,
        'action': action,
        'user_agent': user_agent,
    }
    
    security_logger.warning(
        f"Access violation: User {username} attempted to {action} {resource}",
        extra=extra
    )


def log_admin_action(user_id, username, ip_address, action, resource, resource_id=None, 
                    details=None):
    """
    Log an administrative action.
    
    Args:
        user_id: ID of the admin user
        username: Username of the admin user
        ip_address: IP address of the client
        action: The action taken (create, update, delete, etc.)
        resource: The resource type that was modified
        resource_id: ID of the specific resource
        details: Additional details about the action
    """
    extra = {
        'event_type': 'admin_action',
        'user_id': user_id,
        'username': username,
        'ip_address': ip_address,
        'action': action,
        'resource': resource,
        'resource_id': resource_id,
        'details': details or {},
    }
    
    security_logger.info(
        f"Admin action: {username} {action}d {resource}" + 
        (f" (ID: {resource_id})" if resource_id else ""),
        extra=extra
    )


def log_api_key_usage(key_id, user_id, username, ip_address, endpoint, method):
    """
    Log API key usage.
    
    Args:
        key_id: ID of the API key
        user_id: ID of the user associated with the key
        username: Username of the user
        ip_address: IP address of the client
        endpoint: The API endpoint accessed
        method: The HTTP method used
    """
    extra = {
        'event_type': 'api_key_usage',
        'key_id': key_id,
        'user_id': user_id,
        'username': username,
        'ip_address': ip_address,
        'endpoint': endpoint,
        'method': method,
    }
    
    security_logger.info(
        f"API key used: {username} accessed {endpoint} using method {method}",
        extra=extra
    )


def log_data_export(user_id, username, ip_address, data_type, record_count, 
                   file_format, filters=None):
    """
    Log a data export event.
    
    Args:
        user_id: ID of the user
        username: Username of the user
        ip_address: IP address of the client
        data_type: Type of data exported
        record_count: Number of records exported
        file_format: Format of the export (CSV, Excel, etc.)
        filters: Filters applied to the export
    """
    extra = {
        'event_type': 'data_export',
        'user_id': user_id,
        'username': username,
        'ip_address': ip_address,
        'data_type': data_type,
        'record_count': record_count,
        'file_format': file_format,
        'filters': filters or {},
    }
    
    security_logger.info(
        f"Data export: {username} exported {record_count} {data_type} records in {file_format} format",
        extra=extra
    )


def log_payment_action(user_id, username, ip_address, action, payment_id, amount, 
                      payment_method, status):
    """
    Log a payment-related action.
    
    Args:
        user_id: ID of the user
        username: Username of the user
        ip_address: IP address of the client
        action: The action (create, capture, refund, etc.)
        payment_id: ID of the payment
        amount: Payment amount
        payment_method: Payment method used
        status: Status of the payment
    """
    extra = {
        'event_type': 'payment_action',
        'user_id': user_id,
        'username': username,
        'ip_address': ip_address,
        'action': action,
        'payment_id': payment_id,
        'amount': str(amount),  # Convert Decimal to string for JSON serialization
        'payment_method': payment_method,
        'status': status,
    }
    
    security_logger.info(
        f"Payment {action}: {username} {action}d payment {payment_id} for {amount} using {payment_method} ({status})",
        extra=extra
    )


def log_suspicious_activity(user_id, username, ip_address, activity_type, details=None):
    """
    Log suspicious activity.
    
    Args:
        user_id: ID of the user (or None for anonymous)
        username: Username of the user (or 'anonymous')
        ip_address: IP address of the client
        activity_type: Type of suspicious activity
        details: Additional details about the activity
    """
    extra = {
        'event_type': 'suspicious_activity',
        'user_id': user_id,
        'username': username,
        'ip_address': ip_address,
        'activity_type': activity_type,
        'details': details or {},
    }
    
    security_logger.warning(
        f"Suspicious activity detected: {activity_type} from user {username} at {ip_address}",
        extra=extra
    )
    
    # Store security event in database
    try:
        from apps.logs.models import SecurityEvent
        
        SecurityEvent.objects.create(
            event_type='suspicious_activity',
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details={
                'activity_type': activity_type,
                'details': details or {}
            }
        )
    except Exception as e:
        # Log the error but don't fail the operation
        security_logger.error(f"Failed to store security event: {str(e)}")


def log_brute_force_attempt(ip_address, username, attempt_count, user_agent=None):
    """
    Log a potential brute force attempt.
    
    Args:
        ip_address: IP address of the client
        username: Username being targeted
        attempt_count: Number of failed attempts
        user_agent: User agent string from the request
    """
    extra = {
        'event_type': 'brute_force_attempt',
        'ip_address': ip_address,
        'username': username,
        'attempt_count': attempt_count,
        'user_agent': user_agent,
    }
    
    security_logger.error(
        f"Potential brute force attack detected: {attempt_count} failed login attempts for {username} from {ip_address}",
        extra=extra
    )
    
    # Store security event in database
    try:
        from apps.logs.models import SecurityEvent
        
        SecurityEvent.objects.create(
            event_type='brute_force_attempt',
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                'attempt_count': attempt_count
            }
        )
    except Exception as e:
        # Log the error but don't fail the operation
        security_logger.error(f"Failed to store security event: {str(e)}")


def log_csrf_failure(request, reason):
    """
    Log a CSRF failure.
    
    Args:
        request: The HTTP request object
        reason: Reason for the CSRF failure
    """
    # Get client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0].strip()
    else:
        ip_address = request.META.get('REMOTE_ADDR', '')
    
    # Get user ID if authenticated
    user_id = None
    username = 'anonymous'
    if hasattr(request, 'user') and request.user.is_authenticated:
        user_id = request.user.id
        username = request.user.username
    
    extra = {
        'event_type': 'csrf_failure',
        'user_id': user_id,
        'username': username,
        'ip_address': ip_address,
        'path': request.path,
        'method': request.method,
        'reason': reason,
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'referer': request.META.get('HTTP_REFERER', ''),
    }
    
    security_logger.warning(
        f"CSRF failure: {reason} on {request.method} {request.path} by {username} from {ip_address}",
        extra=extra
    )
    
    # Store security event in database
    try:
        from apps.logs.models import SecurityEvent
        
        SecurityEvent.objects.create(
            event_type='csrf_failure',
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            request_path=request.path,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={
                'method': request.method,
                'reason': reason,
                'referer': request.META.get('HTTP_REFERER', '')
            }
        )
    except Exception as e:
        # Log the error but don't fail the operation
        security_logger.error(f"Failed to store security event: {str(e)}")


def log_rate_limit_exceeded(request, rate_limit_group):
    """
    Log a rate limit exceeded event.
    
    Args:
        request: The HTTP request object
        rate_limit_group: The rate limit group that was exceeded
    """
    # Get client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0].strip()
    else:
        ip_address = request.META.get('REMOTE_ADDR', '')
    
    # Get user ID if authenticated
    user_id = None
    username = 'anonymous'
    if hasattr(request, 'user') and request.user.is_authenticated:
        user_id = request.user.id
        username = request.user.username
    
    extra = {
        'event_type': 'rate_limit_exceeded',
        'user_id': user_id,
        'username': username,
        'ip_address': ip_address,
        'path': request.path,
        'method': request.method,
        'rate_limit_group': rate_limit_group,
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
    }
    
    security_logger.warning(
        f"Rate limit exceeded: {rate_limit_group} on {request.method} {request.path} by {username} from {ip_address}",
        extra=extra
    )
    
    # Store security event in database
    try:
        from apps.logs.models import SecurityEvent
        
        SecurityEvent.objects.create(
            event_type='rate_limit_exceeded',
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            request_path=request.path,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={
                'method': request.method,
                'rate_limit_group': rate_limit_group
            }
        )
    except Exception as e:
        # Log the error but don't fail the operation
        security_logger.error(f"Failed to store security event: {str(e)}")