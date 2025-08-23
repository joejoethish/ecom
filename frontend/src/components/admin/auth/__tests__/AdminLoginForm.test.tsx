import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { AdminLoginForm } from '../AdminLoginForm';
import authSlice from '@/store/slices/authSlice';

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

const mockStore = configureStore({
  reducer: {
    auth: authSlice,
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
    expect(screen.getByText('Secure administrative access')).toBeInTheDocument();
    expect(screen.getByLabelText('Admin Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /secure sign in/i })).toBeInTheDocument();
  });

  it('shows security warning', () => {
    render(
      <Provider store={mockStore}>
        <AdminLoginForm />
      </Provider>
    );

    expect(screen.getByText('This is a secure area. All activities are monitored and logged.')).toBeInTheDocument();
  });
});