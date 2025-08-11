import React from 'react';
import { render, screen } from '@testing-library/react';
import CartSummary from '../CartSummary';

// Mock Next.js Link component
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => {
    return <a href={href}>{children}</a>;
  };
});

describe(&apos;CartSummary Component&apos;, () => {
  const defaultProps = {
    itemCount: 3,
    subtotal: 2500,
    discountAmount: 300,
    totalAmount: 2200,
  };

  it(&apos;renders the cart summary correctly&apos;, () => {
    render(<CartSummary {...defaultProps} />);

    expect(screen.getByText(&apos;Order Summary&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Items (3)&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;₹2,500&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;-₹300&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;FREE&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Above ₹500&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Tax (GST 18%)&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;₹396&apos;)).toBeInTheDocument(); // 18% of 2200
    expect(screen.getByText(&apos;₹2,596&apos;)).toBeInTheDocument(); // 2200 + 0 + 396
    expect(screen.getByText(&apos;You saved ₹300 on this order!&apos;)).toBeInTheDocument();
  });

  it(&apos;shows shipping cost when subtotal is below free shipping threshold&apos;, () => {
    render(<CartSummary {...defaultProps} subtotal={400} />);

    expect(screen.getByText(&apos;₹50&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Add ₹100 more for FREE shipping&apos;)).toBeInTheDocument();
  });

  it(&apos;shows loading state when loading prop is true&apos;, () => {
    render(<CartSummary {...defaultProps} loading={true} />);

    expect(screen.getByText(&apos;Processing...&apos;)).toBeInTheDocument();
  });

  it(&apos;disables checkout button when itemCount is 0&apos;, () => {
    render(<CartSummary {...defaultProps} itemCount={0} />);

    const checkoutButton = screen.getByRole(&apos;button&apos;, { name: /proceed to checkout/i });
    expect(checkoutButton).toBeDisabled();
  });

  it(&apos;shows the correct progress bar percentage for free shipping&apos;, () => {
    render(<CartSummary {...defaultProps} subtotal={250} />);

    const progressBar = document.querySelector('.bg-blue-600');
    expect(progressBar).toHaveStyle('width: 50%'); // 250/500 = 50%
  });
});