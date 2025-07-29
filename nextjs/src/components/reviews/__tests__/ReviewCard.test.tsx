import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReviewCard from '../ReviewCard';
import { Review } from '../../../types';

// Mock the StarRating component
jest.mock('../../ui/StarRating', () => {
  return function MockStarRating({ rating }: any) {
    return <div data-testid="star-rating">Rating: {rating}</div>;
  };
});

// Mock date-fns
jest.mock('date-fns', () => ({
  formatDistanceToNow: () => '2 days ago',
}));

describe('ReviewCard', () => {
  const mockReview: Review = {
    id: 'review-123',
    user: {
      id: 'user-123',
      username: 'johndoe',
      full_name: 'John Doe',
      avatar_url: 'https://example.com/avatar.jpg',
    },
    product: {
      id: 'product-123',
      name: 'Test Product',
      slug: 'test-product',
    },
    rating: 4,
    title: 'Great product!',
    comment: 'I really enjoyed using this product. It exceeded my expectations.',
    pros: 'Good quality, fast delivery',
    cons: 'A bit expensive',
    is_verified_purchase: true,
    status: 'approved',
    helpful_count: 5,
    not_helpful_count: 1,
    helpfulness_score: 83.3,
    images: [
      {
        id: 'img-1',
        image: 'https://example.com/review-image.jpg',
        caption: 'Product in use',
        sort_order: 0,
        created_at: '2024-01-01T00:00:00Z',
      },
    ],
    user_vote: undefined,
    can_moderate: false,
    created_at: '2024-01-01T00:00:00Z',
  };

  const defaultProps = {
    review: mockReview,
    currentUserId: 'user-456',
  };

  it('renders review information correctly', () => {
    render(<ReviewCard {...defaultProps} />);
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Great product!')).toBeInTheDocument();
    expect(screen.getByText('I really enjoyed using this product. It exceeded my expectations.')).toBeInTheDocument();
    expect(screen.getByText('2 days ago')).toBeInTheDocument();
    expect(screen.getByTestId('star-rating')).toBeInTheDocument();
  });

  it('shows verified purchase badge', () => {
    render(<ReviewCard {...defaultProps} />);
    expect(screen.getByText('Verified Purchase')).toBeInTheDocument();
  });

  it('displays pros and cons when available', () => {
    render(<ReviewCard {...defaultProps} />);
    
    expect(screen.getByText('Pros:')).toBeInTheDocument();
    expect(screen.getByText('Good quality, fast delivery')).toBeInTheDocument();
    expect(screen.getByText('Cons:')).toBeInTheDocument();
    expect(screen.getByText('A bit expensive')).toBeInTheDocument();
  });

  it('shows review images', () => {
    render(<ReviewCard {...defaultProps} />);
    
    const image = screen.getByAltText('Product in use');
    expect(image).toBeInTheDocument();
    expect(image).toHaveAttribute('src', 'https://example.com/review-image.jpg');
  });

  it('displays status badges correctly', () => {
    const { rerender } = render(<ReviewCard {...defaultProps} />);
    expect(screen.getByText('Approved')).toBeInTheDocument();

    rerender(
      <ReviewCard 
        {...defaultProps} 
        review={{ ...mockReview, status: 'pending' }} 
      />
    );
    expect(screen.getByText('Pending Review')).toBeInTheDocument();

    rerender(
      <ReviewCard 
        {...defaultProps} 
        review={{ ...mockReview, status: 'flagged' }} 
      />
    );
    expect(screen.getByText('Flagged')).toBeInTheDocument();
  });

  it('shows helpfulness voting for non-own reviews', async () => {
    const mockOnVoteHelpful = jest.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    
    render(
      <ReviewCard 
        {...defaultProps} 
        onVoteHelpful={mockOnVoteHelpful}
      />
    );
    
    expect(screen.getByText('Was this helpful?')).toBeInTheDocument();
    
    const helpfulButton = screen.getByRole('button', { name: /5/ }); // helpful count
    await user.click(helpfulButton);
    
    expect(mockOnVoteHelpful).toHaveBeenCalledWith('review-123', 'helpful');
  });

  it('does not show helpfulness voting for own reviews', () => {
    render(
      <ReviewCard 
        {...defaultProps} 
        currentUserId="user-123" // Same as review user
        onVoteHelpful={jest.fn()}
      />
    );
    
    expect(screen.queryByText('Was this helpful?')).not.toBeInTheDocument();
  });

  it('shows edit and delete options for own reviews', async () => {
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
    
    const moreButton = screen.getByRole('button', { name: '' }); // MoreVertical icon
    await user.click(moreButton);
    
    expect(screen.getByText('Edit')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();
  });

  it('shows report option for other users reviews', async () => {
    const user = userEvent.setup();
    render(
      <ReviewCard 
        {...defaultProps} 
        onReport={jest.fn()}
      />
    );
    
    const moreButton = screen.getByRole('button', { name: '' }); // MoreVertical icon
    await user.click(moreButton);
    
    expect(screen.getByText('Report')).toBeInTheDocument();
  });

  it('calls onEdit when edit is clicked', async () => {
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
    
    const moreButton = screen.getByRole('button', { name: '' });
    await user.click(moreButton);
    
    const editButton = screen.getByText('Edit');
    await user.click(editButton);
    
    expect(mockOnEdit).toHaveBeenCalledWith(mockReview);
  });

  it('calls onDelete when delete is clicked', async () => {
    const mockOnDelete = jest.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    
    render(
      <ReviewCard 
        {...defaultProps} 
        currentUserId="user-123"
        onDelete={mockOnDelete}
      />
    );
    
    const moreButton = screen.getByRole('button', { name: '' });
    await user.click(moreButton);
    
    const deleteButton = screen.getByText('Delete');
    await user.click(deleteButton);
    
    expect(mockOnDelete).toHaveBeenCalledWith('review-123');
  });

  it('calls onReport when report is clicked', async () => {
    const mockOnReport = jest.fn();
    const user = userEvent.setup();
    
    render(
      <ReviewCard 
        {...defaultProps} 
        onReport={mockOnReport}
      />
    );
    
    const moreButton = screen.getByRole('button', { name: '' });
    await user.click(moreButton);
    
    const reportButton = screen.getByText('Report');
    await user.click(reportButton);
    
    expect(mockOnReport).toHaveBeenCalledWith('review-123');
  });

  it('shows moderation actions when enabled', async () => {
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
    
    expect(screen.getByText('Approve')).toBeInTheDocument();
    expect(screen.getByText('Reject')).toBeInTheDocument();
    expect(screen.getByText('Flag')).toBeInTheDocument();
    
    const approveButton = screen.getByText('Approve');
    await user.click(approveButton);
    
    expect(mockOnModerate).toHaveBeenCalledWith('review-123', 'approve');
  });

  it('shows helpfulness score when available', () => {
    render(<ReviewCard {...defaultProps} />);
    expect(screen.getByText('83.3% found this helpful')).toBeInTheDocument();
  });

  it('highlights user vote', () => {
    render(
      <ReviewCard 
        {...defaultProps} 
        review={{ ...mockReview, user_vote: 'helpful' }}
        onVoteHelpful={jest.fn()}
      />
    );
    
    const helpfulButton = screen.getByRole('button', { name: /5/ });
    expect(helpfulButton).toHaveClass('bg-green-100', 'text-green-700');
  });

  it('closes dropdown when clicking outside', async () => {
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