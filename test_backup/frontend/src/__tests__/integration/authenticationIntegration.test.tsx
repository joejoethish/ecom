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

jest.mock('@/services/authApi', () => ({
  authApi: {
    requestPasswordReset: jest.fn(),
    validateResetToken: jest.fn(),
    resetPassword: jest.fn(),
  },
}));

jest.mock('react-hot-toast', () => ({
  success: jest.fn(),
  error: jest.fn(),
}));

jest.mock('@/utils/authIntegration', () => ({
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

const createMockStore = (initialState: any = {}) => {
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
        ...(initialState && 'auth' in initialState ? initialState.auth : {}),
      },
    },
  });
};

describe('Authentication Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);
  });

  describe('Login Form Integration', () => {
    it('should display forgot password link', () => {
      const store = createMockStore();
      mockSearchParams.get.mockReturnValue(null);

      render(
        <Provider store={store}>
          <LoginForm />
        </Provider>
      );

      const forgotPasswordLink = screen.getByText('Forgot your password?');
      expect(forgotPasswordLink).toBeInTheDocument();
      expect(forgotPasswordLink.closest('a')).toHaveAttribute('href', '/auth/forgot-password');
    });

    it('should show success message when redirected from password reset', () => {
      const store = createMockStore();
      mockSearchParams.get.mockReturnValue('password-reset-success');

      render(
        <Provider store={store}>
          <LoginForm />
        </Provider>
      );

      expect(toast.success).toHaveBeenCalledWith(
        'Password reset successful! You can now log in with your new password.'
      );
    });

    it('should have remember me functionality', () => {
      const store = createMockStore();
      mockSearchParams.get.mockReturnValue(null);

      render(
        <Provider store={store}>
          <LoginForm />
        </Provider>
      );

      const rememberMeCheckbox = screen.getByLabelText('Remember me');
      expect(rememberMeCheckbox).toBeInTheDocument();
      expect(rememberMeCheckbox).toHaveAttribute('type', 'checkbox');
    });
  });

  describe('Forgot Password Integration', () => {
    it('should have back to login functionality', async () => {
      const user = userEvent.setup();
      const mockBackToLogin = jest.fn();

      render(
        <ForgotPasswordForm onBackToLogin={mockBackToLogin} />
      );

      const backToLoginButton = screen.getByText('Back to Login');
      await user.click(backToLoginButton);

      expect(mockBackToLogin).toHaveBeenCalled();
    });

    it('should integrate with auth API for password reset request', async () => {
      const user = userEvent.setup();
      const mockOnSuccess = jest.fn();
      
      (authApi.requestPasswordReset as jest.Mock).mockResolvedValue({
        success: true,
      });

      render(
        <ForgotPasswordForm onSuccess={mockOnSuccess} />
      );

      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByText('Send Reset Link');

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(authApi.requestPasswordReset).toHaveBeenCalledWith('test@example.com');
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });
  });

  describe('Reset Password Integration', () => {
    it('should validate token on component mount', async () => {
      const mockToken = 'valid-reset-token';
      
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

    it('should redirect to login after successful password reset', async () => {
      const user = userEvent.setup();
      const mockToken = 'valid-reset-token';
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
        expect(screen.getByLabelText('New Password')).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText('New Password');
      const confirmInput = screen.getByLabelText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });

      await user.type(passwordInput, 'NewPassword123!');
      await user.type(confirmInput, 'NewPassword123!');
      await user.click(submitButton);

      await waitFor(() => {
        expect(authApi.resetPassword).toHaveBeenCalledWith(mockToken, 'NewPassword123!');
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    it('should handle invalid token gracefully', async () => {
      const mockToken = 'invalid-token';
      
      (authApi.validateResetToken as jest.Mock).mockResolvedValue({
        success: false,
        error: { code: 'TOKEN_INVALID', message: 'Invalid token' },
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

  describe('Complete Password Reset Flow', () => {
    it('should support complete flow from login to reset and back', async () => {
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

      const { rerender } = render(
        <Provider store={store}>
          <LoginForm />
        </Provider>
      );

      const forgotPasswordLink = screen.getByText('Forgot your password?');
      expect(forgotPasswordLink).toBeInTheDocument();

      // Step 2: Forgot password form
      rerender(
        <ForgotPasswordForm 
          onSuccess={jest.fn()}
          onBackToLogin={jest.fn()}
        />
      );

      const emailInput = screen.getByLabelText('Email Address');
      const sendResetButton = screen.getByText('Send Reset Link');

      await user.type(emailInput, 'test@example.com');
      await user.click(sendResetButton);

      await waitFor(() => {
        expect(authApi.requestPasswordReset).toHaveBeenCalledWith('test@example.com');
      });

      // Step 3: Reset password form
      const mockToken = 'valid-reset-token';
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
        expect(screen.getByLabelText('New Password')).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText('New Password');
      const confirmInput = screen.getByLabelText('Confirm New Password');
      const resetButton = screen.getByRole('button', { name: 'Reset Password' });

      await user.type(passwordInput, 'NewPassword123!');
      await user.type(confirmInput, 'NewPassword123!');
      await user.click(resetButton);

      await waitFor(() => {
        expect(authApi.resetPassword).toHaveBeenCalledWith(mockToken, 'NewPassword123!');
      });

      // Step 4: Back to login with success message
      mockSearchParams.get.mockReturnValue('password-reset-success');
      
      rerender(
        <Provider store={store}>
          <LoginForm />
        </Provider>
      );

      expect(toast.success).toHaveBeenCalledWith(
        'Password reset successful! You can now log in with your new password.'
      );
    });
  });

  describe('User Model Integration', () => {
    it('should work with different user types', async () => {
      const user = userEvent.setup();
      
      // Test that password reset works regardless of user type
      const testCases = [
        { email: 'customer@example.com', userType: 'customer' },
        { email: 'seller@example.com', userType: 'seller' },
        { email: 'admin@example.com', userType: 'admin' },
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
      const { GUEST_ROUTES } = require('@/middleware/auth');
      
      expect(GUEST_ROUTES).toContain('/auth/forgot-password');
      expect(GUEST_ROUTES).toContain('/auth/reset-password');
      expect(GUEST_ROUTES).toContain('/auth/login');
      expect(GUEST_ROUTES).toContain('/auth/register');
    });
  });
});