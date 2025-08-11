'use client';

import { PaginationInfo } from '@/types';

interface PaginationProps {
  pagination: PaginationInfo;
  onPageChange: (page: number) => void;
}

export function Pagination({ pagination, onPageChange }: PaginationProps) {
  const { current_page, total_pages } = pagination;
  
  // Generate page numbers to display
  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 5;
    
    // Always show first page
    pages.push(1);
    
    // Calculate range of pages to show around current page
    let startPage = Math.max(2, current_page - Math.floor(maxPagesToShow / 2));
    let endPage = Math.min(total_pages - 1, startPage + maxPagesToShow - 2);
    
    // Adjust if we're near the beginning
    if (startPage <= 2) {
      startPage = 2;
      endPage = Math.min(total_pages - 1, maxPagesToShow);
    }
    
    // Adjust if we're near the end
    if (endPage >= total_pages - 1) {
      endPage = total_pages - 1;
      startPage = Math.max(2, total_pages - maxPagesToShow + 1);
    }
    
    // Add ellipsis after first page if needed
    if (startPage > 2) {
      pages.push('ellipsis-start');
    }
    
    // Add middle pages
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    // Add ellipsis before last page if needed
    if (endPage < total_pages - 1) {
      pages.push('ellipsis-end');
    }
    
    // Always show last page if there is more than one page
    if (total_pages > 1) {
      pages.push(total_pages);
    }
    
    return pages;
  };

  if (total_pages <= 1) {
    return null;
  }

  return (
    <nav className="flex justify-center mt-8">
      <ul className="flex items-center space-x-1">
        {/* Previous Page Button */}
        <li>
          <button
            onClick={() => onPageChange(current_page - 1)}
            disabled={current_page === 1}
            className={`px-3 py-2 rounded-md text-sm ${
              current_page === 1
                ? 'text-gray-400 cursor-not-allowed'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
            aria-label="Previous page"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </li>
        
        {/* Page Numbers */}
        {getPageNumbers().map((page, index) => (
          <li key={`page-${page}-${index}`}>
            {page === 'ellipsis-start' || page === 'ellipsis-end' ? (
              <span className="px-3 py-2 text-gray-500">...</span>
            ) : (
              <button
                onClick={() => onPageChange(page as number)}
                className={`px-3 py-2 rounded-md text-sm ${
                  current_page === page
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                {page}
              </button>
            )}
          </li>
        ))}
        
        {/* Next Page Button */}
        <li>
          <button
            onClick={() => onPageChange(current_page + 1)}
            disabled={current_page === total_pages}
            className={`px-3 py-2 rounded-md text-sm ${
              current_page === total_pages
                ? 'text-gray-400 cursor-not-allowed'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
            aria-label="Next page"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </li>
      </ul>
    </nav>
  );
}