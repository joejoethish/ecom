// API utility functions and axios configuration

import axios from 'axios';
import { API_BASE_URL } from '@/constants';
import { ApiResponse, AuthTokens } from '@/types';
import { getStoredTokens, removeStoredTokens, setStoredTokens } from './storage';

class ApiClient {
  private client: unknown;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config: unknown) => {
        const tokens = getStoredTokens();
        if (tokens?.access && config.headers) {
          config.headers.Authorization = `Bearer ${tokens.access}`;
        }
        return config;
      },
      (error: unknown) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response: unknown) => response,
      async (error: unknown) => {
        if (error && typeof error === &apos;object&apos; && &apos;config&apos; in error && &apos;response&apos; in error) {
          const originalRequest = (error as any).config;

          if ((error as any).response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
              const tokens = getStoredTokens();
              if (tokens?.refresh) {
                const response = await this.refreshToken(tokens.refresh);
                const newTokens = response.data as AuthTokens;
                setStoredTokens(newTokens);
                
                // Retry the original request with new token
                if (originalRequest.headers) {
                  originalRequest.headers.Authorization = `Bearer ${newTokens.access}`;
                }
                return this.client(originalRequest);
              }
            } catch (refreshError) {
              // Refresh failed, redirect to login
              removeStoredTokens();
              if (typeof window !== &apos;undefined&apos;) {
                window.location.href = &apos;/auth/login&apos;;
              }
            }
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private async refreshToken(refreshToken: string): Promise<unknown> {
    return this.client.post(&apos;/auth/refresh/&apos;, {
      refresh: refreshToken,
    });
  }

  async get<T = any>(url: string, config?: object): Promise<ApiResponse<T>> {
    try {
      return {
        success: true,
        data: response.data,
      };
    } catch (error: unknown) {
      return this.handleError(error);
    }
  }

  async post<T = any>(url: string, data?: unknown, config?: object): Promise<ApiResponse<T>> {
    try {
      return {
        success: true,
        data: response.data,
      };
    } catch (error: unknown) {
      return this.handleError(error);
    }
  }

  async put<T = any>(url: string, data?: unknown, config?: object): Promise<ApiResponse<T>> {
    try {
      return {
        success: true,
        data: response.data,
      };
    } catch (error: unknown) {
      return this.handleError(error);
    }
  }

  async patch<T = any>(url: string, data?: unknown, config?: object): Promise<ApiResponse<T>> {
    try {
      return {
        success: true,
        data: response.data,
      };
    } catch (error: unknown) {
      return this.handleError(error);
    }
  }

  async delete<T = any>(url: string, config?: object): Promise<ApiResponse<T>> {
    try {
      return {
        success: true,
        data: response.data,
      };
    } catch (error: unknown) {
      return this.handleError(error);
    }
  }

  private handleError(error: unknown): ApiResponse<never> {
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as any;
      if (axiosError.response) {
        // Server responded with error status
        return {
          success: false,
          error: {
            message: axiosError.response.data?.error?.message || axiosError.response.data?.message || 'An error occurred',
            code: axiosError.response.data?.error?.code || 'api_error',
            status_code: axiosError.response.status,
            details: axiosError.response.data?.error?.details || axiosError.response.data,
          },
        };
      } else if (axiosError.request) {
        // Network error
        return {
          success: false,
          error: {
            message: 'Network error. Please check your connection.',
            code: 'network_error',
            status_code: 0,
          },
        };
      }
    }
    
    // Other error
    const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred';
    return {
      success: false,
      error: {
        message: errorMessage,
        code: 'unknown_error',
        status_code: 0,
      },
    };
  }
}

// Create and export a singleton instance
export const apiClient = new ApiClient();

// Export individual methods for convenience