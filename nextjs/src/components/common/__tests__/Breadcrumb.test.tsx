import React from 'react';
import { render, screen } from '@testing-library/react';
import { Breadcrumb, BreadcrumbItem } from '../Breadcrumb';

// Mock the next/link component
jest.mock('next/link', () => {
  return ({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) => (
    <a href={href} className={className}>
      {children}
    </a>
  );
});

// Mock the lucide-react icons
jest.mock('lucide-react', () => ({
  ChevronRight: () => <div data-testid="chevron-icon">ChevronRight Icon</div>,
}));

describe('Breadcrumb Component', () => {
  it('renders nothing when items array is empty', () => {
    const { container } = render(<Breadcrumb items={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders a single breadcrumb item correctly', () => {
    const items: BreadcrumbItem[] = [
      { label: 'Home', href: '/', isCurrent: true }
    ];

    render(<Breadcrumb items={items} />);
    
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.queryByTestId('chevron-icon')).not.toBeInTheDocument();
  });

  it('renders multiple breadcrumb items with separators', () => {
    const items: BreadcrumbItem[] = [
      { label: 'Home', href: '/' },
      { label: 'Products', href: '/products' },
      { label: 'Product Name', href: '/products/123', isCurrent: true }
    ];

    render(<Breadcrumb items={items} />);
    
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Products')).toBeInTheDocument();
    expect(screen.getByText('Product Name')).toBeInTheDocument();
    expect(screen.getAllByTestId('chevron-icon')).toHaveLength(2);
  });

  it('renders current item as span and others as links', () => {
    const items: BreadcrumbItem[] = [
      { label: 'Home', href: '/' },
      { label: 'Products', href: '/products', isCurrent: true }
    ];

    render(<Breadcrumb items={items} />);
    
    const homeLink = screen.getByText('Home').closest('a');
    expect(homeLink).toBeInTheDocument();
    expect(homeLink).toHaveAttribute('href', '/');
    
    const productsText = screen.getByText('Products');
    expect(productsText.tagName).not.toBe('A');
    expect(productsText).toHaveAttribute('aria-current', 'page');
  });
});