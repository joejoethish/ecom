"""
Custom exceptions for the authentication app.

This module defines custom exception classes for authentication-related errors,
providing clear error messages and appropriate HTTP status codes.
"""

from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class AuthenticationException(APIException):
    """Base exception for authentication-related errors."""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Authentication failed.'
    default_code = 'authentication_failed'


class InvalidCredentialsException(AuthenticationException):
    """Raised when user provides invalid login credentials."""
    default_detail = 'Invalid email or password.'
    default_code = 'invalid_credentials'


class AccountNotActivatedException(AuthenticationException):
    """Raised when user tries to login with an inactive account."""
    default_detail = 'Account is not activated. Please check your email for activation instructions.'
    default_code = 'account_not_activated'


class AccountLockedException(AuthenticationException):
    """Raised when user account is locked due to security reasons."""
    default_detail = 'Account is temporarily locked. Please try again later or contact support.'
    default_code = 'account_locked'


class TokenExpiredException(AuthenticationException):
    """Raised when JWT token has expired."""
    default_detail = 'Token has expired. Please login again.'
    default_code = 'token_expired'


class InvalidTokenException(AuthenticationException):
    """Raised when JWT token is invalid or malformed."""
    default_detail = 'Invalid token provided.'
    default_code = 'invalid_token'


class EmailAlreadyExistsException(ValidationError):
    """Raised when trying to register with an email that already exists."""
    def __init__(self):
        super().__init__({
            'email': ['A user with this email already exists.']
        })


class WeakPasswordException(ValidationError):
    """Raised when password doesn't meet security requirements."""
    def __init__(self, message="Password doesn't meet security requirements."):
        super().__init__({
            'password': [message]
        })


class PasswordMismatchException(ValidationError):
    """Raised when password confirmation doesn't match."""
    def __init__(self):
        super().__init__({
            'password_confirm': ['Password confirmation does not match.']
        })


class EmailVerificationException(APIException):
    """Base exception for email verification errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Email verification failed.'
    default_code = 'email_verification_failed'


class InvalidVerificationTokenException(EmailVerificationException):
    """Raised when email verification token is invalid."""
    default_detail = 'Invalid or expired verification token.'
    default_code = 'invalid_verification_token'


class EmailAlreadyVerifiedException(EmailVerificationException):
    """Raised when trying to verify an already verified email."""
    default_detail = 'Email is already verified.'
    default_code = 'email_already_verified'


class PasswordResetException(APIException):
    """Base exception for password reset errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Password reset failed.'
    default_code = 'password_reset_failed'


class InvalidPasswordResetTokenException(PasswordResetException):
    """Raised when password reset token is invalid."""
    default_detail = 'Invalid or expired password reset token.'
    default_code = 'invalid_reset_token'


class UserNotFoundException(APIException):
    """Raised when user is not found."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'User not found.'
    default_code = 'user_not_found'


class PermissionDeniedException(APIException):
    """Raised when user doesn't have required permissions."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'permission_denied'


class RateLimitExceededException(APIException):
    """Raised when rate limit is exceeded."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Too many requests. Please try again later.'
    default_code = 'rate_limit_exceeded'
    
    def __init__(self, retry_after=None, limit=None, window=None):
        super().__init__()
        self.retry_after = retry_after
        self.limit = limit
        self.window = window
        
        if retry_after:
            self.detail = f'Too many requests. Please try again in {retry_after} seconds.'


class TwoFactorAuthenticationException(APIException):
    """Base exception for 2FA-related errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Two-factor authentication error.'
    default_code = 'two_factor_auth_error'


class Invalid2FACodeException(TwoFactorAuthenticationException):
    """Raised when 2FA code is invalid."""
    default_detail = 'Invalid two-factor authentication code.'
    default_code = 'invalid_2fa_code'


class TwoFactorRequiredException(AuthenticationException):
    """Raised when 2FA is required but not provided."""
    default_detail = 'Two-factor authentication is required.'
    default_code = 'two_factor_required'


class SessionExpiredException(AuthenticationException):
    """Raised when user session has expired."""
    default_detail = 'Session has expired. Please login again.'
    default_code = 'session_expired'


class ConcurrentLoginException(AuthenticationException):
    """Raised when concurrent login limit is exceeded."""
    default_detail = 'Maximum number of concurrent sessions reached.'
    default_code = 'concurrent_login_limit'


