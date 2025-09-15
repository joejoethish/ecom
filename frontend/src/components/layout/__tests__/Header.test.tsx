import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { useRouter } from 'next/navigation';
import { Header } from '../Header';
import authSlice from '@/store/slices/authSlice';
import cartSlice from '@/store/slices/cartSlice';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock SearchAutocomplete component
jest.mock('@/components/search/SearchAutocomplete', () => {
  return {
    SearchAutocomplete: ({ onSelect, placeholder, className }: any) => (
      <input
        data-testid="search-autocomplete"
        placeholder={placeholder}
        className={className}
        onChange={(e) => {
          if (e.target.value === 'test') {
            onSelect({ id: '1', type: 'product', name: 'Test Product', url: '/products/1' });
          }
        }}
      />
    ),
  };
});

// Mock LogoutButton component
jest.mock('@/components/auth/LogoutButton', () => {
  return {
    LogoutButton: ({ children, onClick, className }: any) => (
      <button data-testid="logout-button" onClick={onClick} className={className}>
        {children}
      </button>
    ),
  };
});

const mockPush = jest.fn();
const mockRouter = {
  push: mockPush,
  back: jest.fn(),
  forward: jest.fn(),
  refresh: jest.fn(),
  replace: jest.fn(),
  prefetch: jest.fn(),
};

beforeEach(() => {
  (useRouter as jest.Mock).mockReturnValue(mockRouter);
  mockPush.mockClear();
});

const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authSlice,
      cart: cartSlice,
    },
    preloadedState: {
      auth: {
        isAuthenticated: false,
        user: null,
        token: null,
        refreshToken: null,
        loading: false,
        error: null,
        ...(initialState as any)?.auth,
      },
      cart: {
        items: [],
        itemCount: 0,
        total: 0,
        loading: false,
        error: null,
        ...(initialState as any)?.cart,
      },
    },
  });
};

const renderHeader = (initialState = {}) => {
  const store = createMockStore(initialState);
  return render(
    <Provider store={store}>
      <Header />
    </Provider>
  );
};

