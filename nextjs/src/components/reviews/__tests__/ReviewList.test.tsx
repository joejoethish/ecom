import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReviewList from '../ReviewList';
import { Review } from '../../../types';

// Mock the ReviewCard component
jest.mock('../ReviewCard', () => {
  return function MockReviewCard({ review, onVoteHelpful, onReport }: any) {
    return (
      <div data-testid={`review-card-${review.id}`}>
        <h3>{review.title}</h3>
        <p>{review.comment}</p>
        {onVoteHelpful && (
          <button onClick={() => onVoteHelpful(review.id, 'helpful')}>
            Vote Helpful
          </button>
        )}
        {onReport && (
          <button onClick={() => onReport(review.id)}>
            Report
          </button>
        )}
      </div>
    );
  };
});

describe('ReviewList', () => {
  const mockReviews: Review[] = [
    {
      id: 'review-1',
      user: {
        id: 'user-1',
        username: 'user1',
        full_name: 'User One',
        avatar_url: '',
      },
      product: {
        id: 'product-1',
        name: 'Product 1',
        slug: 'product-1',
      },
      rating: 5,
      title: 'Excellent product',
      comment: 'Really great quality',
      is_verified_purchase: true,
      status: 'approved',
      helpful_count: 10,
      not_helpful_count: 1,
      helpfulness_score: 90.9,
      images: [],
      can_moderate: false,
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'review-2',
      user: {
        id: 'user-2',
        username: 'user2',
        full_name: 'User Two',
        avatar_url: '',
      },
      product: {
        id: 'product-1',
        name: 'Product 1',
        slug: 'product-1',
      },
      rating: 3,
      title: 'Average product',
      comment: 'It was okay',
      is_verified_purchase: false,
      status: 'approved',
      helpful_count: 2,
      not_helpful_count: 3,
      helpfulness_score: 40.0,
      images: [],
      can_moderate: false,
      created_at: '2024-01-02T00:00:00Z',
    },
  ];

  const defaultProps = {
    reviews: mockReviews,
    totalCount: 2,
  };

  it('renders reviews correctly', () => {
    render(<ReviewList {...defaultProps} />);
    
    expect(screen.getByText('Reviews (2)')).toBeInTheDocument();
    expect(screen.getByTestId('review-card-review-1')).toBeInTheDocument();
    expect(screen.getByTestId('review-card-review-2')).toBeInTheDocument();
    expect(screen.getByText('Excellent product')).toBeInTheDocument();
    expect(screen.getByText('Average product')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<ReviewList {...defaultProps} loading />);
    
    // Should show skeleton loaders
    const skeletons = screen.getAllByRole('generic');
    expect(skeletons.some(el => el.classList.contains('animate-pulse'))).toBe(true);
  });

  it('shows error state', () => {
    const errorMessage = 'Failed to load reviews';
    render(<ReviewList {...defaultProps} error={errorMessage} />);
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('shows empty state when no reviews', () => {
    render(<ReviewList {...defaultProps} reviews={[]} totalCount={0} />);
    
    expect(screen.getByText('No reviews yet')).toBeInTheDocument();
    expect(screen.getByText('No reviews match your current filters.')).toBeInTheDocument();
  });

  it('shows empty state with product-specific message', () => {
    render(
      <ReviewList 
        {...defaultProps} 
        reviews={[]} 
        totalCount={0} 
        productId="product-123"
      />
    );
    
    expect(screen.getByText('Be the first to review this product!')).toBeInTheDocument();
  });

  it('renders filter panel when showFilters is true', async () => {
    const user = userEvent.setup();
    render(<ReviewList {...defaultProps} showFilters />);
    
    const filtersButton = screen.getByText('Filters');
    await user.click(filtersButton);
    
    expect(screen.getByText('Rating')).toBeInTheDocument();
    expect(screen.getByText('Purchase Status')).toBeInTheDocument();
  });

  it('handles sort option changes', async () => {
    const mockOnFiltersChange = jest.fn();
    const user = userEvent.setup();
    
    render(
      <ReviewList 
        {...defaultProps} 
        onFiltersChange={mockOnFiltersChange}
        showFilters
      />
    );
    
    const sortSelect = screen.getByDisplayValue('Most Helpful');
    await user.selectOptions(sortSelect, 'Newest First');
    
    expect(mockOnFiltersChange).toHaveBeenCalledWith({
      ordering: '-created_at',
    });
  });

  it('handles rating filter changes', async () => {
    const mockOnFiltersChange = jest.fn();
    const user = userEvent.setup();
    
    render(
      <ReviewList 
        {...defaultProps} 
        onFiltersChange={mockOnFiltersChange}
        showFilters
      />
    );
    
    // Open filter panel
    const filtersButton = screen.getByText('Filters');
    await user.click(filtersButton);
    
    // Change rating filter
    const ratingSelect = screen.getByDisplayValue('All Ratings');
    await user.selectOptions(ratingSelect, '5 Stars');
    
    expect(mockOnFiltersChange).toHaveBeenCalledWith({
      rating: 5,
    });
  });

  it('handles verified purchase filter', async () => {
    const mockOnFiltersChange = jest.fn();
    const user = userEvent.setup();
    
    render(
      <ReviewList 
        {...defaultProps} 
        onFiltersChange={mockOnFiltersChange}
        showFilters
      />
    );
    
    // Open filter panel
    const filtersButton = screen.getByText('Filters');
    await user.click(filtersButton);
    
    // Toggle verified purchase filter
    const verifiedCheckbox = screen.getByLabelText(/verified purchases only/i);
    await user.click(verifiedCheckbox);
    
    expect(mockOnFiltersChange).toHaveBeenCalledWith({
      verified_only: true,
    });
  });

  it('shows active filter count', async () => {
    const user = userEvent.setup();
    render(
      <ReviewList 
        {...defaultProps} 
        filters={{ rating: 5, verified_only: true }}
        showFilters
      />
    );
    
    const filtersButton = screen.getByText('Filters');
    expect(screen.getByText('2')).toBeInTheDocument(); // Active filter count badge
  });

  it('clears all filters', async () => {
    const mockOnFiltersChange = jest.fn();
    const user = userEvent.setup();
    
    render(
      <ReviewList 
        {...defaultProps} 
        filters={{ rating: 5, verified_only: true }}
        onFiltersChange={mockOnFiltersChange}
        showFilters
      />
    );
    
    // Open filter panel
    const filtersButton = screen.getByText('Filters');
    await user.click(filtersButton);
    
    // Clear filters
    const clearButton = screen.getByText('Clear all filters');
    await user.click(clearButton);
    
    expect(mockOnFiltersChange).toHaveBeenCalledWith({
      ordering: '-helpful_count',
    });
  });

  it('shows moderation status filter for admin users', async () => {
    const user = userEvent.setup();
    render(
      <ReviewList 
        {...defaultProps} 
        showModerationActions
        showFilters
      />
    );
    
    // Open filter panel
    const filtersButton = screen.getByText('Filters');
    await user.click(filtersButton);
    
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Approved')).toBeInTheDocument();
  });

  it('passes callbacks to ReviewCard components', () => {
    const mockOnVoteHelpful = jest.fn();
    const mockOnReport = jest.fn();
    
    render(
      <ReviewList 
        {...defaultProps} 
        onVoteHelpful={mockOnVoteHelpful}
        onReport={mockOnReport}
      />
    );
    
    const voteButtons = screen.getAllByText('Vote Helpful');
    const reportButtons = screen.getAllByText('Report');
    
    expect(voteButtons).toHaveLength(2);
    expect(reportButtons).toHaveLength(2);
  });

  it('handles review actions correctly', async () => {
    const mockOnVoteHelpful = jest.fn();
    const mockOnReport = jest.fn();
    const user = userEvent.setup();
    
    render(
      <ReviewList 
        {...defaultProps} 
        onVoteHelpful={mockOnVoteHelpful}
        onReport={mockOnReport}
      />
    );
    
    // Test vote helpful
    const voteButton = screen.getAllByText('Vote Helpful')[0];
    await user.click(voteButton);
    expect(mockOnVoteHelpful).toHaveBeenCalledWith('review-1', 'helpful');
    
    // Test report
    const reportButton = screen.getAllByText('Report')[0];
    await user.click(reportButton);
    expect(mockOnReport).toHaveBeenCalledWith('review-1');
  });

  it('shows clear filters option in empty state', async () => {
    const mockOnFiltersChange = jest.fn();
    const user = userEvent.setup();
    
    render(
      <ReviewList 
        {...defaultProps} 
        reviews={[]} 
        totalCount={0}
        filters={{ rating: 5 }}
        onFiltersChange={mockOnFiltersChange}
      />
    );
    
    const clearButton = screen.getByText('Clear filters to see all reviews');
    await user.click(clearButton);
    
    expect(mockOnFiltersChange).toHaveBeenCalledWith({
      ordering: '-helpful_count',
    });
  });
});