import React from 'react';
import { render, screen } from '@testing-library/react';
import { ProductGrid } from '../ProductGrid';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';

// Mock the ProductCard component
jest.mock('../ProductCard', () => ({
  ProductCard: ({ product }: { product: any }) => (
    <div data-testid={`product-card-${product.id}`}>
      {product.name}
    </div>
  ),
}));

const mockStore = configureStore([]);

describe('ProductGrid', () => {
  const mockProducts = [
    {
      id: '1',
      name: 'Product 1',
      price: 100,
      rating: 4.5,
      reviewCount: 10,
      image: '/product1.jpg',
      brand: 'Brand 1',
      features: ['Feature 1', 'Feature 2'],
      freeDelivery: true,
      exchangeOffer: true,
    },
    {
      id: '2',
      name: 'Product 2',
      price: 200,
      originalPrice: 250,
      discount: 20,
      rating: 4.0,
      reviewCount: 5,
      image: '/product2.jpg',
      brand: 'Brand 2',
      features: ['Feature A', 'Feature B'],
      freeDelivery: false,
      exchangeOffer: true,
    },
  ];

  it('renders loading state correctly', () => {
    const store = mockStore({});

    render(
      <Provider store={store}>
        <ProductGrid products={[]} loading={true} />
      </Provider>
    );

    // Check if loading spinner is rendered
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders empty state correctly', () => {
    const store = mockStore({});

    render(
      <Provider store={store}>
        <ProductGrid products={[]} />
      </Provider>
    );

    // Check if empty state is rendered
    expect(screen.getByText('No products found')).toBeInTheDocument();
  });

  it('renders products correctly', () => {
    const store = mockStore({});

    render(
      <Provider store={store}>
        <ProductGrid products={mockProducts} />
      </Provider>
    );

    // Check if product cards are rendered
    expect(screen.getByTestId('product-card-1')).toBeInTheDocument();
    expect(screen.getByTestId('product-card-2')).toBeInTheDocument();
    expect(screen.getByText('Product 1')).toBeInTheDocument();
    expect(screen.getByText('Product 2')).toBeInTheDocument();
  });

  it('applies correct grid columns based on props', () => {
    const store = mockStore({});

    const { container, rerender } = render(
      <Provider store={store}>
        <ProductGrid products={mockProducts} columns={2} />
      </Provider>
    );

    // Check if grid has the correct column classes for 2 columns
    expect(container.firstChild).toHaveClass('grid-cols-1');
    expect(container.firstChild).toHaveClass('sm:grid-cols-2');

    // Rerender with 3 columns
    rerender(
      <Provider store={store}>
        <ProductGrid products={mockProducts} columns={3} />
      </Provider>
    );

    // Check if grid has the correct column classes for 3 columns
    expect(container.firstChild).toHaveClass('grid-cols-1');
    expect(container.firstChild).toHaveClass('sm:grid-cols-2');
    expect(container.firstChild).toHaveClass('lg:grid-cols-3');

    // Rerender with 4 columns
    rerender(
      <Provider store={store}>
        <ProductGrid products={mockProducts} columns={4} />
      </Provider>
    );

    // Check if grid has the correct column classes for 4 columns
    expect(container.firstChild).toHaveClass('grid-cols-1');
    expect(container.firstChild).toHaveClass('sm:grid-cols-2');
    expect(container.firstChild).toHaveClass('md:grid-cols-3');
    expect(container.firstChild).toHaveClass('lg:grid-cols-4');
  });
});