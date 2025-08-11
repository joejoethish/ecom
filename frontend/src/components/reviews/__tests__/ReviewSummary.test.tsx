import React from 'react';
import { render, screen } from '@testing-library/react';
import ReviewSummary from '../ReviewSummary';
import { ProductReviewSummary } from '../../../types';

// Mock the StarRating component
jest.mock('../../ui/StarRating', () => {
  return function MockStarRating({ rating }: { rating: number }) {
    return <div data-testid="star-rating">Rating: {rating}</div>;
  };
});

describe(&apos;ReviewSummary&apos;, () => {
    product_id: &apos;product-123&apos;,
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

  it(&apos;renders summary information correctly&apos;, () => {
    render(<ReviewSummary {...defaultProps} />);

    expect(screen.getByText(&apos;Customer Reviews&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;4.2&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Based on 100 reviews&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;86% Verified Purchases&apos;)).toBeInTheDocument();
    expect(screen.getByTestId(&apos;star-rating&apos;)).toBeInTheDocument();
  });

  it(&apos;displays rating distribution correctly&apos;, () => {
    render(<ReviewSummary {...defaultProps} />);

    // Check that all rating levels are shown
    expect(screen.getAllByText(&apos;5&apos;)).toHaveLength(1);
    expect(screen.getAllByText(&apos;4&apos;)).toHaveLength(1);
    expect(screen.getAllByText(&apos;3&apos;)).toHaveLength(2); // Appears in rating and count
    expect(screen.getAllByText(&apos;2&apos;)).toHaveLength(1);
    expect(screen.getAllByText(&apos;1&apos;)).toHaveLength(1);

    // Check counts and percentages
    expect(screen.getAllByText(&apos;40&apos;)).toHaveLength(1); // 5-star count
    expect(screen.getByText(&apos;(40%)&apos;)).toBeInTheDocument(); // 5-star percentage
    expect(screen.getAllByText(&apos;30&apos;)).toHaveLength(1); // 4-star count
    expect(screen.getByText(&apos;(30%)&apos;)).toBeInTheDocument(); // 4-star percentage
  });

  it(&apos;shows rating labels&apos;, () => {
    render(<ReviewSummary {...defaultProps} />);

    expect(screen.getByText(&apos;Excellent&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Very Good&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Good&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Fair&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Poor&apos;)).toBeInTheDocument();
  });

  it(&apos;handles rating filter clicks&apos;, async () => {
    const mockOnRatingFilter = jest.fn();
    const user = userEvent.setup();

    render(
      <ReviewSummary
        {...defaultProps}
        onRatingFilter={mockOnRatingFilter}
      />
    );

    // Click on 5-star rating
    const fiveStarButton = screen.getByRole(&apos;button&apos;, { name: /5.*Excellent/ });
    await user.click(fiveStarButton);

    expect(mockOnRatingFilter).toHaveBeenCalledWith(5);
  });

  it(&apos;toggles rating filter when same rating is clicked&apos;, async () => {
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
    const fiveStarButton = screen.getByRole(&apos;button&apos;, { name: /5.*Excellent/ });
    await user.click(fiveStarButton);

    expect(mockOnRatingFilter).toHaveBeenCalledWith(undefined);
  });

  it(&apos;highlights selected rating&apos;, () => {
    render(
      <ReviewSummary
        {...defaultProps}
        onRatingFilter={jest.fn()}
        selectedRating={5}
      />
    );

    const fiveStarButton = screen.getByRole(&apos;button&apos;, { name: /5.*Excellent/ });
    expect(fiveStarButton).toHaveClass(&apos;bg-blue-50&apos;, &apos;border-blue-200&apos;);
  });

  it(&apos;shows filter indicator when rating is selected&apos;, () => {
    render(
      <ReviewSummary
        {...defaultProps}
        onRatingFilter={jest.fn()}
        selectedRating={4}
      />
    );

    expect(screen.getByText(&apos;Showing 4-star reviews only&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Show all reviews&apos;)).toBeInTheDocument();
  });

  it(&apos;clears filter when &quot;Show all reviews&quot; is clicked&apos;, async () => {
    const mockOnRatingFilter = jest.fn();
    const user = userEvent.setup();

    render(
      <ReviewSummary
        {...defaultProps}
        onRatingFilter={mockOnRatingFilter}
        selectedRating={4}
      />
    );

    const showAllButton = screen.getByText(&apos;Show all reviews&apos;);
    await user.click(showAllButton);

    expect(mockOnRatingFilter).toHaveBeenCalledWith(undefined);
  });

  it(&apos;handles zero reviews correctly&apos;, () => {
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

    expect(screen.getByText(&apos;0.0&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Based on 0 reviews&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;0% Verified Purchases&apos;)).toBeInTheDocument();
  });

  it(&apos;handles singular review count&apos;, () => {
      ...mockSummary,
      total_reviews: 1,
    };

    render(<ReviewSummary summary={singleReviewSummary} />);

    expect(screen.getByText(&apos;Based on 1 review&apos;)).toBeInTheDocument();
  });

  it(&apos;formats large numbers correctly&apos;, () => {
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

    expect(screen.getByText(&apos;Based on 1,500 reviews&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;750&apos;)).toBeInTheDocument(); // Should format large numbers
  });

  it(&apos;calculates percentages correctly&apos;, () => {
    render(<ReviewSummary {...defaultProps} />);

    // With 100 total reviews:
    // 5 stars: 40 reviews = 40%
    // 4 stars: 30 reviews = 30%
    // 3 stars: 20 reviews = 20%
    // 2 stars: 7 reviews = 7%
    // 1 star: 3 reviews = 3%

    expect(screen.getByText(&apos;(40%)&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;(30%)&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;(20%)&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;(7%)&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;(3%)&apos;)).toBeInTheDocument();
  });

  it(&apos;applies custom className&apos;, () => {
      <ReviewSummary {...defaultProps} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass(&apos;custom-class&apos;);
  });

  it(&apos;disables rating buttons when onRatingFilter is not provided&apos;, () => {
    render(<ReviewSummary {...defaultProps} />);

    const ratingButtons = screen.getAllByRole('button');
    ratingButtons.forEach(button => {
      expect(button).toBeDisabled();
    });
  });
});