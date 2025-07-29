'use client';

import { AuthGuard } from './AuthGuard';

interface GuestRouteProps {
  children: React.ReactNode;
  redirectTo?: string;
  fallback?: React.ReactNode;
}

export function GuestRoute({
  children,
  redirectTo,
  fallback
}: GuestRouteProps) {
  return (
    <AuthGuard
      requireGuest={true}
      redirectTo={redirectTo}
      fallback={fallback}
    >
      {children}
    </AuthGuard>
  );
}