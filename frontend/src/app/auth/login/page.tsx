'use client';

import { Suspense } from 'react';
import { Metadata } from 'next';
import { GuestRoute, LoginForm } from '@/components/auth';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function LoginPage() {
  return (
    <GuestRoute>
      <div className="space-y-6">
        <div>
          <h2 className="text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Welcome back! Please enter your details.
          </p>
        </div>
        <Suspense fallback={<LoadingSpinner />}>
          <LoginForm />
        </Suspense>
      </div>
    </GuestRoute>
  );
}