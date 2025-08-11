import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SearchResults } from '../SearchResults';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/utils/api';

// Mock the ProductGrid component
jest.mock('@/components/products/ProductGrid', () => ({
  ProductGrid: ({ products }: { products: any[] }) => (
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
jest.mock('@/components/products/Pagination', () => ({
  Pagination: ({ currentPage, totalPages, onPageChange }: { currentPage: number, totalPages: number, onPageChange: (page: number) => void }) => (
    <div data-testid="pagination">
      <span>Page {currentPage} of {totalPages}</span>
      <button onClick={() => onPageChange(currentPage + 1)}>Next</button>
    </div>
  ),
}));

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

describe('SearchResults Component', () => {
  const mockRouter = {
    push: jest.fn(),
  };
  
  const mockSearchParams = {
    get: jest.fn(),
    toString: jest.fn().mockReturnValue(''),
  };
  
  const mockSearchResults = {
    count: 42,
    results: [
      {
        id: '1',
        name: 'Smartphone X',
        slug: 'smartphone-x',
        price: 999.99,
        discount_price: null,
        effective_price: 999.99,
        discount_percentage: 0,
        brand: 'Apple',
        category: { name: 'Electronics', slug: 'electronics' },
        primary_image_url: 'smartphone.jpg',
        is_featured: true,
      },
      {
        id: '2',
        name: 'Smart TV 55"',
        slug: 'smart-tv-55',
        price: 899.99,
        discount_price: 699.99,
        effective_price: 699.99,
        discount_percentage: 22.22,
        brand: 'Samsung',
        category: { name: 'Electronics', slug: 'electronics' },
        primary_image_url: 'tv.jpg',
        is_featured: false,
      },
    ],
    page: 1,
    page_size: 20,
    num_pages: 3,
    facets: {},
    query: 'smart',
    filters: {},
    sort_by: 'relevance',
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

  test('renders the search results correctly', async () => {
    // Mock search query
    mockSearchParams.get.mockImplementation((param) => {
      if (param === 'search') return 'smart';
      return null;
    });
    
    render(<SearchResults initialQuery="smart" />);
    
    // Wait for search results to load
    await waitFor(() => {
      expect(screen.getByText('Search results for "smart"')).toBeInTheDocument();
    });
    
    // Check if product count is displayed
    expect(screen.getByText('42 products found')).toBeInTheDocument();
    
    // Check if sort options are displayed
    expect(screen.getByLabelText('Sort by:')).toBeInTheDocument();
    
    // Check if products are displayed
    expect(screen.getByTestId('product-grid')).toBeInTheDocument();
    expect(screen.getByTestId('product-1')).toBeInTheDocument();
    expect(screen.getByTestId('product-2')).toBeInTheDocument();
    
    // Check if pagination is displayed
    expect(screen.getByTestId('pagination')).toBeInTheDocument();
    expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
  });

  test('displays "All Products" when no search query is provided', async () => {
    mockSearchParams.get.mockReturnValue(null);
    
    render(<SearchResults />);
    
    // Wait for search results to load
    await waitFor(() => {
      expect(screen.getByText('All Products')).toBeInTheDocument();
    });
  });

  test('handles sort change', async () => {
    mockSearchParams.get.mockImplementation((param) => {
      if (param === 'search') return 'smart';
      return null;
    });
    
    render(<SearchResults initialQuery="smart" />);
    
    // Wait for search results to load
    await waitFor(() => {
      expect(screen.getByLabelText('Sort by:')).toBeInTheDocument();
    });
    
    // Change sort option
    const sortSelect = screen.getByLabelText('Sort by:');
    fireEvent.change(sortSelect, { target: { value: 'price_asc' } });
    
    // Check if router was called with correct URL
    expect(mockRouter.push).toHaveBeenCalledWith('/products?sort_by=price_asc');
  });

  test('handles page change', async () => {
    mockSearchParams.get.mockImplementation((param) => {
      if (param === 'search') return 'smart';
      return null;
    });
    
    render(<SearchResults initialQuery="smart" />);
    
    // Wait for search results to load
    await waitFor(() => {
      expect(screen.getByTestId('pagination')).toBeInTheDocument();
    });
    
    // Click next page button
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);
    
    // Check if router was called with correct URL
    expect(mockRouter.push).toHaveBeenCalledWith('/products?page=2');
  });

  test('displays loading state', async () => {
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
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('displays error message when API fails', async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({
      success: false,
      error: {
        message: 'Failed to load search results'
      }
    });
    
    render(<SearchResults />);
    
    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText('Failed to load search results')).toBeInTheDocument();
    });
  });

  test('displays empty state when no results found', async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({
      success: true,
      data: {
        ...mockSearchResults,
        count: 0,
        results: [],
      },
    });
    
    mockSearchParams.get.mockImplementation((param) => {
      if (param === 'search') return 'nonexistent';
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