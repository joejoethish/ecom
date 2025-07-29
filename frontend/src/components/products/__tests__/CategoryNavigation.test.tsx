import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { CategoryNavigation } from '../CategoryNavigation';

// Mock Next.js Link component
jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children, onClick }: { href: string; children: React.ReactNode; onClick?: () => void }) => (
    <a href={href} onClick={onClick}>
      {children}
    </a>
  ),
}));

describe('CategoryNavigation', () => {
  const mockCategories = [
    {
      id: 'cat1',
      name: 'Electronics',
      slug: 'electronics',
      is_active: true,
      created_at: '2023-01-01',
    },
    {
      id: 'cat2',
      name: 'Clothing',
      slug: 'clothing',
      is_active: true,
      created_at: '2023-01-01',
    },
    {
      id: 'cat3',
      name: 'Smartphones',
      slug: 'smartphones',
      parent: {
        id: 'cat1',
        name: 'Electronics',
        slug: 'electronics',
        is_active: true,
        created_at: '2023-01-01',
      },
      is_active: true,
      created_at: '2023-01-01',
    },
    {
      id: 'cat4',
      name: 'Laptops',
      slug: 'laptops',
      parent: {
        id: 'cat1',
        name: 'Electronics',
        slug: 'electronics',
        is_active: true,
        created_at: '2023-01-01',
      },
      is_active: true,
      created_at: '2023-01-01',
    },
  ];

  it('renders root categories correctly', () => {
    render(<CategoryNavigation categories={mockCategories} />);

    // Check if root categories are rendered
    expect(screen.getByText('Electronics')).toBeInTheDocument();
    expect(screen.getByText('Clothing')).toBeInTheDocument();
    
    // Check if "All Products" option is rendered
    expect(screen.getByText('All Products')).toBeInTheDocument();
  });

  it('highlights selected category', () => {
    render(<CategoryNavigation categories={mockCategories} selectedCategorySlug="clothing" />);

    // Check if selected category has the correct styling
    const selectedCategory = screen.getByText('Clothing').closest('a');
    expect(selectedCategory).toHaveClass('bg-blue-100');
    expect(selectedCategory).toHaveClass('text-blue-700');
    
    // Check if "All Products" doesn't have the selected styling
    const allProducts = screen.getByText('All Products').closest('a');
    expect(allProducts).not.toHaveClass('bg-blue-100');
    expect(allProducts).not.toHaveClass('text-blue-700');
  });

  it('calls onSelectCategory when a category is clicked', () => {
    const mockOnSelectCategory = jest.fn();
    render(
      <CategoryNavigation 
        categories={mockCategories} 
        onSelectCategory={mockOnSelectCategory} 
      />
    );

    // Click on a category
    fireEvent.click(screen.getByText('Clothing'));
    
    // Check if onSelectCategory was called with the correct slug
    expect(mockOnSelectCategory).toHaveBeenCalledWith('clothing');
  });

  it('expands subcategories when parent category is clicked', () => {
    render(<CategoryNavigation categories={mockCategories} />);

    // Initially, subcategories should not be visible
    expect(screen.queryByText('Smartphones')).not.toBeInTheDocument();
    expect(screen.queryByText('Laptops')).not.toBeInTheDocument();
    
    // Click on the expand button for Electronics
    const expandButtons = screen.getAllByRole('button');
    const electronicsExpandButton = expandButtons.find(button => 
      button.nextSibling && (button.nextSibling as HTMLElement).textContent === 'Electronics'
    );
    
    fireEvent.click(electronicsExpandButton!);
    
    // Now subcategories should be visible
    expect(screen.getByText('Smartphones')).toBeInTheDocument();
    expect(screen.getByText('Laptops')).toBeInTheDocument();
  });

  it('renders empty state correctly', () => {
    render(<CategoryNavigation categories={[]} />);
    
    expect(screen.getByText('No categories available')).toBeInTheDocument();
  });
});