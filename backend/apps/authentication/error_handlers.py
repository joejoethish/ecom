"""
Authentication-specific error handlers and middleware.

This module provides specialized error handling for authentication operations,
integrating with the core exception handling system.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.core.cache import cache
import logging
import time

from .exceptions import (
    AuthErrorResponse, create_structured_error_response,
    RateLimitExceededException, SecurityViolationException,
    BruteForceDetectedException, CSRFTokenMissingException,
    CSRFTokenInvalidException, log_security_event
)

logger = logging.getLogger(__name__)


def authentication_exception_handler(exc, context):
    """
    Custom exception handler specifically for authentication errors.
    
    This handler provides enhanced error responses for authentication-related
    exceptions while maintaining compatibility with the core exception handler.
    
    Args:
        exc: Exception instance
        context: Context dictionary containing request and view information
        
    Returns:
        Response object with structured error data
    """
    # Get request from context
    request = context.get('request')
    view = context.get('view')
    
    # Call the default exception handler first
    response = exception_handler(exc, context)
    
    # Handle authentication-specific exceptions
    if isinstance(exc, (RateLimitExceededException, SecurityViolationException)):
        return _handle_security_exception(exc, request, response)
    
    # If it's a standard DRF exception, enhance the response
    if response is not None:
        return _enhance_standard_response(exc, request, response)
    
    # Handle unexpected exceptions
    return _handle_unexpected_exception(exc, request)


def _handle_security_exception(exc, request, response):
    """Handle security-related exceptions with enhanced logging and response."""
    
    # Log security event
    event_details = {
        'exception_type': type(exc).__name__,
        'message': str(exc),
        'user_agent': request.META.get('HTTP_USER_AGENT', '') if request else '',
        'path': request.path if request else '',
        'method': request.method if request else ''
    }
    
    log_security_event(
        event_type='SECURITY_EXCEPTION',
        user=getattr(request, 'user', None) if request else None,
        ip_address=_get_client_ip(request) if request else None,
        details=event_details
    )
    
    # Create structured error response
    error_response = create_structured_error_response(exc, request)
    
    # Add security-specific headers
    headers = {}
    
    if isinstance(exc, RateLimitExceededException):
        if hasattr(exc, 'retry_after') and exc.retry_after:
            headers['Retry-After'] = str(exc.retry_after)
        if hasattr(exc, 'limit') and exc.limit:
            headers['X-RateLimit-Limit'] = str(exc.limit)
            headers['X-RateLimit-Remaining'] = '0'
    
    if isinstance(exc, BruteForceDetectedException):
        headers['X-Security-Warning'] = 'Brute force attack detected'
    
    return Response(
        error_response,
        status=getattr(exc, 'status_code', status.HTTP_400_BAD_REQUEST),
        headers=headers
    )


def _enhance_standard_response(exc, request, response):
    """Enhance standard DRF exception responses with authentication context."""
    
    # Create structured error response
    error_response = create_structured_error_response(exc, request)
    
    # Preserve original status code
    response.data = error_response
    
    # Add authentication-specific headers
    if hasattr(request, 'user') and request.user.is_authenticated:
        response['X-User-ID'] = str(request.user.id)
    
    response['X-Error-ID'] = _generate_error_id()
    response['X-Timestamp'] = timezone.now().isoformat()
    
    return response


def _handle_unexpected_exception(exc, request):
    """Handle unexpected exceptions with proper logging and generic response."""
    
    # Log the unexpected exception
    logger.error(
        f"Unexpected authentication exception: {type(exc).__name__}",
        exc_info=True,
        extra={
            'exception_type': type(exc).__name__,
            'message': str(exc),
            'path': request.path if request else '',
            'method': request.method if request else '',
            'user_id': request.user.id if request and hasattr(request, 'user') and request.user.is_authenticated else None
        }
    )
    
    # Create generic error response
    error_response = {
        'success': False,
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred. Please try again later.',
            'timestamp': timezone.now().isoformat(),
            'error_id': _generate_error_id()
        }
    }
    
    return Response(
        error_response,
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def _get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _generate_error_id():
    """Generate unique error ID for tracking."""
    import uuid
    return str(uuid.uuid4())[:8]


class AuthenticationErrorMiddleware:
    """
    Middleware for handling authentication errors and security monitoring.
    
    This middleware provides additional security features like:
    - Request monitoring and logging
    - Rate limiting enforcement
    - Security header injection
    - Error response enhancement
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Pre-process request
        self._pre_process_request(request)
        
        # Process request
        response = self.get_response(request)
        
        # Post-process response
        return self._post_process_response(request, response)
    
    def _pre_process_request(self, request):
        """Pre-process request for security monitoring."""
        
        # Add request timestamp
        request._auth_start_time = time.time()
        
        # Log authentication requests
        if self._is_auth_request(request):
            logger.info(
                f"Authentication request: {request.method} {request.path}",
                extra={
                    'ip_address': _get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'path': request.path,
                    'method': request.method
                }
            )
    
    def _post_process_response(self, request, response):
        """Post-process response with security enhancements."""
        
        # Add security headers to authentication responses
        if self._is_auth_request(request):
            self._add_security_headers(response)
        
        # Log authentication response
        if hasattr(request, '_auth_start_time'):
            duration = time.time() - request._auth_start_time
            
            if response.status_code >= 400:
                logger.warning(
                    f"Authentication error: {response.status_code} for {request.path}",
                    extra={
                        'status_code': response.status_code,
                        'duration': duration,
                        'ip_address': _get_client_ip(request),
                        'path': request.path,
                        'method': request.method
                    }
                )
        
        return response
    
    def _is_auth_request(self, request):
        """Check if request is authentication-related."""
        auth_paths = [
            '/api/v1/auth/',
            '/api/v1/admin-auth/',
            '/api/v1/users/me/',
        ]
        return any(request.path.startswith(path) for path in auth_paths)
    
    def _add_security_headers(self, response):
        """Add security headers to response."""
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Cache-Control': 'no-store, no-cache, must-revalidate, private',
            'Pragma': 'no-cache'
        }
        
        for header, value in security_headers.items():
            if header not in response:
                response[header] = value


