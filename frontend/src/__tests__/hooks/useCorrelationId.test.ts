/**
 * Unit tests for useCorrelationId hooks
 */

import { renderHook, act } from '@testing-library/react';
import {
  useCorrelationId,
  usePageTracking,
  useFormTracking,
  useApiTracking,
} from '../../hooks/useCorrelationId';
import { correlationIdService, logWithCorrelationId } from '../../services/correlationId';

// Mock correlation ID service
jest.mock('../../services/correlationId', () => ({
  correlationIdService: {
    getCorrelationId: jest.fn(),
    generateNewCorrelationId: jest.fn(),
    createChildCorrelationId: jest.fn(),
    setCorrelationId: jest.fn(),
  },
  logWithCorrelationId: jest.fn(),
}));

const mockCorrelationIdService = correlationIdService as jest.Mocked<typeof correlationIdService>;
const mockLogWithCorrelationId = logWithCorrelationId as jest.MockedFunction<typeof logWithCorrelationId>;

// Mock window.location
const mockLocation = {
  href: 'https://example.com/test-page',
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

describe('useCorrelationId', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCorrelationIdService.getCorrelationId.mockReturnValue('test-correlation-id');
  });

  it('should return correlation ID and utility functions', () => {
    const { result } = renderHook(() => useCorrelationId());

    expect(result.current.correlationId).toBe('test-correlation-id');
    expect(typeof result.current.generateNewId).toBe('function');
    expect(typeof result.current.createChildId).toBe('function');
    expect(typeof result.current.setCorrelationId).toBe('function');
    expect(typeof result.current.logInteraction).toBe('function');
  });

  it('should generate new correlation ID on mount when enabled', () => {
    renderHook(() => useCorrelationId({ generateOnMount: true, logInteractions: true }));

    expect(mockCorrelationIdService.getCorrelationId).toHaveBeenCalled();
    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'debug',
      'Component mounted with correlation ID',
      { correlationId: 'test-correlation-id' }
    );
  });

  it('should not log on mount when logging is disabled', () => {
    renderHook(() => useCorrelationId({ generateOnMount: true, logInteractions: false }));

    expect(mockLogWithCorrelationId).not.toHaveBeenCalled();
  });

  it('should generate new correlation ID', () => {
    mockCorrelationIdService.generateNewCorrelationId.mockReturnValue('new-correlation-id');
    
    const { result } = renderHook(() => useCorrelationId({ logInteractions: true }));

    act(() => {
      const newId = result.current.generateNewId();
      expect(newId).toBe('new-correlation-id');
    });

    expect(mockCorrelationIdService.generateNewCorrelationId).toHaveBeenCalled();
    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'debug',
      'Generated new correlation ID',
      { correlationId: 'new-correlation-id' }
    );
  });

  it('should create child correlation ID', () => {
    mockCorrelationIdService.createChildCorrelationId.mockReturnValue('child-correlation-id');
    
    const { result } = renderHook(() => useCorrelationId({ logInteractions: true }));

    act(() => {
      const childId = result.current.createChildId();
      expect(childId).toBe('child-correlation-id');
    });

    expect(mockCorrelationIdService.createChildCorrelationId).toHaveBeenCalledWith(undefined);
    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'debug',
      'Created child correlation ID',
      {
        parentId: 'test-correlation-id',
        childId: 'child-correlation-id',
      }
    );
  });

  it('should create child correlation ID with explicit parent', () => {
    mockCorrelationIdService.createChildCorrelationId.mockReturnValue('child-correlation-id');
    
    const { result } = renderHook(() => useCorrelationId({ logInteractions: true }));

    act(() => {
      const childId = result.current.createChildId('explicit-parent-id');
      expect(childId).toBe('child-correlation-id');
    });

    expect(mockCorrelationIdService.createChildCorrelationId).toHaveBeenCalledWith('explicit-parent-id');
    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'debug',
      'Created child correlation ID',
      {
        parentId: 'explicit-parent-id',
        childId: 'child-correlation-id',
      }
    );
  });

  it('should set correlation ID', () => {
    const { result } = renderHook(() => useCorrelationId({ logInteractions: true }));

    act(() => {
      result.current.setCorrelationId('new-id');
    });

    expect(mockCorrelationIdService.setCorrelationId).toHaveBeenCalledWith('new-id');
    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'debug',
      'Correlation ID updated',
      { correlationId: 'new-id' }
    );
  });

  it('should log user interactions', () => {
    const { result } = renderHook(() => useCorrelationId({ logInteractions: true }));

    act(() => {
      result.current.logInteraction('button_click', { buttonId: 'submit' });
    });

    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'info',
      'User interaction: button_click',
      {
        action: 'button_click',
        data: { buttonId: 'submit' },
        timestamp: expect.any(String),
      }
    );
  });

  it('should not log interactions when disabled', () => {
    const { result } = renderHook(() => useCorrelationId({ logInteractions: false }));

    act(() => {
      result.current.logInteraction('button_click');
    });

    expect(mockLogWithCorrelationId).not.toHaveBeenCalled();
  });
});

describe('usePageTracking', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCorrelationIdService.getCorrelationId.mockReturnValue('page-correlation-id');
  });

  it('should track page view on mount', () => {
    renderHook(() => usePageTracking('HomePage'));

    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'info',
      'User interaction: page_view',
      {
        action: 'page_view',
        data: {
          pageName: 'HomePage',
          url: 'https://example.com/test-page',
          timestamp: expect.any(String),
        },
        timestamp: expect.any(String),
      }
    );
  });

  it('should return correlation ID and log function', () => {
    const { result } = renderHook(() => usePageTracking('HomePage'));

    expect(result.current.correlationId).toBe('page-correlation-id');
    expect(typeof result.current.logInteraction).toBe('function');
  });

  it('should track page view when page name changes', () => {
    const { rerender } = renderHook(
      ({ pageName }) => usePageTracking(pageName),
      { initialProps: { pageName: 'HomePage' } }
    );

    // Clear previous calls
    mockLogWithCorrelationId.mockClear();

    rerender({ pageName: 'AboutPage' });

    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'info',
      'User interaction: page_view',
      {
        action: 'page_view',
        data: {
          pageName: 'AboutPage',
          url: 'https://example.com/test-page',
          timestamp: expect.any(String),
        },
        timestamp: expect.any(String),
      }
    );
  });
});

describe('useFormTracking', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCorrelationIdService.getCorrelationId.mockReturnValue('form-correlation-id');
  });

  it('should return form tracking functions', () => {
    const { result } = renderHook(() => useFormTracking('LoginForm'));

    expect(result.current.correlationId).toBe('form-correlation-id');
    expect(typeof result.current.trackFormStart).toBe('function');
    expect(typeof result.current.trackFormSubmit).toBe('function');
    expect(typeof result.current.trackFormError).toBe('function');
    expect(typeof result.current.trackFieldChange).toBe('function');
    expect(typeof result.current.logInteraction).toBe('function');
  });

  it('should track form start', () => {
    const { result } = renderHook(() => useFormTracking('LoginForm'));

    act(() => {
      result.current.trackFormStart();
    });

    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'info',
      'User interaction: form_start',
      {
        action: 'form_start',
        data: {
          formName: 'LoginForm',
          timestamp: expect.any(String),
        },
        timestamp: expect.any(String),
      }
    );
  });

  it('should track form submit', () => {
    const { result } = renderHook(() => useFormTracking('LoginForm'));

    act(() => {
      result.current.trackFormSubmit({ username: 'test', password: '***' });
    });

    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'info',
      'User interaction: form_submit',
      {
        action: 'form_submit',
        data: {
          formName: 'LoginForm',
          data: { username: 'test', password: '***' },
          timestamp: expect.any(String),
        },
        timestamp: expect.any(String),
      }
    );
  });

  it('should track form error', () => {
    const { result } = renderHook(() => useFormTracking('LoginForm'));

    act(() => {
      result.current.trackFormError(new Error('Validation failed'));
    });

    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'info',
      'User interaction: form_error',
      {
        action: 'form_error',
        data: {
          formName: 'LoginForm',
          error: 'Validation failed',
          timestamp: expect.any(String),
        },
        timestamp: expect.any(String),
      }
    );
  });

  it('should track field change', () => {
    const { result } = renderHook(() => useFormTracking('LoginForm'));

    act(() => {
      result.current.trackFieldChange('username', 'testuser');
    });

    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'info',
      'User interaction: field_change',
      {
        action: 'field_change',
        data: {
          formName: 'LoginForm',
          fieldName: 'username',
          value: 'testuser',
          timestamp: expect.any(String),
        },
        timestamp: expect.any(String),
      }
    );
  });

  it('should truncate long field values', () => {
    const { result } = renderHook(() => useFormTracking('LoginForm'));
    const longValue = 'a'.repeat(150);

    act(() => {
      result.current.trackFieldChange('description', longValue);
    });

    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'info',
      'User interaction: field_change',
      {
        action: 'field_change',
        data: {
          formName: 'LoginForm',
          fieldName: 'description',
          value: longValue.substring(0, 100),
          timestamp: expect.any(String),
        },
        timestamp: expect.any(String),
      }
    );
  });
});

describe('useApiTracking', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCorrelationIdService.getCorrelationId.mockReturnValue('api-correlation-id');
  });

  it('should return API tracking functions', () => {
    const { result } = renderHook(() => useApiTracking());

    expect(result.current.correlationId).toBe('api-correlation-id');
    expect(typeof result.current.trackApiCall).toBe('function');
    expect(typeof result.current.trackApiSuccess).toBe('function');
    expect(typeof result.current.trackApiError).toBe('function');
    expect(typeof result.current.logInteraction).toBe('function');
  });

  it('should track API call start', () => {
    const { result } = renderHook(() => useApiTracking());

    act(() => {
      result.current.trackApiCall('POST', '/api/users', { name: 'John' });
    });

    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'info',
      'User interaction: api_call_start',
      {
        action: 'api_call_start',
        data: {
          method: 'POST',
          url: '/api/users',
          data: { name: 'John' },
          timestamp: expect.any(String),
        },
        timestamp: expect.any(String),
      }
    );
  });

  it('should track API call success', () => {
    const { result } = renderHook(() => useApiTracking());

    act(() => {
      result.current.trackApiSuccess('GET', '/api/users', { status: 200 });
    });

    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'info',
      'User interaction: api_call_success',
      {
        action: 'api_call_success',
        data: {
          method: 'GET',
          url: '/api/users',
          status: 200,
          timestamp: expect.any(String),
        },
        timestamp: expect.any(String),
      }
    );
  });

  it('should track API call error', () => {
    const { result } = renderHook(() => useApiTracking());

    act(() => {
      result.current.trackApiError('POST', '/api/users', {
        message: 'Validation failed',
        status: 400,
      });
    });

    expect(mockLogWithCorrelationId).toHaveBeenCalledWith(
      'info',
      'User interaction: api_call_error',
      {
        action: 'api_call_error',
        data: {
          method: 'POST',
          url: '/api/users',
          error: 'Validation failed',
          status: 400,
          timestamp: expect.any(String),
        },
        timestamp: expect.any(String),
      }
    );
  });
});