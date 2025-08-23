import { AUTH_ROUTES } from '@/constants';

export interface AuthError {
  code: string;
  message: string;
  field?: string;
  details?: Record<string, any>;
}

export interface AuthErrorResponse {
  error?: AuthError;
  errors?: Record<string, string[]>;
  detail?: string;
  message?: string;
}

/**
 * Map backend error codes to user-friendly messages
 */
const ERROR_MESSAGES: Record<string, string> = {
  // Authentication errors
  'INVALID_CREDENTIALS': 'Invalid email or password. Please try again.',
  'ACCOUNT_LOCKED': 'Your account has been temporarily locked due to multiple failed login attempts.',
  'EMAIL_NOT_VERIFIED': 'Please verify your email address before signing in.',
  'ACCOUNT_DISABLED': 'Your account has been disabled. Please contact support.',
  'INVALID_TOKEN': 'This link is invalid or has expired. Please request a new one.',
  'TOKEN_EXPIRED': 'This link has expired. Please request a new one.',
  'TOKEN_USED': 'This link has already been used. Please request a new one.',
  
  // Registration errors
  'EMAIL_ALREADY_EXISTS': 'An account with this email already exists.',
  'USERNAME_ALREADY_EXISTS': 'This username is already taken.',
  'WEAK_PASSWORD': 'Password is too weak. Please choose a stronger password.',
  'PASSWORD_MISMATCH': 'Passwords do not match.',
  
  // Verification errors
  'VERIFICATION_FAILED': 'Email verification failed. Please try again.',
  'ALREADY_VERIFIED': 'Your email is already verified.',
  'VERIFICATION_LIMIT_EXCEEDED': 'Too many verification attempts. Please try again later.',
  
  // Password reset errors
  'RESET_FAILED': 'Password reset failed. Please try again.',
  'RESET_LIMIT_EXCEEDED': 'Too many password reset requests. Please try again later.',
  'INVALID_RESET_TOKEN': 'This password reset link is invalid or has expired.',
  
  // Rate limiting
  'RATE_LIMIT_EXCEEDED': 'Too many requests. Please wait before trying again.',
  'LOGIN_ATTEMPTS_EXCEEDED': 'Too many login attempts. Please try again later.',
  
  // Network errors
  'NETWORK_ERROR': 'Network error. Please check your connection and try again.',
  'SERVER_ERROR': 'Server error. Please try again later.',
  'TIMEOUT': 'Request timed out. Please try again.',
  
  // Generic errors
  'UNKNOWN_ERROR': 'An unexpected error occurred. Please try again.',
  'VALIDATION_ERROR': 'Please check your input and try again.',
};

/**
 * Extract error information from API response
 */
export function extractAuthError(error: any): AuthError {
  // Handle different error response formats
  if (error?.response?.data) {
    const data = error.response.data;
    
    // Handle structured error response
    if (data.error) {
      return {
        code: data.error.code || 'UNKNOWN_ERROR',
        message: data.error.message || ERROR_MESSAGES[data.error.code] || ERROR_MESSAGES.UNKNOWN_ERROR,
        field: data.error.field,
        details: data.error.details,
      };
    }
    
    // Handle validation errors
    if (data.errors) {
      const firstField = Object.keys(data.errors)[0];
      const firstError = data.errors[firstField]?.[0];
      return {
        code: 'VALIDATION_ERROR',
        message: firstError || ERROR_MESSAGES.VALIDATION_ERROR,
        field: firstField,
        details: data.errors,
      };
    }
    
    // Handle simple error message
    if (data.detail || data.message) {
      return {
        code: 'UNKNOWN_ERROR',
        message: data.detail || data.message,
      };
    }
  }
  
  // Handle network errors
  if (error?.code === 'NETWORK_ERROR' || !error?.response) {
    return {
      code: 'NETWORK_ERROR',
      message: ERROR_MESSAGES.NETWORK_ERROR,
    };
  }
  
  // Handle timeout errors
  if (error?.code === 'ECONNABORTED') {
    return {
      code: 'TIMEOUT',
      message: ERROR_MESSAGES.TIMEOUT,
    };
  }
  
  // Handle HTTP status codes
  if (error?.response?.status) {
    const status = error.response.status;
    switch (status) {
      case 400:
        return {
          code: 'VALIDATION_ERROR',
          message: ERROR_MESSAGES.VALIDATION_ERROR,
        };
      case 401:
        return {
          code: 'INVALID_CREDENTIALS',
          message: ERROR_MESSAGES.INVALID_CREDENTIALS,
        };
      case 403:
        return {
          code: 'ACCOUNT_DISABLED',
          message: ERROR_MESSAGES.ACCOUNT_DISABLED,
        };
      case 429:
        return {
          code: 'RATE_LIMIT_EXCEEDED',
          message: ERROR_MESSAGES.RATE_LIMIT_EXCEEDED,
        };
      case 500:
      case 502:
      case 503:
      case 504:
        return {
          code: 'SERVER_ERROR',
          message: ERROR_MESSAGES.SERVER_ERROR,
        };
      default:
        return {
          code: 'UNKNOWN_ERROR',
          message: ERROR_MESSAGES.UNKNOWN_ERROR,
        };
    }
  }
  
  // Fallback for unknown errors
  return {
    code: 'UNKNOWN_ERROR',
    message: error?.message || ERROR_MESSAGES.UNKNOWN_ERROR,
  };
}

