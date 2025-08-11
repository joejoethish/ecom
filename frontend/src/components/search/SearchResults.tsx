'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/utils/api';
import { API_ENDPOINTS } from '@/constants';
import { ProductGrid } from '../products/ProductGrid';
import { Pagination } from '../products/Pagination';

interface SearchResultsProps {
  /** Additional CSS classes to apply to the component */
  className?: string;
  /** Initial search query */
  initialQuery?: string;
  /** Initial filters */
  initialFilters?: Record<string, any>;
}

/**
 * SearchResults component for displaying search results with sorting and pagination
 */
export function SearchResults({
  className = '',
  initialQuery = '',
  initialFilters = {},
}: SearchResultsProps) {
  const [products, setProducts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [sortBy, setSortBy] = useState<string>('relevance');
  const [query, setQuery] = useState(initialQuery);
  const [filters, setFilters] = useState(initialFilters);
  
  const router = useRouter();
  const searchParams = useSearchParams();

  // Update state from URL params on mount and when URL changes
  useEffect(() => {
    // Extract search query
    const searchQuery = searchParams.get('search') || '';
    setQuery(searchQuery);
    
    // Extract page number
    const page = searchParams.get('page');
    if (page) {
      setCurrentPage(parseInt(page, 10));
    } else {
      setCurrentPage(1);
    }
    
    // Extract sort option
    const sort = searchParams.get('sort_by');
    if (sort) {
      setSortBy(sort);
    } else {
      setSortBy(searchQuery ? 'relevance' : 'created_at');
    }
    
    // Extract filters
    const extractedFilters: Record<string, any> = {};
    
    // Extract category filter
    const category = searchParams.get('category');
    if (category) {
      extractedFilters.category = category;
    }
    
    // Extract brand filter
    const brand = searchParams.get('brand');
    if (brand) {
      extractedFilters.brand = brand;
    }
    
    // Extract price range filter
    const minPrice = searchParams.get('min_price');
    const maxPrice = searchParams.get('max_price');
    if (minPrice || maxPrice) {
      extractedFilters.price_range = [
        minPrice ? parseFloat(minPrice) : null,
        maxPrice ? parseFloat(maxPrice) : null
      ];
    }
    
    // Extract discount only filter
    const discountOnly = searchParams.get('discount_only');
    if (discountOnly === 'true') {
      extractedFilters.discount_only = true;
    }
    
    // Extract featured filter
    const featured = searchParams.get('is_featured');
    if (featured === 'true') {
      extractedFilters.is_featured = true;
    }
    
    setFilters(extractedFilters);
    
    // Fetch search results with the updated parameters
    fetchSearchResults(searchQuery, extractedFilters, sort || (searchQuery ? 'relevance' : 'created_at'), page ? parseInt(page, 10) : 1);
  }, [searchParams]);

  // Fetch search results from the API
  const fetchSearchResults = async (
    searchQuery: string,
    searchFilters: Record<string, any>,
    sortOption: string,
    page: number
  ) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Build query parameters
      const params = new URLSearchParams();
      
      // Add search query if provided
      if (searchQuery) {
        params.append('q', searchQuery);
      }
      
      // Add pagination parameters
      params.append('page', page.toString());
      params.append('page_size', pageSize.toString());
      
      // Add sorting parameter
      params.append('sort_by', sortOption);
      
      // Add filter parameters
      if (searchFilters.category) {
        params.append('category', searchFilters.category);
      }
      
      if (searchFilters.brand) {
        params.append('brand', searchFilters.brand);
      }
      
      if (searchFilters.price_range) {
        const [min, max] = searchFilters.price_range;
        if (min !== null) {
          params.append('min_price', min.toString());
        }
        if (max !== null) {
          params.append('max_price', max.toString());
        }
      }
      
      if (searchFilters.discount_only) {
        params.append('discount_only', 'true');
      }
      
      if (searchFilters.is_featured) {
        params.append('is_featured', 'true');
      }
      
      // Make API request
      const response = await apiClient.get(
        `${API_ENDPOINTS.SEARCH.PRODUCTS}?${params.toString()}`
      );
      
      if (response.success && response.data) {
        setProducts(response.data.results || []);
        setTotalCount(response.data.count || 0);
        setCurrentPage(response.data.page || 1);
        setTotalPages(response.data.num_pages || 1);
      } else if (response.error) {
        setError(response.error.message);
        setProducts([]);
        setTotalCount(0);
      }
    } catch (error) {
      console.error('Error fetching search results:', error);
      setError('Failed to load search results. Please try again.');
      setProducts([]);
      setTotalCount(0);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle sort change
  const handleSortChange = (newSortBy: string) => {
    setSortBy(newSortBy);
    
    // Update URL with new sort parameter
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      params.set('sort_by', newSortBy);
      
      // Reset to first page when sorting changes
      params.delete('page');
      
      router.push(`/products?${params.toString()}`);
    }
  };

  // Handle page change
  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    
    // Update URL with new page parameter
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      params.set('page', newPage.toString());
      
      router.push(`/products?${params.toString()}`);
    }
  };

  return (
    <div className={className}>
      {/* Results header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
        <div className="mb-4 sm:mb-0">
          <h2 className="text-xl font-semibold">
            {query ? `Search results for "${query}"` : 'All Products'}
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            {isLoading ? 'Loading...' : `${totalCount} products found`}
          </p>
        </div>
        
        {/* Sort options */}
        <div className="flex items-center">
          <label htmlFor="sort-by" className="text-sm text-gray-600 mr-2">
            Sort by:
          </label>
          <select
            id="sort-by"
            value={sortBy}
            onChange={(e) => handleSortChange(e.target.value)}
            className="text-sm border border-gray-300 rounded-md py-1 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          >
            {query && <option value="relevance">Relevance</option>}
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
            <option value="created_at">Newest First</option>
            <option value="-created_at">Oldest First</option>
            <option value="discount">Biggest Discount</option>
          </select>
        </div>
      </div>
      
      {/* Results content */}
      {isLoading ? (
        <div className="flex justify-center items-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mr-2"></div>
          <span className="text-gray-500">Loading search results...</span>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 text-center text-red-600">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 inline-block mr-1" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          {error}
        </div>
      ) : products.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-8 text-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-1">No products found</h3>
          <p className="text-gray-500">
            {query 
              ? `We couldn't find any products matching "${query}". Try using different keywords or filters.` 
              : 'No products match the selected filters. Try changing your filter options.'}
          </p>
        </div>
      ) : (
        <>
          {/* Product grid */}
          <ProductGrid products={products} />
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-8">
              <Pagination 
                pagination={{
                  current_page: currentPage,
                  total_pages: totalPages,
                  count: totalCount,
                  page_size: pageSize,
                  next: currentPage < totalPages ? `?page=${currentPage + 1}` : null,
                  previous: currentPage > 1 ? `?page=${currentPage - 1}` : null
                }}
                onPageChange={handlePageChange}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}