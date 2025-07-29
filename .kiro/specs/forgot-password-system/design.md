# Design Document

## Overview

The Forgot Password System is a secure, email-based password reset mechanism that integrates with the existing Django backend and Next.js frontend. The system follows security best practices including token hashing, rate limiting, and protection against enumeration attacks while providing a smooth user experience.

## Architecture

### System Flow
1. **Request Phase**: User submits email → Backend validates → Token generated → Email sent
2. **Verification Phase**: User clicks email link → Token validated → Reset form displayed
3. **Reset Phase**: User submits new password → Password updated → Token invalidated → Redirect to login

### Security Model
- Cryptographically secure token generation using Django's `secrets` module
- Tokens are hashed before database storage using SHA-256
- Constant-time token comparison to prevent timing attacks
- Rate limiting per IP address (5 requests/hour)
- Generic success messages to prevent email enumeration
- CSRF protection on all forms

## Components and Interfaces

### Backend Components

#### 1. Password Reset Token Model
```python
class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=64)  # SHA-256 hash
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField()
```

#### 2. Rate Limiting Model
```python
class PasswordResetAttempt(models.Model):
    ip_address = models.GenericIPAddressField()
    email = models.EmailField()
    attempted_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
```

#### 3. Password Reset Service
- `generate_reset_token(user, ip_address)`: Creates secure token and database record
- `validate_reset_token(token)`: Verifies token validity and expiration
- `reset_password(token, new_password)`: Updates password and invalidates token
- `check_rate_limit(ip_address)`: Validates request frequency
- `send_reset_email(user, token)`: Sends formatted email with reset link

#### 4. API Endpoints
- `POST /api/v1/auth/forgot-password/`: Request password reset
- `POST /api/v1/auth/reset-password/`: Reset password with token
- `GET /api/v1/auth/validate-reset-token/<token>/`: Validate token

### Frontend Components

#### 1. ForgotPasswordForm Component (Enhanced)
- Email input with validation
- Loading states and error handling
- Success confirmation screen
- Integration with authApi service

#### 2. ResetPasswordForm Component (New)
- Token validation on mount
- Password strength validation
- Confirmation password matching
- Success/error state management

#### 3. AuthApi Service (Enhanced)
```typescript
interface AuthApi {
  requestPasswordReset(email: string): Promise<ApiResponse<void>>;
  validateResetToken(token: string): Promise<ApiResponse<{valid: boolean}>>;
  resetPassword(token: string, password: string): Promise<ApiResponse<void>>;
}
```

#### 4. Password Reset Pages
- `/auth/forgot-password`: Forgot password form
- `/auth/reset-password/[token]`: Password reset form with token validation

## Data Models

### Database Schema

#### password_reset_tokens
```sql
CREATE TABLE password_reset_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    ip_address INET NOT NULL,
    CONSTRAINT fk_password_reset_tokens_user FOREIGN KEY (user_id) REFERENCES auth_user(id)
);

CREATE INDEX idx_password_reset_tokens_token_hash ON password_reset_tokens(token_hash);
CREATE INDEX idx_password_reset_tokens_expires_at ON password_reset_tokens(expires_at);
CREATE INDEX idx_password_reset_tokens_user_used ON password_reset_tokens(user_id, is_used);
```

#### password_reset_attempts
```sql
CREATE TABLE password_reset_attempts (
    id BIGSERIAL PRIMARY KEY,
    ip_address INET NOT NULL,
    email VARCHAR(254) NOT NULL,
    attempted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    success BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_password_reset_attempts_ip_time ON password_reset_attempts(ip_address, attempted_at);
CREATE INDEX idx_password_reset_attempts_email_time ON password_reset_attempts(email, attempted_at);
```

### API Response Formats

#### Request Password Reset Response
```typescript
interface RequestResetResponse {
  success: boolean;
  message: string;
  error?: {
    code: string;
    message: string;
  };
}
```

#### Validate Token Response
```typescript
interface ValidateTokenResponse {
  success: boolean;
  data?: {
    valid: boolean;
    expired?: boolean;
  };
  error?: {
    code: string;
    message: string;
  };
}
```

## Error Handling

### Backend Error Scenarios
1. **Rate Limit Exceeded**: Return 429 with retry-after header
2. **Invalid Email Format**: Return 400 with validation errors
3. **Token Not Found/Expired**: Return 400 with specific error codes
4. **Password Validation Failed**: Return 400 with password requirements
5. **Database Errors**: Return 500 with generic error message

### Frontend Error Handling
1. **Network Errors**: Display retry option with exponential backoff
2. **Validation Errors**: Show field-specific error messages
3. **Rate Limiting**: Display countdown timer and retry guidance
4. **Token Expiration**: Redirect to forgot password with explanation
5. **Server Errors**: Show generic error with support contact

### Error Codes
- `RATE_LIMIT_EXCEEDED`: Too many requests from IP
- `TOKEN_EXPIRED`: Reset token has expired
- `TOKEN_INVALID`: Reset token not found or malformed
- `TOKEN_USED`: Reset token already consumed
- `PASSWORD_WEAK`: Password doesn't meet requirements
- `USER_NOT_FOUND`: Email not in system (internal only)

## Testing Strategy

### Backend Testing

#### Unit Tests
- Token generation and validation logic
- Password hashing and comparison
- Rate limiting functionality
- Email service integration
- Database model operations

#### Integration Tests
- Complete password reset flow
- API endpoint responses
- Email delivery verification
- Rate limiting across requests
- Token expiration handling

#### Security Tests
- Timing attack resistance
- Token enumeration prevention
- CSRF protection validation
- SQL injection prevention
- XSS protection in emails

### Frontend Testing

#### Component Tests
- Form validation and submission
- Loading state management
- Error message display
- Success flow navigation
- Token validation handling

#### Integration Tests
- API service integration
- Route navigation flow
- Error boundary behavior
- Accessibility compliance
- Cross-browser compatibility

#### E2E Tests
- Complete password reset journey
- Email link clicking simulation
- Form validation scenarios
- Error recovery flows
- Mobile responsiveness

### Performance Testing
- Email sending performance under load
- Database query optimization
- Token cleanup job efficiency
- Rate limiting accuracy
- Frontend bundle size impact

## Security Considerations

### Token Security
- 32-character cryptographically secure tokens
- SHA-256 hashing before database storage
- 1-hour expiration window
- Immediate invalidation after use
- Cleanup of expired tokens

### Attack Prevention
- Rate limiting: 5 requests per IP per hour
- Email enumeration protection via generic responses
- Timing attack prevention with constant-time comparison
- CSRF protection on all forms
- SQL injection prevention via parameterized queries

### Data Protection
- Minimal logging of sensitive information
- Secure email template rendering
- IP address anonymization in logs
- Compliance with data retention policies
- Encrypted database connections

### Monitoring and Alerting
- Failed reset attempt tracking
- Suspicious activity detection
- Rate limit breach notifications
- Email delivery failure alerts
- Performance metric monitoring