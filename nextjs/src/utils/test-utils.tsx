import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore, EnhancedStore } from '@reduxjs/toolkit';
import { ThemeProvider } from 'next-themes';

// Import all reducers
import authReducer from '@/store/slices/authSlice';
import cartReducer from '@/store/slices/cartSlice';
import productReducer from '@/store/slices/productSlice';
import orderReducer from '@/store/slices/orderSlice';
import notificationReducer from '@/store/slices/notificationSlice';
import inventoryReducer from '@/store/slices/inventorySlice';
import chatReducer from '@/store/slices/chatSlice';
import paymentReducer from '@/store/slices/paymentSlice';
import shippingReducer from '@/store/slices/shippingSlice';
import sellerReducer from '@/store/slices/sellerSlice';
import wishlistReducer from '@/store/slices/wishlistSlice';
import customerReducer from '@/store/slices/customerSlice';

import type { RootState } from '@/store';

// Test store configuration
export interface TestStoreOptions {
  preloadedState?: Partial<RootState>;
  store?: EnhancedStore;
}

export function createTestStore(options: TestStoreOptions = {}) {
  const { preloadedState } = options;
  
  return configureStore({
    reducer: {
      auth: authReducer as any,
      cart: cartReducer as any,
      products: productReducer as any,
      orders: orderReducer as any,
      notifications: notificationReducer as any,
      inventory: inventoryReducer as any,
      chat: chatReducer as any,
      payments: paymentReducer as any,
      shipping: shippingReducer as any,
      seller: sellerReducer as any,
      wishlist: wishlistReducer as any,
      customer: customerReducer as any,
    },
    preloadedState,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: {
          ignoredActions: ['auth/setUser', 'auth/setToken'],
          ignoredActionPaths: ['payload.data'],
          ignoredPaths: ['auth.user', 'auth.token'],
        },
      }),
  });
}

// Custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  preloadedState?: Partial<RootState>;
  store?: EnhancedStore;
  theme?: 'light' | 'dark' | 'system';
}

export function renderWithProviders(
  ui: ReactElement,
  options: CustomRenderOptions = {}
) {
  const {
    preloadedState,
    store = createTestStore({ preloadedState }),
    theme = 'light',
    ...renderOptions
  } = options;

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <Provider store={store}>
        <ThemeProvider attribute="class" defaultTheme={theme}>
          {children}
        </ThemeProvider>
      </Provider>
    );
  }

  return {
    store,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  };
}

// Mock data factories with proper typing
export const mockUser = (overrides: Partial<RootState['auth']['user']> = {}) => ({
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  user_type: 'customer' as const,
  phone_number: '+1234567890',
  is_verified: true,
  is_staff: false,
  is_superuser: false,
  created_at: '2023-01-01T00:00:00Z',
  ...overrides,
});

export const mockProduct = (overrides: Partial<any> = {}) => ({
  id: '1',
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
  price: 99.99,
  discount_price: 79.99,
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
  ...overrides,
});

export const mockOrder = (overrides: Partial<any> = {}) => ({
  id: '1',
  order_number: 'ORD-20230101-12345',
  status: 'DELIVERED' as const,
  total_amount: 99.99,
  discount_amount: 10.00,
  tax_amount: 8.99,
  shipping_amount: 5.99,
  shipping_address: {
    id: '1',
    type: 'shipping' as const,
    first_name: 'John',
    last_name: 'Doe',
    address_line_1: '123 Test St',
    city: 'Test City',
    state: 'Test State',
    postal_code: '12345',
    country: 'Test Country',
    phone: '+1234567890',
    is_default: true,
  },
  billing_address: {
    id: '2',
    type: 'HOME' as const,
    first_name: 'John',
    last_name: 'Doe',
    address_line_1: '123 Test St',
    city: 'Test City',
    state: 'Test State',
    postal_code: '12345',
    country: 'Test Country',
    phone: '+1234567890',
    is_default: true,
  },
  payment_method: 'credit_card',
  payment_status: 'COMPLETED',
  items: [],
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  ...overrides,
});

export const mockCartItem = (overrides: Partial<any> = {}) => ({
  id: '1',
  product: mockProduct(),
  quantity: 1,
  added_at: '2023-01-01T00:00:00Z',
  ...overrides,
});

export const mockNotification = (overrides: Partial<any> = {}) => ({
  id: '1',
  title: 'Test Notification',
  message: 'This is a test notification',
  type: 'info' as const,
  isRead: false,
  created_at: '2023-01-01T00:00:00Z',
  ...overrides,
});

// Test event helpers
export const createMockEvent = <T extends Event>(
  type: string,
  properties: Partial<T> = {}
): T => {
  const event = new Event(type) as T;
  Object.assign(event, properties);
  return event;
};

export const createMockKeyboardEvent = (
  key: string,
  properties: Partial<KeyboardEvent> = {}
): KeyboardEvent => {
  return createMockEvent('keydown', {
    key,
    code: `Key${key.toUpperCase()}`,
    keyCode: key.charCodeAt(0),
    which: key.charCodeAt(0),
    ...properties,
  });
};

export const createMockMouseEvent = (
  type: 'click' | 'mousedown' | 'mouseup' | 'mouseover' | 'mouseout' = 'click',
  properties: Partial<MouseEvent> = {}
): MouseEvent => {
  return createMockEvent(type, {
    button: 0,
    buttons: 1,
    clientX: 0,
    clientY: 0,
    ...properties,
  });
};

// Async test helpers
export const waitForNextTick = () => new Promise(resolve => setTimeout(resolve, 0));

export const waitForCondition = async (
  condition: () => boolean,
  timeout = 5000,
  interval = 100
): Promise<void> => {
  const startTime = Date.now();
  
  while (!condition()) {
    if (Date.now() - startTime > timeout) {
      throw new Error(`Condition not met within ${timeout}ms`);
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }
};

// Re-export everything from testing library
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';