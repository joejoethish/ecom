import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { thunk } from 'redux-thunk';
import CouponSection from '../CouponSection';
import { applyCoupon, removeCoupon } from '@/store/slices/cartSlice';
import { AppliedCoupon } from '@/types';
import type { Middleware } from '@reduxjs/toolkit';

// Mock the Redux store
const mockStore = configureStore(middlewares);

// Mock the Redux actions
jest.mock('@/store/slices/cartSlice', () => ({
  applyCoupon: jest.fn(() => ({ type: &apos;mock-apply-coupon&apos; })),
  removeCoupon: jest.fn(() => ({ type: &apos;mock-remove-coupon&apos; })),
}));

describe(&apos;CouponSection Component&apos;, () => {
    {
      coupon: {
        id: &apos;c1&apos;,
        code: &apos;SAVE10&apos;,
        name: &apos;Save 10% on orders above ₹500&apos;,
        discount_type: &apos;PERCENTAGE&apos; as const,
        value: 10,
        minimum_order_amount: 500,
        valid_from: &apos;2023-01-01&apos;,
        valid_until: &apos;2023-12-31&apos;,
        is_active: true,
      },
      discount_amount: 200,
    },
  ];

  let store: unknown;

  beforeEach(() => {
    store = mockStore({
      cart: {
        appliedCoupons: mockAppliedCoupons,
        loading: false,
      },
    });
  });

  it(&apos;renders the coupon section correctly when collapsed&apos;, () => {
    render(
      <Provider store={store}>
        <CouponSection appliedCoupons={mockAppliedCoupons} />
      </Provider>
    );

    expect(screen.getByText(&apos;Apply Coupon&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;(₹200 saved)&apos;)).toBeInTheDocument();
    expect(screen.queryByText(&apos;Applied Coupons&apos;)).not.toBeInTheDocument(); // Not visible when collapsed
  });

  it(&apos;expands when clicked and shows applied coupons&apos;, () => {
    render(
      <Provider store={store}>
        <CouponSection appliedCoupons={mockAppliedCoupons} />
      </Provider>
    );

    // Click to expand
    fireEvent.click(screen.getByText(&apos;Apply Coupon&apos;));

    expect(screen.getByText(&apos;Applied Coupons&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;SAVE10&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Save 10% on orders above ₹500&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;-₹200&apos;)).toBeInTheDocument();
  });

  it(&apos;dispatches applyCoupon when form is submitted&apos;, () => {
    render(
      <Provider store={store}>
        <CouponSection appliedCoupons={mockAppliedCoupons} />
      </Provider>
    );

    // Click to expand
    fireEvent.click(screen.getByText(&apos;Apply Coupon&apos;));

    // Enter coupon code
    const input = screen.getByPlaceholderText(&apos;Enter coupon code&apos;);
    fireEvent.change(input, { target: { value: &apos;NEWCODE&apos; } });

    // Submit form
    const applyButton = screen.getByRole(&apos;button&apos;, { name: &apos;Apply&apos; });
    fireEvent.click(applyButton);

    expect(applyCoupon).toHaveBeenCalledWith(&apos;NEWCODE&apos;);
  });

  it(&apos;dispatches removeCoupon when remove button is clicked&apos;, () => {
    render(
      <Provider store={store}>
        <CouponSection appliedCoupons={mockAppliedCoupons} />
      </Provider>
    );

    // Click to expand
    fireEvent.click(screen.getByText(&apos;Apply Coupon&apos;));

    // Click remove button
    const removeButton = screen.getByTitle(&apos;Remove coupon&apos;);
    fireEvent.click(removeButton);

    expect(removeCoupon).toHaveBeenCalledWith(&apos;c1&apos;);
  });

  it(&apos;shows loading state when loading prop is true&apos;, () => {
    render(
      <Provider store={store}>
        <CouponSection appliedCoupons={mockAppliedCoupons} loading={true} />
      </Provider>
    );

    // Click to expand
    fireEvent.click(screen.getByText(&apos;Apply Coupon&apos;));

    expect(screen.getByText(&apos;Applying...&apos;)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(&apos;Enter coupon code&apos;)).toBeDisabled();
  });

  it(&apos;sets coupon code when popular coupon is clicked&apos;, () => {
    render(
      <Provider store={store}>
        <CouponSection appliedCoupons={[]} />
      </Provider>
    );

    // Click to expand
    fireEvent.click(screen.getByText('Apply Coupon'));

    // Click a popular coupon
    fireEvent.click(screen.getByText('WELCOME20'));

    const input = screen.getByPlaceholderText('Enter coupon code');
    expect(input).toHaveValue('WELCOME20');
  });
});