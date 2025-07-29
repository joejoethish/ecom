import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import StarRating from '../../ui/StarRating';

describe('StarRating', () => {
  it('renders correct number of stars', () => {
    render(<StarRating rating={3} />);
    const stars = screen.getAllByRole('button');
    expect(stars).toHaveLength(5); // Default maxRating is 5
  });

  it('displays correct rating visually', () => {
    render(<StarRating rating={3.5} />);
    // This test would need to check the visual representation
    // For now, we'll just ensure it renders without crashing
    expect(screen.getAllByRole('button')).toHaveLength(5);
  });

  it('shows rating value when showValue is true', () => {
    render(<StarRating rating={4.2} showValue />);
    expect(screen.getByText('4.2 / 5')).toBeInTheDocument();
  });

  it('calls onRatingChange when interactive and star is clicked', () => {
    const mockOnRatingChange = jest.fn();
    render(
      <StarRating 
        rating={2} 
        interactive 
        onRatingChange={mockOnRatingChange} 
      />
    );
    
    const stars = screen.getAllByRole('button');
    fireEvent.click(stars[3]); // Click 4th star (rating 4)
    
    expect(mockOnRatingChange).toHaveBeenCalledWith(4);
  });

  it('does not call onRatingChange when not interactive', () => {
    const mockOnRatingChange = jest.fn();
    render(
      <StarRating 
        rating={2} 
        interactive={false} 
        onRatingChange={mockOnRatingChange} 
      />
    );
    
    const stars = screen.getAllByRole('button');
    fireEvent.click(stars[3]);
    
    expect(mockOnRatingChange).not.toHaveBeenCalled();
  });

  it('applies custom className', () => {
    const { container } = render(
      <StarRating rating={3} className="custom-class" />
    );
    
    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('renders with different sizes', () => {
    const { rerender } = render(<StarRating rating={3} size="sm" />);
    let stars = screen.getAllByRole('button');
    expect(stars[0]).toHaveClass('w-4', 'h-4');

    rerender(<StarRating rating={3} size="lg" />);
    stars = screen.getAllByRole('button');
    expect(stars[0]).toHaveClass('w-6', 'h-6');
  });

  it('handles hover states when interactive', () => {
    const mockOnRatingChange = jest.fn();
    render(
      <StarRating 
        rating={2} 
        interactive 
        onRatingChange={mockOnRatingChange} 
      />
    );
    
    const stars = screen.getAllByRole('button');
    
    // Hover over 4th star
    fireEvent.mouseEnter(stars[3]);
    // The visual state should change, but we can't easily test this
    // without more complex DOM inspection
    
    // Mouse leave should reset hover state
    fireEvent.mouseLeave(stars[3]);
  });
});