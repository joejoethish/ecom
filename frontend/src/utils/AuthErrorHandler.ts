// Authentication error handling utility

export interface AuthError {
  code: string;
  message: string;
  field?: string;
  details?: any;
}

export interface AuthErrorResponse {
  error: AuthError;
  userMessage: string;
  shouldRetry: boolean;
  shouldRedirect?: string;
}

export class AuthErrorHandler {
  private static readonly ERROR_CODES = {
    // Authentication errors
    INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
    ACCOUNT_LOCKED: 'ACCOUNT_LOCKED',
    ACCOUNT_DISABLED: 'ACCOUNT_DISABLED',
    EMAIL_NOT_VERIFIED: 'EMAIL_NOT_VERIFIED',
    TOKEN_EXPIRED: 'TOKEN_EXPIRED',
    TOKEN_INVALID: 'TOKEN_INVALID',
    
    // Rate limiting
    RATE_LIMITED: 'RATE_LIMITED',
    TOO_MANY_ATTEMPTS: 'TOO_MANY_ATTEMPTS',
    
    // Validation errors
    VALIDATION_ERROR: 'VALIDATION_ERROR',
    WEAK_PASSWORD: 'WEAK_PASSWORD',
    EMAIL_EXISTS: 'EMAIL_EXISTS',
    
    // Network errors
    NETWORK_ERROR: 'NETWORK_ERROR',
    SERVER_ERROR: 'SERVER_ERROR',
    TIMEOUT: 'TIMEOUT',
    
    // Permission errors
    INSUFFICIENT_PERMISSIONS: 'INSUFFICIENT_PERMISSIONS',
    ADMIN_REQUIRED: 'ADMIN_REQUIRED',
  } as const;

  private static readonly USER_MESSAGES = {
    [AuthErrorHandler.ERROR_CODES.INVALID_CREDENTIALS]: 
      'Invalid email or password. Please check your credentials and try again.',
    [AuthErrorHandler.ERROR_CODES.ACCOUNT_LOCKED]: 
      'Your account has been temporarily locked due to multiple failed login attempts. Please try again later or contact support.',
    [AuthErrorHandler.ERROR_CODES.ACCOUNT_DISABLED]: 
      'Your account has been disabled. Please contact support for assistance.',
    [AuthErrorHandler.ERROR_CODES.EMAIL_NOT_VERIFIED]: 
      'Please verify your email address before logging in. Check your inbox for a verification link.',
    [AuthErrorHandler.ERROR_CODES.TOKEN_EXPIRED]: 
      'Your session has expired. Please log in again.',
    [AuthErrorHandler.ERROR_CODES.TOKEN_INVALID]: 
      'Invalid authentication token. Please log in again.',
    [AuthErrorHandler.ERROR_CODES.RATE_LIMITED]: 
      'Too many requests. Please wait a moment before trying again.',
    [AuthErrorHandler.ERROR_CODES.TOO_MANY_ATTEMPTS]: 
      'Too many login attempts. Please wait 15 minutes before trying again.',
    [AuthErrorHandler.ERROR_CODES.VALIDATION_ERROR]: 
      'Please check your input and try again.',
    [AuthErrorHandler.ERROR_CODES.WEAK_PASSWORD]: 
      'Password is too weak. Please choose a stronger password with at least 8 characters, including uppercase, lowercase, numbers, and special characters.',
    [AuthErrorHandler.ERROR_CODES.EMAIL_EXISTS]: 
      'An account with this email address already exists. Please use a different email or try logging in.',
    [AuthErrorHandler.ERROR_CODES.NETWORK_ERROR]: 
      'Network connection error. Please check your internet connection and try again.',
    [AuthErrorHandler.ERROR_CODES.SERVER_ERROR]: 
      'Server error occurred. Please try again later or contact support if the problem persists.',
    [AuthErrorHandler.ERROR_CODES.TIMEOUT]: 
      'Request timed out. Please check your connection and try again.',
    [AuthErrorHandler.ERROR_CODES.INSUFFICIENT_PERMISSIONS]: 
      'You do not have permission to perform this action.',
    [AuthErrorHandler.ERROR_CODES.ADMIN_REQUIRED]: 
      'Admin privileges required to access this resource.',
  } as const;

  /**
   * Process authentication error and return structured response
   */
  static handleError(error: any): AuthErrorResponse {
    // Handle network errors
    if (!error.response) {
      return {
        error: {
          code: this.ERROR_CODES.NETWORK_ERROR,
          message: error.message || 'Network error',
        },
        userMessage: this.USER_MESSAGES[this.ERROR_CODES.NETWORK_ERROR],
        shouldRetry: true,
      };
    }

    const { status, data } = error.response;

    // Handle different HTTP status codes
    switch (status) {
      case 400:
        return this.handleBadRequest(data);
      case 401:
        return this.handleUnauthorized(data);
      case 403:
        return this.handleForbidden(data);
      case 429:
        return this.handleRateLimit(data);
      case 500:
      case 502:
      case 503:
      case 504:
        return this.handleServerError(data);
      default:
        return this.handleGenericError(data);
    }
  }

