'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { AUTH_ROUTES } from '@/constants';

interface BreadcrumbItem {
  label: string;
  href?: string;
  current?: boolean;
}

export function AuthBreadcrumb() {
  const pathname = usePathname();

  const getBreadcrumbItems = (): BreadcrumbItem[] => {
    const items: BreadcrumbItem[] = [
      { label: 'Home', href: '/' }
    ];

    if (pathname === AUTH_ROUTES.LOGIN) {
      items.push({ label: 'Sign In', current: true });
    } else if (pathname === AUTH_ROUTES.REGISTER) {
      items.push({ label: 'Sign Up', current: true });
    } else if (pathname === AUTH_ROUTES.FORGOT_PASSWORD) {
      items.push(
        { label: 'Sign In', href: AUTH_ROUTES.LOGIN },
        { label: 'Forgot Password', current: true }
      );
    } else if (pathname.includes('/reset-password/')) {
      items.push(
        { label: 'Sign In', href: AUTH_ROUTES.LOGIN },
        { label: 'Reset Password', current: true }
      );
    } else if (pathname === AUTH_ROUTES.VERIFY_EMAIL) {
      items.push({ label: 'Verify Email', current: true });
    } else if (pathname.includes('/verify-email/')) {
      items.push({ label: 'Email Verification', current: true });
    }

    return items;
  };

  const breadcrumbItems = getBreadcrumbItems();

  if (breadcrumbItems.length <= 1) {
    return null;
  }

  return (
    <nav className="flex mb-4" aria-label="Breadcrumb">
      <ol className="inline-flex items-center space-x-1 md:space-x-3">
        {breadcrumbItems.map((item, index) => (
          <li key={index} className="inline-flex items-center">
            {index > 0 && (
              <svg
                className="w-3 h-3 text-gray-400 mx-1"
                aria-hidden="true"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 6 10"
              >
                <path
                  stroke="currentColor"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="m1 9 4-4-4-4"
                />
              </svg>
            )}
            {item.current ? (
              <span className="text-sm font-medium text-gray-500" aria-current="page">
                {item.label}
              </span>
            ) : (
              <Link
                href={item.href!}
                className="text-sm font-medium text-gray-700 hover:text-indigo-600 transition-colors"
              >
                {item.label}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}