import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReviewForm from '../ReviewForm';
import { Review } from '../../../types';

// Mock the StarRating component
jest.mock('../../ui/StarRating', () => {
  return function MockStarRating({ rating, interactive, onRatingChange }: any) {
    return (
      <div data-testid="star-rating">
        <span>Rating: {rating}</span>
        {interactive && (
          <button onClick={() => onRatingChange?.(5)}>Set 5 stars</button>
        )}
      </div>
    );
  };
});

describe('ReviewForm', () => {
  const mockOnSubmit = jest.fn();
  const mockOnCancel = jest.fn();
  const defaultProps = {
    productId: 'product-123',
    onSubmit: mockOnSubmit,
    onCancel: mockOnCancel,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders form fields correctly', () => {
    render(<ReviewForm {...defaultProps} />);
    
    expect(screen.getByText('Write a Review')).toBeInTheDocument();
    expect(screen.getByTestId('star-rating')).toBeInTheDocument();
    expect(screen.getByLabelText(/review title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/review comment/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/what did you like/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/what could be improved/i)).toBeInTheDocument();
    expect(screen.getByText('Submit Review')).toBeInTheDocument();
  });

  it('renders edit mode when existingReview is provided', () => {
    const existingReview: Partial<Review> = {
      id: 'review-123',
      rating: 4,
      title: 'Great product',
      comment: 'I really liked this product',
      pros: 'Good quality',
      cons: 'A bit expensive',
    };

    render(
      <ReviewForm 
        {...defaultProps} 
        existingReview={existingReview as Review} 
      />
    );
    
    expect(screen.getByText('Edit Your Review')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Great product')).toBeInTheDocument();
    expect(screen.getByDisplayValue('I really liked this product')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Good quality')).toBeInTheDocument();
    expect(screen.getByDisplayValue('A bit expensive')).toBeInTheDocument();
    expect(screen.getByText('Update Review')).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    const user = userEvent.setup();
    render(<ReviewForm {...defaultProps} />);
    
    const submitButton = screen.getByText('Submit Review');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Please select a rating')).toBeInTheDocument();
      expect(screen.getByText('Review title is required')).toBeInTheDocument();
      expect(screen.getByText('Review comment is required')).toBeInTheDocument();
    });
    
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('validates minimum field lengths', async () => {
    const user = userEvent.setup();
    render(<ReviewForm {...defaultProps} />);
    
    // Set rating
    const setRatingButton = screen.getByText('Set 5 stars');
    await user.click(setRatingButton);
    
    // Enter short title and comment
    const titleInput = screen.getByLabelText(/review title/i);
    const commentInput = screen.getByLabelText(/review comment/i);
    
    await user.type(titleInput, 'Bad');
    await user.type(commentInput, 'Too short');
    
    const submitButton = screen.getByText('Submit Review');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Title should be at least 5 characters long')).toBeInTheDocument();
      expect(screen.getByText('Comment should be at least 10 characters long')).toBeInTheDocument();
    });
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValue(undefined);
    
    render(<ReviewForm {...defaultProps} />);
    
    // Fill form
    const setRatingButton = screen.getByText('Set 5 stars');
    await user.click(setRatingButton);
    
    const titleInput = screen.getByLabelText(/review title/i);
    const commentInput = screen.getByLabelText(/review comment/i);
    const prosInput = screen.getByLabelText(/what did you like/i);
    const consInput = screen.getByLabelText(/what could be improved/i);
    
    await user.type(titleInput, 'Great product overall');
    await user.type(commentInput, 'This product exceeded my expectations in every way');
    await user.type(prosInput, 'Excellent build quality');
    await user.type(consInput, 'Could be cheaper');
    
    const submitButton = screen.getByText('Submit Review');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        product: 'product-123',
        rating: 5,
        title: 'Great product overall',
        comment: 'This product exceeded my expectations in every way',
        pros: 'Excellent build quality',
        cons: 'Could be cheaper',
        images: undefined,
      });
    });
  });

  it('handles image upload', async () => {
    const user = userEvent.setup();
    render(<ReviewForm {...defaultProps} />);
    
    const fileInput = screen.getByRole('textbox', { hidden: true });
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    
    await user.upload(fileInput, file);
    
    // Should show image preview (this would need more complex testing for actual preview)
    // For now, just ensure no errors are thrown
  });

  it('validates image file types and sizes', async () => {
    const user = userEvent.setup();
    render(<ReviewForm {...defaultProps} />);
    
    const fileInput = screen.getByRole('textbox', { hidden: true });
    
    // Test invalid file type
    const invalidFile = new File(['test'], 'test.txt', { type: 'text/plain' });
    await user.upload(fileInput, invalidFile);
    
    await waitFor(() => {
      expect(screen.getByText('Only image files are allowed')).toBeInTheDocument();
    });
  });

  it('limits number of images', async () => {
    const user = userEvent.setup();
    render(<ReviewForm {...defaultProps} />);
    
    const fileInput = screen.getByRole('textbox', { hidden: true });
    
    // Try to upload 6 images (limit is 5)
    const files = Array.from({ length: 6 }, (_, i) => 
      new File(['test'], `test${i}.jpg`, { type: 'image/jpeg' })
    );
    
    await user.upload(fileInput, files);
    
    await waitFor(() => {
      expect(screen.getByText('You can upload a maximum of 5 images')).toBeInTheDocument();
    });
  });

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup();
    render(<ReviewForm {...defaultProps} />);
    
    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);
    
    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('shows loading state', () => {
    render(<ReviewForm {...defaultProps} loading />);
    
    expect(screen.getByText('Submitting...')).toBeInTheDocument();
    expect(screen.getByText('Submitting...')).toBeDisabled();
  });

  it('displays error message', () => {
    const errorMessage = 'Failed to submit review';
    render(<ReviewForm {...defaultProps} error={errorMessage} />);
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('clears field errors when user starts typing', async () => {
    const user = userEvent.setup();
    render(<ReviewForm {...defaultProps} />);
    
    // Trigger validation errors
    const submitButton = screen.getByText('Submit Review');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Review title is required')).toBeInTheDocument();
    });
    
    // Start typing in title field
    const titleInput = screen.getByLabelText(/review title/i);
    await user.type(titleInput, 'A');
    
    // Error should be cleared
    expect(screen.queryByText('Review title is required')).not.toBeInTheDocument();
  });
});