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
      slug: 'product-1',
      description: 'Description 1',
      short_description: 'Short description 1',
      category: {
        id: 'cat1',
        name: 'Category 1',
        slug: 'category-1',
        is_active: true,
        created_at: '2023-01-01',
      },
      brand: 'Brand 1',
      sku: 'SKU1',
      price: 100,
      is_active: true,
      is_featured: false,
      images: [],
      created_at: '2023-01-01',
      updated_at: '2023-01-01',
    },
    {
      id: '2',
      name: 'Product 2',
      slug: 'product-2',
      description: 'Description 2',
      short_description: 'Short description 2',
      category: {
        id: 'cat2',
        name: 'Category 2',
        slug: 'category-2',
        is_active: true,
        created_at: '2023-01-01',
      },
      brand: 'Brand 2',
      sku: 'SKU2',
      price: 200,
      is_active: true,
      is_featured: false,
      images: [],
      created_at: '2023-01-01',
      updated_at: '2023-01-01',
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
    const emptyMessage = 'No products found';

    render(
      <Provider store={store}>
        <ProductGrid products={[]} emptyMessage={emptyMessage} />
      </Provider>
    );

    // Check if empty message is rendered
    expect(screen.getByText(emptyMessage)).toBeInTheDocument();
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