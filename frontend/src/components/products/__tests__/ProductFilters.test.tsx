import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductFilters } from '../ProductFilters';

describe('ProductFilters', () => {
  const mockBrands = [
    { label: &apos;Brand 1&apos;, value: &apos;brand1&apos;, count: 10 },
    { label: &apos;Brand 2&apos;, value: &apos;brand2&apos;, count: 5 },
    { label: &apos;Brand 3&apos;, value: &apos;brand3&apos;, count: 3 },
  ];

  const mockPriceRange = {
    min: 10,
    max: 1000,
  };

  it(&apos;renders filter sections correctly&apos;, () => {
    const handleFilterChange = jest.fn();
    render(
      <ProductFilters
        brands={mockBrands}
        priceRange={mockPriceRange}
        onFilterChange={handleFilterChange}
      />
    );

    // Check if price range section is rendered
    expect(screen.getByText(&apos;Price Range&apos;)).toBeInTheDocument();
    
    // Check if brands section is rendered
    expect(screen.getByText(&apos;Brands&apos;)).toBeInTheDocument();
    
    // Check if discount filter is rendered
    expect(screen.getByText(&apos;On Sale&apos;)).toBeInTheDocument();
    
    // Check if sort by section is rendered
    expect(screen.getByText(&apos;Sort By&apos;)).toBeInTheDocument();
  });

  it(&apos;renders brand options correctly&apos;, () => {
    const handleFilterChange = jest.fn();
    render(
      <ProductFilters
        brands={mockBrands}
        priceRange={mockPriceRange}
        onFilterChange={handleFilterChange}
      />
    );

    // Check if brand options are rendered
    expect(screen.getByText(&apos;Brand 1 (10)&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Brand 2 (5)&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Brand 3 (3)&apos;)).toBeInTheDocument();
  });

  it(&apos;updates price range inputs correctly&apos;, () => {
    const handleFilterChange = jest.fn();
    render(
      <ProductFilters
        brands={mockBrands}
        priceRange={mockPriceRange}
        onFilterChange={handleFilterChange}
      />
    );

    // Get price range inputs
    const minPriceInput = screen.getByPlaceholderText(/min/i);
    const maxPriceInput = screen.getByPlaceholderText(/max/i);
    
    // Change min price
    fireEvent.change(minPriceInput, { target: { value: &apos;20&apos; } });
    expect(minPriceInput).toHaveValue(20);
    
    // Change max price
    fireEvent.change(maxPriceInput, { target: { value: &apos;500&apos; } });
    expect(maxPriceInput).toHaveValue(500);
  });

  it(&apos;toggles brand checkboxes correctly&apos;, () => {
    const handleFilterChange = jest.fn();
    render(
      <ProductFilters
        brands={mockBrands}
        priceRange={mockPriceRange}
        onFilterChange={handleFilterChange}
      />
    );

    // Get brand checkboxes
    const brand1Checkbox = screen.getByLabelText(/Brand 1/);
    const brand2Checkbox = screen.getByLabelText(/Brand 2/);
    
    // Check brand1
    fireEvent.click(brand1Checkbox);
    expect(brand1Checkbox).toBeChecked();
    
    // Check brand2
    fireEvent.click(brand2Checkbox);
    expect(brand2Checkbox).toBeChecked();
    
    // Uncheck brand1
    fireEvent.click(brand1Checkbox);
    expect(brand1Checkbox).not.toBeChecked();
  });

  it(&apos;toggles discount filter correctly&apos;, () => {
    const handleFilterChange = jest.fn();
    render(
      <ProductFilters
        brands={mockBrands}
        priceRange={mockPriceRange}
        onFilterChange={handleFilterChange}
      />
    );

    // Get discount checkbox
    const discountCheckbox = screen.getByLabelText(&apos;On Sale&apos;);
    
    // Check discount
    fireEvent.click(discountCheckbox);
    expect(discountCheckbox).toBeChecked();
    
    // Uncheck discount
    fireEvent.click(discountCheckbox);
    expect(discountCheckbox).not.toBeChecked();
  });

  it(&apos;changes sort option correctly&apos;, () => {
    const handleFilterChange = jest.fn();
    render(
      <ProductFilters
        brands={mockBrands}
        priceRange={mockPriceRange}
        onFilterChange={handleFilterChange}
      />
    );

    // Get sort select
    const sortSelect = screen.getByRole(&apos;combobox&apos;);
    
    // Change sort option
    fireEvent.change(sortSelect, { target: { value: &apos;price&apos; } });
    expect(sortSelect).toHaveValue(&apos;price&apos;);
  });

  it(&apos;calls onFilterChange with correct filters when Apply Filters button is clicked&apos;, () => {
    const handleFilterChange = jest.fn();
    render(
      <ProductFilters
        brands={mockBrands}
        priceRange={mockPriceRange}
        onFilterChange={handleFilterChange}
      />
    );

    // Set up filters
    fireEvent.change(screen.getByPlaceholderText(/min/i), { target: { value: &apos;20&apos; } });
    fireEvent.change(screen.getByPlaceholderText(/max/i), { target: { value: &apos;500&apos; } });
    fireEvent.click(screen.getByLabelText(/Brand 1/));
    fireEvent.click(screen.getByLabelText(/Brand 2/));
    fireEvent.click(screen.getByLabelText(&apos;On Sale&apos;));
    fireEvent.change(screen.getByRole(&apos;combobox&apos;), { target: { value: &apos;price&apos; } });
    
    // Click Apply Filters button
    fireEvent.click(screen.getByText(&apos;Apply Filters&apos;));
    
    // Check if onFilterChange was called with correct filters
    expect(handleFilterChange).toHaveBeenCalledWith({
      min_price: 20,
      max_price: 500,
      brand: &apos;brand1,brand2&apos;,
      has_discount: true,
      sort: &apos;price&apos;,
    });
  });

  it(&apos;resets filters when Reset button is clicked&apos;, () => {
    const handleFilterChange = jest.fn();
    render(
      <ProductFilters
        brands={mockBrands}
        priceRange={mockPriceRange}
        onFilterChange={handleFilterChange}
        initialFilters={{
          min_price: 20,
          max_price: 500,
          brand: ['brand1', 'brand2'],
          has_discount: true,
          sort: 'price',
        }}
      />
    );

    // Click Reset button
    fireEvent.click(screen.getByText(&apos;Reset&apos;));
    
    // Check if onFilterChange was called with empty filters
    expect(handleFilterChange).toHaveBeenCalledWith({});
    
    // Check if inputs are reset
    expect(screen.getByPlaceholderText(/min/i)).toHaveValue(&apos;&apos;);
    expect(screen.getByPlaceholderText(/max/i)).toHaveValue(&apos;&apos;);
    expect(screen.getByLabelText(/Brand 1/)).not.toBeChecked();
    expect(screen.getByLabelText(/Brand 2/)).not.toBeChecked();
    expect(screen.getByLabelText(&apos;On Sale&apos;)).not.toBeChecked();
    expect(screen.getByRole(&apos;combobox&apos;)).toHaveValue(&apos;&apos;);
  });

  it(&apos;initializes with provided initial filters&apos;, () => {
    const handleFilterChange = jest.fn();
    render(
      <ProductFilters
        brands={mockBrands}
        priceRange={mockPriceRange}
        onFilterChange={handleFilterChange}
        initialFilters={{
          min_price: 20,
          max_price: 500,
          brand: ['brand1', 'brand2'],
          has_discount: true,
          sort: 'price',
        }}
      />
    );

    // Check if inputs are initialized with initial filters
    expect(screen.getByPlaceholderText(/min/i)).toHaveValue(20);
    expect(screen.getByPlaceholderText(/max/i)).toHaveValue(500);
    expect(screen.getByLabelText(/Brand 1/)).toBeChecked();
    expect(screen.getByLabelText(/Brand 2/)).toBeChecked();
    expect(screen.getByLabelText('On Sale')).toBeChecked();
    expect(screen.getByRole('combobox')).toHaveValue('price');
  });
});