import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import { ProductDetails } from '../ProductDetails';
import { renderWithProviders, createMockProduct } from '@/test-utils';

// Mock formatCurrency utility
jest.mock('@/utils/format', () => ({
  formatCurrency: (value: number) => `$${value.toFixed(2)}`,
}));

describe(&apos;ProductDetails&apos;, () => {
  const mockProduct = createMockProduct();

  it(&apos;renders product details correctly&apos;, () => {
    renderWithProviders(<ProductDetails product={mockProduct} />);

    // Check if product name is rendered (using role to get the main heading)
    expect(screen.getByRole(&apos;heading&apos;, { name: &apos;Test Product&apos; })).toBeInTheDocument();

    // Check if product description is rendered
    expect(screen.getByText(&apos;Test description with details about the product.&apos;)).toBeInTheDocument();

    // Check if brand is rendered
    expect(screen.getByText(&apos;Brand: Test Brand&apos;)).toBeInTheDocument();

    // Check if price is rendered
    expect(screen.getByText(&apos;$80.00&apos;)).toBeInTheDocument();

    // Check if original price is rendered
    expect(screen.getByText(&apos;$100.00&apos;)).toBeInTheDocument();

    // Check if SKU is rendered
    expect(screen.getByText(&apos;SKU: TEST123&apos;)).toBeInTheDocument();

    // Check if category is rendered in breadcrumbs
    expect(screen.getAllByText(&apos;Test Category&apos;)[0]).toBeInTheDocument();

    // Check if weight is rendered
    expect(screen.getByText(&apos;1 kg&apos;)).toBeInTheDocument();
  });

  it(&apos;renders product images and thumbnails correctly&apos;, () => {
    renderWithProviders(<ProductDetails product={mockProduct} />);

    // Check if main image is rendered
    const mainImage = screen.getAllByRole(&apos;img&apos;)[0];
    expect(mainImage).toHaveAttribute(&apos;src&apos;, &apos;/test-image-1.jpg&apos;);

    // Check if thumbnails are rendered
    const thumbnails = screen.getAllByRole(&apos;img&apos;);
    expect(thumbnails.length).toBe(3); // Main image + 2 thumbnails
    expect(thumbnails[1]).toHaveAttribute(&apos;src&apos;, &apos;/test-image-1.jpg&apos;);
    expect(thumbnails[2]).toHaveAttribute(&apos;src&apos;, &apos;/test-image-2.jpg&apos;);
  });

  it(&apos;changes main image when thumbnail is clicked&apos;, () => {
    renderWithProviders(<ProductDetails product={mockProduct} />);

    // Get main image before clicking thumbnail
    const mainImageBefore = screen.getAllByRole(&apos;img&apos;)[0];
    expect(mainImageBefore).toHaveAttribute(&apos;src&apos;, &apos;/test-image-1.jpg&apos;);

    // Click on second thumbnail
    const secondThumbnail = screen.getAllByRole(&apos;button&apos;)[1]; // First button is quantity input
    fireEvent.click(secondThumbnail);

    // Check if main image has changed
    const mainImageAfter = screen.getAllByRole(&apos;img&apos;)[0];
    expect(mainImageAfter).toHaveAttribute(&apos;src&apos;, &apos;/test-image-2.jpg&apos;);
  });

  it(&apos;updates quantity when input changes&apos;, () => {
    renderWithProviders(<ProductDetails product={mockProduct} />);

    // Get quantity input
    const quantityInput = screen.getByLabelText(&apos;Quantity&apos;);

    // Change quantity
    fireEvent.change(quantityInput, { target: { value: &apos;3&apos; } });

    // Check if quantity has been updated
    expect(quantityInput).toHaveValue(3);
  });

  it(&apos;dispatches addToCart action when add to cart button is clicked&apos;, () => {

    // Mock the dispatch function
    const mockDispatch = jest.fn();
    store.dispatch = mockDispatch;

    // Get quantity input and change it
    const quantityInput = screen.getByLabelText(&apos;Quantity&apos;);
    fireEvent.change(quantityInput, { target: { value: &apos;3&apos; } });

    // Click add to cart button
    const addToCartButton = screen.getByText(&apos;Add to Cart&apos;);
    fireEvent.click(addToCartButton);

    // Check if dispatch was called
    expect(mockDispatch).toHaveBeenCalled();
  });

  it(&apos;renders out of stock state correctly&apos;, () => {
    const outOfStockProduct = createMockProduct({
      status: &apos;out_of_stock&apos;,
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