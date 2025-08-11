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

describe(&apos;CategoryNavigation&apos;, () => {
  const mockCategories = [
    {
      id: &apos;cat1&apos;,
      name: &apos;Electronics&apos;,
      slug: &apos;electronics&apos;,
      is_active: true,
      created_at: &apos;2023-01-01&apos;,
    },
    {
      id: &apos;cat2&apos;,
      name: &apos;Clothing&apos;,
      slug: &apos;clothing&apos;,
      is_active: true,
      created_at: &apos;2023-01-01&apos;,
    },
    {
      id: &apos;cat3&apos;,
      name: &apos;Smartphones&apos;,
      slug: &apos;smartphones&apos;,
      parent: {
        id: &apos;cat1&apos;,
        name: &apos;Electronics&apos;,
        slug: &apos;electronics&apos;,
        is_active: true,
        created_at: &apos;2023-01-01&apos;,
      },
      is_active: true,
      created_at: &apos;2023-01-01&apos;,
    },
    {
      id: &apos;cat4&apos;,
      name: &apos;Laptops&apos;,
      slug: &apos;laptops&apos;,
      parent: {
        id: &apos;cat1&apos;,
        name: &apos;Electronics&apos;,
        slug: &apos;electronics&apos;,
        is_active: true,
        created_at: &apos;2023-01-01&apos;,
      },
      is_active: true,
      created_at: &apos;2023-01-01&apos;,
    },
  ];

  it(&apos;renders root categories correctly&apos;, () => {
    render(<CategoryNavigation categories={mockCategories} />);

    // Check if root categories are rendered
    expect(screen.getByText(&apos;Electronics&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Clothing&apos;)).toBeInTheDocument();
    
    // Check if &quot;All Products&quot; option is rendered
    expect(screen.getByText(&apos;All Products&apos;)).toBeInTheDocument();
  });

  it(&apos;highlights selected category&apos;, () => {
    render(<CategoryNavigation categories={mockCategories} selectedCategorySlug="clothing" />);

    // Check if selected category has the correct styling
    const selectedCategory = screen.getByText(&apos;Clothing&apos;).closest(&apos;a&apos;);
    expect(selectedCategory).toHaveClass(&apos;bg-blue-100&apos;);
    expect(selectedCategory).toHaveClass(&apos;text-blue-700&apos;);
    
    // Check if &quot;All Products&quot; doesn&apos;t have the selected styling
    const allProducts = screen.getByText(&apos;All Products&apos;).closest(&apos;a&apos;);
    expect(allProducts).not.toHaveClass(&apos;bg-blue-100&apos;);
    expect(allProducts).not.toHaveClass(&apos;text-blue-700&apos;);
  });

  it(&apos;calls onSelectCategory when a category is clicked&apos;, () => {
    const mockOnSelectCategory = jest.fn();
    render(
      <CategoryNavigation 
        categories={mockCategories} 
        onSelectCategory={mockOnSelectCategory} 
      />
    );

    // Click on a category
    fireEvent.click(screen.getByText(&apos;Clothing&apos;));
    
    // Check if onSelectCategory was called with the correct slug
    expect(mockOnSelectCategory).toHaveBeenCalledWith(&apos;clothing&apos;);
  });

  it(&apos;expands subcategories when parent category is clicked&apos;, () => {
    render(<CategoryNavigation categories={mockCategories} />);

    // Initially, subcategories should not be visible
    expect(screen.queryByText(&apos;Smartphones&apos;)).not.toBeInTheDocument();
    expect(screen.queryByText(&apos;Laptops&apos;)).not.toBeInTheDocument();
    
    // Click on the expand button for Electronics
    const expandButtons = screen.getAllByRole(&apos;button&apos;);
    const electronicsExpandButton = expandButtons.find(button => 
      button.nextSibling && (button.nextSibling as HTMLElement).textContent === &apos;Electronics&apos;
    );
    
    fireEvent.click(electronicsExpandButton!);
    
    // Now subcategories should be visible
    expect(screen.getByText(&apos;Smartphones&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Laptops&apos;)).toBeInTheDocument();
  });

  it(&apos;renders empty state correctly&apos;, () => {
    render(<CategoryNavigation categories={[]} />);
    
    expect(screen.getByText('No categories available')).toBeInTheDocument();
  });
});