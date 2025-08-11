/**
 * Enhanced error handling utilities for inventory management
 */
import toast from 'react-hot-toast';
import { ApiResponse } from '@/types';

export interface ErrorDetails {
  message: string;
  code?: string;
  status_code?: number;
  field_errors?: Record<string, string[]>;
  details?: any;
}

export interface NetworkError {
  type: 'network';
  message: string;
}

export interface ValidationError {
  type: 'validation';
  message: string;
  field_errors: Record<string, string[]>;
}

export interface ServerError {
  type: 'server';
  message: string;
  status_code: number;
  code?: string;
}

export interface UnknownError {
  type: 'unknown';
  message: string;
}

export interface PermissionError {
  type: 'permission';
  message: string;
}

export type ErrorType = NetworkError | ValidationError | ServerError | UnknownError | PermissionError;

/**
 * Parse API response error into structured error type
 */
export const parseApiError = (response: ApiResponse<any>): ErrorType => {
  if (!response.error) {
    return {
      type: 'unknown',
      message: 'An unexpected error occurred'
    };
  }

  const { error } = response;

  // Network error
  if (error.status_code === 0 || error.code === 'network_error') {
    return {
      type: 'network',
      message: error.message || 'Network error. Please check your connection.'
    };
  }

  // Validation error (400)
  if (error.status_code === 400) {
    const fieldErrors: Record<string, string[]> = {};
    
    // Parse Django REST framework validation errors
    if (error.details && typeof error.details === 'object') {
      Object.entries(error.details).forEach(([field, messages]) => {
        if (Array.isArray(messages)) {
          fieldErrors[field] = messages;
        } else if (typeof messages === 'string') {
          fieldErrors[field] = [messages];
        }
      });
    }

    return {
      type: 'validation',
      message: error.message || 'Please check your input and try again.',
      field_errors: fieldErrors
    };
  }

  // Server error (500+)
  if (error.status_code >= 500) {
    return {
      type: 'server',
      message: error.message || 'Server error. Please try again later.',
      status_code: error.status_code,
      code: error.code
    };
  }

  // Permission errors (401, 403)
  if (error.status_code === 401 || error.status_code === 403) {
    return {
      type: 'permission',
      message: error.message || 'You do not have permission to perform this action.'
    };
  }

  // Other client errors (404, etc.)
  return {
    type: 'server',
    message: error.message || 'An error occurred. Please try again.',
    status_code: error.status_code,
    code: error.code
  };
};

/**
 * Display error message using toast notification
 */
export const showErrorToast = (error: ErrorType, customMessage?: string) => {
  const message = customMessage || error.message;
  
  switch (error.type) {
    case 'network':
      toast.error(message, {
        duration: 5000,
        icon: '🌐',
      });
      break;
    case 'validation':
      toast.error(message, {
        duration: 4000,
        icon: '⚠️',
      });
      break;
    case 'server':
      toast.error(message, {
        duration: 6000,
        icon: '🚨',
      });
      break;
    case 'permission':
      toast.error(message, {
        duration: 5000,
        icon: '🔒',
      });
      break;
    default:
      toast.error(message, {
        duration: 4000,
      });
  }
};

/**
 * Display success message using toast notification
 */
export const showSuccessToast = (message: string, options?: { duration?: number; icon?: string }) => {
  toast.success(message, {
    duration: options?.duration || 3000,
    icon: options?.icon || '✅',
  });
};

/**
 * Handle API response with automatic error display
 */
export const handleApiResponse = <T>(
  response: ApiResponse<T>,
  options?: {
    successMessage?: string;
    errorMessage?: string;
    showSuccessToast?: boolean;
    showErrorToast?: boolean;
  }
): { success: boolean; data?: T; error?: ErrorType } => {
  const {
    successMessage,
    errorMessage,
    showSuccessToast: showSuccess = false,
    showErrorToast: showError = true
  } = options || {};

  if (response.success) {
    if (showSuccess && successMessage) {
      showSuccessToast(successMessage);
    }
    return { success: true, data: response.data };
  } else {
    const error = parseApiError(response);
    if (showError) {
      showErrorToast(error, errorMessage);
    }
    return { success: false, error };
  }
};

