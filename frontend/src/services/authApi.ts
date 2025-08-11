/**
 * Authentication API service for password reset functionality
 */
import { apiClient } from '@/utils/api';
import { ApiResponse } from '@/types';
import { API_ENDPOINTS } from '@/constants';
import { withPerformanceMonitoring } from '@/utils/securityMonitoring';

// TypeScript interfaces for API responses
export interface RequestPasswordResetResponse {
  success: boolean;
  message: string;
}

export interface ValidateResetTokenResponse {
  valid: boolean;
  expired?: boolean;
}

export interface ResetPasswordResponse {
  success: boolean;
  message: string;
}

export interface PasswordResetError {
  code: string;
  message: string;
  details?: unknown;
}

  /**
   * Request a password reset for the given email address
   * @param email - User's email address
   * @returns Promise with API response
   */
  async requestPasswordReset(email: string): Promise<ApiResponse<RequestPasswordResetResponse>> {
    return withPerformanceMonitoring(
      &apos;password_reset_request&apos;,
      async () => {
        try {
          const response = await apiClient.post<RequestPasswordResetResponse>(
            API_ENDPOINTS.AUTH.FORGOT_PASSWORD,
            { email }
          );
          return response;
        } catch (error) {
          return {
            success: false,
            error: {
              message: &apos;Failed to request password reset&apos;,
              code: &apos;request_failed&apos;,
              status_code: 500
            }
          };
        }
      },
      { email: email.substring(0, 3) + &apos;***&apos; }
    );
  },

  /**
   * Validate a password reset token
   * @param token - Reset token from email link
   * @returns Promise with validation result
   */
  async validateResetToken(token: string): Promise<ApiResponse<ValidateResetTokenResponse>> {
    return withPerformanceMonitoring(
      &apos;token_validation&apos;,
      async () => {
        try {
          const response = await apiClient.get<ValidateResetTokenResponse>(
            API_ENDPOINTS.AUTH.VALIDATE_RESET_TOKEN(token)
          );
          return response;
        } catch (error) {
          return {
            success: false,
            error: {
              message: &apos;Failed to validate reset token&apos;,
              code: &apos;validation_failed&apos;,
              status_code: 500
            }
          };
        }
      },
      { token: token.substring(0, 8) + &apos;...&apos; }
    );
  },

  /**
   * Reset password using a valid token
   * @param token - Reset token from email link
   * @param password - New password
   * @returns Promise with reset result
   */
  async resetPassword(token: string, password: string): Promise<ApiResponse<ResetPasswordResponse>> {
    return withPerformanceMonitoring(
      &apos;password_reset&apos;,
      async () => {
        try {
          const response = await apiClient.post<ResetPasswordResponse>(
            API_ENDPOINTS.AUTH.RESET_PASSWORD,
            { 
              token,
              password 
            }
          );
          return response;
        } catch (error) {
          return {
            success: false,
            error: {
              message: 'Failed to reset password',
              code: 'reset_failed',
              status_code: 500
            }
          };
        }
      },
      { token: token.substring(0, 8) + '...' }
    );
  }
};