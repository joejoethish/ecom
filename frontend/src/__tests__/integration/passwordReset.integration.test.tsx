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
jest.mock(&apos;@/services/authApi&apos;);
const mockAuthApi = authApi as jest.Mocked<typeof authApi>;

// Mock error handling utilities
jest.mock(&apos;@/utils/passwordResetErrors&apos;, () => ({
  getPasswordResetErrorMessage: jest.fn((error) => error?.message || &apos;An error occurred&apos;),
  logPasswordResetError: jest.fn(),
  isRetryablePasswordResetError: jest.fn(() => true),
  isValidTokenFormat: jest.fn(() => true),
  logPasswordResetSecurityEvent: jest.fn(),
}));

// Mock security monitoring
jest.mock(&apos;@/utils/securityMonitoring&apos;, () => ({
  withPerformanceMonitoring: jest.fn((operation, fn, details) => fn()),
}));

  <div>{children}</div>
);

describe(&apos;Password Reset Integration Tests&apos;, () => {
  const mockRouter = {
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
  });

  describe(&apos;Complete Password Reset Flow&apos;, () => {
    it(&apos;completes full password reset flow successfully&apos;, async () => {
      const user = userEvent.setup();
      
      // Mock API responses
      mockAuthApi.requestPasswordReset.mockResolvedValue({
        success: true,
        data: { success: true, message: &apos;Reset email sent&apos; }
      });
      
      mockAuthApi.validateResetToken.mockResolvedValue({
        success: true,
        data: { valid: true }
      });
      
      mockAuthApi.resetPassword.mockResolvedValue({
        success: true,
        data: { success: true, message: &apos;Password reset successful&apos; }
      });

      // Step 1: Request password reset
        <TestWrapper>
          <ForgotPasswordForm 
            onSuccess={jest.fn()}
            onBackToLogin={jest.fn()}
          />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText(&apos;Email Address&apos;);
      const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Send Reset Link&apos; });

      await user.type(emailInput, &apos;test@example.com&apos;);
      await user.click(submitButton);

      // Should show success screen
      await waitFor(() => {
        expect(screen.getByText(&apos;Check Your Email&apos;)).toBeInTheDocument();
        expect(screen.getByText(&apos;test@example.com&apos;)).toBeInTheDocument();
      });

      expect(mockAuthApi.requestPasswordReset).toHaveBeenCalledWith(&apos;test@example.com&apos;);

      // Step 2: User clicks reset link (simulate with ResetPasswordForm)
      const token = &apos;abcd1234567890abcd1234567890abcd&apos;;
      
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
        expect(screen.getByText(&apos;Reset Your Password&apos;)).toBeInTheDocument();
      });

      // Step 3: Reset password
      const passwordInput = screen.getByLabelText(&apos;New Password&apos;);
      const confirmInput = screen.getByLabelText(&apos;Confirm New Password&apos;);
      const resetButton = screen.getByRole(&apos;button&apos;, { name: &apos;Reset Password&apos; });

      await user.type(passwordInput, &apos;NewPassword123!&apos;);
      await user.type(confirmInput, &apos;NewPassword123!&apos;);
      await user.click(resetButton);

      // Should complete password reset
      await waitFor(() => {
        expect(mockAuthApi.resetPassword).toHaveBeenCalledWith(token, &apos;NewPassword123!&apos;);
      });

      await waitFor(() => {
        expect(screen.getByText(&apos;Password Reset Successful!&apos;)).toBeInTheDocument();
      });
    });

    it(&apos;handles errors at each step of the flow&apos;, async () => {
      const user = userEvent.setup();

      // Test error in password reset request
      mockAuthApi.requestPasswordReset.mockResolvedValue({
        success: false,
        error: {
          message: &apos;Rate limit exceeded&apos;,
          code: &apos;rate_limit_exceeded&apos;,
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

      const emailInput = screen.getByLabelText(&apos;Email Address&apos;);
      const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Send Reset Link&apos; });

      await user.type(emailInput, &apos;test@example.com&apos;);
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(&apos;Rate limit exceeded&apos;)).toBeInTheDocument();
      });
    });

    it(&apos;handles invalid token in reset flow&apos;, async () => {
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
        expect(screen.getByText(&apos;Invalid Reset Link&apos;)).toBeInTheDocument();
      });
    });

    it(&apos;handles password reset failure&apos;, async () => {
      const user = userEvent.setup();
      
      mockAuthApi.validateResetToken.mockResolvedValue({
        success: true,
        data: { valid: true }
      });
      
      mockAuthApi.resetPassword.mockResolvedValue({
        success: false,
        error: {
          message: &apos;Token expired during reset&apos;,
          code: &apos;token_expired&apos;,
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
        expect(screen.getByText(&apos;Reset Your Password&apos;)).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText(&apos;New Password&apos;);
      const confirmInput = screen.getByLabelText(&apos;Confirm New Password&apos;);
      const resetButton = screen.getByRole(&apos;button&apos;, { name: &apos;Reset Password&apos; });

      await user.type(passwordInput, &apos;NewPassword123!&apos;);
      await user.type(confirmInput, &apos;NewPassword123!&apos;);
      await user.click(resetButton);

      await waitFor(() => {
        expect(screen.getByText(&apos;Token expired during reset&apos;)).toBeInTheDocument();
      });
    });
  });

  describe(&apos;Form Validation Integration&apos;, () => {
    it(&apos;validates email format in forgot password form&apos;, async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ForgotPasswordForm 
            onSuccess={jest.fn()}
            onBackToLogin={jest.fn()}
          />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText(&apos;Email Address&apos;);
      const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Send Reset Link&apos; });

      // Test various invalid email formats
      const invalidEmails = [&apos;invalid&apos;, &apos;invalid@&apos;, &apos;@domain.com&apos;, &apos;invalid.email&apos;];
      
      for (const email of invalidEmails) {
        await user.clear(emailInput);
        await user.type(emailInput, email);
        await user.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText(&apos;Please enter a valid email address&apos;)).toBeInTheDocument();
        });
      }

      // Test valid email
      await user.clear(emailInput);
      await user.type(emailInput, &apos;valid@example.com&apos;);
      
      await waitFor(() => {
        expect(screen.queryByText(&apos;Please enter a valid email address&apos;)).not.toBeInTheDocument();
      });
    });

    it(&apos;validates password strength in reset form&apos;, async () => {
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
        expect(screen.getByLabelText(&apos;New Password&apos;)).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText(&apos;New Password&apos;);
      const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Reset Password&apos; });

      // Test weak passwords
      const weakPasswords = [
        &apos;weak&apos;,
        &apos;password&apos;,
        &apos;PASSWORD&apos;,
        &apos;password123&apos;,
        &apos;Password123&apos;
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
      await user.type(passwordInput, &apos;StrongPassword123!&apos;);
      
      // Should not show validation error for strong password
      await waitFor(() => {
        expect(screen.queryByText(/Password must/)).not.toBeInTheDocument();
      });
    });

    it(&apos;validates password confirmation matching&apos;, async () => {
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
        expect(screen.getByLabelText(&apos;New Password&apos;)).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText(&apos;New Password&apos;);
      const confirmInput = screen.getByLabelText(&apos;Confirm New Password&apos;);
      const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Reset Password&apos; });

      await user.type(passwordInput, &apos;StrongPassword123!&apos;);
      await user.type(confirmInput, &apos;DifferentPassword123!&apos;);
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(&apos;Passwords do not match&apos;)).toBeInTheDocument();
      });

      // Test matching passwords
      await user.clear(confirmInput);
      await user.type(confirmInput, &apos;StrongPassword123!&apos;);
      
      await waitFor(() => {
        expect(screen.queryByText(&apos;Passwords do not match&apos;)).not.toBeInTheDocument();
      });
    });
  });

  describe(&apos;Loading States Integration&apos;, () => {
    it(&apos;shows loading states throughout the flow&apos;, async () => {
      const user = userEvent.setup();
      
      // Mock delayed API responses
      let resolveRequest: (value: unknown) => void;
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

      const emailInput = screen.getByLabelText(&apos;Email Address&apos;);
      const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Send Reset Link&apos; });

      await user.type(emailInput, &apos;test@example.com&apos;);
      await user.click(submitButton);

      // Should show loading state
      expect(screen.getByText(&apos;Sending Reset Link...&apos;)).toBeInTheDocument();
      expect(submitButton).toBeDisabled();

      // Resolve the request
      resolveRequest!({
        success: true,
        data: { success: true, message: &apos;Reset email sent&apos; }
      });

      await waitFor(() => {
        expect(screen.getByText(&apos;Check Your Email&apos;)).toBeInTheDocument();
      });
    });
  });

  describe(&apos;Error Recovery Integration&apos;, () => {
    it(&apos;allows retry after network errors&apos;, async () => {
      const user = userEvent.setup();
      
      // First call fails, second succeeds
      mockAuthApi.requestPasswordReset
        .mockRejectedValueOnce(new Error(&apos;Network error&apos;))
        .mockResolvedValueOnce({
          success: true,
          data: { success: true, message: &apos;Reset email sent&apos; }
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