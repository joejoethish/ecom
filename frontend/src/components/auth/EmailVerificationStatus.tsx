'use client';

import React, { useState } from 'react';
import { ExclamationTriangleIcon, CheckCircleIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useAuth } from '@/hooks/useAuth';
import { authApi } from '@/services/authApi';

interface EmailVerificationStatusProps {
  showOnlyWhenUnverified?: boolean;
  className?: string;
  onDismiss?: () => void;
}

const EmailVerificationStatus: React.FC<EmailVerificationStatusProps> = ({
  showOnlyWhenUnverified = true,
  className = '',
  onDismiss,
}) => {
  const { user, isAuthenticated } = useAuth();
  const [isResending, setIsResending] = useState(false);
  const [resendMessage, setResendMessage] = useState<string>('');
  const [isDismissed, setIsDismissed] = useState(false);

  // Don't show if user is not authenticated
  if (!isAuthenticated || !user) {
    return null;
  }

  // Don't show if user is verified and we only show for unverified
  if (showOnlyWhenUnverified && (user.is_email_verified || user.is_verified)) {
    return null;
  }

  // Don't show if dismissed
  if (isDismissed) {
    return null;
  }

  const isVerified = user.is_email_verified || user.is_verified;

  const handleResendVerification = async () => {
    try {
      setIsResending(true);
      setResendMessage('');

      const response = await authApi.resendVerification();

      if (response.success && response.data) {
        setResendMessage(response.data.message || 'Verification email sent successfully!');
      } else {
        setResendMessage(response.error?.message || 'Failed to send verification email');
      }
    } catch (error) {
      setResendMessage('An unexpected error occurred');
    } finally {
      setIsResending(false);
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  if (isVerified) {
    return (
      <div className={`bg-green-50 border border-green-200 rounded-md p-4 ${className}`}>
        <div className="flex">
          <div className="flex-shrink-0">
            <CheckCircleIcon className="h-5 w-5 text-green-400" />
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm font-medium text-green-800">
              Email Verified
            </p>
            <p className="mt-1 text-sm text-green-700">
              Your email address has been successfully verified.
            </p>
          </div>
          {onDismiss && (
            <div className="ml-auto pl-3">
              <div className="-mx-1.5 -my-1.5">
                <button
                  type="button"
                  onClick={handleDismiss}
                  className="inline-flex bg-green-50 rounded-md p-1.5 text-green-500 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-green-50 focus:ring-green-600"
                >
                  <span className="sr-only">Dismiss</span>
                  <XMarkIcon className="h-3 w-3" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-yellow-50 border border-yellow-200 rounded-md p-4 ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-yellow-800">
            Email Verification Required
          </h3>
          <div className="mt-2 text-sm text-yellow-700">
            <p>
              Please verify your email address ({user.email}) to access all features.
            </p>
            {resendMessage && (
              <p className="mt-2 font-medium">
                {resendMessage}
              </p>
            )}
          </div>
          <div className="mt-4">
            <div className="-mx-2 -my-1.5 flex">
              <button
                type="button"
                onClick={handleResendVerification}
                disabled={isResending}
                className="bg-yellow-50 px-2 py-1.5 rounded-md text-sm font-medium text-yellow-800 hover:bg-yellow-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-yellow-50 focus:ring-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isResending ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-yellow-800 mr-1"></div>
                    Sending...
                  </div>
                ) : (
                  'Resend verification email'
                )}
              </button>
              {onDismiss && (
                <button
                  type="button"
                  onClick={handleDismiss}
                  className="ml-3 bg-yellow-50 px-2 py-1.5 rounded-md text-sm font-medium text-yellow-800 hover:bg-yellow-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-yellow-50 focus:ring-yellow-600"
                >
                  Dismiss
                </button>
              )}
            </div>
          </div>
        </div>
        {onDismiss && (
          <div className="ml-auto pl-3">
            <div className="-mx-1.5 -my-1.5">
              <button
                type="button"
                onClick={handleDismiss}
                className="inline-flex bg-yellow-50 rounded-md p-1.5 text-yellow-500 hover:bg-yellow-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-yellow-50 focus:ring-yellow-600"
              >
                <span className="sr-only">Dismiss</span>
                <XMarkIcon className="h-3 w-3" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailVerificationStatus;