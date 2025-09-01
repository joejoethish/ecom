'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useDebounce } from '@/hooks/useDebounce';
import { apiClient } from '@/utils/api';
import { API_ENDPOINTS } from '@/constants';

/**
 * Interface for search suggestion items
 */
interface SearchSuggestion {
  id: string;
  type: 'product' | 'category';
  name: string;
  image?: string;
  url: string;
}

/**
 * Interface for product suggestions from API
 */
interface ProductSuggestion {
  id: string;
  name: string;
  slug: string;
  price: number;
  image: string | null;
  category: string | null;
}

/**
 * Interface for API response
 */
interface SuggestionsResponse {
  suggestions: string[];
  products: ProductSuggestion[];
  query: string;
  error?: string;
}

/**
 * Props for SearchAutocomplete component
 */
interface SearchAutocompleteProps {
  onSelect: (suggestion: SearchSuggestion) => void;
  placeholder?: string;
  className?: string;
  autoFocus?: boolean;
  initialValue?: string;
}

/**
 * SearchAutocomplete component with debounced search and dropdown UI
 */
export function SearchAutocomplete({
  onSelect,
  placeholder = "Search products and categories...",
  className = "",
  autoFocus = false,
  initialValue = ""
}: SearchAutocompleteProps) {
  const [query, setQuery] = useState(initialValue);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  
  const debouncedQuery = useDebounce(query, 300);
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Debounced search function
  const debouncedSearch = useCallback(async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        q: searchQuery,
        limit: '5'
      });

      const response = await apiClient.get(
        `${API_ENDPOINTS.SEARCH.SUGGESTIONS}?${params.toString()}`
      );

      if (response.success && response.data) {
        const data = response.data as SuggestionsResponse;
        const allSuggestions: SearchSuggestion[] = [];

        // Add text suggestions
        data.suggestions.forEach(suggestion => {
          allSuggestions.push({
            id: `text-${suggestion}`,
            type: 'category',
            name: suggestion,
            url: `/products?search=${encodeURIComponent(suggestion)}`
          });
        });

        // Add product suggestions
        data.products.forEach(product => {
          allSuggestions.push({
            id: product.id,
            type: 'product',
            name: product.name,
            image: product.image || undefined,
            url: `/products/${product.slug}`
          });
        });

        setSuggestions(allSuggestions);
        setIsOpen(allSuggestions.length > 0);
        setSelectedIndex(-1);
      } else if (response.error) {
        setError(response.error.message || 'Failed to fetch suggestions');
        setSuggestions([]);
        setIsOpen(false);
      }
    } catch (error) {
      console.error('Error fetching search suggestions:', error);
      setError('Failed to fetch suggestions. Please try again.');
      setSuggestions([]);
      setIsOpen(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Effect for debounced search
  useEffect(() => {
    debouncedSearch(debouncedQuery);
  }, [debouncedQuery, debouncedSearch]);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSelectedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (!isOpen || suggestions.length === 0) {
      if (event.key === 'Enter') {
        event.preventDefault();
        handleSearch();
      }
      return;
    }

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        setSelectedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        event.preventDefault();
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;
      case 'Enter':
        event.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          handleSuggestionSelect(suggestions[selectedIndex]);
        } else {
          handleSearch();
        }
        break;
      case 'Escape':
        event.preventDefault();
        setIsOpen(false);
        setSelectedIndex(-1);
        inputRef.current?.blur();
        break;
      case 'Tab':
        setIsOpen(false);
        setSelectedIndex(-1);
        break;
    }
  };

  // Handle suggestion selection
  const handleSuggestionSelect = (suggestion: SearchSuggestion) => {
    setQuery(suggestion.name);
    setIsOpen(false);
    setSelectedIndex(-1);
    onSelect(suggestion);
  };

  // Handle search submission
  const handleSearch = () => {
    if (query.trim()) {
      const searchSuggestion: SearchSuggestion = {
        id: `search-${query}`,
        type: 'category',
        name: query,
        url: `/products?search=${encodeURIComponent(query)}`
      };
      onSelect(searchSuggestion);
    }
  };

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    if (value.length >= 2) {
      setIsOpen(true);
    } else {
      setIsOpen(false);
      setSuggestions([]);
    }
  };

  // Handle input focus
  const handleInputFocus = () => {
    if (query.length >= 2 && suggestions.length > 0) {
      setIsOpen(true);
    }
  };

  // Scroll selected item into view
  useEffect(() => {
    if (selectedIndex >= 0 && listRef.current) {
      const selectedElement = listRef.current.children[selectedIndex] as HTMLElement;
      if (selectedElement) {
        selectedElement.scrollIntoView({
          block: 'nearest',
          behavior: 'smooth'
        });
      }
    }
  }, [selectedIndex]);

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className="w-full px-4 py-2 pl-4 pr-12 text-gray-900 bg-white border-0 rounded-sm focus:outline-none focus:ring-2 focus:ring-yellow-400"
          aria-label="Search"
          aria-expanded={isOpen}
          aria-autocomplete="list"
          aria-activedescendant={selectedIndex >= 0 ? `suggestion-${selectedIndex}` : undefined}
          role="combobox"
        />
        
        <button
          type="button"
          onClick={handleSearch}
          className="absolute right-0 top-0 h-full px-4 bg-yellow-400 hover:bg-yellow-500 rounded-r-sm focus:outline-none focus:ring-2 focus:ring-yellow-600"
          aria-label="Search"
        >
          <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>
      </div>

      {/* Dropdown suggestions */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-96 overflow-y-auto">
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
          ) : suggestions.length === 0 ? (
            <div className="p-4 text-center text-gray-500">No suggestions found</div>
          ) : (
            <ul ref={listRef} role="listbox" className="py-1">
              {suggestions.map((suggestion, index) => (
                <li
                  key={suggestion.id}
                  id={`suggestion-${index}`}
                  role="option"
                  aria-selected={index === selectedIndex}
                  className={`px-4 py-2 cursor-pointer flex items-center hover:bg-gray-100 ${
                    index === selectedIndex ? 'bg-blue-50 text-blue-900' : 'text-gray-900'
                  }`}
                  onClick={() => handleSuggestionSelect(suggestion)}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  {suggestion.type === 'product' && suggestion.image ? (
                    <div className="h-10 w-10 relative mr-3 flex-shrink-0">
                      <img
                        src={suggestion.image}
                        alt={suggestion.name}
                        className="h-full w-full object-cover rounded"
                        loading="lazy"
                      />
                    </div>
                  ) : (
                    <div className="h-10 w-10 bg-gray-200 mr-3 flex-shrink-0 rounded flex items-center justify-center">
                      {suggestion.type === 'product' ? (
                        <svg className="h-5 w-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                        </svg>
                      ) : (
                        <svg className="h-5 w-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                      )}
                    </div>
                  )}
                  
                  <div className="flex-grow min-w-0">
                    <div className="font-medium truncate">
                      <span 
                        dangerouslySetInnerHTML={{ 
                          __html: suggestion.name.replace(
                            new RegExp(`(${query})`, 'gi'), 
                            '<span class="font-semibold text-blue-600">$1</span>'
                          ) 
                        }} 
                      />
                    </div>
                    {suggestion.type === 'product' && (
                      <div className="text-sm text-gray-500">
                        Product
                      </div>
                    )}
                  </div>
                  
                  <div className="ml-2 text-gray-400">
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}