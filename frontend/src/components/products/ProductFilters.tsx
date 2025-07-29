'use client';

import { useState, useEffect } from 'react';
import { formatCurrency } from '@/utils/format';

interface FilterOption {
  label: string;
  value: string;
  count?: number;
}

interface PriceRange {
  min: number;
  max: number;
}

interface ProductFiltersProps {
  brands: FilterOption[];
  priceRange: PriceRange;
  onFilterChange: (filters: Record<string, any>) => void;
  initialFilters?: Record<string, any>;
}

export function ProductFilters({
  brands,
  priceRange,
  onFilterChange,
  initialFilters = {}
}: ProductFiltersProps) {
  const [filters, setFilters] = useState({
    min_price: initialFilters.min_price || '',
    max_price: initialFilters.max_price || '',
    brand: initialFilters.brand || [],
    has_discount: initialFilters.has_discount || false,
    sort: initialFilters.sort || '',
  });

  // Update filters when initialFilters change
  useEffect(() => {
    setFilters(prev => ({
      ...prev,
      ...initialFilters
    }));
  }, [initialFilters]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target as HTMLInputElement;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFilters(prev => ({
        ...prev,
        [name]: checked
      }));
    } else {
      setFilters(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleBrandChange = (brand: string) => {
    setFilters(prev => {
      const currentBrands = Array.isArray(prev.brand) ? prev.brand : [];
      const updatedBrands = currentBrands.includes(brand)
        ? currentBrands.filter(b => b !== brand)
        : [...currentBrands, brand];
      
      return {
        ...prev,
        brand: updatedBrands
      };
    });
  };

  const handleApplyFilters = () => {
    // Convert empty strings to undefined to avoid sending empty parameters
    const cleanedFilters = Object.entries(filters).reduce((acc, [key, value]) => {
      if (value === '' || (Array.isArray(value) && value.length === 0)) {
        return acc;
      }
      
      // Convert array of brands to comma-separated string
      if (key === 'brand' && Array.isArray(value) && value.length > 0) {
        acc[key] = value.join(',');
      } else {
        acc[key] = value;
      }
      
      return acc;
    }, {} as Record<string, any>);
    
    onFilterChange(cleanedFilters);
  };

  const handleResetFilters = () => {
    setFilters({
      min_price: '',
      max_price: '',
      brand: [],
      has_discount: false,
      sort: '',
    });
    onFilterChange({});
  };

  return (
    <div className="p-4 border rounded-lg bg-white">
      <h3 className="font-medium text-gray-900 mb-4">Filters</h3>
      
      {/* Price Range */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Price Range</h4>
        <div className="flex items-center space-x-2">
          <input
            type="number"
            name="min_price"
            value={filters.min_price}
            onChange={handleInputChange}
            placeholder={`Min ${formatCurrency(priceRange.min)}`}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <span className="text-gray-500">-</span>
          <input
            type="number"
            name="max_price"
            value={filters.max_price}
            onChange={handleInputChange}
            placeholder={`Max ${formatCurrency(priceRange.max)}`}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
      </div>
      
      {/* Brands */}
      {brands.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Brands</h4>
          <div className="max-h-48 overflow-y-auto">
            {brands.map(brand => (
              <div key={brand.value} className="flex items-center mb-1">
                <input
                  type="checkbox"
                  id={`brand-${brand.value}`}
                  checked={Array.isArray(filters.brand) && filters.brand.includes(brand.value)}
                  onChange={() => handleBrandChange(brand.value)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor={`brand-${brand.value}`} className="ml-2 text-sm text-gray-700">
                  {brand.label} {brand.count && <span className="text-gray-500">({brand.count})</span>}
                </label>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Discount Filter */}
      <div className="mb-4">
        <div className="flex items-center">
          <input
            type="checkbox"
            id="has-discount"
            name="has_discount"
            checked={filters.has_discount}
            onChange={handleInputChange}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="has-discount" className="ml-2 text-sm text-gray-700">
            On Sale
          </label>
        </div>
      </div>
      
      {/* Sort By */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Sort By</h4>
        <select
          name="sort"
          value={filters.sort}
          onChange={handleInputChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">Relevance</option>
          <option value="price">Price: Low to High</option>
          <option value="-price">Price: High to Low</option>
          <option value="-created_at">Newest First</option>
          <option value="name">Name: A to Z</option>
          <option value="-name">Name: Z to A</option>
        </select>
      </div>
      
      {/* Action Buttons */}
      <div className="flex space-x-2">
        <button
          onClick={handleApplyFilters}
          className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md text-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Apply Filters
        </button>
        <button
          onClick={handleResetFilters}
          className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-md text-sm hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400"
        >
          Reset
        </button>
      </div>
    </div>
  );
}