# Authentication Error Handling System Documentation

## Overview

This document describes the comprehensive error handling system implemented for the authentication module as part of Task 9.1. The system provides structured error responses, enhanced security monitoring, and robust rate limiting capabilities.

## Architecture

### Core Components

1. **Custom Exception Classes** (`exceptions.py`)
   - 25+ specialized exception classes for different error scenarios
   - Hierarchical exception structure with base classes
   - Enhanced parameter support for detailed error information

2. **Structured Error Response Format** (`AuthErrorResponse`)
   - Consistent JSON response format across all authentication endpoints
   - Timestamp tracking and error correlation
   - Support for field-specific validation errors

3. **Error Handlers and Middleware** (`error_handlers.py`)
   - Authentication-specific exception handler
   - Security monitoring middleware
   - Rate limiting middleware with sliding window algorithm

4. **Validation Functions**
   - Enhanced password strength validation
   - Email format validation with RFC compliance
   - Username format validation with reserved name checking

## Exception Classes

### Base Exceptions

- `AuthenticationException` - Base for all authentication errors
- `SecurityViolationException` - Base for security-related violations
- `RateLimitExceededException` - Base for rate limiting errors

### Authentication Errors

- `InvalidCredentialsException` - Invalid login credentials
- `AccountNotActivatedException` - Account not activated
- `AccountLockedException` - Account temporarily locked
- `TokenExpiredException` - JWT token expired
- `InvalidTokenException` - Invalid or malformed token
- `SessionExpiredException` - User session expired

### Security Violations

- `BruteForceDetectedException` - Brute force attack detected
- `IPBlockedException` - IP address blocked
- `SuspiciousLocationException` - Login from unusual location
- `DeviceFingerprintMismatchException` - Device verification failed
- `TokenReplayAttackException` - Token replay attack detected
- `CSRFTokenMissingException` - CSRF token missing
- `CSRFTokenInvalidException` - CSRF token invalid

### Rate Limiting Errors

- `LoginRateLimitExceededException` - Login attempts exceeded
- `PasswordResetRateLimitExceededException` - Password reset requests exceeded
- `EmailVerificationRateLimitExceededException` - Email verification requests exceeded
- `RegistrationRateLimitExceededException` - Registration attempts exceeded

### Validation Errors

- `PasswordComplexityException` - Password doesn't meet requirements
- `EmailFormatException` - Invalid email format
- `UsernameFormatException` - Invalid username format
- `PasswordHistoryException` - Password recently used

### Token Errors

- `TokenBlacklistedException` - Token revoked/blacklisted
- `TokenMalformedException` - Token format invalid
- `RefreshTokenExpiredException` - Refresh token expired
- `TokenSignatureInvalidException` - Token signature verification failed

## Error Response Format

### Standard Response Structure

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "timestamp": "2025-01-14T10:30:00Z",
    "details": {
      "additional": "context"
    },
    "field_errors": {
      "field_name": ["Field-specific error message"]
    },
    "retry_after": 60
  }
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVALID_CREDENTIALS` | Invalid login credentials | 401 |
| `ACCOUNT_LOCKED` | Account temporarily locked | 401 |
| `TOKEN_EXPIRED` | JWT token expired | 401 |
| `RATE_LIMIT_EXCEEDED` | Rate limit exceeded | 429 |
| `BRUTE_FORCE_DETECTED` | Brute force attack detected | 403 |
| `CSRF_TOKEN_MISSING` | CSRF token missing | 403 |
| `PASSWORD_COMPLEXITY` | Password doesn't meet requirements | 400 |
| `EMAIL_FORMAT_INVALID` | Invalid email format | 400 |

## Rate Limiting Configuration

### Default Limits

| Endpoint | Limit | Window | Identifier |
|----------|-------|--------|------------|
| `/api/v1/auth/login/` | 5 requests | 15 minutes | IP address |
| `/api/v1/auth/register/` | 3 requests | 1 hour | IP address |
| `/api/v1/auth/forgot-password/` | 5 requests | 1 hour | IP address |
| `/api/v1/auth/reset-password/` | 10 requests | 1 hour | IP address |
| `/api/v1/auth/resend-verification/` | 3 requests | 1 hour | User ID |

### Rate Limit Headers

```http
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 2
X-RateLimit-Reset: 1642176000
Retry-After: 300
```

## Security Features

### Brute Force Protection

- Tracks failed login attempts per user and IP
- Automatic account lockout after 5 failed attempts
- IP-based blocking after 10 failed attempts from same IP
- Configurable lockout duration (default: 30 minutes)

### CSRF Protection

- CSRF token validation for sensitive operations
- Automatic token generation and validation
- Security headers injection

### Security Headers

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Cache-Control: no-store, no-cache, must-revalidate, private
```

## Validation Rules

### Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character
- No common passwords (password, 123456, etc.)
- No long sequential characters (4+ in a row)
- No more than 2 repeated characters
- Cannot contain personal information (username, email, name)

### Email Validation

- RFC 5321 compliant format validation
- Maximum length: 254 characters
- Local part maximum: 64 characters
- Domain validation

### Username Validation

- Length: 3-30 characters
- Allowed characters: letters, numbers, underscores, hyphens
- Must start with letter or number
- Reserved usernames blocked (admin, root, etc.)

