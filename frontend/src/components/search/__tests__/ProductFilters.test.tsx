import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ProductFilters } from '../ProductFilters';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/utils/api';

// Mock the next/navigation router and searchParams
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

// Mock the API client
jest.mock('@/utils/api', () => ({
  apiClient: {
    get: jest.fn(),
  },
}));

describe('ProductFilters Component', () => {
  const mockRouter = {
    push: jest.fn(),
  };
  
  const mockSearchParams = {
    get: jest.fn(),
    toString: jest.fn().mockReturnValue(''),
  };
  
  const mockFilterOptions = {
    categories: [
      { name: 'Electronics', count: 42 },
      { name: 'Clothing', count: 36 },
      { name: 'Books', count: 28 },
    ],
    brands: [
      { name: 'Apple', count: 15 },
      { name: 'Samsung', count: 12 },
      { name: 'Sony', count: 8 },
    ],
    price_ranges: [
      { from: null, to: 100, count: 25, label: 'Under $100' },
      { from: 100, to: 500, count: 30, label: '$100 - $500' },
      { from: 500, to: 1000, count: 15, label: '$500 - $1000' },
      { from: 1000, to: null, count: 10, label: '$1000+' },
    ],
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);
    (apiClient.get as jest.Mock).mockResolvedValue({
      success: true,
      data: mockFilterOptions,
    });
  });

  test('renders the filter component correctly', async () => {
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText('Filters')).toBeInTheDocument();
    });
    
    // Check if categories are displayed
    await waitFor(() => {
      expect(screen.getByText('Categories')).toBeInTheDocument();
      expect(screen.getByText('Electronics (42)')).toBeInTheDocument();
      expect(screen.getByText('Clothing (36)')).toBeInTheDocument();
      expect(screen.getByText('Books (28)')).toBeInTheDocument();
    });
    
    // Check if brands are displayed
    await waitFor(() => {
      expect(screen.getByText('Brands')).toBeInTheDocument();
      expect(screen.getByText('Apple (15)')).toBeInTheDocument();
      expect(screen.getByText('Samsung (12)')).toBeInTheDocument();
      expect(screen.getByText('Sony (8)')).toBeInTheDocument();
    });
    
    // Check if price ranges are displayed
    await waitFor(() => {
      expect(screen.getByText('Price Range')).toBeInTheDocument();
      expect(screen.getByText('Under $100 (25)')).toBeInTheDocument();
      expect(screen.getByText('$100 - $500 (30)')).toBeInTheDocument();
      expect(screen.getByText('$500 - $1000 (15)')).toBeInTheDocument();
      expect(screen.getByText('$1000+ (10)')).toBeInTheDocument();
    });
    
    // Check if additional filters are displayed
    expect(screen.getByText('Additional Filters')).toBeInTheDocument();
    expect(screen.getByText('Discounted Items Only')).toBeInTheDocument();
    expect(screen.getByText('Featured Items Only')).toBeInTheDocument();
  });

  test('handles category filter selection', async () => {
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText('Categories')).toBeInTheDocument();
    });
    
    // Click on a category
    const categoryCheckbox = screen.getByLabelText('Electronics (42)');
    fireEvent.click(categoryCheckbox);
    
    // Check if router was called with correct URL
    expect(mockRouter.push).toHaveBeenCalledWith('/products?category=Electronics');
  });

  test('handles brand filter selection', async () => {
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText('Brands')).toBeInTheDocument();
    });
    
    // Click on a brand
    const brandCheckbox = screen.getByLabelText('Apple');
    fireEvent.click(brandCheckbox);
    
    // Check if router was called with correct URL
    expect(mockRouter.push).toHaveBeenCalledWith('/products?brand=Apple');
  });

  test('handles price range filter selection', async () => {
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText('Price Range')).toBeInTheDocument();
    });
    
    // Click on a price range
    const priceRangeRadio = screen.getByLabelText('$100 - $500');
    fireEvent.click(priceRangeRadio);
    
    // Check if router was called with correct URL
    expect(mockRouter.push).toHaveBeenCalledWith('/products?min_price=100&max_price=500');
  });

  test('handles discount only filter selection', async () => {
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText('Additional Filters')).toBeInTheDocument();
    });
    
    // Click on discount only checkbox
    const discountCheckbox = screen.getByLabelText('Discounted Items Only');
    fireEvent.click(discountCheckbox);
    
    // Check if router was called with correct URL
    expect(mockRouter.push).toHaveBeenCalledWith('/products?discount_only=true');
  });

  test('handles featured only filter selection', async () => {
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText('Additional Filters')).toBeInTheDocument();
    });
    
    // Click on featured only checkbox
    const featuredCheckbox = screen.getByLabelText('Featured Items Only');
    fireEvent.click(featuredCheckbox);
    
    // Check if router was called with correct URL
    expect(mockRouter.push).toHaveBeenCalledWith('/products?is_featured=true');
  });

  test('clears all filters when clear button is clicked', async () => {
    // Mock initial filters
    mockSearchParams.get.mockImplementation((param) => {
      if (param === 'category') return 'Electronics';
      if (param === 'brand') return 'Apple';
      if (param === 'discount_only') return 'true';
      return null;
    });
    
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText('Clear All')).toBeInTheDocument();
    });
    
    // Click on clear all button
    const clearButton = screen.getByText('Clear All');
    fireEvent.click(clearButton);
    
    // Check if router was called with URL without filters
    expect(mockRouter.push).toHaveBeenCalledWith('/products');
  });

  test('preserves search query when applying filters', async () => {
    // Mock search query
    mockSearchParams.get.mockImplementation((param) => {
      if (param === 'search') return 'smartphone';
      return null;
    });
    
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText('Categories')).toBeInTheDocument();
    });
    
    // Click on a category
    const categoryCheckbox = screen.getByLabelText('Electronics (42)');
    fireEvent.click(categoryCheckbox);
    
    // Check if router was called with correct URL that includes the search query
    expect(mockRouter.push).toHaveBeenCalledWith('/products?category=Electronics&search=smartphone');
  });

  test('handles API error gracefully', async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({
      success: false,
      error: {
        message: 'Failed to load filter options'
      }
    });
    
    render(<ProductFilters />);
    
    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText('Failed to load filter options')).toBeInTheDocument();
    });
  });
});