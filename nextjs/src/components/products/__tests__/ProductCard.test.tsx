import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductCard } from '../ProductCard';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { addToCart } from '@/store/slices/cartSlice';

// Mock Next.js components
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line @next/next/no-img-element
    return <img {...props} src={props.src} alt={props.alt} />;
  },
}));

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock formatCurrency utility
jest.mock('@/utils/format', () => ({
  formatCurrency: (value: number) => `$${value.toFixed(2)}`,
}));

const mockStore = configureStore([]);

describe('ProductCard', () => {
  const mockProduct = {
    id: '1',
    name: 'Test Product',
    slug: 'test-product',
    description: 'Test description',
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
  };

  it('renders product information correctly', () => {
    const store = mockStore({
      cart: {
        items: [],
        itemCount: 0,
        totalAmount: 0,
        loading: false,
        error: null,
      },
    });

    render(
      <Provider store={store}>
        <ProductCard product={mockProduct} />
      </Provider>
    );

    // Check if product name is rendered
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    
    // Check if category name is rendered
    expect(screen.getByText('Test Category')).toBeInTheDocument();
    
    // Check if brand is rendered
    expect(screen.getByText('Test Brand')).toBeInTheDocument();
    
    // Check if price is rendered
    expect(screen.getByText('$80.00')).toBeInTheDocument();
    
    // Check if original price is rendered and has line-through style
    const originalPrice = screen.getByText('$100.00');
    expect(originalPrice).toBeInTheDocument();
    expect(originalPrice).toHaveClass('line-through');
    
    // Check if discount badge is rendered
    expect(screen.getByText('20% OFF')).toBeInTheDocument();
  });

  it('dispatches addToCart action when add to cart button is clicked', () => {
    const store = mockStore({
      cart: {
        items: [],
        itemCount: 0,
        totalAmount: 0,
        loading: false,
        error: null,
      },
    });

    store.dispatch = jest.fn();

    render(
      <Provider store={store}>
        <ProductCard product={mockProduct} />
      </Provider>
    );

    // Find and click the add to cart button
    const addToCartButton = screen.getByLabelText('Add to cart');
    fireEvent.click(addToCartButton);

    // Check if the addToCart action was dispatched with the correct payload
    expect(store.dispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        type: expect.stringContaining('cart/addToCart'),
        payload: { productId: '1', quantity: 1 },
      })
    );
  });

  it('renders product without discount correctly', () => {
    const productWithoutDiscount = {
      ...mockProduct,
      discount_price: undefined,
    };

    const store = mockStore({
      cart: {
        items: [],
        itemCount: 0,
        totalAmount: 0,
        loading: false,
        error: null,
      },
    });

    render(
      <Provider store={store}>
        <ProductCard product={productWithoutDiscount} />
      </Provider>
    );

    // Check if price is rendered
    expect(screen.getByText('$100.00')).toBeInTheDocument();
    
    // Check that there's no discount badge
    expect(screen.queryByText('% OFF')).not.toBeInTheDocument();
    
    // Check that there's no original price with line-through
    const prices = screen.getAllByText('$100.00');
    expect(prices.length).toBe(1);
    expect(prices[0]).not.toHaveClass('line-through');
  });
});