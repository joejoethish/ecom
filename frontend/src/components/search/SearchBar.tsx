'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useDebounce } from '@/hooks/useDebounce';
import { apiClient } from '@/utils/api';
import { API_ENDPOINTS } from '@/constants';

/**
 * Interface for product suggestion items returned from the search API
 */
interface SearchSuggestion {
  id: string;
  name: string;
  slug: string;
  price: number;
  image: string | null;
  category: string | null;
}

/**
 * Props for the SearchBar component
 */
interface SearchBarProps {
  /** Placeholder text for the search input */
  placeholder?: string;
  /** Additional CSS classes to apply to the component */
  className?: string;
  /** Optional callback function when search is submitted */
  onSearch?: (query: string) => void;
  /** Whether to autofocus the search input */
  autoFocus?: boolean;
  /** Initial value for the search input */
  initialValue?: string;
  /** Optional category context for filtering suggestions */
  categoryContext?: string;
  /** Optional brand context for filtering suggestions */
  brandContext?: string;
  /** Maximum number of suggestions to show */
  maxSuggestions?: number;
}

/**
 * SearchBar component with autocomplete suggestions
 * 
 * Provides real-time search suggestions as the user types, including
 * both text suggestions and product previews.
 */
export function SearchBar({
  placeholder = 'Search for products...',
  className = '',
  onSearch,
  autoFocus = false,
  initialValue = '',
  categoryContext,
  brandContext,
  maxSuggestions = 5,
}: SearchBarProps) {
  const [query, setQuery] = useState(initialValue);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [productSuggestions, setProductSuggestions] = useState<SearchSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debouncedQuery = useDebounce(query, 300);
  const router = useRouter();
  const searchRef = useRef<HTMLDivElement>(null);

  // Fetch suggestions when query changes
  useEffect(() => {
    if (debouncedQuery.length < 2) {
      setSuggestions([]);
      setProductSuggestions([]);
      setError(null);
      return;
    }

    const fetchSuggestions = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Build the query parameters
        const params = new URLSearchParams({
          q: debouncedQuery,
          limit: maxSuggestions.toString()
        });
        
        // Add optional context parameters if provided
        if (categoryContext) {
          params.append('category', categoryContext);
        }
        
        if (brandContext) {
          params.append('brand', brandContext);
        }
        
        const response = await apiClient.get(
          `${API_ENDPOINTS.SEARCH.SUGGESTIONS}?${params.toString()}`
        );
        
        if (response.success && response.data) {
          setSuggestions(response.data.suggestions || []);
          setProductSuggestions(response.data.products || []);
        } else if (response.error) {
          setError(response.error.message);
          setSuggestions([]);
          setProductSuggestions([]);
        }
      } catch (error) {
        console.error('Error fetching search suggestions:', error);
        setError('Failed to fetch suggestions. Please try again.');
        setSuggestions([]);
        setProductSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSuggestions();
  }, [debouncedQuery, categoryContext, brandContext, maxSuggestions]);

  // Handle click outside to close suggestions
  useEffect(() => {
    if (typeof document === 'undefined') return;
    
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Handle search submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      if (onSearch) {
        onSearch(query);
      } else {
        router.push(`/products?search=${encodeURIComponent(query)}`);
      }
      setShowSuggestions(false);
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    if (onSearch) {
      onSearch(suggestion);
    } else {
      router.push(`/products?search=${encodeURIComponent(suggestion)}`);
    }
    setShowSuggestions(false);
  };

  // Handle product click
  const handleProductClick = (product: SearchSuggestion) => {
    router.push(`/products/${product.slug}`);
    setShowSuggestions(false);
  };

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    // TODO: Implement keyboard navigation for accessibility
    // This would allow users to navigate suggestions with arrow keys
    if (event.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  // Clear search input
  const handleClearSearch = () => {
    setQuery('');
    setSuggestions([]);
    setProductSuggestions([]);
    setError(null);
  };

  return (
    <div className={`relative ${className}`} ref={searchRef}>
      <form onSubmit={handleSubmit} className="w-full">
        <div className="relative">
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            autoFocus={autoFocus}
            className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            aria-label="Search"
            aria-expanded={showSuggestions}
            aria-autocomplete="list"
            role="combobox"
          />
          
          {query && (
            <button
              type="button"
              onClick={handleClearSearch}
              className="absolute right-10 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              aria-label="Clear search"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
          
          <button
            type="submit"
            className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
            aria-label="Search"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>
      </form>

      {/* Suggestions dropdown */}
      {showSuggestions && (query.length >= 2) && (
        <div 
          className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-96 overflow-y-auto"
          role="listbox"
        >
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">
              <div className="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-blue-500 mr-2"></div>
              Loading suggestions...
            </div>
          ) : error ? (
            <div className="p-4 text-center text-red-500">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 inline-block mr-1" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          ) : (
            <>
              {suggestions.length === 0 && productSuggestions.length === 0 ? (
                <div className="p-4 text-center text-gray-500">No suggestions found</div>
              ) : (
                <>
                  {suggestions.length > 0 && (
                    <div className="p-2">
                      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2 mb-1">
                        Suggestions
                      </h3>
                      <ul>
                        {suggestions.map((suggestion, index) => (
                          <li key={index} role="option">
                            <button
                              className="w-full text-left px-4 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                              onClick={() => handleSuggestionClick(suggestion)}
                            >
                              <div className="flex items-center">
                                <svg
                                  xmlns="http://www.w3.org/2000/svg"
                                  className="h-4 w-4 mr-2 text-gray-500"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                  stroke="currentColor"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                                  />
                                </svg>
                                <span 
                                  dangerouslySetInnerHTML={{ 
                                    __html: suggestion.replace(
                                      new RegExp(`(${query})`, 'gi'), 
                                      '<span class="font-semibold text-blue-600">$1</span>'
                                    ) 
                                  }} 
                                />
                              </div>
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {productSuggestions.length > 0 && (
                    <div className={`p-2 ${suggestions.length > 0 ? 'border-t border-gray-200' : ''}`}>
                      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2 mb-1">
                        Products
                      </h3>
                      <ul>
                        {productSuggestions.map((product) => (
                          <li key={product.id} role="option">
                            <button
                              className="w-full text-left px-4 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                              onClick={() => handleProductClick(product)}
                            >
                              <div className="flex items-center">
                                {product.image ? (
                                  <div className="h-12 w-12 relative mr-3 flex-shrink-0">
                                    <img
                                      src={product.image}
                                      alt={product.name}
                                      className="h-full w-full object-cover rounded"
                                      loading="lazy"
                                    />
                                  </div>
                                ) : (
                                  <div className="h-12 w-12 bg-gray-200 mr-3 flex-shrink-0 rounded flex items-center justify-center">
                                    <span className="text-gray-500 text-xs">No image</span>
                                  </div>
                                )}
                                <div className="flex-grow min-w-0">
                                  <div className="font-medium truncate">
                                    <span 
                                      dangerouslySetInnerHTML={{ 
                                        __html: product.name.replace(
                                          new RegExp(`(${query})`, 'gi'), 
                                          '<span class="font-semibold text-blue-600">$1</span>'
                                        ) 
                                      }} 
                                    />
                                  </div>
                                  <div className="text-sm text-gray-500 flex items-center">
                                    <span className="font-medium">${product.price.toFixed(2)}</span>
                                    {product.category && (
                                      <>
                                        <span className="mx-1">•</span>
                                        <span className="truncate">{product.category}</span>
                                      </>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}