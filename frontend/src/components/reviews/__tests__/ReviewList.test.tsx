import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReviewList from '../ReviewList';
import { Review } from '../../../types';

interface MockReviewCardProps {
  review: Review;
  onVoteHelpful?: (reviewId: string, vote: 'helpful' | 'not_helpful') => Promise<void>;
  onReport?: (reviewId: string) => void;
}

// Mock the ReviewCard component
jest.mock(&apos;../ReviewCard&apos;, () => {
  return function MockReviewCard({ review, onVoteHelpful, onReport }: MockReviewCardProps) {
    return (
      <div data-testid={`review-card-${review.id}`}>
        <h3>{review.title}</h3>
        <p>{review.comment}</p>
        {onVoteHelpful && (
          <button onClick={() => onVoteHelpful(review.id, &apos;helpful&apos;)}>
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

describe(&apos;ReviewList&apos;, () => {
    {
      id: &apos;review-1&apos;,
      user: {
        id: &apos;user-1&apos;,
        username: &apos;user1&apos;,
        full_name: &apos;User One&apos;,
        avatar_url: &apos;&apos;,
      },
      product: {
        id: &apos;product-1&apos;,
        name: &apos;Product 1&apos;,
        slug: &apos;product-1&apos;,
      },
      rating: 5,
      title: &apos;Excellent product&apos;,
      comment: &apos;Really great quality&apos;,
      is_verified_purchase: true,
      status: &apos;approved&apos;,
      helpful_count: 10,
      not_helpful_count: 1,
      helpfulness_score: 90.9,
      images: [],
      can_moderate: false,
      created_at: &apos;2024-01-01T00:00:00Z&apos;,
    },
    {
      id: &apos;review-2&apos;,
      user: {
        id: &apos;user-2&apos;,
        username: &apos;user2&apos;,
        full_name: &apos;User Two&apos;,
        avatar_url: &apos;&apos;,
      },
      product: {
        id: &apos;product-1&apos;,
        name: &apos;Product 1&apos;,
        slug: &apos;product-1&apos;,
      },
      rating: 3,
      title: &apos;Average product&apos;,
      comment: &apos;It was okay&apos;,
      is_verified_purchase: false,
      status: &apos;approved&apos;,
      helpful_count: 2,
      not_helpful_count: 3,
      helpfulness_score: 40.0,
      images: [],
      can_moderate: false,
      created_at: &apos;2024-01-02T00:00:00Z&apos;,
    },
  ];

  const defaultProps = {
    reviews: mockReviews,
    totalCount: 2,
  };

  it(&apos;renders reviews correctly&apos;, () => {
    render(<ReviewList {...defaultProps} />);
    
    expect(screen.getByText(&apos;Reviews (2)&apos;)).toBeInTheDocument();
    expect(screen.getByTestId(&apos;review-card-review-1&apos;)).toBeInTheDocument();
    expect(screen.getByTestId(&apos;review-card-review-2&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Excellent product&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Average product&apos;)).toBeInTheDocument();
  });

  it(&apos;shows loading state&apos;, () => {
    render(<ReviewList {...defaultProps} loading />);
    
    // Should show skeleton loaders
    const skeletons = screen.getAllByRole(&apos;generic&apos;);
    expect(skeletons.some(el => el.classList.contains(&apos;animate-pulse&apos;))).toBe(true);
  });

  it(&apos;shows error state&apos;, () => {
    const errorMessage = &apos;Failed to load reviews&apos;;
    render(<ReviewList {...defaultProps} error={errorMessage} />);
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it(&apos;shows empty state when no reviews&apos;, () => {
    render(<ReviewList {...defaultProps} reviews={[]} totalCount={0} />);
    
    expect(screen.getByText(&apos;No reviews yet&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;No reviews match your current filters.&apos;)).toBeInTheDocument();
  });

  it(&apos;shows empty state with product-specific message&apos;, () => {
    render(
      <ReviewList 
        {...defaultProps} 
        reviews={[]} 
        totalCount={0} 
        productId="product-123"
      />
    );
    
    expect(screen.getByText(&apos;Be the first to review this product!&apos;)).toBeInTheDocument();
  });

  it(&apos;renders filter panel when showFilters is true&apos;, async () => {
    const user = userEvent.setup();
    render(<ReviewList {...defaultProps} showFilters />);
    
    const filtersButton = screen.getByText(&apos;Filters&apos;);
    await user.click(filtersButton);
    
    expect(screen.getByText(&apos;Rating&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Purchase Status&apos;)).toBeInTheDocument();
  });

  it(&apos;handles sort option changes&apos;, async () => {
    const mockOnFiltersChange = jest.fn();
    const user = userEvent.setup();
    
    render(
      <ReviewList 
        {...defaultProps} 
        onFiltersChange={mockOnFiltersChange}
        showFilters
      />
    );
    
    const sortSelect = screen.getByDisplayValue(&apos;Most Helpful&apos;);
    await user.selectOptions(sortSelect, &apos;Newest First&apos;);
    
    expect(mockOnFiltersChange).toHaveBeenCalledWith({
      ordering: &apos;-created_at&apos;,
    });
  });

  it(&apos;handles rating filter changes&apos;, async () => {
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
    const filtersButton = screen.getByText(&apos;Filters&apos;);
    await user.click(filtersButton);
    
    // Change rating filter
    const ratingSelect = screen.getByDisplayValue(&apos;All Ratings&apos;);
    await user.selectOptions(ratingSelect, &apos;5 Stars&apos;);
    
    expect(mockOnFiltersChange).toHaveBeenCalledWith({
      rating: 5,
    });
  });

  it(&apos;handles verified purchase filter&apos;, async () => {
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
    const filtersButton = screen.getByText(&apos;Filters&apos;);
    await user.click(filtersButton);
    
    // Toggle verified purchase filter
    const verifiedCheckbox = screen.getByLabelText(/verified purchases only/i);
    await user.click(verifiedCheckbox);
    
    expect(mockOnFiltersChange).toHaveBeenCalledWith({
      verified_only: true,
    });
  });

  it(&apos;shows active filter count&apos;, async () => {
    render(
      <ReviewList 
        {...defaultProps} 
        filters={{ rating: 5, verified_only: true }}
        showFilters
      />
    );
    
    expect(screen.getByText(&apos;2&apos;)).toBeInTheDocument(); // Active filter count badge
  });

  it(&apos;clears all filters&apos;, async () => {
    const mockOnFiltersChange = jest.fn();
    
    render(
      <ReviewList 
        {...defaultProps} 
        filters={{ rating: 5, verified_only: true }}
        onFiltersChange={mockOnFiltersChange}
        showFilters
      />
    );
    
    // Open filter panel
    const filtersButton = screen.getByText(&apos;Filters&apos;);
    await user.click(filtersButton);
    
    // Clear filters
    const clearButton = screen.getByText(&apos;Clear all filters&apos;);
    await user.click(clearButton);
    
    expect(mockOnFiltersChange).toHaveBeenCalledWith({
      ordering: &apos;-helpful_count&apos;,
    });
  });

  it(&apos;shows moderation status filter for admin users&apos;, async () => {
    const user = userEvent.setup();
    render(
      <ReviewList 
        {...defaultProps} 
        showModerationActions
        showFilters
      />
    );
    
    // Open filter panel
    const filtersButton = screen.getByText(&apos;Filters&apos;);
    await user.click(filtersButton);
    
    expect(screen.getByText(&apos;Status&apos;)).toBeInTheDocument();
    expect(screen.getByDisplayValue(&apos;Approved&apos;)).toBeInTheDocument();
  });

  it(&apos;passes callbacks to ReviewCard components&apos;, () => {
    const mockOnVoteHelpful = jest.fn();
    const mockOnReport = jest.fn();
    
    render(
      <ReviewList 
        {...defaultProps} 
        onVoteHelpful={mockOnVoteHelpful}
        onReport={mockOnReport}
      />
    );
    
    const voteButtons = screen.getAllByText(&apos;Vote Helpful&apos;);
    const reportButtons = screen.getAllByText(&apos;Report&apos;);
    
    expect(voteButtons).toHaveLength(2);
    expect(reportButtons).toHaveLength(2);
  });

  it(&apos;handles review actions correctly&apos;, async () => {
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
    const voteButton = screen.getAllByText(&apos;Vote Helpful&apos;)[0];
    await user.click(voteButton);
    expect(mockOnVoteHelpful).toHaveBeenCalledWith(&apos;review-1&apos;, &apos;helpful&apos;);
    
    // Test report
    const reportButton = screen.getAllByText(&apos;Report&apos;)[0];
    await user.click(reportButton);
    expect(mockOnReport).toHaveBeenCalledWith(&apos;review-1&apos;);
  });

  it(&apos;shows clear filters option in empty state&apos;, async () => {
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