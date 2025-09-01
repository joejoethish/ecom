'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAppSelector, useAppDispatch } from '@/store';
import { initializeAuth } from '@/store/slices/authSlice';
import { ROUTES } from '@/constants';
import { Loading } from '@/components/ui/Loading';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

interface AuthGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  requireGuest?: boolean;
  allowedUserTypes?: ('customer' | 'seller' | 'admin' | 'inventory_manager' | 'warehouse_staff')[];
  redirectTo?: string;
  fallback?: React.ReactNode;
}

interface AuthGuardState {
  isInitialized: boolean;
  shouldRedirect: boolean;
  redirectPath: string | null;
  accessDenied: boolean;
}

function AuthGuardContent({
  children,
  requireAuth = false,
  requireGuest = false,
  allowedUserTypes = [],
  redirectTo,
  fallback
}: AuthGuardProps) {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { user, isAuthenticated, loading, error } = useAppSelector((state) => state.auth);
  
  const [isInitialized, setIsInitialized] = useState(false);
  const [hasRedirected, setHasRedirected] = useState(false);
  const redirectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        await dispatch(initializeAuth()).unwrap();
      } catch (error) {
        console.error('Auth initialization failed:', error);
      } finally {
        setIsInitialized(true);
      }
    };

    initAuth();
  }, [dispatch]);

  // Handle authentication logic and redirects
  useEffect(() => {
    if (!isInitialized || loading || hasRedirected) {
      return;
    }

    let shouldRedirect = false;
    let redirectPath: string | null = null;

    // Check if guest access is required but user is authenticated
    if (requireGuest && isAuthenticated) {
      shouldRedirect = true;
      redirectPath = redirectTo || ROUTES.HOME;
    }
    // Check if authentication is required but user is not authenticated
    else if (requireAuth && !isAuthenticated) {
      shouldRedirect = true;
      redirectPath = redirectTo || ROUTES.LOGIN;
    }
    // Check user type permissions
    else if (requireAuth && isAuthenticated && allowedUserTypes.length > 0 && user) {
      if (!allowedUserTypes.includes(user.user_type)) {
        if (redirectTo) {
          shouldRedirect = true;
          redirectPath = redirectTo;
        }
      }
    }

    if (shouldRedirect && redirectPath) {
      setHasRedirected(true);
      redirectTimeoutRef.current = setTimeout(() => {
        router.push(redirectPath);
      }, 0);
    }

    return () => {
      if (redirectTimeoutRef.current) {
        clearTimeout(redirectTimeoutRef.current);
      }
    };
  }, [
    isInitialized,
    loading,
    isAuthenticated,
    user,
    requireAuth,
    requireGuest,
    allowedUserTypes,
    redirectTo,
    hasRedirected,
    router
  ]);

  // Show loading while initializing or during auth loading
  if (!isInitialized || loading) {
    return fallback || <Loading />;
  }

  // Show loading while redirect is pending
  if (hasRedirected) {
    return fallback || <Loading />;
  }

  // Check for access denied (user type permissions)
  if (requireAuth && isAuthenticated && allowedUserTypes.length > 0 && user) {
    if (!allowedUserTypes.includes(user.user_type) && !redirectTo) {
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

  // Show error state if auth initialization failed
  if (error && !isAuthenticated && requireAuth) {
    return fallback || (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-2">Authentication Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

export function AuthGuard(props: AuthGuardProps) {
  return (
    <ErrorBoundary
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-2">Something went wrong</h2>
            <p className="text-gray-600 mb-4">An error occurred while checking authentication.</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Reload Page
            </button>
          </div>
        </div>
      }
    >
      <AuthGuardContent {...props} />
    </ErrorBoundary>
  );
}