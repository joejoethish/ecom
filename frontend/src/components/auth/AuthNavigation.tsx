'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { AUTH_ROUTES } from '@/constants';

interface AuthNavigationProps {
  showTabs?: boolean;
  showBackToHome?: boolean;
}

export function AuthNavigation({ 
  showTabs = true, 
  showBackToHome = true 
}: AuthNavigationProps) {
  const pathname = usePathname();

  // Don't show tabs for certain pages
  const isEmailVerificationPage = pathname.includes('/verify-email/');
  const isResetPasswordPage = pathname.includes('/reset-password/');
  const shouldShowTabs = showTabs && !isEmailVerificationPage && !isResetPasswordPage;

  return (
    <div className="text-center space-y-4">
      {/* Logo/Brand */}
      {showBackToHome && (
        <Link href="/" className="inline-block">
          <h1 className="text-3xl font-bold text-indigo-600 hover:text-indigo-500 transition-colors">
            E-Commerce Platform
          </h1>
        </Link>
      )}

      {/* Navigation tabs */}
      {shouldShowTabs && (
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
      )}
    </div>
  );
}

interface AuthFooterProps {
  showSupportLinks?: boolean;
}

export function AuthFooter({ showSupportLinks = true }: AuthFooterProps) {
  if (!showSupportLinks) return null;

  return (
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
  );
}