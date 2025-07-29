'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { SearchBar } from '@/components/search/SearchBar';
import { ProductFilters } from '@/components/search/ProductFilters';
import { SearchResults } from '@/components/search/SearchResults';

/**
 * Search page component that combines search bar, filters, and results
 */
function SearchPageContent() {
  const searchParams = useSearchParams();
  const query = searchParams.get('search') || '';
  
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Search bar */}
      <div className="mb-8">
        <SearchBar 
          initialValue={query}
          autoFocus={!query}
          className="max-w-3xl mx-auto"
        />
      </div>
      
      <div className="flex flex-col md:flex-row gap-6">
        {/* Filters sidebar */}
        <div className="w-full md:w-64 flex-shrink-0">
          <Suspense fallback={<div>Loading filters...</div>}>
            <ProductFilters />
          </Suspense>
        </div>
        
        {/* Search results */}
        <div className="flex-grow">
          <Suspense fallback={<div>Loading results...</div>}>
            <SearchResults initialQuery={query} />
          </Suspense>
        </div>
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <SearchPageContent />
    </Suspense>
  );
}