/**
 * Get user-friendly error message
 */
export function getErrorMessage(error: any): string {
  const authError = extractAuthError(error);
  return authError.message;
}

/**
 * Get field-specific validation errors
 */
export function getFieldErrors(error: any): Record<string, string> {
  const authError = extractAuthError(error);
  
  if (authError.details && typeof authError.details === 'object') {
    const fieldErrors: Record<string, string> = {};
    
    for (const [field, messages] of Object.entries(authError.details)) {
      if (Array.isArray(messages) && messages.length > 0) {
        fieldErrors[field] = messages[0];
      } else if (typeof messages === 'string') {
        fieldErrors[field] = messages;
      }
    }
    
    return fieldErrors;
  }
  
  if (authError.field) {
    return {
      [authError.field]: authError.message,
    };
  }
  
  return {};
}

/**
 * Check if error requires redirect to login
 */
export function shouldRedirectToLogin(error: any): boolean {
  const authError = extractAuthError(error);
  const redirectCodes = [
    'INVALID_TOKEN',
    'TOKEN_EXPIRED',
    'ACCOUNT_DISABLED',
    'INVALID_CREDENTIALS',
  ];
  
  return redirectCodes.includes(authError.code);
}

/**
 * Check if error requires email verification
 */
export function requiresEmailVerification(error: any): boolean {
  const authError = extractAuthError(error);
  return authError.code === 'EMAIL_NOT_VERIFIED';
}

/**
 * Get suggested action for error
 */
export function getSuggestedAction(error: any): {
  action: string;
  route?: string;
  message?: string;
} {
  const authError = extractAuthError(error);
  
  switch (authError.code) {
    case 'EMAIL_NOT_VERIFIED':
      return {
        action: 'verify_email',
        route: AUTH_ROUTES.VERIFY_EMAIL,
        message: 'Please verify your email address to continue.',
      };
      
    case 'INVALID_TOKEN':
    case 'TOKEN_EXPIRED':
    case 'TOKEN_USED':
      if (authError.message.toLowerCase().includes('password')) {
        return {
          action: 'request_password_reset',
          route: AUTH_ROUTES.FORGOT_PASSWORD,
          message: 'Please request a new password reset link.',
        };
      } else {
        return {
          action: 'resend_verification',
          route: AUTH_ROUTES.VERIFY_EMAIL,
          message: 'Please request a new verification email.',
        };
      }
      
    case 'ACCOUNT_LOCKED':
    case 'LOGIN_ATTEMPTS_EXCEEDED':
      return {
        action: 'wait_and_retry',
        message: 'Please wait a few minutes before trying again.',
      };
      
    case 'RATE_LIMIT_EXCEEDED':
      return {
        action: 'wait_and_retry',
        message: 'Please wait before making another request.',
      };
      
    case 'NETWORK_ERROR':
      return {
        action: 'check_connection',
        message: 'Please check your internet connection and try again.',
      };
      
    case 'SERVER_ERROR':
      return {
        action: 'try_later',
        message: 'Our servers are experiencing issues. Please try again later.',
      };
      
    default:
      return {
        action: 'retry',
        message: 'Please try again.',
      };
  }
}

/**
 * Format error for display in UI
 */
export function formatErrorForDisplay(error: any): {
  title: string;
  message: string;
  action?: {
    label: string;
    route?: string;
    callback?: () => void;
  };
} {
  const authError = extractAuthError(error);
  const suggestion = getSuggestedAction(error);
  
  let title = 'Error';
  switch (authError.code) {
    case 'INVALID_CREDENTIALS':
      title = 'Login Failed';
      break;
    case 'EMAIL_NOT_VERIFIED':
      title = 'Email Verification Required';
      break;
    case 'ACCOUNT_LOCKED':
      title = 'Account Locked';
      break;
    case 'RATE_LIMIT_EXCEEDED':
      title = 'Too Many Requests';
      break;
    case 'NETWORK_ERROR':
      title = 'Connection Error';
      break;
    case 'SERVER_ERROR':
      title = 'Server Error';
      break;
  }
  
  let actionLabel = 'Try Again';
  switch (suggestion.action) {
    case 'verify_email':
      actionLabel = 'Verify Email';
      break;
    case 'request_password_reset':
      actionLabel = 'Reset Password';
      break;
    case 'resend_verification':
      actionLabel = 'Resend Email';
      break;
    case 'wait_and_retry':
      actionLabel = 'OK';
      break;
  }
  
  return {
    title,
    message: authError.message,
    action: {
      label: actionLabel,
      route: suggestion.route,
    },
  };
}