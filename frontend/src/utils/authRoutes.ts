import { AUTH_ROUTES } from '@/constants';

export interface AuthRouteConfig {
  path: string;
  title: string;
  description: string;
  requiresAuth?: boolean;
  guestOnly?: boolean;
  showInNavigation?: boolean;
}

export const AUTH_ROUTE_CONFIGS: Record<string, AuthRouteConfig> = {
  [AUTH_ROUTES.LOGIN]: {
    path: AUTH_ROUTES.LOGIN,
    title: 'Sign In',
    description: 'Welcome back! Please enter your details.',
    guestOnly: true,
    showInNavigation: true,
  },
  [AUTH_ROUTES.REGISTER]: {
    path: AUTH_ROUTES.REGISTER,
    title: 'Create Account',
    description: 'Join our platform and start your journey today.',
    guestOnly: true,
    showInNavigation: true,
  },
  [AUTH_ROUTES.FORGOT_PASSWORD]: {
    path: AUTH_ROUTES.FORGOT_PASSWORD,
    title: 'Forgot Password',
    description: 'No worries! Enter your email and we\'ll send you a reset link.',
    guestOnly: true,
    showInNavigation: false,
  },
  [AUTH_ROUTES.RESET_PASSWORD]: {
    path: AUTH_ROUTES.RESET_PASSWORD,
    title: 'Reset Password',
    description: 'Enter your new password below.',
    guestOnly: true,
    showInNavigation: false,
  },
  [AUTH_ROUTES.VERIFY_EMAIL]: {
    path: AUTH_ROUTES.VERIFY_EMAIL,
    title: 'Verify Email',
    description: 'Didn\'t receive the verification email? We can send you another one.',
    guestOnly: false,
    showInNavigation: false,
  },
};

/**
 * Get route configuration for a given path
 */
export function getAuthRouteConfig(path: string): AuthRouteConfig | null {
  // Handle dynamic routes like /auth/reset-password/[token]
  if (path.includes('/reset-password/') && path !== AUTH_ROUTES.RESET_PASSWORD) {
    return AUTH_ROUTE_CONFIGS[AUTH_ROUTES.RESET_PASSWORD];
  }
  
  if (path.includes('/verify-email/') && path !== AUTH_ROUTES.VERIFY_EMAIL) {
    return {
      path: path,
      title: 'Email Verification',
      description: 'Verifying your email address...',
      guestOnly: false,
      showInNavigation: false,
    };
  }

  return AUTH_ROUTE_CONFIGS[path] || null;
}

/**
 * Generate deep link for email verification
 */
export function generateEmailVerificationLink(token: string, baseUrl?: string): string {
  const base = baseUrl || (typeof window !== 'undefined' ? window.location.origin : '');
  return `${base}/auth/verify-email/${token}`;
}

/**
 * Generate deep link for password reset
 */
export function generatePasswordResetLink(token: string, baseUrl?: string): string {
  const base = baseUrl || (typeof window !== 'undefined' ? window.location.origin : '');
  return `${base}/auth/reset-password/${token}`;
}

/**
 * Parse token from URL path
 */
export function parseTokenFromPath(path: string): string | null {
  const segments = path.split('/');
  
  if (path.includes('/verify-email/')) {
    const tokenIndex = segments.indexOf('verify-email') + 1;
    return segments[tokenIndex] || null;
  }
  
  if (path.includes('/reset-password/')) {
    const tokenIndex = segments.indexOf('reset-password') + 1;
    return segments[tokenIndex] || null;
  }
  
  return null;
}

/**
 * Check if a route is a valid authentication route
 */
export function isValidAuthRoute(path: string): boolean {
  // Check exact matches
  if (AUTH_ROUTE_CONFIGS[path]) {
    return true;
  }
  
  // Check dynamic routes
  if (path.includes('/verify-email/') || path.includes('/reset-password/')) {
    const token = parseTokenFromPath(path);
    return !!token && token.length > 0;
  }
  
  return false;
}

/**
 * Get redirect URL after successful authentication
 */
export function getPostAuthRedirect(userType?: string, redirectParam?: string): string {
  // Use redirect parameter if provided
  if (redirectParam && redirectParam !== '/auth/login' && redirectParam !== '/auth/register') {
    return redirectParam;
  }
  
  // Default redirects based on user type
  switch (userType) {
    case 'admin':
      return '/admin/dashboard';
    case 'seller':
      return '/seller/dashboard';
    case 'customer':
    default:
      return '/profile';
  }
}