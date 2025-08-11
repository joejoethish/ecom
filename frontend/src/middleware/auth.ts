// Authentication middleware utilities

import { NextRequest, NextResponse } from 'next/server';
import { MAIN_ROUTES, AUTH_ROUTES, PROFILE_ROUTES, ADMIN_ROUTES, SELLER_ROUTES } from '@/constants/routes';

// Protected routes that require authentication
const PROTECTED_ROUTES = [
  PROFILE_ROUTES.DASHBOARD,
  PROFILE_ROUTES.ORDERS,
  MAIN_ROUTES.CART,
  MAIN_ROUTES.CHECKOUT,
  ADMIN_ROUTES.DASHBOARD,
  SELLER_ROUTES.DASHBOARD,
];

// Guest-only routes (redirect if authenticated)
const GUEST_ROUTES = [
  AUTH_ROUTES.LOGIN,
  AUTH_ROUTES.REGISTER,
  AUTH_ROUTES.FORGOT_PASSWORD,
  AUTH_ROUTES.RESET_PASSWORD,
];

/**
 * Authentication middleware for Next.js
 * Handles route protection and redirects based on authentication status
 */
export function authMiddleware(request: NextRequest) {
  
  // Get tokens from cookies or headers
  const accessToken = request.cookies.get('access_token')?.value;
  const refreshToken = request.cookies.get('refresh_token')?.value;
  
  const isAuthenticated = !!(accessToken || refreshToken);
  
  // Check if route requires authentication
  const isProtectedRoute = PROTECTED_ROUTES.some(route => 
    pathname.startsWith(route)
  );
  
  // Check if route is guest-only
  const isGuestRoute = GUEST_ROUTES.some(route => 
    pathname.startsWith(route)
  );
  
  // Check if route is admin-only or seller-only
  const isAdminRoute = pathname.startsWith('/admin');
  const isSellerRoute = pathname.startsWith('/seller');
  
  // Redirect unauthenticated users from protected routes
  if (isProtectedRoute && !isAuthenticated) {
    const loginUrl = new URL(AUTH_ROUTES.LOGIN, request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }
  
  // Redirect authenticated users from guest-only routes
  if (isGuestRoute && isAuthenticated) {
    return NextResponse.redirect(new URL(MAIN_ROUTES.HOME, request.url));
  }
  
  // For admin/seller routes, we'll do basic authentication check here
  // but the full authorization will be handled in the components
  // since we need user data from the store
  if ((isAdminRoute || isSellerRoute) && !isAuthenticated) {
    const loginUrl = new URL(AUTH_ROUTES.LOGIN, request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }
  
  return NextResponse.next();
}

/**
 * Helper function to check if a path should be processed by auth middleware
 * @param pathname - The current pathname
 * @returns Boolean indicating if the path should be processed
 */
export function shouldProcessAuth(pathname: string): boolean {
  // Skip API routes, static files, and Next.js internals
  if (
    pathname.startsWith('/api/') ||
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/favicon.ico') ||
    pathname.includes('.')
  ) {
    return false;
  }
  
  return true;
}