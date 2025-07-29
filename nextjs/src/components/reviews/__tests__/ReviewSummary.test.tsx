import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReviewSummary from '../ReviewSummary';
import { ProductReviewSummary } from '../../../types';

// Mock the StarRating component
jest.mock('../../ui/StarRating', () => {
  return function MockStarRating({ rating }: any) {
    return <div data-testid="star-rating">Rating: {rating}</div>;
  };
});

describe('ReviewSummary', () => {
  const mockSummary: ProductReviewSummary = {
    product_id: 'product-123',
    total_reviews: 100,
    average_rating: 4.2,
    rating_distribution: {
      5: 40,
      4: 30,
      3: 20,
      2: 7,
      1: 3,
    },
    recent_reviews: [],
    verified_purchase_percentage: 85.5,
  };

  const defaultProps = {
    summary: mockSummary,
  };

  it('renders summary information correctly', () => {
    render(<ReviewSummary {...defaultProps} />);

    expect(screen.getByText('Customer Reviews')).toBeInTheDocument();
    expect(screen.getByText('4.2')).toBeInTheDocument();
    expect(screen.getByText('Based on 100 reviews')).toBeInTheDocument();
    expect(screen.getByText('86% Verified Purchases')).toBeInTheDocument();
    expect(screen.getByTestId('star-rating')).toBeInTheDocument();
  });

  it('displays rating distribution correctly', () => {
    render(<ReviewSummary {...defaultProps} />);

    // Check that all rating levels are shown
    expect(screen.getAllByText('5')).toHaveLength(1);
    expect(screen.getAllByText('4')).toHaveLength(1);
    expect(screen.getAllByText('3')).toHaveLength(2); // Appears in rating and count
    expect(screen.getAllByText('2')).toHaveLength(1);
    expect(screen.getAllByText('1')).toHaveLength(1);

    // Check counts and percentages
    expect(screen.getAllByText('40')).toHaveLength(1); // 5-star count
    expect(screen.getByText('(40%)')).toBeInTheDocument(); // 5-star percentage
    expect(screen.getAllByText('30')).toHaveLength(1); // 4-star count
    expect(screen.getByText('(30%)')).toBeInTheDocument(); // 4-star percentage
  });

  it('shows rating labels', () => {
    render(<ReviewSummary {...defaultProps} />);

    expect(screen.getByText('Excellent')).toBeInTheDocument();
    expect(screen.getByText('Very Good')).toBeInTheDocument();
    expect(screen.getByText('Good')).toBeInTheDocument();
    expect(screen.getByText('Fair')).toBeInTheDocument();
    expect(screen.getByText('Poor')).toBeInTheDocument();
  });

  it('handles rating filter clicks', async () => {
    const mockOnRatingFilter = jest.fn();
    const user = userEvent.setup();

    render(
      <ReviewSummary
        {...defaultProps}
        onRatingFilter={mockOnRatingFilter}
      />
    );

    // Click on 5-star rating
    const fiveStarButton = screen.getByRole('button', { name: /5.*Excellent/ });
    await user.click(fiveStarButton);

    expect(mockOnRatingFilter).toHaveBeenCalledWith(5);
  });

  it('toggles rating filter when same rating is clicked', async () => {
    const mockOnRatingFilter = jest.fn();
    const user = userEvent.setup();

    render(
      <ReviewSummary
        {...defaultProps}
        onRatingFilter={mockOnRatingFilter}
        selectedRating={5}
      />
    );

    // Click on already selected 5-star rating
    const fiveStarButton = screen.getByRole('button', { name: /5.*Excellent/ });
    await user.click(fiveStarButton);

    expect(mockOnRatingFilter).toHaveBeenCalledWith(undefined);
  });

  it('highlights selected rating', () => {
    render(
      <ReviewSummary
        {...defaultProps}
        onRatingFilter={jest.fn()}
        selectedRating={5}
      />
    );

    const fiveStarButton = screen.getByRole('button', { name: /5.*Excellent/ });
    expect(fiveStarButton).toHaveClass('bg-blue-50', 'border-blue-200');
  });

  it('shows filter indicator when rating is selected', () => {
    render(
      <ReviewSummary
        {...defaultProps}
        onRatingFilter={jest.fn()}
        selectedRating={4}
      />
    );

    expect(screen.getByText('Showing 4-star reviews only')).toBeInTheDocument();
    expect(screen.getByText('Show all reviews')).toBeInTheDocument();
  });

  it('clears filter when "Show all reviews" is clicked', async () => {
    const mockOnRatingFilter = jest.fn();
    const user = userEvent.setup();

    render(
      <ReviewSummary
        {...defaultProps}
        onRatingFilter={mockOnRatingFilter}
        selectedRating={4}
      />
    );

    const showAllButton = screen.getByText('Show all reviews');
    await user.click(showAllButton);

    expect(mockOnRatingFilter).toHaveBeenCalledWith(undefined);
  });

  it('handles zero reviews correctly', () => {
    const emptySummary: ProductReviewSummary = {
      ...mockSummary,
      total_reviews: 0,
      average_rating: 0,
      rating_distribution: {
        5: 0,
        4: 0,
        3: 0,
        2: 0,
        1: 0,
      },
      verified_purchase_percentage: 0,
    };

    render(<ReviewSummary summary={emptySummary} />);

    expect(screen.getByText('0.0')).toBeInTheDocument();
    expect(screen.getByText('Based on 0 reviews')).toBeInTheDocument();
    expect(screen.getByText('0% Verified Purchases')).toBeInTheDocument();
  });

  it('handles singular review count', () => {
    const singleReviewSummary: ProductReviewSummary = {
      ...mockSummary,
      total_reviews: 1,
    };

    render(<ReviewSummary summary={singleReviewSummary} />);

    expect(screen.getByText('Based on 1 review')).toBeInTheDocument();
  });

  it('formats large numbers correctly', () => {
    const largeSummary: ProductReviewSummary = {
      ...mockSummary,
      total_reviews: 1500,
      rating_distribution: {
        5: 750,
        4: 450,
        3: 225,
        2: 60,
        1: 15,
      },
    };

    render(<ReviewSummary summary={largeSummary} />);

    expect(screen.getByText('Based on 1,500 reviews')).toBeInTheDocument();
    expect(screen.getByText('750')).toBeInTheDocument(); // Should format large numbers
  });

  it('calculates percentages correctly', () => {
    render(<ReviewSummary {...defaultProps} />);

    // With 100 total reviews:
    // 5 stars: 40 reviews = 40%
    // 4 stars: 30 reviews = 30%
    // 3 stars: 20 reviews = 20%
    // 2 stars: 7 reviews = 7%
    // 1 star: 3 reviews = 3%

    expect(screen.getByText('(40%)')).toBeInTheDocument();
    expect(screen.getByText('(30%)')).toBeInTheDocument();
    expect(screen.getByText('(20%)')).toBeInTheDocument();
    expect(screen.getByText('(7%)')).toBeInTheDocument();
    expect(screen.getByText('(3%)')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <ReviewSummary {...defaultProps} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('disables rating buttons when onRatingFilter is not provided', () => {
    render(<ReviewSummary {...defaultProps} />);

    const ratingButtons = screen.getAllByRole('button');
    ratingButtons.forEach(button => {
      expect(button).toBeDisabled();
    });
  });
});