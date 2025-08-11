import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Pagination } from '../Pagination';

describe('Pagination', () => {
  const mockPagination = {
    count: 100,
    next: 'http://example.com/page/2',
    previous: null,
    page_size: 20,
    total_pages: 5,
    current_page: 1,
  };

  it('renders pagination correctly', () => {
    const handlePageChange = jest.fn();
    render(
      <Pagination 
        pagination={mockPagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Check if page numbers are rendered
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('highlights current page', () => {
    const handlePageChange = jest.fn();
    render(
      <Pagination 
        pagination={mockPagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Check if current page has the correct styling
    const currentPage = screen.getByText('1').closest('button');
    expect(currentPage).toHaveClass('bg-blue-600');
    expect(currentPage).toHaveClass('text-white');
  });

  it('calls onPageChange when a page number is clicked', () => {
    const handlePageChange = jest.fn();
    render(
      <Pagination 
        pagination={mockPagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Click on page 2
    fireEvent.click(screen.getByText('2'));
    
    // Check if onPageChange was called with the correct page number
    expect(handlePageChange).toHaveBeenCalledWith(2);
  });

  it('disables previous button on first page', () => {
    const handlePageChange = jest.fn();
    render(
      <Pagination 
        pagination={mockPagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Find previous button
    const prevButton = screen.getByLabelText('Previous page');
    
    // Check if it's disabled
    expect(prevButton).toBeDisabled();
    expect(prevButton).toHaveClass('text-gray-400');
    expect(prevButton).toHaveClass('cursor-not-allowed');
  });

  it('enables previous button when not on first page', () => {
    const handlePageChange = jest.fn();
    const pagination = { ...mockPagination, current_page: 2, previous: 'http://example.com/page/1' };
    
    render(
      <Pagination 
        pagination={pagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Find previous button
    const prevButton = screen.getByLabelText('Previous page');
    
    // Check if it's enabled
    expect(prevButton).not.toBeDisabled();
    expect(prevButton).not.toHaveClass('text-gray-400');
    expect(prevButton).not.toHaveClass('cursor-not-allowed');
    
    // Click previous button
    fireEvent.click(prevButton);
    
    // Check if onPageChange was called with the correct page number
    expect(handlePageChange).toHaveBeenCalledWith(1);
  });

  it('disables next button on last page', () => {
    const handlePageChange = jest.fn();
    const pagination = { ...mockPagination, current_page: 5, next: null };
    
    render(
      <Pagination 
        pagination={pagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Find next button
    const nextButton = screen.getByLabelText('Next page');
    
    // Check if it's disabled
    expect(nextButton).toBeDisabled();
    expect(nextButton).toHaveClass('text-gray-400');
    expect(nextButton).toHaveClass('cursor-not-allowed');
  });

  it('enables next button when not on last page', () => {
    const handlePageChange = jest.fn();
    
    render(
      <Pagination 
        pagination={mockPagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Find next button
    const nextButton = screen.getByLabelText('Next page');
    
    // Check if it's enabled
    expect(nextButton).not.toBeDisabled();
    expect(nextButton).not.toHaveClass('text-gray-400');
    expect(nextButton).not.toHaveClass('cursor-not-allowed');
    
    // Click next button
    fireEvent.click(nextButton);
    
    // Check if onPageChange was called with the correct page number
    expect(handlePageChange).toHaveBeenCalledWith(2);
  });

  it('does not render pagination when there is only one page', () => {
    const handlePageChange = jest.fn();
    const pagination = { ...mockPagination, count: 10, total_pages: 1 };
    
    const { container } = render(
      <Pagination 
        pagination={pagination} 
        onPageChange={handlePageChange} 
      />
    );

    // Check if pagination is not rendered
    expect(container.firstChild).toBeNull();
  });
});