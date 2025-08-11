import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { thunk } from 'redux-thunk';
import SellerDashboard from '../SellerDashboard';
import type { Middleware } from '@reduxjs/toolkit';

// Create mock store
const middlewares: Middleware[] = [thunk];
const mockStore = configureStore(middlewares);

describe('SellerDashboard Component', () => {
  test('renders loading state', () => {
    const store = mockStore({
      seller: {
        profile: null,
        analytics: null,
        loading: true,
        error: null,
      },
    });

    render(
      <Provider store={store}>
        <SellerDashboard />
      </Provider>
    );

    // Check if loading spinner is displayed
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  test('renders no profile state', () => {
    const store = mockStore({
      seller: {
        profile: null,
        analytics: null,
        loading: false,
        error: null,
      },
    });

    render(
      <Provider store={store}>
        <SellerDashboard />
      </Provider>
    );

    // Check if "not found" message is displayed
    expect(screen.getByText('Seller Profile Not Found')).toBeInTheDocument();
    expect(screen.getByText('You need to register as a seller to access the dashboard.')).toBeInTheDocument();
    expect(screen.getByText('Register as Seller')).toBeInTheDocument();
  });

  test('renders dashboard with seller data', () => {
    const mockProfile = {
      id: '1',
      business_name: 'Test Business',
      verification_status: 'VERIFIED',
      verification_status_display: 'Verified',
      created_at: '2023-01-01T00:00:00Z',
    };

    const mockAnalytics = {
      total_sales: 10000,
      total_orders: 50,
      total_products: 25,
      recent_orders: [
        {
          id: '1',
          order_number: 'ORD-12345',
          total_amount: 2499,
          status: 'DELIVERED',
          created_at: '2023-06-15T10:30:00Z',
        },
      ],
      sales_by_period: [
        { period: 'Jan', amount: 1000 },
        { period: 'Feb', amount: 1500 },
      ],
      top_products: [
        {
          id: '1',
          name: 'Test Product',
          sales: 5000,
          quantity: 10,
        },
      ],
    };

    const store = mockStore({
      seller: {
        profile: mockProfile,
        analytics: mockAnalytics,
        loading: false,
        error: null,
      },
    });

    render(
      <Provider store={store}>
        <SellerDashboard />
      </Provider>
    );

    // Check if dashboard elements are displayed
    expect(screen.getByText(`Welcome, ${mockProfile.business_name}!`)).toBeInTheDocument();
    expect(screen.getByText('Your seller account is verified.')).toBeInTheDocument();
    expect(screen.getByText('₹10,000')).toBeInTheDocument(); // Total sales
    expect(screen.getByText('50')).toBeInTheDocument(); // Total orders
    expect(screen.getByText('25')).toBeInTheDocument(); // Total products
    expect(screen.getByText('ORD-12345')).toBeInTheDocument(); // Order number
    expect(screen.getByText('Test Product')).toBeInTheDocument(); // Product name
  });
});