class RateLimitingMiddleware:
    """
    Enhanced rate limiting middleware for authentication endpoints.
    
    This middleware provides more sophisticated rate limiting with:
    - Per-endpoint rate limits
    - User-based and IP-based limiting
    - Sliding window algorithm
    - Rate limit headers
    """
    
    # Rate limit configurations
    RATE_LIMITS = {
        '/api/v1/auth/login/': {'limit': 5, 'window': 900, 'per': 'ip'},  # 5 per 15 min per IP
        '/api/v1/auth/register/': {'limit': 3, 'window': 3600, 'per': 'ip'},  # 3 per hour per IP
        '/api/v1/auth/forgot-password/': {'limit': 5, 'window': 3600, 'per': 'ip'},  # 5 per hour per IP
        '/api/v1/auth/reset-password/': {'limit': 10, 'window': 3600, 'per': 'ip'},  # 10 per hour per IP
        '/api/v1/auth/resend-verification/': {'limit': 3, 'window': 3600, 'per': 'user'},  # 3 per hour per user
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check rate limits before processing request
        rate_limit_response = self._check_rate_limits(request)
        if rate_limit_response:
            return rate_limit_response
        
        response = self.get_response(request)
        
        # Add rate limit headers to response
        self._add_rate_limit_headers(request, response)
        
        return response
    
    def _check_rate_limits(self, request):
        """Check if request should be rate limited."""
        
        # Only check POST requests
        if request.method != 'POST':
            return None
        
        # Find matching rate limit configuration
        rate_limit_config = None
        for path, config in self.RATE_LIMITS.items():
            if request.path.startswith(path):
                rate_limit_config = config
                break
        
        if not rate_limit_config:
            return None
        
        # Get identifier based on configuration
        if rate_limit_config['per'] == 'user':
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return None
            identifier = f"user:{request.user.id}"
        else:  # per IP
            identifier = f"ip:{_get_client_ip(request)}"
        
        # Check rate limit
        try:
            self._enforce_rate_limit(
                identifier=identifier,
                endpoint=request.path,
                limit=rate_limit_config['limit'],
                window=rate_limit_config['window']
            )
        except RateLimitExceededException as e:
            return self._create_rate_limit_response(e)
        
        return None
    
    def _enforce_rate_limit(self, identifier, endpoint, limit, window):
        """Enforce rate limit using sliding window algorithm."""
        
        cache_key = f"rate_limit:{endpoint}:{identifier}"
        current_time = int(time.time())
        
        # Get current request timestamps
        request_times = cache.get(cache_key, [])
        
        # Remove timestamps outside the current window
        window_start = current_time - window
        request_times = [t for t in request_times if t > window_start]
        
        # Check if rate limit exceeded
        if len(request_times) >= limit:
            oldest_request = min(request_times)
            reset_time = oldest_request + window
            retry_after = reset_time - current_time
            
            raise RateLimitExceededException(
                retry_after=retry_after,
                limit=limit,
                window=window
            )
        
        # Add current request timestamp
        request_times.append(current_time)
        cache.set(cache_key, request_times, window)
        
        # Store rate limit info for headers
        remaining = limit - len(request_times)
        setattr(request, '_rate_limit_info', {
            'limit': limit,
            'remaining': remaining,
            'reset': current_time + window
        })
    
    def _create_rate_limit_response(self, exception):
        """Create rate limit exceeded response."""
        
        error_response = create_structured_error_response(exception)
        
        headers = {
            'Retry-After': str(exception.retry_after) if exception.retry_after else '60',
            'X-RateLimit-Limit': str(exception.limit) if exception.limit else '0',
            'X-RateLimit-Remaining': '0'
        }
        
        return Response(
            error_response,
            status=status.HTTP_429_TOO_MANY_REQUESTS,
            headers=headers
        )
    
    def _add_rate_limit_headers(self, request, response):
        """Add rate limit headers to response."""
        
        if hasattr(request, '_rate_limit_info'):
            info = request._rate_limit_info
            response['X-RateLimit-Limit'] = str(info['limit'])
            response['X-RateLimit-Remaining'] = str(info['remaining'])
            response['X-RateLimit-Reset'] = str(info['reset'])