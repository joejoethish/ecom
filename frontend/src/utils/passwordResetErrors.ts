/**
 * Password reset specific error handling utilities
 */
import { extractErrorInfo, getDisplayErrorMessage, logError } from './errorHandling';

/**
 * Password reset specific error codes
 */
export const PASSWORD_RESET_ERROR_CODES = {
  // Token related errors
  TOKEN_INVALID: 'token_invalid',
  TOKEN_EXPIRED: 'token_expired',
  TOKEN_NOT_FOUND: 'token_not_found',
  TOKEN_ALREADY_USED: 'token_already_used',
  
  // Email related errors
  EMAIL_NOT_FOUND: 'email_not_found',
  EMAIL_SEND_FAILED: 'email_send_failed',
  EMAIL_INVALID_FORMAT: 'email_invalid_format',
  
  // Password related errors
  PASSWORD_TOO_WEAK: 'password_too_weak',
  PASSWORD_MISMATCH: 'password_mismatch',
  PASSWORD_SAME_AS_OLD: 'password_same_as_old',
  
  // Rate limiting errors
  RATE_LIMIT_EXCEEDED: 'rate_limit_exceeded',
  TOO_MANY_ATTEMPTS: 'too_many_attempts',
  
  // General errors
  NETWORK_ERROR: 'network_error',
  SERVER_ERROR: 'server_error',
  VALIDATION_ERROR: 'validation_error',
} as const;

/**
 * User-friendly error messages for password reset errors
 */
export const PASSWORD_RESET_ERROR_MESSAGES = {
  [PASSWORD_RESET_ERROR_CODES.TOKEN_INVALID]: 'This password reset link is invalid. Please request a new one.',
  [PASSWORD_RESET_ERROR_CODES.TOKEN_EXPIRED]: 'This password reset link has expired. Please request a new one.',
  [PASSWORD_RESET_ERROR_CODES.TOKEN_NOT_FOUND]: 'This password reset link is not valid. Please request a new one.',
  [PASSWORD_RESET_ERROR_CODES.TOKEN_ALREADY_USED]: 'This password reset link has already been used. Please request a new one if needed.',
  
  [PASSWORD_RESET_ERROR_CODES.EMAIL_NOT_FOUND]: 'If an account with this email exists, you will receive a password reset link.',
  [PASSWORD_RESET_ERROR_CODES.EMAIL_SEND_FAILED]: 'We encountered an issue sending the reset email. Please try again.',
  [PASSWORD_RESET_ERROR_CODES.EMAIL_INVALID_FORMAT]: 'Please enter a valid email address.',
  
  [PASSWORD_RESET_ERROR_CODES.PASSWORD_TOO_WEAK]: 'Password must be at least 8 characters with uppercase, lowercase, number, and special character.',
  [PASSWORD_RESET_ERROR_CODES.PASSWORD_MISMATCH]: 'Passwords do not match. Please try again.',
  [PASSWORD_RESET_ERROR_CODES.PASSWORD_SAME_AS_OLD]: 'New password must be different from your current password.',
  
  [PASSWORD_RESET_ERROR_CODES.RATE_LIMIT_EXCEEDED]: 'Too many password reset requests. Please wait before trying again.',
  [PASSWORD_RESET_ERROR_CODES.TOO_MANY_ATTEMPTS]: 'Too many failed attempts. Please wait 15 minutes before trying again.',
  
  [PASSWORD_RESET_ERROR_CODES.NETWORK_ERROR]: 'Unable to connect to the server. Please check your internet connection and try again.',
  [PASSWORD_RESET_ERROR_CODES.SERVER_ERROR]: 'A server error occurred. Please try again later.',
  [PASSWORD_RESET_ERROR_CODES.VALIDATION_ERROR]: 'Please check your input and try again.',
} as const;

/**
 * Determine if an error is retryable
 */
export const isRetryablePasswordResetError = (errorCode: string): boolean => {
  const retryableErrors = [
    PASSWORD_RESET_ERROR_CODES.NETWORK_ERROR,
    PASSWORD_RESET_ERROR_CODES.SERVER_ERROR,
    PASSWORD_RESET_ERROR_CODES.EMAIL_SEND_FAILED,
  ];
  
  return retryableErrors.includes(errorCode as any);
};

