import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { thunk } from 'redux-thunk';
import SavedItems from '../SavedItems';
import { moveToCart, removeSavedItem } from '@/store/slices/cartSlice';
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
  moveToCart: jest.fn(() => ({ type: &apos;mock-move-to-cart&apos; })),
  removeSavedItem: jest.fn(() => ({ type: &apos;mock-remove-saved-item&apos; })),
}));

describe(&apos;SavedItems Component&apos;, () => {
  const mockSavedItems = [
    {
      id: &apos;s1&apos;,
      product: {
        id: &apos;p1&apos;,
        name: &apos;Saved Product&apos;,
        slug: &apos;saved-product&apos;,
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
        sku: &apos;TST002&apos;,
        price: 1500,
        discount_price: 1200,
        is_active: true,
        is_featured: false,
        dimensions: {},
        images: [
          {
            id: &apos;img1&apos;,
            image: &apos;/saved-image.jpg&apos;,
            alt_text: &apos;Saved Image&apos;,
            is_primary: true,
            order: 1,
          },
        ],
        created_at: &apos;2023-01-01&apos;,
        updated_at: &apos;2023-01-01&apos;,
      },
      saved_at: &apos;2023-01-01&apos;,
    },
  ];

  let store: unknown;

  beforeEach(() => {
    store = mockStore({
      cart: {
        savedItems: mockSavedItems,
      },
    });
  });

  it(&apos;renders the saved items correctly&apos;, () => {
    render(
      <Provider store={store}>
        <SavedItems savedItems={mockSavedItems} />
      </Provider>
    );

    expect(screen.getByText(&apos;Saved for Later (1)&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Saved Product&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Brand: Test Brand&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;₹1,200&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;₹1,500&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;20% off&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Move to Cart&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Remove&apos;)).toBeInTheDocument();
  });

  it(&apos;shows empty state when no saved items&apos;, () => {
    render(
      <Provider store={store}>
        <SavedItems savedItems={[]} />
      </Provider>
    );

    expect(screen.getByText(&apos;No saved items&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Items you save for later will appear here&apos;)).toBeInTheDocument();
  });

  it(&apos;dispatches moveToCart when move to cart button is clicked&apos;, () => {
    render(
      <Provider store={store}>
        <SavedItems savedItems={mockSavedItems} />
      </Provider>
    );

    fireEvent.click(screen.getByText(&apos;Move to Cart&apos;));
    expect(moveToCart).toHaveBeenCalledWith(&apos;s1&apos;);
  });

  it(&apos;dispatches removeSavedItem when remove button is clicked&apos;, () => {
    render(
      <Provider store={store}>
        <SavedItems savedItems={mockSavedItems} />
      </Provider>
    );

    fireEvent.click(screen.getByText('Remove'));
    expect(removeSavedItem).toHaveBeenCalledWith('s1');
  });
});