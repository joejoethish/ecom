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
jest.mock(&apos;lucide-react&apos;, () => ({
  ChevronRight: () => <div data-testid="chevron-icon">ChevronRight Icon</div>,
}));

describe(&apos;Breadcrumb Component&apos;, () => {
  it(&apos;renders nothing when items array is empty&apos;, () => {
    expect(container.firstChild).toBeNull();
  });

  it(&apos;renders a single breadcrumb item correctly&apos;, () => {
      { label: &apos;Home&apos;, href: &apos;/&apos;, isCurrent: true }
    ];

    render(<Breadcrumb items={items} />);
    
    expect(screen.getByText(&apos;Home&apos;)).toBeInTheDocument();
    expect(screen.queryByTestId(&apos;chevron-icon&apos;)).not.toBeInTheDocument();
  });

  it(&apos;renders multiple breadcrumb items with separators&apos;, () => {
      { label: &apos;Home&apos;, href: &apos;/&apos; },
      { label: &apos;Products&apos;, href: &apos;/products&apos; },
      { label: &apos;Product Name&apos;, href: &apos;/products/123&apos;, isCurrent: true }
    ];

    render(<Breadcrumb items={items} />);
    
    expect(screen.getByText(&apos;Home&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Products&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Product Name&apos;)).toBeInTheDocument();
    expect(screen.getAllByTestId(&apos;chevron-icon&apos;)).toHaveLength(2);
  });

  it(&apos;renders current item as span and others as links&apos;, () => {
      { label: &apos;Home&apos;, href: &apos;/&apos; },
      { label: &apos;Products&apos;, href: &apos;/products&apos;, isCurrent: true }
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