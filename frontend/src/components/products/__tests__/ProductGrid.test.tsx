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

describe(&apos;ProductGrid&apos;, () => {
  const mockProducts = [
    {
      id: &apos;1&apos;,
      name: &apos;Product 1&apos;,
      slug: &apos;product-1&apos;,
      description: &apos;Description 1&apos;,
      short_description: &apos;Short description 1&apos;,
      category: {
        id: &apos;cat1&apos;,
        name: &apos;Category 1&apos;,
        slug: &apos;category-1&apos;,
        is_active: true,
        created_at: &apos;2023-01-01&apos;,
      },
      brand: &apos;Brand 1&apos;,
      sku: &apos;SKU1&apos;,
      price: 100,
      is_active: true,
      is_featured: false,
      images: [],
      created_at: &apos;2023-01-01&apos;,
      updated_at: &apos;2023-01-01&apos;,
    },
    {
      id: &apos;2&apos;,
      name: &apos;Product 2&apos;,
      slug: &apos;product-2&apos;,
      description: &apos;Description 2&apos;,
      short_description: &apos;Short description 2&apos;,
      category: {
        id: &apos;cat2&apos;,
        name: &apos;Category 2&apos;,
        slug: &apos;category-2&apos;,
        is_active: true,
        created_at: &apos;2023-01-01&apos;,
      },
      brand: &apos;Brand 2&apos;,
      sku: &apos;SKU2&apos;,
      price: 200,
      is_active: true,
      is_featured: false,
      images: [],
      created_at: &apos;2023-01-01&apos;,
      updated_at: &apos;2023-01-01&apos;,
    },
  ];

  it(&apos;renders loading state correctly&apos;, () => {
    const store = mockStore({});

    render(
      <Provider store={store}>
        <ProductGrid products={[]} loading={true} />
      </Provider>
    );

    // Check if loading spinner is rendered
    expect(screen.getByRole(&apos;status&apos;)).toBeInTheDocument();
  });

  it(&apos;renders empty state correctly&apos;, () => {
    const store = mockStore({});
    const emptyMessage = &apos;No products found&apos;;

    render(
      <Provider store={store}>
        <ProductGrid products={[]} emptyMessage={emptyMessage} />
      </Provider>
    );

    // Check if empty message is rendered
    expect(screen.getByText(emptyMessage)).toBeInTheDocument();
  });

  it(&apos;renders products correctly&apos;, () => {
    const store = mockStore({});

    render(
      <Provider store={store}>
        <ProductGrid products={mockProducts} />
      </Provider>
    );

    // Check if product cards are rendered
    expect(screen.getByTestId(&apos;product-card-1&apos;)).toBeInTheDocument();
    expect(screen.getByTestId(&apos;product-card-2&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Product 1&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Product 2&apos;)).toBeInTheDocument();
  });

  it(&apos;applies correct grid columns based on props&apos;, () => {
    const store = mockStore({});

      <Provider store={store}>
        <ProductGrid products={mockProducts} columns={2} />
      </Provider>
    );

    // Check if grid has the correct column classes for 2 columns
    expect(container.firstChild).toHaveClass(&apos;grid-cols-1&apos;);
    expect(container.firstChild).toHaveClass(&apos;sm:grid-cols-2&apos;);

    // Rerender with 3 columns
    rerender(
      <Provider store={store}>
        <ProductGrid products={mockProducts} columns={3} />
      </Provider>
    );

    // Check if grid has the correct column classes for 3 columns
    expect(container.firstChild).toHaveClass(&apos;grid-cols-1&apos;);
    expect(container.firstChild).toHaveClass(&apos;sm:grid-cols-2&apos;);
    expect(container.firstChild).toHaveClass(&apos;lg:grid-cols-3&apos;);

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