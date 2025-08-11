import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SearchResults } from '../SearchResults';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/utils/api';

interface Product {
  id: string;
  name: string;
}

// Mock the ProductGrid component
jest.mock('@/components/products/ProductGrid', () => ({
  ProductGrid: ({ products }: { products: Product[] }) => (
    <div data-testid="product-grid">
      {products.map(product => (
        <div key={product.id} data-testid={`product-${product.id}`}>
          {product.name}
        </div>
      ))}
    </div>
  ),
}));

// Mock the Pagination component
jest.mock(&apos;@/components/products/Pagination&apos;, () => ({
  Pagination: ({ currentPage, totalPages, onPageChange }: { currentPage: number, totalPages: number, onPageChange: (page: number) => void }) => (
    <div data-testid="pagination">
      <span>Page {currentPage} of {totalPages}</span>
      <button onClick={() => onPageChange(currentPage + 1)}>Next</button>
    </div>
  ),
}));

// Mock the next/navigation router and searchParams
jest.mock(&apos;next/navigation&apos;, () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

// Mock the API client
jest.mock(&apos;@/utils/api&apos;, () => ({
  apiClient: {
    get: jest.fn(),
  },
}));

describe(&apos;SearchResults Component&apos;, () => {
  const mockRouter = {
    push: jest.fn(),
  };
  
  const mockSearchParams = {
    get: jest.fn(),
    toString: jest.fn().mockReturnValue(&apos;&apos;),
  };
  
  const mockSearchResults = {
    count: 42,
    results: [
      {
        id: &apos;1&apos;,
        name: &apos;Smartphone X&apos;,
        slug: &apos;smartphone-x&apos;,
        price: 999.99,
        discount_price: null,
        effective_price: 999.99,
        discount_percentage: 0,
        brand: &apos;Apple&apos;,
        category: { name: &apos;Electronics&apos;, slug: &apos;electronics&apos; },
        primary_image_url: &apos;smartphone.jpg&apos;,
        is_featured: true,
      },
      {
        id: &apos;2&apos;,
        name: &apos;Smart TV 55&quot;&apos;,
        slug: &apos;smart-tv-55&apos;,
        price: 899.99,
        discount_price: 699.99,
        effective_price: 699.99,
        discount_percentage: 22.22,
        brand: &apos;Samsung&apos;,
        category: { name: &apos;Electronics&apos;, slug: &apos;electronics&apos; },
        primary_image_url: &apos;tv.jpg&apos;,
        is_featured: false,
      },
    ],
    page: 1,
    page_size: 20,
    num_pages: 3,
    facets: {},
    query: &apos;smart&apos;,
    filters: {},
    sort_by: &apos;relevance&apos;,
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);
    (apiClient.get as jest.Mock).mockResolvedValue({
      success: true,
      data: mockSearchResults,
    });
  });

  test(&apos;renders the search results correctly&apos;, async () => {
    // Mock search query
    mockSearchParams.get.mockImplementation((param) => {
      if (param === &apos;search&apos;) return &apos;smart&apos;;
      return null;
    });
    
    render(<SearchResults initialQuery="smart" />);
    
    // Wait for search results to load
    await waitFor(() => {
      expect(screen.getByText(&apos;Search results for &quot;smart&quot;&apos;)).toBeInTheDocument();
    });
    
    // Check if product count is displayed
    expect(screen.getByText(&apos;42 products found&apos;)).toBeInTheDocument();
    
    // Check if sort options are displayed
    expect(screen.getByLabelText(&apos;Sort by:&apos;)).toBeInTheDocument();
    
    // Check if products are displayed
    expect(screen.getByTestId(&apos;product-grid&apos;)).toBeInTheDocument();
    expect(screen.getByTestId(&apos;product-1&apos;)).toBeInTheDocument();
    expect(screen.getByTestId(&apos;product-2&apos;)).toBeInTheDocument();
    
    // Check if pagination is displayed
    expect(screen.getByTestId(&apos;pagination&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Page 1 of 3&apos;)).toBeInTheDocument();
  });

  test(&apos;displays &quot;All Products&quot; when no search query is provided&apos;, async () => {
    mockSearchParams.get.mockReturnValue(null);
    
    render(<SearchResults />);
    
    // Wait for search results to load
    await waitFor(() => {
      expect(screen.getByText(&apos;All Products&apos;)).toBeInTheDocument();
    });
  });

  test(&apos;handles sort change&apos;, async () => {
    mockSearchParams.get.mockImplementation((param) => {
      if (param === &apos;search&apos;) return &apos;smart&apos;;
      return null;
    });
    
    render(<SearchResults initialQuery="smart" />);
    
    // Wait for search results to load
    await waitFor(() => {
      expect(screen.getByLabelText(&apos;Sort by:&apos;)).toBeInTheDocument();
    });
    
    // Change sort option
    const sortSelect = screen.getByLabelText(&apos;Sort by:&apos;);
    fireEvent.change(sortSelect, { target: { value: &apos;price_asc&apos; } });
    
    // Check if router was called with correct URL
    expect(mockRouter.push).toHaveBeenCalledWith(&apos;/products?sort_by=price_asc&apos;);
  });

  test(&apos;handles page change&apos;, async () => {
    mockSearchParams.get.mockImplementation((param) => {
      if (param === &apos;search&apos;) return &apos;smart&apos;;
      return null;
    });
    
    render(<SearchResults initialQuery="smart" />);
    
    // Wait for search results to load
    await waitFor(() => {
      expect(screen.getByTestId(&apos;pagination&apos;)).toBeInTheDocument();
    });
    
    // Click next page button
    const nextButton = screen.getByText(&apos;Next&apos;);
    fireEvent.click(nextButton);
    
    // Check if router was called with correct URL
    expect(mockRouter.push).toHaveBeenCalledWith(&apos;/products?page=2&apos;);
  });

  test(&apos;displays loading state&apos;, async () => {
    // Delay API response to show loading state
    (apiClient.get as jest.Mock).mockImplementation(() => {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            success: true,
            data: mockSearchResults,
          });
        }, 100);
      });
    });
    
    render(<SearchResults />);
    
    // Check if loading state is displayed
    expect(screen.getByText(&apos;Loading...&apos;)).toBeInTheDocument();
  });

  test(&apos;displays error message when API fails&apos;, async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({
      success: false,
      error: {
        message: &apos;Failed to load search results&apos;
      }
    });
    
    render(<SearchResults />);
    
    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText(&apos;Failed to load search results&apos;)).toBeInTheDocument();
    });
  });

  test(&apos;displays empty state when no results found&apos;, async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({
      success: true,
      data: {
        ...mockSearchResults,
        count: 0,
        results: [],
      },
    });
    
    mockSearchParams.get.mockImplementation((param) => {
      if (param === &apos;search&apos;) return &apos;nonexistent&apos;;
      return null;
    });
    
    render(<SearchResults initialQuery="nonexistent" />);
    
    // Wait for empty state to appear
    await waitFor(() => {
      expect(screen.getByText('No products found')).toBeInTheDocument();
      expect(screen.getByText(/We couldn't find any products matching "nonexistent"/)).toBeInTheDocument();
    });
  });
});