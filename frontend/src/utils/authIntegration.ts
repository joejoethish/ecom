/**
 * Authentication system integration utilities
 */
import { logSecurityEvent } from './securityMonitoring';
import { tokenUtils } from './tokenCleanup';

/**
 * Integration points for password reset with existing auth system
 */
export const authIntegration = {
  /**
   * Handle successful password reset
   */
  onPasswordResetSuccess: (email: string, token: string) => {
    // Mark token as used
    tokenUtils.markTokenUsed(token);
    
    // Log security event
    logSecurityEvent(
      'password_reset',
      'password_reset_completed',
      'low',
      {
        email: email.substring(0, 3) + '***@' + email.split('@')[1],
        success: true,
        timestamp: new Date().toISOString()
      }
    );
    
    // Clear any existing auth tokens since password changed
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },

  /**
   * Handle password reset request
   */
  onPasswordResetRequest: (email: string) => {
    logSecurityEvent(
      'password_reset',
      'password_reset_requested',
      'low',
      {
        email: email.substring(0, 3) + '***@' + email.split('@')[1],
        timestamp: new Date().toISOString()
      }
    );
  },

  /**
   * Handle failed password reset attempt
   */
  onPasswordResetFailure: (email: string, errorCode: string, token?: string) => {
    logSecurityEvent(
      'password_reset',
      'password_reset_failed',
      'medium',
      {
        email: email ? email.substring(0, 3) + '***@' + email.split('@')[1] : undefined,
        errorCode,
        token: token ? token.substring(0, 8) + '...' : undefined,
        timestamp: new Date().toISOString()
      }
    );
  },

  /**
   * Check if user should be redirected after login
   */
  getPostLoginRedirect: (): string => {
    // Check if there's a stored redirect URL
    const storedRedirect = typeof window !== 'undefined' 
      ? sessionStorage.getItem('post_login_redirect') 
      : null;
    
    if (storedRedirect) {
      sessionStorage.removeItem('post_login_redirect');
      return storedRedirect;
    }
    
    return '/'; // Default to home page
  },

  /**
   * Store redirect URL for after login
   */
  setPostLoginRedirect: (url: string) => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('post_login_redirect', url);
    }
  },

  /**
   * Check if current session is valid
   */
  isSessionValid: (): boolean => {
    if (typeof window === 'undefined') return false;
    
    const accessToken = localStorage.getItem('access_token');
    const user = localStorage.getItem('user');
    
    return !!(accessToken && user);
  },

  /**
   * Clear all authentication data
   */
  clearAuthData: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      sessionStorage.removeItem('post_login_redirect');
    }
  },

  /**
   * Get current user information
   */
  getCurrentUser: () => {
    if (typeof window === 'undefined') return null;
    
    try {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('Error parsing user data:', error);
      return null;
    }
  },

  /**
   * Update user password in local storage (if user data includes password hash)
   */
  updateUserPassword: (newPasswordHash?: string) => {
    if (typeof window === 'undefined') return;
    
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const user = JSON.parse(userStr);
        // Note: In most cases, password hash shouldn't be stored client-side
        // This is just for completeness of the integration
        if (newPasswordHash) {
          user.password_updated_at = new Date().toISOString();
        }
        localStorage.setItem('user', JSON.stringify(user));
      }
    } catch (error) {
      console.error('Error updating user data:', error);
    }
  },

  /**
   * Check if password reset is available for current environment
   */
  isPasswordResetAvailable: (): boolean => {
    // Check if all required services are available
    const hasLocalStorage = typeof window !== 'undefined' && 'localStorage' in window;
    const hasSessionStorage = typeof window !== 'undefined' && 'sessionStorage' in window;
    
    return hasLocalStorage && hasSessionStorage;
  },

  /**
   * Get password reset statistics for admin dashboard
   */
  getPasswordResetStats: () => {
    const tokenStats = tokenUtils.getStats();
    
    return {
      tokenStats,
      isSystemAvailable: authIntegration.isPasswordResetAvailable(),
      currentUser: authIntegration.getCurrentUser(),
      sessionValid: authIntegration.isSessionValid()
    };
  }
};

/**
 * Middleware for authentication routes
 */
export const authMiddleware = {
  /**
   * Check if user can access password reset
   */
  canAccessPasswordReset: (): boolean => {
    // Password reset should be available to non-authenticated users
    return !authIntegration.isSessionValid();
  },

  /**
   * Check if user should be redirected from auth pages
   */
  shouldRedirectFromAuth: (): string | null => {
    if (authIntegration.isSessionValid()) {
      return authIntegration.getPostLoginRedirect();
    }
    return null;
  },

  /**
   * Handle route protection
   */
  protectRoute: (requireAuth: boolean = true): boolean => {
    const isAuthenticated = authIntegration.isSessionValid();
    
    if (requireAuth && !isAuthenticated) {
      // Store current URL for redirect after login
      if (typeof window !== 'undefined') {
        authIntegration.setPostLoginRedirect(window.location.pathname);
      }
      return false;
    }
    
    if (!requireAuth && isAuthenticated) {
      // User is authenticated but trying to access guest-only page
      return false;
    }
    
    return true;
  }
};

/**
 * React hooks for authentication integration
 */
export const useAuthIntegration = () => {
  return {
    onPasswordResetSuccess: authIntegration.onPasswordResetSuccess,
    onPasswordResetRequest: authIntegration.onPasswordResetRequest,
    onPasswordResetFailure: authIntegration.onPasswordResetFailure,
    isSessionValid: authIntegration.isSessionValid,
    getCurrentUser: authIntegration.getCurrentUser,
    clearAuthData: authIntegration.clearAuthData,
    getPostLoginRedirect: authIntegration.getPostLoginRedirect,
    setPostLoginRedirect: authIntegration.setPostLoginRedirect
  };
};