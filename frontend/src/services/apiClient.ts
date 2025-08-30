/**
 * API Client with Correlation ID Integration
 * 
 * This service provides a centralized API client that automatically
 * includes correlation IDs in all requests for end-to-end tracing.
 */

import axios from 'axios';
import { correlationIdService, logWithCorrelationId } from './correlationId';

export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  defaultHeaders?: Record<string, string>;
  enableLogging?: boolean;
  enableRetry?: boolean;
  maxRetries?: number;
}

export interface ApiResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
  correlationId?: string;
}

export interface ApiError {
  message: string;
  status?: number;
  statusText?: string;
  correlationId?: string;
  data?: any;
}

export class ApiClient {
  private axiosInstance: any;
  private config: Required<ApiClientConfig>;

  constructor(config: ApiClientConfig) {
    this.config = {
      timeout: 30000,
      defaultHeaders: {},
      enableLogging: true,
      enableRetry: true,
      maxRetries: 3,
      ...config,
    };

    this.axiosInstance = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
        ...this.config.defaultHeaders,
      },
    });

    this.setupInterceptors();
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor - add correlation ID and log requests
    this.axiosInstance.interceptors.request.use(
      (config: any) => {
        // Add correlation ID to headers
        const correlationHeaders = correlationIdService.getHeaders();
        config.headers = {
          ...config.headers,
          ...correlationHeaders,
        };

        // Log request if enabled
        if (this.config.enableLogging) {
          logWithCorrelationId('debug', `API Request: ${config.method?.toUpperCase()} ${config.url}`, {
            headers: config.headers,
            data: config.data,
          });
        }

        return config;
      },
      (error: any) => {
        if (this.config.enableLogging) {
          logWithCorrelationId('error', 'API Request Error', error);
        }
        return Promise.reject(error);
      }
    );

    // Response interceptor - log responses and handle errors
    this.axiosInstance.interceptors.response.use(
      (response: any) => {
        // Extract correlation ID from response headers
        const correlationId = response.headers['x-correlation-id'] || 
                             response.headers['X-Correlation-ID'];

        // Log response if enabled
        if (this.config.enableLogging) {
          logWithCorrelationId('debug', `API Response: ${response.status} ${response.statusText}`, {
            correlationId,
            url: response.config.url,
            data: response.data,
          });
        }

        return response;
      },
      (error: any) => {
        // Extract correlation ID from error response
        const correlationId = error.response?.headers?.['x-correlation-id'] || 
                             error.response?.headers?.['X-Correlation-ID'];

        // Log error if enabled
        if (this.config.enableLogging) {
          logWithCorrelationId('error', `API Error: ${error.response?.status || 'Network Error'}`, {
            correlationId,
            url: error.config?.url,
            message: error.message,
            data: error.response?.data,
          });
        }

        // Transform error for consistent handling
        const apiError: ApiError = {
          message: error.message,
          status: error.response?.status,
          statusText: error.response?.statusText,
          correlationId,
          data: error.response?.data,
        };

        return Promise.reject(apiError);
      }
    );
  }

  /**
   * Generic request method
   */
  private async request<T = any>(config: any): Promise<ApiResponse<T>> {
    try {
      const response = await this.axiosInstance.request(config);
      
      return {
        data: response.data,
        status: response.status,
        statusText: response.statusText,
        headers: response.headers as Record<string, string>,
        correlationId: response.headers['x-correlation-id'] || response.headers['X-Correlation-ID'],
      };
    } catch (error) {
      throw error; // Re-throw the transformed error from interceptor
    }
  }

  /**
   * GET request
   */
  public async get<T = any>(url: string, config?: any): Promise<ApiResponse<T>> {
    return this.request<T>({
      method: 'GET',
      url,
      ...config,
    });
  }

  /**
   * POST request
   */
  public async post<T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> {
    return this.request<T>({
      method: 'POST',
      url,
      data,
      ...config,
    });
  }

  /**
   * PUT request
   */
  public async put<T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> {
    return this.request<T>({
      method: 'PUT',
      url,
      data,
      ...config,
    });
  }

  /**
   * PATCH request
   */
  public async patch<T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> {
    return this.request<T>({
      method: 'PATCH',
      url,
      data,
      ...config,
    });
  }

  /**
   * DELETE request
   */
  public async delete<T = any>(url: string, config?: any): Promise<ApiResponse<T>> {
    return this.request<T>({
      method: 'DELETE',
      url,
      ...config,
    });
  }

  /**
   * Upload file with correlation ID
   */
  public async uploadFile<T = any>(
    url: string, 
    file: File, 
    onProgress?: (progress: number) => void,
    config?: any
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<T>({
      method: 'POST',
      url,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent: any) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
      ...config,
    });
  }

  /**
   * Set authentication token
   */
  public setAuthToken(token: string): void {
    this.axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  /**
   * Remove authentication token
   */
  public removeAuthToken(): void {
    delete this.axiosInstance.defaults.headers.common['Authorization'];
  }

  /**
   * Update base URL
   */
  public setBaseURL(baseURL: string): void {
    this.axiosInstance.defaults.baseURL = baseURL;
  }

  /**
   * Get current correlation ID
   */
  public getCurrentCorrelationId(): string {
    return correlationIdService.getCorrelationId();
  }

  /**
   * Create a new correlation ID for the next request
   */
  public generateNewCorrelationId(): string {
    return correlationIdService.generateNewCorrelationId();
  }
}

// Create default API client instance
const createDefaultApiClient = () => new ApiClient({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api',
  enableLogging: process.env.NODE_ENV === 'development',
});

export default createDefaultApiClient;