/**
 * Get user-friendly error message for password reset errors
 */
export const getPasswordResetErrorMessage = (error: unknown): string => {
  const errorInfo = extractErrorInfo(error);
  
  // Check if it's a specific password reset error
  if (errorInfo.code in PASSWORD_RESET_ERROR_MESSAGES) {
    return PASSWORD_RESET_ERROR_MESSAGES[errorInfo.code as keyof typeof PASSWORD_RESET_ERROR_MESSAGES];
  }
  
  // Fall back to general error handling
  return getDisplayErrorMessage(error);
};

/**
 * Log password reset specific errors with context
 */
export const logPasswordResetError = (
  error: unknown, 
  context: string, 
  additionalData?: Record<string, any>
): void => {
  const errorInfo = extractErrorInfo(error);
  
  // Enhanced logging for password reset errors
  if (process.env.NODE_ENV === 'development') {
    console.error('Password Reset Error:', {
      context,
      error: errorInfo,
      additionalData,
      timestamp: new Date().toISOString(),
      originalError: error,
    });
  }
  
  // In production, you might want to send this to an error tracking service
  // with additional password reset specific context
  logError(error, `PasswordReset.${context}`);
};

/**
 * Handle password reset API response errors
 */
export const handlePasswordResetApiError = (response: any): never => {
  const errorCode = response.error?.code || 'unknown_error';
  const errorMessage = getPasswordResetErrorMessage(response.error);
  
  const error = new Error(errorMessage);
  (error as any).code = errorCode;
  (error as any).statusCode = response.error?.status_code;
  (error as any).details = response.error?.details;
  
  throw error;
};

/**
 * Retry configuration for password reset operations
 */
export const PASSWORD_RESET_RETRY_CONFIG = {
  maxRetries: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
  backoffMultiplier: 2,
  jitterMax: 1000, // 1 second
} as const;

/**
 * Enhanced retry function specifically for password reset operations
 */
export const retryPasswordResetOperation = async <T>(
  operation: () => Promise<T>,
  context: string,
  config = PASSWORD_RESET_RETRY_CONFIG
): Promise<T> => {
  let lastError: unknown;
  
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      
      const errorInfo = extractErrorInfo(error);
      
      // Don't retry on certain error types
      if (!isRetryablePasswordResetError(errorInfo.code)) {
        logPasswordResetError(error, `${context}.NonRetryableError`, { attempt });
        break;
      }
      
      // Don't retry on the last attempt
      if (attempt === config.maxRetries) {
        logPasswordResetError(error, `${context}.MaxRetriesExceeded`, { attempt });
        break;
      }
      
      // Calculate delay with exponential backoff and jitter
      const baseDelay = Math.min(
        config.baseDelay * Math.pow(config.backoffMultiplier, attempt),
        config.maxDelay
      );
      const jitter = Math.random() * config.jitterMax;
      const delay = baseDelay + jitter;
      
      logPasswordResetError(error, `${context}.RetryAttempt`, { 
        attempt: attempt + 1, 
        delay,
        willRetry: true 
      });
      
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
};

/**
 * Validate password reset token format
 */
export const isValidTokenFormat = (token: string): boolean => {
  // Token should be a hex string of at least 32 characters
  return /^[a-f0-9]{32,}$/i.test(token);
};

/**
 * Security event logging for password reset operations
 */
export const logPasswordResetSecurityEvent = (
  event: 'request' | 'validate' | 'reset' | 'suspicious',
  details: {
    email?: string;
    token?: string;
    ipAddress?: string;
    userAgent?: string;
    success?: boolean;
    errorCode?: string;
    additionalData?: Record<string, any>;
  }
): void => {
  // Import here to avoid circular dependencies
  const { logSecurityEvent } = require('./securityMonitoring');
  
  const severity = details.success === false && details.errorCode ? 'medium' : 'low';
  
  logSecurityEvent(
    'password_reset',
    `password_reset_${event}`,
    severity,
    {
      success: details.success,
      errorCode: details.errorCode,
      email: details.email,
      token: details.token,
      ...details.additionalData
    },
    {
      ipAddress: details.ipAddress,
      userAgent: details.userAgent
    }
  );
};