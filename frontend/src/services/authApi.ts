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
  details?: any;
}

export interface EmailVerificationResponse {
  success: boolean;
  message: string;
  user?: any;
}

export interface ResendVerificationResponse {
  success: boolean;
  message: string;
}

export const authApi = {
  /**
   * Request a password reset for the given email address
   * @param email - User's email address
   * @returns Promise with API response
   */
  async requestPasswordReset(email: string): Promise<ApiResponse<RequestPasswordResetResponse>> {
    return withPerformanceMonitoring(
      'password_reset_request',
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
              message: 'Failed to request password reset',
              code: 'request_failed',
              status_code: 500
            }
          };
        }
      },
      { email: email.substring(0, 3) + '***' }
    );
  },

  /**
   * Validate a password reset token
   * @param token - Reset token from email link
   * @returns Promise with validation result
   */
  async validateResetToken(token: string): Promise<ApiResponse<ValidateResetTokenResponse>> {
    return withPerformanceMonitoring(
      'token_validation',
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
              message: 'Failed to validate reset token',
              code: 'validation_failed',
              status_code: 500
            }
          };
        }
      },
      { token: token.substring(0, 8) + '...' }
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
      'password_reset',
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
  },

  /**
   * Verify email using a verification token
   * @param token - Email verification token from email link
   * @returns Promise with verification result
   */
  async verifyEmail(token: string): Promise<ApiResponse<EmailVerificationResponse>> {
    return withPerformanceMonitoring(
      'email_verification',
      async () => {
        try {
          const response = await apiClient.get<EmailVerificationResponse>(
            API_ENDPOINTS.AUTH.VERIFY_EMAIL(token)
          );
          return response;
        } catch (error) {
          return {
            success: false,
            error: {
              message: 'Failed to verify email',
              code: 'verification_failed',
              status_code: 500
            }
          };
        }
      },
      { token: token.substring(0, 8) + '...' }
    );
  },

  /**
   * Resend email verification
   * @returns Promise with resend result
   */
  async resendVerification(): Promise<ApiResponse<ResendVerificationResponse>> {
    return withPerformanceMonitoring(
      'resend_verification',
      async () => {
        try {
          const response = await apiClient.post<ResendVerificationResponse>(
            API_ENDPOINTS.AUTH.RESEND_VERIFICATION,
            {}
          );
          return response;
        } catch (error) {
          return {
            success: false,
            error: {
              message: 'Failed to resend verification email',
              code: 'resend_failed',
              status_code: 500
            }
          };
        }
      }
    );
  }
};