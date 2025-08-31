/**
 * Unit tests for Correlation ID Service
 */

import { CorrelationIdService, correlationIdService } from '../../services/correlationId';

// Mock uuid
jest.mock('uuid', () => ({
  v4: jest.fn(() => 'test-uuid-1234-5678-9012'),
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

// Mock console methods
const mockConsole = {
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};

Object.defineProperty(console, 'debug', { value: mockConsole.debug });
Object.defineProperty(console, 'info', { value: mockConsole.info });
Object.defineProperty(console, 'warn', { value: mockConsole.warn });
Object.defineProperty(console, 'error', { value: mockConsole.error });

describe('CorrelationIdService', () => {
  let service: CorrelationIdService;

  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks();
    mockSessionStorage.getItem.mockReturnValue(null);
    
    // Reset singleton instance
    (CorrelationIdService as any).instance = undefined;
    
    // Create new service instance
    service = CorrelationIdService.getInstance({
      generateOnPageLoad: false, // Disable auto-generation for tests
      persistInSession: true,
    });
  });

  describe('getInstance', () => {
    it('should return singleton instance', () => {
      const instance1 = CorrelationIdService.getInstance();
      const instance2 = CorrelationIdService.getInstance();
      
      expect(instance1).toBe(instance2);
    });
  });

  describe('generateNewCorrelationId', () => {
    it('should generate new correlation ID', () => {
      const correlationId = service.generateNewCorrelationId();
      
      expect(correlationId).toBe('test-uuid-1234-5678-9012');
      expect(mockSessionStorage.setItem).toHaveBeenCalledWith(
        'correlation_id',
        'test-uuid-1234-5678-9012'
      );
      expect(mockConsole.debug).toHaveBeenCalledWith(
        'Correlation ID set: test-uuid-1234-5678-9012'
      );
    });
  });

  describe('setCorrelationId', () => {
    it('should set valid correlation ID', () => {
      const validId = 'valid-correlation-id-123';
      
      service.setCorrelationId(validId);
      
      expect(service.getCorrelationId()).toBe(validId);
      expect(mockSessionStorage.setItem).toHaveBeenCalledWith('correlation_id', validId);
      expect(mockConsole.debug).toHaveBeenCalledWith(`Correlation ID set: ${validId}`);
    });

    it('should generate new ID for invalid correlation ID', () => {
      const invalidId = 'x'; // Too short
      
      service.setCorrelationId(invalidId);
      
      expect(service.getCorrelationId()).toBe('test-uuid-1234-5678-9012');
      expect(mockConsole.warn).toHaveBeenCalledWith(
        `Invalid correlation ID format: ${invalidId}. Generating new one.`
      );
    });

    it('should handle empty correlation ID', () => {
      service.setCorrelationId('');
      
      expect(service.getCorrelationId()).toBe('test-uuid-1234-5678-9012');
      expect(mockConsole.warn).toHaveBeenCalled();
    });
  });

  describe('getCorrelationId', () => {
    it('should return existing correlation ID', () => {
      service.setCorrelationId('existing-id');
      
      const result = service.getCorrelationId();
      
      expect(result).toBe('existing-id');
    });

    it('should generate new ID if none exists', () => {
      const result = service.getCorrelationId();
      
      expect(result).toBe('test-uuid-1234-5678-9012');
    });
  });

  describe('createChildCorrelationId', () => {
    it('should create child correlation ID with current parent', () => {
      service.setCorrelationId('parent-id');
      
      const childId = service.createChildCorrelationId();
      
      expect(childId).toBe('test-uuid-1234-5678-9012');
      expect(mockConsole.debug).toHaveBeenCalledWith(
        'Created child correlation ID: test-uuid-1234-5678-9012 for parent: parent-id'
      );
    });

    it('should create child correlation ID with explicit parent', () => {
      const parentId = 'explicit-parent-id';
      
      const childId = service.createChildCorrelationId(parentId);
      
      expect(childId).toBe('test-uuid-1234-5678-9012');
      expect(mockConsole.debug).toHaveBeenCalledWith(
        `Created child correlation ID: test-uuid-1234-5678-9012 for parent: ${parentId}`
      );
    });
  });

  describe('getHeaders', () => {
    it('should return headers with correlation ID', () => {
      service.setCorrelationId('test-correlation-id');
      
      const headers = service.getHeaders();
      
      expect(headers).toEqual({
        'X-Correlation-ID': 'test-correlation-id',
      });
    });
  });

  describe('addToHeaders', () => {
    it('should add correlation ID to existing headers', () => {
      service.setCorrelationId('test-correlation-id');
      const existingHeaders = { 'Content-Type': 'application/json' };
      
      const headers = service.addToHeaders(existingHeaders);
      
      expect(headers).toEqual({
        'Content-Type': 'application/json',
        'X-Correlation-ID': 'test-correlation-id',
      });
    });

    it('should add correlation ID to empty headers', () => {
      service.setCorrelationId('test-correlation-id');
      
      const headers = service.addToHeaders();
      
      expect(headers).toEqual({
        'X-Correlation-ID': 'test-correlation-id',
      });
    });
  });

  describe('clearCorrelationId', () => {
    it('should clear correlation ID', () => {
      service.setCorrelationId('test-id');
      
      service.clearCorrelationId();
      
      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('correlation_id');
    });
  });

  describe('logWithCorrelationId', () => {
    it('should log with correlation ID prefix', () => {
      service.setCorrelationId('test-correlation-id');
      
      service.logWithCorrelationId('info', 'Test message', { key: 'value' });
      
      expect(mockConsole.info).toHaveBeenCalledWith(
        '[test-correlation-id] Test message',
        { key: 'value' }
      );
    });

    it('should log error messages', () => {
      service.setCorrelationId('test-correlation-id');
      
      // Mock console.error directly for this test
      const originalError = console.error;
      console.error = jest.fn();
      
      service.logWithCorrelationId('error', 'Error message');
      
      expect(console.error).toHaveBeenCalledWith(
        '[test-correlation-id] Error message',
        undefined
      );
      
      // Restore original console.error
      console.error = originalError;
    });
  });

  describe('session storage integration', () => {
    it('should load correlation ID from session storage on initialization', () => {
      // Reset singleton
      (CorrelationIdService as any).instance = undefined;
      mockSessionStorage.getItem.mockReturnValue('stored-correlation-id');
      
      const newService = CorrelationIdService.getInstance({
        generateOnPageLoad: true,
        persistInSession: true,
      });
      
      expect(newService.getCorrelationId()).toBe('stored-correlation-id');
    });

    it('should generate new ID if stored ID is invalid', () => {
      // Reset singleton
      (CorrelationIdService as any).instance = undefined;
      mockSessionStorage.getItem.mockReturnValue('invalid'); // Too short
      
      const newService = CorrelationIdService.getInstance({
        generateOnPageLoad: true,
        persistInSession: true,
      });
      
      expect(newService.getCorrelationId()).toBe('test-uuid-1234-5678-9012');
    });

    it('should not persist when persistInSession is false', () => {
      // Reset singleton
      (CorrelationIdService as any).instance = undefined;
      
      const newService = CorrelationIdService.getInstance({
        generateOnPageLoad: false,
        persistInSession: false,
      });
      
      newService.setCorrelationId('test-id');
      
      expect(mockSessionStorage.setItem).not.toHaveBeenCalled();
    });
  });

  describe('validation', () => {
    it('should validate UUID format', () => {
      const validUuid = '123e4567-e89b-12d3-a456-426614174000';
      
      service.setCorrelationId(validUuid);
      
      expect(service.getCorrelationId()).toBe(validUuid);
      expect(mockConsole.warn).not.toHaveBeenCalled();
    });

    it('should validate alphanumeric format', () => {
      const validAlphanumeric = 'valid-correlation-id-123';
      
      service.setCorrelationId(validAlphanumeric);
      
      expect(service.getCorrelationId()).toBe(validAlphanumeric);
      expect(mockConsole.warn).not.toHaveBeenCalled();
    });

    it('should reject too short IDs', () => {
      service.setCorrelationId('short');
      
      expect(mockConsole.warn).toHaveBeenCalled();
    });

    it('should reject too long IDs', () => {
      const tooLong = 'a'.repeat(100);
      
      service.setCorrelationId(tooLong);
      
      expect(mockConsole.warn).toHaveBeenCalled();
    });

    it('should reject IDs with invalid characters', () => {
      service.setCorrelationId('invalid@#$%');
      
      expect(mockConsole.warn).toHaveBeenCalled();
    });
  });
});

describe('correlationIdService singleton', () => {
  it('should be available as singleton export', () => {
    expect(correlationIdService).toBeInstanceOf(CorrelationIdService);
  });
});

describe('utility functions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should export utility functions', () => {
    const {
      getCorrelationId,
      setCorrelationId,
      getCorrelationHeaders,
      addCorrelationToHeaders,
      createChildCorrelationId,
      logWithCorrelationId,
    } = require('../../services/correlationId');

    expect(typeof getCorrelationId).toBe('function');
    expect(typeof setCorrelationId).toBe('function');
    expect(typeof getCorrelationHeaders).toBe('function');
    expect(typeof addCorrelationToHeaders).toBe('function');
    expect(typeof createChildCorrelationId).toBe('function');
    expect(typeof logWithCorrelationId).toBe('function');
  });
});