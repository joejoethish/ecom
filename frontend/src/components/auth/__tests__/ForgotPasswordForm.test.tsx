import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ForgotPasswordForm } from '../ForgotPasswordForm';
import { authApi } from '@/services/authApi';

// Mock the authApi
jest.mock('@/services/authApi');
const mockAuthApi = authApi as jest.Mocked<typeof authApi>;

// Mock the error handling utilities
jest.mock(&apos;@/utils/passwordResetErrors&apos;, () => ({
  getPasswordResetErrorMessage: jest.fn((error) => error?.message || &apos;An error occurred&apos;),
  logPasswordResetError: jest.fn(),
  isRetryablePasswordResetError: jest.fn(() => true),
  logPasswordResetSecurityEvent: jest.fn(),
}));

describe(&apos;ForgotPasswordForm&apos;, () => {
  const mockOnSuccess = jest.fn();
  const mockOnBackToLogin = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it(&apos;renders the form correctly&apos;, () => {
    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    expect(screen.getByText(&apos;Forgot Password?&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(&apos;Email Address&apos;)).toBeInTheDocument();
    expect(screen.getByRole(&apos;button&apos;, { name: &apos;Send Reset Link&apos; })).toBeInTheDocument();
    expect(screen.getByRole(&apos;button&apos;, { name: &apos;Back to Login&apos; })).toBeInTheDocument();
  });

  it(&apos;validates email format&apos;, async () => {
    const user = userEvent.setup();
    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    const emailInput = screen.getByLabelText(&apos;Email Address&apos;);
    const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Send Reset Link&apos; });

    // Test invalid email
    await user.type(emailInput, &apos;invalid-email&apos;);
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Please enter a valid email address&apos;)).toBeInTheDocument();
    });

    // Test valid email
    await user.clear(emailInput);
    await user.type(emailInput, &apos;test@example.com&apos;);
    
    // The validation error should disappear
    await waitFor(() => {
      expect(screen.queryByText(&apos;Please enter a valid email address&apos;)).not.toBeInTheDocument();
    });
  });

  it(&apos;requires email to be entered&apos;, async () => {
    const user = userEvent.setup();
    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Send Reset Link&apos; });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Email address is required&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;submits form successfully&apos;, async () => {
    const user = userEvent.setup();
    mockAuthApi.requestPasswordReset.mockResolvedValue({
      success: true,
      data: { success: true, message: &apos;Reset email sent&apos; }
    });

    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    const emailInput = screen.getByLabelText(&apos;Email Address&apos;);
    const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Send Reset Link&apos; });

    await user.type(emailInput, &apos;test@example.com&apos;);
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockAuthApi.requestPasswordReset).toHaveBeenCalledWith(&apos;test@example.com&apos;);
    });

    // Should show success screen
    await waitFor(() => {
      expect(screen.getByText(&apos;Check Your Email&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;test@example.com&apos;)).toBeInTheDocument();
    });

    expect(mockOnSuccess).toHaveBeenCalled();
  });

  it(&apos;handles API errors&apos;, async () => {
    const user = userEvent.setup();
    mockAuthApi.requestPasswordReset.mockResolvedValue({
      success: false,
      error: {
        message: &apos;Server error&apos;,
        code: &apos;server_error&apos;,
        status_code: 500
      }
    });

    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    const emailInput = screen.getByLabelText(&apos;Email Address&apos;);
    const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Send Reset Link&apos; });

    await user.type(emailInput, &apos;test@example.com&apos;);
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(&apos;Server error&apos;)).toBeInTheDocument();
    });

    expect(mockOnSuccess).not.toHaveBeenCalled();
  });

  it(&apos;shows loading state during submission&apos;, async () => {
    const user = userEvent.setup();
    let resolvePromise: (value: unknown) => void;
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

    const emailInput = screen.getByLabelText(&apos;Email Address&apos;);
    const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Send Reset Link&apos; });

    await user.type(emailInput, &apos;test@example.com&apos;);
    await user.click(submitButton);

    // Should show loading state
    expect(screen.getByText(&apos;Sending Reset Link...&apos;)).toBeInTheDocument();
    expect(submitButton).toBeDisabled();

    // Resolve the promise
    resolvePromise!({
      success: true,
      data: { success: true, message: &apos;Reset email sent&apos; }
    });

    await waitFor(() => {
      expect(screen.getByText(&apos;Check Your Email&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;allows trying different email from success screen&apos;, async () => {
    const user = userEvent.setup();
    mockAuthApi.requestPasswordReset.mockResolvedValue({
      success: true,
      data: { success: true, message: &apos;Reset email sent&apos; }
    });

    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    const emailInput = screen.getByLabelText(&apos;Email Address&apos;);
    const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Send Reset Link&apos; });

    await user.type(emailInput, &apos;test@example.com&apos;);
    await user.click(submitButton);

    // Wait for success screen
    await waitFor(() => {
      expect(screen.getByText(&apos;Check Your Email&apos;)).toBeInTheDocument();
    });

    // Click &quot;Try Different Email&quot;
    const tryDifferentButton = screen.getByRole(&apos;button&apos;, { name: &apos;Try Different Email&apos; });
    await user.click(tryDifferentButton);

    // Should return to form
    await waitFor(() => {
      expect(screen.getByText(&apos;Forgot Password?&apos;)).toBeInTheDocument();
      expect(screen.getByLabelText(&apos;Email Address&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;calls onBackToLogin when back button is clicked&apos;, async () => {
    const user = userEvent.setup();
    render(
      <ForgotPasswordForm 
        onSuccess={mockOnSuccess}
        onBackToLogin={mockOnBackToLogin}
      />
    );

    const backButton = screen.getByRole(&apos;button&apos;, { name: &apos;Back to Login&apos; });
    await user.click(backButton);

    expect(mockOnBackToLogin).toHaveBeenCalled();
  });

  it(&apos;handles network errors with retry functionality&apos;, async () => {
    const user = userEvent.setup();
    mockAuthApi.requestPasswordReset.mockRejectedValue(new Error(&apos;Network error&apos;));

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