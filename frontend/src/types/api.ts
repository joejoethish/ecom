/**
 * Common API response types for the application
 */

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  next: string | null;
  previous: string | null;
}

export interface ErrorResponse {
  error: string;
  details?: Record<string, any>;
  code?: string;
}

export interface SuccessResponse<T = any> {
  data: T;
  message?: string;
}