class SuspiciousActivityException(APIException):
    """Raised when suspicious activity is detected."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Suspicious activity detected. Account temporarily restricted.'
    default_code = 'suspicious_activity'


class ProfileIncompleteException(APIException):
    """Raised when user profile is incomplete for certain actions."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Profile information is incomplete. Please update your profile.'
    default_code = 'profile_incomplete'


class EmailChangeException(APIException):
    """Base exception for email change errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Email change failed.'
    default_code = 'email_change_failed'


class InvalidEmailChangeTokenException(EmailChangeException):
    """Raised when email change token is invalid."""
    default_detail = 'Invalid or expired email change token.'
    default_code = 'invalid_email_change_token'


# Enhanced Security Exceptions

class SecurityViolationException(APIException):
    """Base exception for security violations."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Security violation detected.'
    default_code = 'security_violation'


class BruteForceDetectedException(SecurityViolationException):
    """Raised when brute force attack is detected."""
    default_detail = 'Multiple failed login attempts detected. Account temporarily locked.'
    default_code = 'brute_force_detected'
    
    def __init__(self, lockout_duration=None):
        super().__init__()
        self.lockout_duration = lockout_duration
        if lockout_duration:
            self.detail = f'Account locked for {lockout_duration} minutes due to multiple failed attempts.'


class IPBlockedException(SecurityViolationException):
    """Raised when IP address is blocked."""
    default_detail = 'Your IP address has been temporarily blocked.'
    default_code = 'ip_blocked'


class SuspiciousLocationException(SecurityViolationException):
    """Raised when login from suspicious location is detected."""
    default_detail = 'Login from unusual location detected. Additional verification required.'
    default_code = 'suspicious_location'


class DeviceFingerprintMismatchException(SecurityViolationException):
    """Raised when device fingerprint doesn't match."""
    default_detail = 'Device verification failed. Please verify your identity.'
    default_code = 'device_mismatch'


class TokenReplayAttackException(SecurityViolationException):
    """Raised when token replay attack is detected."""
    default_detail = 'Token has already been used. Possible replay attack detected.'
    default_code = 'token_replay'


class CSRFTokenMissingException(SecurityViolationException):
    """Raised when CSRF token is missing."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'CSRF token missing or invalid.'
    default_code = 'csrf_token_missing'


class CSRFTokenInvalidException(SecurityViolationException):
    """Raised when CSRF token is invalid."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'CSRF token validation failed.'
    default_code = 'csrf_token_invalid'


# Enhanced Rate Limiting Exceptions

class LoginRateLimitExceededException(RateLimitExceededException):
    """Raised when login rate limit is exceeded."""
    default_detail = 'Too many login attempts. Please try again later.'
    default_code = 'login_rate_limit_exceeded'


class PasswordResetRateLimitExceededException(RateLimitExceededException):
    """Raised when password reset rate limit is exceeded."""
    default_detail = 'Too many password reset requests. Please try again later.'
    default_code = 'password_reset_rate_limit_exceeded'


class EmailVerificationRateLimitExceededException(RateLimitExceededException):
    """Raised when email verification rate limit is exceeded."""
    default_detail = 'Too many verification emails sent. Please try again later.'
    default_code = 'email_verification_rate_limit_exceeded'


class RegistrationRateLimitExceededException(RateLimitExceededException):
    """Raised when registration rate limit is exceeded."""
    default_detail = 'Too many registration attempts. Please try again later.'
    default_code = 'registration_rate_limit_exceeded'


# Enhanced Validation Exceptions

class EmailFormatException(ValidationError):
    """Raised when email format is invalid."""
    def __init__(self):
        super().__init__({
            'email': ['Please enter a valid email address.']
        })


class UsernameFormatException(ValidationError):
    """Raised when username format is invalid."""
    def __init__(self, message="Username must be 3-30 characters and contain only letters, numbers, and underscores."):
        super().__init__({
            'username': [message]
        })


class PasswordComplexityException(ValidationError):
    """Raised when password doesn't meet complexity requirements."""
    def __init__(self, missing_requirements=None):
        if missing_requirements:
            message = f"Password must contain: {', '.join(missing_requirements)}"
        else:
            message = "Password doesn't meet complexity requirements."
        super().__init__({
            'password': [message]
        })


