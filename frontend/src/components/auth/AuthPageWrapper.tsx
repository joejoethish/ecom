'use client';

import React from 'react';
import { AuthNavigation, AuthFooter } from './AuthNavigation';
import { AuthBreadcrumb } from './AuthBreadcrumb';

interface AuthPageWrapperProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  showNavigation?: boolean;
  showBreadcrumb?: boolean;
  showFooter?: boolean;
  maxWidth?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function AuthPageWrapper({
  children,
  title,
  subtitle,
  showNavigation = true,
  showBreadcrumb = false,
  showFooter = true,
  maxWidth = 'md',
  className = ''
}: AuthPageWrapperProps) {
  const maxWidthClasses = {
    sm: 'sm:max-w-sm',
    md: 'sm:max-w-md',
    lg: 'sm:max-w-lg'
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      {/* Header with navigation */}
      {showNavigation && (
        <div className={`sm:mx-auto sm:w-full ${maxWidthClasses[maxWidth]}`}>
          <AuthNavigation />
        </div>
      )}

      {/* Main content */}
      <div className={`mt-8 sm:mx-auto sm:w-full ${maxWidthClasses[maxWidth]}`}>
        <div className={`bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10 ${className}`}>
          {/* Breadcrumb */}
          {showBreadcrumb && <AuthBreadcrumb />}
          
          <div className="space-y-6">
            {/* Page title and subtitle */}
            <div>
              <h2 className="text-center text-3xl font-extrabold text-gray-900">
                {title}
              </h2>
              {subtitle && (
                <p className="mt-2 text-center text-sm text-gray-600">
                  {subtitle}
                </p>
              )}
            </div>
            
            {/* Page content */}
            {children}
          </div>
        </div>
      </div>

      {/* Footer */}
      {showFooter && <AuthFooter />}
    </div>
  );
}