"""
Authentication middleware for security and rate limiting.
"""
import time
import hashlib
from django.http import JsonResponse
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class PasswordResetRateLimitMiddleware:
    """
    Rate limiting middleware specifically for password reset endpoints.
    Requirements: 4.2, 4.3 - Implement rate limiting middleware for password reset endpoints
    """
    
    # Rate limiting configuration
    RATE_LIMIT_REQUESTS = 5  # Maximum requests per window
    RATE_LIMIT_WINDOW = 3600  # Window in seconds (1 hour)
    
    # Endpoints to apply rate limiting
    RATE_LIMITED_ENDPOINTS = [
        '/api/v1/auth/forgot-password/',
        '/api/v1/auth/reset-password/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this endpoint should be rate limited
        if self._should_rate_limit(request):
            # Check rate limit before processing request
            rate_limit_response = self._check_rate_limit(request)
            if rate_limit_response:
                return rate_limit_response
        
        response = self.get_response(request)
        return response

    def _should_rate_limit(self, request):
        """Check if the current request should be rate limited."""
        path = request.path_info
        method = request.method
        
        # Only rate limit POST requests to password reset endpoints
        if method != 'POST':
            return False
            
        return any(path.startswith(endpoint) for endpoint in self.RATE_LIMITED_ENDPOINTS)

    def _get_client_identifier(self, request):
        """
        Get a unique identifier for the client.
        Uses IP address with additional headers for better identification.
        """
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        # Include User-Agent for better fingerprinting
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create a hash of IP + User-Agent for cache key
        identifier = f"{ip}:{user_agent}"
        return hashlib.sha256(identifier.encode()).hexdigest()[:32]

    def _get_cache_key(self, request):
        """Generate cache key for rate limiting."""
        client_id = self._get_client_identifier(request)
        endpoint = request.path_info
        return f"rate_limit:password_reset:{client_id}:{endpoint}"

    def _check_rate_limit(self, request):
        """
        Check if the request should be rate limited.
        Returns JsonResponse if rate limited, None otherwise.
        """
        try:
            cache_key = self._get_cache_key(request)
            current_time = int(time.time())
            
            # Get current request timestamps from cache
            request_times = cache.get(cache_key, [])
            
            # Remove timestamps outside the current window
            window_start = current_time - self.RATE_LIMIT_WINDOW
            request_times = [t for t in request_times if t > window_start]
            
            # Check if rate limit exceeded
            if len(request_times) >= self.RATE_LIMIT_REQUESTS:
                # Calculate when the rate limit will reset
                oldest_request = min(request_times)
                reset_time = oldest_request + self.RATE_LIMIT_WINDOW
                retry_after = reset_time - current_time
                
                # Log rate limit violation
                client_ip = self._get_client_ip(request)
                logger.warning(
                    f"Rate limit exceeded for password reset endpoint. "
                    f"IP: {client_ip}, Endpoint: {request.path_info}, "
                    f"Requests: {len(request_times)}/{self.RATE_LIMIT_REQUESTS}"
                )
                
                return JsonResponse({
                    'success': False,
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': f'Too many requests. Please try again in {retry_after} seconds.',
                        'retry_after': retry_after
                    }
                }, status=429, headers={
                    'Retry-After': str(retry_after),
                    'X-RateLimit-Limit': str(self.RATE_LIMIT_REQUESTS),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(reset_time)
                })
            
            # Add current request timestamp
            request_times.append(current_time)
            
            # Update cache with new timestamps
            cache.set(cache_key, request_times, self.RATE_LIMIT_WINDOW)
            
            # Add rate limit headers to successful requests
            remaining = self.RATE_LIMIT_REQUESTS - len(request_times)
            request.rate_limit_headers = {
                'X-RateLimit-Limit': str(self.RATE_LIMIT_REQUESTS),
                'X-RateLimit-Remaining': str(remaining),
                'X-RateLimit-Reset': str(current_time + self.RATE_LIMIT_WINDOW)
            }
            
            return None  # No rate limiting
            
        except Exception as e:
            logger.error(f"Rate limiting check failed: {str(e)}")
            # In case of error, allow the request but log it
            return None

    def _get_client_ip(self, request):
        """Get client IP address for logging."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


class CSRFPasswordResetMiddleware:
    """
    Enhanced CSRF protection middleware for password reset forms.
    Requirements: 5.6 - Implement CSRF protection on all password reset forms
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add CSRF headers to password reset endpoints
        if self._is_password_reset_endpoint(request):
            self._add_csrf_headers(request, response)
        
        return response

    def _is_password_reset_endpoint(self, request):
        """Check if this is a password reset endpoint."""
        password_reset_paths = [
            '/api/v1/auth/forgot-password/',
            '/api/v1/auth/reset-password/',
            '/api/v1/auth/validate-reset-token/',
        ]
        return any(request.path_info.startswith(path) for path in password_reset_paths)

    def _add_csrf_headers(self, request, response):
        """Add CSRF-related security headers."""
        # Add CSRF token to response headers for frontend consumption
        if hasattr(request, 'META') and 'CSRF_COOKIE' in request.META:
            response['X-CSRFToken'] = request.META['CSRF_COOKIE']
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Add CORS headers specifically for password reset
        if request.method == 'OPTIONS':
            response['Access-Control-Allow-Headers'] = (
                'Accept, Content-Type, Content-Length, Accept-Encoding, '
                'X-CSRF-Token, Authorization, X-Requested-With'
            )
            response['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'


class SecurityHeadersMiddleware:
    """
    Add security headers to all responses.
    Requirements: General security enhancement for password reset system
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add rate limit headers if they were set by rate limiting middleware
        if hasattr(request, 'rate_limit_headers'):
            for header, value in request.rate_limit_headers.items():
                response[header] = value
        
        return response