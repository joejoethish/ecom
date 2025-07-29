/**
 * Error handling utilities and types
 */
import axios from 'axios';
import { ApiResponse } from '@/types';
import { isAxiosError, hasErrorResponse, hasErrorRequest, hasApiError } from './typeGuards';

/**
 * Standard error interface for the application
 */
export interface AppError {
  message: string;
  code: string;
  status_code?: number;
  details?: any;
}

/**
 * Error codes used throughout the application
 */
export const ERROR_CODES = {
  NETWORK_ERROR: 'network_error',
  API_ERROR: 'api_error',
  VALIDATION_ERROR: 'validation_error',
  AUTHENTICATION_ERROR: 'authentication_error',
  AUTHORIZATION_ERROR: 'authorization_error',
  NOT_FOUND_ERROR: 'not_found_error',
  SERVER_ERROR: 'server_error',
  UNKNOWN_ERROR: 'unknown_error',
} as const;

/**
 * Extract error information from various error types
 */
export const extractErrorInfo = (error: unknown): AppError => {
  // Handle AxiosError
  if (isAxiosError(error)) {
    if (hasErrorResponse(error)) {
      return {
        message: error.response.data?.error?.message || 
                error.response.data?.message || 
                'An error occurred',
        code: error.response.data?.error?.code || ERROR_CODES.API_ERROR,
        status_code: error.response.status,
        details: error.response.data?.error?.details || error.response.data,
      };
    } else if (hasErrorRequest(error)) {
      return {
        message: 'Network error. Please check your connection.',
        code: ERROR_CODES.NETWORK_ERROR,
        status_code: 0,
      };
    }
  }

  // Handle standard Error
  if (error && typeof error === 'object' && 'message' in error) {
    return {
      message: (error as Error).message,
      code: ERROR_CODES.UNKNOWN_ERROR,
      status_code: 0,
    };
  }

  // Handle string errors
  if (typeof error === 'string') {
    return {
      message: error,
      code: ERROR_CODES.UNKNOWN_ERROR,
      status_code: 0,
    };
  }

  // Fallback for unknown error types
  return {
    message: 'An unexpected error occurred',
    code: ERROR_CODES.UNKNOWN_ERROR,
    status_code: 0,
  };
};

/**
 * Handle API response errors
 */
export const handleApiResponse = <T>(response: ApiResponse<T>): T => {
  if (hasApiError(response)) {
    throw new Error(response.error.message);
  }
  
  if (!response.data) {
    throw new Error('No data received from API');
  }
  
  return response.data;
};

/**
 * Create a standardized error message for display to users
 */
export const getDisplayErrorMessage = (error: unknown): string => {
  const errorInfo = extractErrorInfo(error);
  
  switch (errorInfo.code) {
    case ERROR_CODES.NETWORK_ERROR:
      return 'Unable to connect to the server. Please check your internet connection and try again.';
    case ERROR_CODES.AUTHENTICATION_ERROR:
      return 'Please log in to continue.';
    case ERROR_CODES.AUTHORIZATION_ERROR:
      return 'You do not have permission to perform this action.';
    case ERROR_CODES.NOT_FOUND_ERROR:
      return 'The requested resource was not found.';
    case ERROR_CODES.VALIDATION_ERROR:
      return errorInfo.message || 'Please check your input and try again.';
    case ERROR_CODES.SERVER_ERROR:
      return 'A server error occurred. Please try again later.';
    default:
      return errorInfo.message || 'An unexpected error occurred. Please try again.';
  }
};

/**
 * Log error information for debugging
 */
export const logError = (error: unknown, context?: string): void => {
  const errorInfo = extractErrorInfo(error);
  
  if (process.env.NODE_ENV === 'development') {
    console.error('Error occurred:', {
      context,
      error: errorInfo,
      originalError: error,
    });
  }
  
  // In production, you might want to send this to an error tracking service
  // like Sentry, LogRocket, etc.
};

/**
 * Retry function with exponential backoff
 */
export const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> => {
  let lastError: unknown;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (attempt === maxRetries) {
        break;
      }
      
      // Don't retry on certain error types
      if (isAxiosError(error) && hasErrorResponse(error)) {
        const status = error.response.status;
        if (status >= 400 && status < 500 && status !== 429) {
          // Don't retry client errors (except rate limiting)
          break;
        }
      }
      
      // Exponential backoff with jitter
      const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
};