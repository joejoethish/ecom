import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ForgotPasswordForm } from '../ForgotPasswordForm';
import { authApi } from '@/services/authApi';

// Mock the authApi
jest.mock('@/services/authApi');
const mockAuthApi = authApi as jest.Mocked<typeof authApi>;

// Mock the error handling utilities
jest.mock('@/utils/passwordResetErrors', () => ({
  getPasswordResetErrorMessage: jest.fn((error) => error?.message || 'An error occurred'),
  logPasswordResetError: jest.fn(),
  isRetryablePasswordResetError: jest.fn(() => true),
  logPasswordResetSecurityEvent: jest.fn(),
}));

describe('ForgotPasswordForm', () => {
  const mockOnSuccess = jest.fn();
  const mockOnBackToLogin = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the form correctly', () => {
    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    expect(screen.getByText('Forgot Password?')).toBeInTheDocument();
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Send Reset Link' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Back to Login' })).toBeInTheDocument();
  });

  it('validates email format', async () => {
    const user = userEvent.setup();
    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    const emailInput = screen.getByLabelText('Email Address');
    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });

    // Test invalid email
    await user.type(emailInput, 'invalid-email');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
    });

    // Test valid email
    await user.clear(emailInput);
    await user.type(emailInput, 'test@example.com');
    
    // The validation error should disappear
    await waitFor(() => {
      expect(screen.queryByText('Please enter a valid email address')).not.toBeInTheDocument();
    });
  });

  it('requires email to be entered', async () => {
    const user = userEvent.setup();
    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Email address is required')).toBeInTheDocument();
    });
  });

  it('submits form successfully', async () => {
    const user = userEvent.setup();
    mockAuthApi.requestPasswordReset.mockResolvedValue({
      success: true,
      data: { success: true, message: 'Reset email sent' }
    });

    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    const emailInput = screen.getByLabelText('Email Address');
    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });

    await user.type(emailInput, 'test@example.com');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockAuthApi.requestPasswordReset).toHaveBeenCalledWith('test@example.com');
    });

    // Should show success screen
    await waitFor(() => {
      expect(screen.getByText('Check Your Email')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    expect(mockOnSuccess).toHaveBeenCalled();
  });

  it('handles API errors', async () => {
    const user = userEvent.setup();
    mockAuthApi.requestPasswordReset.mockResolvedValue({
      success: false,
      error: {
        message: 'Server error',
        code: 'server_error',
        status_code: 500
      }
    });

    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    const emailInput = screen.getByLabelText('Email Address');
    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });

    await user.type(emailInput, 'test@example.com');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Server error')).toBeInTheDocument();
    });

    expect(mockOnSuccess).not.toHaveBeenCalled();
  });

  it('shows loading state during submission', async () => {
    const user = userEvent.setup();
    let resolvePromise: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    
    mockAuthApi.requestPasswordReset.mockReturnValue(promise as any);

    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    const emailInput = screen.getByLabelText('Email Address');
    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });

    await user.type(emailInput, 'test@example.com');
    await user.click(submitButton);

    // Should show loading state
    expect(screen.getByText('Sending Reset Link...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();

    // Resolve the promise
    resolvePromise!({
      success: true,
      data: { success: true, message: 'Reset email sent' }
    });

    await waitFor(() => {
      expect(screen.getByText('Check Your Email')).toBeInTheDocument();
    });
  });

  it('allows trying different email from success screen', async () => {
    const user = userEvent.setup();
    mockAuthApi.requestPasswordReset.mockResolvedValue({
      success: true,
      data: { success: true, message: 'Reset email sent' }
    });

    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    const emailInput = screen.getByLabelText('Email Address');
    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });

    await user.type(emailInput, 'test@example.com');
    await user.click(submitButton);

    // Wait for success screen
    await waitFor(() => {
      expect(screen.getByText('Check Your Email')).toBeInTheDocument();
    });

    // Click "Try Different Email"
    const tryDifferentButton = screen.getByRole('button', { name: 'Try Different Email' });
    await user.click(tryDifferentButton);

    // Should return to form
    await waitFor(() => {
      expect(screen.getByText('Forgot Password?')).toBeInTheDocument();
      expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
    });
  });

  it('calls onBackToLogin when back button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    const backButton = screen.getByRole('button', { name: 'Back to Login' });
    await user.click(backButton);

    expect(mockOnBackToLogin).toHaveBeenCalled();
  });

  it('handles network errors with retry functionality', async () => {
    const user = userEvent.setup();
    mockAuthApi.requestPasswordReset.mockRejectedValue(new Error('Network error'));

    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    const emailInput = screen.getByLabelText('Email Address');
    const submitButton = screen.getByRole('button', { name: 'Send Reset Link' });

    await user.type(emailInput, 'test@example.com');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    // Should show retry button
    const retryButton = screen.getByRole('button', { name: 'Try Again' });
    expect(retryButton).toBeInTheDocument();
  });
});