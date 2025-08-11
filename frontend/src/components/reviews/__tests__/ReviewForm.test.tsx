import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReviewForm from '../ReviewForm';
import { Review } from '../../../types';

interface MockStarRatingProps {
  rating: number;
  interactive?: boolean;
  onRatingChange?: (rating: number) => void;
}

// Mock the StarRating component
jest.mock(&apos;../../ui/StarRating&apos;, () => {
  return function MockStarRating({ rating, interactive, onRatingChange }: MockStarRatingProps) {
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

describe(&apos;ReviewForm&apos;, () => {
  const mockOnSubmit = jest.fn();
  const mockOnCancel = jest.fn();
  const defaultProps = {
    productId: &apos;product-123&apos;,
    onSubmit: mockOnSubmit,
    onCancel: mockOnCancel,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it(&apos;renders form fields correctly&apos;, () => {
    render(<ReviewForm {...defaultProps} />);
    
    expect(screen.getByText(&apos;Write a Review&apos;)).toBeInTheDocument();
    expect(screen.getByTestId(&apos;star-rating&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(/review title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/review comment/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/what did you like/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/what could be improved/i)).toBeInTheDocument();
    expect(screen.getByText(&apos;Submit Review&apos;)).toBeInTheDocument();
  });

  it(&apos;renders edit mode when existingReview is provided&apos;, () => {
      id: &apos;review-123&apos;,
      rating: 4,
      title: &apos;Great product&apos;,
      comment: &apos;I really liked this product&apos;,
      pros: &apos;Good quality&apos;,
      cons: &apos;A bit expensive&apos;,
    };

    render(
      <ReviewForm 
        {...defaultProps} 
        existingReview={existingReview as Review} 
      />
    );
    
    expect(screen.getByText(&apos;Edit Your Review&apos;)).toBeInTheDocument();
    expect(screen.getByDisplayValue(&apos;Great product&apos;)).toBeInTheDocument();
    expect(screen.getByDisplayValue(&apos;I really liked this product&apos;)).toBeInTheDocument();
    expect(screen.getByDisplayValue(&apos;Good quality&apos;)).toBeInTheDocument();
    expect(screen.getByDisplayValue(&apos;A bit expensive&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Update Review&apos;)).toBeInTheDocument();
  });

  it(&apos;validates required fields&apos;, async () => {
    const user = userEvent.setup();
    render(<ReviewForm {...defaultProps} />);
    
    const submitButton = screen.getByText(&apos;Submit Review&apos;);
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Please select a rating&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Review title is required&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Review comment is required&apos;)).toBeInTheDocument();
    });
    
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it(&apos;validates minimum field lengths&apos;, async () => {
    const user = userEvent.setup();
    render(<ReviewForm {...defaultProps} />);
    
    // Set rating
    const setRatingButton = screen.getByText(&apos;Set 5 stars&apos;);
    await user.click(setRatingButton);
    
    // Enter short title and comment
    const titleInput = screen.getByLabelText(/review title/i);
    const commentInput = screen.getByLabelText(/review comment/i);
    
    await user.type(titleInput, &apos;Bad&apos;);
    await user.type(commentInput, &apos;Too short&apos;);
    
    const submitButton = screen.getByText(&apos;Submit Review&apos;);
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Title should be at least 5 characters long&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Comment should be at least 10 characters long&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;submits form with valid data&apos;, async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValue(undefined);
    
    render(<ReviewForm {...defaultProps} />);
    
    // Fill form
    const setRatingButton = screen.getByText(&apos;Set 5 stars&apos;);
    await user.click(setRatingButton);
    
    const titleInput = screen.getByLabelText(/review title/i);
    const commentInput = screen.getByLabelText(/review comment/i);
    const prosInput = screen.getByLabelText(/what did you like/i);
    const consInput = screen.getByLabelText(/what could be improved/i);
    
    await user.type(titleInput, &apos;Great product overall&apos;);
    await user.type(commentInput, &apos;This product exceeded my expectations in every way&apos;);
    await user.type(prosInput, &apos;Excellent build quality&apos;);
    await user.type(consInput, &apos;Could be cheaper&apos;);
    
    const submitButton = screen.getByText(&apos;Submit Review&apos;);
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        product: &apos;product-123&apos;,
        rating: 5,
        title: &apos;Great product overall&apos;,
        comment: &apos;This product exceeded my expectations in every way&apos;,
        pros: &apos;Excellent build quality&apos;,
        cons: &apos;Could be cheaper&apos;,
        images: undefined,
      });
    });
  });

  it(&apos;handles image upload&apos;, async () => {
    const user = userEvent.setup();
    render(<ReviewForm {...defaultProps} />);
    
    const fileInput = screen.getByRole(&apos;textbox&apos;, { hidden: true });
    const file = new File([&apos;test&apos;], &apos;test.jpg&apos;, { type: &apos;image/jpeg&apos; });
    
    await user.upload(fileInput, file);
    
    // Should show image preview (this would need more complex testing for actual preview)
    // For now, just ensure no errors are thrown
  });

  it(&apos;validates image file types and sizes&apos;, async () => {
    const user = userEvent.setup();
    render(<ReviewForm {...defaultProps} />);
    
    const fileInput = screen.getByRole(&apos;textbox&apos;, { hidden: true });
    
    // Test invalid file type
    const invalidFile = new File([&apos;test&apos;], &apos;test.txt&apos;, { type: &apos;text/plain&apos; });
    await user.upload(fileInput, invalidFile);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Only image files are allowed&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;limits number of images&apos;, async () => {
    const user = userEvent.setup();
    render(<ReviewForm {...defaultProps} />);
    
    const fileInput = screen.getByRole(&apos;textbox&apos;, { hidden: true });
    
    // Try to upload 6 images (limit is 5)
    const files = Array.from({ length: 6 }, (_, i) => 
      new File([&apos;test&apos;], `test${i}.jpg`, { type: &apos;image/jpeg&apos; })
    );
    
    await user.upload(fileInput, files);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;You can upload a maximum of 5 images&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;calls onCancel when cancel button is clicked&apos;, async () => {
    const user = userEvent.setup();
    render(<ReviewForm {...defaultProps} />);
    
    const cancelButton = screen.getByText(&apos;Cancel&apos;);
    await user.click(cancelButton);
    
    expect(mockOnCancel).toHaveBeenCalled();
  });

  it(&apos;shows loading state&apos;, () => {
    render(<ReviewForm {...defaultProps} loading />);
    
    expect(screen.getByText(&apos;Submitting...&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Submitting...&apos;)).toBeDisabled();
  });

  it(&apos;displays error message&apos;, () => {
    const errorMessage = &apos;Failed to submit review&apos;;
    render(<ReviewForm {...defaultProps} error={errorMessage} />);
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it(&apos;clears field errors when user starts typing&apos;, async () => {
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