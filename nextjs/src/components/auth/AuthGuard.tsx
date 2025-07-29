'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAppSelector, useAppDispatch } from '@/store';
import { initializeAuth } from '@/store/slices/authSlice';
import { ROUTES } from '@/constants';
import { Loading } from '@/components/ui/Loading';

interface AuthGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  requireGuest?: boolean;
  allowedUserTypes?: ('customer' | 'seller' | 'admin')[];
  redirectTo?: string;
  fallback?: React.ReactNode;
}

export function AuthGuard({
  children,
  requireAuth = false,
  requireGuest = false,
  allowedUserTypes = [],
  redirectTo,
  fallback
}: AuthGuardProps) {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { user, isAuthenticated, loading } = useAppSelector((state) => state.auth);

  useEffect(() => {
    // Initialize auth state on mount
    dispatch(initializeAuth());
  }, [dispatch]);

  // Show loading while checking authentication
  if (loading) {
    return fallback || <Loading />;
  }

  // Redirect guests if authentication is required
  if (requireAuth && !isAuthenticated) {
    const redirect = redirectTo || ROUTES.LOGIN;
    router.push(redirect);
    return fallback || <Loading />;
  }

  // Redirect authenticated users if guest-only access is required
  if (requireGuest && isAuthenticated) {
    const redirect = redirectTo || ROUTES.HOME;
    router.push(redirect);
    return fallback || <Loading />;
  }

  // Check user type permissions
  if (requireAuth && isAuthenticated && allowedUserTypes.length > 0 && user) {
    if (!allowedUserTypes.includes(user.user_type)) {
      const redirect = redirectTo || ROUTES.HOME;
      router.push(redirect);
      return fallback || (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
            <p className="text-gray-600">You don't have permission to access this page.</p>
          </div>
        </div>
      );
    }
  }

  return <>{children}</>;
}