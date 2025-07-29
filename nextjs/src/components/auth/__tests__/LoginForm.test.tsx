import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Provider } from 'react-redux';
import { configureStore, createSlice } from '@reduxjs/toolkit';
import { LoginForm } from '../LoginForm';
import { loginUser } from '@/store/slices/authSlice';
import toast from 'react-hot-toast';

// Mock the loginUser async thunk
jest.mock('@/store/slices/authSlice', () => ({
  loginUser: jest.fn(),
}));

const mockLoginUser = loginUser as jest.MockedFunction<typeof loginUser>;
const mockPush = jest.fn();

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
  success: jest.fn(),
  error: jest.fn(),
}));

// Mock constants
jest.mock('@/constants', () => ({
  ROUTES: {
    HOME: '/',
    REGISTER: '/auth/register',
  },
}));

// Create a mock auth slice for testing
const mockAuthSlice = createSlice({
  name: 'auth',
  initialState: {
    user: null,
    tokens: null,
    isAuthenticated: false,
    loading: false,
    error: null,
  },
  reducers: {},
});

const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: mockAuthSlice.reducer,
    },
    preloadedState: {
      auth: {
        user: null,
        tokens: null,
        isAuthenticated: false,
        loading: false,
        error: null,
        ...initialState,
      },
    },
  });
};

describe('LoginForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPush.mockClear();
  });

  it('renders login form correctly', () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    expect(screen.getByText('Sign in to your account')).toBeInTheDocument();
    expect(screen.getByLabelText('Email address')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();
    expect(screen.getByText('create a new account')).toBeInTheDocument();
  });

  it('shows validation errors for empty fields', async () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    const form = document.querySelector('form');

    // Submit the form
    fireEvent.submit(form!);

    // Wait for validation errors to appear
    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument();
      expect(screen.getByText('Password is required')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('shows validation error for invalid email', async () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    const emailInput = screen.getByLabelText('Email address');
    const form = document.querySelector('form');

    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.submit(form!);

    await waitFor(() => {
      expect(screen.getByText('Email is invalid')).toBeInTheDocument();
    });
  });

  it('clears validation errors when user starts typing', async () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    const emailInput = screen.getByLabelText('Email address');
    const form = document.querySelector('form');

    // Trigger validation error by submitting form
    fireEvent.submit(form!);

    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument();
    });

    // Start typing to clear error
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });

    await waitFor(() => {
      expect(screen.queryByText('Email is required')).not.toBeInTheDocument();
    });
  });

  it('submits form with valid credentials', async () => {
    const store = createMockStore();

    // Mock successful login
    mockLoginUser.mockReturnValue({
      type: 'auth/login/fulfilled',
      payload: { user: { id: '1', email: 'test@example.com' }, tokens: { access: 'token' } },
      unwrap: jest.fn().mockResolvedValue({ user: { id: '1', email: 'test@example.com' }, tokens: { access: 'token' } })
    } as any);

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    const emailInput = screen.getByLabelText('Email address');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: 'Sign in' });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockLoginUser).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      });
    });
  });

  it('shows error message from Redux state', () => {
    const store = createMockStore({
      error: 'Invalid credentials',
    });

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
  });

  it('disables submit button when loading', () => {
    const store = createMockStore({
      loading: true,
    });

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    const submitButton = screen.getByRole('button', { name: 'Sign in' });
    expect(submitButton).toBeDisabled();
  });

  it('handles login failure with toast error', async () => {
    const store = createMockStore();

    // Mock failed login
    mockLoginUser.mockReturnValue({
      type: 'auth/login/rejected',
      error: { message: 'Login failed' },
      unwrap: jest.fn().mockRejectedValue('Login failed')
    } as any);

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    const emailInput = screen.getByLabelText('Email address');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: 'Sign in' });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Login failed');
    });
  });
});