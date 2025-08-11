import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ResetPasswordForm } from '../ResetPasswordForm';
import { authApi } from '@/services/authApi';

// Mock the authApi
jest.mock('@/services/authApi');
const mockAuthApi = authApi as jest.Mocked<typeof authApi>;

// Mock the error handling utilities
jest.mock('@/utils/passwordResetErrors', () => ({
  getPasswordResetErrorMessage: jest.fn((error) => error?.message || 'An error occurred'),
  logPasswordResetError: jest.fn(),
  isRetryablePasswordResetError: jest.fn(() => true),
  isValidTokenFormat: jest.fn(() => true),
  logPasswordResetSecurityEvent: jest.fn(),
}));

describe('ResetPasswordForm', () => {
  const mockOnSuccess = jest.fn();
  const mockOnBackToLogin = jest.fn();
  const validToken = 'abcd1234567890abcd1234567890abcd';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('validates token on mount', async () => {
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
      expect(screen.getByText('Reset Your Password')).toBeInTheDocument();
    });
  });

  it('shows loading state during token validation', () => {
    mockAuthApi.validateResetToken.mockReturnValue(new Promise(() => { })); // Never resolves

    render(
      <ResetPasswordForm
        token={validToken}
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    expect(screen.getByText('Validating Reset Link')).toBeInTheDocument();
  });

  it('shows error for invalid token', async () => {
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
      expect(screen.getByText('Invalid Reset Link')).toBeInTheDocument();
    });
  });

  it('shows error for expired token', async () => {
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
      expect(screen.getByText('Invalid Reset Link')).toBeInTheDocument();
    });
  });

  it('renders password form for valid token', async () => {
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
      expect(screen.getByLabelText('New Password')).toBeInTheDocument();
      expect(screen.getByLabelText('Confirm New Password')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Reset Password' })).toBeInTheDocument();
    });
  });

  it('validates password strength', async () => {
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
      expect(screen.getByLabelText('New Password')).toBeInTheDocument();
    });

    const passwordInput = screen.getByLabelText('New Password');
    const submitButton = screen.getByRole('button', { name: 'Reset Password' });

    // Test weak password
    await user.type(passwordInput, 'weak');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Password must be at least 8 characters long')).toBeInTheDocument();
    });

    // Test password without uppercase
    await user.clear(passwordInput);
    await user.type(passwordInput, 'password123!');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Password must contain at least one uppercase letter')).toBeInTheDocument();
    });
  });

  it('validates password confirmation', async () => {
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
      expect(screen.getByLabelText('New Password')).toBeInTheDocument();
    });

    const passwordInput = screen.getByLabelText('New Password');
    const confirmInput = screen.getByLabelText('Confirm New Password');
    const submitButton = screen.getByRole('button', { name: 'Reset Password' });

    await user.type(passwordInput, 'Password123!');
    await user.type(confirmInput, 'DifferentPassword123!');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    });
  });

  it('shows password strength indicator', async () => {
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
      expect(screen.getByLabelText('New Password')).toBeInTheDocument();
    });

    const passwordInput = screen.getByLabelText('New Password');

    // Type a password to trigger strength indicator
    await user.type(passwordInput, 'Password123!');

    await waitFor(() => {
      expect(screen.getByText('Password Strength')).toBeInTheDocument();
    });
  });

  it('submits form successfully', async () => {
    const user = userEvent.setup();
    mockAuthApi.validateResetToken.mockResolvedValue({
      success: true,
      data: { valid: true }
    });
    mockAuthApi.resetPassword.mockResolvedValue({
      success: true,
      data: { success: true, message: 'Password reset successful' }
    });

    render(
      <ResetPasswordForm
        token={validToken}
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText('New Password')).toBeInTheDocument();
    });

    const passwordInput = screen.getByLabelText('New Password');
    const confirmInput = screen.getByLabelText('Confirm New Password');
    const submitButton = screen.getByRole('button', { name: 'Reset Password' });

    await user.type(passwordInput, 'Password123!');
    await user.type(confirmInput, 'Password123!');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockAuthApi.resetPassword).toHaveBeenCalledWith(validToken, 'Password123!');
    });

    // Should show success screen
    await waitFor(() => {
      expect(screen.getByText('Password Reset Successful!')).toBeInTheDocument();
    });

    expect(mockOnSuccess).toHaveBeenCalled();
  });

  it('handles reset password API errors', async () => {
    const user = userEvent.setup();
    mockAuthApi.validateResetToken.mockResolvedValue({
      success: true,
      data: { valid: true }
    });
    mockAuthApi.resetPassword.mockResolvedValue({
      success: false,
      error: {
        message: 'Token expired',
        code: 'token_expired',
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
      expect(screen.getByLabelText('New Password')).toBeInTheDocument();
    });

    const passwordInput = screen.getByLabelText('New Password');
    const confirmInput = screen.getByLabelText('Confirm New Password');
    const submitButton = screen.getByRole('button', { name: 'Reset Password' });

    await user.type(passwordInput, 'Password123!');
    await user.type(confirmInput, 'Password123!');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Token expired')).toBeInTheDocument();
    });

    expect(mockOnSuccess).not.toHaveBeenCalled();
  });

  it('shows loading state during password reset', async () => {
    const user = userEvent.setup();
    mockAuthApi.validateResetToken.mockResolvedValue({
      success: true,
      data: { valid: true }
    });

    let resolvePromise: (value: any) => void;
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
      expect(screen.getByLabelText('New Password')).toBeInTheDocument();
    });

    const passwordInput = screen.getByLabelText('New Password');
    const confirmInput = screen.getByLabelText('Confirm New Password');
    const submitButton = screen.getByRole('button', { name: 'Reset Password' });

    await user.type(passwordInput, 'Password123!');
    await user.type(confirmInput, 'Password123!');
    await user.click(submitButton);

    // Should show loading state
    expect(screen.getByText('Resetting Password...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();

    // Resolve the promise
    resolvePromise!({
      success: true,
      data: { success: true, message: 'Password reset successful' }
    });

    await waitFor(() => {
      expect(screen.getByText('Password Reset Successful!')).toBeInTheDocument();
    });
  });

  it('calls onBackToLogin when back button is clicked', async () => {
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
      expect(screen.getByLabelText('New Password')).toBeInTheDocument();
    });

    const backButton = screen.getByRole('button', { name: 'Back to Login' });
    await user.click(backButton);

    expect(mockOnBackToLogin).toHaveBeenCalled();
  });

  it('handles missing token', () => {
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