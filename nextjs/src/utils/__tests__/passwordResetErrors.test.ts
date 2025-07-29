import {
  PASSWORD_RESET_ERROR_CODES,
  PASSWORD_RESET_ERROR_MESSAGES,
  isRetryablePasswordResetError,
  getPasswordResetErrorMessage,
  logPasswordResetError,
  handlePasswordResetApiError,
  retryPasswordResetOperation,
  isValidTokenFormat,
} from '../passwordResetErrors';

// Mock the base error handling utilities
jest.mock('../errorHandling', () => ({
  extractErrorInfo: jest.fn((error) => ({
    message: error?.message || 'Unknown error',
    code: error?.code || 'unknown_error',
    status_code: error?.status_code || 0,
  })),
  getDisplayErrorMessage: jest.fn((error) => error?.message || 'An error occurred'),
  logError: jest.fn(),
}));

// Mock security monitoring
jest.mock('../securityMonitoring', () => ({
  logSecurityEvent: jest.fn(),
}));

describe('passwordResetErrors', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('PASSWORD_RESET_ERROR_CODES', () => {
    it('contains all expected error codes', () => {
      expect(PASSWORD_RESET_ERROR_CODES.TOKEN_INVALID).toBe('token_invalid');
      expect(PASSWORD_RESET_ERROR_CODES.TOKEN_EXPIRED).toBe('token_expired');
      expect(PASSWORD_RESET_ERROR_CODES.EMAIL_NOT_FOUND).toBe('email_not_found');
      expect(PASSWORD_RESET_ERROR_CODES.PASSWORD_TOO_WEAK).toBe('password_too_weak');
      expect(PASSWORD_RESET_ERROR_CODES.RATE_LIMIT_EXCEEDED).toBe('rate_limit_exceeded');
      expect(PASSWORD_RESET_ERROR_CODES.NETWORK_ERROR).toBe('network_error');
    });
  });

  describe('PASSWORD_RESET_ERROR_MESSAGES', () => {
    it('provides user-friendly messages for all error codes', () => {
      expect(PASSWORD_RESET_ERROR_MESSAGES[PASSWORD_RESET_ERROR_CODES.TOKEN_INVALID])
        .toBe('This password reset link is invalid. Please request a new one.');
      expect(PASSWORD_RESET_ERROR_MESSAGES[PASSWORD_RESET_ERROR_CODES.TOKEN_EXPIRED])
        .toBe('This password reset link has expired. Please request a new one.');
      expect(PASSWORD_RESET_ERROR_MESSAGES[PASSWORD_RESET_ERROR_CODES.EMAIL_NOT_FOUND])
        .toBe('If an account with this email exists, you will receive a password reset link.');
    });
  });

  describe('isRetryablePasswordResetError', () => {
    it('returns true for retryable errors', () => {
      expect(isRetryablePasswordResetError(PASSWORD_RESET_ERROR_CODES.NETWORK_ERROR)).toBe(true);
      expect(isRetryablePasswordResetError(PASSWORD_RESET_ERROR_CODES.SERVER_ERROR)).toBe(true);
      expect(isRetryablePasswordResetError(PASSWORD_RESET_ERROR_CODES.EMAIL_SEND_FAILED)).toBe(true);
    });

    it('returns false for non-retryable errors', () => {
      expect(isRetryablePasswordResetError(PASSWORD_RESET_ERROR_CODES.TOKEN_INVALID)).toBe(false);
      expect(isRetryablePasswordResetError(PASSWORD_RESET_ERROR_CODES.TOKEN_EXPIRED)).toBe(false);
      expect(isRetryablePasswordResetError(PASSWORD_RESET_ERROR_CODES.PASSWORD_TOO_WEAK)).toBe(false);
    });
  });

  describe('getPasswordResetErrorMessage', () => {
    it('returns specific message for password reset errors', () => {
      const error = { code: PASSWORD_RESET_ERROR_CODES.TOKEN_INVALID };
      const message = getPasswordResetErrorMessage(error);
      expect(message).toBe(PASSWORD_RESET_ERROR_MESSAGES[PASSWORD_RESET_ERROR_CODES.TOKEN_INVALID]);
    });

    it('falls back to general error handling for unknown codes', () => {
      const error = { code: 'unknown_code', message: 'Unknown error' };
      const message = getPasswordResetErrorMessage(error);
      expect(message).toBe('Unknown error');
    });
  });

  describe('handlePasswordResetApiError', () => {
    it('throws error with correct properties', () => {
      const response = {
        error: {
          code: PASSWORD_RESET_ERROR_CODES.TOKEN_EXPIRED,
          message: 'Token expired',
          status_code: 400,
          details: { token: 'abc123' }
        }
      };

      expect(() => handlePasswordResetApiError(response)).toThrow('Token expired');
    });

    it('handles response without error details', () => {
      const response = { error: null };
      
      expect(() => handlePasswordResetApiError(response)).toThrow();
    });
  });

  describe('retryPasswordResetOperation', () => {
    it('retries operation on retryable errors', async () => {
      const mockOperation = jest.fn()
        .mockRejectedValueOnce({ code: PASSWORD_RESET_ERROR_CODES.NETWORK_ERROR })
        .mockResolvedValueOnce('success');

      const result = await retryPasswordResetOperation(mockOperation, 'test');

      expect(mockOperation).toHaveBeenCalledTimes(2);
      expect(result).toBe('success');
    });

    it('does not retry on non-retryable errors', async () => {
      const mockOperation = jest.fn()
        .mockRejectedValue({ code: PASSWORD_RESET_ERROR_CODES.TOKEN_INVALID });

      await expect(retryPasswordResetOperation(mockOperation, 'test'))
        .rejects.toEqual({ code: PASSWORD_RESET_ERROR_CODES.TOKEN_INVALID });

      expect(mockOperation).toHaveBeenCalledTimes(1);
    });

    it('respects max retry limit', async () => {
      const mockOperation = jest.fn()
        .mockRejectedValue({ code: PASSWORD_RESET_ERROR_CODES.NETWORK_ERROR });

      await expect(retryPasswordResetOperation(mockOperation, 'test'))
        .rejects.toEqual({ code: PASSWORD_RESET_ERROR_CODES.NETWORK_ERROR });

      expect(mockOperation).toHaveBeenCalledTimes(4); // Initial + 3 retries
    });
  });

  describe('isValidTokenFormat', () => {
    it('validates correct token format', () => {
      expect(isValidTokenFormat('abcd1234567890abcd1234567890abcd')).toBe(true);
      expect(isValidTokenFormat('ABCD1234567890ABCD1234567890ABCD')).toBe(true);
      expect(isValidTokenFormat('abcd1234567890abcd1234567890abcd1234567890')).toBe(true);
    });

    it('rejects invalid token formats', () => {
      expect(isValidTokenFormat('short')).toBe(false);
      expect(isValidTokenFormat('contains-invalid-chars!')).toBe(false);
      expect(isValidTokenFormat('abcd1234567890abcd1234567890ab')).toBe(false); // Too short
      expect(isValidTokenFormat('')).toBe(false);
    });
  });

  describe('logPasswordResetError', () => {
    it('logs error with context and additional data', () => {
      const error = new Error('Test error');
      const context = 'testContext';
      const additionalData = { email: 'test@example.com' };

      logPasswordResetError(error, context, additionalData);

      // Should call the base logError function
      const { logError } = require('../errorHandling');
      expect(logError).toHaveBeenCalledWith(error, 'PasswordReset.testContext');
    });
  });

  describe('logPasswordResetSecurityEvent', () => {
    it('logs security events with proper format', () => {
      const mockLogSecurityEvent = require('../securityMonitoring').logSecurityEvent;
      
      const { logPasswordResetSecurityEvent } = require('../passwordResetErrors');
      
      logPasswordResetSecurityEvent('request', {
        email: 'test@example.com',
        success: true,
        ipAddress: '192.168.1.1'
      });

      expect(mockLogSecurityEvent).toHaveBeenCalledWith(
        'password_reset',
        'password_reset_request',
        'low',
        expect.objectContaining({
          success: true,
          email: 'test@example.com'
        }),
        expect.objectContaining({
          ipAddress: '192.168.1.1'
        })
      );
    });

    it('sets appropriate severity for failed operations', () => {
      const mockLogSecurityEvent = require('../securityMonitoring').logSecurityEvent;
      
      const { logPasswordResetSecurityEvent } = require('../passwordResetErrors');
      
      logPasswordResetSecurityEvent('validate', {
        success: false,
        errorCode: 'token_invalid'
      });

      expect(mockLogSecurityEvent).toHaveBeenCalledWith(
        'password_reset',
        'password_reset_validate',
        'medium',
        expect.objectContaining({
          success: false,
          errorCode: 'token_invalid'
        }),
        expect.objectContaining({})
      );
    });
  });
});