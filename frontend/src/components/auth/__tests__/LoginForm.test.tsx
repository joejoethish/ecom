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
jest.mock(&apos;next/navigation&apos;, () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock react-hot-toast
jest.mock(&apos;react-hot-toast&apos;, () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
  success: jest.fn(),
  error: jest.fn(),
}));

// Mock constants
jest.mock(&apos;@/constants&apos;, () => ({
  ROUTES: {
    HOME: &apos;/&apos;,
    REGISTER: &apos;/auth/register&apos;,
  },
}));

// Create a mock auth slice for testing
const mockAuthSlice = createSlice({
  name: &apos;auth&apos;,
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

describe(&apos;LoginForm&apos;, () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPush.mockClear();
  });

  it(&apos;renders login form correctly&apos;, () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    expect(screen.getByText(&apos;Sign in to your account&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(&apos;Email address&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(&apos;Password&apos;)).toBeInTheDocument();
    expect(screen.getByRole(&apos;button&apos;, { name: &apos;Sign in&apos; })).toBeInTheDocument();
    expect(screen.getByText(&apos;create a new account&apos;)).toBeInTheDocument();
  });

  it(&apos;shows validation errors for empty fields&apos;, async () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    const form = document.querySelector(&apos;form&apos;);

    // Submit the form
    fireEvent.submit(form!);

    // Wait for validation errors to appear
    await waitFor(() => {
      expect(screen.getByText(&apos;Email is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Password is required&apos;)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it(&apos;shows validation error for invalid email&apos;, async () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    const emailInput = screen.getByLabelText(&apos;Email address&apos;);
    const form = document.querySelector(&apos;form&apos;);

    fireEvent.change(emailInput, { target: { value: &apos;invalid-email&apos; } });
    fireEvent.submit(form!);

    await waitFor(() => {
      expect(screen.getByText(&apos;Email is invalid&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;clears validation errors when user starts typing&apos;, async () => {
    const store = createMockStore();

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    const emailInput = screen.getByLabelText(&apos;Email address&apos;);
    const form = document.querySelector(&apos;form&apos;);

    // Trigger validation error by submitting form
    fireEvent.submit(form!);

    await waitFor(() => {
      expect(screen.getByText(&apos;Email is required&apos;)).toBeInTheDocument();
    });

    // Start typing to clear error
    fireEvent.change(emailInput, { target: { value: &apos;test@example.com&apos; } });

    await waitFor(() => {
      expect(screen.queryByText(&apos;Email is required&apos;)).not.toBeInTheDocument();
    });
  });

  it(&apos;submits form with valid credentials&apos;, async () => {
    const store = createMockStore();

    // Mock successful login
    mockLoginUser.mockReturnValue({
      type: &apos;auth/login/fulfilled&apos;,
      payload: { user: { id: &apos;1&apos;, email: &apos;test@example.com&apos; }, tokens: { access: &apos;token&apos; } },
      unwrap: jest.fn().mockResolvedValue({ user: { id: &apos;1&apos;, email: &apos;test@example.com&apos; }, tokens: { access: &apos;token&apos; } })
    } as any);

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    const emailInput = screen.getByLabelText(&apos;Email address&apos;);
    const passwordInput = screen.getByLabelText(&apos;Password&apos;);
    const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Sign in&apos; });

    fireEvent.change(emailInput, { target: { value: &apos;test@example.com&apos; } });
    fireEvent.change(passwordInput, { target: { value: &apos;password123&apos; } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockLoginUser).toHaveBeenCalledWith({
        email: &apos;test@example.com&apos;,
        password: &apos;password123&apos;,
      });
    });
  });

  it(&apos;shows error message from Redux state&apos;, () => {
    const store = createMockStore({
      error: &apos;Invalid credentials&apos;,
    });

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    expect(screen.getByText(&apos;Invalid credentials&apos;)).toBeInTheDocument();
  });

  it(&apos;disables submit button when loading&apos;, () => {
    const store = createMockStore({
      loading: true,
    });

    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    const submitButton = screen.getByRole(&apos;button&apos;, { name: &apos;Sign in&apos; });
    expect(submitButton).toBeDisabled();
  });

  it(&apos;handles login failure with toast error&apos;, async () => {
    const store = createMockStore();

    // Mock failed login
    mockLoginUser.mockReturnValue({
      type: &apos;auth/login/rejected&apos;,
      error: { message: &apos;Login failed&apos; },
      unwrap: jest.fn().mockRejectedValue(&apos;Login failed&apos;)
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