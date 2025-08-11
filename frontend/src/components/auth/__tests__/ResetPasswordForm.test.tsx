import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ResetPasswordForm } from '../ResetPasswordForm';
import { authApi } from '@/services/authApi';

// Mock the authApi
jest.mock('@/services/authApi');
const mockAuthApi = authApi as jest.Mocked<typeof authApi>;

// Mock the error handling utilities
jest.mock(&apos;@/utils/passwordResetErrors&apos;, () => ({
  getPasswordResetErrorMessage: jest.fn((error) => error?.message || &apos;An error occurred&apos;),
  logPasswordResetError: jest.fn(),
  isRetryablePasswordResetError: jest.fn(() => true),
  isValidTokenFormat: jest.fn(() => true),
  logPasswordResetSecurityEvent: jest.fn(),
}));

describe(&apos;ResetPasswordForm&apos;, () => {
  const mockOnSuccess = jest.fn();
  const mockOnBackToLogin = jest.fn();
  const validToken = &apos;abcd1234567890abcd1234567890abcd&apos;;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it(&apos;validates token on mount&apos;, async () => {
    mockAuthApi.validateResetToken.mockResolvedValue({
      success: true,
      data: { valid: true }
    });

    render(
      <ResetPasswordForm
        token={validToken}
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    await waitFor(() => {
      expect(mockAuthApi.validateResetToken).toHaveBeenCalledWith(validToken);
    });

    // Should show the form after validation
    await waitFor(() => {
      expect(screen.getByText(&apos;Reset Your Password&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;shows loading state during token validation&apos;, () => {
    mockAuthApi.validateResetToken.mockReturnValue(new Promise(() => { })); // Never resolves

    render(
      <ResetPasswordForm
        token={validToken}
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    expect(screen.getByText(&apos;Validating Reset Link&apos;)).toBeInTheDocument();
  });

  it(&apos;shows error for invalid token&apos;, async () => {
    mockAuthApi.validateResetToken.mockResolvedValue({
      success: true,
      data: { valid: false }
    });

    render(
      <ResetPasswordForm
        token={validToken}
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(&apos;Invalid Reset Link&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;shows error for expired token&apos;, async () => {
    mockAuthApi.validateResetToken.mockResolvedValue({
      success: true,
      data: { valid: false, expired: true }
    });

    render(
      <ResetPasswordForm
        token={validToken}
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(&apos;Invalid Reset Link&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;renders password form for valid token&apos;, async () => {
    mockAuthApi.validateResetToken.mockResolvedValue({
      success: true,
      data: { valid: true }
    });

    render(
      <ResetPasswordForm
        token={validToken}
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText(&apos;New Password&apos;)).toBeInTheDocument();
      expect(screen.getByLabelText(&apos;Confirm New Password&apos;)).toBeInTheDocument();
      expect(screen.getByRole(&apos;button&apos;, { name: &apos;Reset Password&apos; })).toBeInTheDocument();
    });
  });

  it(&apos;validates password strength&apos;, async () => {
    const user = userEvent.setup();
    mockAuthApi.validateResetToken.mockResolvedValue({
      success: true,
      data: { valid: true }
    });

    render(
      <ResetPasswordForm
        token={validToken}
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText(&apos;New Password&apos;)).toBeInTheDocument();
    });

    const passwordInput = screen.getByLabelText(&apos;New Password&apos;);
    const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Reset Password&apos; });

    // Test weak password
    await user.type(passwordInput, &apos;weak&apos;);
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Password must be at least 8 characters long&apos;)).toBeInTheDocument();
    });

    // Test password without uppercase
    await user.clear(passwordInput);
    await user.type(passwordInput, &apos;password123!&apos;);
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Password must contain at least one uppercase letter&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;validates password confirmation&apos;, async () => {
    const user = userEvent.setup();
    mockAuthApi.validateResetToken.mockResolvedValue({
      success: true,
      data: { valid: true }
    });

    render(
      <ResetPasswordForm
        token={validToken}
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText(&apos;New Password&apos;)).toBeInTheDocument();
    });

    const passwordInput = screen.getByLabelText(&apos;New Password&apos;);
    const confirmInput = screen.getByLabelText(&apos;Confirm New Password&apos;);
    const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Reset Password&apos; });

    await user.type(passwordInput, &apos;Password123!&apos;);
    await user.type(confirmInput, &apos;DifferentPassword123!&apos;);
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Passwords do not match&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;shows password strength indicator&apos;, async () => {
    const user = userEvent.setup();
    mockAuthApi.validateResetToken.mockResolvedValue({
      success: true,
      data: { valid: true }
    });

    render(
      <ResetPasswordForm
        token={validToken}
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText(&apos;New Password&apos;)).toBeInTheDocument();
    });

    const passwordInput = screen.getByLabelText(&apos;New Password&apos;);

    // Type a password to trigger strength indicator
    await user.type(passwordInput, &apos;Password123!&apos;);

    await waitFor(() => {
      expect(screen.getByText(&apos;Password Strength&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;submits form successfully&apos;, async () => {
    const user = userEvent.setup();
    mockAuthApi.validateResetToken.mockResolvedValue({
      success: true,
      data: { valid: true }
    });
    mockAuthApi.resetPassword.mockResolvedValue({
      success: true,
      data: { success: true, message: &apos;Password reset successful&apos; }
    });

    render(
      <ResetPasswordForm
        token={validToken}
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText(&apos;New Password&apos;)).toBeInTheDocument();
    });

    const passwordInput = screen.getByLabelText(&apos;New Password&apos;);
    const confirmInput = screen.getByLabelText(&apos;Confirm New Password&apos;);
    const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Reset Password&apos; });

    await user.type(passwordInput, &apos;Password123!&apos;);
    await user.type(confirmInput, &apos;Password123!&apos;);
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockAuthApi.resetPassword).toHaveBeenCalledWith(validToken, &apos;Password123!&apos;);
    });

    // Should show success screen
    await waitFor(() => {
      expect(screen.getByText(&apos;Password Reset Successful!&apos;)).toBeInTheDocument();
    });

    expect(mockOnSuccess).toHaveBeenCalled();
  });

  it(&apos;handles reset password API errors&apos;, async () => {
    const user = userEvent.setup();
    mockAuthApi.validateResetToken.mockResolvedValue({
      success: true,
      data: { valid: true }
    });
    mockAuthApi.resetPassword.mockResolvedValue({
      success: false,
      error: {
        message: &apos;Token expired&apos;,
        code: &apos;token_expired&apos;,
        status_code: 400
      }
    });

    render(
      <ResetPasswordForm
        token={validToken}
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText(&apos;New Password&apos;)).toBeInTheDocument();
    });

    const passwordInput = screen.getByLabelText(&apos;New Password&apos;);
    const confirmInput = screen.getByLabelText(&apos;Confirm New Password&apos;);
    const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Reset Password&apos; });

    await user.type(passwordInput, &apos;Password123!&apos;);
    await user.type(confirmInput, &apos;Password123!&apos;);
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Token expired&apos;)).toBeInTheDocument();
    });

    expect(mockOnSuccess).not.toHaveBeenCalled();
  });

  it(&apos;shows loading state during password reset&apos;, async () => {
    const user = userEvent.setup();
    mockAuthApi.validateResetToken.mockResolvedValue({
      success: true,
      data: { valid: true }
    });

    let resolvePromise: (value: unknown) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    mockAuthApi.resetPassword.mockReturnValue(promise as any);

    render(
      <ResetPasswordForm
        token={validToken}
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText(&apos;New Password&apos;)).toBeInTheDocument();
    });

    const passwordInput = screen.getByLabelText(&apos;New Password&apos;);
    const confirmInput = screen.getByLabelText(&apos;Confirm New Password&apos;);
    const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Reset Password&apos; });

    await user.type(passwordInput, &apos;Password123!&apos;);
    await user.type(confirmInput, &apos;Password123!&apos;);
    await user.click(submitButton);

    // Should show loading state
    expect(screen.getByText(&apos;Resetting Password...&apos;)).toBeInTheDocument();
    expect(submitButton).toBeDisabled();

    // Resolve the promise
    resolvePromise!({
      success: true,
      data: { success: true, message: &apos;Password reset successful&apos; }
    });

    await waitFor(() => {
      expect(screen.getByText(&apos;Password Reset Successful!&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;calls onBackToLogin when back button is clicked&apos;, async () => {
    const user = userEvent.setup();
    mockAuthApi.validateResetToken.mockResolvedValue({
      success: true,
      data: { valid: true }
    });

    render(
      <ResetPasswordForm
        token={validToken}
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText(&apos;New Password&apos;)).toBeInTheDocument();
    });

    const backButton = screen.getByRole(&apos;button&apos;, { name: &apos;Back to Login&apos; });
    await user.click(backButton);

    expect(mockOnBackToLogin).toHaveBeenCalled();
  });

  it(&apos;handles missing token&apos;, () => {
    render(
      <ResetPasswordForm
        token=""
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    expect(screen.getByText('Invalid Reset Link')).toBeInTheDocument();
  });
});