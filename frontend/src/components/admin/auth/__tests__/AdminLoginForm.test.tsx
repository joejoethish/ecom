import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { AdminLoginForm } from '../AdminLoginForm';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
  useSearchParams: () => ({
    get: jest.fn(),
  }),
}));

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  success: jest.fn(),
  error: jest.fn(),
}));

// Mock the form error handling hook
jest.mock('@/hooks/useFormErrorHandling', () => ({
  useFormErrorHandling: () => ({
    fieldErrors: {},
    generalError: null,
    hasErrors: false,
    isSubmitting: false,
    handleError: jest.fn(),
    handleSuccess: jest.fn(),
    setSubmitting: jest.fn(),
    handleFieldChange: jest.fn(),
    getFieldError: jest.fn(() => null),
    clearErrors: jest.fn(),
  }),
}));

// Mock auth slice
const authSlice = {
  name: 'auth',
  initialState: { user: null, token: null, isLoading: false, error: null },
  reducers: {},
  reducer: (state = { user: null, token: null, isLoading: false, error: null }, action: any) => state
};

const mockStore = configureStore({
  reducer: {
    auth: authSlice.reducer,
  },
});

describe('AdminLoginForm', () => {
  it('renders admin login form', () => {
    render(
      <Provider store={mockStore}>
        <AdminLoginForm />
      </Provider>
    );

    expect(screen.getByText('Admin Portal')).toBeInTheDocument();
    expect(screen.getByText('Sign in to access the admin dashboard')).toBeInTheDocument();
    expect(screen.getByLabelText('Admin Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in to admin portal/i })).toBeInTheDocument();
  });

  it('renders form fields correctly', () => {
    render(
      <Provider store={mockStore}>
        <AdminLoginForm />
      </Provider>
    );

    const emailInput = screen.getByLabelText('Admin Email');
    const passwordInput = screen.getByLabelText('Password');
    
    expect(emailInput).toHaveAttribute('type', 'email');
    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(emailInput).toHaveAttribute('placeholder', 'Enter your admin email');
    expect(passwordInput).toHaveAttribute('placeholder', 'Enter your password');
  });
});