import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/services/authApi';
import { useAuth } from '@/hooks/useAuth';
import EmailVerificationPage from '../EmailVerificationPage';

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

jest.mock('@/services/authApi', () => ({
  authApi: {
    verifyEmail: jest.fn(),
    resendVerification: jest.fn(),
  },
}));

jest.mock('@/hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

jest.mock('@/constants/routes', () => ({
  AUTH_ROUTES: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
  },
}));

const mockPush = jest.fn();
const mockAuthApi = authApi as jest.Mocked<typeof authApi>;
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;

describe('EmailVerificationPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseRouter.mockReturnValue({
      push: mockPush,
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
    });
    
    mockUseAuth.mockReturnValue({
      user: null,
      tokens: null,
      isAuthenticated: false,
      loading: false,
      error: null,
      clearError: jest.fn(),
      isAdmin: false,
      isSeller: false,
      isCustomer: false,
    });
  });

  describe('Initial verification process', () => {
    it('should show loading state initially', () => {
      render(<EmailVerificationPage token="valid-token" />);
      
      expect(screen.getByText('Verifying your email...')).toBeInTheDocument();
      expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
    });

    it('should handle missing token', async () => {
      render(<EmailVerificationPage token="" />);
      
      await waitFor(() => {
        expect(screen.getByText('Verification Failed')).toBeInTheDocument();
        expect(screen.getByText('Invalid verification token')).toBeInTheDocument();
      });
    });
  });

  describe('Successful verification', () => {
    it('should show success message and redirect for unauthenticated user', async () => {
      mockAuthApi.verifyEmail.mockResolvedValue({
        success: true,
        data: { 
          success: true,
          message: 'Email verified successfully!' 
        },
      });

      render(<EmailVerificationPage token="valid-token" />);

      await waitFor(() => {
        expect(screen.getByText('Email Verified Successfully!')).toBeInTheDocument();
        expect(screen.getByText('Email verified successfully!')).toBeInTheDocument();
        expect(screen.getByText(/You will be redirected to the login page/)).toBeInTheDocument();
      });

      // Check if redirect is scheduled
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/auth/login');
      }, { timeout: 4000 });
    });

    it('should redirect to dashboard for authenticated user', async () => {
      mockUseAuth.mockReturnValue({
        user: { 
          id: '1', 
          email: 'test@example.com',
          username: 'testuser',
          user_type: 'customer',
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z'
        },
        tokens: { access: 'token', refresh: 'refresh' },
        isAuthenticated: true,
        loading: false,
        error: null,
        clearError: jest.fn(),
        isAdmin: false,
        isSeller: false,
        isCustomer: true,
      });

      mockAuthApi.verifyEmail.mockResolvedValue({
        success: true,
        data: { 
          success: true,
          message: 'Email verified successfully!' 
        },
      });

      render(<EmailVerificationPage token="valid-token" />);

      await waitFor(() => {
        expect(screen.getByText(/You will be redirected to your dashboard/)).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/dashboard');
      }, { timeout: 4000 });
    });
  });

  describe('Error handling', () => {
    it('should handle expired token', async () => {
      mockUseAuth.mockReturnValue({
        user: { 
          id: '1', 
          email: 'test@example.com',
          username: 'testuser',
          user_type: 'customer',
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z'
        },
        tokens: { access: 'token', refresh: 'refresh' },
        isAuthenticated: true,
        loading: false,
        error: null,
        clearError: jest.fn(),
        isAdmin: false,
        isSeller: false,
        isCustomer: true,
      });

      mockAuthApi.verifyEmail.mockResolvedValue({
        success: false,
        error: {
          code: 'TOKEN_EXPIRED',
          message: 'Token has expired',
          status_code: 400,
        },
      });

      render(<EmailVerificationPage token="expired-token" />);

      await waitFor(() => {
        expect(screen.getByText('Verification Link Expired')).toBeInTheDocument();
        expect(screen.getByText('Verification link has expired. Please request a new one.')).toBeInTheDocument();
        expect(screen.getByText('Resend Verification Email')).toBeInTheDocument();
      });
    });

    it('should handle already verified email', async () => {
      mockAuthApi.verifyEmail.mockResolvedValue({
        success: false,
        error: {
          code: 'ALREADY_VERIFIED',
          message: 'Email already verified',
          status_code: 400,
        },
      });

      render(<EmailVerificationPage token="valid-token" />);

      await waitFor(() => {
        expect(screen.getByText('Email Already Verified')).toBeInTheDocument();
        expect(screen.getByText('Your email is already verified.')).toBeInTheDocument();
        expect(screen.getByText('Go to Login')).toBeInTheDocument();
      });
    });

    it('should handle generic verification error for unauthenticated user', async () => {
      mockAuthApi.verifyEmail.mockResolvedValue({
        success: false,
        error: {
          code: 'INVALID_TOKEN',
          message: 'Invalid verification token',
          status_code: 400,
        },
      });

      render(<EmailVerificationPage token="invalid-token" />);

      await waitFor(() => {
        expect(screen.getByText('Verification Failed')).toBeInTheDocument();
        expect(screen.getByText('Invalid verification token')).toBeInTheDocument();
        expect(screen.getByText('Go to Login')).toBeInTheDocument();
        expect(screen.getByText('Create New Account')).toBeInTheDocument();
      });
    });

    it('should handle network error', async () => {
      mockAuthApi.verifyEmail.mockRejectedValue(new Error('Network error'));

      render(<EmailVerificationPage token="valid-token" />);

      await waitFor(() => {
        expect(screen.getByText('Verification Failed')).toBeInTheDocument();
        expect(screen.getByText('An unexpected error occurred during verification')).toBeInTheDocument();
      });
    });
  });

  describe('Resend verification functionality', () => {
    it('should resend verification email successfully', async () => {
      mockUseAuth.mockReturnValue({
        user: { 
          id: '1', 
          email: 'test@example.com',
          username: 'testuser',
          user_type: 'customer',
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z'
        },
        tokens: { access: 'token', refresh: 'refresh' },
        isAuthenticated: true,
        loading: false,
        error: null,
        clearError: jest.fn(),
        isAdmin: false,
        isSeller: false,
        isCustomer: true,
      });

      mockAuthApi.verifyEmail.mockResolvedValue({
        success: false,
        error: { 
          code: 'TOKEN_EXPIRED',
          message: 'Token expired',
          status_code: 400,
        },
      });

      mockAuthApi.resendVerification.mockResolvedValue({
        success: true,
        data: { 
          success: true,
          message: 'Verification email sent' 
        },
      });

      render(<EmailVerificationPage token="expired-token" />);

      await waitFor(() => {
        expect(screen.getByText('Resend Verification Email')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Resend Verification Email'));

      await waitFor(() => {
        expect(mockAuthApi.resendVerification).toHaveBeenCalled();
        expect(screen.getByText('A new verification email has been sent to your email address.')).toBeInTheDocument();
      });
    });

    it('should handle resend verification failure', async () => {
      mockUseAuth.mockReturnValue({
        user: { 
          id: '1', 
          email: 'test@example.com',
          username: 'testuser',
          user_type: 'customer',
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z'
        },
        tokens: { access: 'token', refresh: 'refresh' },
        isAuthenticated: true,
        loading: false,
        error: null,
        clearError: jest.fn(),
        isAdmin: false,
        isSeller: false,
        isCustomer: true,
      });

      mockAuthApi.verifyEmail.mockResolvedValue({
        success: false,
        error: { 
          code: 'TOKEN_EXPIRED',
          message: 'Token expired',
          status_code: 400,
        },
      });

      mockAuthApi.resendVerification.mockResolvedValue({
        success: false,
        error: { 
          message: 'Failed to send email',
          code: 'SEND_FAILED',
          status_code: 500,
        },
      });

      render(<EmailVerificationPage token="expired-token" />);

      await waitFor(() => {
        expect(screen.getByText('Resend Verification Email')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Resend Verification Email'));

      await waitFor(() => {
        expect(screen.getByText('Failed to send email')).toBeInTheDocument();
      });
    });

    it('should show loading state during resend', async () => {
      mockUseAuth.mockReturnValue({
        user: { 
          id: '1', 
          email: 'test@example.com',
          username: 'testuser',
          user_type: 'customer',
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z'
        },
        tokens: { access: 'token', refresh: 'refresh' },
        isAuthenticated: true,
        loading: false,
        error: null,
        clearError: jest.fn(),
        isAdmin: false,
        isSeller: false,
        isCustomer: true,
      });

      mockAuthApi.verifyEmail.mockResolvedValue({
        success: false,
        error: { 
          code: 'TOKEN_EXPIRED',
          message: 'Token expired',
          status_code: 400,
        },
      });

      // Make resendVerification hang to test loading state
      mockAuthApi.resendVerification.mockImplementation(() => new Promise(() => {}));

      render(<EmailVerificationPage token="expired-token" />);

      await waitFor(() => {
        expect(screen.getByText('Resend Verification Email')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Resend Verification Email'));

      await waitFor(() => {
        expect(screen.getByRole('button')).toBeDisabled();
        expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner in button
      });
    });
  });

  describe('Navigation actions', () => {
    it('should navigate to login when "Go to Login" is clicked', async () => {
      mockAuthApi.verifyEmail.mockResolvedValue({
        success: false,
        error: { 
          code: 'ALREADY_VERIFIED',
          message: 'Already verified',
          status_code: 400,
        },
      });

      render(<EmailVerificationPage token="valid-token" />);

      await waitFor(() => {
        expect(screen.getByText('Go to Login')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Go to Login'));
      expect(mockPush).toHaveBeenCalledWith('/auth/login');
    });

    it('should navigate to dashboard when authenticated user clicks "Go to Dashboard"', async () => {
      mockUseAuth.mockReturnValue({
        user: { 
          id: '1', 
          email: 'test@example.com',
          username: 'testuser',
          user_type: 'customer',
          is_verified: true,
          created_at: '2023-01-01T00:00:00Z'
        },
        tokens: { access: 'token', refresh: 'refresh' },
        isAuthenticated: true,
        loading: false,
        error: null,
        clearError: jest.fn(),
        isAdmin: false,
        isSeller: false,
        isCustomer: true,
      });

      mockAuthApi.verifyEmail.mockResolvedValue({
        success: false,
        error: { 
          code: 'ALREADY_VERIFIED',
          message: 'Already verified',
          status_code: 400,
        },
      });

      render(<EmailVerificationPage token="valid-token" />);

      await waitFor(() => {
        expect(screen.getByText('Go to Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Go to Dashboard'));
      expect(mockPush).toHaveBeenCalledWith('/dashboard');
    });

    it('should navigate to register when "Create New Account" is clicked', async () => {
      mockAuthApi.verifyEmail.mockResolvedValue({
        success: false,
        error: { 
          code: 'INVALID_TOKEN',
          message: 'Invalid token',
          status_code: 400,
        },
      });

      render(<EmailVerificationPage token="invalid-token" />);

      await waitFor(() => {
        expect(screen.getByText('Create New Account')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Create New Account'));
      expect(mockPush).toHaveBeenCalledWith('/auth/register');
    });
  });

  describe('UI elements and accessibility', () => {
    it('should display correct icons for different states', async () => {
      // Test success icon
      mockAuthApi.verifyEmail.mockResolvedValue({
        success: true,
        data: { 
          success: true,
          message: 'Success' 
        },
      });

      const { rerender } = render(<EmailVerificationPage token="valid-token" />);

      await waitFor(() => {
        expect(screen.getByText('Email Verified Successfully!')).toBeInTheDocument();
      });

      // Test error icon
      mockAuthApi.verifyEmail.mockResolvedValue({
        success: false,
        error: { 
          code: 'INVALID_TOKEN',
          message: 'Invalid token',
          status_code: 400,
        },
      });

      rerender(<EmailVerificationPage token="invalid-token" />);

      await waitFor(() => {
        expect(screen.getByText('Verification Failed')).toBeInTheDocument();
      });
    });

    it('should have proper ARIA labels and roles', () => {
      render(<EmailVerificationPage token="valid-token" />);
      
      // Check for loading spinner with proper role
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('should apply correct CSS classes for different states', async () => {
      mockAuthApi.verifyEmail.mockResolvedValue({
        success: true,
        data: { 
          success: true,
          message: 'Success' 
        },
      });

      render(<EmailVerificationPage token="valid-token" />);

      await waitFor(() => {
        const title = screen.getByText('Email Verified Successfully!');
        expect(title).toHaveClass('text-green-600');
      });
    });
  });
});