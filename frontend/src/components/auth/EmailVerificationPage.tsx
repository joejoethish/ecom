'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { CheckCircleIcon, XCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { authApi } from '@/services/authApi';
import { useAuth } from '@/hooks/useAuth';
import { AUTH_ROUTES } from '@/constants/routes';

interface EmailVerificationPageProps {
  token: string;
}

type VerificationStatus = 'verifying' | 'success' | 'error' | 'expired' | 'already_verified';

const EmailVerificationPage: React.FC<EmailVerificationPageProps> = ({ token }) => {
  const [status, setStatus] = useState<VerificationStatus>('verifying');
  const [message, setMessage] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setStatus('error');
        setMessage('Invalid verification token');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        const response = await authApi.verifyEmail(token);

        if (response.success && response.data) {
          setStatus('success');
          setMessage(response.data.message || 'Email verified successfully!');
          
          // Redirect to login after successful verification if not authenticated
          setTimeout(() => {
            if (!isAuthenticated) {
              router.push(AUTH_ROUTES.LOGIN);
            } else {
              router.push('/dashboard');
            }
          }, 3000);
        } else {
          const errorCode = response.error?.code;
          
          if (errorCode === 'TOKEN_EXPIRED') {
            setStatus('expired');
            setMessage('Verification link has expired. Please request a new one.');
          } else if (errorCode === 'ALREADY_VERIFIED') {
            setStatus('already_verified');
            setMessage('Your email is already verified.');
          } else {
            setStatus('error');
            setMessage(response.error?.message || 'Email verification failed');
          }
        }
      } catch (error) {
        setStatus('error');
        setMessage('An unexpected error occurred during verification');
      } finally {
        setIsLoading(false);
      }
    };

    verifyEmail();
  }, [token, router, isAuthenticated]);

  const handleResendVerification = async () => {
    try {
      setIsLoading(true);
      const response = await authApi.resendVerification();
      
      if (response.success) {
        setMessage('A new verification email has been sent to your email address.');
      } else {
        setMessage(response.error?.message || 'Failed to resend verification email');
      }
    } catch (error) {
      setMessage('Failed to resend verification email');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="h-16 w-16 text-green-500" />;
      case 'error':
        return <XCircleIcon className="h-16 w-16 text-red-500" />;
      case 'expired':
      case 'already_verified':
        return <ExclamationTriangleIcon className="h-16 w-16 text-yellow-500" />;
      default:
        return (
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
        );
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      case 'expired':
      case 'already_verified':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
    }
  };

  const getTitle = () => {
    switch (status) {
      case 'verifying':
        return 'Verifying your email...';
      case 'success':
        return 'Email Verified Successfully!';
      case 'error':
        return 'Verification Failed';
      case 'expired':
        return 'Verification Link Expired';
      case 'already_verified':
        return 'Email Already Verified';
      default:
        return 'Email Verification';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center mb-6">
            {getStatusIcon()}
          </div>
          
          <h2 className={`text-3xl font-extrabold ${getStatusColor()}`}>
            {getTitle()}
          </h2>
          
          <p className="mt-4 text-sm text-gray-600">
            {message}
          </p>

          {status === 'success' && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md">
              <p className="text-sm text-green-700">
                You will be redirected to {isAuthenticated ? 'your dashboard' : 'the login page'} in a few seconds.
              </p>
            </div>
          )}

          {(status === 'expired' || (status === 'error' && isAuthenticated)) && (
            <div className="mt-6">
              <button
                onClick={handleResendVerification}
                disabled={isLoading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  'Resend Verification Email'
                )}
              </button>
            </div>
          )}

          {status === 'already_verified' && (
            <div className="mt-6">
              <button
                onClick={() => router.push(isAuthenticated ? '/dashboard' : AUTH_ROUTES.LOGIN)}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {isAuthenticated ? 'Go to Dashboard' : 'Go to Login'}
              </button>
            </div>
          )}

          {status === 'error' && !isAuthenticated && (
            <div className="mt-6 space-y-3">
              <button
                onClick={() => router.push(AUTH_ROUTES.LOGIN)}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Go to Login
              </button>
              <button
                onClick={() => router.push(AUTH_ROUTES.REGISTER)}
                className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Create New Account
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmailVerificationPage;