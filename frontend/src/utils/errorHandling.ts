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
  details?: unknown;
}

export interface NetworkError {
  type: &apos;network&apos;;
  message: string;
}

export interface ValidationError {
  type: &apos;validation&apos;;
  message: string;
  field_errors: Record<string, string[]>;
}

export interface ServerError {
  type: &apos;server&apos;;
  message: string;
  status_code: number;
  code?: string;
}

export interface UnknownError {
  type: &apos;unknown&apos;;
  message: string;
}

export interface PermissionError {
  type: &apos;permission&apos;;
  message: string;
}

export type ErrorType = NetworkError | ValidationError | ServerError | UnknownError | PermissionError;

/**
 * Parse API response error into structured error type
 */
export const parseApiError = (response: ApiResponse<unknown>): ErrorType => {
  if (!response.error) {
    return {
      type: &apos;unknown&apos;,
      message: &apos;An unexpected error occurred&apos;
    };
  }


  // Network error
  if (error.status_code === 0 || error.code === &apos;network_error&apos;) {
    return {
      type: &apos;network&apos;,
      message: error.message || &apos;Network error. Please check your connection.&apos;
    };
  }

  // Validation error (400)
  if (error.status_code === 400) {
    
    // Parse Django REST framework validation errors
    if (error.details && typeof error.details === &apos;object&apos;) {
      Object.entries(error.details).forEach(([field, messages]) => {
        if (Array.isArray(messages)) {
          fieldErrors[field] = messages;
        } else if (typeof messages === &apos;string&apos;) {
          fieldErrors[field] = [messages];
        }
      });
    }

    return {
      type: &apos;validation&apos;,
      message: error.message || &apos;Please check your input and try again.&apos;,
      field_errors: fieldErrors
    };
  }

  // Server error (500+)
  if (error.status_code >= 500) {
    return {
      type: &apos;server&apos;,
      message: error.message || &apos;Server error. Please try again later.&apos;,
      status_code: error.status_code,
      code: error.code
    };
  }

  // Permission errors (401, 403)
  if (error.status_code === 401 || error.status_code === 403) {
    return {
      type: &apos;permission&apos;,
      message: error.message || &apos;You do not have permission to perform this action.&apos;
    };
  }

  // Other client errors (404, etc.)
  return {
    type: &apos;server&apos;,
    message: error.message || &apos;An error occurred. Please try again.&apos;,
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
    case &apos;network&apos;:
      toast.error(message, {
        duration: 5000,
        icon: &apos;🌐&apos;,
      });
      break;
    case &apos;validation&apos;:
      toast.error(message, {
        duration: 4000,
        icon: &apos;⚠️&apos;,
      });
      break;
    case &apos;server&apos;:
      toast.error(message, {
        duration: 6000,
        icon: &apos;🚨&apos;,
      });
      break;
    case &apos;permission&apos;:
      toast.error(message, {
        duration: 5000,
        icon: &apos;🔒&apos;,
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
    icon: options?.icon || &apos;✅&apos;,
  });
};

/**
 * Handle API response with automatic error display
 */
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
    create: &apos;Failed to create item&apos;,
    update: &apos;Failed to update item&apos;,
    delete: &apos;Failed to delete item&apos;,
    fetch: &apos;Failed to load data&apos;,
    search: &apos;Search failed&apos;,
    export: &apos;Export failed&apos;,
    adjust: &apos;Stock adjustment failed&apos;,
    acknowledge: &apos;Failed to acknowledge alert&apos;
  };

  const baseMessage = baseMessages[operation] || &apos;Operation failed&apos;;

  switch (error.type) {
    case &apos;network&apos;:
      return `${baseMessage}. Please check your internet connection and try again.`;
    case &apos;validation&apos;:
      return `${baseMessage}. Please check your input and try again.`;
    case &apos;server&apos;:
      if (error.status_code === 404) {
        return `${baseMessage}. The requested item was not found.`;
      }
      if (error.status_code === 403) {
        return `${baseMessage}. You don&apos;t have permission to perform this action.`;
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
  
  Object.entries(error.field_errors).forEach(([field, messages]) => {
    formattedErrors[field] = messages[0]; // Take first error message
  });

  return formattedErrors;
};

/**
 * Check if error is recoverable (user can retry)
 */
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
export const extractErrorInfo = (error: unknown): { message: string; code: string; status_code?: number } => {
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
  const errorInfo = extractErrorInfo(error);
  return errorInfo.message;
};

/**
 * Log error for debugging purposes
 */
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