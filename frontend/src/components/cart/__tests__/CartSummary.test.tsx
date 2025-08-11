import React from 'react';
import { render, screen } from '@testing-library/react';
import CartSummary from '../CartSummary';

// Mock Next.js Link component
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => {
    return <a href={href}>{children}</a>;
  };
});

describe('CartSummary Component', () => {
  const defaultProps = {
    itemCount: 3,
    subtotal: 2500,
    discountAmount: 300,
    totalAmount: 2200,
  };

  it('renders the cart summary correctly', () => {
    render(<CartSummary {...defaultProps} />);

    expect(screen.getByText('Order Summary')).toBeInTheDocument();
    expect(screen.getByText('Items (3)')).toBeInTheDocument();
    expect(screen.getByText('₹2,500')).toBeInTheDocument();
    expect(screen.getByText('-₹300')).toBeInTheDocument();
    expect(screen.getByText('FREE')).toBeInTheDocument();
    expect(screen.getByText('Above ₹500')).toBeInTheDocument();
    expect(screen.getByText('Tax (GST 18%)')).toBeInTheDocument();
    expect(screen.getByText('₹396')).toBeInTheDocument(); // 18% of 2200
    expect(screen.getByText('₹2,596')).toBeInTheDocument(); // 2200 + 0 + 396
    expect(screen.getByText('You saved ₹300 on this order!')).toBeInTheDocument();
  });

  it('shows shipping cost when subtotal is below free shipping threshold', () => {
    render(<CartSummary {...defaultProps} subtotal={400} />);

    expect(screen.getByText('₹50')).toBeInTheDocument();
    expect(screen.getByText('Add ₹100 more for FREE shipping')).toBeInTheDocument();
  });

  it('shows loading state when loading prop is true', () => {
    render(<CartSummary {...defaultProps} loading={true} />);

    expect(screen.getByText('Processing...')).toBeInTheDocument();
  });

  it('disables checkout button when itemCount is 0', () => {
    render(<CartSummary {...defaultProps} itemCount={0} />);

    const checkoutButton = screen.getByRole('button', { name: /proceed to checkout/i });
    expect(checkoutButton).toBeDisabled();
  });

  it('shows the correct progress bar percentage for free shipping', () => {
    render(<CartSummary {...defaultProps} subtotal={250} />);

    const progressBar = document.querySelector('.bg-blue-600');
    expect(progressBar).toHaveStyle('width: 50%'); // 250/500 = 50%
  });
});