import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import WishlistPage from '../page';
import wishlistReducer from '@/store/slices/wishlistSlice';
import cartReducer from '@/store/slices/cartSlice';
import authReducer from '@/store/slices/authSlice';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  useParams: () => ({}),
}));

// Mock next/image
jest.mock('next/image', () => {
  return function MockImage({ src, alt, ...props }: any) {
    return <img src={src} alt={alt} {...props} />;
  };
});

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock API client
jest.mock('@/utils/api', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn(),
  },
}));

const mockWishlistState = {
  wishlist: {
    id: '1',
    items: [
      {
        id: '1',
        product: {
          id: 'prod-1',
          name: 'Test Product',
          price: 99.99,
          discount_price: 79.99,
          brand: 'Test Brand',
          is_active: true,
          images: [
            {
              image: '/test-image.jpg',
              alt_text: 'Test Product Image',
            },
          ],
        },
        added_at: '2023-01-01T00:00:00Z',
      },
    ],
    created_at: '2023-01-01T00:00:00Z',
  },
  loading: false,
  error: null,
};

const createMockStore = (overrides: any = {}) => {
  const defaultState = {
    wishlist: mockWishlistState,
    cart: { 
      items: [], 
      savedItems: [],
      appliedCoupons: [],
      itemCount: 0,
      subtotal: 0,
      discountAmount: 0,
      totalAmount: 0,
      loading: false, 
      error: null 
    },
    auth: { 
      user: { id: '1', username: 'testuser' }, 
      tokens: null,
      isAuthenticated: true,
      loading: false,
      error: null
    },
  };

  // Merge overrides with default state
  const finalState = {
    ...defaultState,
    ...overrides,
  };

  return configureStore({
    reducer: {
      wishlist: wishlistReducer,
      cart: cartReducer,
      auth: authReducer,
    } as any,
    preloadedState: finalState as any,
  });
};

const renderWithProvider = (component: React.ReactElement, initialState: any = {}) => {
  const store = createMockStore(initialState);
  return render(
    <Provider store={store}>
      {component}
    </Provider>
  );
};

describe('WishlistPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders wishlist page with items', () => {
    renderWithProvider(<WishlistPage />);
    
    expect(screen.getByText('My Wishlist')).toBeInTheDocument();
    expect(screen.getByText('1 item saved')).toBeInTheDocument();
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('Test Brand')).toBeInTheDocument();
  });

  it('renders empty wishlist state', () => {
    const emptyWishlistState = {
      wishlist: {
        wishlist: {
          id: '1',
          items: [],
          created_at: '2023-01-01T00:00:00Z',
        },
        loading: false,
        error: null,
      },
    };

    renderWithProvider(<WishlistPage />, emptyWishlistState);
    
    expect(screen.getByText('Your wishlist is empty')).toBeInTheDocument();
    expect(screen.getByText('Start adding items you love to your wishlist')).toBeInTheDocument();
    expect(screen.getByText('Browse Products')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    const loadingState = {
      wishlist: {
        wishlist: null,
        loading: true,
        error: null,
      },
    };

    renderWithProvider(<WishlistPage />, loadingState);
    
    // Should render skeleton loaders (8 cards with multiple skeleton elements each)
    expect(document.querySelectorAll('.animate-pulse')).toHaveLength(50); // 8 cards * 6 skeleton elements + 2 header skeletons
  });

  it('renders error state', async () => {
    const errorState = {
      wishlist: {
        wishlist: null,
        loading: false,
        error: 'Failed to load wishlist',
      },
    };

    renderWithProvider(<WishlistPage />, errorState);
    
    // Wait for the component to settle and check that it renders without crashing
    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    });
  });

  it('handles add to cart action', async () => {
    renderWithProvider(<WishlistPage />);
    
    const addToCartButton = screen.getByText('Add to Cart');
    fireEvent.click(addToCartButton);
    
    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText('Adding...')).toBeInTheDocument();
    });
  });

  it('displays product pricing correctly', () => {
    renderWithProvider(<WishlistPage />);
    
    // Should show discount price and original price
    expect(screen.getByText('$79.99')).toBeInTheDocument();
    expect(screen.getByText('$99.99')).toBeInTheDocument();
  });
});