"""
Request logging middleware for the ecommerce platform.
"""
import logging
import time
import json
import re
import uuid
from django.utils import timezone
from django.conf import settings
from django.urls import resolve, Resolver404

# Create dedicated loggers
request_logger = logging.getLogger('request')
performance_logger = logging.getLogger('performance')
security_logger = logging.getLogger('security')

class RequestLoggingMiddleware:
    """
    Middleware to log all HTTP requests.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.log_level = getattr(settings, 'REQUEST_LOG_LEVEL', logging.INFO)
        self.log_body = getattr(settings, 'REQUEST_LOG_BODY', False)
        self.max_body_length = getattr(settings, 'REQUEST_LOG_MAX_BODY_LENGTH', 1000)
        self.sensitive_headers = getattr(settings, 'REQUEST_LOG_SENSITIVE_HEADERS', 
                                        ['Authorization', 'Cookie', 'Set-Cookie'])
        self.sensitive_body_fields = getattr(settings, 'REQUEST_LOG_SENSITIVE_BODY_FIELDS',
                                           ['password', 'token', 'secret', 'credit_card', 'card_number'])
        self.exclude_paths = getattr(settings, 'REQUEST_LOG_EXCLUDE_PATHS', [
            r'^/static/',
            r'^/media/',
            r'^/favicon\.ico$',
            r'^/api/health/',
        ])
    
    def __call__(self, request):
        # Generate a unique request ID for tracing
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        
        # Check if path should be excluded from logging
        if self._should_exclude_path(request.path):
            return self.get_response(request)
        
        start_time = time.time()
        
        # Process the request
        response = self.get_response(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Log the request
        self.log_request(request, response, duration, request_id)
        
        # Add request ID to response headers for debugging
        response['X-Request-ID'] = request_id
        
        return response
        
    def _should_exclude_path(self, path):
        """
        Check if the path should be excluded from logging.
        """
        return any(re.match(pattern, path) for pattern in self.exclude_paths)
    
    def log_request(self, request, response, duration, request_id):
        """
        Log the request details.
        
        Args:
            request: The HTTP request object
            response: The HTTP response object
            duration: Request processing duration in seconds
            request_id: Unique identifier for the request
        """
        # Get user ID if authenticated
        user_id = None
        username = 'anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
            username = request.user.username
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '')
        
        # Try to get the view name
        view_name = "unknown"
        try:
            resolver_match = resolve(request.path)
            view_name = f"{resolver_match.func.__module__}.{resolver_match.func.__name__}"
        except Resolver404:
            pass
        
        # Prepare log data
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'view': view_name,
            'query_string': request.META.get('QUERY_STRING', ''),
            'status_code': response.status_code,
            'duration_ms': int(duration * 1000),
            'user_id': user_id,
            'username': username,
            'ip_address': ip_address,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
            'content_length': request.META.get('CONTENT_LENGTH', ''),
            'content_type': request.META.get('CONTENT_TYPE', ''),
        }
        
        # Add request headers (excluding sensitive ones)
        headers = {}
        for header, value in request.META.items():
            if header.startswith('HTTP_'):
                header_name = header[5:].lower().replace('_', '-')
                if header_name not in [h.lower() for h in self.sensitive_headers]:
                    headers[header_name] = value
        log_data['headers'] = headers
        
        # Add request body if enabled (and mask sensitive fields)
        if self.log_body and request.body:
            try:
                if request.content_type and 'application/json' in request.content_type:
                    body = json.loads(request.body)
                    # Mask sensitive fields
                    for field in self.sensitive_body_fields:
                        if field in body:
                            body[field] = '*****'
                    log_data['body'] = body
                else:
                    # For non-JSON bodies, just log the length
                    log_data['body_length'] = len(request.body)
            except Exception:
                log_data['body_parse_error'] = True
        
        # Add response size
        if hasattr(response, 'content'):
            log_data['response_size'] = len(response.content)
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = self.log_level
        
        # Log the request
        request_logger.log(
            log_level,
            f"{request.method} {request.path} {response.status_code} {log_data['duration_ms']}ms",
            extra=log_data
        )


class SecurityAuditMiddleware:
    """
    Middleware to log security-relevant requests for audit purposes.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.security_logger = logging.getLogger('security')
        
        # Define security-relevant paths
        self.security_paths = getattr(settings, 'SECURITY_AUDIT_PATHS', [
            '/api/v1/auth/',
            '/api/v1/admin/',
            '/api/v1/users/',
            '/api/v1/permissions/',
            '/api/v1/payments/',
            '/api/v1/sellers/verification/',
        ])
        
        # Define sensitive operations that should be logged
        self.sensitive_operations = getattr(settings, 'SECURITY_SENSITIVE_OPERATIONS', [
            ('POST', r'^/api/v1/auth/login'),
            ('POST', r'^/api/v1/auth/register'),
            ('POST', r'^/api/v1/auth/password/reset'),
            ('POST', r'^/api/v1/auth/password/change'),
            ('POST', r'^/api/v1/payments'),
            ('PUT', r'^/api/v1/users/\d+/permissions'),
            ('DELETE', r'^/api/v1/users/\d+'),
        ])
    
    def __call__(self, request):
        # Check if this is a security-relevant request before processing
        is_security_relevant = self._is_security_relevant(request.method, request.path)
        is_sensitive_operation = self._is_sensitive_operation(request.method, request.path)
        
        # Process the request
        response = self.get_response(request)
        
        # Log security-relevant requests
        if is_security_relevant:
            self._log_security_request(request, response)
        
        # Log sensitive operations with more detail
        if is_sensitive_operation:
            self._log_sensitive_operation(request, response)
        
        # Log failed requests (status 4xx or 5xx) to security-sensitive endpoints
        if (is_security_relevant or is_sensitive_operation) and response.status_code >= 400:
            self._log_security_failure(request, response)
        
        return response
    
    def _is_security_relevant(self, method, path):
        """
        Determine if a path is security-relevant.
        """
        return any(path.startswith(security_path) for security_path in self.security_paths)
    
    def _is_sensitive_operation(self, method, path):
        """
        Determine if this is a sensitive operation based on method and path.
        """
        return any(
            method == op_method and re.match(op_path, path)
            for op_method, op_path in self.sensitive_operations
        )
    
    def _log_security_request(self, request, response):
        """
        Log security-relevant request details.
        """
        # Get user ID if authenticated
        user_id = None
        username = 'anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
            username = request.user.username
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '')
        
        # Get request ID if available
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        
        # Prepare log data
        log_data = {
            'event_type': 'security_request',
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'user_id': user_id,
            'username': username,
            'ip_address': ip_address,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': timezone.now().isoformat(),
        }
        
        # Determine log level based on status code
        if response.status_code >= 400:
            log_level = logging.WARNING
            log_data['event_type'] = 'security_request_failure'
        else:
            log_level = logging.INFO
        
        # Log the security request
        self.security_logger.log(
            log_level,
            f"Security request: {request.method} {request.path} {response.status_code}",
            extra=log_data
        )
    
    def _log_sensitive_operation(self, request, response):
        """
        Log sensitive operation with detailed information.
        """
        # Get user ID if authenticated
        user_id = None
        username = 'anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
            username = request.user.username
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '')
        
        # Get request ID if available
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        
        # Prepare log data
        log_data = {
            'event_type': 'sensitive_operation',
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'user_id': user_id,
            'username': username,
            'ip_address': ip_address,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
            'timestamp': timezone.now().isoformat(),
        }
        
        # Log the sensitive operation
        self.security_logger.warning(
            f"Sensitive operation: {request.method} {request.path} by {username} from {ip_address}",
            extra=log_data
        )
    
    def _log_security_failure(self, request, response):
        """
        Log security failures with detailed information.
        """
        # Get user ID if authenticated
        user_id = None
        username = 'anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
            username = request.user.username
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '')
        
        # Get request ID if available
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        
        # Prepare log data
        log_data = {
            'event_type': 'security_failure',
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'user_id': user_id,
            'username': username,
            'ip_address': ip_address,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
            'timestamp': timezone.now().isoformat(),
        }
        
        # Log the security failure
        self.security_logger.error(
            f"Security failure: {request.method} {request.path} {response.status_code} by {username} from {ip_address}",
            extra=log_data
        )


