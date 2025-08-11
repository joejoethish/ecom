import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Pagination } from '../Pagination';

describe('Pagination', () => {
  const mockPagination = {
    count: 100,
    next: &apos;http://example.com/page/2&apos;,
    previous: null,
    page_size: 20,
    total_pages: 5,
    current_page: 1,
  };

  it(&apos;renders pagination correctly&apos;, () => {
    const handlePageChange = jest.fn();
    render(
      <Pagination 
        pagination={mockPagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Check if page numbers are rendered
    expect(screen.getByText(&apos;1&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;2&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;3&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;4&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;5&apos;)).toBeInTheDocument();
  });

  it(&apos;highlights current page&apos;, () => {
    const handlePageChange = jest.fn();
    render(
      <Pagination 
        pagination={mockPagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Check if current page has the correct styling
    const currentPage = screen.getByText(&apos;1&apos;).closest(&apos;button&apos;);
    expect(currentPage).toHaveClass(&apos;bg-blue-600&apos;);
    expect(currentPage).toHaveClass(&apos;text-white&apos;);
  });

  it(&apos;calls onPageChange when a page number is clicked&apos;, () => {
    const handlePageChange = jest.fn();
    render(
      <Pagination 
        pagination={mockPagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Click on page 2
    fireEvent.click(screen.getByText(&apos;2&apos;));
    
    // Check if onPageChange was called with the correct page number
    expect(handlePageChange).toHaveBeenCalledWith(2);
  });

  it(&apos;disables previous button on first page&apos;, () => {
    const handlePageChange = jest.fn();
    render(
      <Pagination 
        pagination={mockPagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Find previous button
    const prevButton = screen.getByLabelText(&apos;Previous page&apos;);
    
    // Check if it&apos;s disabled
    expect(prevButton).toBeDisabled();
    expect(prevButton).toHaveClass(&apos;text-gray-400&apos;);
    expect(prevButton).toHaveClass(&apos;cursor-not-allowed&apos;);
  });

  it(&apos;enables previous button when not on first page&apos;, () => {
    const handlePageChange = jest.fn();
    const pagination = { ...mockPagination, current_page: 2, previous: &apos;http://example.com/page/1&apos; };
    
    render(
      <Pagination 
        pagination={pagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Find previous button
    const prevButton = screen.getByLabelText(&apos;Previous page&apos;);
    
    // Check if it&apos;s enabled
    expect(prevButton).not.toBeDisabled();
    expect(prevButton).not.toHaveClass(&apos;text-gray-400&apos;);
    expect(prevButton).not.toHaveClass(&apos;cursor-not-allowed&apos;);
    
    // Click previous button
    fireEvent.click(prevButton);
    
    // Check if onPageChange was called with the correct page number
    expect(handlePageChange).toHaveBeenCalledWith(1);
  });

  it(&apos;disables next button on last page&apos;, () => {
    const handlePageChange = jest.fn();
    const pagination = { ...mockPagination, current_page: 5, next: null };
    
    render(
      <Pagination 
        pagination={pagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Find next button
    const nextButton = screen.getByLabelText(&apos;Next page&apos;);
    
    // Check if it&apos;s disabled
    expect(nextButton).toBeDisabled();
    expect(nextButton).toHaveClass(&apos;text-gray-400&apos;);
    expect(nextButton).toHaveClass(&apos;cursor-not-allowed&apos;);
  });

  it(&apos;enables next button when not on last page&apos;, () => {
    const handlePageChange = jest.fn();
    
    render(
      <Pagination 
        pagination={mockPagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Find next button
    const nextButton = screen.getByLabelText(&apos;Next page&apos;);
    
    // Check if it&apos;s enabled
    expect(nextButton).not.toBeDisabled();
    expect(nextButton).not.toHaveClass(&apos;text-gray-400&apos;);
    expect(nextButton).not.toHaveClass(&apos;cursor-not-allowed&apos;);
    
    // Click next button
    fireEvent.click(nextButton);
    
    // Check if onPageChange was called with the correct page number
    expect(handlePageChange).toHaveBeenCalledWith(2);
  });

  it(&apos;does not render pagination when there is only one page&apos;, () => {
    const handlePageChange = jest.fn();
    const pagination = { ...mockPagination, count: 10, total_pages: 1 };
    
      <Pagination 
        pagination={pagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Check if pagination is not rendered
    expect(container.firstChild).toBeNull();
  });
});