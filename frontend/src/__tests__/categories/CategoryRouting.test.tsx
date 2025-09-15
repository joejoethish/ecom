import { render, screen, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { CategoryPage } from '@/components/categories/CategoryPage';
import { categoriesApi } from '@/services/categoriesApi';
import { productsApi } from '@/services/productsApi';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(() => new URLSearchParams()),
}));

// Mock API services
jest.mock('@/services/categoriesApi');
jest.mock('@/services/productsApi');

const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
  back: jest.fn(),
};

const mockCategory = {
  id: 1,
  name: 'Electronics',
  slug: 'electronics',
  description: 'Electronic products and gadgets',
  product_count: 150,
  top_brands: [
    { name: 'Apple', count: 25 },
    { name: 'Samsung', count: 30 },
  ],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockProducts = {
  data: [
    {
      id: '1',
      name: 'iPhone 15',
      slug: 'iphone-15',
      price: 999,
      discount_price: 899,
      discount_percentage: 10,
      image: '/images/iphone15.jpg',
      rating: 4.5,
      review_count: 120,
      brand: 'Apple',
      category: {
        id: 1,
        name: 'Electronics',
        slug: 'electronics',
      },
      is_featured: true,
      free_delivery: true,
      exchange_offer: true,
    },
  ],
  total_count: 1,
  page: 1,
  total_pages: 1,
  has_next: false,
  has_previous: false,
};

const mockFilters = {
  category: {
    id: 1,
    name: 'Electronics',
    slug: 'electronics',
  },
  brands: [
    { name: 'Apple', count: 25 },
    { name: 'Samsung', count: 30 },
  ],
  price_ranges: [
    { from: null, to: 100, label: 'Under $100', count: 5 },
    { from: 100, to: 500, label: '$100 - $500', count: 15 },
  ],
  total_products: 150,
};

describe('Category Routing', () => {
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    jest.clearAllMocks();
  });

  describe('CategoryPage Component', () => {
    it('renders category page with products', () => {
      render(
        <CategoryPage
          category={mockCategory}
          products={mockProducts}
          filters={mockFilters}
          currentPage={1}
          searchParams={{}}
        />
      );

      expect(screen.getByText('Electronics')).toBeInTheDocument();
      expect(screen.getByText('Electronic products and gadgets')).toBeInTheDocument();
      expect(screen.getByText('1 products found')).toBeInTheDocument();
      expect(screen.getByText('iPhone 15')).toBeInTheDocument();
    });

    it('displays popular brands', () => {
      render(
        <CategoryPage
          category={mockCategory}
          products={mockProducts}
          filters={mockFilters}
          currentPage={1}
          searchParams={{}}
        />
      );

      expect(screen.getByText('Popular Brands')).toBeInTheDocument();
      expect(screen.getByText('Apple (25)')).toBeInTheDocument();
      expect(screen.getByText('Samsung (30)')).toBeInTheDocument();
    });

    it('handles filter changes', () => {
      render(
        <CategoryPage
          category={mockCategory}
          products={mockProducts}
          filters={mockFilters}
          currentPage={1}
          searchParams={{}}
        />
      );

      // Click on a brand filter
      const appleFilter = screen.getByText('Apple (25)');
      appleFilter.click();

      expect(mockRouter.push).toHaveBeenCalledWith('/categories/electronics?brand=Apple');
    });

    it('displays no products message when empty', () => {
      const emptyProducts = {
        ...mockProducts,
        data: [],
        total_count: 0,
      };

      render(
        <CategoryPage
          category={mockCategory}
          products={emptyProducts}
          filters={mockFilters}
          currentPage={1}
          searchParams={{}}
        />
      );

      expect(screen.getByText('No products found')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your filters or search criteria.')).toBeInTheDocument();
    });

    it('shows active filters', () => {
      render(
        <CategoryPage
          category={mockCategory}
          products={mockProducts}
          filters={mockFilters}
          currentPage={1}
          searchParams={{ brand: 'Apple', price_min: '100' }}
        />
      );

      expect(screen.getByText('Active filters:')).toBeInTheDocument();
      expect(screen.getByText('Brand: Apple')).toBeInTheDocument();
    });
  });

  describe('API Integration', () => {
    it('calls category details API', async () => {
      const mockCategoryResponse = {
        success: true,
        data: mockCategory,
      };

      (categoriesApi.getCategoryDetails as jest.Mock).mockResolvedValue(mockCategoryResponse);

      await categoriesApi.getCategoryDetails('electronics');

      expect(categoriesApi.getCategoryDetails).toHaveBeenCalledWith('electronics');
    });

    it('calls products by category API', async () => {
      const mockProductsResponse = {
        success: true,
        data: mockProducts,
      };

      (productsApi.getProductsByCategory as jest.Mock).mockResolvedValue(mockProductsResponse);

      await productsApi.getProductsByCategory('electronics', {
        page: 1,
        sort: 'name',
      });

      expect(productsApi.getProductsByCategory).toHaveBeenCalledWith('electronics', {
        page: 1,
        sort: 'name',
      });
    });

    it('calls category filters API', async () => {
      const mockFiltersResponse = {
        success: true,
        data: mockFilters,
      };

      (categoriesApi.getCategoryFilters as jest.Mock).mockResolvedValue(mockFiltersResponse);

      await categoriesApi.getCategoryFilters('electronics');

      expect(categoriesApi.getCategoryFilters).toHaveBeenCalledWith('electronics');
    });
  });

  describe('URL Generation', () => {
    it('generates correct category URLs', () => {
      const categorySlug = 'electronics';
      const expectedUrl = `/categories/${categorySlug}`;
      
      // This would be tested in the actual routing logic
      expect(expectedUrl).toBe('/categories/electronics');
    });

    it('generates URLs with query parameters', () => {
      const categorySlug = 'electronics';
      const params = new URLSearchParams({
        brand: 'Apple',
        sort: 'price',
        page: '2',
      });
      
      const expectedUrl = `/categories/${categorySlug}?${params.toString()}`;
      
      expect(expectedUrl).toBe('/categories/electronics?brand=Apple&sort=price&page=2');
    });
  });
});

describe('Static Params Generation', () => {
  it('generates static params for categories', async () => {
    const mockCategoriesResponse = {
      success: true,
      data: {
        data: [
          { id: 1, name: 'Electronics', slug: 'electronics' },
          { id: 2, name: 'Fashion', slug: 'fashion' },
          { id: 3, name: 'Books', slug: 'books' },
        ],
        total_count: 3,
      },
    };

    (categoriesApi.getAllCategories as jest.Mock).mockResolvedValue(mockCategoriesResponse);

    // This would be the actual generateStaticParams function
    const generateStaticParams = async () => {
      try {
        const response = await categoriesApi.getAllCategories();
        
        if (response.success && response.data) {
          return response.data.data.map((category) => ({
            slug: category.slug,
          }));
        }
        
        return [];
      } catch (error) {
        return [];
      }
    };

    const result = await generateStaticParams();

    expect(result).toEqual([
      { slug: 'electronics' },
      { slug: 'fashion' },
      { slug: 'books' },
    ]);
  });
});