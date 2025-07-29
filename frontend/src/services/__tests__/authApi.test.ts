import { authApi } from '../authApi';
import { apiClient } from '@/utils/api';

// Mock the API client
jest.mock('@/utils/api');
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

// Mock performance monitoring
jest.mock('@/utils/securityMonitoring', () => ({
  withPerformanceMonitoring: jest.fn((operation, fn, details) => fn()),
}));

describe('authApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('requestPasswordReset', () => {
    it('makes correct API call for password reset request', async () => {
      const mockResponse = {
        success: true,
        data: { success: true, message: 'Reset email sent' }
      };
      mockApiClient.post.mockResolvedValue(mockResponse);

      const result = await authApi.requestPasswordReset('test@example.com');

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/auth/forgot-password/',
        { email: 'test@example.com' }
      );
      expect(result).toEqual(mockResponse);
    });

    it('handles API errors gracefully', async () => {
      mockApiClient.post.mockRejectedValue(new Error('Network error'));

      const result = await authApi.requestPasswordReset('test@example.com');

      expect(result).toEqual({
        success: false,
        error: {
          message: 'Failed to request password reset',
          code: 'request_failed',
          status_code: 500
        }
      });
    });

    it('validates email parameter', async () => {
      const mockResponse = {
        success: true,
        data: { success: true, message: 'Reset email sent' }
      };
      mockApiClient.post.mockResolvedValue(mockResponse);

      await authApi.requestPasswordReset('user@domain.com');

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/auth/forgot-password/',
        { email: 'user@domain.com' }
      );
    });
  });

  describe('validateResetToken', () => {
    it('makes correct API call for token validation', async () => {
      const token = 'abcd1234567890abcd1234567890abcd';
      const mockResponse = {
        success: true,
        data: { valid: true }
      };
      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await authApi.validateResetToken(token);

      expect(mockApiClient.get).toHaveBeenCalledWith(
        `/auth/validate-reset-token/${token}/`
      );
      expect(result).toEqual(mockResponse);
    });

    it('handles invalid token response', async () => {
      const token = 'invalid-token';
      const mockResponse = {
        success: true,
        data: { valid: false, expired: true }
      };
      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await authApi.validateResetToken(token);

      expect(result).toEqual(mockResponse);
    });

    it('handles API errors gracefully', async () => {
      const token = 'abcd1234567890abcd1234567890abcd';
      mockApiClient.get.mockRejectedValue(new Error('Server error'));

      const result = await authApi.validateResetToken(token);

      expect(result).toEqual({
        success: false,
        error: {
          message: 'Failed to validate reset token',
          code: 'validation_failed',
          status_code: 500
        }
      });
    });
  });

  describe('resetPassword', () => {
    it('makes correct API call for password reset', async () => {
      const token = 'abcd1234567890abcd1234567890abcd';
      const password = 'NewPassword123!';
      const mockResponse = {
        success: true,
        data: { success: true, message: 'Password reset successful' }
      };
      mockApiClient.post.mockResolvedValue(mockResponse);

      const result = await authApi.resetPassword(token, password);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/auth/reset-password/',
        { token, password }
      );
      expect(result).toEqual(mockResponse);
    });

    it('handles password reset failure', async () => {
      const token = 'abcd1234567890abcd1234567890abcd';
      const password = 'NewPassword123!';
      const mockResponse = {
        success: false,
        error: {
          message: 'Token expired',
          code: 'token_expired',
          status_code: 400
        }
      };
      mockApiClient.post.mockResolvedValue(mockResponse);

      const result = await authApi.resetPassword(token, password);

      expect(result).toEqual(mockResponse);
    });

    it('handles API errors gracefully', async () => {
      const token = 'abcd1234567890abcd1234567890abcd';
      const password = 'NewPassword123!';
      mockApiClient.post.mockRejectedValue(new Error('Network error'));

      const result = await authApi.resetPassword(token, password);

      expect(result).toEqual({
        success: false,
        error: {
          message: 'Failed to reset password',
          code: 'reset_failed',
          status_code: 500
        }
      });
    });

    it('validates required parameters', async () => {
      const token = 'abcd1234567890abcd1234567890abcd';
      const password = 'NewPassword123!';
      const mockResponse = {
        success: true,
        data: { success: true, message: 'Password reset successful' }
      };
      mockApiClient.post.mockResolvedValue(mockResponse);

      await authApi.resetPassword(token, password);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/auth/reset-password/',
        { token, password }
      );
    });
  });

  describe('error handling', () => {
    it('returns consistent error format for all methods', async () => {
      mockApiClient.post.mockRejectedValue(new Error('Test error'));
      mockApiClient.get.mockRejectedValue(new Error('Test error'));

      const resetResult = await authApi.requestPasswordReset('test@example.com');
      const validateResult = await authApi.validateResetToken('token');
      const passwordResult = await authApi.resetPassword('token', 'password');

      // All should have consistent error structure
      expect(resetResult.success).toBe(false);
      expect(resetResult.error).toBeDefined();
      expect(resetResult.error?.message).toBeDefined();
      expect(resetResult.error?.code).toBeDefined();
      expect(resetResult.error?.status_code).toBeDefined();

      expect(validateResult.success).toBe(false);
      expect(validateResult.error).toBeDefined();

      expect(passwordResult.success).toBe(false);
      expect(passwordResult.error).toBeDefined();
    });
  });
});