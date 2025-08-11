import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import { ProductDetails } from '../ProductDetails';
import { renderWithProviders, createMockProduct } from '@/test-utils';

// Mock formatCurrency utility
jest.mock('@/utils/format', () => ({
  formatCurrency: (value: number) => `$${value.toFixed(2)}`,
}));

describe('ProductDetails', () => {
  const mockProduct = createMockProduct();

  it('renders product details correctly', () => {
    renderWithProviders(<ProductDetails product={mockProduct} />);

    // Check if product name is rendered (using role to get the main heading)
    expect(screen.getByRole('heading', { name: 'Test Product' })).toBeInTheDocument();

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
    renderWithProviders(<ProductDetails product={mockProduct} />);

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
    renderWithProviders(<ProductDetails product={mockProduct} />);

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
    renderWithProviders(<ProductDetails product={mockProduct} />);

    // Get quantity input
    const quantityInput = screen.getByLabelText('Quantity');

    // Change quantity
    fireEvent.change(quantityInput, { target: { value: '3' } });

    // Check if quantity has been updated
    expect(quantityInput).toHaveValue(3);
  });

  it('dispatches addToCart action when add to cart button is clicked', () => {
    const { store } = renderWithProviders(<ProductDetails product={mockProduct} />);

    // Mock the dispatch function
    const mockDispatch = jest.fn();
    store.dispatch = mockDispatch;

    // Get quantity input and change it
    const quantityInput = screen.getByLabelText('Quantity');
    fireEvent.change(quantityInput, { target: { value: '3' } });

    // Click add to cart button
    const addToCartButton = screen.getByText('Add to Cart');
    fireEvent.click(addToCartButton);

    // Check if dispatch was called
    expect(mockDispatch).toHaveBeenCalled();
  });

  it('renders out of stock state correctly', () => {
    const outOfStockProduct = createMockProduct({
      status: 'out_of_stock',
    });

    renderWithProviders(<ProductDetails product={outOfStockProduct} />);

    // Check if out of stock badge is rendered
    expect(screen.getAllByText('Out of Stock')).toHaveLength(2); // Badge and button

    // Check if add to cart button is disabled
    const addToCartButton = screen.getByRole('button', { name: 'Out of Stock' });
    expect(addToCartButton).toBeDisabled();
    expect(addToCartButton).toHaveClass('bg-gray-400');
    expect(addToCartButton).toHaveClass('cursor-not-allowed');

    // Check if quantity input is disabled
    const quantityInput = screen.getByLabelText('Quantity');
    expect(quantityInput).toBeDisabled();
  });
});