describe('Header Component', () => {
  describe('Basic Rendering', () => {
    it('renders the header with logo and search bar', () => {
      renderHeader();
      
      expect(screen.getByText('FlipMart')).toBeInTheDocument();
      expect(screen.getByText('Explore')).toBeInTheDocument();
      expect(screen.getByTestId('search-autocomplete')).toBeInTheDocument();
    });

    it('renders login and signup buttons when not authenticated', () => {
      renderHeader();
      
      expect(screen.getByText('Login')).toBeInTheDocument();
      expect(screen.getByText('Sign Up')).toBeInTheDocument();
    });

    it('renders user menu when authenticated', () => {
      renderHeader({
        auth: {
          isAuthenticated: true,
          user: { username: 'testuser', user_type: 'customer' },
        },
      });
      
      expect(screen.getByText('testuser')).toBeInTheDocument();
      expect(screen.queryByText('Login')).not.toBeInTheDocument();
    });
  });

  describe('More Dropdown Menu', () => {
    it('renders the More dropdown trigger', () => {
      renderHeader();
      
      expect(screen.getByText('More')).toBeInTheDocument();
    });

    it('opens More dropdown when clicked', async () => {
      renderHeader();
      
      const moreButton = screen.getByText('More');
      fireEvent.click(moreButton);
      
      await waitFor(() => {
        expect(screen.getByText('Notification Preferences')).toBeInTheDocument();
        expect(screen.getByText('24x7 Customer Care')).toBeInTheDocument();
        expect(screen.getByText('Advertise')).toBeInTheDocument();
        expect(screen.getByText('Download App')).toBeInTheDocument();
      });
    });

    it('navigates to notification preferences when clicked', async () => {
      renderHeader();
      
      const moreButton = screen.getByText('More');
      fireEvent.click(moreButton);
      
      await waitFor(() => {
        const notificationItem = screen.getByText('Notification Preferences');
        fireEvent.click(notificationItem);
        expect(mockPush).toHaveBeenCalledWith('/notifications');
      });
    });

    it('navigates to customer care when clicked', async () => {
      renderHeader();
      
      const moreButton = screen.getByText('More');
      fireEvent.click(moreButton);
      
      await waitFor(() => {
        const customerCareItem = screen.getByText('24x7 Customer Care');
        fireEvent.click(customerCareItem);
        expect(mockPush).toHaveBeenCalledWith('/customer-care');
      });
    });

    it('navigates to advertise page when clicked', async () => {
      renderHeader();
      
      const moreButton = screen.getByText('More');
      fireEvent.click(moreButton);
      
      await waitFor(() => {
        const advertiseItem = screen.getByText('Advertise');
        fireEvent.click(advertiseItem);
        expect(mockPush).toHaveBeenCalledWith('/advertise');
      });
    });

    it('navigates to download app page when clicked', async () => {
      renderHeader();
      
      const moreButton = screen.getByText('More');
      fireEvent.click(moreButton);
      
      await waitFor(() => {
        const downloadAppItem = screen.getByText('Download App');
        fireEvent.click(downloadAppItem);
        expect(mockPush).toHaveBeenCalledWith('/download-app');
      });
    });
  });

  describe('User Dropdown Menu', () => {
    const authenticatedState = {
      auth: {
        isAuthenticated: true,
        user: { username: 'testuser', user_type: 'customer' },
      },
    };

    it('opens user dropdown when clicked', async () => {
      renderHeader(authenticatedState);
      
      const userButton = screen.getByText('testuser');
      fireEvent.click(userButton);
      
      await waitFor(() => {
        expect(screen.getByText('Hello testuser')).toBeInTheDocument();
        expect(screen.getByText('My Profile')).toBeInTheDocument();
        expect(screen.getByText('My Orders')).toBeInTheDocument();
        expect(screen.getByText('Wishlist')).toBeInTheDocument();
        expect(screen.getByText('Rewards')).toBeInTheDocument();
      });
    });

    it('navigates to profile when clicked', async () => {
      renderHeader(authenticatedState);
      
      const userButton = screen.getByText('testuser');
      fireEvent.click(userButton);
      
      await waitFor(() => {
        const profileItem = screen.getByText('My Profile');
        fireEvent.click(profileItem);
        expect(mockPush).toHaveBeenCalledWith('/profile');
      });
    });

    it('navigates to orders when clicked', async () => {
      renderHeader(authenticatedState);
      
      const userButton = screen.getByText('testuser');
      fireEvent.click(userButton);
      
      await waitFor(() => {
        const ordersItem = screen.getByText('My Orders');
        fireEvent.click(ordersItem);
        expect(mockPush).toHaveBeenCalledWith('/profile/orders');
      });
    });

    it('shows seller dashboard for seller users', async () => {
      renderHeader({
        auth: {
          isAuthenticated: true,
          user: { username: 'seller', user_type: 'seller' },
        },
      });
      
      const userButton = screen.getByText('seller');
      fireEvent.click(userButton);
      
      await waitFor(() => {
        expect(screen.getByText('Seller Dashboard')).toBeInTheDocument();
      });
    });

    it('shows admin panel for admin users', async () => {
      renderHeader({
        auth: {
          isAuthenticated: true,
          user: { username: 'admin', user_type: 'admin' },
        },
      });
      
      const userButton = screen.getByText('admin');
      fireEvent.click(userButton);
      
      await waitFor(() => {
        expect(screen.getByText('Admin Panel')).toBeInTheDocument();
      });
    });

    it('shows logout button', async () => {
      renderHeader(authenticatedState);
      
      const userButton = screen.getByText('testuser');
      fireEvent.click(userButton);
      
      await waitFor(() => {
        expect(screen.getByTestId('logout-button')).toBeInTheDocument();
      });
    });
  });

  describe('Cart Icon', () => {
    it('shows cart with item count', () => {
      renderHeader({
        cart: {
          itemCount: 3,
        },
      });
      
      expect(screen.getByText('Cart')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('does not show count badge when cart is empty', () => {
      renderHeader({
        cart: {
          itemCount: 0,
        },
      });
      
      expect(screen.getByText('Cart')).toBeInTheDocument();
      expect(screen.queryByText('0')).not.toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('handles search suggestion selection', () => {
      renderHeader();
      
      const searchInput = screen.getByTestId('search-autocomplete');
      fireEvent.change(searchInput, { target: { value: 'test' } });
      
      expect(mockPush).toHaveBeenCalledWith('/products/1');
    });
  });

  describe('Secondary Navigation', () => {
    it('renders category links', () => {
      renderHeader();
      
      expect(screen.getByText('Electronics')).toBeInTheDocument();
      expect(screen.getByText('Fashion')).toBeInTheDocument();
      expect(screen.getByText('Home & Kitchen')).toBeInTheDocument();
      expect(screen.getByText('Books')).toBeInTheDocument();
      expect(screen.getByText('Sports')).toBeInTheDocument();
      expect(screen.getByText('Beauty')).toBeInTheDocument();
      expect(screen.getByText('Grocery')).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    it('hides username on mobile screens', () => {
      renderHeader({
        auth: {
          isAuthenticated: true,
          user: { username: 'testuser', user_type: 'customer' },
        },
      });
      
      const usernameElement = screen.getByText('testuser');
      expect(usernameElement).toHaveClass('hidden', 'md:block');
    });

    it('hides cart text on mobile screens', () => {
      renderHeader();
      
      const cartTextElement = screen.getByText('Cart');
      expect(cartTextElement).toHaveClass('hidden', 'md:block');
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes for dropdown triggers', () => {
      renderHeader();
      
      const moreButton = screen.getByText('More');
      expect(moreButton.closest('button')).toHaveAttribute('aria-expanded');
      expect(moreButton.closest('button')).toHaveAttribute('aria-haspopup');
    });

    it('shows user avatar with proper alt text', () => {
      renderHeader({
        auth: {
          isAuthenticated: true,
          user: { username: 'testuser', user_type: 'customer' },
        },
      });
      
      const avatar = screen.getByText('T'); // First letter of username
      expect(avatar).toBeInTheDocument();
    });
  });
});