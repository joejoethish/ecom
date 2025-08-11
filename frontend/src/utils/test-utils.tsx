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
          ignoredActions: [&apos;auth/setUser&apos;, &apos;auth/setToken&apos;],
          ignoredActionPaths: [&apos;payload.data&apos;],
          ignoredPaths: [&apos;auth.user&apos;, &apos;auth.token&apos;],
        },
      }),
  });
}

// Custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  preloadedState?: Partial<RootState>;
  store?: EnhancedStore;
  theme?: &apos;light&apos; | &apos;dark&apos; | &apos;system&apos;;
}

export function renderWithProviders(
  ui: ReactElement,
  options: CustomRenderOptions = {}
) {
  const {
    preloadedState,
    store = createTestStore({ preloadedState }),
    theme = &apos;light&apos;,
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
  id: &apos;1&apos;,
  username: &apos;testuser&apos;,
  email: &apos;test@example.com&apos;,
  user_type: &apos;customer&apos; as const,
  phone_number: &apos;+1234567890&apos;,
  is_verified: true,
  is_staff: false,
  is_superuser: false,
  created_at: &apos;2023-01-01T00:00:00Z&apos;,
  ...overrides,
});

export const mockProduct = (overrides: Partial<unknown> = {}) => ({
  id: &apos;1&apos;,
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
  price: 99.99,
  discount_price: 79.99,
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
  ...overrides,
});

  id: &apos;1&apos;,
  order_number: &apos;ORD-20230101-12345&apos;,
  status: &apos;DELIVERED&apos; as const,
  total_amount: 99.99,
  discount_amount: 10.00,
  tax_amount: 8.99,
  shipping_amount: 5.99,
  shipping_address: {
    id: &apos;1&apos;,
    type: &apos;shipping&apos; as const,
    first_name: &apos;John&apos;,
    last_name: &apos;Doe&apos;,
    address_line_1: &apos;123 Test St&apos;,
    city: &apos;Test City&apos;,
    state: &apos;Test State&apos;,
    postal_code: &apos;12345&apos;,
    country: &apos;Test Country&apos;,
    phone: &apos;+1234567890&apos;,
    is_default: true,
  },
  billing_address: {
    id: &apos;2&apos;,
    type: &apos;HOME&apos; as const,
    first_name: &apos;John&apos;,
    last_name: &apos;Doe&apos;,
    address_line_1: &apos;123 Test St&apos;,
    city: &apos;Test City&apos;,
    state: &apos;Test State&apos;,
    postal_code: &apos;12345&apos;,
    country: &apos;Test Country&apos;,
    phone: &apos;+1234567890&apos;,
    is_default: true,
  },
  payment_method: &apos;credit_card&apos;,
  payment_status: &apos;COMPLETED&apos;,
  items: [],
  created_at: &apos;2023-01-01T00:00:00Z&apos;,
  updated_at: &apos;2023-01-01T00:00:00Z&apos;,
  ...overrides,
});

  id: &apos;1&apos;,
  product: mockProduct(),
  quantity: 1,
  added_at: &apos;2023-01-01T00:00:00Z&apos;,
  ...overrides,
});

  id: &apos;1&apos;,
  title: &apos;Test Notification&apos;,
  message: &apos;This is a test notification&apos;,
  type: &apos;info&apos; as const,
  isRead: false,
  created_at: &apos;2023-01-01T00:00:00Z&apos;,
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

  key: string,
  properties: Partial<KeyboardEvent> = {}
): KeyboardEvent => {
  return createMockEvent(&apos;keydown&apos;, {
    key,
    code: `Key${key.toUpperCase()}`,
    keyCode: key.charCodeAt(0),
    which: key.charCodeAt(0),
    ...properties,
  });
};

  type: &apos;click&apos; | &apos;mousedown&apos; | &apos;mouseup&apos; | &apos;mouseover&apos; | &apos;mouseout&apos; = &apos;click&apos;,
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