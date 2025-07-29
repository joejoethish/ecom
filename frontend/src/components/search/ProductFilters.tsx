'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/utils/api';
import { API_ENDPOINTS } from '@/constants';

interface FilterOption {
  name: string;
  count: number;
}

interface PriceRange {
  from: number | null;
  to: number | null;
  count: number;
  label: string;
}

interface FilterOptions {
  categories?: FilterOption[];
  brands?: FilterOption[];
  tags?: FilterOption[];
  price_ranges?: PriceRange[];
  discount_ranges?: {
    from: number | null;
    to: number | null;
    count: number;
    label: string;
  }[];
}

interface ProductFiltersProps {
  /** Additional CSS classes to apply to the component */
  className?: string;
  /** Callback when filters change */
  onFilterChange?: (filters: Record<string, any>) => void;
  /** Initial filters */
  initialFilters?: Record<string, any>;
}

/**
 * ProductFilters component for filtering search results
 * 
 * Provides filter options for categories, brands, price ranges, and more
 */
export function ProductFilters({
  className = '',
  onFilterChange,
  initialFilters = {},
}: ProductFiltersProps) {
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({});
  const [selectedFilters, setSelectedFilters] = useState<Record<string, any>>(initialFilters);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [priceRange, setPriceRange] = useState<[number | null, number | null]>([null, null]);
  const router = useRouter();
  const searchParams = useSearchParams();

  // Fetch filter options on component mount
  useEffect(() => {
    fetchFilterOptions();
  }, []);

  // Update selected filters from URL params on mount
  useEffect(() => {
    const filters: Record<string, any> = {};
    
    // Extract category filter
    const category = searchParams.get('category');
    if (category) {
      filters.category = category;
    }
    
    // Extract brand filter
    const brand = searchParams.get('brand');
    if (brand) {
      filters.brand = brand;
    }
    
    // Extract price range filter
    const minPrice = searchParams.get('min_price');
    const maxPrice = searchParams.get('max_price');
    if (minPrice || maxPrice) {
      setPriceRange([
        minPrice ? parseFloat(minPrice) : null,
        maxPrice ? parseFloat(maxPrice) : null
      ]);
      filters.price_range = [
        minPrice ? parseFloat(minPrice) : null,
        maxPrice ? parseFloat(maxPrice) : null
      ];
    }
    
    // Extract discount only filter
    const discountOnly = searchParams.get('discount_only');
    if (discountOnly === 'true') {
      filters.discount_only = true;
    }
    
    // Extract featured filter
    const featured = searchParams.get('is_featured');
    if (featured === 'true') {
      filters.is_featured = true;
    }
    
    setSelectedFilters(filters);
  }, [searchParams]);

  // Fetch available filter options from the API
  const fetchFilterOptions = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.get(API_ENDPOINTS.SEARCH.FILTERS);
      
      if (response.success && response.data) {
        setFilterOptions(response.data);
      } else if (response.error) {
        setError(response.error.message);
      }
    } catch (error) {
      console.error('Error fetching filter options:', error);
      setError('Failed to load filter options. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle category filter change
  const handleCategoryChange = (category: string) => {
    const newFilters = { ...selectedFilters };
    
    if (newFilters.category === category) {
      delete newFilters.category;
    } else {
      newFilters.category = category;
    }
    
    updateFilters(newFilters);
  };

  // Handle brand filter change
  const handleBrandChange = (brand: string) => {
    const newFilters = { ...selectedFilters };
    
    if (newFilters.brand === brand) {
      delete newFilters.brand;
    } else {
      newFilters.brand = brand;
    }
    
    updateFilters(newFilters);
  };

  // Handle price range filter change
  const handlePriceRangeChange = (range: [number | null, number | null]) => {
    setPriceRange(range);
    
    const newFilters = { ...selectedFilters };
    newFilters.price_range = range;
    
    updateFilters(newFilters);
  };

  // Handle discount only filter change
  const handleDiscountOnlyChange = (checked: boolean) => {
    const newFilters = { ...selectedFilters };
    
    if (checked) {
      newFilters.discount_only = true;
    } else {
      delete newFilters.discount_only;
    }
    
    updateFilters(newFilters);
  };

  // Handle featured filter change
  const handleFeaturedChange = (checked: boolean) => {
    const newFilters = { ...selectedFilters };
    
    if (checked) {
      newFilters.is_featured = true;
    } else {
      delete newFilters.is_featured;
    }
    
    updateFilters(newFilters);
  };

  // Update filters and notify parent component
  const updateFilters = (newFilters: Record<string, any>) => {
    setSelectedFilters(newFilters);
    
    if (onFilterChange) {
      onFilterChange(newFilters);
    } else {
      // Build query string from filters
      if (typeof window !== 'undefined') {
        const params = new URLSearchParams(window.location.search);
      
      // Update category parameter
      if (newFilters.category) {
        params.set('category', newFilters.category);
      } else {
        params.delete('category');
      }
      
      // Update brand parameter
      if (newFilters.brand) {
        params.set('brand', newFilters.brand);
      } else {
        params.delete('brand');
      }
      
      // Update price range parameters
      if (newFilters.price_range) {
        const [min, max] = newFilters.price_range;
        if (min !== null) {
          params.set('min_price', min.toString());
        } else {
          params.delete('min_price');
        }
        
        if (max !== null) {
          params.set('max_price', max.toString());
        } else {
          params.delete('max_price');
        }
      } else {
        params.delete('min_price');
        params.delete('max_price');
      }
      
      // Update discount only parameter
      if (newFilters.discount_only) {
        params.set('discount_only', 'true');
      } else {
        params.delete('discount_only');
      }
      
      // Update featured parameter
      if (newFilters.is_featured) {
        params.set('is_featured', 'true');
      } else {
        params.delete('is_featured');
      }
      
      // Preserve search query if it exists
      const searchQuery = searchParams.get('search');
      if (searchQuery) {
        params.set('search', searchQuery);
      }
      
        // Update URL with new filters
        const queryString = params.toString();
        router.push(`/products${queryString ? `?${queryString}` : ''}`);
      }
    }
  };

  // Clear all filters
  const clearAllFilters = () => {
    setSelectedFilters({});
    setPriceRange([null, null]);
    
    if (onFilterChange) {
      onFilterChange({});
    } else {
      // Preserve only the search query if it exists
      const searchQuery = searchParams.get('search');
      if (searchQuery) {
        router.push(`/products?search=${encodeURIComponent(searchQuery)}`);
      } else {
        router.push('/products');
      }
    }
  };

  // Check if any filters are applied
  const hasActiveFilters = Object.keys(selectedFilters).length > 0;

  return (
    <div className={`bg-white rounded-lg shadow p-4 ${className}`}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Filters</h2>
        {hasActiveFilters && (
          <button
            onClick={clearAllFilters}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Clear All
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="py-4 text-center">
          <div className="inline-block animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-blue-500 mr-2"></div>
          <span className="text-gray-500">Loading filters...</span>
        </div>
      ) : error ? (
        <div className="py-4 text-center text-red-500">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 inline-block mr-1" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          {error}
        </div>
      ) : (
        <>
          {/* Categories filter */}
          {filterOptions.categories && filterOptions.categories.length > 0 && (
            <div className="mb-6">
              <h3 className="font-medium mb-2">Categories</h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {filterOptions.categories.map((category) => (
                  <div key={category.name} className="flex items-center">
                    <input
                      type="checkbox"
                      id={`category-${category.name}`}
                      checked={selectedFilters.category === category.name}
                      onChange={() => handleCategoryChange(category.name)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor={`category-${category.name}`} className="ml-2 text-sm text-gray-700">
                      {category.name} <span className="text-gray-500">({category.count})</span>
                    </label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Brands filter */}
          {filterOptions.brands && filterOptions.brands.length > 0 && (
            <div className="mb-6">
              <h3 className="font-medium mb-2">Brands</h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {filterOptions.brands.map((brand) => (
                  <div key={brand.name} className="flex items-center">
                    <input
                      type="checkbox"
                      id={`brand-${brand.name}`}
                      checked={selectedFilters.brand === brand.name}
                      onChange={() => handleBrandChange(brand.name)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor={`brand-${brand.name}`} className="ml-2 text-sm text-gray-700">
                      {brand.name} <span className="text-gray-500">({brand.count})</span>
                    </label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Price range filter */}
          {filterOptions.price_ranges && filterOptions.price_ranges.length > 0 && (
            <div className="mb-6">
              <h3 className="font-medium mb-2">Price Range</h3>
              <div className="space-y-2">
                {filterOptions.price_ranges.map((range, index) => (
                  <div key={index} className="flex items-center">
                    <input
                      type="radio"
                      id={`price-range-${index}`}
                      name="price-range"
                      checked={
                        priceRange[0] === range.from && 
                        priceRange[1] === range.to
                      }
                      onChange={() => handlePriceRangeChange([range.from, range.to])}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                    <label htmlFor={`price-range-${index}`} className="ml-2 text-sm text-gray-700">
                      {range.label} <span className="text-gray-500">({range.count})</span>
                    </label>
                  </div>
                ))}
                
                {/* Custom price range */}
                <div className="mt-3 flex items-center space-x-2">
                  <input
                    type="number"
                    placeholder="Min"
                    value={priceRange[0] !== null ? priceRange[0] : ''}
                    onChange={(e) => {
                      const value = e.target.value ? parseFloat(e.target.value) : null;
                      handlePriceRangeChange([value, priceRange[1]]);
                    }}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                    min="0"
                  />
                  <span className="text-gray-500">to</span>
                  <input
                    type="number"
                    placeholder="Max"
                    value={priceRange[1] !== null ? priceRange[1] : ''}
                    onChange={(e) => {
                      const value = e.target.value ? parseFloat(e.target.value) : null;
                      handlePriceRangeChange([priceRange[0], value]);
                    }}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                    min="0"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Additional filters */}
          <div className="mb-6">
            <h3 className="font-medium mb-2">Additional Filters</h3>
            <div className="space-y-2">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="discount-only"
                  checked={!!selectedFilters.discount_only}
                  onChange={(e) => handleDiscountOnlyChange(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="discount-only" className="ml-2 text-sm text-gray-700">
                  Discounted Items Only
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="featured-only"
                  checked={!!selectedFilters.is_featured}
                  onChange={(e) => handleFeaturedChange(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="featured-only" className="ml-2 text-sm text-gray-700">
                  Featured Items Only
                </label>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}