//  Enhanced error display components for authentication and form errors
 
import React from 'react';
import { AlertTriangle, RefreshCw, X, CheckCircle, Info, AlertCircle } from 'lucide-react';
import { Button } from './Button';
import { AuthErrorHandler } from '@/utils/AuthErrorHandler';

export interface ErrorDisplayProps {
  error: any;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
  variant?: 'inline' | 'banner' | 'modal';
  showIcon?: boolean;
  showRetry?: boolean;
  showDismiss?: boolean;
}

/**
 * Main error display component with multiple variants
 */
export function ErrorDisplay({
  error,
  onRetry,
  onDismiss,
  className = '',
  variant = 'inline',
  showIcon = true,
  showRetry = true,
  showDismiss = false,
}: ErrorDisplayProps) {
  if (!error) return null;

  const authError = AuthErrorHandler.handleError(error);
  const shouldShowRetry = showRetry && authError.shouldRetry && onRetry;

  const baseClasses = 'rounded-lg border p-4';
  const variantClasses = {
    inline: 'bg-red-50 border-red-200',
    banner: 'bg-red-50 border-red-200 border-l-4 border-l-red-500',
    modal: 'bg-white border-red-200 shadow-lg',
  };

  return (
    <div className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      <div className="flex items-start">
        {showIcon && (
          <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
        )}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-red-800 mb-1">
            {authError.error.code === 'VALIDATION_ERROR' ? 'Validation Error' : 'Error'}
          </p>
          <p className="text-sm text-red-700">{authError.userMessage}</p>
          
          {(shouldShowRetry || showDismiss) && (
            <div className="mt-3 flex gap-2">
              {shouldShowRetry && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onRetry}
                  className="text-red-700 border-red-300 hover:bg-red-100"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try Again
                </Button>
              )}
              {showDismiss && onDismiss && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onDismiss}
                  className="text-red-700 hover:bg-red-100"
                >
                  Dismiss
                </Button>
              )}
            </div>
          )}
        </div>
        {showDismiss && onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-3 flex-shrink-0 text-red-400 hover:text-red-600"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Form field error display component
 */
export interface FieldErrorProps {
  error?: string;
  className?: string;
}

export function FieldError({ error, className = '' }: FieldErrorProps) {
  if (!error) return null;

  return (
    <p className={`text-sm text-red-600 mt-1 ${className}`}>
      {error}
    </p>
  );
}

/**
 * Form errors summary component
 */
export interface FormErrorSummaryProps {
  errors: Record<string, string>;
  generalError?: string;
  className?: string;
  onDismiss?: () => void;
}

export function FormErrorSummary({
  errors,
  generalError,
  className = '',
  onDismiss,
}: FormErrorSummaryProps) {
  const fieldErrors = Object.entries(errors).filter(([key]) => key !== 'general');
  const hasErrors = fieldErrors.length > 0 || generalError;

  if (!hasErrors) return null;

  return (
    <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-start">
        <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="text-sm font-medium text-red-800 mb-2">
            Please correct the following errors:
          </h3>
          
          {generalError && (
            <p className="text-sm text-red-700 mb-2">{generalError}</p>
          )}
          
          {fieldErrors.length > 0 && (
            <ul className="text-sm text-red-700 space-y-1">
              {fieldErrors.map(([field, error]) => (
                <li key={field} className="flex items-start">
                  <span className="inline-block w-2 h-2 bg-red-400 rounded-full mt-2 mr-2 flex-shrink-0" />
                  <span>
                    <strong className="capitalize">{field.replace('_', ' ')}:</strong> {error}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-3 flex-shrink-0 text-red-400 hover:text-red-600"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Success message display component
 */
export interface SuccessDisplayProps {
  message: string;
  onDismiss?: () => void;
  className?: string;
  variant?: 'inline' | 'banner';
  showIcon?: boolean;
}

export function SuccessDisplay({
  message,
  onDismiss,
  className = '',
  variant = 'inline',
  showIcon = true,
}: SuccessDisplayProps) {
  const baseClasses = 'rounded-lg border p-4';
  const variantClasses = {
    inline: 'bg-green-50 border-green-200',
    banner: 'bg-green-50 border-green-200 border-l-4 border-l-green-500',
  };

  return (
    <div className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      <div className="flex items-start">
        {showIcon && (
          <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" />
        )}
        <div className="flex-1">
          <p className="text-sm text-green-700">{message}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-3 flex-shrink-0 text-green-400 hover:text-green-600"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Network error specific display component
 */
export function NetworkErrorDisplay({
  onRetry,
  className = '',
}: {
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <ErrorDisplay
      error={{
        response: null,
        message: 'Network connection error',
      }}
      onRetry={onRetry}
      className={className}
      showRetry={!!onRetry}
    />
  );
}

/**
 * Loading error display component
 */
export function LoadingErrorDisplay({
  resource = 'data',
  onRetry,
  className = '',
}: {
  resource?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div className={`text-center py-8 ${className}`}>
      <AlertTriangle className="h-12 w-12 text-red-400 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        Failed to load {resource}
      </h3>
      <p className="text-gray-600 mb-6">
        We encountered an error while loading the {resource}. Please try again.
      </p>
      {onRetry && (
        <Button onClick={onRetry} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
      )}
    </div>
  );
}