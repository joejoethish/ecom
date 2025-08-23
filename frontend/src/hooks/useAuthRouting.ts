'use client';

import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { useCallback, useEffect } from 'react';
import { useAppSelector } from '@/store';
import { 
  getAuthRouteConfig, 
  getPostAuthRedirect, 
  isValidAuthRoute,
  parseTokenFromPath 
} from '@/utils/authRoutes';
import { AUTH_ROUTES } from '@/constants';

export function useAuthRouting() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user, isAuthenticated, loading } = useAppSelector((state) => state.auth);

  const redirectParam = searchParams.get('redirect');
  const routeConfig = getAuthRouteConfig(pathname);

  /**
   * Navigate to login with optional redirect parameter
   */
  const navigateToLogin = useCallback((redirectTo?: string) => {
    const loginUrl = new URL(AUTH_ROUTES.LOGIN, window.location.origin);
    if (redirectTo) {
      loginUrl.searchParams.set('redirect', redirectTo);
    }
    router.push(loginUrl.pathname + loginUrl.search);
  }, [router]);

  /**
   * Navigate to register with optional redirect parameter
   */
  const navigateToRegister = useCallback((redirectTo?: string) => {
    const registerUrl = new URL(AUTH_ROUTES.REGISTER, window.location.origin);
    if (redirectTo) {
      registerUrl.searchParams.set('redirect', redirectTo);
    }
    router.push(registerUrl.pathname + registerUrl.search);
  }, [router]);

  /**
   * Navigate to appropriate dashboard after authentication
   */
  const navigateToPostAuthDestination = useCallback(() => {
    const destination = getPostAuthRedirect(user?.user_type, redirectParam || undefined);
    router.push(destination);
  }, [router, user?.user_type, redirectParam]);

  /**
   * Navigate to forgot password page
   */
  const navigateToForgotPassword = useCallback(() => {
    router.push(AUTH_ROUTES.FORGOT_PASSWORD);
  }, [router]);

  /**
   * Navigate to email verification page
   */
  const navigateToEmailVerification = useCallback(() => {
    router.push(AUTH_ROUTES.VERIFY_EMAIL);
  }, [router]);

  /**
   * Handle successful authentication
   */
  const handleAuthSuccess = useCallback(() => {
    navigateToPostAuthDestination();
  }, [navigateToPostAuthDestination]);

  /**
   * Handle authentication failure
   */
  const handleAuthFailure = useCallback((error?: string) => {
    // Could add error handling logic here
    console.error('Authentication failed:', error);
  }, []);

  /**
   * Check if current route requires authentication
   */
  const requiresAuth = routeConfig?.requiresAuth ?? false;

  /**
   * Check if current route is guest-only
   */
  const isGuestOnly = routeConfig?.guestOnly ?? false;

  /**
   * Get token from current path (for verification/reset pages)
   */
  const token = parseTokenFromPath(pathname);

  /**
   * Check if current route is valid
   */
  const isValidRoute = isValidAuthRoute(pathname);

  /**
   * Auto-redirect based on authentication state and route requirements
   */
  useEffect(() => {
    if (loading) return; // Wait for auth state to load

    // Redirect authenticated users from guest-only pages
    if (isAuthenticated && isGuestOnly) {
      navigateToPostAuthDestination();
      return;
    }

    // Redirect unauthenticated users from protected pages
    if (!isAuthenticated && requiresAuth) {
      navigateToLogin(pathname);
      return;
    }
  }, [
    isAuthenticated, 
    loading, 
    isGuestOnly, 
    requiresAuth, 
    pathname, 
    navigateToLogin, 
    navigateToPostAuthDestination
  ]);

  return {
    // Navigation functions
    navigateToLogin,
    navigateToRegister,
    navigateToForgotPassword,
    navigateToEmailVerification,
    navigateToPostAuthDestination,
    
    // Event handlers
    handleAuthSuccess,
    handleAuthFailure,
    
    // Route information
    routeConfig,
    requiresAuth,
    isGuestOnly,
    isValidRoute,
    token,
    redirectParam,
    
    // Current state
    pathname,
    isAuthenticated,
    user,
    loading,
  };
}