class PasswordHistoryException(ValidationError):
    """Raised when password was recently used."""
    def __init__(self):
        super().__init__({
            'password': ['This password was recently used. Please choose a different password.']
        })


class PasswordExpiredException(AuthenticationException):
    """Raised when password has expired."""
    default_detail = 'Your password has expired. Please reset your password.'
    default_code = 'password_expired'


# Enhanced Token Exceptions

class TokenBlacklistedException(AuthenticationException):
    """Raised when token is blacklisted."""
    default_detail = 'Token has been revoked.'
    default_code = 'token_blacklisted'


class TokenMalformedException(AuthenticationException):
    """Raised when token format is invalid."""
    default_detail = 'Token format is invalid.'
    default_code = 'token_malformed'


class RefreshTokenExpiredException(AuthenticationException):
    """Raised when refresh token has expired."""
    default_detail = 'Refresh token has expired. Please login again.'
    default_code = 'refresh_token_expired'


class TokenSignatureInvalidException(AuthenticationException):
    """Raised when token signature is invalid."""
    default_detail = 'Token signature verification failed.'
    default_code = 'token_signature_invalid'


# Structured Error Response Format

class AuthErrorResponse:
    """Structured error response format for authentication errors."""
    
    def __init__(self, error_code: str, message: str, details=None, status_code=400, 
                 field_errors=None, retry_after=None, timestamp=None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        self.field_errors = field_errors or {}
        self.retry_after = retry_after
        self.timestamp = timestamp or timezone.now().isoformat()
    
    def to_dict(self):
        """Convert error response to dictionary format."""
        response = {
            'success': False,
            'error': {
                'code': self.error_code,
                'message': self.message,
                'timestamp': self.timestamp
            }
        }
        
        if self.details:
            response['error']['details'] = self.details
        
        if self.field_errors:
            response['error']['field_errors'] = self.field_errors
        
        if self.retry_after:
            response['error']['retry_after'] = self.retry_after
        
        return response
    
    @classmethod
    def from_exception(cls, exception):
        """Create error response from exception instance."""
        error_code = getattr(exception, 'default_code', 'unknown_error')
        message = str(exception)
        status_code = getattr(exception, 'status_code', 400)
        
        # Handle specific exception types
        if isinstance(exception, RateLimitExceededException):
            retry_after = getattr(exception, 'retry_after', None)
            return cls(
                error_code=error_code,
                message=message,
                status_code=status_code,
                retry_after=retry_after
            )
        
        if isinstance(exception, ValidationError):
            field_errors = {}
            if hasattr(exception, 'detail') and isinstance(exception.detail, dict):
                field_errors = exception.detail
            return cls(
                error_code=error_code,
                message=message,
                status_code=status_code,
                field_errors=field_errors
            )
        
        return cls(
            error_code=error_code,
            message=message,
            status_code=status_code
        )


# Enhanced Utility Functions

def handle_authentication_error(error_type: str, **kwargs):
    """
    Factory function to create appropriate authentication exceptions.
    
    Args:
        error_type: Type of error to create
        **kwargs: Additional parameters for the exception
    
    Returns:
        Appropriate exception instance
    """
    error_map = {
        # Basic authentication errors
        'invalid_credentials': InvalidCredentialsException,
        'account_not_activated': AccountNotActivatedException,
        'account_locked': AccountLockedException,
        'token_expired': TokenExpiredException,
        'invalid_token': InvalidTokenException,
        'email_exists': EmailAlreadyExistsException,
        'weak_password': WeakPasswordException,
        'password_mismatch': PasswordMismatchException,
        'user_not_found': UserNotFoundException,
        'permission_denied': PermissionDeniedException,
        'session_expired': SessionExpiredException,
        'suspicious_activity': SuspiciousActivityException,
        
        # Rate limiting errors
        'rate_limit_exceeded': RateLimitExceededException,
        'login_rate_limit_exceeded': LoginRateLimitExceededException,
        'password_reset_rate_limit_exceeded': PasswordResetRateLimitExceededException,
        'email_verification_rate_limit_exceeded': EmailVerificationRateLimitExceededException,
        'registration_rate_limit_exceeded': RegistrationRateLimitExceededException,
        
        # Security violations
        'brute_force_detected': BruteForceDetectedException,
        'ip_blocked': IPBlockedException,
        'suspicious_location': SuspiciousLocationException,
        'device_mismatch': DeviceFingerprintMismatchException,
        'token_replay': TokenReplayAttackException,
        'csrf_token_missing': CSRFTokenMissingException,
        'csrf_token_invalid': CSRFTokenInvalidException,
        
        # Token errors
        'token_blacklisted': TokenBlacklistedException,
        'token_malformed': TokenMalformedException,
        'refresh_token_expired': RefreshTokenExpiredException,
        'token_signature_invalid': TokenSignatureInvalidException,
        
        # Password errors
        'password_expired': PasswordExpiredException,
        'password_history': PasswordHistoryException,
        'password_complexity': PasswordComplexityException,
        
        # Email verification errors
        'invalid_verification_token': InvalidVerificationTokenException,
        'email_already_verified': EmailAlreadyVerifiedException,
        
        # Password reset errors
        'invalid_reset_token': InvalidPasswordResetTokenException,
    }
    
    exception_class = error_map.get(error_type, AuthenticationException)
    
    # Handle special cases with parameters
    if error_type == 'weak_password' and 'message' in kwargs:
        return exception_class(kwargs['message'])
    elif error_type == 'brute_force_detected' and 'lockout_duration' in kwargs:
        return exception_class(kwargs['lockout_duration'])
    elif error_type in ['rate_limit_exceeded', 'login_rate_limit_exceeded', 
                        'password_reset_rate_limit_exceeded', 'email_verification_rate_limit_exceeded',
                        'registration_rate_limit_exceeded']:
        return exception_class(
            retry_after=kwargs.get('retry_after'),
            limit=kwargs.get('limit'),
            window=kwargs.get('window')
        )
    elif error_type == 'password_complexity' and 'missing_requirements' in kwargs:
        return exception_class(kwargs['missing_requirements'])
    
    return exception_class()


def validate_password_strength(password: str, user=None) -> None:
    """
    Enhanced password strength validation with comprehensive checks.
    
    Args:
        password: Password to validate
        user: User instance for additional validation (optional)
        
    Raises:
        PasswordComplexityException: If password doesn't meet requirements
        PasswordHistoryException: If password was recently used
    """
    missing_requirements = []
    
    # Length check
    if len(password) < 8:
        missing_requirements.append("at least 8 characters")
    
    # Character type checks
    if not any(c.isupper() for c in password):
        missing_requirements.append("at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        missing_requirements.append("at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        missing_requirements.append("at least one number")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?~`" for c in password):
        missing_requirements.append("at least one special character")
    
    # Common password patterns check
    common_patterns = [
        'password', '123456', 'qwerty', 'abc123', 'admin', 'letmein',
        'welcome', 'monkey', '1234567890', 'password123'
    ]
    
    if password.lower() in common_patterns:
        missing_requirements.append("not a common password")
    
    # Sequential characters check (4+ in a row)
    if _has_sequential_chars(password):
        missing_requirements.append("no long sequential characters (abcd, 1234)")
    
    # Repeated characters check
    if _has_repeated_chars(password):
        missing_requirements.append("no more than 2 repeated characters")
    
    # User-specific checks
    if user:
        # Check against user information
        user_info = [
            getattr(user, 'username', '').lower(),
            getattr(user, 'email', '').split('@')[0].lower(),
            getattr(user, 'first_name', '').lower(),
            getattr(user, 'last_name', '').lower(),
        ]
        
        for info in user_info:
            if info and len(info) > 2 and info in password.lower():
                missing_requirements.append("not contain personal information")
                break
    
    if missing_requirements:
        raise PasswordComplexityException(missing_requirements)


def _has_sequential_chars(password: str, min_length: int = 4) -> bool:
    """Check if password contains sequential characters (4+ in a row)."""
    password_lower = password.lower()
    
    # Check for alphabetical sequences (4+ characters)
    for i in range(len(password_lower) - min_length + 1):
        sequence = password_lower[i:i + min_length]
        if all(ord(sequence[j]) == ord(sequence[0]) + j for j in range(len(sequence))):
            return True
    
    # Check for numerical sequences (4+ characters)
    for i in range(len(password) - min_length + 1):
        sequence = password[i:i + min_length]
        if sequence.isdigit():
            if all(int(sequence[j]) == int(sequence[0]) + j for j in range(len(sequence))):
                return True
    
    return False


def _has_repeated_chars(password: str, max_repeats: int = 2) -> bool:
    """Check if password has too many repeated characters."""
    char_count = {}
    for char in password:
        char_count[char] = char_count.get(char, 0) + 1
        if char_count[char] > max_repeats:
            return True
    return False


def validate_email_format(email: str) -> None:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Raises:
        EmailFormatException: If email format is invalid
    """
    import re
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not email or not re.match(email_pattern, email):
        raise EmailFormatException()
    
    # Additional checks
    if len(email) > 254:  # RFC 5321 limit
        raise EmailFormatException()
    
    local_part, domain = email.rsplit('@', 1)
    if len(local_part) > 64:  # RFC 5321 limit
        raise EmailFormatException()


def validate_username_format(username: str) -> None:
    """
    Validate username format.
    
    Args:
        username: Username to validate
        
    Raises:
        UsernameFormatException: If username format is invalid
    """
    import re
    
    if not username:
        raise UsernameFormatException("Username is required.")
    
    if len(username) < 3:
        raise UsernameFormatException("Username must be at least 3 characters long.")
    
    if len(username) > 30:
        raise UsernameFormatException("Username must be no more than 30 characters long.")
    
    # Allow letters, numbers, underscores, and hyphens
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise UsernameFormatException(
            "Username can only contain letters, numbers, underscores, and hyphens."
        )
    
    # Must start with a letter or number
    if not re.match(r'^[a-zA-Z0-9]', username):
        raise UsernameFormatException("Username must start with a letter or number.")
    
    # Reserved usernames
    reserved_usernames = [
        'admin', 'administrator', 'root', 'system', 'api', 'www', 'mail',
        'support', 'help', 'info', 'contact', 'service', 'test', 'demo'
    ]
    
    if username.lower() in reserved_usernames:
        raise UsernameFormatException("This username is reserved and cannot be used.")


def check_user_permissions(user, required_permission: str) -> None:
    """
    Check if user has required permissions.
    
    Args:
        user: User instance
        required_permission: Permission string to check
        
    Raises:
        PermissionDeniedException: If user doesn't have permission
    """
    if not user.has_perm(required_permission):
        raise PermissionDeniedException(
            f"User does not have '{required_permission}' permission."
        )


def validate_user_status(user) -> None:
    """
    Enhanced user account status validation for authentication.
    
    Args:
        user: User instance
        
    Raises:
        AccountNotActivatedException: If account is not active
        AccountLockedException: If account is locked
        PasswordExpiredException: If password has expired
        EmailNotVerifiedException: If email verification is required
    """
    if not user.is_active:
        raise AccountNotActivatedException()
    
    # Check if user is locked
    if hasattr(user, 'is_locked') and user.is_locked:
        raise AccountLockedException()
    
    # Check if account is locked due to failed attempts
    if hasattr(user, 'account_locked_until') and user.account_locked_until:
        if timezone.now() < user.account_locked_until:
            remaining_time = (user.account_locked_until - timezone.now()).total_seconds() / 60
            raise BruteForceDetectedException(lockout_duration=int(remaining_time))
    
    # Check password expiration (if implemented)
    if hasattr(user, 'password_expires_at') and user.password_expires_at:
        if timezone.now() > user.password_expires_at:
            raise PasswordExpiredException()
    
    # Check email verification requirement
    if hasattr(user, 'is_email_verified') and not user.is_email_verified:
        # Allow some grace period or check if verification is required for this action
        if getattr(user, 'email_verification_required', True):
            raise EmailNotVerifiedException()


def check_rate_limit(identifier: str, action: str, limit: int, window: int) -> None:
    """
    Generic rate limiting function.
    
    Args:
        identifier: Unique identifier (IP, user ID, etc.)
        action: Action being rate limited
        limit: Maximum number of requests
        window: Time window in seconds
        
    Raises:
        RateLimitExceededException: If rate limit is exceeded
    """
    from django.core.cache import cache
    import time
    
    cache_key = f"rate_limit:{action}:{identifier}"
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
        
        # Log rate limit violation
        logger.warning(
            f"Rate limit exceeded for {action}. "
            f"Identifier: {identifier}, "
            f"Requests: {len(request_times)}/{limit}"
        )
        
        raise RateLimitExceededException(
            retry_after=retry_after,
            limit=limit,
            window=window
        )
    
    # Add current request timestamp
    request_times.append(current_time)
    cache.set(cache_key, request_times, window)


def check_login_rate_limit(identifier: str) -> None:
    """Check rate limit for login attempts."""
    check_rate_limit(identifier, 'login', limit=5, window=900)  # 5 attempts per 15 minutes


def check_password_reset_rate_limit(identifier: str) -> None:
    """Check rate limit for password reset requests."""
    check_rate_limit(identifier, 'password_reset', limit=5, window=3600)  # 5 attempts per hour


def check_email_verification_rate_limit(identifier: str) -> None:
    """Check rate limit for email verification requests."""
    check_rate_limit(identifier, 'email_verification', limit=3, window=3600)  # 3 attempts per hour


def check_registration_rate_limit(identifier: str) -> None:
    """Check rate limit for registration attempts."""
    check_rate_limit(identifier, 'registration', limit=10, window=3600)  # 10 attempts per hour


def detect_brute_force_attack(user, ip_address: str) -> None:
    """
    Detect and handle brute force attacks.
    
    Args:
        user: User instance
        ip_address: Client IP address
        
    Raises:
        BruteForceDetectedException: If brute force attack is detected
    """
    from django.core.cache import cache
    
    # Track failed attempts per user
    user_key = f"failed_attempts:user:{user.id if user else 'unknown'}"
    ip_key = f"failed_attempts:ip:{ip_address}"
    
    user_attempts = cache.get(user_key, 0)
    ip_attempts = cache.get(ip_key, 0)
    
    # Increment counters
    cache.set(user_key, user_attempts + 1, 3600)  # 1 hour
    cache.set(ip_key, ip_attempts + 1, 3600)  # 1 hour
    
    # Check thresholds
    if user_attempts >= 5 or ip_attempts >= 10:
        # Lock user account if applicable
        if user and hasattr(user, 'account_locked_until'):
            user.account_locked_until = timezone.now() + timedelta(minutes=30)
            user.save(update_fields=['account_locked_until'])
        
        logger.warning(
            f"Brute force attack detected. User: {user.id if user else 'unknown'}, "
            f"IP: {ip_address}, User attempts: {user_attempts}, IP attempts: {ip_attempts}"
        )
        
        raise BruteForceDetectedException(lockout_duration=30)


def validate_csrf_token(request) -> None:
    """
    Validate CSRF token for sensitive operations.
    
    Args:
        request: Django request object
        
    Raises:
        CSRFTokenMissingException: If CSRF token is missing
        CSRFTokenInvalidException: If CSRF token is invalid
    """
    from django.middleware.csrf import get_token
    from django.views.decorators.csrf import _get_token
    
    # Get CSRF token from request
    csrf_token = request.META.get('HTTP_X_CSRFTOKEN') or request.POST.get('csrfmiddlewaretoken')
    
    if not csrf_token:
        raise CSRFTokenMissingException()
    
    # Validate token
    expected_token = get_token(request)
    if csrf_token != expected_token:
        raise CSRFTokenInvalidException()


def log_security_event(event_type: str, user=None, ip_address: str = None, 
                      details: dict = None) -> None:
    """
    Log security events for monitoring and analysis.
    
    Args:
        event_type: Type of security event
        user: User instance (optional)
        ip_address: Client IP address (optional)
        details: Additional event details (optional)
    """
    log_data = {
        'security_event_type': event_type,
        'security_timestamp': timezone.now().isoformat(),
        'security_user_id': user.id if user else None,
        'security_username': user.username if user else None,
        'security_ip_address': ip_address,
        'security_details': details or {}
    }
    
    logger.warning(f"Security Event: {event_type}", extra=log_data)


def create_structured_error_response(exception, request=None):
    """
    Create a structured error response from an exception.
    
    Args:
        exception: Exception instance
        request: Django request object (optional)
        
    Returns:
        Dictionary containing structured error response
    """
    error_response = AuthErrorResponse.from_exception(exception)
    
    # Add request context if available
    if request:
        error_response.details.update({
            'path': request.path,
            'method': request.method,
            'timestamp': timezone.now().isoformat()
        })
    
    # Log the error with prefixed keys to avoid conflicts
    logger.error(
        f"Authentication error: {error_response.error_code}",
        extra={
            'auth_error_code': error_response.error_code,
            'auth_error_message': error_response.message,
            'auth_status_code': error_response.status_code,
            'auth_error_details': error_response.details
        }
    )
    
    return error_response.to_dict()