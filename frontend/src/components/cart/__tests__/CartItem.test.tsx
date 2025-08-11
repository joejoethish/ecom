import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { thunk } from 'redux-thunk';
import CartItem from '../CartItem';
import { updateCartItem, removeCartItem, saveForLater } from '@/store/slices/cartSlice';
import type { Middleware } from '@reduxjs/toolkit';

// Mock the Redux store
const mockStore = configureStore(middlewares);

// Mock the Next.js Image component
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: unknown) => {
    return <img {...props} />;
  },
}));

// Mock the Redux actions
jest.mock(&apos;@/store/slices/cartSlice&apos;, () => ({
  updateCartItem: jest.fn(() => ({ type: &apos;mock-update&apos; })),
  removeCartItem: jest.fn(() => ({ type: &apos;mock-remove&apos; })),
  saveForLater: jest.fn(() => ({ type: &apos;mock-save&apos; })),
}));

describe(&apos;CartItem Component&apos;, () => {
  const mockItem = {
    id: &apos;1&apos;,
    product: {
      id: &apos;p1&apos;,
      name: &apos;Test Product&apos;,
      slug: &apos;test-product&apos;,
      description: &apos;Test description&apos;,
      short_description: &apos;Short description&apos;,
      category: {
        id: &apos;c1&apos;,
        name: &apos;Test Category&apos;,
        slug: &apos;test-category&apos;,
        is_active: true,
        created_at: &apos;2023-01-01&apos;,
      },
      brand: &apos;Test Brand&apos;,
      sku: &apos;TST001&apos;,
      price: 1000,
      discount_price: 800,
      is_active: true,
      is_featured: false,
      dimensions: {},
      images: [
        {
          id: &apos;img1&apos;,
          image: &apos;/test-image.jpg&apos;,
          alt_text: &apos;Test Image&apos;,
          is_primary: true,
          order: 1,
        },
      ],
      created_at: &apos;2023-01-01&apos;,
      updated_at: &apos;2023-01-01&apos;,
    },
    quantity: 2,
    added_at: &apos;2023-01-01&apos;,
  };

  let store: unknown;

  beforeEach(() => {
    store = mockStore({
      cart: {
        items: [mockItem],
        loading: false,
      },
    });
  });

  it(&apos;renders the cart item correctly&apos;, () => {
    render(
      <Provider store={store}>
        <CartItem item={mockItem} />
      </Provider>
    );

    expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Brand: Test Brand&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;₹800&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;₹1,000&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;20% off&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;2&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;₹1,600&apos;)).toBeInTheDocument();
  });

  it(&apos;dispatches updateCartItem when quantity is changed&apos;, () => {
    render(
      <Provider store={store}>
        <CartItem item={mockItem} />
      </Provider>
    );

    // Click the increment button
    fireEvent.click(screen.getByText(&apos;+&apos;));
    expect(updateCartItem).toHaveBeenCalledWith({ itemId: &apos;1&apos;, quantity: 3 });

    // Click the decrement button
    fireEvent.click(screen.getByText(&apos;-&apos;));
    expect(updateCartItem).toHaveBeenCalledWith({ itemId: &apos;1&apos;, quantity: 1 });
  });

  it(&apos;dispatches removeCartItem when remove button is clicked&apos;, () => {
    render(
      <Provider store={store}>
        <CartItem item={mockItem} />
      </Provider>
    );

    fireEvent.click(screen.getByText(&apos;Remove&apos;));
    expect(removeCartItem).toHaveBeenCalledWith(&apos;1&apos;);
  });

  it(&apos;dispatches saveForLater when save for later button is clicked&apos;, () => {
    render(
      <Provider store={store}>
        <CartItem item={mockItem} />
      </Provider>
    );

    fireEvent.click(screen.getByText('Save for Later'));
    expect(saveForLater).toHaveBeenCalledWith('1');
  });
});