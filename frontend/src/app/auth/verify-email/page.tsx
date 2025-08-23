import React from 'react';
import { Metadata } from 'next';
import ResendVerificationForm from '@/components/auth/ResendVerificationForm';
import Link from 'next/link';
import { AUTH_ROUTES } from '@/constants';

export const metadata: Metadata = {
  title: 'Resend Email Verification | E-Commerce Platform',
  description: 'Resend your email verification link to complete your account setup',
};

export default function ResendVerificationPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <Link href="/" className="inline-block">
            <h1 className="text-3xl font-bold text-indigo-600 hover:text-indigo-500 transition-colors">
              E-Commerce Platform
            </h1>
          </Link>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="space-y-6">
            <div>
              <h2 className="text-center text-3xl font-extrabold text-gray-900">
                Verify your email
              </h2>
              <p className="mt-2 text-center text-sm text-gray-600">
                Didn't receive the verification email? We can send you another one.
              </p>
            </div>
            
            <ResendVerificationForm />
            
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