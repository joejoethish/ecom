/**
 * Custom hook for form error handling with authentication integration
 */
import { useState, useCallback } from 'react';
import { AuthErrorHandler, FormErrorHandler, NotificationErrorHandler } from '@/utils/AuthErrorHandler';

export interface UseFormErrorHandlingOptions {
  showNotifications?: boolean;
  clearOnChange?: boolean;
  onError?: (error: any) => void;
  onSuccess?: () => void;
}

export interface FormErrorState {
  fieldErrors: Record<string, string>;
  generalError: string | null;
  hasErrors: boolean;
  isSubmitting: boolean;
}

export function useFormErrorHandling(options: UseFormErrorHandlingOptions = {}) {
  const {
    showNotifications = true,
    clearOnChange = true,
    onError,
    onSuccess,
  } = options;

  const [errorState, setErrorState] = useState<FormErrorState>({
    fieldErrors: {},
    generalError: null,
    hasErrors: false,
    isSubmitting: false,
  });

  const clearErrors = useCallback(() => {
    setErrorState({
      fieldErrors: {},
      generalError: null,
      hasErrors: false,
      isSubmitting: false,
    });
  }, []);

  const clearFieldError = useCallback((fieldName: string) => {
    setErrorState(prev => ({
      ...prev,
      fieldErrors: {
        ...prev.fieldErrors,
        [fieldName]: '',
      },
      hasErrors: Object.keys(prev.fieldErrors).some(key => key !== fieldName && prev.fieldErrors[key]) || !!prev.generalError,
    }));
  }, []);

  const setFieldError = useCallback((fieldName: string, error: string) => {
    setErrorState(prev => ({
      ...prev,
      fieldErrors: {
        ...prev.fieldErrors,
        [fieldName]: error,
      },
      hasErrors: true,
    }));
  }, []);

  const handleError = useCallback((error: any) => {
    const fieldErrors = FormErrorHandler.processFormErrors(error);
    const generalError = FormErrorHandler.getGeneralError(error);

    setErrorState({
      fieldErrors,
      generalError,
      hasErrors: Object.keys(fieldErrors).length > 0 || !!generalError,
      isSubmitting: false,
    });

    if (showNotifications && generalError) {
      NotificationErrorHandler.showError(error);
    }

    if (onError) {
      onError(error);
    }
  }, [showNotifications, onError]);

  const handleSuccess = useCallback((message?: string) => {
    clearErrors();
    
    if (showNotifications && message) {
      NotificationErrorHandler.showSuccess(message);
    }

    if (onSuccess) {
      onSuccess();
    }
  }, [clearErrors, showNotifications, onSuccess]);

  const setSubmitting = useCallback((isSubmitting: boolean) => {
    setErrorState(prev => ({
      ...prev,
      isSubmitting,
    }));
  }, []);

  const handleFieldChange = useCallback((fieldName: string) => {
    if (clearOnChange && errorState.fieldErrors[fieldName]) {
      clearFieldError(fieldName);
    }
  }, [clearOnChange, clearFieldError, errorState.fieldErrors]);

  const getFieldError = useCallback((fieldName: string): string | undefined => {
    return errorState.fieldErrors[fieldName] || undefined;
  }, [errorState.fieldErrors]);

  const hasFieldError = useCallback((fieldName: string): boolean => {
    return !!errorState.fieldErrors[fieldName];
  }, [errorState.fieldErrors]);

  return {
    // Error state
    ...errorState,
    
    // Error management
    clearErrors,
    clearFieldError,
    setFieldError,
    handleError,
    handleSuccess,
    setSubmitting,
    
    // Field helpers
    handleFieldChange,
    getFieldError,
    hasFieldError,
    
    // Utility functions
    shouldShowRetry: (error: any) => {
      const authError = AuthErrorHandler.handleError(error);
      return authError.shouldRetry;
    },
    
    getErrorMessage: (error: any) => {
      const authError = AuthErrorHandler.handleError(error);
      return authError.userMessage;
    },
  };
}