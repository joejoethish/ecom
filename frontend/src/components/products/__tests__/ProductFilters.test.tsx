import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductFilters } from '../ProductFilters';

describe('ProductFilters', () => {
  const mockBrands = [
    { label: 'Brand 1', value: 'brand1', count: 10 },
    { label: 'Brand 2', value: 'brand2', count: 5 },
    { label: 'Brand 3', value: 'brand3', count: 3 },
  ];

  const mockPriceRange = {
    min: 10,
    max: 1000,
  };

  it('renders filter sections correctly', () => {
    const handleFilterChange = jest.fn();
    render(
      <ProductFilters
        brands={mockBrands}
        priceRange={mockPriceRange}
        onFilterChange={handleFilterChange}
      />
    );

    // Check if price range section is rendered
    expect(screen.getByText('Price Range')).toBeInTheDocument();
    
    // Check if brands section is rendered
    expect(screen.getByText('Brands')).toBeInTheDocument();
    
    // Check if discount filter is rendered
    expect(screen.getByText('On Sale')).toBeInTheDocument();
    
    // Check if sort by section is rendered
    expect(screen.getByText('Sort By')).toBeInTheDocument();
  });

  it('renders brand options correctly', () => {
    const handleFilterChange = jest.fn();
    render(
      <ProductFilters
        brands={mockBrands}
        priceRange={mockPriceRange}
        onFilterChange={handleFilterChange}
      />
    );

    // Check if brand options are rendered
    expect(screen.getByText('Brand 1 (10)')).toBeInTheDocument();
    expect(screen.getByText('Brand 2 (5)')).toBeInTheDocument();
    expect(screen.getByText('Brand 3 (3)')).toBeInTheDocument();
  });

  it('updates price range inputs correctly', () => {
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
    fireEvent.change(minPriceInput, { target: { value: '20' } });
    expect(minPriceInput).toHaveValue(20);
    
    // Change max price
    fireEvent.change(maxPriceInput, { target: { value: '500' } });
    expect(maxPriceInput).toHaveValue(500);
  });

  it('toggles brand checkboxes correctly', () => {
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

  it('toggles discount filter correctly', () => {
    const handleFilterChange = jest.fn();
    render(
      <ProductFilters
        brands={mockBrands}
        priceRange={mockPriceRange}
        onFilterChange={handleFilterChange}
      />
    );

    // Get discount checkbox
    const discountCheckbox = screen.getByLabelText('On Sale');
    
    // Check discount
    fireEvent.click(discountCheckbox);
    expect(discountCheckbox).toBeChecked();
    
    // Uncheck discount
    fireEvent.click(discountCheckbox);
    expect(discountCheckbox).not.toBeChecked();
  });

  it('changes sort option correctly', () => {
    const handleFilterChange = jest.fn();
    render(
      <ProductFilters
        brands={mockBrands}
        priceRange={mockPriceRange}
        onFilterChange={handleFilterChange}
      />
    );

    // Get sort select
    const sortSelect = screen.getByRole('combobox');
    
    // Change sort option
    fireEvent.change(sortSelect, { target: { value: 'price' } });
    expect(sortSelect).toHaveValue('price');
  });

  it('calls onFilterChange with correct filters when Apply Filters button is clicked', () => {
    const handleFilterChange = jest.fn();
    render(
      <ProductFilters
        brands={mockBrands}
        priceRange={mockPriceRange}
        onFilterChange={handleFilterChange}
      />
    );

    // Set up filters
    fireEvent.change(screen.getByPlaceholderText(/min/i), { target: { value: '20' } });
    fireEvent.change(screen.getByPlaceholderText(/max/i), { target: { value: '500' } });
    fireEvent.click(screen.getByLabelText(/Brand 1/));
    fireEvent.click(screen.getByLabelText(/Brand 2/));
    fireEvent.click(screen.getByLabelText('On Sale'));
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'price' } });
    
    // Click Apply Filters button
    fireEvent.click(screen.getByText('Apply Filters'));
    
    // Check if onFilterChange was called with correct filters
    expect(handleFilterChange).toHaveBeenCalledWith({
      min_price: 20,
      max_price: 500,
      brand: 'brand1,brand2',
      has_discount: true,
      sort: 'price',
    });
  });

  it('resets filters when Reset button is clicked', () => {
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
    fireEvent.click(screen.getByText('Reset'));
    
    // Check if onFilterChange was called with empty filters
    expect(handleFilterChange).toHaveBeenCalledWith({});
    
    // Check if inputs are reset
    expect(screen.getByPlaceholderText(/min/i)).toHaveValue('');
    expect(screen.getByPlaceholderText(/max/i)).toHaveValue('');
    expect(screen.getByLabelText(/Brand 1/)).not.toBeChecked();
    expect(screen.getByLabelText(/Brand 2/)).not.toBeChecked();
    expect(screen.getByLabelText('On Sale')).not.toBeChecked();
    expect(screen.getByRole('combobox')).toHaveValue('');
  });

  it('initializes with provided initial filters', () => {
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