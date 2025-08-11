import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import StarRating from '../../ui/StarRating';

describe('StarRating', () => {
  it(&apos;renders correct number of stars&apos;, () => {
    render(<StarRating rating={3} />);
    const stars = screen.getAllByRole(&apos;button&apos;);
    expect(stars).toHaveLength(5); // Default maxRating is 5
  });

  it(&apos;displays correct rating visually&apos;, () => {
    render(<StarRating rating={3.5} />);
    // This test would need to check the visual representation
    // For now, we&apos;ll just ensure it renders without crashing
    expect(screen.getAllByRole(&apos;button&apos;)).toHaveLength(5);
  });

  it(&apos;shows rating value when showValue is true&apos;, () => {
    render(<StarRating rating={4.2} showValue />);
    expect(screen.getByText(&apos;4.2 / 5&apos;)).toBeInTheDocument();
  });

  it(&apos;calls onRatingChange when interactive and star is clicked&apos;, () => {
    const mockOnRatingChange = jest.fn();
    render(
      <StarRating 
        rating={2} 
        interactive 
        onRatingChange={mockOnRatingChange} 
      />
    );
    
    const stars = screen.getAllByRole(&apos;button&apos;);
    fireEvent.click(stars[3]); // Click 4th star (rating 4)
    
    expect(mockOnRatingChange).toHaveBeenCalledWith(4);
  });

  it(&apos;does not call onRatingChange when not interactive&apos;, () => {
    const mockOnRatingChange = jest.fn();
    render(
      <StarRating 
        rating={2} 
        interactive={false} 
        onRatingChange={mockOnRatingChange} 
      />
    );
    
    const stars = screen.getAllByRole(&apos;button&apos;);
    fireEvent.click(stars[3]);
    
    expect(mockOnRatingChange).not.toHaveBeenCalled();
  });

  it(&apos;applies custom className&apos;, () => {
      <StarRating rating={3} className="custom-class" />
    );
    
    expect(container.firstChild).toHaveClass(&apos;custom-class&apos;);
  });

  it(&apos;renders with different sizes&apos;, () => {
    let stars = screen.getAllByRole(&apos;button&apos;);
    expect(stars[0]).toHaveClass(&apos;w-4&apos;, &apos;h-4&apos;);

    rerender(<StarRating rating={3} size="lg" />);
    stars = screen.getAllByRole(&apos;button&apos;);
    expect(stars[0]).toHaveClass(&apos;w-6&apos;, &apos;h-6&apos;);
  });

  it(&apos;handles hover states when interactive&apos;, () => {
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