/**
 * Get user-friendly error message for specific operations
 */
export const getOperationErrorMessage = (operation: string, error: ErrorType): string => {
  const baseMessages: Record<string, string> = {
    create: 'Failed to create item',
    update: 'Failed to update item',
    delete: 'Failed to delete item',
    fetch: 'Failed to load data',
    search: 'Search failed',
    export: 'Export failed',
    adjust: 'Stock adjustment failed',
    acknowledge: 'Failed to acknowledge alert'
  };

  const baseMessage = baseMessages[operation] || 'Operation failed';

  switch (error.type) {
    case 'network':
      return `${baseMessage}. Please check your internet connection and try again.`;
    case 'validation':
      return `${baseMessage}. Please check your input and try again.`;
    case 'server':
      if (error.status_code === 404) {
        return `${baseMessage}. The requested item was not found.`;
      }
      if (error.status_code === 403) {
        return `${baseMessage}. You don't have permission to perform this action.`;
      }
      if (error.status_code === 409) {
        return `${baseMessage}. This action conflicts with existing data.`;
      }
      return `${baseMessage}. Please try again later.`;
    default:
      return `${baseMessage}. Please try again.`;
  }
};

/**
 * Retry mechanism for failed operations
 */
export const withRetry = async <T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> => {
  let lastError: Error;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error('Unknown error');
      
      if (attempt === maxRetries) {
        throw lastError;
      }

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay * attempt));
    }
  }

  throw lastError!;
};

/**
 * Debounce function for search operations
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;

  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * Format validation errors for display in forms
 */
export const formatValidationErrors = (error: ValidationError): Record<string, string> => {
  const formattedErrors: Record<string, string> = {};
  
  Object.entries(error.field_errors).forEach(([field, messages]) => {
    formattedErrors[field] = messages[0]; // Take first error message
  });

  return formattedErrors;
};

/**
 * Check if error is recoverable (user can retry)
 */
export const isRecoverableError = (error: ErrorType): boolean => {
  switch (error.type) {
    case 'network':
      return true;
    case 'server':
      // 5xx errors are usually temporary
      return error.status_code >= 500;
    case 'validation':
      return false; // User needs to fix input
    default:
      return true;
  }
};

/**
 * Extract error information from various error types
 */
export const extractErrorInfo = (error: any): { message: string; code: string; status_code?: number } => {
  if (!error) {
    return {
      message: 'An unexpected error occurred',
      code: 'unknown_error'
    };
  }

  // If it's already an ErrorType
  if (error.type && error.message) {
    return {
      message: error.message,
      code: error.code || error.type,
      status_code: error.status_code
    };
  }

  // If it's an API response error
  if (error.message && error.code) {
    return {
      message: error.message,
      code: error.code,
      status_code: error.status_code
    };
  }

  // If it's a standard Error object
  if (error instanceof Error) {
    return {
      message: error.message,
      code: 'error'
    };
  }

  // If it's a string
  if (typeof error === 'string') {
    return {
      message: error,
      code: 'string_error'
    };
  }

  // Fallback
  return {
    message: 'An unexpected error occurred',
    code: 'unknown_error'
  };
};

/**
 * Get display-friendly error message
 */
export const getDisplayErrorMessage = (error: any): string => {
  const errorInfo = extractErrorInfo(error);
  return errorInfo.message;
};

/**
 * Log error for debugging purposes
 */
export const logError = (error: any, context?: string, additionalData?: any): void => {
  const errorInfo = extractErrorInfo(error);

  console.error('Error logged:', {
    context,
    error: errorInfo,
    additionalData,
    timestamp: new Date().toISOString()
  });
};

/**
 * Retry with backoff (alias for withRetry for backward compatibility)
 */
export const retryWithBackoff = withRetry;