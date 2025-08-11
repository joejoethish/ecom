import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReviewCard from '../ReviewCard';
import { Review } from '../../../types';

// Mock the StarRating component
jest.mock('../../ui/StarRating', () => {
  return function MockStarRating({ rating }: { rating: number }) {
    return <div data-testid="star-rating">Rating: {rating}</div>;
  };
});

// Mock date-fns
jest.mock(&apos;date-fns&apos;, () => ({
  formatDistanceToNow: () => &apos;2 days ago&apos;,
}));

describe(&apos;ReviewCard&apos;, () => {
    id: &apos;review-123&apos;,
    user: {
      id: &apos;user-123&apos;,
      username: &apos;johndoe&apos;,
      full_name: &apos;John Doe&apos;,
      avatar_url: &apos;https://example.com/avatar.jpg&apos;,
    },
    product: {
      id: &apos;product-123&apos;,
      name: &apos;Test Product&apos;,
      slug: &apos;test-product&apos;,
    },
    rating: 4,
    title: &apos;Great product!&apos;,
    comment: &apos;I really enjoyed using this product. It exceeded my expectations.&apos;,
    pros: &apos;Good quality, fast delivery&apos;,
    cons: &apos;A bit expensive&apos;,
    is_verified_purchase: true,
    status: &apos;approved&apos;,
    helpful_count: 5,
    not_helpful_count: 1,
    helpfulness_score: 83.3,
    images: [
      {
        id: &apos;img-1&apos;,
        image: &apos;https://example.com/review-image.jpg&apos;,
        caption: &apos;Product in use&apos;,
        sort_order: 0,
        created_at: &apos;2024-01-01T00:00:00Z&apos;,
      },
    ],
    user_vote: undefined,
    can_moderate: false,
    created_at: &apos;2024-01-01T00:00:00Z&apos;,
  };

  const defaultProps = {
    review: mockReview,
    currentUserId: &apos;user-456&apos;,
  };

  it(&apos;renders review information correctly&apos;, () => {
    render(<ReviewCard {...defaultProps} />);
    
    expect(screen.getByText(&apos;John Doe&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Great product!&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;I really enjoyed using this product. It exceeded my expectations.&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;2 days ago&apos;)).toBeInTheDocument();
    expect(screen.getByTestId(&apos;star-rating&apos;)).toBeInTheDocument();
  });

  it(&apos;shows verified purchase badge&apos;, () => {
    render(<ReviewCard {...defaultProps} />);
    expect(screen.getByText(&apos;Verified Purchase&apos;)).toBeInTheDocument();
  });

  it(&apos;displays pros and cons when available&apos;, () => {
    render(<ReviewCard {...defaultProps} />);
    
    expect(screen.getByText(&apos;Pros:&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Good quality, fast delivery&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Cons:&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;A bit expensive&apos;)).toBeInTheDocument();
  });

  it(&apos;shows review images&apos;, () => {
    render(<ReviewCard {...defaultProps} />);
    
    const image = screen.getByAltText(&apos;Product in use&apos;);
    expect(image).toBeInTheDocument();
    expect(image).toHaveAttribute(&apos;src&apos;, &apos;https://example.com/review-image.jpg&apos;);
  });

  it(&apos;displays status badges correctly&apos;, () => {
    expect(screen.getByText(&apos;Approved&apos;)).toBeInTheDocument();

    rerender(
      <ReviewCard 
        {...defaultProps} 
        review={{ ...mockReview, status: 'pending' }} 
      />
    );
    expect(screen.getByText(&apos;Pending Review&apos;)).toBeInTheDocument();

    rerender(
      <ReviewCard 
        {...defaultProps} 
        review={{ ...mockReview, status: 'flagged' }} 
      />
    );
    expect(screen.getByText(&apos;Flagged&apos;)).toBeInTheDocument();
  });

  it(&apos;shows helpfulness voting for non-own reviews&apos;, async () => {
    const mockOnVoteHelpful = jest.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    
    render(
      <ReviewCard 
        {...defaultProps} 
        onVoteHelpful={mockOnVoteHelpful}
      />
    );
    
    expect(screen.getByText(&apos;Was this helpful?&apos;)).toBeInTheDocument();
    
    const helpfulButton = screen.getByRole(&apos;button&apos;, { name: /5/ }); // helpful count
    await user.click(helpfulButton);
    
    expect(mockOnVoteHelpful).toHaveBeenCalledWith(&apos;review-123&apos;, &apos;helpful&apos;);
  });

  it(&apos;does not show helpfulness voting for own reviews&apos;, () => {
    render(
      <ReviewCard 
        {...defaultProps} 
        currentUserId="user-123" // Same as review user
        onVoteHelpful={jest.fn()}
      />
    );
    
    expect(screen.queryByText(&apos;Was this helpful?&apos;)).not.toBeInTheDocument();
  });

  it(&apos;shows edit and delete options for own reviews&apos;, async () => {
    const user = userEvent.setup();
    render(
      <ReviewCard 
        {...defaultProps} 
        currentUserId="user-123" // Same as review user
        review={{ ...mockReview, status: 'pending' }} // Can only edit pending reviews
        onEdit={jest.fn()}
        onDelete={jest.fn()}
      />
    );
    
    const moreButton = screen.getByRole(&apos;button&apos;, { name: &apos;&apos; }); // MoreVertical icon
    await user.click(moreButton);
    
    expect(screen.getByText(&apos;Edit&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Delete&apos;)).toBeInTheDocument();
  });

  it(&apos;shows report option for other users reviews&apos;, async () => {
    const user = userEvent.setup();
    render(
      <ReviewCard 
        {...defaultProps} 
        onReport={jest.fn()}
      />
    );
    
    const moreButton = screen.getByRole(&apos;button&apos;, { name: &apos;&apos; }); // MoreVertical icon
    await user.click(moreButton);
    
    expect(screen.getByText(&apos;Report&apos;)).toBeInTheDocument();
  });

  it(&apos;calls onEdit when edit is clicked&apos;, async () => {
    const mockOnEdit = jest.fn();
    const user = userEvent.setup();
    
    render(
      <ReviewCard 
        {...defaultProps} 
        currentUserId="user-123"
        review={{ ...mockReview, status: 'pending' }}
        onEdit={mockOnEdit}
      />
    );
    
    const moreButton = screen.getByRole(&apos;button&apos;, { name: &apos;&apos; });
    await user.click(moreButton);
    
    const editButton = screen.getByText(&apos;Edit&apos;);
    await user.click(editButton);
    
    expect(mockOnEdit).toHaveBeenCalledWith(mockReview);
  });

  it(&apos;calls onDelete when delete is clicked&apos;, async () => {
    const mockOnDelete = jest.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    
    render(
      <ReviewCard 
        {...defaultProps} 
        currentUserId="user-123"
        onDelete={mockOnDelete}
      />
    );
    
    const moreButton = screen.getByRole(&apos;button&apos;, { name: &apos;&apos; });
    await user.click(moreButton);
    
    const deleteButton = screen.getByText(&apos;Delete&apos;);
    await user.click(deleteButton);
    
    expect(mockOnDelete).toHaveBeenCalledWith(&apos;review-123&apos;);
  });

  it(&apos;calls onReport when report is clicked&apos;, async () => {
    const mockOnReport = jest.fn();
    const user = userEvent.setup();
    
    render(
      <ReviewCard 
        {...defaultProps} 
        onReport={mockOnReport}
      />
    );
    
    const moreButton = screen.getByRole(&apos;button&apos;, { name: &apos;&apos; });
    await user.click(moreButton);
    
    const reportButton = screen.getByText(&apos;Report&apos;);
    await user.click(reportButton);
    
    expect(mockOnReport).toHaveBeenCalledWith(&apos;review-123&apos;);
  });

  it(&apos;shows moderation actions when enabled&apos;, async () => {
    const mockOnModerate = jest.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    
    render(
      <ReviewCard 
        {...defaultProps} 
        review={{ ...mockReview, can_moderate: true }}
        showModerationActions
        onModerate={mockOnModerate}
      />
    );
    
    expect(screen.getByText(&apos;Approve&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Reject&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Flag&apos;)).toBeInTheDocument();
    
    const approveButton = screen.getByText(&apos;Approve&apos;);
    await user.click(approveButton);
    
    expect(mockOnModerate).toHaveBeenCalledWith(&apos;review-123&apos;, &apos;approve&apos;);
  });

  it(&apos;shows helpfulness score when available&apos;, () => {
    render(<ReviewCard {...defaultProps} />);
    expect(screen.getByText(&apos;83.3% found this helpful&apos;)).toBeInTheDocument();
  });

  it(&apos;highlights user vote&apos;, () => {
    render(
      <ReviewCard 
        {...defaultProps} 
        review={{ ...mockReview, user_vote: 'helpful' }}
        onVoteHelpful={jest.fn()}
      />
    );
    
    const helpfulButton = screen.getByRole(&apos;button&apos;, { name: /5/ });
    expect(helpfulButton).toHaveClass(&apos;bg-green-100&apos;, &apos;text-green-700&apos;);
  });

  it(&apos;closes dropdown when clicking outside&apos;, async () => {
    const user = userEvent.setup();
    render(
      <ReviewCard 
        {...defaultProps} 
        onReport={jest.fn()}
      />
    );
    
    const moreButton = screen.getByRole('button', { name: '' });
    await user.click(moreButton);
    
    expect(screen.getByText('Report')).toBeInTheDocument();
    
    // Click outside (on the backdrop)
    const backdrop = document.querySelector('.fixed.inset-0');
    if (backdrop) {
      fireEvent.click(backdrop);
    }
    
    await waitFor(() => {
      expect(screen.queryByText('Report')).not.toBeInTheDocument();
    });
  });
});