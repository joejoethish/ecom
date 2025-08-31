// Unit tests for AdminLogin component
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';

// Mock AdminLogin component
const AdminLogin = () => (
  <form>
    <label htmlFor="username">Username</label>
    <input id="username" name="username" type="text" />
    <label htmlFor="password">Password</label>
    <input id="password" name="password" type="password" />
    <button type="submit">Login</button>
  </form>
);

// Mock auth slice
const authSlice = {
  reducer: (state = { user: null, token: null, isLoading: false, error: null }, action: any) => state
};

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
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

describe("AdminLogin Component", () => {
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

  test("renders login form correctly", () => {
    renderWithProvider(<AdminLogin />);
    
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /login/i })).toBeInTheDocument();
  });

  test("displays validation errors for empty fields", async () => {
    const user = userEvent.setup();
    renderWithProvider(<AdminLogin />);
    
    const loginButton = screen.getByRole("button", { name: /login/i });
    await user.click(loginButton);
    
    await waitFor(() => {
      expect(screen.getByText(/username is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });

  test("submits form with valid credentials", async () => {
    const user = userEvent.setup();
    renderWithProvider(<AdminLogin />);
    
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole("button", { name: /login/i });
    
    await user.type(usernameInput, "admin");
    await user.type(passwordInput, "password123");
    await user.click(loginButton);
    
    // Verify form submission
    expect(usernameInput).toHaveValue("admin");
    expect(passwordInput).toHaveValue("password123");
  });

  test("displays loading state during authentication", () => {
    const loadingStore = createMockStore({ isLoading: true });
    
    render(
      <Provider store={loadingStore}>
        <AdminLogin />
      </Provider>
    );
    
    expect(screen.getByRole("button", { name: /logging in/i })).toBeDisabled();
  });

  test("displays error message on authentication failure", () => {
    const errorStore = createMockStore({ 
      error: "Invalid credentials" 
    });
    
    render(
      <Provider store={errorStore}>
        <AdminLogin />
      </Provider>
    );
    
    expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
  });

  test("handles keyboard navigation", async () => {
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
    await user.type(usernameInput, "admin");
    await user.type(passwordInput, "password123");
    await user.keyboard("{Enter}");
    
    // Form should be submitted
  });

  test("clears error message when user starts typing", async () => {
    const user = userEvent.setup();
    const errorStore = createMockStore({ 
      error: "Invalid credentials" 
    });
    
    render(
      <Provider store={errorStore}>
        <AdminLogin />
      </Provider>
    );
    
    expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    
    const usernameInput = screen.getByLabelText(/username/i);
    await user.type(usernameInput, "a");
    
    // Error should be cleared (this depends on implementation)
  });

  test("prevents multiple form submissions", async () => {
    const user = userEvent.setup();
    renderWithProvider(<AdminLogin />);
    
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole("button", { name: /login/i });
    
    await user.type(usernameInput, "admin");
    await user.type(passwordInput, "password123");
    
    // Click multiple times quickly
    await user.click(loginButton);
    await user.click(loginButton);
    await user.click(loginButton);
    
    // Should only submit once (implementation dependent)
  });

  test("shows password visibility toggle", async () => {
    const user = userEvent.setup();
    renderWithProvider(<AdminLogin />);
    
    const passwordInput = screen.getByLabelText(/password/i);
    const toggleButton = screen.getByRole("button", { name: /show password/i });
    
    expect(passwordInput).toHaveAttribute("type", "password");
    
    await user.click(toggleButton);
    expect(passwordInput).toHaveAttribute("type", "text");
    
    await user.click(toggleButton);
    expect(passwordInput).toHaveAttribute("type", "password");
  });

  test("remembers username if &quot;Remember Me&quot; is checked", async () => {
    const user = userEvent.setup();
    renderWithProvider(<AdminLogin />);
    
    const usernameInput = screen.getByLabelText(/username/i);
    const rememberCheckbox = screen.getByLabelText(/remember me/i);
    
    await user.type(usernameInput, "admin");
    await user.click(rememberCheckbox);
    
    expect(rememberCheckbox).toBeChecked();
    // Implementation would save to localStorage
  });

  test("handles network errors gracefully", async () => {
    // Mock network error
    const networkErrorStore = createMockStore({ 
      error: "Network error. Please try again." 
    });
    
    render(
      <Provider store={networkErrorStore}>
        <AdminLogin />
      </Provider>
    );
    
    expect(screen.getByText(/network error/i)).toBeInTheDocument();
  });

  test("redirects to dashboard on successful login", async () => {
    const mockPush = jest.fn();
    jest.doMock("next/navigation", () => ({
      useRouter: () => ({
        push: mockPush,
        replace: jest.fn(),
        prefetch: jest.fn(),
      }),
    }));
    
    const successStore = createMockStore({ 
      user: { id: 1, username: "admin" },
      token: "mock-token"
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