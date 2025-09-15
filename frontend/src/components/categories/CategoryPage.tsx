'use client';

import React, { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Category, CategoryFilters } from '@/services/categoriesApi';
import { Product } from '@/services/productsApi';
import { ProductGrid } from '@/components/products/ProductGrid';
import { CategoryFilters as CategoryFiltersComponent } from '@/components/categories/CategoryFilters';
import { CategoryBreadcrumb } from '@/components/categories/CategoryBreadcrumb';
import { CategorySort } from '@/components/categories/CategorySort';
import { Pagination } from '@/components/ui/Pagination';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface CategoryPageProps {
  category: Category & {
    top_brands: Array<{
      name: string;
      count: number;
    }>;
  };
  products: {
    data: Product[];
    total_count: number;
    page: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
  filters: CategoryFilters | null;
  currentPage: number;
  searchParams: {
    page?: string;
    sort?: string;
    brand?: string;
    price_min?: string;
    price_max?: string;
  };
}

export function CategoryPage({
  category,
  products,
  filters,
  currentPage,
  searchParams,
}: CategoryPageProps) {
  const router = useRouter();
  const [showFilters, setShowFilters] = useState(false);
  
  const handleFilterChange = (newFilters: Record<string, string | undefined>) => {
    const params = new URLSearchParams();
    
    // Preserve existing params and add new ones
    Object.entries({ ...searchParams, ...newFilters }).forEach(([key, value]) => {
      if (value && value !== 'undefined') {
        params.set(key, value);
      }
    });
    
    // Remove page when filters change
    if (Object.keys(newFilters).some(key => key !== 'page')) {
      params.delete('page');
    }
    
    const queryString = params.toString();
    const newUrl = `/categories/${category.slug}${queryString ? `?${queryString}` : ''}`;
    
    router.push(newUrl);
  };
  
  const handleSortChange = (sort: string) => {
    handleFilterChange({ sort });
  };
  
  const handlePageChange = (page: number) => {
    handleFilterChange({ page: page.toString() });
  };
  
  const clearFilters = () => {
    router.push(`/categories/${category.slug}`);
  };
  
  const hasActiveFilters = Boolean(
    searchParams.brand || 
    searchParams.price_min || 
    searchParams.price_max
  );
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Breadcrumb */}
      <CategoryBreadcrumb category={category} />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Category Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{category.name}</h1>
              {category.description && (
                <p className="mt-2 text-gray-600">{category.description}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                {products.total_count} products found
              </p>
            </div>
            
            {/* Mobile filter toggle */}
            <div className="lg:hidden">
              <Button
                variant="outline"
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center space-x-2"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z" />
                </svg>
                <span>Filters</span>
              </Button>
            </div>
          </div>
          
          {/* Top Brands */}
          {category.top_brands && category.top_brands.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Popular Brands</h3>
              <div className="flex flex-wrap gap-2">
                {category.top_brands.slice(0, 8).map((brand) => (
                  <Button
                    key={brand.name}
                    variant="outline"
                    size="sm"
                    onClick={() => handleFilterChange({ brand: brand.name })}
                    className={`text-xs ${
                      searchParams.brand === brand.name
                        ? 'bg-blue-50 border-blue-200 text-blue-700'
                        : ''
                    }`}
                  >
                    {brand.name} ({brand.count})
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Filters Sidebar */}
          <div className={`lg:w-64 ${showFilters ? 'block' : 'hidden lg:block'}`}>
            <div className="sticky top-4">
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">Filters</CardTitle>
                    {hasActiveFilters && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={clearFilters}
                        className="text-blue-600 hover:text-blue-700"
                      >
                        Clear All
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {filters && (
                    <CategoryFiltersComponent
                      filters={filters}
                      activeFilters={searchParams}
                      onFilterChange={handleFilterChange}
                    />
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
          
          {/* Main Content */}
          <div className="flex-1">
            {/* Sort and View Options */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-4">
                <CategorySort
                  currentSort={searchParams.sort || 'name'}
                  onSortChange={handleSortChange}
                />
                
                {hasActiveFilters && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">Active filters:</span>
                    {searchParams.brand && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        Brand: {searchParams.brand}
                        <button
                          onClick={() => handleFilterChange({ brand: undefined })}
                          className="ml-1 text-blue-600 hover:text-blue-800"
                        >
                          ×
                        </button>
                      </span>
                    )}
                    {(searchParams.price_min || searchParams.price_max) && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        Price: ${searchParams.price_min || '0'} - ${searchParams.price_max || '∞'}
                        <button
                          onClick={() => handleFilterChange({ price_min: undefined, price_max: undefined })}
                          className="ml-1 text-blue-600 hover:text-blue-800"
                        >
                          ×
                        </button>
                      </span>
                    )}
                  </div>
                )}
              </div>
              
              <div className="text-sm text-gray-500">
                Page {currentPage} of {products.total_pages}
              </div>
            </div>
            
            {/* Products Grid */}
            {products.data.length > 0 ? (
              <>
                <ProductGrid products={products.data} />
                
                {/* Pagination */}
                {products.total_pages > 1 && (
                  <div className="mt-8 flex justify-center">
                    <Pagination
                      currentPage={currentPage}
                      totalPages={products.total_pages}
                      onPageChange={handlePageChange}
                      hasNext={products.has_next}
                      hasPrevious={products.has_previous}
                    />
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12">
                <div className="text-gray-400 mb-4">
                  <svg className="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m0 0V9a1 1 0 011-1h1m-1 1v4h1m0-4h1" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No products found</h3>
                <p className="text-gray-500 mb-4">
                  Try adjusting your filters or search criteria.
                </p>
                {hasActiveFilters && (
                  <Button onClick={clearFilters}>
                    Clear Filters
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}