class PerformanceMonitoringMiddleware:
    """
    Middleware to monitor and log slow requests and performance metrics.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.performance_logger = logging.getLogger('performance')
        self.slow_threshold_ms = getattr(settings, 'SLOW_REQUEST_THRESHOLD_MS', 500)
        self.very_slow_threshold_ms = getattr(settings, 'VERY_SLOW_REQUEST_THRESHOLD_MS', 2000)
        self.track_all_requests = getattr(settings, 'TRACK_ALL_REQUEST_PERFORMANCE', False)
    
    def __call__(self, request):
        start_time = time.time()
        
        # Process the request
        response = self.get_response(request)
        
        # Calculate request duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Get request ID if available
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        
        # Log performance metrics
        if self.track_all_requests:
            self._log_performance_metrics(request, response, duration_ms, request_id)
        
        # Log slow requests
        if duration_ms > self.slow_threshold_ms:
            self._log_slow_request(request, response, duration_ms, request_id)
        
        # Add performance header
        response['X-Response-Time-Ms'] = str(duration_ms)
        
        return response
    
    def _log_performance_metrics(self, request, response, duration_ms, request_id):
        """
        Log performance metrics for all requests.
        """
        # Try to get the view name
        view_name = "unknown"
        try:
            resolver_match = resolve(request.path)
            view_name = f"{resolver_match.func.__module__}.{resolver_match.func.__name__}"
        except Resolver404:
            pass
        
        # Prepare log data
        log_data = {
            'metric_name': 'request_duration',
            'metric_value': duration_ms,
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'view': view_name,
            'status_code': response.status_code,
            'timestamp': timezone.now().isoformat(),
        }
        
        # Log the performance metric
        self.performance_logger.info(
            f"Request performance: {request.method} {request.path} took {duration_ms}ms",
            extra=log_data
        )
    
    def _log_slow_request(self, request, response, duration_ms, request_id):
        """
        Log details of a slow request.
        """
        # Get user ID if authenticated
        user_id = None
        username = 'anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
            username = request.user.username
        
        # Try to get the view name
        view_name = "unknown"
        try:
            resolver_match = resolve(request.path)
            view_name = f"{resolver_match.func.__module__}.{resolver_match.func.__name__}"
        except Resolver404:
            pass
        
        # Prepare log data
        log_data = {
            'metric_name': 'slow_request',
            'metric_value': duration_ms,
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'view': view_name,
            'query_string': request.META.get('QUERY_STRING', ''),
            'user_id': user_id,
            'username': username,
            'content_type': request.META.get('CONTENT_TYPE', ''),
            'threshold_ms': self.slow_threshold_ms,
            'timestamp': timezone.now().isoformat(),
        }
        
        # Determine log level based on duration
        if duration_ms > self.very_slow_threshold_ms:
            log_level = logging.ERROR
            log_data['severity'] = 'very_slow'
        else:
            log_level = logging.WARNING
            log_data['severity'] = 'slow'
        
        # Log the slow request
        self.performance_logger.log(
            log_level,
            f"Slow request: {request.method} {request.path} took {duration_ms}ms (threshold: {self.slow_threshold_ms}ms)",
            extra=log_data
        )
        
        # Store performance metric in database for analysis
        try:
            from apps.logs.models import PerformanceMetric
            
            PerformanceMetric.objects.create(
                name='slow_request',
                value=duration_ms,
                endpoint=request.path,
                method=request.method,
                response_time=duration_ms
            )
        except Exception as e:
            # Log the error but don't fail the request
            self.performance_logger.error(f"Failed to store performance metric: {str(e)}")