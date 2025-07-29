import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Button } from '@/components/ui/Button';
import { authApi } from '@/services/authApi';
import { extractErrorInfo, getDisplayErrorMessage, logError, retryWithBackoff } from '@/utils/errorHandling';
import { 
  getPasswordResetErrorMessage, 
  logPasswordResetError, 
  isRetryablePasswordResetError,
  logPasswordResetSecurityEvent 
} from '@/utils/passwordResetErrors';
import { useAuthIntegration } from '@/utils/authIntegration';

interface ForgotPasswordFormData {
  email: string;
}

interface ForgotPasswordFormProps {
  onSuccess?: () => void;
  onBackToLogin?: () => void;
}

interface ErrorState {
  message: string;
  code: string;
  canRetry: boolean;
}

export const ForgotPasswordForm: React.FC<ForgotPasswordFormProps> = ({
  onSuccess,
  onBackToLogin
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<ErrorState | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const { onPasswordResetRequest, onPasswordResetFailure } = useAuthIntegration();

  const {
    register,
    handleSubmit,
    formState: { errors },
    getValues,
    reset
  } = useForm<ForgotPasswordFormData>();

  const handleRetry = async (data: ForgotPasswordFormData) => {
    try {
      const response = await retryWithBackoff(
        () => authApi.requestPasswordReset(data.email),
        2, // Max 2 retries
        1000 // 1 second base delay
      );
      
      if (response.success) {
        setIsSuccess(true);
        setRetryCount(0);
        onSuccess?.();
      } else {
        throw new Error(response.error?.message || 'Failed to send reset email');
      }
    } catch (err) {
      const errorInfo = extractErrorInfo(err);
      logPasswordResetError(err, 'handleRetry', { email: data.email });
      
      setError({
        message: getPasswordResetErrorMessage(err),
        code: errorInfo.code,
        canRetry: isRetryablePasswordResetError(errorInfo.code)
      });
      setRetryCount(prev => prev + 1);
    }
  };

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await authApi.requestPasswordReset(data.email);
      
      if (response.success) {
        // Handle successful password reset request
        onPasswordResetRequest(data.email);
        
        setIsSuccess(true);
        setRetryCount(0);
        onSuccess?.();
      } else {
        const errorInfo = extractErrorInfo(response.error);
        logPasswordResetError(response.error, 'onSubmit', { email: data.email });
        
        // Handle password reset request failure
        onPasswordResetFailure(data.email, errorInfo.code);
        
        setError({
          message: getPasswordResetErrorMessage(response.error),
          code: errorInfo.code,
          canRetry: isRetryablePasswordResetError(errorInfo.code)
        });
      }
    } catch (err) {
      const errorInfo = extractErrorInfo(err);
      logPasswordResetError(err, 'onSubmit', { email: data.email });
      
      setError({
        message: getPasswordResetErrorMessage(err),
        code: errorInfo.code,
        canRetry: isRetryablePasswordResetError(errorInfo.code)
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    const submittedEmail = getValues('email');
    
    return (
      <div style={{ 
        maxWidth: '400px', 
        margin: '0 auto', 
        padding: '32px', 
        backgroundColor: 'white', 
        borderRadius: '8px', 
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)' 
      }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ 
            width: '80px', 
            height: '80px', 
            backgroundColor: '#4caf50', 
            borderRadius: '50%', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            margin: '0 auto 24px auto',
            boxShadow: '0 4px 16px rgba(76, 175, 80, 0.3)'
          }}>
            <svg style={{ width: '40px', height: '40px', color: 'white' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h2 style={{ fontSize: '28px', fontWeight: 'bold', color: '#212121', marginBottom: '12px' }}>
            Check Your Email
          </h2>
          <p style={{ color: '#757575', fontSize: '16px', lineHeight: '1.6', marginBottom: '8px' }}>
            We've sent a password reset link to:
          </p>
          <p style={{ 
            color: '#2196f3', 
            fontSize: '16px', 
            fontWeight: '600',
            wordBreak: 'break-word',
            marginBottom: '16px'
          }}>
            {submittedEmail}
          </p>
          <p style={{ color: '#757575', fontSize: '14px', lineHeight: '1.5' }}>
            Click the link in the email to reset your password. The link will expire in 1 hour.
          </p>
        </div>

        <div style={{ 
          backgroundColor: '#f8f9fa', 
          borderRadius: '8px', 
          padding: '20px', 
          marginBottom: '24px',
          border: '1px solid #e9ecef'
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#212121', marginBottom: '12px' }}>
            Next Steps:
          </h3>
          <ul style={{ 
            margin: 0, 
            paddingLeft: '20px', 
            color: '#757575', 
            fontSize: '14px',
            lineHeight: '1.6'
          }}>
            <li style={{ marginBottom: '8px' }}>Check your email inbox for the reset link</li>
            <li style={{ marginBottom: '8px' }}>Look in your spam or junk folder if you don't see it</li>
            <li style={{ marginBottom: '8px' }}>Click the link to create a new password</li>
            <li>The link expires in 1 hour for security</li>
          </ul>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <p style={{ fontSize: '14px', color: '#757575', textAlign: 'center', marginBottom: '16px' }}>
            Didn't receive the email?
          </p>
          <Button
            onClick={() => {
              setIsSuccess(false);
              setError(null);
              setRetryCount(0);
              reset();
            }}
            variant="outline"
            style={{ width: '100%', marginBottom: '12px' }}
          >
            Try Different Email
          </Button>
        </div>

        <div style={{ textAlign: 'center' }}>
          <button
            onClick={onBackToLogin}
            style={{
              background: 'none',
              border: 'none',
              color: '#2196f3',
              fontSize: '14px',
              cursor: 'pointer',
              textDecoration: 'underline',
              padding: '8px'
            }}
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      maxWidth: '400px', 
      margin: '0 auto', 
      padding: '32px', 
      backgroundColor: 'white', 
      borderRadius: '8px', 
      boxShadow: '0 4px 12px rgba(0,0,0,0.1)' 
    }}>
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <h2 style={{ fontSize: '28px', fontWeight: 'bold', color: '#212121', marginBottom: '8px' }}>
          Forgot Password?
        </h2>
        <p style={{ color: '#757575', fontSize: '14px' }}>
          Enter your email address and we'll send you a link to reset your password.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div style={{ marginBottom: '24px' }}>
          <label style={{ 
            display: 'block', 
            fontSize: '14px', 
            fontWeight: '500', 
            color: '#212121', 
            marginBottom: '8px' 
          }}>
            Email Address
          </label>
          <input
            type="email"
            {...register('email', {
              required: 'Email address is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Please enter a valid email address'
              }
            })}
            style={{
              width: '100%',
              padding: '14px 16px',
              border: `2px solid ${errors.email ? '#f44336' : '#e0e0e0'}`,
              borderRadius: '8px',
              fontSize: '16px',
              outline: 'none',
              transition: 'border-color 0.2s, box-shadow 0.2s',
              boxSizing: 'border-box',
              backgroundColor: errors.email ? '#ffeaea' : 'white'
            }}
            placeholder="Enter your email address"
            disabled={isLoading}
            onFocus={(e) => {
              if (!errors.email) {
                e.target.style.borderColor = '#2196f3';
                e.target.style.boxShadow = '0 0 0 3px rgba(33, 150, 243, 0.1)';
              }
            }}
            onBlur={(e) => {
              if (!errors.email) {
                e.target.style.borderColor = '#e0e0e0';
                e.target.style.boxShadow = 'none';
              }
            }}
          />
          {errors.email && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px' }}>
              <svg style={{ width: '16px', height: '16px', color: '#f44336', flexShrink: 0 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p style={{ color: '#f44336', fontSize: '13px', margin: 0, fontWeight: '500' }}>
                {errors.email.message}
              </p>
            </div>
          )}
        </div>

        {error && (
          <div style={{ 
            backgroundColor: error.code === 'network_error' ? '#fff3cd' : '#ffebee', 
            border: `1px solid ${error.code === 'network_error' ? '#ffeaa7' : '#ffcdd2'}`, 
            borderRadius: '8px', 
            padding: '16px', 
            marginBottom: '24px' 
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <div style={{ 
                width: '20px', 
                height: '20px', 
                flexShrink: 0,
                marginTop: '2px'
              }}>
                {error.code === 'network_error' ? (
                  <svg style={{ width: '20px', height: '20px', color: '#856404' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                ) : (
                  <svg style={{ width: '20px', height: '20px', color: '#c62828' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ 
                  color: error.code === 'network_error' ? '#856404' : '#c62828', 
                  fontSize: '14px', 
                  margin: '0 0 8px 0',
                  fontWeight: '500'
                }}>
                  {error.message}
                </p>
                {error.canRetry && (
                  <button
                    onClick={() => handleRetry(getValues())}
                    disabled={isLoading}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: error.code === 'network_error' ? '#856404' : '#c62828',
                      fontSize: '13px',
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      textDecoration: 'underline',
                      padding: '0',
                      fontWeight: '500'
                    }}
                  >
                    {isLoading ? 'Retrying...' : `Try Again${retryCount > 0 ? ` (${retryCount} attempts)` : ''}`}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        <Button
          type="submit"
          disabled={isLoading}
          style={{ 
            width: '100%', 
            marginBottom: '16px',
            backgroundColor: isLoading ? '#90caf9' : '#2196f3',
            color: 'white',
            padding: '14px',
            fontSize: '16px',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            transition: 'background-color 0.2s ease'
          }}
        >
          {isLoading && (
            <div style={{
              width: '16px',
              height: '16px',
              border: '2px solid transparent',
              borderTop: '2px solid white',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
          )}
          {isLoading ? 'Sending Reset Link...' : 'Send Reset Link'}
        </Button>

        <style jsx>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>

        <div style={{ textAlign: 'center' }}>
          <button
            type="button"
            onClick={onBackToLogin}
            style={{
              background: 'none',
              border: 'none',
              color: '#2196f3',
              fontSize: '14px',
              cursor: 'pointer',
              textDecoration: 'underline'
            }}
          >
            Back to Login
          </button>
        </div>
      </form>
    </div>
  );
};