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
const middlewares: Middleware[] = [thunk];
const mockStore = configureStore(middlewares);

// Mock the Redux actions
jest.mock('@/store/slices/cartSlice', () => ({
  applyCoupon: jest.fn(() => ({ type: 'mock-apply-coupon' })),
  removeCoupon: jest.fn(() => ({ type: 'mock-remove-coupon' })),
}));

describe('CouponSection Component', () => {
  const mockAppliedCoupons: AppliedCoupon[] = [
    {
      coupon: {
        id: 'c1',
        code: 'SAVE10',
        name: 'Save 10% on orders above ₹500',
        discount_type: 'PERCENTAGE' as const,
        value: 10,
        minimum_order_amount: 500,
        valid_from: '2023-01-01',
        valid_until: '2023-12-31',
        is_active: true,
      },
      discount_amount: 200,
    },
  ];

  let store: any;

  beforeEach(() => {
    store = mockStore({
      cart: {
        appliedCoupons: mockAppliedCoupons,
        loading: false,
      },
    });
  });

  it('renders the coupon section correctly when collapsed', () => {
    render(
      <Provider store={store}>
        <CouponSection appliedCoupons={mockAppliedCoupons} />
      </Provider>
    );

    expect(screen.getByText('Apply Coupon')).toBeInTheDocument();
    expect(screen.getByText('(₹200 saved)')).toBeInTheDocument();
    expect(screen.queryByText('Applied Coupons')).not.toBeInTheDocument(); // Not visible when collapsed
  });

  it('expands when clicked and shows applied coupons', () => {
    render(
      <Provider store={store}>
        <CouponSection appliedCoupons={mockAppliedCoupons} />
      </Provider>
    );

    // Click to expand
    fireEvent.click(screen.getByText('Apply Coupon'));

    expect(screen.getByText('Applied Coupons')).toBeInTheDocument();
    expect(screen.getByText('SAVE10')).toBeInTheDocument();
    expect(screen.getByText('Save 10% on orders above ₹500')).toBeInTheDocument();
    expect(screen.getByText('-₹200')).toBeInTheDocument();
  });

  it('dispatches applyCoupon when form is submitted', () => {
    render(
      <Provider store={store}>
        <CouponSection appliedCoupons={mockAppliedCoupons} />
      </Provider>
    );

    // Click to expand
    fireEvent.click(screen.getByText('Apply Coupon'));

    // Enter coupon code
    const input = screen.getByPlaceholderText('Enter coupon code');
    fireEvent.change(input, { target: { value: 'NEWCODE' } });

    // Submit form
    const applyButton = screen.getByRole('button', { name: 'Apply' });
    fireEvent.click(applyButton);

    expect(applyCoupon).toHaveBeenCalledWith('NEWCODE');
  });

  it('dispatches removeCoupon when remove button is clicked', () => {
    render(
      <Provider store={store}>
        <CouponSection appliedCoupons={mockAppliedCoupons} />
      </Provider>
    );

    // Click to expand
    fireEvent.click(screen.getByText('Apply Coupon'));

    // Click remove button
    const removeButton = screen.getByTitle('Remove coupon');
    fireEvent.click(removeButton);

    expect(removeCoupon).toHaveBeenCalledWith('c1');
  });

  it('shows loading state when loading prop is true', () => {
    render(
      <Provider store={store}>
        <CouponSection appliedCoupons={mockAppliedCoupons} loading={true} />
      </Provider>
    );

    // Click to expand
    fireEvent.click(screen.getByText('Apply Coupon'));

    expect(screen.getByText('Applying...')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter coupon code')).toBeDisabled();
  });

  it('sets coupon code when popular coupon is clicked', () => {
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