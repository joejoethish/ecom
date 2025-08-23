'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { AUTH_ROUTES } from '@/constants';

interface AuthLayoutProps {
  children: React.ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  const pathname = usePathname();

  // Don't show navigation for email verification pages (they should be standalone)
  const isEmailVerificationPage = pathname.includes('/verify-email/');
  const isResetPasswordPage = pathname.includes('/reset-password/');

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        {/* Logo/Brand */}
        <div className="text-center">
          <Link href="/" className="inline-block">
            <h1 className="text-3xl font-bold text-indigo-600 hover:text-indigo-500 transition-colors">
              E-Commerce Platform
            </h1>
          </Link>
        </div>

        {/* Navigation tabs for auth pages (except verification pages) */}
        {!isEmailVerificationPage && !isResetPasswordPage && (
          <div className="mt-8">
            <nav className="flex space-x-4 justify-center">
              <Link
                href={AUTH_ROUTES.LOGIN}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  pathname === AUTH_ROUTES.LOGIN
                    ? 'bg-indigo-100 text-indigo-700 border border-indigo-200'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                Sign In
              </Link>
              <Link
                href={AUTH_ROUTES.REGISTER}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  pathname === AUTH_ROUTES.REGISTER
                    ? 'bg-indigo-100 text-indigo-700 border border-indigo-200'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                Sign Up
              </Link>
            </nav>
          </div>
        )}
      </div>

      {/* Main content */}
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {children}
        </div>
      </div>

      {/* Footer links */}
      <div className="mt-8 text-center">
        <div className="text-sm text-gray-600 space-x-4">
          <Link href="/terms" className="hover:text-gray-900 transition-colors">
            Terms of Service
          </Link>
          <span>•</span>
          <Link href="/privacy" className="hover:text-gray-900 transition-colors">
            Privacy Policy
          </Link>
          <span>•</span>
          <Link href="/contact" className="hover:text-gray-900 transition-colors">
            Contact Support
          </Link>
        </div>
      </div>
    </div>
  );
}