  private static handleBadRequest(data: any): AuthErrorResponse {
    // Check for specific validation errors
    if (data.email && data.email.includes('already exists')) {
      return {
        error: {
          code: this.ERROR_CODES.EMAIL_EXISTS,
          message: data.email,
          field: 'email',
        },
        userMessage: this.USER_MESSAGES[this.ERROR_CODES.EMAIL_EXISTS],
        shouldRetry: false,
      };
    }

    if (data.password && data.password.includes('weak')) {
      return {
        error: {
          code: this.ERROR_CODES.WEAK_PASSWORD,
          message: data.password,
          field: 'password',
        },
        userMessage: this.USER_MESSAGES[this.ERROR_CODES.WEAK_PASSWORD],
        shouldRetry: false,
      };
    }

    return {
      error: {
        code: this.ERROR_CODES.VALIDATION_ERROR,
        message: data.detail || data.message || 'Validation error',
        details: data,
      },
      userMessage: this.USER_MESSAGES[this.ERROR_CODES.VALIDATION_ERROR],
      shouldRetry: false,
    };
  }

  private static handleUnauthorized(data: any): AuthErrorResponse {
    const message = data.detail || data.message || '';

    if (message.includes('Invalid credentials') || message.includes('authentication failed')) {
      return {
        error: {
          code: this.ERROR_CODES.INVALID_CREDENTIALS,
          message,
        },
        userMessage: this.USER_MESSAGES[this.ERROR_CODES.INVALID_CREDENTIALS],
        shouldRetry: false,
      };
    }

    if (message.includes('email not verified')) {
      return {
        error: {
          code: this.ERROR_CODES.EMAIL_NOT_VERIFIED,
          message,
        },
        userMessage: this.USER_MESSAGES[this.ERROR_CODES.EMAIL_NOT_VERIFIED],
        shouldRetry: false,
        shouldRedirect: '/auth/verify-email',
      };
    }

    if (message.includes('token expired')) {
      return {
        error: {
          code: this.ERROR_CODES.TOKEN_EXPIRED,
          message,
        },
        userMessage: this.USER_MESSAGES[this.ERROR_CODES.TOKEN_EXPIRED],
        shouldRetry: false,
        shouldRedirect: '/auth/login',
      };
    }

    return {
      error: {
        code: this.ERROR_CODES.TOKEN_INVALID,
        message,
      },
      userMessage: this.USER_MESSAGES[this.ERROR_CODES.TOKEN_INVALID],
      shouldRetry: false,
      shouldRedirect: '/auth/login',
    };
  }

  private static handleForbidden(data: any): AuthErrorResponse {
    const message = data.detail || data.message || '';

    if (message.includes('admin') || message.includes('Admin')) {
      return {
        error: {
          code: this.ERROR_CODES.ADMIN_REQUIRED,
          message,
        },
        userMessage: this.USER_MESSAGES[this.ERROR_CODES.ADMIN_REQUIRED],
        shouldRetry: false,
      };
    }

    if (message.includes('disabled') || message.includes('suspended')) {
      return {
        error: {
          code: this.ERROR_CODES.ACCOUNT_DISABLED,
          message,
        },
        userMessage: this.USER_MESSAGES[this.ERROR_CODES.ACCOUNT_DISABLED],
        shouldRetry: false,
      };
    }

    return {
      error: {
        code: this.ERROR_CODES.INSUFFICIENT_PERMISSIONS,
        message,
      },
      userMessage: this.USER_MESSAGES[this.ERROR_CODES.INSUFFICIENT_PERMISSIONS],
      shouldRetry: false,
    };
  }

  private static handleRateLimit(data: any): AuthErrorResponse {
    const message = data.detail || data.message || '';

    if (message.includes('login attempts') || message.includes('account locked')) {
      return {
        error: {
          code: this.ERROR_CODES.ACCOUNT_LOCKED,
          message,
        },
        userMessage: this.USER_MESSAGES[this.ERROR_CODES.ACCOUNT_LOCKED],
        shouldRetry: true,
      };
    }

    return {
      error: {
        code: this.ERROR_CODES.RATE_LIMITED,
        message,
      },
      userMessage: this.USER_MESSAGES[this.ERROR_CODES.RATE_LIMITED],
      shouldRetry: true,
    };
  }

  private static handleServerError(data: any): AuthErrorResponse {
    return {
      error: {
        code: this.ERROR_CODES.SERVER_ERROR,
        message: data.detail || data.message || 'Server error',
      },
      userMessage: this.USER_MESSAGES[this.ERROR_CODES.SERVER_ERROR],
      shouldRetry: true,
    };
  }

  private static handleGenericError(data: any): AuthErrorResponse {
    return {
      error: {
        code: this.ERROR_CODES.SERVER_ERROR,
        message: data.detail || data.message || 'Unknown error',
      },
      userMessage: 'An unexpected error occurred. Please try again.',
      shouldRetry: true,
    };
  }

  /**
   * Get user-friendly message for error code
   */
  static getUserMessage(errorCode: string): string {
    return this.USER_MESSAGES[errorCode as keyof typeof this.USER_MESSAGES] || 
           'An unexpected error occurred. Please try again.';
  }

  /**
   * Check if error should trigger automatic retry
   */
  static shouldRetry(error: AuthError): boolean {
    const retryableCodes = [
      this.ERROR_CODES.NETWORK_ERROR,
      this.ERROR_CODES.SERVER_ERROR,
      this.ERROR_CODES.TIMEOUT,
      this.ERROR_CODES.RATE_LIMITED,
    ];
    
    return retryableCodes.includes(error.code as any);
  }

  /**
   * Check if error should trigger redirect
   */
  static getRedirectPath(error: AuthError): string | null {
    switch (error.code) {
      case this.ERROR_CODES.EMAIL_NOT_VERIFIED:
        return '/auth/verify-email';
      case this.ERROR_CODES.TOKEN_EXPIRED:
      case this.ERROR_CODES.TOKEN_INVALID:
        return '/auth/login';
      default:
        return null;
    }
  }
}

export default AuthErrorHandler;