/**
 * Unit tests for API Client with Correlation ID Integration
 */

// Mock axios first
jest.mock('axios');

// Mock correlation ID service
jest.mock('../../services/correlationId', () => ({
  correlationIdService: {
    getHeaders: jest.fn(),
    generateNewCorrelationId: jest.fn(),
    getCorrelationId: jest.fn(),
  },
  logWithCorrelationId: jest.fn(),
}));

import axios from 'axios';
import { ApiClient } from '../../services/apiClient';
import { correlationIdService } from '../../services/correlationId';

const mockedAxios = axios as jest.Mocked<typeof axios>;

const mockCorrelationIdService = correlationIdService as jest.Mocked<typeof correlationIdService>;
const mockLogWithCorrelationId = require('../../services/correlationId').logWithCorrelationId;

describe('ApiClient', () => {
  let apiClient: ApiClient;
  let mockAxiosInstance: any;

  beforeAll(() => {
    // Mock axios.create before any tests run
    mockAxiosInstance = {
      request: jest.fn(),
      interceptors: {
        request: {
          use: jest.fn(),
        },
        response: {
          use: jest.fn(),
        },
      },
      defaults: {
        headers: {
          common: {},
        },
        baseURL: '',
      },
    };

    mockedAxios.create.mockReturnValue(mockAxiosInstance);
  });

  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks();

    // Mock correlation ID service
    mockCorrelationIdService.getHeaders.mockReturnValue({
      'X-Correlation-ID': 'test-correlation-id',
    });
    mockCorrelationIdService.getCorrelationId.mockReturnValue('test-correlation-id');

    // Reset axios.create mock
    mockedAxios.create.mockReturnValue(mockAxiosInstance);

    // Create API client
    apiClient = new ApiClient({
      baseURL: 'https://api.example.com',
      enableLogging: true,
    });
  });

  describe('constructor', () => {
    it('should create axios instance with correct config', () => {
      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: 'https://api.example.com',
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });

    it('should setup interceptors', () => {
      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled();
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });

    it('should use custom config values', () => {
      const customClient = new ApiClient({
        baseURL: 'https://custom.api.com',
        timeout: 5000,
        defaultHeaders: { 'Custom-Header': 'value' },
        enableLogging: false,
      });

      expect(mockedAxios.create).toHaveBeenLastCalledWith({
        baseURL: 'https://custom.api.com',
        timeout: 5000,
        headers: {
          'Content-Type': 'application/json',
          'Custom-Header': 'value',
        },
      });
    });
  });

  describe('request interceptor', () => {
    let requestInterceptor: any;

    beforeEach(() => {
      // Get the request interceptor function
      const interceptorCall = mockAxiosInstance.interceptors.request.use.mock.calls[0];
      requestInterceptor = interceptorCall[0];
    });

    it('should add correlation ID to request headers', () => {
      const config = {
        method: 'GET',
        url: '/test',
        headers: {},
      };

      const result = requestInterceptor(config);

      expect(result.headers).toEqual({
        'X-Correlation-ID': 'test-correlation-id',
      });
    });

    it('should preserve existing headers', () => {
      const config = {
        method: 'POST',
        url: '/test',
        headers: {
          'Authorization': 'Bearer token',
        },
      };

      const result = requestInterceptor(config);

      expect(result.headers).toEqual({
        'Authorization': 'Bearer token',
        'X-Correlation-ID': 'test-correlation-id',
      });
    });

    it('should log request when logging is enabled', () => {
      const config = {
        method: 'POST',
        url: '/test',
        headers: {},
        data: { key: 'value' },
      };

      requestInterceptor(config);

      expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
        'debug',
        'API Request: POST /test',
        {
          headers: { 'X-Correlation-ID': 'test-correlation-id' },
          data: { key: 'value' },
        }
      );
    });
  });

  describe('response interceptor', () => {
    let responseInterceptor: any;
    let errorInterceptor: any;

    beforeEach(() => {
      // Get the response interceptor functions
      const interceptorCall = mockAxiosInstance.interceptors.response.use.mock.calls[0];
      responseInterceptor = interceptorCall[0];
      errorInterceptor = interceptorCall[1];
    });

    it('should log successful response', () => {
      const response = {
        status: 200,
        statusText: 'OK',
        headers: {
          'x-correlation-id': 'response-correlation-id',
        },
        config: {
          url: '/test',
        },
        data: { result: 'success' },
      };

      const result = responseInterceptor(response);

      expect(result).toBe(response);
      expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
        'debug',
        'API Response: 200 OK',
        {
          correlationId: 'response-correlation-id',
          url: '/test',
          data: { result: 'success' },
        }
      );
    });

    it('should handle response without correlation ID', () => {
      const response = {
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { url: '/test' },
        data: {},
      };

      responseInterceptor(response);

      expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
        'debug',
        'API Response: 200 OK',
        {
          correlationId: undefined,
          url: '/test',
          data: {},
        }
      );
    });

    it('should handle and transform errors', () => {
      const axiosError: any = {
        message: 'Request failed',
        name: 'AxiosError',
        config: { url: '/test' },
        response: {
          status: 400,
          statusText: 'Bad Request',
          headers: {
            'x-correlation-id': 'error-correlation-id',
          },
          data: { error: 'Invalid request' },
          config: {},
        },
        isAxiosError: true,
        toJSON: () => ({}),
      };

      expect(() => errorInterceptor(axiosError)).rejects.toEqual({
        message: 'Request failed',
        status: 400,
        statusText: 'Bad Request',
        correlationId: 'error-correlation-id',
        data: { error: 'Invalid request' },
      });

      expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
        'error',
        'API Error: 400',
        {
          correlationId: 'error-correlation-id',
          url: '/test',
          message: 'Request failed',
          data: { error: 'Invalid request' },
        }
      );
    });

    it('should handle network errors', () => {
      const networkError: any = {
        message: 'Network Error',
        name: 'AxiosError',
        config: { url: '/test' },
        isAxiosError: true,
        toJSON: () => ({}),
      };

      expect(() => errorInterceptor(networkError)).rejects.toEqual({
        message: 'Network Error',
        status: undefined,
        statusText: undefined,
        correlationId: undefined,
        data: undefined,
      });

      expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
        'error',
        'API Error: Network Error',
        {
          correlationId: undefined,
          url: '/test',
          message: 'Network Error',
          data: undefined,
        }
      );
    });
  });

  describe('HTTP methods', () => {
    beforeEach(() => {
      mockAxiosInstance.request.mockResolvedValue({
        data: { result: 'success' },
        status: 200,
        statusText: 'OK',
        headers: { 'x-correlation-id': 'test-correlation-id' },
      });
    });

    it('should make GET request', async () => {
      const response = await apiClient.get('/test');

      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'GET',
        url: '/test',
      });

      expect(response).toEqual({
        data: { result: 'success' },
        status: 200,
        statusText: 'OK',
        headers: { 'x-correlation-id': 'test-correlation-id' },
        correlationId: 'test-correlation-id',
      });
    });

    it('should make POST request with data', async () => {
      const postData = { key: 'value' };
      
      await apiClient.post('/test', postData);

      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'POST',
        url: '/test',
        data: postData,
      });
    });

    it('should make PUT request', async () => {
      const putData = { id: 1, name: 'updated' };
      
      await apiClient.put('/test/1', putData);

      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'PUT',
        url: '/test/1',
        data: putData,
      });
    });

    it('should make PATCH request', async () => {
      const patchData = { name: 'patched' };
      
      await apiClient.patch('/test/1', patchData);

      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'PATCH',
        url: '/test/1',
        data: patchData,
      });
    });

    it('should make DELETE request', async () => {
      await apiClient.delete('/test/1');

      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'DELETE',
        url: '/test/1',
      });
    });
  });

  describe('file upload', () => {
    it('should upload file with correlation ID', async () => {
      const mockFile = new File(['content'], 'test.txt', { type: 'text/plain' });
      const mockOnProgress = jest.fn();

      mockAxiosInstance.request.mockResolvedValue({
        data: { fileId: 'uploaded-file-id' },
        status: 201,
        statusText: 'Created',
        headers: {},
      });

      await apiClient.uploadFile('/upload', mockFile, mockOnProgress);

      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'POST',
        url: '/upload',
        data: expect.any(FormData),
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: expect.any(Function),
      });
    });
  });

  describe('authentication', () => {
    it('should set auth token', () => {
      apiClient.setAuthToken('test-token');

      expect(mockAxiosInstance.defaults.headers.common['Authorization']).toBe('Bearer test-token');
    });

    it('should remove auth token', () => {
      mockAxiosInstance.defaults.headers.common['Authorization'] = 'Bearer test-token';
      
      apiClient.removeAuthToken();

      expect(mockAxiosInstance.defaults.headers.common['Authorization']).toBeUndefined();
    });
  });

  describe('base URL', () => {
    it('should update base URL', () => {
      apiClient.setBaseURL('https://new-api.example.com');

      expect(mockAxiosInstance.defaults.baseURL).toBe('https://new-api.example.com');
    });
  });

  describe('correlation ID methods', () => {
    it('should get current correlation ID', () => {
      const correlationId = apiClient.getCurrentCorrelationId();

      expect(correlationId).toBe('test-correlation-id');
      expect(mockCorrelationIdService.getCorrelationId).toHaveBeenCalled();
    });

    it('should generate new correlation ID', () => {
      mockCorrelationIdService.generateNewCorrelationId.mockReturnValue('new-correlation-id');

      const correlationId = apiClient.generateNewCorrelationId();

      expect(correlationId).toBe('new-correlation-id');
      expect(mockCorrelationIdService.generateNewCorrelationId).toHaveBeenCalled();
    });
  });
});