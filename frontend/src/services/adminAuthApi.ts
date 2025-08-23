/**
 * Admin Authentication API service with enhanced security features
 */
import { apiClient } from '@/utils/api';
import { ApiResponse, User, AuthTokens } from '@/types';
import { withPerformanceMonitoring } from '@/utils/securityMonitoring';

// Admin-specific interfaces
export interface AdminLoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface AdminLoginResponse {
  user: User;
  tokens: AuthTokens;
  sessionId: string;
  expiresAt: string;
  securityLevel: 'standard' | 'elevated';
}

export interface AdminSessionInfo {
  id: string;
  user: User;
  deviceInfo: {
    browser: string;
    os: string;
    device: string;
    userAgent: string;
  };
  ipAddress: string;
  location?: {
    country: string;
    city: string;
    region: string;
  };
  createdAt: string;
  lastActivity: string;
  expiresAt: string;
  isActive: boolean;
  isCurrent: boolean;
  securityLevel: 'standard' | 'elevated';
  loginMethod: 'password' | '2fa' | 'sso';
}

export interface AdminSecurityEvent {
  id: string;
  eventType: 'login' | 'logout' | 'failed_login' | 'session_timeout' | 'suspicious_activity';
  userId: string;
  ipAddress: string;
  userAgent: string;
  timestamp: string;
  details: Record<string, any>;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface AdminLogoutResponse {
  success: boolean;
  message: string;
  clearedSessions: number;
}

// API endpoints for admin authentication
const ADMIN_AUTH_ENDPOINTS = {
  LOGIN: '/admin-auth/login/',
  LOGOUT: '/admin-auth/logout/',
  LOGOUT_ALL: '/admin-auth/logout-all/',
  REFRESH: '/admin-auth/refresh/',
  SESSIONS: '/admin-auth/sessions/',
  TERMINATE_SESSION: (sessionId: string) => `/admin-auth/sessions/${sessionId}/terminate/`,
  SECURITY_EVENTS: '/admin-auth/security-events/',
  VALIDATE_SESSION: '/admin-auth/validate-session/',
} as const;

export const adminAuthApi = {
  /**
   * Admin login with enhanced security features
   */
  async login(credentials: AdminLoginCredentials): Promise<ApiResponse<AdminLoginResponse>> {
    return withPerformanceMonitoring(
      'admin_login',
      async () => {
        try {
          // Collect device information for security tracking
          const deviceInfo = {
            browser: navigator.userAgent.split(' ').pop() || 'Unknown',
            os: navigator.platform || 'Unknown',
            device: /Mobile|Android|iPhone|iPad/.test(navigator.userAgent) ? 'Mobile' : 'Desktop',
            userAgent: navigator.userAgent,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language,
            screen: `${screen.width}x${screen.height}`,
          };

          const response = await apiClient.post<AdminLoginResponse>(
            ADMIN_AUTH_ENDPOINTS.LOGIN,
            {
              ...credentials,
              deviceInfo,
              clientTimestamp: new Date().toISOString(),
            }
          );

          // Log successful login for security monitoring
          if (response.success) {
            console.log('Admin login successful:', {
              userId: response.data?.user.id,
              email: response.data?.user.email,
              sessionId: response.data?.sessionId,
              timestamp: new Date().toISOString(),
              deviceInfo,
            });
          }

          return response;
        } catch (error: any) {
          // Log failed login attempt
          console.error('Admin login failed:', {
            email: credentials.email,
            timestamp: new Date().toISOString(),
            error: error.message,
            userAgent: navigator.userAgent,
          });

          return {
            success: false,
            error: {
              message: 'Admin login failed',
              code: 'admin_login_failed',
              status_code: error.status || 500,
              details: error.response?.data,
            }
          };
        }
      },
      { 
        email: credentials.email.substring(0, 3) + '***',
        rememberMe: credentials.rememberMe 
      }
    );
  },

  /**
   * Admin logout with session cleanup
   */
  async logout(sessionId?: string): Promise<ApiResponse<AdminLogoutResponse>> {
    return withPerformanceMonitoring(
      'admin_logout',
      async () => {
        try {
          const response = await apiClient.post<AdminLogoutResponse>(
            ADMIN_AUTH_ENDPOINTS.LOGOUT,
            { sessionId }
          );

          // Log logout for security monitoring
          console.log('Admin logout:', {
            sessionId,
            timestamp: new Date().toISOString(),
          });

          return response;
        } catch (error: any) {
          return {
            success: false,
            error: {
              message: 'Logout failed',
              code: 'logout_failed',
              status_code: error.status || 500
            }
          };
        }
      },
      { sessionId }
    );
  },

  /**
   * Logout from all admin sessions
   */
  async logoutAll(): Promise<ApiResponse<AdminLogoutResponse>> {
    return withPerformanceMonitoring(
      'admin_logout_all',
      async () => {
        try {
          const response = await apiClient.post<AdminLogoutResponse>(
            ADMIN_AUTH_ENDPOINTS.LOGOUT_ALL,
            {}
          );

          // Log logout all for security monitoring
          console.log('Admin logout all sessions:', {
            timestamp: new Date().toISOString(),
            clearedSessions: response.data?.clearedSessions,
          });

          return response;
        } catch (error: any) {
          return {
            success: false,
            error: {
              message: 'Failed to logout from all sessions',
              code: 'logout_all_failed',
              status_code: error.status || 500
            }
          };
        }
      }
    );
  },

  /**
   * Refresh admin authentication tokens
   */
  async refreshToken(refreshToken: string): Promise<ApiResponse<AdminLoginResponse>> {
    return withPerformanceMonitoring(
      'admin_token_refresh',
      async () => {
        try {
          const response = await apiClient.post<AdminLoginResponse>(
            ADMIN_AUTH_ENDPOINTS.REFRESH,
            { refresh: refreshToken }
          );

          return response;
        } catch (error: any) {
          return {
            success: false,
            error: {
              message: 'Token refresh failed',
              code: 'token_refresh_failed',
              status_code: error.status || 500
            }
          };
        }
      }
    );
  },

  /**
   * Get admin session information
   */
  async getSessions(): Promise<ApiResponse<AdminSessionInfo[]>> {
    return withPerformanceMonitoring(
      'admin_get_sessions',
      async () => {
        try {
          const response = await apiClient.get<AdminSessionInfo[]>(
            ADMIN_AUTH_ENDPOINTS.SESSIONS
          );

          return response;
        } catch (error: any) {
          return {
            success: false,
            error: {
              message: 'Failed to fetch sessions',
              code: 'sessions_fetch_failed',
              status_code: error.status || 500
            }
          };
        }
      }
    );
  },

  /**
   * Terminate a specific admin session
   */
  async terminateSession(sessionId: string): Promise<ApiResponse<{ success: boolean; message: string }>> {
    return withPerformanceMonitoring(
      'admin_terminate_session',
      async () => {
        try {
          const response = await apiClient.delete(
            ADMIN_AUTH_ENDPOINTS.TERMINATE_SESSION(sessionId)
          );

          // Log session termination
          console.log('Admin session terminated:', {
            sessionId,
            timestamp: new Date().toISOString(),
          });

          return response;
        } catch (error: any) {
          return {
            success: false,
            error: {
              message: 'Failed to terminate session',
              code: 'session_terminate_failed',
              status_code: error.status || 500
            }
          };
        }
      },
      { sessionId }
    );
  },

  /**
   * Get admin security events
   */
  async getSecurityEvents(limit = 50): Promise<ApiResponse<AdminSecurityEvent[]>> {
    return withPerformanceMonitoring(
      'admin_security_events',
      async () => {
        try {
          const response = await apiClient.get<AdminSecurityEvent[]>(
            `${ADMIN_AUTH_ENDPOINTS.SECURITY_EVENTS}?limit=${limit}`
          );

          return response;
        } catch (error: any) {
          return {
            success: false,
            error: {
              message: 'Failed to fetch security events',
              code: 'security_events_failed',
              status_code: error.status || 500
            }
          };
        }
      },
      { limit }
    );
  },

  /**
   * Validate current admin session
   */
  async validateSession(): Promise<ApiResponse<{ valid: boolean; expiresAt: string }>> {
    return withPerformanceMonitoring(
      'admin_validate_session',
      async () => {
        try {
          const response = await apiClient.get(
            ADMIN_AUTH_ENDPOINTS.VALIDATE_SESSION
          );

          return response;
        } catch (error: any) {
          return {
            success: false,
            error: {
              message: 'Session validation failed',
              code: 'session_validation_failed',
              status_code: error.status || 500
            }
          };
        }
      }
    );
  },
};