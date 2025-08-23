'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { ForgotPasswordForm } from '@/components/auth/ForgotPasswordForm';
import { AUTH_ROUTES } from '@/constants';
import Link from 'next/link';

export default function ForgotPasswordPage() {
  const router = useRouter();

  const handleSuccess = () => {
    // Stay on the same page to show success message
    // User can navigate back to login from the success screen
  };

  const handleBackToLogin = () => {
    router.push(AUTH_ROUTES.LOGIN);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-center text-3xl font-extrabold text-gray-900">
          Forgot your password?
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          No worries! Enter your email and we'll send you a reset link.
        </p>
      </div>
      
      <ForgotPasswordForm
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
  );
}