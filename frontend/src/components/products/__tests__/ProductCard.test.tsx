import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductCard } from '../ProductCard';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { addToCart } from '@/store/slices/cartSlice';

// Mock Next.js components
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: unknown) => {
    // eslint-disable-next-line @next/next/no-img-element
    return <img {...props} src={props.src} alt={props.alt} />;
  },
}));

jest.mock(&apos;next/link&apos;, () => ({
  __esModule: true,
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock formatCurrency utility
jest.mock(&apos;@/utils/format&apos;, () => ({
  formatCurrency: (value: number) => `$${value.toFixed(2)}`,
}));

const mockStore = configureStore([]);

describe(&apos;ProductCard&apos;, () => {
  const mockProduct = {
    id: &apos;1&apos;,
    name: &apos;Test Product&apos;,
    slug: &apos;test-product&apos;,
    description: &apos;Test description&apos;,
    short_description: &apos;Short description&apos;,
    category: {
      id: &apos;cat1&apos;,
      name: &apos;Test Category&apos;,
      slug: &apos;test-category&apos;,
      is_active: true,
      created_at: &apos;2023-01-01&apos;,
    },
    brand: &apos;Test Brand&apos;,
    sku: &apos;TEST123&apos;,
    price: 100,
    discount_price: 80,
    is_active: true,
    is_featured: false,
    weight: 1,
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
  };

  it(&apos;renders product information correctly&apos;, () => {
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
    expect(screen.getByText(&apos;Test Product&apos;)).toBeInTheDocument();
    
    // Check if category name is rendered
    expect(screen.getByText(&apos;Test Category&apos;)).toBeInTheDocument();
    
    // Check if brand is rendered
    expect(screen.getByText(&apos;Test Brand&apos;)).toBeInTheDocument();
    
    // Check if price is rendered
    expect(screen.getByText(&apos;$80.00&apos;)).toBeInTheDocument();
    
    // Check if original price is rendered and has line-through style
    const originalPrice = screen.getByText(&apos;$100.00&apos;);
    expect(originalPrice).toBeInTheDocument();
    expect(originalPrice).toHaveClass(&apos;line-through&apos;);
    
    // Check if discount badge is rendered
    expect(screen.getByText(&apos;20% OFF&apos;)).toBeInTheDocument();
  });

  it(&apos;dispatches addToCart action when add to cart button is clicked&apos;, () => {
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
    const addToCartButton = screen.getByLabelText(&apos;Add to cart&apos;);
    fireEvent.click(addToCartButton);

    // Check if the addToCart action was dispatched with the correct payload
    expect(store.dispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        type: expect.stringContaining(&apos;cart/addToCart&apos;),
        payload: { productId: &apos;1&apos;, quantity: 1 },
      })
    );
  });

  it(&apos;renders product without discount correctly&apos;, () => {
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