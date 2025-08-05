import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import authSlice from '@/store/slices/authSlice';
import cartSlice from '@/store/slices/cartSlice';

// Create a test store
export const createTestStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authSlice,
      cart: cartSlice,
    },
    preloadedState: initialState,
  });
};

// Custom render function that includes providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialState?: any;
  store?: any;
}

export const renderWithProviders = (
  ui: React.ReactElement,
  {
    initialState = {},
    store = createTestStore(initialState),
    ...renderOptions
  }: CustomRenderOptions = {}
) => {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <Provider store={store}>{children}</Provider>;
  }

  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
};

// Mock data factories
export const createMockProduct = (overrides = {}) => ({
  id: '1',
  name: 'Test Product',
  slug: 'test-product',
  description: 'Test description with details about the product.',
  short_description: 'Short description',
  category: {
    id: 'cat1',
    name: 'Test Category',
    slug: 'test-category',
    is_active: true,
    created_at: '2023-01-01',
  },
  brand: 'Test Brand',
  sku: 'TEST123',
  price: 100,
  discount_price: 80,
  is_active: true,
  is_featured: false,
  weight: 1,
  dimensions: { length: 10, width: 5, height: 2 },
  images: [
    {
      id: 'img1',
      image: '/test-image-1.jpg',
      alt_text: 'Test Image 1',
      is_primary: true,
      order: 1,
    },
    {
      id: 'img2',
      image: '/test-image-2.jpg',
      alt_text: 'Test Image 2',
      is_primary: false,
      order: 2,
    },
  ],
  status: 'active',
  created_at: '2023-01-01',
  updated_at: '2023-01-01',
  ...overrides,
});

export const createMockUser = (overrides = {}) => ({
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  user_type: 'customer',
  is_verified: true,
  created_at: '2023-01-01',
  ...overrides,
});

// Re-export everything from testing-library
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';