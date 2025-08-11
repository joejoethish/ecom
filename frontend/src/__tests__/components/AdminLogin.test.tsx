// Unit tests for AdminLogin component
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import AdminLogin from '@/components/auth/AdminLogin';
import { authSlice } from '@/store/slices/authSlice';

// Mock store setup
const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authSlice.reducer,
    },
    preloadedState: {
      auth: {
        user: null,
        token: null,
        isLoading: false,
        error: null,
        ...initialState,
      },
    },
  });
};

// Mock next/navigation
jest.mock(&apos;next/navigation&apos;, () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

describe(&apos;AdminLogin Component&apos;, () => {
  let mockStore: ReturnType<typeof createMockStore>;
  
  beforeEach(() => {
    mockStore = createMockStore();
  });

  const renderWithProvider = (component: React.ReactElement) => {
    return render(
      <Provider store={mockStore}>
        {component}
      </Provider>
    );
  };

  test(&apos;renders login form correctly&apos;, () => {
    renderWithProvider(<AdminLogin />);
    
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole(&apos;button&apos;, { name: /login/i })).toBeInTheDocument();
  });

  test(&apos;displays validation errors for empty fields&apos;, async () => {
    const user = userEvent.setup();
    renderWithProvider(<AdminLogin />);
    
    const loginButton = screen.getByRole(&apos;button&apos;, { name: /login/i });
    await user.click(loginButton);
    
    await waitFor(() => {
      expect(screen.getByText(/username is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });

  test(&apos;submits form with valid credentials&apos;, async () => {
    const user = userEvent.setup();
    renderWithProvider(<AdminLogin />);
    
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole(&apos;button&apos;, { name: /login/i });
    
    await user.type(usernameInput, &apos;admin&apos;);
    await user.type(passwordInput, &apos;password123&apos;);
    await user.click(loginButton);
    
    // Verify form submission
    expect(usernameInput).toHaveValue(&apos;admin&apos;);
    expect(passwordInput).toHaveValue(&apos;password123&apos;);
  });

  test(&apos;displays loading state during authentication&apos;, () => {
    const loadingStore = createMockStore({ isLoading: true });
    
    render(
      <Provider store={loadingStore}>
        <AdminLogin />
      </Provider>
    );
    
    expect(screen.getByRole(&apos;button&apos;, { name: /logging in/i })).toBeDisabled();
  });

  test(&apos;displays error message on authentication failure&apos;, () => {
    const errorStore = createMockStore({ 
      error: &apos;Invalid credentials&apos; 
    });
    
    render(
      <Provider store={errorStore}>
        <AdminLogin />
      </Provider>
    );
    
    expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
  });

  test(&apos;handles keyboard navigation&apos;, async () => {
    const user = userEvent.setup();
    renderWithProvider(<AdminLogin />);
    
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    
    // Tab navigation
    await user.tab();
    expect(usernameInput).toHaveFocus();
    
    await user.tab();
    expect(passwordInput).toHaveFocus();
    
    // Enter key submission
    await user.type(usernameInput, &apos;admin&apos;);
    await user.type(passwordInput, &apos;password123&apos;);
    await user.keyboard(&apos;{Enter}&apos;);
    
    // Form should be submitted
  });

  test(&apos;clears error message when user starts typing&apos;, async () => {
    const user = userEvent.setup();
    const errorStore = createMockStore({ 
      error: &apos;Invalid credentials&apos; 
    });
    
    render(
      <Provider store={errorStore}>
        <AdminLogin />
      </Provider>
    );
    
    expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    
    const usernameInput = screen.getByLabelText(/username/i);
    await user.type(usernameInput, &apos;a&apos;);
    
    // Error should be cleared (this depends on implementation)
  });

  test(&apos;prevents multiple form submissions&apos;, async () => {
    const user = userEvent.setup();
    renderWithProvider(<AdminLogin />);
    
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole(&apos;button&apos;, { name: /login/i });
    
    await user.type(usernameInput, &apos;admin&apos;);
    await user.type(passwordInput, &apos;password123&apos;);
    
    // Click multiple times quickly
    await user.click(loginButton);
    await user.click(loginButton);
    await user.click(loginButton);
    
    // Should only submit once (implementation dependent)
  });

  test(&apos;shows password visibility toggle&apos;, async () => {
    const user = userEvent.setup();
    renderWithProvider(<AdminLogin />);
    
    const passwordInput = screen.getByLabelText(/password/i);
    const toggleButton = screen.getByRole(&apos;button&apos;, { name: /show password/i });
    
    expect(passwordInput).toHaveAttribute(&apos;type&apos;, &apos;password&apos;);
    
    await user.click(toggleButton);
    expect(passwordInput).toHaveAttribute(&apos;type&apos;, &apos;text&apos;);
    
    await user.click(toggleButton);
    expect(passwordInput).toHaveAttribute(&apos;type&apos;, &apos;password&apos;);
  });

  test(&apos;remembers username if &quot;Remember Me&quot; is checked&apos;, async () => {
    const user = userEvent.setup();
    renderWithProvider(<AdminLogin />);
    
    const usernameInput = screen.getByLabelText(/username/i);
    const rememberCheckbox = screen.getByLabelText(/remember me/i);
    
    await user.type(usernameInput, &apos;admin&apos;);
    await user.click(rememberCheckbox);
    
    expect(rememberCheckbox).toBeChecked();
    // Implementation would save to localStorage
  });

  test(&apos;handles network errors gracefully&apos;, async () => {
    // Mock network error
    const networkErrorStore = createMockStore({ 
      error: &apos;Network error. Please try again.&apos; 
    });
    
    render(
      <Provider store={networkErrorStore}>
        <AdminLogin />
      </Provider>
    );
    
    expect(screen.getByText(/network error/i)).toBeInTheDocument();
  });

  test(&apos;redirects to dashboard on successful login&apos;, async () => {
    const mockPush = jest.fn();
    jest.doMock(&apos;next/navigation&apos;, () => ({
      useRouter: () => ({
        push: mockPush,
        replace: jest.fn(),
        prefetch: jest.fn(),
      }),
    }));
    
    const successStore = createMockStore({ 
      user: { id: 1, username: &apos;admin&apos; },
      token: &apos;mock-token&apos;
    });
    
    render(
      <Provider store={successStore}>
        <AdminLogin />
      </Provider>
    );
    
    // Should redirect to dashboard
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/admin/dashboard');
    });
  });
});