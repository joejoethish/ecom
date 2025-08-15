'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { EnvelopeIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/24/outline';
import { authApi } from '@/services/authApi';
import { useAuth } from '@/hooks/useAuth';

interface ResendVerificationFormProps {
  onSuccess?: () => void;
  onError?: (error: string) => void;
  className?: string;
}

interface FormData {
  email?: string;
}

const schema = yup.object().shape({
  email: yup
    .string()
    .email('Please enter a valid email address')
    .when('$isAuthenticated', {
      is: false,
      then: (schema) => schema.required('Email is required'),
      otherwise: (schema) => schema.notRequired(),
    }),
});

type NotificationStatus = 'idle' | 'success' | 'error' | 'loading';

const ResendVerificationForm: React.FC<ResendVerificationFormProps> = ({
  onSuccess,
  onError,
  className = '',
}) => {
  const [status, setStatus] = useState<NotificationStatus>('idle');
  const [message, setMessage] = useState<string>('');
  const { user, isAuthenticated } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<FormData>({
    resolver: yupResolver(schema),
    context: { isAuthenticated },
    defaultValues: {
      email: isAuthenticated ? user?.email : '',
    },
  });

  const onSubmit = async (data: FormData) => {
    try {
      setStatus('loading');
      setMessage('');

      const response = await authApi.resendVerification();

      if (response.success && response.data) {
        setStatus('success');
        setMessage(response.data.message || 'Verification email sent successfully!');
        reset();
        onSuccess?.();
      } else {
        const errorMessage = response.error?.message || 'Failed to send verification email';
        setStatus('error');
        setMessage(errorMessage);
        onError?.(errorMessage);
      }
    } catch (error) {
      const errorMessage = 'An unexpected error occurred';
      setStatus('error');
      setMessage(errorMessage);
      onError?.(errorMessage);
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'error':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'loading':
        return <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>;
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return '';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="text-center">
        <EnvelopeIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h2 className="mt-4 text-2xl font-bold text-gray-900">
          Resend Email Verification
        </h2>
        <p className="mt-2 text-sm text-gray-600">
          {isAuthenticated
            ? `We'll send a new verification email to ${user?.email}`
            : 'Enter your email address to receive a new verification link'}
        </p>
      </div>

      {/* Status Message */}
      {message && (status === 'success' || status === 'error') && (
        <div className={`p-4 rounded-md border ${getStatusColor()}`}>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              {getStatusIcon()}
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium">
                {message}
              </p>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {!isAuthenticated && (
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email Address
            </label>
            <div className="mt-1">
              <input
                {...register('email')}
                type="email"
                autoComplete="email"
                className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Enter your email address"
              />
              {errors.email && (
                <p className="mt-2 text-sm text-red-600">{errors.email.message}</p>
              )}
            </div>
          </div>
        )}

        <div>
          <button
            type="submit"
            disabled={isSubmitting || status === 'loading'}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {(isSubmitting || status === 'loading') ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Sending...
              </div>
            ) : (
              'Send Verification Email'
            )}
          </button>
        </div>

        {status === 'success' && (
          <div className="text-center">
            <p className="text-sm text-gray-600">
              Please check your email and click the verification link to complete the process.
            </p>
          </div>
        )}
      </form>

      {/* Rate Limiting Notice */}
      <div className="text-center">
        <p className="text-xs text-gray-500">
          You can request a new verification email up to 3 times per hour.
        </p>
      </div>
    </div>
  );
};

export default ResendVerificationForm;