/**
 * React Hook for Correlation ID Management
 * 
 * This hook provides React components with correlation ID functionality
 * for tracking user interactions and API calls.
 */

import { useCallback, useEffect, useState } from 'react';
import { correlationIdService, logWithCorrelationId } from '../services/correlationId';

export interface UseCorrelationIdOptions {
  generateOnMount?: boolean;
  logInteractions?: boolean;
  persistInSession?: boolean;
}

export interface UseCorrelationIdReturn {
  correlationId: string;
  generateNewId: () => string;
  createChildId: (parentId?: string) => string;
  logInteraction: (action: string, data?: any) => void;
  setCorrelationId: (id: string) => void;
}

/**
 * Hook for managing correlation IDs in React components
 */
export const useCorrelationId = (options: UseCorrelationIdOptions = {}): UseCorrelationIdReturn => {
  const {
    generateOnMount = true,
    logInteractions = true,
    persistInSession = true,
  } = options;

  const [correlationId, setCorrelationIdState] = useState<string>(() => {
    return correlationIdService.getCorrelationId();
  });

  // Initialize correlation ID on mount
  useEffect(() => {
    if (generateOnMount) {
      const currentId = correlationIdService.getCorrelationId();
      setCorrelationIdState(currentId);
      
      if (logInteractions) {
        logWithCorrelationId('debug', 'Component mounted with correlation ID', {
          correlationId: currentId,
        });
      }
    }
  }, [generateOnMount, logInteractions]);

  // Generate new correlation ID
  const generateNewId = useCallback((): string => {
    const newId = correlationIdService.generateNewCorrelationId();
    setCorrelationIdState(newId);
    
    if (logInteractions) {
      logWithCorrelationId('debug', 'Generated new correlation ID', {
        correlationId: newId,
      });
    }
    
    return newId;
  }, [logInteractions]);

  // Create child correlation ID
  const createChildId = useCallback((parentId?: string): string => {
    const childId = correlationIdService.createChildCorrelationId(parentId);
    
    if (logInteractions) {
      logWithCorrelationId('debug', 'Created child correlation ID', {
        parentId: parentId || correlationId,
        childId,
      });
    }
    
    return childId;
  }, [correlationId, logInteractions]);

  // Set correlation ID
  const setCorrelationId = useCallback((id: string): void => {
    correlationIdService.setCorrelationId(id);
    setCorrelationIdState(id);
    
    if (logInteractions) {
      logWithCorrelationId('debug', 'Correlation ID updated', {
        correlationId: id,
      });
    }
  }, [logInteractions]);

  // Log user interaction with correlation ID
  const logInteraction = useCallback((action: string, data?: any): void => {
    if (logInteractions) {
      logWithCorrelationId('info', `User interaction: ${action}`, {
        action,
        data,
        timestamp: new Date().toISOString(),
      });
    }
  }, [logInteractions]);

  return {
    correlationId,
    generateNewId,
    createChildId,
    setCorrelationId,
    logInteraction,
  };
};

/**
 * Hook for tracking page views with correlation ID
 */
export const usePageTracking = (pageName: string, options: UseCorrelationIdOptions = {}) => {
  const { correlationId, logInteraction } = useCorrelationId(options);

  useEffect(() => {
    logInteraction('page_view', {
      pageName,
      url: typeof window !== 'undefined' ? window.location.href : '',
      timestamp: new Date().toISOString(),
    });
  }, [pageName, logInteraction]);

  return { correlationId, logInteraction };
};

/**
 * Hook for tracking form interactions with correlation ID
 */
export const useFormTracking = (formName: string, options: UseCorrelationIdOptions = {}) => {
  const { correlationId, logInteraction } = useCorrelationId(options);

  const trackFormStart = useCallback(() => {
    logInteraction('form_start', {
      formName,
      timestamp: new Date().toISOString(),
    });
  }, [formName, logInteraction]);

  const trackFormSubmit = useCallback((data?: any) => {
    logInteraction('form_submit', {
      formName,
      data,
      timestamp: new Date().toISOString(),
    });
  }, [formName, logInteraction]);

  const trackFormError = useCallback((error: any) => {
    logInteraction('form_error', {
      formName,
      error: error.message || error,
      timestamp: new Date().toISOString(),
    });
  }, [formName, logInteraction]);

  const trackFieldChange = useCallback((fieldName: string, value: any) => {
    logInteraction('field_change', {
      formName,
      fieldName,
      value: typeof value === 'string' ? value.substring(0, 100) : value, // Truncate long values
      timestamp: new Date().toISOString(),
    });
  }, [formName, logInteraction]);

  return {
    correlationId,
    trackFormStart,
    trackFormSubmit,
    trackFormError,
    trackFieldChange,
    logInteraction,
  };
};

/**
 * Hook for tracking API calls with correlation ID
 */
export const useApiTracking = (options: UseCorrelationIdOptions = {}) => {
  const { correlationId, logInteraction } = useCorrelationId(options);

  const trackApiCall = useCallback((method: string, url: string, data?: any) => {
    logInteraction('api_call_start', {
      method,
      url,
      data,
      timestamp: new Date().toISOString(),
    });
  }, [logInteraction]);

  const trackApiSuccess = useCallback((method: string, url: string, response?: any) => {
    logInteraction('api_call_success', {
      method,
      url,
      status: response?.status,
      timestamp: new Date().toISOString(),
    });
  }, [logInteraction]);

  const trackApiError = useCallback((method: string, url: string, error: any) => {
    logInteraction('api_call_error', {
      method,
      url,
      error: error.message || error,
      status: error.status,
      timestamp: new Date().toISOString(),
    });
  }, [logInteraction]);

  return {
    correlationId,
    trackApiCall,
    trackApiSuccess,
    trackApiError,
    logInteraction,
  };
};