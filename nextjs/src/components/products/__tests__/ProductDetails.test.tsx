import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductDetails } from '../ProductDetails';
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

describe('ProductDetails', () => {
  const mockProduct = {
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
  };

  it('renders product details correctly', () => {
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
        <ProductDetails product={mockProduct} />
      </Provider>
    );

    // Check if product name is rendered
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    
    // Check if product description is rendered
    expect(screen.getByText('Test description with details about the product.')).toBeInTheDocument();
    
    // Check if brand is rendered
    expect(screen.getByText('Brand: Test Brand')).toBeInTheDocument();
    
    // Check if price is rendered
    expect(screen.getByText('$80.00')).toBeInTheDocument();
    
    // Check if original price is rendered
    expect(screen.getByText('$100.00')).toBeInTheDocument();
    
    // Check if SKU is rendered
    expect(screen.getByText('SKU: TEST123')).toBeInTheDocument();
    
    // Check if category is rendered in breadcrumbs
    expect(screen.getAllByText('Test Category')[0]).toBeInTheDocument();
    
    // Check if weight is rendered
    expect(screen.getByText('1 kg')).toBeInTheDocument();
  });

  it('renders product images and thumbnails correctly', () => {
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
        <ProductDetails product={mockProduct} />
      </Provider>
    );

    // Check if main image is rendered
    const mainImage = screen.getAllByRole('img')[0];
    expect(mainImage).toHaveAttribute('src', '/test-image-1.jpg');
    
    // Check if thumbnails are rendered
    const thumbnails = screen.getAllByRole('img');
    expect(thumbnails.length).toBe(3); // Main image + 2 thumbnails
    expect(thumbnails[1]).toHaveAttribute('src', '/test-image-1.jpg');
    expect(thumbnails[2]).toHaveAttribute('src', '/test-image-2.jpg');
  });

  it('changes main image when thumbnail is clicked', () => {
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
        <ProductDetails product={mockProduct} />
      </Provider>
    );

    // Get main image before clicking thumbnail
    const mainImageBefore = screen.getAllByRole('img')[0];
    expect(mainImageBefore).toHaveAttribute('src', '/test-image-1.jpg');
    
    // Click on second thumbnail
    const secondThumbnail = screen.getAllByRole('button')[1]; // First button is quantity input
    fireEvent.click(secondThumbnail);
    
    // Check if main image has changed
    const mainImageAfter = screen.getAllByRole('img')[0];
    expect(mainImageAfter).toHaveAttribute('src', '/test-image-2.jpg');
  });

  it('updates quantity when input changes', () => {
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
        <ProductDetails product={mockProduct} />
      </Provider>
    );

    // Get quantity input
    const quantityInput = screen.getByLabelText('Quantity');
    
    // Change quantity
    fireEvent.change(quantityInput, { target: { value: '3' } });
    
    // Check if quantity has been updated
    expect(quantityInput).toHaveValue(3);
  });

  it('dispatches addToCart action with correct quantity when add to cart button is clicked', () => {
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
        <ProductDetails product={mockProduct} />
      </Provider>
    );

    // Get quantity input and change it
    const quantityInput = screen.getByLabelText('Quantity');
    fireEvent.change(quantityInput, { target: { value: '3' } });
    
    // Click add to cart button
    const addToCartButton = screen.getByText('Add to Cart');
    fireEvent.click(addToCartButton);
    
    // Check if addToCart action was dispatched with correct payload
    expect(store.dispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        type: expect.stringContaining('cart/addToCart'),
        payload: { productId: '1', quantity: 3 },
      })
    );
  });

  it('renders out of stock state correctly', () => {
    const outOfStockProduct = {
      ...mockProduct,
      status: 'out_of_stock',
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
        <ProductDetails product={outOfStockProduct} />
      </Provider>
    );

    // Check if out of stock badge is rendered
    expect(screen.getByText('Out of Stock')).toBeInTheDocument();
    
    // Check if add to cart button is disabled
    const addToCartButton = screen.getByText('Out of Stock');
    expect(addToCartButton).toBeDisabled();
    expect(addToCartButton).toHaveClass('bg-gray-400');
    expect(addToCartButton).toHaveClass('cursor-not-allowed');
    
    // Check if quantity input is disabled
    const quantityInput = screen.getByLabelText('Quantity');
    expect(quantityInput).toBeDisabled();
  });
});