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
jest.mock(&apos;@/utils/api&apos;, () => ({
  apiClient: {
    get: jest.fn(),
  },
}));

describe(&apos;ProductFilters Component&apos;, () => {
  const mockRouter = {
    push: jest.fn(),
  };
  
  const mockSearchParams = {
    get: jest.fn(),
    toString: jest.fn().mockReturnValue(&apos;&apos;),
  };
  
  const mockFilterOptions = {
    categories: [
      { name: &apos;Electronics&apos;, count: 42 },
      { name: &apos;Clothing&apos;, count: 36 },
      { name: &apos;Books&apos;, count: 28 },
    ],
    brands: [
      { name: &apos;Apple&apos;, count: 15 },
      { name: &apos;Samsung&apos;, count: 12 },
      { name: &apos;Sony&apos;, count: 8 },
    ],
    price_ranges: [
      { from: null, to: 100, count: 25, label: &apos;Under $100&apos; },
      { from: 100, to: 500, count: 30, label: &apos;$100 - $500&apos; },
      { from: 500, to: 1000, count: 15, label: &apos;$500 - $1000&apos; },
      { from: 1000, to: null, count: 10, label: &apos;$1000+&apos; },
    ],
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);
    
    // Mock API calls based on the endpoint
    (apiClient.get as jest.Mock).mockImplementation((endpoint) => {
      if (endpoint === &apos;/categories/&apos;) {
        return Promise.resolve({
          success: true,
          data: {
            data: [
              { name: &apos;Electronics&apos;, product_count: 42 },
              { name: &apos;Clothing&apos;, product_count: 36 },
              { name: &apos;Books&apos;, product_count: 28 },
            ]
          }
        });
      }
      
      if (endpoint.startsWith(&apos;/categories/&apos;) && endpoint.endsWith(&apos;/filters/&apos;)) {
        return Promise.resolve({
          success: true,
          data: {
            category: { name: &apos;Electronics&apos; },
            total_products: 42,
            brands: mockFilterOptions.brands,
            price_ranges: mockFilterOptions.price_ranges,
          }
        });
      }
      
      return Promise.resolve({
        success: false,
        error: { message: &apos;Endpoint not found&apos; }
      });
    });
  });

  test(&apos;renders the filter component correctly&apos;, async () => {
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText(&apos;Filters&apos;)).toBeInTheDocument();
    });
    
    // Check if categories are displayed
    await waitFor(() => {
      expect(screen.getByText(&apos;Categories&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Electronics (42)&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Clothing (36)&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Books (28)&apos;)).toBeInTheDocument();
    });
    
    // Check if brands are displayed
    await waitFor(() => {
      expect(screen.getByText(&apos;Brands&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Apple (15)&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Samsung (12)&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Sony (8)&apos;)).toBeInTheDocument();
    });
    
    // Check if price ranges are displayed
    await waitFor(() => {
      expect(screen.getByText(&apos;Price Range&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Under $100 (25)&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;$100 - $500 (30)&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;$500 - $1000 (15)&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;$1000+ (10)&apos;)).toBeInTheDocument();
    });
    
    // Check if additional filters are displayed
    expect(screen.getByText(&apos;Additional Filters&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Discounted Items Only&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Featured Items Only&apos;)).toBeInTheDocument();
  });

  test(&apos;handles category filter selection&apos;, async () => {
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText(&apos;Categories&apos;)).toBeInTheDocument();
    });
    
    // Click on a category
    const categoryCheckbox = screen.getByLabelText(&apos;Electronics (42)&apos;);
    fireEvent.click(categoryCheckbox);
    
    // Check if router was called with correct URL
    expect(mockRouter.push).toHaveBeenCalledWith(&apos;/products?category=Electronics&apos;);
  });

  test(&apos;handles brand filter selection&apos;, async () => {
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText(&apos;Brands&apos;)).toBeInTheDocument();
    });
    
    // Click on a brand
    const brandCheckbox = screen.getByLabelText(&apos;Apple&apos;);
    fireEvent.click(brandCheckbox);
    
    // Check if router was called with correct URL
    expect(mockRouter.push).toHaveBeenCalledWith(&apos;/products?brand=Apple&apos;);
  });

  test(&apos;handles price range filter selection&apos;, async () => {
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText(&apos;Price Range&apos;)).toBeInTheDocument();
    });
    
    // Click on a price range
    const priceRangeRadio = screen.getByLabelText(&apos;$100 - $500&apos;);
    fireEvent.click(priceRangeRadio);
    
    // Check if router was called with correct URL
    expect(mockRouter.push).toHaveBeenCalledWith(&apos;/products?min_price=100&max_price=500&apos;);
  });

  test(&apos;handles discount only filter selection&apos;, async () => {
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText(&apos;Additional Filters&apos;)).toBeInTheDocument();
    });
    
    // Click on discount only checkbox
    const discountCheckbox = screen.getByLabelText(&apos;Discounted Items Only&apos;);
    fireEvent.click(discountCheckbox);
    
    // Check if router was called with correct URL
    expect(mockRouter.push).toHaveBeenCalledWith(&apos;/products?discount_only=true&apos;);
  });

  test(&apos;handles featured only filter selection&apos;, async () => {
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText(&apos;Additional Filters&apos;)).toBeInTheDocument();
    });
    
    // Click on featured only checkbox
    const featuredCheckbox = screen.getByLabelText(&apos;Featured Items Only&apos;);
    fireEvent.click(featuredCheckbox);
    
    // Check if router was called with correct URL
    expect(mockRouter.push).toHaveBeenCalledWith(&apos;/products?is_featured=true&apos;);
  });

  test(&apos;clears all filters when clear button is clicked&apos;, async () => {
    // Mock initial filters
    mockSearchParams.get.mockImplementation((param) => {
      if (param === &apos;category&apos;) return &apos;Electronics&apos;;
      if (param === &apos;brand&apos;) return &apos;Apple&apos;;
      if (param === &apos;discount_only&apos;) return &apos;true&apos;;
      return null;
    });
    
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText(&apos;Clear All&apos;)).toBeInTheDocument();
    });
    
    // Click on clear all button
    const clearButton = screen.getByText(&apos;Clear All&apos;);
    fireEvent.click(clearButton);
    
    // Check if router was called with URL without filters
    expect(mockRouter.push).toHaveBeenCalledWith(&apos;/products&apos;);
  });

  test(&apos;preserves search query when applying filters&apos;, async () => {
    // Mock search query
    mockSearchParams.get.mockImplementation((param) => {
      if (param === &apos;search&apos;) return &apos;smartphone&apos;;
      return null;
    });
    
    render(<ProductFilters />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText(&apos;Categories&apos;)).toBeInTheDocument();
    });
    
    // Click on a category
    const categoryCheckbox = screen.getByLabelText(&apos;Electronics (42)&apos;);
    fireEvent.click(categoryCheckbox);
    
    // Check if router was called with correct URL that includes the search query
    expect(mockRouter.push).toHaveBeenCalledWith(&apos;/products?category=Electronics&search=smartphone&apos;);
  });

  test(&apos;handles API error gracefully&apos;, async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({
      success: false,
      error: {
        message: &apos;Failed to load filter options&apos;
      }
    });
    
    render(<ProductFilters />);
    
    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText('Failed to load filter options')).toBeInTheDocument();
    });
  });
});