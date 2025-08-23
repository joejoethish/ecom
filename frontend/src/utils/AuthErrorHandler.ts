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

/**
 * Enhanced form validation error handling
 */
export class FormErrorHandler {
  /**
   * Process form validation errors from API response
   */
  static processFormErrors(error: any): Record<string, string> {
    const fieldErrors: Record<string, string> = {};

    if (error?.response?.data) {
      const data = error.response.data;

      // Handle Django REST framework validation errors
      if (data.errors && typeof data.errors === 'object') {
        Object.entries(data.errors).forEach(([field, messages]) => {
          if (Array.isArray(messages) && messages.length > 0) {
            fieldErrors[field] = messages[0];
          } else if (typeof messages === 'string') {
            fieldErrors[field] = messages;
          }
        });
      }

      // Handle non_field_errors
      if (data.non_field_errors && Array.isArray(data.non_field_errors)) {
        fieldErrors.general = data.non_field_errors[0];
      }

      // Handle individual field errors in root level
      Object.keys(data).forEach(key => {
        if (key !== 'error' && key !== 'errors' && Array.isArray(data[key])) {
          fieldErrors[key] = data[key][0];
        }
      });
    }

    return fieldErrors;
  }

  /**
   * Get general error message from form errors
   */
  static getGeneralError(error: any): string | null {
    const authError = AuthErrorHandler.handleError(error);
    
    // Check for general form errors
    if (error?.response?.data?.non_field_errors) {
      return error.response.data.non_field_errors[0];
    }

    // Return the processed auth error message
    return authError.userMessage;
  }

  /**
   * Check if error has field-specific validation errors
   */
  static hasFieldErrors(error: any): boolean {
    const fieldErrors = this.processFormErrors(error);
    return Object.keys(fieldErrors).length > 0;
  }
}

/**
 * Notification error handler for displaying errors to users
 */
export class NotificationErrorHandler {
  /**
   * Show error notification with appropriate styling and actions
   */
  static showError(error: any, options?: {
    title?: string;
    duration?: number;
    showRetry?: boolean;
    onRetry?: () => void;
  }): void {
    const authError = AuthErrorHandler.handleError(error);
    const { title, duration = 5000, showRetry = false, onRetry } = options || {};

    // Import toast dynamically to avoid SSR issues
    import('react-hot-toast').then(({ default: toast }) => {
      toast.error(authError.userMessage, {
        duration,
        style: {
          background: '#FEF2F2',
          border: '1px solid #FECACA',
          color: '#991B1B',
        },
        iconTheme: {
          primary: '#DC2626',
          secondary: '#FEF2F2',
        },
      });
    });
  }

  /**
   * Show success notification
   */
  static showSuccess(message: string, options?: {
    duration?: number;
  }): void {
    const { duration = 3000 } = options || {};

    import('react-hot-toast').then(({ default: toast }) => {
      toast.success(message, {
        duration,
        style: {
          background: '#F0FDF4',
          border: '1px solid #BBF7D0',
          color: '#166534',
        },
        iconTheme: {
          primary: '#16A34A',
          secondary: '#F0FDF4',
        },
      });
    });
  }

  /**
   * Show warning notification
   */
  static showWarning(message: string, options?: {
    duration?: number;
  }): void {
    const { duration = 4000 } = options || {};

    import('react-hot-toast').then(({ default: toast }) => {
      toast(message, {
        duration,
        icon: '⚠️',
        style: {
          background: '#FFFBEB',
          border: '1px solid #FED7AA',
          color: '#92400E',
        },
      });
    });
  }

  /**
   * Show info notification
   */
  static showInfo(message: string, options?: {
    duration?: number;
  }): void {
    const { duration = 4000 } = options || {};

    import('react-hot-toast').then(({ default: toast }) => {
      toast(message, {
        duration,
        icon: 'ℹ️',
        style: {
          background: '#EFF6FF',
          border: '1px solid #BFDBFE',
          color: '#1E40AF',
        },
      });
    });
  }
}

export default AuthErrorHandler;