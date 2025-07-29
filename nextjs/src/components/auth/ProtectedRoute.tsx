'use client';

import { AuthGuard } from './AuthGuard';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedUserTypes?: ('customer' | 'seller' | 'admin')[];
  redirectTo?: string;
  fallback?: React.ReactNode;
}

export function ProtectedRoute({
  children,
  allowedUserTypes = [],
  redirectTo,
  fallback
}: ProtectedRouteProps) {
  return (
    <AuthGuard
      requireAuth={true}
      allowedUserTypes={allowedUserTypes}
      redirectTo={redirectTo}
      fallback={fallback}
    >
      {children}
    </AuthGuard>
  );
}