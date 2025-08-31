/**
 * Integration tests for the complete password reset flow
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useRouter } from 'next/navigation';
import { ForgotPasswordForm } from '@/components/auth/ForgotPasswordForm';
import { ResetPasswordForm } from '@/components/auth/ResetPasswordForm';
import { authApi } from '@/services/authApi';

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock the authApi
jest.mock('@/services/authApi');
const mockAuthApi = authApi as jest.Mocked<typeof authApi>;

// Mock error handling utilities
jest.mock('@/utils/passwordResetErrors', () => ({
  getPasswordResetErrorMessage: jest.fn((error) => error?.message || 'An error occurred'),
  logPasswordResetError: jest.fn(),
  isRetryablePasswordResetError: jest.fn(() => true),
  isValidTokenFormat: jest.fn(() => true),
  logPasswordResetSecurityEvent: jest.fn(),
}));

// Mock security monitoring
jest.mock('@/utils/securityMonitoring', () => ({
  withPerformanceMonitoring: jest.fn((operation, fn, details) => fn()),
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div>{children}</div>
);

describe('Password Reset Integration Tests', () => {
  const mockRouter = {
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
  });

  describe('Complete Password Reset Flow', () => {
    it('completes full password reset flow successfully', async () => {
      const user = userEvent.setup();
      
      // Mock API responses
      mockAuthApi.requestPasswordReset.mockResolvedValue({
        success: true,
        data: { success: true, message: 'Reset email sent' }
      });
      
      mockAuthApi.validateResetToken.mockResolvedValue({
        success: true,
        data: { valid: true }
      });
      
      mockAuthApi.resetPassword.mockResolvedValue({
        success: true,
        data: { success: true, message: 'Password reset successful' }
      });

      // Step 1: Request password reset
      const { rerender } = render(
        <TestWrapper>
          <ForgotPasswordForm 
            onSuccess={jest.fn()}
            onBackToLogin={jest.fn()}
          />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      // Should show success screen
      await waitFor(() => {
        expect(screen.getByText('Check Your Email')).toBeInTheDocument();
        expect(screen.getByText('test@example.com')).toBeInTheDocument();
      });

      expect(mockAuthApi.requestPasswordReset).toHaveBeenCalledWith('test@example.com');

      // Step 2: User clicks reset link (simulate with ResetPasswordForm)
      const token = 'abcd1234567890abcd1234567890abcd';
      
      rerender(
        <TestWrapper>
          <ResetPasswordForm 
            token={token}
            onSuccess={jest.fn()}
            onBackToLogin={jest.fn()}
          />
        </TestWrapper>
      );

      // Should validate token and show form
      await waitFor(() => {
        expect(mockAuthApi.validateResetToken).toHaveBeenCalledWith(token);
      });

      await waitFor(() => {
        expect(screen.getByText('Reset Your Password')).toBeInTheDocument();
      });

      // Step 3: Reset password
      const passwordInput = screen.getByLabelText('New Password');
      const confirmInput = screen.getByLabelText('Confirm New Password');
      const resetButton = screen.getByRole('button', { name: 'Reset Password' });

      await user.type(passwordInput, 'NewPassword123!');
      await user.type(confirmInput, 'NewPassword123!');
      await user.click(resetButton);

      // Should complete password reset
      await waitFor(() => {
        expect(mockAuthApi.resetPassword).toHaveBeenCalledWith(token, 'NewPassword123!');
      });

      await waitFor(() => {
        expect(screen.getByText('Password Reset Successful!')).toBeInTheDocument();
      });
    });

    it('handles errors at each step of the flow', async () => {
      const user = userEvent.setup();

      // Test error in password reset request
      mockAuthApi.requestPasswordReset.mockResolvedValue({
        success: false,
        error: {
          message: 'Rate limit exceeded',
          code: 'rate_limit_exceeded',
          status_code: 429
        }
      });

      render(
        <TestWrapper>
          <ForgotPasswordForm 
            onSuccess={jest.fn()}
            onBackToLogin={jest.fn()}
          />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Rate limit exceeded')).toBeInTheDocument();
      });
    });

    it('handles invalid token in reset flow', async () => {
      mockAuthApi.validateResetToken.mockResolvedValue({
        success: true,
        data: { valid: false, expired: true }
      });

      render(
        <TestWrapper>
          <ResetPasswordForm 
            token="invalid-token"
            onSuccess={jest.fn()}
            onBackToLogin={jest.fn()}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Invalid Reset Link')).toBeInTheDocument();
      });
    });

    it('handles password reset failure', async () => {
      const user = userEvent.setup();
      
      mockAuthApi.validateResetToken.mockResolvedValue({
        success: true,
        data: { valid: true }
      });
      
      mockAuthApi.resetPassword.mockResolvedValue({
        success: false,
        error: {
          message: 'Token expired during reset',
          code: 'token_expired',
          status_code: 400
        }
      });

      render(
        <TestWrapper>
          <ResetPasswordForm 
            token="valid-token"
            onSuccess={jest.fn()}
            onBackToLogin={jest.fn()}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Reset Your Password')).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText('New Password');
      const confirmInput = screen.getByLabelText('Confirm New Password');
      const resetButton = screen.getByRole('button', { name: 'Reset Password' });

      await user.type(passwordInput, 'NewPassword123!');
      await user.type(confirmInput, 'NewPassword123!');
      await user.click(resetButton);

      await waitFor(() => {
        expect(screen.getByText('Token expired during reset')).toBeInTheDocument();
      });
    });
  });

  describe('Form Validation Integration', () => {
    it('validates email format in forgot password form', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ForgotPasswordForm 
            onSuccess={jest.fn()}
            onBackToLogin={jest.fn()}
          />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });

      // Test various invalid email formats
      const invalidEmails = ['invalid', 'invalid@', '@domain.com', 'invalid.email'];
      
      for (const email of invalidEmails) {
        await user.clear(emailInput);
        await user.type(emailInput, email);
        await user.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
        });
      }

      // Test valid email
      await user.clear(emailInput);
      await user.type(emailInput, 'valid@example.com');
      
      await waitFor(() => {
        expect(screen.queryByText('Please enter a valid email address')).not.toBeInTheDocument();
      });
    });

    it('validates password strength in reset form', async () => {
      const user = userEvent.setup();
      
      mockAuthApi.validateResetToken.mockResolvedValue({
        success: true,
        data: { valid: true }
      });

      render(
        <TestWrapper>
          <ResetPasswordForm 
            token="valid-token"
            onSuccess={jest.fn()}
            onBackToLogin={jest.fn()}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText('New Password')).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText('New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });

      // Test weak passwords
      const weakPasswords = [
        'weak',
        'password',
        'PASSWORD',
        'password123',
        'Password123'
      ];

      for (const password of weakPasswords) {
        await user.clear(passwordInput);
        await user.type(passwordInput, password);
        await user.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText(/Password must/)).toBeInTheDocument();
        });
      }

      // Test strong password
      await user.clear(passwordInput);
      await user.type(passwordInput, 'StrongPassword123!');
      
      // Should not show validation error for strong password
      await waitFor(() => {
        expect(screen.queryByText(/Password must/)).not.toBeInTheDocument();
      });
    });

    it('validates password confirmation matching', async () => {
      const user = userEvent.setup();
      
      mockAuthApi.validateResetToken.mockResolvedValue({
        success: true,
        data: { valid: true }
      });

      render(
        <TestWrapper>
          <ResetPasswordForm 
            token="valid-token"
            onSuccess={jest.fn()}
            onBackToLogin={jest.fn()}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText('New Password')).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText('New Password');
      const confirmInput = screen.getByLabelText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });

      await user.type(passwordInput, 'StrongPassword123!');
      await user.type(confirmInput, 'DifferentPassword123!');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
      });

      // Test matching passwords
      await user.clear(confirmInput);
      await user.type(confirmInput, 'StrongPassword123!');
      
      await waitFor(() => {
        expect(screen.queryByText('Passwords do not match')).not.toBeInTheDocument();
      });
    });
  });

  describe('Loading States Integration', () => {
    it('shows loading states throughout the flow', async () => {
      const user = userEvent.setup();
      
      // Mock delayed API responses
      let resolveRequest: (value: any) => void;
      const requestPromise = new Promise((resolve) => {
        resolveRequest = resolve;
      });
      mockAuthApi.requestPasswordReset.mockReturnValue(requestPromise as any);

      render(
        <TestWrapper>
          <ForgotPasswordForm 
            onSuccess={jest.fn()}
            onBackToLogin={jest.fn()}
          />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      // Should show loading state
      expect(screen.getByText('Sending Reset Link...')).toBeInTheDocument();
      expect(submitButton).toBeDisabled();

      // Resolve the request
      resolveRequest!({
        success: true,
        data: { success: true, message: 'Reset email sent' }
      });

      await waitFor(() => {
        expect(screen.getByText('Check Your Email')).toBeInTheDocument();
      });
    });
  });

  describe('Error Recovery Integration', () => {
    it('allows retry after network errors', async () => {
      const user = userEvent.setup();
      
      // First call fails, second succeeds
      mockAuthApi.requestPasswordReset
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          success: true,
          data: { success: true, message: 'Reset email sent' }
        });

      render(
        <TestWrapper>
          <ForgotPasswordForm 
            onSuccess={jest.fn()}
            onBackToLogin={jest.fn()}
          />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      // Should show error
      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });

      // Should show retry button
      const retryButton = screen.getByRole('button', { name: 'Try Again' });
      await user.click(retryButton);

      // Should succeed on retry
      await waitFor(() => {
        expect(screen.getByText('Check Your Email')).toBeInTheDocument();
      });

      expect(mockAuthApi.requestPasswordReset).toHaveBeenCalledTimes(2);
    });
  });
});