'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ResetPasswordForm } from '@/components/auth/ResetPasswordForm';
import { AUTH_ROUTES } from '@/constants';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function ResetPasswordPage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;

  const handleSuccess = () => {
    // Redirect to login after successful password reset
    // Give user time to read the success message
    setTimeout(() => {
      router.push(AUTH_ROUTES.LOGIN + '?message=password-reset-success');
    }, 3000);
  };

  const handleBackToLogin = () => {
    router.push(AUTH_ROUTES.LOGIN);
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100 mb-4">
                <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Invalid Reset Link
              </h2>
              <p className="text-gray-600 mb-6">
                This password reset link is missing or invalid. Please request a new password reset.
              </p>
              <div className="space-y-4">
                <Button
                  onClick={handleBackToLogin}
                  className="w-full"
                >
                  Back to Login
                </Button>
                <Link
                  href={AUTH_ROUTES.FORGOT_PASSWORD}
                  className="block text-sm text-indigo-600 hover:text-indigo-500 transition-colors"
                >
                  Request new reset link
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-indigo-600">
            E-Commerce Platform
          </h1>
        </div>
      </div>
      
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="space-y-6">
            <div>
              <h2 className="text-center text-3xl font-extrabold text-gray-900">
                Reset your password
              </h2>
              <p className="mt-2 text-center text-sm text-gray-600">
                Enter your new password below.
              </p>
            </div>
            
            <ResetPasswordForm
              token={token}
              onSuccess={handleSuccess}
              onBackToLogin={handleBackToLogin}
            />
            
            <div className="text-center">
              <Link
                href={AUTH_ROUTES.LOGIN}
                className="text-sm text-indigo-600 hover:text-indigo-500 transition-colors"
              >
                ← Back to sign in
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}