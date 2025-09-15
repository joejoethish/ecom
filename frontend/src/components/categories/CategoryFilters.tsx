'use client';

import React, { useState } from 'react';
import { CategoryFilters as CategoryFiltersType } from '@/services/categoriesApi';
import { Button } from '@/components/ui/Button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface CategoryFiltersProps {
  filters: CategoryFiltersType;
  activeFilters: {
    brand?: string;
    price_min?: string;
    price_max?: string;
  };
  onFilterChange: (filters: Record<string, string | undefined>) => void;
}

export function CategoryFilters({ filters, activeFilters, onFilterChange }: CategoryFiltersProps) {
  const [priceMin, setPriceMin] = useState(activeFilters.price_min || '');
  const [priceMax, setPriceMax] = useState(activeFilters.price_max || '');
  const [expandedSections, setExpandedSections] = useState({
    brands: true,
    price: true,
  });
  
  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };
  
  const handleBrandChange = (brandName: string, checked: boolean) => {
    if (checked) {
      onFilterChange({ brand: brandName });
    } else {
      onFilterChange({ brand: undefined });
    }
  };
  
  const handlePriceRangeClick = (range: { from: number | null; to: number | null }) => {
    onFilterChange({
      price_min: range.from?.toString(),
      price_max: range.to?.toString(),
    });
    setPriceMin(range.from?.toString() || '');
    setPriceMax(range.to?.toString() || '');
  };
  
  const handleCustomPriceApply = () => {
    onFilterChange({
      price_min: priceMin || undefined,
      price_max: priceMax || undefined,
    });
  };
  
  const clearPriceFilter = () => {
    setPriceMin('');
    setPriceMax('');
    onFilterChange({
      price_min: undefined,
      price_max: undefined,
    });
  };
  
  return (
    <div className="space-y-6">
      {/* Brands Filter */}
      {filters.brands && filters.brands.length > 0 && (
        <div>
          <button
            onClick={() => toggleSection('brands')}
            className="flex items-center justify-between w-full text-left"
          >
            <h3 className="text-sm font-medium text-gray-900">Brand</h3>
            <svg
              className={`h-4 w-4 transition-transform ${
                expandedSections.brands ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {expandedSections.brands && (
            <div className="mt-3 space-y-2 max-h-48 overflow-y-auto">
              {filters.brands.map((brand) => (
                <div key={brand.name} className="flex items-center">
                  <Checkbox
                    id={`brand-${brand.name}`}
                    checked={activeFilters.brand === brand.name}
                    onCheckedChange={(checked) => 
                      handleBrandChange(brand.name, checked as boolean)
                    }
                  />
                  <Label
                    htmlFor={`brand-${brand.name}`}
                    className="ml-2 text-sm text-gray-700 cursor-pointer flex-1"
                  >
                    {brand.name} ({brand.count})
                  </Label>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      {/* Price Filter */}
      <div>
        <button
          onClick={() => toggleSection('price')}
          className="flex items-center justify-between w-full text-left"
        >
          <h3 className="text-sm font-medium text-gray-900">Price</h3>
          <svg
            className={`h-4 w-4 transition-transform ${
              expandedSections.price ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        
        {expandedSections.price && (
          <div className="mt-3 space-y-3">
            {/* Predefined Price Ranges */}
            {filters.price_ranges && filters.price_ranges.length > 0 && (
              <div className="space-y-2">
                {filters.price_ranges
                  .filter(range => range.count > 0)
                  .map((range, index) => (
                    <button
                      key={index}
                      onClick={() => handlePriceRangeClick(range)}
                      className={`block w-full text-left text-sm py-1 px-2 rounded hover:bg-gray-50 ${
                        activeFilters.price_min === range.from?.toString() &&
                        activeFilters.price_max === range.to?.toString()
                          ? 'bg-blue-50 text-blue-700'
                          : 'text-gray-700'
                      }`}
                    >
                      {range.label} ({range.count})
                    </button>
                  ))}
              </div>
            )}
            
            {/* Custom Price Range */}
            <div className="border-t pt-3">
              <Label className="text-xs text-gray-600 mb-2 block">Custom Range</Label>
              <div className="flex items-center space-x-2">
                <Input
                  type="number"
                  placeholder="Min"
                  value={priceMin}
                  onChange={(e) => setPriceMin(e.target.value)}
                  className="text-xs"
                />
                <span className="text-gray-400">-</span>
                <Input
                  type="number"
                  placeholder="Max"
                  value={priceMax}
                  onChange={(e) => setPriceMax(e.target.value)}
                  className="text-xs"
                />
              </div>
              <div className="flex space-x-2 mt-2">
                <Button
                  size="sm"
                  onClick={handleCustomPriceApply}
                  className="flex-1 text-xs"
                >
                  Apply
                </Button>
                {(activeFilters.price_min || activeFilters.price_max) && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={clearPriceFilter}
                    className="text-xs"
                  >
                    Clear
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}