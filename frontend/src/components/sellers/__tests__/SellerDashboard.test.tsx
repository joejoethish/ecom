import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { thunk } from 'redux-thunk';
import SellerDashboard from '../SellerDashboard';
import type { Middleware } from '@reduxjs/toolkit';

// Create mock store
const mockStore = configureStore(middlewares);

describe('SellerDashboard Component', () => {
  test(&apos;renders loading state&apos;, () => {
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
    expect(screen.getByRole(&apos;status&apos;)).toBeInTheDocument();
  });

  test(&apos;renders no profile state&apos;, () => {
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

    // Check if &quot;not found&quot; message is displayed
    expect(screen.getByText(&apos;Seller Profile Not Found&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;You need to register as a seller to access the dashboard.&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Register as Seller&apos;)).toBeInTheDocument();
  });

  test(&apos;renders dashboard with seller data&apos;, () => {
    const mockProfile = {
      id: &apos;1&apos;,
      business_name: &apos;Test Business&apos;,
      verification_status: &apos;VERIFIED&apos;,
      verification_status_display: &apos;Verified&apos;,
      created_at: &apos;2023-01-01T00:00:00Z&apos;,
    };

    const mockAnalytics = {
      total_sales: 10000,
      total_orders: 50,
      total_products: 25,
      recent_orders: [
        {
          id: &apos;1&apos;,
          order_number: &apos;ORD-12345&apos;,
          total_amount: 2499,
          status: &apos;DELIVERED&apos;,
          created_at: &apos;2023-06-15T10:30:00Z&apos;,
        },
      ],
      sales_by_period: [
        { period: &apos;Jan&apos;, amount: 1000 },
        { period: &apos;Feb&apos;, amount: 1500 },
      ],
      top_products: [
        {
          id: &apos;1&apos;,
          name: &apos;Test Product&apos;,
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