"""
Authentication middleware for security and rate limiting.
"""
import time
import hashlib
import json
from django.http import JsonResponse
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import PasswordResetAttempt, EmailVerificationAttempt

logger = logging.getLogger(__name__)
User = get_user_model()


class AuthenticationRateLimitMiddleware:
    """
    Comprehensive rate limiting middleware for all authentication endpoints.
    Requirements: 1.1, 1.2, 2.1, 2.2 - Implement rate limiting for authentication endpoints
    """
    
    # Rate limiting configuration for different endpoint types
    RATE_LIMITS = {
        'login': {'requests': 5, 'window': 900},  # 5 attempts per 15 minutes
        'register': {'requests': 10, 'window': 3600},  # 10 registrations per hour
        'password_reset': {'requests': 5, 'window': 3600},  # 5 requests per hour
        'email_verification': {'requests': 3, 'window': 3600},  # 3 requests per hour
        'admin_login': {'requests': 3, 'window': 900},  # 3 attempts per 15 minutes (stricter)
        'refresh_token': {'requests': 20, 'window': 3600},  # 20 refreshes per hour
    }
    
    # Endpoints mapping to rate limit types
    ENDPOINT_MAPPING = {
        '/api/v1/auth/login/': 'login',
        '/api/v1/auth/register/': 'register',
        '/api/v1/auth/password-reset/request/': 'password_reset',
        '/api/v1/auth/password-reset/confirm/': 'password_reset',
        '/api/v1/auth/verify-email/': 'email_verification',
        '/api/v1/auth/resend-verification/': 'email_verification',
        '/api/v1/admin-auth/login/': 'admin_login',
        '/api/v1/auth/refresh/': 'refresh_token',
        '/api/v1/admin-auth/refresh/': 'refresh_token',
        # Legacy endpoints
        '/api/v1/auth/forgot-password/': 'password_reset',
        '/api/v1/auth/reset-password/': 'password_reset',
    }
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this endpoint should be rate limited
        endpoint_type = self._get_endpoint_type(request)
        if endpoint_type:
            # Check rate limit before processing request
            rate_limit_response = self._check_rate_limit(request, endpoint_type)
            if rate_limit_response:
                # Log the rate limit violation
                self._log_rate_limit_violation(request, endpoint_type)
                return rate_limit_response
        
        response = self.get_response(request)
        
        # Add rate limit headers to successful responses
        if endpoint_type and hasattr(request, 'rate_limit_headers'):
            for header, value in request.rate_limit_headers.items():
                response[header] = value
        
        return response

    def _get_endpoint_type(self, request):
        """Get the endpoint type for rate limiting."""
        path = request.path_info
        method = request.method
        
        # Only rate limit specific HTTP methods
        if method not in ['POST', 'GET']:
            return None
        
        # Check for exact path matches
        if path in self.ENDPOINT_MAPPING:
            return self.ENDPOINT_MAPPING[path]
        
        # Check for pattern matches (e.g., verify-email with token)
        for endpoint_path, endpoint_type in self.ENDPOINT_MAPPING.items():
            if path.startswith(endpoint_path.rstrip('/')):
                return endpoint_type
        
        return None

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

    def _get_cache_key(self, request, endpoint_type):
        """Generate cache key for rate limiting."""
        client_id = self._get_client_identifier(request)
        return f"rate_limit:auth:{endpoint_type}:{client_id}"

    def _check_rate_limit(self, request, endpoint_type):
        """
        Check if the request should be rate limited.
        Returns JsonResponse if rate limited, None otherwise.
        """
        try:
            rate_config = self.RATE_LIMITS[endpoint_type]
            cache_key = self._get_cache_key(request, endpoint_type)
            current_time = int(time.time())
            
            # Get current request timestamps from cache
            request_times = cache.get(cache_key, [])
            
            # Remove timestamps outside the current window
            window_start = current_time - rate_config['window']
            request_times = [t for t in request_times if t > window_start]
            
            # Check if rate limit exceeded
            if len(request_times) >= rate_config['requests']:
                # Calculate when the rate limit will reset
                oldest_request = min(request_times)
                reset_time = oldest_request + rate_config['window']
                retry_after = reset_time - current_time
                
                return JsonResponse({
                    'success': False,
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': f'Too many {endpoint_type} requests. Please try again in {retry_after} seconds.',
                        'retry_after': retry_after,
                        'endpoint_type': endpoint_type
                    }
                }, status=429, headers={
                    'Retry-After': str(retry_after),
                    'X-RateLimit-Limit': str(rate_config['requests']),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(reset_time),
                    'X-RateLimit-Type': endpoint_type
                })
            
            # Add current request timestamp
            request_times.append(current_time)
            
            # Update cache with new timestamps
            cache.set(cache_key, request_times, rate_config['window'])
            
            # Add rate limit headers to successful requests
            remaining = rate_config['requests'] - len(request_times)
            request.rate_limit_headers = {
                'X-RateLimit-Limit': str(rate_config['requests']),
                'X-RateLimit-Remaining': str(remaining),
                'X-RateLimit-Reset': str(current_time + rate_config['window']),
                'X-RateLimit-Type': endpoint_type
            }
            
            return None  # No rate limiting
            
        except Exception as e:
            logger.error(f"Rate limiting check failed for {endpoint_type}: {str(e)}")
            # In case of error, allow the request but log it
            return None

    def _get_client_ip(self, request):
        """Get client IP address for logging."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    def _log_rate_limit_violation(self, request, endpoint_type):
        """Log rate limit violations for security monitoring."""
        client_ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        logger.warning(
            f"Rate limit exceeded for {endpoint_type} endpoint. "
            f"IP: {client_ip}, Path: {request.path_info}, "
            f"User-Agent: {user_agent[:100]}..."
        )
        
        # Store attempt in database for analysis
        try:
            if endpoint_type == 'password_reset':
                email = self._extract_email_from_request(request)
                if email:
                    PasswordResetAttempt.objects.create(
                        ip_address=client_ip,
                        email=email,
                        success=False,
                        user_agent=user_agent
                    )
            elif endpoint_type == 'email_verification':
                email = self._extract_email_from_request(request)
                if email:
                    EmailVerificationAttempt.objects.create(
                        ip_address=client_ip,
                        email=email,
                        success=False,
                        user_agent=user_agent
                    )
        except Exception as e:
            logger.error(f"Failed to log rate limit attempt: {str(e)}")

    def _extract_email_from_request(self, request):
        """Extract email from request body for logging."""
        try:
            if hasattr(request, 'body') and request.body:
                if request.content_type == 'application/json':
                    data = json.loads(request.body.decode('utf-8'))
                    return data.get('email', '')
                elif request.content_type == 'application/x-www-form-urlencoded':
                    return request.POST.get('email', '')
        except Exception:
            pass
        return ''


class AccountLockoutMiddleware:
    """
    Account lockout middleware for failed login attempts.
    Requirements: 1.1, 1.2, 2.1, 2.2 - Create account lockout functionality for failed attempts
    """
    
    # Lockout configuration
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    
    # Login endpoints that trigger lockout checks
    LOGIN_ENDPOINTS = [
        '/api/v1/auth/login/',
        '/api/v1/admin-auth/login/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check for account lockout before processing login requests
        if self._is_login_endpoint(request):
            lockout_response = self._check_account_lockout(request)
            if lockout_response:
                return lockout_response
        
        response = self.get_response(request)
        
        # Handle failed login attempts after processing
        if self._is_login_endpoint(request) and response.status_code in [400, 401]:
            self._handle_failed_login(request, response)
        elif self._is_login_endpoint(request) and response.status_code == 200:
            self._handle_successful_login(request)
        
        return response

    def _is_login_endpoint(self, request):
        """Check if this is a login endpoint."""
        return (request.method == 'POST' and 
                any(request.path_info.startswith(endpoint) for endpoint in self.LOGIN_ENDPOINTS))

    def _check_account_lockout(self, request):
        """Check if account is locked and return appropriate response."""
        try:
            email = self._extract_email_from_request(request)
            if not email:
                return None
            
            try:
                user = User.objects.get(email=email)
                if user.is_account_locked:
                    # Calculate remaining lockout time
                    remaining_time = (user.account_locked_until - timezone.now()).total_seconds()
                    if remaining_time > 0:
                        logger.warning(f"Login attempt on locked account: {email} from IP: {self._get_client_ip(request)}")
                        
                        return JsonResponse({
                            'success': False,
                            'error': {
                                'code': 'ACCOUNT_LOCKED',
                                'message': f'Account is temporarily locked. Try again in {int(remaining_time/60)} minutes.',
                                'locked_until': user.account_locked_until.isoformat(),
                                'remaining_seconds': int(remaining_time)
                            }
                        }, status=423)  # 423 Locked
                    else:
                        # Lockout period expired, unlock account
                        user.unlock_account()
            except User.DoesNotExist:
                # Don't reveal if email exists or not
                pass
                
        except Exception as e:
            logger.error(f"Account lockout check failed: {str(e)}")
        
        return None

    def _handle_failed_login(self, request, response):
        """Handle failed login attempts and implement lockout logic."""
        try:
            email = self._extract_email_from_request(request)
            if not email:
                return
            
            client_ip = self._get_client_ip(request)
            
            try:
                user = User.objects.get(email=email)
                
                # Increment failed attempts
                user.increment_failed_login()
                
                logger.warning(
                    f"Failed login attempt #{user.failed_login_attempts} for {email} "
                    f"from IP: {client_ip}"
                )
                
                # If account was just locked, update the response
                if user.is_account_locked:
                    remaining_time = (user.account_locked_until - timezone.now()).total_seconds()
                    logger.critical(
                        f"Account locked due to {self.MAX_FAILED_ATTEMPTS} failed attempts: "
                        f"{email} from IP: {client_ip}"
                    )
                    
                    # Update response to indicate account lockout
                    if hasattr(response, '_container'):
                        try:
                            response_data = json.loads(b''.join(response._container).decode('utf-8'))
                            response_data['error'] = {
                                'code': 'ACCOUNT_LOCKED',
                                'message': f'Account locked due to too many failed attempts. Try again in {int(remaining_time/60)} minutes.',
                                'locked_until': user.account_locked_until.isoformat(),
                                'remaining_seconds': int(remaining_time)
                            }
                            response._container = [json.dumps(response_data).encode('utf-8')]
                            response.status_code = 423
                        except Exception:
                            pass
                            
            except User.DoesNotExist:
                # Log suspicious activity for non-existent emails
                logger.warning(f"Login attempt with non-existent email: {email} from IP: {client_ip}")
                
        except Exception as e:
            logger.error(f"Failed login handling error: {str(e)}")

    def _handle_successful_login(self, request):
        """Handle successful login - reset failed attempts."""
        try:
            email = self._extract_email_from_request(request)
            if not email:
                return
            
            try:
                user = User.objects.get(email=email)
                if user.failed_login_attempts > 0:
                    user.reset_failed_login()
                    logger.info(f"Reset failed login attempts for {email}")
            except User.DoesNotExist:
                pass
                
        except Exception as e:
            logger.error(f"Successful login handling error: {str(e)}")

    def _extract_email_from_request(self, request):
        """Extract email from request body."""
        try:
            if hasattr(request, 'body') and request.body:
                if request.content_type == 'application/json':
                    data = json.loads(request.body.decode('utf-8'))
                    return data.get('email', '')
                elif request.content_type == 'application/x-www-form-urlencoded':
                    return request.POST.get('email', '')
        except Exception:
            pass
        return ''

    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


class IPSecurityMonitoringMiddleware:
    """
    IP-based security monitoring and suspicious activity detection.
    Requirements: 1.1, 1.2, 2.1, 2.2 - Add IP-based rate limiting and monitoring
    """
    
    # Suspicious activity thresholds
    SUSPICIOUS_THRESHOLDS = {
        'requests_per_minute': 30,  # More than 30 requests per minute
        'failed_logins_per_hour': 10,  # More than 10 failed logins per hour
        'different_endpoints_per_minute': 10,  # Accessing too many different endpoints
    }
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Monitor request patterns before processing
        self._monitor_request_patterns(request)
        
        response = self.get_response(request)
        
        # Analyze response patterns after processing
        self._analyze_response_patterns(request, response)
        
        return response

    def _monitor_request_patterns(self, request):
        """Monitor incoming request patterns for suspicious activity."""
        try:
            client_ip = self._get_client_ip(request)
            current_time = int(time.time())
            
            # Track requests per minute
            minute_key = f"ip_monitor:requests_per_minute:{client_ip}:{current_time // 60}"
            requests_this_minute = cache.get(minute_key, 0)
            cache.set(minute_key, requests_this_minute + 1, 60)
            
            # Track unique endpoints accessed per minute
            endpoints_key = f"ip_monitor:endpoints_per_minute:{client_ip}:{current_time // 60}"
            endpoints_this_minute = cache.get(endpoints_key, set())
            endpoints_this_minute.add(request.path_info)
            cache.set(endpoints_key, endpoints_this_minute, 60)
            
            # Check for suspicious activity
            if requests_this_minute > self.SUSPICIOUS_THRESHOLDS['requests_per_minute']:
                self._log_suspicious_activity(
                    client_ip, 'HIGH_REQUEST_RATE', 
                    f"IP making {requests_this_minute} requests per minute"
                )
            
            if len(endpoints_this_minute) > self.SUSPICIOUS_THRESHOLDS['different_endpoints_per_minute']:
                self._log_suspicious_activity(
                    client_ip, 'ENDPOINT_SCANNING', 
                    f"IP accessing {len(endpoints_this_minute)} different endpoints per minute"
                )
                
        except Exception as e:
            logger.error(f"Request pattern monitoring failed: {str(e)}")

    def _analyze_response_patterns(self, request, response):
        """Analyze response patterns for security insights."""
        try:
            client_ip = self._get_client_ip(request)
            current_time = int(time.time())
            
            # Track failed authentication attempts per hour
            if (request.path_info.startswith('/api/v1/auth/') and 
                response.status_code in [400, 401, 403]):
                
                hour_key = f"ip_monitor:failed_auth_per_hour:{client_ip}:{current_time // 3600}"
                failed_attempts = cache.get(hour_key, 0)
                cache.set(hour_key, failed_attempts + 1, 3600)
                
                if failed_attempts > self.SUSPICIOUS_THRESHOLDS['failed_logins_per_hour']:
                    self._log_suspicious_activity(
                        client_ip, 'BRUTE_FORCE_ATTEMPT', 
                        f"IP has {failed_attempts} failed authentication attempts in the last hour"
                    )
                    
        except Exception as e:
            logger.error(f"Response pattern analysis failed: {str(e)}")

    def _log_suspicious_activity(self, ip_address, activity_type, description):
        """Log suspicious activity for security monitoring."""
        logger.critical(
            f"SUSPICIOUS ACTIVITY DETECTED - Type: {activity_type}, "
            f"IP: {ip_address}, Description: {description}"
        )
        
        # Store in cache for security dashboard
        suspicious_key = f"security:suspicious_ips:{ip_address}"
        suspicious_data = cache.get(suspicious_key, {})
        
        if activity_type not in suspicious_data:
            suspicious_data[activity_type] = []
        
        suspicious_data[activity_type].append({
            'timestamp': timezone.now().isoformat(),
            'description': description
        })
        
        # Keep only last 24 hours of data
        cache.set(suspicious_key, suspicious_data, 86400)

    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


class CSRFAuthenticationMiddleware:
    """
    Enhanced CSRF protection middleware for all authentication endpoints.
    Requirements: Enhanced CSRF protection for authentication system
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add CSRF headers to authentication endpoints
        if self._is_authentication_endpoint(request):
            self._add_csrf_headers(request, response)
        
        return response

    def _is_authentication_endpoint(self, request):
        """Check if this is an authentication endpoint."""
        auth_paths = [
            '/api/v1/auth/',
            '/api/v1/admin-auth/',
        ]
        return any(request.path_info.startswith(path) for path in auth_paths)

    def _add_csrf_headers(self, request, response):
        """Add CSRF-related security headers."""
        # Add CSRF token to response headers for frontend consumption
        if hasattr(request, 'META') and 'CSRF_COOKIE' in request.META:
            response['X-CSRFToken'] = request.META['CSRF_COOKIE']
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Add CORS headers for authentication endpoints
        if request.method == 'OPTIONS':
            response['Access-Control-Allow-Headers'] = (
                'Accept, Content-Type, Content-Length, Accept-Encoding, '
                'X-CSRF-Token, Authorization, X-Requested-With'
            )
            response['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE, OPTIONS'


class SecurityHeadersMiddleware:
    """
    Enhanced security headers middleware for all authentication responses.
    Requirements: 1.1, 1.2, 2.1, 2.2 - General security enhancement for authentication system
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add comprehensive security headers
        self._add_security_headers(response)
        
        # Add rate limit headers if they were set by rate limiting middleware
        if hasattr(request, 'rate_limit_headers'):
            for header, value in request.rate_limit_headers.items():
                response[header] = value
        
        # Add authentication-specific headers
        if self._is_authentication_endpoint(request):
            self._add_authentication_headers(request, response)
        
        return response

    def _add_security_headers(self, response):
        """Add comprehensive security headers."""
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['X-Permitted-Cross-Domain-Policies'] = 'none'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

    def _add_authentication_headers(self, request, response):
        """Add authentication-specific security headers."""
        # Prevent caching of authentication responses
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
        
        # Add security timestamp
        response['X-Security-Timestamp'] = str(int(time.time()))
        
        # Add request ID for tracking
        if hasattr(request, 'META'):
            request_id = request.META.get('HTTP_X_REQUEST_ID', 
                                        hashlib.md5(f"{time.time()}{request.path}".encode()).hexdigest()[:16])
            response['X-Request-ID'] = request_id

    def _is_authentication_endpoint(self, request):
        """Check if this is an authentication endpoint."""
        auth_paths = [
            '/api/v1/auth/',
            '/api/v1/admin-auth/',
        ]
        return any(request.path_info.startswith(path) for path in auth_paths)