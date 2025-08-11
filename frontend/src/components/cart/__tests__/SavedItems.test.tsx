import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { thunk } from 'redux-thunk';
import SavedItems from '../SavedItems';
import { moveToCart, removeSavedItem } from '@/store/slices/cartSlice';
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
  moveToCart: jest.fn(() => ({ type: 'mock-move-to-cart' })),
  removeSavedItem: jest.fn(() => ({ type: 'mock-remove-saved-item' })),
}));

describe('SavedItems Component', () => {
  const mockSavedItems = [
    {
      id: 's1',
      product: {
        id: 'p1',
        name: 'Saved Product',
        slug: 'saved-product',
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
        sku: 'TST002',
        price: 1500,
        discount_price: 1200,
        is_active: true,
        is_featured: false,
        dimensions: {},
        images: [
          {
            id: 'img1',
            image: '/saved-image.jpg',
            alt_text: 'Saved Image',
            is_primary: true,
            order: 1,
          },
        ],
        created_at: '2023-01-01',
        updated_at: '2023-01-01',
      },
      saved_at: '2023-01-01',
    },
  ];

  let store: any;

  beforeEach(() => {
    store = mockStore({
      cart: {
        savedItems: mockSavedItems,
      },
    });
  });

  it('renders the saved items correctly', () => {
    render(
      <Provider store={store}>
        <SavedItems savedItems={mockSavedItems} />
      </Provider>
    );

    expect(screen.getByText('Saved for Later (1)')).toBeInTheDocument();
    expect(screen.getByText('Saved Product')).toBeInTheDocument();
    expect(screen.getByText('Brand: Test Brand')).toBeInTheDocument();
    expect(screen.getByText('₹1,200')).toBeInTheDocument();
    expect(screen.getByText('₹1,500')).toBeInTheDocument();
    expect(screen.getByText('20% off')).toBeInTheDocument();
    expect(screen.getByText('Move to Cart')).toBeInTheDocument();
    expect(screen.getByText('Remove')).toBeInTheDocument();
  });

  it('shows empty state when no saved items', () => {
    render(
      <Provider store={store}>
        <SavedItems savedItems={[]} />
      </Provider>
    );

    expect(screen.getByText('No saved items')).toBeInTheDocument();
    expect(screen.getByText('Items you save for later will appear here')).toBeInTheDocument();
  });

  it('dispatches moveToCart when move to cart button is clicked', () => {
    render(
      <Provider store={store}>
        <SavedItems savedItems={mockSavedItems} />
      </Provider>
    );

    fireEvent.click(screen.getByText('Move to Cart'));
    expect(moveToCart).toHaveBeenCalledWith('s1');
  });

  it('dispatches removeSavedItem when remove button is clicked', () => {
    render(
      <Provider store={store}>
        <SavedItems savedItems={mockSavedItems} />
      </Provider>
    );

    fireEvent.click(screen.getByText('Remove'));
    expect(removeSavedItem).toHaveBeenCalledWith('s1');
  });
});