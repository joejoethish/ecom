/**
 * Integration tests for Correlation ID system
 */

import { renderHook, act } from '@testing-library/react';
import { correlationIdService } from '../../services/correlationId';
import { ApiClient } from '../../services/apiClient';
import { useCorrelationId } from '../../hooks/useCorrelationId';

// Mock uuid
jest.mock('uuid', () => ({
  v4: jest.fn(() => 'integration-test-uuid-1234'),
}));

// Mock sessionStorage
const mockSessionStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage,
});

// Mock axios
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    request: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
    defaults: {
      headers: { common: {} },
      baseURL: '',
    },
  })),
}));

describe('Correlation ID Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSessionStorage.getItem.mockReturnValue(null);
    
    // Reset correlation ID service singleton
    (correlationIdService.constructor as any).instance = undefined;
  });

  describe('End-to-End Correlation Flow', () => {
    it('should maintain correlation ID across service, API client, and React hooks', () => {
      // 1. Start with correlation ID service
      const initialId = correlationIdService.generateNewCorrelationId();
      expect(initialId).toBe('integration-test-uuid-1234');

      // 2. Verify API client gets the same correlation ID
      const apiClient = new ApiClient({
        baseURL: 'https://api.example.com',
        enableLogging: false,
      });

      const apiCorrelationId = apiClient.getCurrentCorrelationId();
      expect(apiCorrelationId).toBe(initialId);

      // 3. Verify React hook gets the same correlation ID
      const { result } = renderHook(() => useCorrelationId());
      expect(result.current.correlationId).toBe(initialId);

      // 4. Generate new ID from hook and verify propagation
      act(() => {
        result.current.generateNewId();
      });

      const newId = result.current.correlationId;
      expect(newId).toBe('integration-test-uuid-1234');
      expect(correlationIdService.getCorrelationId()).toBe(newId);
      expect(apiClient.getCurrentCorrelationId()).toBe(newId);
    });

    it('should create and track child correlation IDs', () => {
      // Set parent correlation ID
      const parentId = 'parent-correlation-id';
      correlationIdService.setCorrelationId(parentId);

      // Create child ID through service
      const childId1 = correlationIdService.createChildCorrelationId();
      expect(childId1).toBe('integration-test-uuid-1234');

      // Create child ID through React hook
      const { result } = renderHook(() => useCorrelationId());
      
      let childId2: string;
      act(() => {
        childId2 = result.current.createChildId();
      });

      expect(childId2!).toBe('integration-test-uuid-1234');
      
      // Verify parent ID is still preserved
      expect(correlationIdService.getCorrelationId()).toBe(parentId);
    });

    it('should handle correlation ID headers in API client', () => {
      const testId = 'test-api-correlation-id';
      correlationIdService.setCorrelationId(testId);

      const headers = correlationIdService.getHeaders();
      expect(headers).toEqual({
        'X-Correlation-ID': testId,
      });

      const existingHeaders = { 'Content-Type': 'application/json' };
      const combinedHeaders = correlationIdService.addToHeaders(existingHeaders);
      expect(combinedHeaders).toEqual({
        'Content-Type': 'application/json',
        'X-Correlation-ID': testId,
      });
    });

    it('should persist correlation ID in session storage', () => {
      const testId = 'persistent-correlation-id';
      
      correlationIdService.setCorrelationId(testId);
      
      expect(mockSessionStorage.setItem).toHaveBeenCalledWith(
        'correlation_id',
        testId
      );
    });

    it('should load correlation ID from session storage on initialization', () => {
      const storedId = 'stored-correlation-id';
      mockSessionStorage.getItem.mockReturnValue(storedId);

      // Reset singleton to trigger initialization
      (correlationIdService.constructor as any).instance = undefined;
      
      // Create new service instance that should load from storage
      const newService = (correlationIdService.constructor as any).getInstance({
        generateOnPageLoad: true,
        persistInSession: true,
      });

      expect(newService.getCorrelationId()).toBe(storedId);
    });
  });

  describe('User Interaction Tracking', () => {
    it('should track page views with correlation ID', () => {
      const consoleSpy = jest.spyOn(console, 'info').mockImplementation();
      
      const { result } = renderHook(() => 
        useCorrelationId({ logInteractions: true })
      );

      act(() => {
        result.current.logInteraction('page_view', {
          page: '/dashboard',
          timestamp: '2023-01-01T00:00:00Z',
        });
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('[integration-test-uuid-1234] User interaction: page_view'),
        expect.objectContaining({
          action: 'page_view',
          data: {
            page: '/dashboard',
            timestamp: '2023-01-01T00:00:00Z',
          },
        })
      );

      consoleSpy.mockRestore();
    });

    it('should track form interactions with correlation ID', () => {
      const consoleSpy = jest.spyOn(console, 'info').mockImplementation();
      
      const { result } = renderHook(() => 
        useCorrelationId({ logInteractions: true })
      );

      act(() => {
        result.current.logInteraction('form_submit', {
          formName: 'loginForm',
          fields: ['username', 'password'],
        });
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('[integration-test-uuid-1234] User interaction: form_submit'),
        expect.objectContaining({
          action: 'form_submit',
          data: {
            formName: 'loginForm',
            fields: ['username', 'password'],
          },
        })
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle invalid correlation IDs gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      
      // Try to set invalid correlation ID
      correlationIdService.setCorrelationId('x'); // Too short
      
      // Should generate new valid ID
      expect(correlationIdService.getCorrelationId()).toBe('integration-test-uuid-1234');
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Invalid correlation ID format')
      );

      consoleSpy.mockRestore();
    });

    it('should clear correlation ID properly', () => {
      const testId = 'test-clear-id';
      correlationIdService.setCorrelationId(testId);
      
      expect(correlationIdService.getCorrelationId()).toBe(testId);
      
      correlationIdService.clearCorrelationId();
      
      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('correlation_id');
    });

    it('should work without session storage', () => {
      // Reset singleton with session storage disabled
      (correlationIdService.constructor as any).instance = undefined;
      
      const newService = (correlationIdService.constructor as any).getInstance({
        generateOnPageLoad: false,
        persistInSession: false,
      });

      const testId = 'no-persist-id';
      newService.setCorrelationId(testId);
      
      expect(newService.getCorrelationId()).toBe(testId);
      expect(mockSessionStorage.setItem).not.toHaveBeenCalled();
    });
  });

  describe('Performance and Memory', () => {
    it('should maintain singleton pattern', () => {
      const instance1 = (correlationIdService.constructor as any).getInstance();
      const instance2 = (correlationIdService.constructor as any).getInstance();
      
      expect(instance1).toBe(instance2);
    });

    it('should handle rapid correlation ID changes', () => {
      const ids: string[] = [];
      
      for (let i = 0; i < 10; i++) {
        const id = correlationIdService.generateNewCorrelationId();
        ids.push(id);
      }
      
      // All IDs should be the same due to mocked uuid
      expect(ids.every(id => id === 'integration-test-uuid-1234')).toBe(true);
      expect(ids.length).toBe(10);
    });
  });
});