## Usage Examples

### Exception Handling in Views

```python
from apps.authentication.exceptions import (
    handle_authentication_error, create_structured_error_response
)

def login_view(request):
    try:
        # Authentication logic
        pass
    except Exception as e:
        # Create structured error response
        error_response = create_structured_error_response(e, request)
        return Response(error_response, status=400)
```

### Rate Limiting

```python
from apps.authentication.exceptions import check_login_rate_limit

def login_view(request):
    try:
        # Check rate limit
        check_login_rate_limit(get_client_ip(request))
        
        # Proceed with login
        pass
    except RateLimitExceededException as e:
        return Response(
            create_structured_error_response(e, request),
            status=429,
            headers={'Retry-After': str(e.retry_after)}
        )
```

### Password Validation

```python
from apps.authentication.exceptions import validate_password_strength

def register_view(request):
    try:
        password = request.data.get('password')
        validate_password_strength(password, user=request.user)
        
        # Proceed with registration
        pass
    except PasswordComplexityException as e:
        return Response(
            create_structured_error_response(e, request),
            status=400
        )
```

## Middleware Configuration

### Django Settings

```python
MIDDLEWARE = [
    # ... other middleware
    'apps.authentication.error_handlers.AuthenticationErrorMiddleware',
    'apps.authentication.error_handlers.RateLimitingMiddleware',
    # ... other middleware
]

# Exception handler configuration
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    # ... other settings
}
```

## Monitoring and Logging

### Security Event Logging

```python
from apps.authentication.exceptions import log_security_event

# Log security events
log_security_event(
    event_type='SUSPICIOUS_LOGIN',
    user=user,
    ip_address='192.168.1.1',
    details={'location': 'Unknown', 'device': 'Mobile'}
)
```

### Log Format

```json
{
  "level": "WARNING",
  "message": "Security Event: SUSPICIOUS_LOGIN",
  "security_event_type": "SUSPICIOUS_LOGIN",
  "security_timestamp": "2025-01-14T10:30:00Z",
  "security_user_id": 123,
  "security_username": "testuser",
  "security_ip_address": "192.168.1.1",
  "security_details": {
    "location": "Unknown",
    "device": "Mobile"
  }
}
```

## Testing

### Running Tests

```bash
# Run authentication error handling tests
python manage.py test apps.authentication.tests.test_error_handling

# Run validation script
python validate_error_handling.py
```

### Test Coverage

- Exception class instantiation and behavior
- Error response format validation
- Password, email, and username validation
- Rate limiting functionality
- Security event logging
- Middleware functionality
- Integration with core exception handler

## Integration Points

### Core Exception Handler

The authentication error handler integrates with the existing core exception handler in `core/exceptions.py`. Authentication-related requests are automatically routed to the specialized handler.

### Frontend Integration

The structured error response format is designed to be easily consumed by frontend applications:

```javascript
// Frontend error handling
if (!response.success) {
  const error = response.error;
  
  // Display general error message
  showError(error.message);
  
  // Handle field-specific errors
  if (error.field_errors) {
    Object.keys(error.field_errors).forEach(field => {
      showFieldError(field, error.field_errors[field][0]);
    });
  }
  
  // Handle rate limiting
  if (error.code === 'RATE_LIMIT_EXCEEDED' && error.retry_after) {
    showRetryMessage(error.retry_after);
  }
}
```

## Performance Considerations

### Caching

- Rate limiting uses Redis cache for performance
- Sliding window algorithm for efficient rate limit tracking
- Automatic cleanup of expired rate limit entries

### Database Impact

- Minimal database queries for error handling
- Security events logged asynchronously where possible
- Efficient indexing on user and IP-based lookups

## Security Considerations

### Information Disclosure

- Error messages designed to prevent information leakage
- Generic responses for user enumeration prevention
- Detailed logging for security monitoring without exposing sensitive data

### Attack Mitigation

- Rate limiting prevents brute force attacks
- Account lockout mechanisms
- IP-based blocking for persistent attackers
- CSRF protection for state-changing operations

## Maintenance

### Adding New Exceptions

1. Create exception class in `exceptions.py`
2. Add to exception factory function
3. Update error handler if needed
4. Add tests for new exception
5. Update documentation

### Modifying Rate Limits

1. Update `RATE_LIMITS` configuration in middleware
2. Test new limits
3. Update documentation
4. Monitor impact on legitimate users

## Troubleshooting

### Common Issues

1. **Rate limit false positives**: Check cache configuration and time synchronization
2. **Missing error details**: Ensure proper exception instantiation with parameters
3. **Logging conflicts**: Use prefixed keys in log extra data
4. **Middleware order**: Ensure authentication middleware is properly ordered

### Debug Mode

Enable debug logging for detailed error handling information:

```python
LOGGING = {
    'loggers': {
        'apps.authentication.exceptions': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## Conclusion

The authentication error handling system provides comprehensive error management with:

- **Consistency**: Structured error responses across all endpoints
- **Security**: Rate limiting, brute force protection, and security monitoring
- **Usability**: Clear error messages and proper HTTP status codes
- **Maintainability**: Modular design with easy extension points
- **Performance**: Efficient caching and minimal overhead

This implementation satisfies all requirements of Task 9.1 and provides a solid foundation for secure authentication error handling.