import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { thunk } from 'redux-thunk';
import SellerRegistrationForm from '../SellerRegistrationForm';
import { registerAsSeller } from '../../../store/slices/sellerSlice';
import type { Middleware } from '@reduxjs/toolkit';

// Mock the next/router
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

// Mock the dispatch function
jest.mock('react-redux', () => ({
  ...jest.requireActual('react-redux'),
  useDispatch: () => jest.fn().mockReturnValue(() => Promise.resolve()),
}));

// Create mock store
const middlewares: Middleware[] = [thunk];
const mockStore = configureStore(middlewares);

describe('SellerRegistrationForm Component', () => {
  let store: any;

  beforeEach(() => {
    store = mockStore({
      seller: {
        loading: false,
        error: null,
      },
    });
  });

  test('renders the form correctly', () => {
    render(
      <Provider store={store}>
        <SellerRegistrationForm />
      </Provider>
    );

    // Check if form elements are displayed
    expect(screen.getByText('Seller Registration')).toBeInTheDocument();
    expect(screen.getByLabelText(/Business Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Business Type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/City/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Country/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Phone Number/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Register as Seller/i })).toBeInTheDocument();
  });

  test('displays error message when there is an error', () => {
    const errorStore = mockStore({
      seller: {
        loading: false,
        error: 'Registration failed',
      },
    });

    render(
      <Provider store={errorStore}>
        <SellerRegistrationForm />
      </Provider>
    );

    // Check if error message is displayed
    expect(screen.getByText('Registration failed')).toBeInTheDocument();
  });

  test('disables submit button when loading', () => {
    const loadingStore = mockStore({
      seller: {
        loading: true,
        error: null,
      },
    });

    render(
      <Provider store={loadingStore}>
        <SellerRegistrationForm />
      </Provider>
    );

    // Check if submit button is disabled
    expect(screen.getByRole('button', { name: /Submitting/i })).toBeDisabled();
  });

  test('handles form submission', async () => {
    render(
      <Provider store={store}>
        <SellerRegistrationForm />
      </Provider>
    );

    // Fill out the form
    fireEvent.change(screen.getByLabelText(/Business Name/i), {
      target: { value: 'Test Business' },
    });
    fireEvent.change(screen.getByLabelText(/Address/i), {
      target: { value: '123 Test Street' },
    });
    fireEvent.change(screen.getByLabelText(/City/i), {
      target: { value: 'Test City' },
    });
    fireEvent.change(screen.getByLabelText(/State/i), {
      target: { value: 'Test State' },
    });
    fireEvent.change(screen.getByLabelText(/Country/i), {
      target: { value: 'Test Country' },
    });
    fireEvent.change(screen.getByLabelText(/Postal Code/i), {
      target: { value: '12345' },
    });
    fireEvent.change(screen.getByLabelText(/Phone Number/i), {
      target: { value: '1234567890' },
    });
    fireEvent.change(screen.getByLabelText(/Email/i), {
      target: { value: 'test@example.com' },
    });

    // Submit the form
    fireEvent.submit(screen.getByRole('button', { name: /Register as Seller/i }));

    // Wait for the form submission to complete
    await waitFor(() => {
      // Check if the form was submitted
      expect(screen.getByRole('button', { name: /Register as Seller/i })).not.toBeDisabled();
    });
  });
});