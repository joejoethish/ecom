/**
 * Integration tests for authentication system with password reset
 * Tests the complete flow from login form to password reset and back
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { useRouter, useSearchParams } from 'next/navigation';
import { LoginForm } from '@/components/auth/LoginForm';
import { ForgotPasswordForm } from '@/components/auth/ForgotPasswordForm';
import { ResetPasswordForm } from '@/components/auth/ResetPasswordForm';
import { authApi } from '@/services/authApi';
import authSlice from '@/store/slices/authSlice';
import toast from 'react-hot-toast';

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

jest.mock(&apos;@/services/authApi&apos;, () => ({
  authApi: {
    requestPasswordReset: jest.fn(),
    validateResetToken: jest.fn(),
    resetPassword: jest.fn(),
  },
}));

jest.mock(&apos;react-hot-toast&apos;, () => ({
  success: jest.fn(),
  error: jest.fn(),
}));

jest.mock(&apos;@/utils/authIntegration&apos;, () => ({
  useAuthIntegration: () => ({
    onPasswordResetRequest: jest.fn(),
    onPasswordResetFailure: jest.fn(),
  }),
}));

const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
  back: jest.fn(),
};

const mockSearchParams = {
  get: jest.fn(),
};

const createMockStore = (initialState: unknown = {}) => {
  return configureStore({
    reducer: {
      auth: authSlice,
    },
    preloadedState: {
      auth: {
        user: null,
        loading: false,
        error: null,
        isAuthenticated: false,
        ...(initialState && &apos;auth&apos; in initialState ? initialState.auth : {}),
      },
    },
  });
};

describe(&apos;Authentication Integration&apos;, () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);
  });

  describe(&apos;Login Form Integration&apos;, () => {
    it(&apos;should display forgot password link&apos;, () => {
      const store = createMockStore();
      mockSearchParams.get.mockReturnValue(null);

      render(
        <Provider store={store}>
          <LoginForm />
        </Provider>
      );

      const forgotPasswordLink = screen.getByText(&apos;Forgot your password?&apos;);
      expect(forgotPasswordLink).toBeInTheDocument();
      expect(forgotPasswordLink.closest(&apos;a&apos;)).toHaveAttribute(&apos;href&apos;, &apos;/auth/forgot-password&apos;);
    });

    it(&apos;should show success message when redirected from password reset&apos;, () => {
      const store = createMockStore();
      mockSearchParams.get.mockReturnValue(&apos;password-reset-success&apos;);

      render(
        <Provider store={store}>
          <LoginForm />
        </Provider>
      );

      expect(toast.success).toHaveBeenCalledWith(
        &apos;Password reset successful! You can now log in with your new password.&apos;
      );
    });

    it(&apos;should have remember me functionality&apos;, () => {
      const store = createMockStore();
      mockSearchParams.get.mockReturnValue(null);

      render(
        <Provider store={store}>
          <LoginForm />
        </Provider>
      );

      const rememberMeCheckbox = screen.getByLabelText(&apos;Remember me&apos;);
      expect(rememberMeCheckbox).toBeInTheDocument();
      expect(rememberMeCheckbox).toHaveAttribute(&apos;type&apos;, &apos;checkbox&apos;);
    });
  });

  describe(&apos;Forgot Password Integration&apos;, () => {
    it(&apos;should have back to login functionality&apos;, async () => {
      const user = userEvent.setup();
      const mockBackToLogin = jest.fn();

      render(
        <ForgotPasswordForm onBackToLogin={mockBackToLogin} />
      );

      const backToLoginButton = screen.getByText(&apos;Back to Login&apos;);
      await user.click(backToLoginButton);

      expect(mockBackToLogin).toHaveBeenCalled();
    });

    it(&apos;should integrate with auth API for password reset request&apos;, async () => {
      const user = userEvent.setup();
      const mockOnSuccess = jest.fn();
      
      (authApi.requestPasswordReset as jest.Mock).mockResolvedValue({
        success: true,
      });

      render(
        <ForgotPasswordForm onSuccess={mockOnSuccess} />
      );

      const emailInput = screen.getByLabelText(&apos;Email Address&apos;);
      const submitButton = screen.getByText(&apos;Send Reset Link&apos;);

      await user.type(emailInput, &apos;test@example.com&apos;);
      await user.click(submitButton);

      await waitFor(() => {
        expect(authApi.requestPasswordReset).toHaveBeenCalledWith(&apos;test@example.com&apos;);
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });
  });

  describe(&apos;Reset Password Integration&apos;, () => {
    it(&apos;should validate token on component mount&apos;, async () => {
      const mockToken = &apos;valid-reset-token&apos;;
      
      (authApi.validateResetToken as jest.Mock).mockResolvedValue({
        success: true,
        data: { valid: true },
      });

      render(
        <ResetPasswordForm 
          token={mockToken}
          onSuccess={jest.fn()}
          onBackToLogin={jest.fn()}
        />
      );

      await waitFor(() => {
        expect(authApi.validateResetToken).toHaveBeenCalledWith(mockToken);
      });
    });

    it(&apos;should redirect to login after successful password reset&apos;, async () => {
      const user = userEvent.setup();
      const mockToken = &apos;valid-reset-token&apos;;
      const mockOnSuccess = jest.fn();
      
      (authApi.validateResetToken as jest.Mock).mockResolvedValue({
        success: true,
        data: { valid: true },
      });

      (authApi.resetPassword as jest.Mock).mockResolvedValue({
        success: true,
      });

      render(
        <ResetPasswordForm 
          token={mockToken}
          onSuccess={mockOnSuccess}
          onBackToLogin={jest.fn()}
        />
      );

      // Wait for token validation
      await waitFor(() => {
        expect(screen.getByLabelText(&apos;New Password&apos;)).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText(&apos;New Password&apos;);
      const confirmInput = screen.getByLabelText(&apos;Confirm New Password&apos;);
      const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Reset Password&apos; });

      await user.type(passwordInput, &apos;NewPassword123!&apos;);
      await user.type(confirmInput, &apos;NewPassword123!&apos;);
      await user.click(submitButton);

      await waitFor(() => {
        expect(authApi.resetPassword).toHaveBeenCalledWith(mockToken, &apos;NewPassword123!&apos;);
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    it(&apos;should handle invalid token gracefully&apos;, async () => {
      const mockToken = &apos;invalid-token&apos;;
      
      (authApi.validateResetToken as jest.Mock).mockResolvedValue({
        success: false,
        error: { code: &apos;TOKEN_INVALID&apos;, message: &apos;Invalid token&apos; },
      });

      render(
        <ResetPasswordForm 
          token={mockToken}
          onSuccess={jest.fn()}
          onBackToLogin={jest.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/invalid.*token/i)).toBeInTheDocument();
      });
    });
  });

  describe(&apos;Complete Password Reset Flow&apos;, () => {
    it(&apos;should support complete flow from login to reset and back&apos;, async () => {
      const user = userEvent.setup();
      
      // Mock API responses
      (authApi.requestPasswordReset as jest.Mock).mockResolvedValue({
        success: true,
      });
      
      (authApi.validateResetToken as jest.Mock).mockResolvedValue({
        success: true,
        data: { valid: true },
      });
      
      (authApi.resetPassword as jest.Mock).mockResolvedValue({
        success: true,
      });

      // Step 1: Login form with forgot password link
      const store = createMockStore();
      mockSearchParams.get.mockReturnValue(null);

        <Provider store={store}>
          <LoginForm />
        </Provider>
      );

      const forgotPasswordLink = screen.getByText(&apos;Forgot your password?&apos;);
      expect(forgotPasswordLink).toBeInTheDocument();

      // Step 2: Forgot password form
      rerender(
        <ForgotPasswordForm 
          onSuccess={jest.fn()}
          onBackToLogin={jest.fn()}
        />
      );

      const emailInput = screen.getByLabelText(&apos;Email Address&apos;);
      const sendResetButton = screen.getByText(&apos;Send Reset Link&apos;);

      await user.type(emailInput, &apos;test@example.com&apos;);
      await user.click(sendResetButton);

      await waitFor(() => {
        expect(authApi.requestPasswordReset).toHaveBeenCalledWith(&apos;test@example.com&apos;);
      });

      // Step 3: Reset password form
      const mockToken = &apos;valid-reset-token&apos;;
      rerender(
        <ResetPasswordForm 
          token={mockToken}
          onSuccess={jest.fn()}
          onBackToLogin={jest.fn()}
        />
      );

      await waitFor(() => {
        expect(authApi.validateResetToken).toHaveBeenCalledWith(mockToken);
      });

      // Wait for form to be ready
      await waitFor(() => {
        expect(screen.getByLabelText(&apos;New Password&apos;)).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText(&apos;New Password&apos;);
      const confirmInput = screen.getByLabelText(&apos;Confirm New Password&apos;);
      const resetButton = screen.getByRole(&apos;button&apos;, { name: &apos;Reset Password&apos; });

      await user.type(passwordInput, &apos;NewPassword123!&apos;);
      await user.type(confirmInput, &apos;NewPassword123!&apos;);
      await user.click(resetButton);

      await waitFor(() => {
        expect(authApi.resetPassword).toHaveBeenCalledWith(mockToken, &apos;NewPassword123!&apos;);
      });

      // Step 4: Back to login with success message
      mockSearchParams.get.mockReturnValue(&apos;password-reset-success&apos;);
      
      rerender(
        <Provider store={store}>
          <LoginForm />
        </Provider>
      );

      expect(toast.success).toHaveBeenCalledWith(
        &apos;Password reset successful! You can now log in with your new password.&apos;
      );
    });
  });

  describe(&apos;User Model Integration&apos;, () => {
    it(&apos;should work with different user types&apos;, async () => {
      const user = userEvent.setup();
      
      // Test that password reset works regardless of user type
      const testCases = [
        { email: &apos;customer@example.com&apos;, userType: &apos;customer&apos; },
        { email: &apos;seller@example.com&apos;, userType: &apos;seller&apos; },
        { email: &apos;admin@example.com&apos;, userType: &apos;admin&apos; },
      ];

      for (const testCase of testCases) {
        (authApi.requestPasswordReset as jest.Mock).mockResolvedValue({
          success: true,
        });

        render(
          <ForgotPasswordForm onSuccess={jest.fn()} />
        );

        const emailInput = screen.getByLabelText('Email Address');
        const submitButton = screen.getByText('Send Reset Link');

        await user.clear(emailInput);
        await user.type(emailInput, testCase.email);
        await user.click(submitButton);

        await waitFor(() => {
          expect(authApi.requestPasswordReset).toHaveBeenCalledWith(testCase.email);
        });

        // Clean up for next iteration
        jest.clearAllMocks();
      }
    });
  });

  describe('Authentication Middleware Integration', () => {
    it('should handle route protection correctly', () => {
      // This test verifies that the middleware configuration includes
      // password reset routes in guest routes
      import { GUEST_ROUTES }  from '@/middleware/auth';
      
      expect(GUEST_ROUTES).toContain('/auth/forgot-password');
      expect(GUEST_ROUTES).toContain('/auth/reset-password');
      expect(GUEST_ROUTES).toContain('/auth/login');
      expect(GUEST_ROUTES).toContain('/auth/register');
    });
  });
});