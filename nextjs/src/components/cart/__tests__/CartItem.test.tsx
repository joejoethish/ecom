import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { thunk } from 'redux-thunk';
import CartItem from '../CartItem';
import { updateCartItem, removeCartItem, saveForLater } from '@/store/slices/cartSlice';
import type { Middleware } from '@reduxjs/toolkit';

// Mock the Redux store
const middlewares: Middleware[] = [thunk];
const mockStore = configureStore(middlewares);

// Mock the Next.js Image component
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    return <img {...props} />;
  },
}));

// Mock the Redux actions
jest.mock('@/store/slices/cartSlice', () => ({
  updateCartItem: jest.fn(() => ({ type: 'mock-update' })),
  removeCartItem: jest.fn(() => ({ type: 'mock-remove' })),
  saveForLater: jest.fn(() => ({ type: 'mock-save' })),
}));

describe('CartItem Component', () => {
  const mockItem = {
    id: '1',
    product: {
      id: 'p1',
      name: 'Test Product',
      slug: 'test-product',
      description: 'Test description',
      short_description: 'Short description',
      category: {
        id: 'c1',
        name: 'Test Category',
        slug: 'test-category',
        is_active: true,
        created_at: '2023-01-01',
      },
      brand: 'Test Brand',
      sku: 'TST001',
      price: 1000,
      discount_price: 800,
      is_active: true,
      is_featured: false,
      dimensions: {},
      images: [
        {
          id: 'img1',
          image: '/test-image.jpg',
          alt_text: 'Test Image',
          is_primary: true,
          order: 1,
        },
      ],
      created_at: '2023-01-01',
      updated_at: '2023-01-01',
    },
    quantity: 2,
    added_at: '2023-01-01',
  };

  let store: any;

  beforeEach(() => {
    store = mockStore({
      cart: {
        items: [mockItem],
        loading: false,
      },
    });
  });

  it('renders the cart item correctly', () => {
    render(
      <Provider store={store}>
        <CartItem item={mockItem} />
      </Provider>
    );

    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('Brand: Test Brand')).toBeInTheDocument();
    expect(screen.getByText('₹800')).toBeInTheDocument();
    expect(screen.getByText('₹1,000')).toBeInTheDocument();
    expect(screen.getByText('20% off')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('₹1,600')).toBeInTheDocument();
  });

  it('dispatches updateCartItem when quantity is changed', () => {
    render(
      <Provider store={store}>
        <CartItem item={mockItem} />
      </Provider>
    );

    // Click the increment button
    fireEvent.click(screen.getByText('+'));
    expect(updateCartItem).toHaveBeenCalledWith({ itemId: '1', quantity: 3 });

    // Click the decrement button
    fireEvent.click(screen.getByText('-'));
    expect(updateCartItem).toHaveBeenCalledWith({ itemId: '1', quantity: 1 });
  });

  it('dispatches removeCartItem when remove button is clicked', () => {
    render(
      <Provider store={store}>
        <CartItem item={mockItem} />
      </Provider>
    );

    fireEvent.click(screen.getByText('Remove'));
    expect(removeCartItem).toHaveBeenCalledWith('1');
  });

  it('dispatches saveForLater when save for later button is clicked', () => {
    render(
      <Provider store={store}>
        <CartItem item={mockItem} />
      </Provider>
    );

    fireEvent.click(screen.getByText('Save for Later'));
    expect(saveForLater).toHaveBeenCalledWith('1');
  });
});