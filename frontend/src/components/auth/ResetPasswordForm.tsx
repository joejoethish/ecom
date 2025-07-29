import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Button } from '@/components/ui/Button';
import { authApi } from '@/services/authApi';
import { extractErrorInfo, getDisplayErrorMessage, logError } from '@/utils/errorHandling';
import { 
  getPasswordResetErrorMessage, 
  logPasswordResetError, 
  isRetryablePasswordResetError,
  isValidTokenFormat,
  logPasswordResetSecurityEvent 
} from '@/utils/passwordResetErrors';
import { useTokenCleanup } from '@/utils/tokenCleanup';
import { useAuthIntegration } from '@/utils/authIntegration';

interface ResetPasswordFormData {
  password: string;
  confirmPassword: string;
}

interface ResetPasswordFormProps {
  token: string;
  onSuccess?: () => void;
  onBackToLogin?: () => void;
}

interface ErrorState {
  message: string;
  code: string;
  canRetry: boolean;
}

export const ResetPasswordForm: React.FC<ResetPasswordFormProps> = ({
  token,
  onSuccess,
  onBackToLogin
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<ErrorState | null>(null);
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);
  const [isValidatingToken, setIsValidatingToken] = useState(true);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    reset
  } = useForm<ResetPasswordFormData>();

  const password = watch('password');
  const { markTokenUsed, isTokenValid } = useTokenCleanup();
  const { onPasswordResetSuccess, onPasswordResetFailure } = useAuthIntegration();

  // Validate token on component mount
  useEffect(() => {
    const validateToken = async () => {
      try {
        setIsValidatingToken(true);
        const response = await authApi.validateResetToken(token);
        
        if (response.success && response.data?.valid) {
          setTokenValid(true);
        } else {
          setTokenValid(false);
          setError({
            message: response.data?.expired 
              ? 'This password reset link has expired. Please request a new one.'
              : 'This password reset link is invalid. Please request a new one.',
            code: response.data?.expired ? 'token_expired' : 'token_invalid',
            canRetry: false
          });
        }
      } catch (err) {
        const errorInfo = extractErrorInfo(err);
        logPasswordResetError(err, 'validateToken', { token: token.substring(0, 8) + '...' });
        logPasswordResetSecurityEvent('validate', { 
          token, 
          success: false, 
          errorCode: errorInfo.code 
        });
        
        setTokenValid(false);
        setError({
          message: getPasswordResetErrorMessage(err),
          code: errorInfo.code,
          canRetry: isRetryablePasswordResetError(errorInfo.code)
        });
      } finally {
        setIsValidatingToken(false);
      }
    };

    if (token) {
      validateToken();
    } else {
      setTokenValid(false);
      setIsValidatingToken(false);
    }
  }, [token]);

  const validatePassword = (password: string): string | true => {
    if (password.length < 8) {
      return 'Password must be at least 8 characters long';
    }
    if (!/(?=.*[a-z])/.test(password)) {
      return 'Password must contain at least one lowercase letter';
    }
    if (!/(?=.*[A-Z])/.test(password)) {
      return 'Password must contain at least one uppercase letter';
    }
    if (!/(?=.*\d)/.test(password)) {
      return 'Password must contain at least one number';
    }
    if (!/(?=.*[@$!%*?&])/.test(password)) {
      return 'Password must contain at least one special character (@$!%*?&)';
    }
    return true;
  };

  const onSubmit = async (data: ResetPasswordFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await authApi.resetPassword(token, data.password);
      
      if (response.success) {
        logPasswordResetSecurityEvent('reset', { 
          token, 
          success: true 
        });
        
        // Mark token as used to prevent reuse
        markTokenUsed(token);
        
        // Handle successful password reset
        onPasswordResetSuccess('', token); // Email not available in this context
        
        setIsSuccess(true);
        onSuccess?.();
      } else {
        const errorInfo = extractErrorInfo(response.error);
        logPasswordResetError(response.error, 'onSubmit', { token: token.substring(0, 8) + '...' });
        logPasswordResetSecurityEvent('reset', { 
          token, 
          success: false, 
          errorCode: errorInfo.code 
        });
        
        // Handle password reset failure
        onPasswordResetFailure('', errorInfo.code, token);
        
        setError({
          message: getPasswordResetErrorMessage(response.error),
          code: errorInfo.code,
          canRetry: isRetryablePasswordResetError(errorInfo.code)
        });
      }
    } catch (err) {
      const errorInfo = extractErrorInfo(err);
      logPasswordResetError(err, 'onSubmit', { token: token.substring(0, 8) + '...' });
      logPasswordResetSecurityEvent('reset', { 
        token, 
        success: false, 
        errorCode: errorInfo.code 
      });
      
      setError({
        message: getPasswordResetErrorMessage(err),
        code: errorInfo.code,
        canRetry: isRetryablePasswordResetError(errorInfo.code)
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = async () => {
    if (tokenValid === false) {
      // Retry token validation
      setIsValidatingToken(true);
      setError(null);
      
      try {
        const response = await authApi.validateResetToken(token);
        
        if (response.success && response.data?.valid) {
          setTokenValid(true);
        } else {
          setTokenValid(false);
          setError({
            message: response.data?.expired 
              ? 'This password reset link has expired. Please request a new one.'
              : 'This password reset link is invalid. Please request a new one.',
            code: response.data?.expired ? 'token_expired' : 'token_invalid',
            canRetry: false
          });
        }
      } catch (err) {
        const errorInfo = extractErrorInfo(err);
        logPasswordResetError(err, 'handleRetry', { token: token.substring(0, 8) + '...' });
        
        setError({
          message: getPasswordResetErrorMessage(err),
          code: errorInfo.code,
          canRetry: isRetryablePasswordResetError(errorInfo.code)
        });
      } finally {
        setIsValidatingToken(false);
      }
    }
  };

  // Loading state during token validation
  if (isValidatingToken) {
    return (
      <div style={{ 
        maxWidth: '400px', 
        margin: '0 auto', 
        padding: '32px', 
        backgroundColor: 'white', 
        borderRadius: '8px', 
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        textAlign: 'center'
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #2196f3',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 24px auto'
        }} />
        <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#212121', marginBottom: '8px' }}>
          Validating Reset Link
        </h2>
        <p style={{ color: '#757575', fontSize: '14px' }}>
          Please wait while we verify your password reset link...
        </p>
        
        <style jsx>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // Success state
  if (isSuccess) {
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
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 style={{ fontSize: '28px', fontWeight: 'bold', color: '#212121', marginBottom: '12px' }}>
            Password Reset Successful!
          </h2>
          <p style={{ color: '#757575', fontSize: '16px', lineHeight: '1.6', marginBottom: '24px' }}>
            Your password has been successfully updated. You can now log in with your new password.
          </p>
        </div>

        <Button
          onClick={onBackToLogin}
          style={{ 
            width: '100%', 
            backgroundColor: '#2196f3',
            color: 'white',
            padding: '14px',
            fontSize: '16px',
            fontWeight: '600'
          }}
        >
          Continue to Login
        </Button>
      </div>
    );
  }

  // Invalid token state
  if (tokenValid === false) {
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
            backgroundColor: '#f44336', 
            borderRadius: '50%', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            margin: '0 auto 24px auto',
            boxShadow: '0 4px 16px rgba(244, 67, 54, 0.3)'
          }}>
            <svg style={{ width: '40px', height: '40px', color: 'white' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 style={{ fontSize: '28px', fontWeight: 'bold', color: '#212121', marginBottom: '12px' }}>
            Invalid Reset Link
          </h2>
          <p style={{ color: '#757575', fontSize: '16px', lineHeight: '1.6', marginBottom: '24px' }}>
            {error?.message || 'This password reset link is invalid or has expired.'}
          </p>
        </div>

        {error?.canRetry && (
          <Button
            onClick={handleRetry}
            variant="outline"
            style={{ width: '100%', marginBottom: '16px' }}
          >
            Try Again
          </Button>
        )}

        <Button
          onClick={onBackToLogin}
          style={{ 
            width: '100%', 
            backgroundColor: '#2196f3',
            color: 'white',
            padding: '14px',
            fontSize: '16px',
            fontWeight: '600'
          }}
        >
          Back to Login
        </Button>
      </div>
    );
  }

  // Main form
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
          Reset Your Password
        </h2>
        <p style={{ color: '#757575', fontSize: '14px' }}>
          Enter your new password below. Make sure it's strong and secure.
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
            New Password
          </label>
          <input
            type="password"
            {...register('password', {
              required: 'Password is required',
              validate: validatePassword
            })}
            style={{
              width: '100%',
              padding: '14px 16px',
              border: `2px solid ${errors.password ? '#f44336' : '#e0e0e0'}`,
              borderRadius: '8px',
              fontSize: '16px',
              outline: 'none',
              transition: 'border-color 0.2s, box-shadow 0.2s',
              boxSizing: 'border-box',
              backgroundColor: errors.password ? '#ffeaea' : 'white'
            }}
            placeholder="Enter your new password"
            disabled={isLoading}
            onFocus={(e) => {
              if (!errors.password) {
                e.target.style.borderColor = '#2196f3';
                e.target.style.boxShadow = '0 0 0 3px rgba(33, 150, 243, 0.1)';
              }
            }}
            onBlur={(e) => {
              if (!errors.password) {
                e.target.style.borderColor = '#e0e0e0';
                e.target.style.boxShadow = 'none';
              }
            }}
          />
          {errors.password && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px' }}>
              <svg style={{ width: '16px', height: '16px', color: '#f44336', flexShrink: 0 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p style={{ color: '#f44336', fontSize: '13px', margin: 0, fontWeight: '500' }}>
                {errors.password.message}
              </p>
            </div>
          )}
          
          {/* Password strength indicator */}
          {password && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ fontSize: '12px', fontWeight: '500', color: '#757575', marginBottom: '6px' }}>
                Password Strength
              </div>
              <div style={{ display: 'flex', gap: '4px', marginBottom: '8px' }}>
                {[1, 2, 3, 4].map((level) => {
                  const strength = getPasswordStrength(password);
                  return (
                    <div
                      key={level}
                      style={{
                        flex: 1,
                        height: '4px',
                        borderRadius: '2px',
                        backgroundColor: strength >= level 
                          ? strength === 1 ? '#f44336' 
                          : strength === 2 ? '#ff9800'
                          : strength === 3 ? '#2196f3'
                          : '#4caf50'
                          : '#e0e0e0'
                      }}
                    />
                  );
                })}
              </div>
              <div style={{ fontSize: '11px', color: '#757575' }}>
                {getPasswordStrengthText(getPasswordStrength(password))}
              </div>
            </div>
          )}
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ 
            display: 'block', 
            fontSize: '14px', 
            fontWeight: '500', 
            color: '#212121', 
            marginBottom: '8px' 
          }}>
            Confirm New Password
          </label>
          <input
            type="password"
            {...register('confirmPassword', {
              required: 'Please confirm your password',
              validate: (value) => value === password || 'Passwords do not match'
            })}
            style={{
              width: '100%',
              padding: '14px 16px',
              border: `2px solid ${errors.confirmPassword ? '#f44336' : '#e0e0e0'}`,
              borderRadius: '8px',
              fontSize: '16px',
              outline: 'none',
              transition: 'border-color 0.2s, box-shadow 0.2s',
              boxSizing: 'border-box',
              backgroundColor: errors.confirmPassword ? '#ffeaea' : 'white'
            }}
            placeholder="Confirm your new password"
            disabled={isLoading}
            onFocus={(e) => {
              if (!errors.confirmPassword) {
                e.target.style.borderColor = '#2196f3';
                e.target.style.boxShadow = '0 0 0 3px rgba(33, 150, 243, 0.1)';
              }
            }}
            onBlur={(e) => {
              if (!errors.confirmPassword) {
                e.target.style.borderColor = '#e0e0e0';
                e.target.style.boxShadow = 'none';
              }
            }}
          />
          {errors.confirmPassword && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px' }}>
              <svg style={{ width: '16px', height: '16px', color: '#f44336', flexShrink: 0 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p style={{ color: '#f44336', fontSize: '13px', margin: 0, fontWeight: '500' }}>
                {errors.confirmPassword.message}
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
                <svg style={{ width: '20px', height: '20px', color: error.code === 'network_error' ? '#856404' : '#c62828' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
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
                    onClick={handleRetry}
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
                    {isLoading ? 'Retrying...' : 'Try Again'}
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
          {isLoading ? 'Resetting Password...' : 'Reset Password'}
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

// Helper functions for password strength
const getPasswordStrength = (password: string): number => {
  let strength = 0;
  
  if (password.length >= 8) strength++;
  if (/(?=.*[a-z])/.test(password)) strength++;
  if (/(?=.*[A-Z])/.test(password)) strength++;
  if (/(?=.*\d)/.test(password)) strength++;
  if (/(?=.*[@$!%*?&])/.test(password)) strength++;
  
  return Math.min(strength, 4);
};

const getPasswordStrengthText = (strength: number): string => {
  switch (strength) {
    case 0:
    case 1:
      return 'Weak - Add more characters and variety';
    case 2:
      return 'Fair - Add uppercase, numbers, or symbols';
    case 3:
      return 'Good - Consider adding more variety';
    case 4:
      return 'Strong - Great password!';
    default:
      return '';
  }
};